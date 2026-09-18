"""
Volume features: moving average, ratio to MA, rolling percentile.
See RESEARCH_SPEC.md section 4.
"""

from __future__ import annotations

import pandas as pd

from src.features.common import rolling_percentile_rank

VOLUME_MA_WINDOW = 20
VOLUME_PERCENTILE_WINDOW = 365


def add_volume_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    volume = out["volume"]

    vol_ma = volume.rolling(VOLUME_MA_WINDOW, min_periods=VOLUME_MA_WINDOW).mean()
    out["volume_ma_20"] = vol_ma
    out["volume_ratio_20"] = volume / vol_ma
    out["volume_percentile_365d"] = rolling_percentile_rank(volume, VOLUME_PERCENTILE_WINDOW)

    return out
