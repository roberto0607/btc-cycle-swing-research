"""
Chains price, momentum, volatility, volume, and structure features into
one feature table. Order doesn't affect correctness (each add_* function
only reads the original OHLCV columns, not other features' outputs), but
is kept consistent for readable diffs.

Regime features (src/features/regime.py) are NOT included here -- regime
classification is a Phase 3 research question (does a regime label add
information at all?), not a fixed feature to compute alongside these.
"""

from __future__ import annotations

import pandas as pd

from src.features.momentum import add_momentum_features
from src.features.price import add_price_features
from src.features.structure import add_structure_features
from src.features.volatility import add_volatility_features
from src.features.volume import add_volume_features


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    `df` must be a single (source, symbol, timeframe) OHLCV series, sorted
    ascending by timestamp -- exactly the shape written by
    src/data/ingestion/schema.write_raw. Returns a new DataFrame with all
    original columns plus every feature column from every family.
    """
    out = df.copy()
    out = add_price_features(out)
    out = add_momentum_features(out)
    out = add_volatility_features(out)
    out = add_volume_features(out)
    out = add_structure_features(out)
    return out
