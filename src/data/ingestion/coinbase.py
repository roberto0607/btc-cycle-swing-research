"""
Coinbase Exchange public candles ingestion (no auth required).

Endpoint: GET https://api.exchange.coinbase.com/products/BTC-USD/candles
Returns at most 300 candles per call, so for daily granularity we page
through ~299-day windows. Coinbase requires a descriptive User-Agent or
requests can get rejected.

Docs: https://docs.cdp.coinbase.com/exchange/reference/exchangerestapi_getproductcandles
"""

from __future__ import annotations

import datetime as dt
import time

import requests

from src.data.ingestion.schema import OHLCVRow

COINBASE_BASE_URL = "https://api.exchange.coinbase.com"
DEFAULT_PRODUCT_ID = "BTC-USD"
DEFAULT_GRANULARITY_SECONDS = 86400  # daily
MAX_CANDLES_PER_CALL = 300
REQUEST_DELAY_SECONDS = 0.35  # public rate limit is ~3 req/sec
HEADERS = {"User-Agent": "btc-cycle-swing-research/0.1 (research ingestion script)"}


class CoinbaseAPIError(RuntimeError):
    pass


def _fetch_window(
    product_id: str, granularity: int, start: dt.datetime, end: dt.datetime
) -> list[list[float]]:
    params = {
        "start": start.isoformat(),
        "end": end.isoformat(),
        "granularity": granularity,
    }
    resp = requests.get(
        f"{COINBASE_BASE_URL}/products/{product_id}/candles",
        params=params,
        headers=HEADERS,
        timeout=30,
    )
    if resp.status_code != 200:
        raise CoinbaseAPIError(f"Coinbase API error {resp.status_code}: {resp.text}")
    return resp.json()


def fetch_candles(
    product_id: str = DEFAULT_PRODUCT_ID,
    granularity: int = DEFAULT_GRANULARITY_SECONDS,
    start: dt.datetime | None = None,
    end: dt.datetime | None = None,
) -> list[OHLCVRow]:
    """
    Fetch daily candles for `product_id` from `start` to `end` (defaults:
    2014-01-01 to now), paginating in windows sized to stay under
    Coinbase's 300-candles-per-call limit.
    """
    if start is None:
        start = dt.datetime(2014, 1, 1, tzinfo=dt.timezone.utc)
    if end is None:
        end = dt.datetime.now(dt.timezone.utc)

    ingested_at = dt.datetime.now(dt.timezone.utc)
    window_seconds = granularity * (MAX_CANDLES_PER_CALL - 1)
    window = dt.timedelta(seconds=window_seconds)

    all_rows: list[OHLCVRow] = []
    cursor = start

    while cursor < end:
        window_end = min(cursor + window, end)
        candles = _fetch_window(product_id, granularity, cursor, window_end)

        for c in candles:
            # Coinbase candle shape: [time, low, high, open, close, volume]
            time_, low, high, open_, close, volume = c
            all_rows.append(
                OHLCVRow(
                    timestamp=dt.datetime.fromtimestamp(time_, tz=dt.timezone.utc),
                    source="coinbase",
                    symbol="BTC-USD",
                    timeframe="1d",
                    open=float(open_),
                    high=float(high),
                    low=float(low),
                    close=float(close),
                    volume=float(volume),
                    ingested_at=ingested_at,
                )
            )

        cursor = window_end
        time.sleep(REQUEST_DELAY_SECONDS)

    return all_rows
