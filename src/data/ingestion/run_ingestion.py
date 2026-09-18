"""
Milestone 2 entrypoint: pull daily BTC-USD OHLCV from Kraken and/or
Coinbase and write it to data/raw/ as Parquet.

Usage:
    python -m src.data.ingestion.run_ingestion --source all
    python -m src.data.ingestion.run_ingestion --source kraken
    python -m src.data.ingestion.run_ingestion --source coinbase --start 2020-01-01

Raw output files:
    data/raw/kraken_btc_usd_1d.parquet
    data/raw/coinbase_btc_usd_1d.parquet

Re-running is safe: writes are append-and-deduplicate (see schema.py).
"""

from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path

from src.data.ingestion import coinbase, kraken
from src.data.ingestion.schema import write_raw

RAW_DIR = Path(__file__).resolve().parents[3] / "data" / "raw"

# RESEARCH_SPEC.md section 2.1: primary dataset starts 2014-01-01.
#
# NOTE: passing this as `since` to Kraken does NOT get you full history --
# Kraken's OHLC endpoint has a hard platform limit and only ever returns
# the most recent ~720 daily candles regardless of `since` (see the long
# comment at the top of kraken.py). We still pass it, for two reasons:
# it's harmless (Kraken just ignores it past its own floor), and it's the
# correct value for Coinbase, which genuinely honors it. Kraken is a
# recent-period cross-check only in this project -- see RESEARCH_SPEC.md
# section 2.1's 2026-09-18 correction note.
DEFAULT_START = dt.datetime(2014, 1, 1, tzinfo=dt.timezone.utc)


def _parse_date(s: str) -> dt.datetime:
    return dt.datetime.strptime(s, "%Y-%m-%d").replace(tzinfo=dt.timezone.utc)


def run_kraken(start: dt.datetime | None) -> None:
    print("Fetching Kraken daily BTC-USD OHLC...")
    rows = kraken.fetch_ohlc(since=start or DEFAULT_START)
    n = write_raw(rows, RAW_DIR / "kraken_btc_usd_1d.parquet")
    print(f"  Kraken: fetched {len(rows)} candles this run, {n} total rows on disk.")


def run_coinbase(start: dt.datetime | None, end: dt.datetime | None) -> None:
    print("Fetching Coinbase daily BTC-USD candles...")
    rows = coinbase.fetch_candles(start=start, end=end)
    n = write_raw(rows, RAW_DIR / "coinbase_btc_usd_1d.parquet")
    print(f"  Coinbase: fetched {len(rows)} candles this run, {n} total rows on disk.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Pull daily BTC-USD OHLCV into data/raw/")
    parser.add_argument(
        "--source", choices=["kraken", "coinbase", "all"], default="all"
    )
    parser.add_argument(
        "--start", type=_parse_date, default=None, help="YYYY-MM-DD, defaults to 2014-01-01"
    )
    parser.add_argument(
        "--end", type=_parse_date, default=None, help="YYYY-MM-DD, defaults to now (Coinbase only)"
    )
    args = parser.parse_args()

    if args.source in ("kraken", "all"):
        run_kraken(args.start)
    if args.source in ("coinbase", "all"):
        run_coinbase(args.start, args.end)


if __name__ == "__main__":
    main()
