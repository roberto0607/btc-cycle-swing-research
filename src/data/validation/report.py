"""
Turns the raw check_* results from checks.py into a per-series validation
report, and renders a set of reports as a human-readable Markdown file.

A report "passes" if it has zero CRITICAL findings. Gaps are reported but
are NOT critical by default -- a missing exchange day is real market
history, not necessarily bad data, and must never be silently filled in
(master spec Section 15, Rule 3 "no look-ahead bias" doesn't apply here,
but the sibling rule against inventing data does). Duplicates, bad OHLC
geometry, nulls, and non-positive prices/negative volume ARE critical --
those are unambiguous data-quality defects, not real market behavior.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field

import pandas as pd

from src.data.validation import checks


@dataclass
class ValidationReport:
    source: str
    symbol: str
    timeframe: str
    row_count: int
    date_min: pd.Timestamp | None
    date_max: pd.Timestamp | None
    duplicate_timestamps: list[str] = field(default_factory=list)
    null_rows: int = 0
    non_positive_rows: int = 0
    bad_ohlc_rows: int = 0
    gap_dates: list[str] = field(default_factory=list)
    total_gap_count: int = 0
    monotonic: bool = True

    @property
    def critical_issue_count(self) -> int:
        return (
            len(self.duplicate_timestamps)
            + self.null_rows
            + self.non_positive_rows
            + self.bad_ohlc_rows
            + (0 if self.monotonic else 1)
        )

    @property
    def passed(self) -> bool:
        return self.critical_issue_count == 0


def validate_dataframe(df: pd.DataFrame, source: str) -> ValidationReport:
    if df.empty:
        return ValidationReport(
            source=source, symbol="", timeframe="", row_count=0,
            date_min=None, date_max=None,
        )

    symbol = df["symbol"].iloc[0]
    timeframe = df["timeframe"].iloc[0]

    dupes = checks.check_duplicate_timestamps(df)
    nulls = checks.check_nulls(df)
    non_positive = checks.check_non_positive_prices(df)
    bad_ohlc = checks.check_ohlc_consistency(df)
    gaps = checks.check_gaps(df)
    monotonic = checks.check_monotonic_timestamps(df)

    return ValidationReport(
        source=source,
        symbol=symbol,
        timeframe=timeframe,
        row_count=len(df),
        date_min=df["timestamp"].min(),
        date_max=df["timestamp"].max(),
        duplicate_timestamps=[str(ts) for ts in dupes.index[:20]],
        null_rows=len(nulls),
        non_positive_rows=len(non_positive),
        bad_ohlc_rows=len(bad_ohlc),
        gap_dates=[str(d) for d in gaps[:50]],
        total_gap_count=len(gaps),
        monotonic=monotonic,
    )


def render_markdown(reports: list[ValidationReport], generated_at: dt.datetime | None = None) -> str:
    generated_at = generated_at or dt.datetime.now(dt.timezone.utc)
    lines = [
        "# Data Validation Report",
        "",
        f"Generated: {generated_at.isoformat()}",
        "",
        "| Source | Symbol | Timeframe | Rows | Date range | Duplicates | Nulls | Bad OHLC | Non-positive | Gaps | Monotonic | Status |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in reports:
        date_range = f"{r.date_min} → {r.date_max}" if r.date_min is not None else "—"
        status = "PASS" if r.passed else "FAIL"
        lines.append(
            f"| {r.source} | {r.symbol} | {r.timeframe} | {r.row_count} | {date_range} "
            f"| {len(r.duplicate_timestamps)} | {r.null_rows} | {r.bad_ohlc_rows} "
            f"| {r.non_positive_rows} | {r.total_gap_count} | {r.monotonic} | {status} |"
        )

    lines.append("")
    lines.append("## Details")
    for r in reports:
        lines.append(f"\n### {r.source} — {r.symbol} {r.timeframe}")
        if r.passed:
            lines.append("No critical issues.")
        if r.duplicate_timestamps:
            lines.append(f"\n**Duplicate timestamps** (showing up to 20): {r.duplicate_timestamps}")
        if r.null_rows:
            lines.append(f"\n**Rows with null OHLCV values:** {r.null_rows}")
        if r.non_positive_rows:
            lines.append(f"\n**Rows with non-positive price / negative volume:** {r.non_positive_rows}")
        if r.bad_ohlc_rows:
            lines.append(f"\n**Rows violating OHLC geometry (high/low inconsistent with open/close):** {r.bad_ohlc_rows}")
        if not r.monotonic:
            lines.append("\n**Timestamps are not sorted ascending.**")
        if r.gap_dates:
            lines.append(
                f"\n**Missing calendar dates within range** (informational, not "
                f"auto-filled, showing up to 50 of {r.total_gap_count}): {r.gap_dates}"
            )

    return "\n".join(lines) + "\n"
