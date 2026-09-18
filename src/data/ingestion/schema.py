"""
Canonical raw-data schema and storage helpers for Phase 1 ingestion.

Every exchange client normalizes its own response shape into this schema
before anything touches disk. See docs/DATA_DICTIONARY.md for the
authoritative column definitions — keep this file and that doc in sync.

Raw data is immutable once written (Methodology.md, "Engineering hygiene"):
new pulls are appended and de-duplicated on (source, symbol, timeframe,
timestamp), never overwritten in place.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

RAW_SCHEMA = pa.schema(
    [
        ("timestamp", pa.timestamp("s", tz="UTC")),
        ("source", pa.string()),
        ("symbol", pa.string()),
        ("timeframe", pa.string()),
        ("open", pa.float64()),
        ("high", pa.float64()),
        ("low", pa.float64()),
        ("close", pa.float64()),
        ("volume", pa.float64()),
        ("ingested_at", pa.timestamp("s", tz="UTC")),
    ]
)


@dataclass(frozen=True)
class OHLCVRow:
    timestamp: dt.datetime  # candle open time, UTC, tz-aware
    source: str  # "kraken" | "coinbase"
    symbol: str  # "BTC-USD"
    timeframe: str  # "1d"
    open: float
    high: float
    low: float
    close: float
    volume: float
    ingested_at: dt.datetime


def rows_to_table(rows: list[OHLCVRow]) -> pa.Table:
    if not rows:
        return RAW_SCHEMA.empty_table()
    return pa.Table.from_pylist(
        [
            {
                "timestamp": r.timestamp,
                "source": r.source,
                "symbol": r.symbol,
                "timeframe": r.timeframe,
                "open": r.open,
                "high": r.high,
                "low": r.low,
                "close": r.close,
                "volume": r.volume,
                "ingested_at": r.ingested_at,
            }
            for r in rows
        ],
        schema=RAW_SCHEMA,
    )


def write_raw(rows: list[OHLCVRow], out_path: Path) -> int:
    """
    Append-and-deduplicate write. If out_path already exists, the new rows
    are merged with the existing file, duplicates on
    (source, symbol, timeframe, timestamp) are dropped keeping the newest
    ingested_at, and the result is rewritten sorted by timestamp.

    Returns the number of rows in the resulting file.
    """
    new_table = rows_to_table(rows)

    if out_path.exists():
        # Parquet round-trips timestamps at a different precision (ms)
        # than we write them at (s), so cast back to RAW_SCHEMA before
        # concatenating or pyarrow raises on the schema mismatch.
        existing = pq.read_table(out_path).cast(RAW_SCHEMA)
        combined = pa.concat_tables([existing, new_table])
    else:
        combined = new_table

    if combined.num_rows == 0:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        pq.write_table(combined, out_path)
        return 0

    df = combined.to_pandas()
    df = df.sort_values("ingested_at").drop_duplicates(
        subset=["source", "symbol", "timeframe", "timestamp"], keep="last"
    )
    df = df.sort_values("timestamp").reset_index(drop=True)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(pa.Table.from_pandas(df, schema=RAW_SCHEMA, preserve_index=False), out_path)
    return len(df)
