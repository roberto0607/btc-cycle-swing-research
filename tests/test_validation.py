"""
Tests for Milestone 3 validation. Each test builds a small synthetic
DataFrame with exactly one kind of known defect and checks that the
relevant check_* function (and, for a couple of cases, the report-level
pass/fail rollup) catches it -- and that a clean series reports no
critical issues.
"""

from __future__ import annotations

import datetime as dt

import pandas as pd

from src.data.validation import checks
from src.data.validation.report import validate_dataframe

UTC = dt.timezone.utc


def _clean_df(n_days: int = 10) -> pd.DataFrame:
    dates = pd.date_range("2024-01-01", periods=n_days, freq="D", tz="UTC")
    rows = []
    price = 40000.0
    for d in dates:
        rows.append(
            {
                "timestamp": d,
                "source": "test",
                "symbol": "BTC-USD",
                "timeframe": "1d",
                "open": price,
                "high": price + 100,
                "low": price - 100,
                "close": price + 10,
                "volume": 1000.0,
                "ingested_at": dt.datetime.now(UTC),
            }
        )
        price += 10
    return pd.DataFrame(rows)


def test_clean_series_has_no_critical_issues():
    df = _clean_df()
    report = validate_dataframe(df, source="test")
    assert report.passed
    assert report.critical_issue_count == 0
    assert report.total_gap_count == 0


def test_check_duplicate_timestamps_detects_duplicate():
    df = _clean_df()
    dup_row = df.iloc[[0]].copy()
    df = pd.concat([df, dup_row], ignore_index=True)

    dupes = checks.check_duplicate_timestamps(df)
    assert len(dupes) == 1

    report = validate_dataframe(df, source="test")
    assert not report.passed
    assert len(report.duplicate_timestamps) == 1


def test_check_ohlc_consistency_detects_high_below_low():
    df = _clean_df()
    df.loc[3, "high"] = df.loc[3, "low"] - 1  # impossible candle

    bad = checks.check_ohlc_consistency(df)
    assert len(bad) == 1

    report = validate_dataframe(df, source="test")
    assert not report.passed
    assert report.bad_ohlc_rows == 1


def test_check_non_positive_prices_detects_zero_close():
    df = _clean_df()
    df.loc[5, "close"] = 0.0

    bad = checks.check_non_positive_prices(df)
    assert len(bad) == 1

    report = validate_dataframe(df, source="test")
    assert not report.passed
    assert report.non_positive_rows == 1


def test_check_non_positive_prices_detects_negative_volume():
    df = _clean_df()
    df.loc[2, "volume"] = -5.0

    bad = checks.check_non_positive_prices(df)
    assert len(bad) == 1


def test_check_nulls_detects_missing_close():
    df = _clean_df()
    df.loc[1, "close"] = None

    bad = checks.check_nulls(df)
    assert len(bad) == 1

    report = validate_dataframe(df, source="test")
    assert not report.passed
    assert report.null_rows == 1


def test_check_gaps_detects_missing_day():
    df = _clean_df(n_days=10)
    df = df.drop(index=4).reset_index(drop=True)  # remove 2024-01-05

    gaps = checks.check_gaps(df)
    assert len(gaps) == 1
    assert str(gaps[0].date()) == "2024-01-05"

    # Gaps are informational, not critical -- report still passes.
    report = validate_dataframe(df, source="test")
    assert report.passed
    assert report.total_gap_count == 1


def test_check_monotonic_timestamps_detects_unsorted():
    df = _clean_df()
    df = df.iloc[::-1].reset_index(drop=True)  # reverse order

    assert checks.check_monotonic_timestamps(df) is False

    report = validate_dataframe(df, source="test")
    assert not report.passed
    assert report.monotonic is False


def test_validate_dataframe_handles_empty_input():
    df = pd.DataFrame(
        columns=["timestamp", "source", "symbol", "timeframe", "open", "high", "low", "close", "volume", "ingested_at"]
    )
    report = validate_dataframe(df, source="empty")
    assert report.row_count == 0
    assert report.passed
