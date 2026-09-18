"""
Individual data-quality checks for raw OHLCV data.

Each function takes a DataFrame matching the schema in
src/data/ingestion/schema.py (timestamp, source, symbol, timeframe, open,
high, low, close, volume, ingested_at) for a SINGLE (source, symbol,
timeframe) series, and returns the problem rows/values it found. Empty
result = clean on that check.

These are deliberately dumb and literal -- no judgment calls, no
"probably fine" thresholds. Judgment calls belong in report.py, where
findings are converted into "critical" vs "informational".
"""

from __future__ import annotations

import pandas as pd


def check_duplicate_timestamps(df: pd.DataFrame) -> pd.Series:
    """Timestamps appearing more than once in this series."""
    counts = df["timestamp"].value_counts()
    return counts[counts > 1]


def check_nulls(df: pd.DataFrame) -> pd.DataFrame:
    """Rows with a null in any OHLCV column."""
    cols = ["open", "high", "low", "close", "volume"]
    mask = df[cols].isnull().any(axis=1)
    return df.loc[mask]


def check_non_positive_prices(df: pd.DataFrame) -> pd.DataFrame:
    """Rows where open/high/low/close <= 0 (volume == 0 is allowed -- a
    genuinely illiquid day is possible; volume < 0 is not)."""
    price_cols = ["open", "high", "low", "close"]
    bad_price = (df[price_cols] <= 0).any(axis=1)
    bad_volume = df["volume"] < 0
    return df.loc[bad_price | bad_volume]


def check_ohlc_consistency(df: pd.DataFrame) -> pd.DataFrame:
    """
    Rows that violate basic candle geometry:
        high must be >= open, close, and low
        low must be <= open, close, and high
    """
    bad = (
        (df["high"] < df["low"])
        | (df["high"] < df["open"])
        | (df["high"] < df["close"])
        | (df["low"] > df["open"])
        | (df["low"] > df["close"])
    )
    return df.loc[bad]


def check_gaps(df: pd.DataFrame, freq: str = "D") -> pd.DatetimeIndex:
    """
    Expected calendar dates (at `freq`) between this series' min and max
    timestamp that don't appear in the data at all. For a mature, liquid
    market like BTC-USD daily candles, any gap here is worth an explicit
    look -- it does not necessarily mean bad data (an exchange outage is
    real market history too), but it must never be silently interpolated
    away (master spec: "no unrealistic fills", "document provenance").
    """
    if df.empty:
        return pd.DatetimeIndex([])
    full_range = pd.date_range(
        start=df["timestamp"].min(), end=df["timestamp"].max(), freq=freq, tz="UTC"
    )
    present = pd.DatetimeIndex(df["timestamp"].unique())
    missing = full_range.difference(present)
    return missing


def check_monotonic_timestamps(df: pd.DataFrame) -> bool:
    """True if timestamps are sorted ascending (expected after ingestion's
    write_raw, which always sorts -- this check exists to catch a future
    change to that guarantee)."""
    return df["timestamp"].is_monotonic_increasing
