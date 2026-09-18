"""
Kraken public OHLC ingestion (no auth required).

Endpoint: GET https://api.kraken.com/0/public/OHLC

IMPORTANT PLATFORM LIMIT (confirmed against Kraken's own docs, and by a
live run of this exact function that returned exactly 721 rows no matter
how far back `since` was set):

    "Returns up to 720 of the most recent entries (older data cannot be
    retrieved, regardless of the value of `since`)."

There is NO pagination path to deep history on this endpoint -- passing an
older `since` does not unlock older candles, it's simply ignored past that
~720-candle floor. This function's pagination loop is technically correct
(it will terminate cleanly either way) but on a real request it will only
ever return the most recent ~720 daily candles (~2 years), regardless of
`since`. See docs/RESEARCH_SPEC.md \u00a72.1 -- Kraken is a recent-period
cross-check only in this project, NOT the full-history primary source.
Coinbase's /candles endpoint (coinbase.py) is what actually paginates back
to 2014.

Docs: https://docs.kraken.com/api/docs/rest-api/get-ohlc-data
"""

from __future__ import annotations

import datetime as dt
import time

import requests

from src.data.ingestion.schema import OHLCVRow

KRAKEN_BASE_URL = "https://api.kraken.com/0/public"
DEFAULT_PAIR = "XBTUSD"
DEFAULT_INTERVAL_MINUTES = 1440  # daily
REQUEST_DELAY_SECONDS = 1.0  # be polite; public endpoint is IP rate-limited


class KrakenAPIError(RuntimeError):
    pass


def _fetch_page(pair: str, interval: int, since: int | None) -> dict:
    params: dict[str, str | int] = {"pair": pair, "interval": interval}
    if since is not None:
        params["since"] = since

    resp = requests.get(f"{KRAKEN_BASE_URL}/OHLC", params=params, timeout=30)
    resp.raise_for_status()
    payload = resp.json()

    if payload.get("error"):
        raise KrakenAPIError(f"Kraken API returned errors: {payload['error']}")

    return payload["result"]


def fetch_ohlc(
    pair: str = DEFAULT_PAIR,
    interval: int = DEFAULT_INTERVAL_MINUTES,
    since: dt.datetime | None = None,
) -> list[OHLCVRow]:
    """
    Fetch the full available daily OHLC history for `pair` starting from
    `since` (or Kraken's earliest available data if omitted), paginating
    until no new candles are returned.
    """
    since_ts = int(since.timestamp()) if since else None
    ingested_at = dt.datetime.now(dt.timezone.utc)

    all_rows: list[OHLCVRow] = []
    seen_last: int | None = None

    while True:
        result = _fetch_page(pair, interval, since_ts)

        # The candle data lives under a Kraken-internal pair key (e.g.
        # "XXBTZUSD") alongside "last" — find that key rather than
        # hardcoding it, since Kraken's internal naming isn't the same as
        # the request pair string.
        candle_key = next(k for k in result if k != "last")
        candles = result[candle_key]
        last = result["last"]

        if not candles or last == seen_last:
            break

        for c in candles:
            # [time, open, high, low, close, vwap, volume, count]
            all_rows.append(
                OHLCVRow(
                    timestamp=dt.datetime.fromtimestamp(c[0], tz=dt.timezone.utc),
                    source="kraken",
                    symbol="BTC-USD",
                    timeframe="1d",
                    open=float(c[1]),
                    high=float(c[2]),
                    low=float(c[3]),
                    close=float(c[4]),
                    volume=float(c[6]),
                    ingested_at=ingested_at,
                )
            )

        seen_last = last
        since_ts = last
        time.sleep(REQUEST_DELAY_SECONDS)

        # Kraken returns <= 720 candles/call; once a page comes back with
        # fewer candles than the max, we've reached the most recent data.
        if len(candles) < 720:
            break

    return all_rows
