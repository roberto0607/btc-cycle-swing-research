"""
Milestone 4 entrypoint: build the feature table from the primary
(Coinbase) raw dataset and write it to data/features/.

Usage:
    python -m src.features.run_features

Reads:
    data/raw/coinbase_btc_usd_1d.parquet   (primary, full-history source)
Writes:
    data/features/coinbase_btc_usd_1d_features.parquet

Deliberately only builds features from the primary source. Kraken's raw
file (recent ~2 years only, see RESEARCH_SPEC.md section 2.1) is a
cross-validation input for later research questions, not part of the main
feature table.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.features.pipeline import build_features

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_PATH = PROJECT_ROOT / "data" / "raw" / "coinbase_btc_usd_1d.parquet"
OUT_PATH = PROJECT_ROOT / "data" / "features" / "coinbase_btc_usd_1d_features.parquet"


def main() -> None:
    if not RAW_PATH.exists():
        raise FileNotFoundError(
            f"{RAW_PATH} not found -- run Milestone 2 ingestion first "
            f"(python -m src.data.ingestion.run_ingestion --source coinbase)."
        )

    df = pd.read_parquet(RAW_PATH)
    df = df.sort_values("timestamp").reset_index(drop=True)

    features = build_features(df)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    features.to_parquet(OUT_PATH, index=False)

    n_feature_cols = len(features.columns) - len(df.columns)
    warmup_rows = features.isnull().any(axis=1).sum()
    print(f"Built {n_feature_cols} feature columns across {len(features)} rows.")
    print(f"Rows with at least one NaN (rolling-window warmup period): {warmup_rows}")
    print(f"Written to {OUT_PATH}")


if __name__ == "__main__":
    main()
