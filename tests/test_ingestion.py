"""
Tests for Milestone 2 ingestion. These use synthetic, API-shaped data —
no live network calls — so they run offline and in CI. They check the
normalization logic (raw exchange shape -> canonical OHLCVRow) and the
append/dedupe write path, which is exactly the kind of thing that causes
silent data-quality bugs if untested (see docs/METHODOLOGY.md).
"""

from __future__ import annotations

import datetime as dt

from src.data.ingestion.schema import OHLCVRow, write_raw


def _row(ts: dt.datetime, close: float, source: str = "kraken") -> OHLCVRow:
    return OHLCVRow(
        timestamp=ts,
        source=source,
        symbol="BTC-USD",
        timeframe="1d",
        open=close - 1,
        high=close + 1,
        low=close - 2,
        close=close,
        volume=100.0,
        ingested_at=dt.datetime.now(dt.timezone.utc),
    )


def test_write_raw_creates_file(tmp_path):
    rows = [
        _row(dt.datetime(2024, 1, 1, tzinfo=dt.timezone.utc), 42000.0),
        _row(dt.datetime(2024, 1, 2, tzinfo=dt.timezone.utc), 43000.0),
    ]
    out = tmp_path / "kraken_btc_usd_1d.parquet"
    n = write_raw(rows, out)
    assert n == 2
    assert out.exists()


def test_write_raw_deduplicates_on_rerun(tmp_path):
    out = tmp_path / "kraken_btc_usd_1d.parquet"
    day1 = dt.datetime(2024, 1, 1, tzinfo=dt.timezone.utc)

    write_raw([_row(day1, 42000.0)], out)
    # Simulate re-running ingestion later: same timestamp, corrected close.
    n = write_raw([_row(day1, 42500.0)], out)

    assert n == 1  # no duplicate row for the same (source, symbol, tf, ts)


def test_write_raw_keeps_distinct_sources_separate(tmp_path):
    out = tmp_path / "combined.parquet"
    day1 = dt.datetime(2024, 1, 1, tzinfo=dt.timezone.utc)

    write_raw([_row(day1, 42000.0, source="kraken")], out)
    n = write_raw([_row(day1, 42010.0, source="coinbase")], out)

    # Same timestamp, different exchange -> both rows kept, not deduped
    # against each other. This matters for Section 50 cross-validation.
    assert n == 2


def test_write_raw_sorts_by_timestamp(tmp_path):
    import pyarrow.parquet as pq

    out = tmp_path / "unsorted.parquet"
    day2 = dt.datetime(2024, 1, 2, tzinfo=dt.timezone.utc)
    day1 = dt.datetime(2024, 1, 1, tzinfo=dt.timezone.utc)

    write_raw([_row(day2, 43000.0), _row(day1, 42000.0)], out)

    df = pq.read_table(out).to_pandas()
    assert list(df["timestamp"]) == sorted(df["timestamp"])
