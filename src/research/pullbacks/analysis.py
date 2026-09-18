"""
The central question from RESEARCH_SPEC.md section 12: "An indicator may
behave differently depending on the market regime... every important
analysis should be segmented by regime." Milestone 5's extension-vs-
forward-return table couldn't do this (no regime labels existed yet).
Milestone 6 built the regime labels but didn't combine them with
extension or formal pullback labels. This module closes that loop.

Example of the question this answers:
    P(pullback_10pct_30d | RSI in top tercile, BULL regime)
        vs.
    P(pullback_10pct_30d | RSI in top tercile, BEAR regime)
        vs.
    P(pullback_10pct_30d)  <- unconditional baseline
"""

from __future__ import annotations

import pandas as pd

MIN_BUCKET_SIZE = 20  # below this, a bucket's rate is too noisy to report


def regime_conditional_extension_pullback(
    df: pd.DataFrame,
    extension_col: str,
    pullback_col: str,
    regime_col: str = "regime",
    n_buckets: int = 3,
    bucket_labels: tuple[str, ...] | None = None,
) -> pd.DataFrame:
    """
    Within EACH regime separately, buckets `extension_col` into
    `n_buckets` equal-frequency groups (default 3 -> Low/Mid/High) and
    reports the pullback rate (mean of the boolean `pullback_col`) per
    bucket. Also includes an 'ALL' pseudo-regime row (buckets computed
    across the whole series, ignoring regime) as the unconditional
    baseline for direct comparison -- this is exactly what Milestone 5
    reported, so putting it in the same table makes the "does regime add
    information" comparison direct.

    Buckets are computed SEPARATELY per regime (via groupby + qcut), not
    globally then filtered -- because a regime's own extension
    distribution is what should be split into Low/Mid/High, per section
    12's point that the same raw indicator value means different things
    in different regimes. A bucket with fewer than MIN_BUCKET_SIZE rows
    is dropped rather than reported with a misleadingly precise rate.
    """
    if bucket_labels is None:
        bucket_labels = tuple(["Low", "Mid", "High"][:n_buckets]) if n_buckets == 3 else tuple(
            f"bucket_{i}" for i in range(n_buckets)
        )
    if len(bucket_labels) != n_buckets:
        raise ValueError("bucket_labels length must match n_buckets")

    d = df[[extension_col, pullback_col, regime_col]].dropna(subset=[extension_col, pullback_col]).copy()
    d[pullback_col] = d[pullback_col].astype("boolean")

    def _bucket_and_summarize(group: pd.DataFrame, regime_label: str) -> list[dict]:
        rows = []
        if len(group) < MIN_BUCKET_SIZE * n_buckets:
            return rows  # not enough data in this regime to bucket meaningfully at all
        try:
            bucketed = pd.qcut(group[extension_col], n_buckets, labels=bucket_labels, duplicates="drop")
        except ValueError:
            return rows  # not enough distinct values to form n_buckets groups

        group = group.copy()
        group["_bucket"] = bucketed
        for bucket_label, bucket_group in group.groupby("_bucket", observed=True):
            n = len(bucket_group)
            if n < MIN_BUCKET_SIZE:
                continue
            rows.append(
                {
                    "regime": regime_label,
                    "extension_bucket": bucket_label,
                    "n": n,
                    "extension_mean": bucket_group[extension_col].mean(),
                    "pullback_rate": bucket_group[pullback_col].mean(),
                }
            )
        return rows

    all_rows = _bucket_and_summarize(d, "ALL")
    for regime_label, group in d.groupby(regime_col):
        all_rows.extend(_bucket_and_summarize(group, regime_label))

    return pd.DataFrame(all_rows)
