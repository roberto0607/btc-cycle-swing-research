"""
Milestone 3 entrypoint: validate every file in data/raw/ and write a
Markdown report to reports/.

Usage:
    python -m src.data.validation.run_validation

Exit code is 1 if any series has critical issues (duplicates, nulls, bad
OHLC geometry, non-positive prices/negative volume, unsorted timestamps)
-- meant to be usable as a CI gate later. Gaps are reported but do not by
themselves fail the run (see report.py docstring for why).

Never modifies data/raw/ -- this is read-only validation. Output:
    reports/data_validation_latest.md          (overwritten each run)
    reports/data_validation_<UTC timestamp>.md (kept, one per run)
"""

from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

import pandas as pd

from src.data.validation.report import render_markdown, validate_dataframe

PROJECT_ROOT = Path(__file__).resolve().parents[3]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
REPORTS_DIR = PROJECT_ROOT / "reports"


def main() -> None:
    parquet_files = sorted(RAW_DIR.glob("*.parquet"))
    if not parquet_files:
        print(f"No parquet files found in {RAW_DIR}. Run Milestone 2 ingestion first.")
        sys.exit(1)

    reports = []
    for path in parquet_files:
        df = pd.read_parquet(path)
        source_label = path.stem  # e.g. "kraken_btc_usd_1d"
        report = validate_dataframe(df, source=source_label)
        reports.append(report)

        status = "PASS" if report.passed else "FAIL"
        print(
            f"{source_label}: {report.row_count} rows, "
            f"{report.date_min} \u2192 {report.date_max}, "
            f"{report.critical_issue_count} critical issue(s), "
            f"{report.total_gap_count} gap(s) -- {status}"
        )

    generated_at = dt.datetime.now(dt.timezone.utc)
    markdown = render_markdown(reports, generated_at=generated_at)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    (REPORTS_DIR / "data_validation_latest.md").write_text(markdown)
    stamped_name = f"data_validation_{generated_at.strftime('%Y%m%dT%H%M%SZ')}.md"
    (REPORTS_DIR / stamped_name).write_text(markdown)

    print(f"\nReport written to reports/data_validation_latest.md and reports/{stamped_name}")

    if any(not r.passed for r in reports):
        print("\nOne or more series has CRITICAL issues -- see report for details.")
        sys.exit(1)


if __name__ == "__main__":
    main()
