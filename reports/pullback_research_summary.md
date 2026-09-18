# Phase 4 Pullback Research

Full PULLBACK(threshold, horizon) grid (7 thresholds x 6 horizons = 42 labels) is in `data/labels/coinbase_btc_usd_1d_labeled.parquet`. This report shows a representative subset for readability.

## The central question, properly conditioned

Milestone 5's extension-vs-forward-return table was unconditional and showed the OPPOSITE of the swing hypothesis (extension looked bullish). RESEARCH_SPEC.md section 12 said that's expected if the relationship depends on regime and wasn't being isolated. Compare each regime's bucket rates below against the 'ALL' row: if High extension shows a meaningfully higher pullback_rate than Low extension WITHIN a regime (especially BULL/LATE_BULL, where Milestone 5's unconditional view was dominated by 'up mostly goes up'), that's the swing signal Milestone 5 couldn't isolate. Buckets with n below the minimum sample size are omitted rather than shown with an unreliable rate.

### pullback_10pct_14d by rsi_14 bucket, per regime
| regime | extension_bucket | n | extension_mean | pullback_rate |
|---|---|---|---|---|
| ALL | Low | 1351 | 33.8813 | 0.3501 |
| ALL | Mid | 1350 | 53.1722 | 0.2904 |
| ALL | High | 1350 | 74.2958 | 0.3059 |
| ACCUMULATION | Low | 60 | 28.3339 | 0.3500 |
| ACCUMULATION | Mid | 59 | 41.1309 | 0.2203 |
| ACCUMULATION | High | 60 | 51.3372 | 0.3167 |
| BEAR | Low | 300 | 23.7347 | 0.3667 |
| BEAR | Mid | 299 | 40.1784 | 0.3010 |
| BEAR | High | 300 | 56.7431 | 0.2767 |
| BULL | Low | 489 | 46.0940 | 0.2986 |
| BULL | Mid | 489 | 59.6961 | 0.2904 |
| BULL | High | 489 | 75.3572 | 0.2270 |
| DISTRIBUTION | Low | 197 | 29.5379 | 0.3959 |
| DISTRIBUTION | Mid | 197 | 40.4115 | 0.3604 |
| DISTRIBUTION | High | 197 | 53.6874 | 0.3858 |
| EARLY_RECOVERY | Low | 77 | 48.7882 | 0.4416 |
| EARLY_RECOVERY | Mid | 76 | 61.8737 | 0.3553 |
| EARLY_RECOVERY | High | 77 | 73.5913 | 0.3506 |
| LATE_BULL | Low | 103 | 77.1501 | 0.3301 |
| LATE_BULL | Mid | 102 | 82.2378 | 0.4118 |
| LATE_BULL | High | 103 | 90.0702 | 0.5631 |
| LATE_RECOVERY | Low | 64 | 45.9189 | 0.1875 |
| LATE_RECOVERY | Mid | 64 | 61.0293 | 0.1719 |
| LATE_RECOVERY | High | 64 | 74.7720 | 0.3125 |
![rsi_14 vs pullback_10pct_14d](figures/pullback_rate_rsi_14_pullback_10pct_14d.png)

### pullback_10pct_14d by dist_from_sma_50 bucket, per regime
| regime | extension_bucket | n | extension_mean | pullback_rate |
|---|---|---|---|---|
| ALL | Low | 1339 | -0.1132 | 0.3249 |
| ALL | Mid | 1338 | 0.0240 | 0.2855 |
| ALL | High | 1339 | 0.2122 | 0.3294 |
| ACCUMULATION | Low | 60 | -0.1344 | 0.2667 |
| ACCUMULATION | Mid | 59 | -0.0731 | 0.2542 |
| ACCUMULATION | High | 60 | -0.0280 | 0.3667 |
| BEAR | Low | 300 | -0.2183 | 0.3667 |
| BEAR | Mid | 299 | -0.0968 | 0.3478 |
| BEAR | High | 300 | -0.0276 | 0.2300 |
| BULL | Low | 489 | 0.0315 | 0.2352 |
| BULL | Mid | 489 | 0.1060 | 0.2577 |
| BULL | High | 489 | 0.2497 | 0.3231 |
| DISTRIBUTION | Low | 197 | -0.1261 | 0.4010 |
| DISTRIBUTION | Mid | 197 | -0.0459 | 0.2995 |
| DISTRIBUTION | High | 197 | -0.0162 | 0.4416 |
| EARLY_RECOVERY | Low | 77 | 0.0172 | 0.4416 |
| EARLY_RECOVERY | Mid | 76 | 0.0602 | 0.2763 |
| EARLY_RECOVERY | High | 77 | 0.1316 | 0.4286 |
| LATE_BULL | Low | 103 | 0.1035 | 0.2524 |
| LATE_BULL | Mid | 102 | 0.2701 | 0.4216 |
| LATE_BULL | High | 103 | 0.4955 | 0.6311 |
| LATE_RECOVERY | Low | 64 | 0.0115 | 0.1562 |
| LATE_RECOVERY | Mid | 64 | 0.0422 | 0.2500 |
| LATE_RECOVERY | High | 64 | 0.1146 | 0.2656 |
![dist_from_sma_50 vs pullback_10pct_14d](figures/pullback_rate_dist_from_sma_50_pullback_10pct_14d.png)

### pullback_10pct_14d by runup_from_low_365d bucket, per regime
| regime | extension_bucket | n | extension_mean | pullback_rate |
|---|---|---|---|---|
| ALL | Low | 1234 | 0.2962 | 0.2593 |
| ALL | Mid | 1233 | 1.2360 | 0.1963 |
| ALL | High | 1234 | 4.6569 | 0.5105 |
| ACCUMULATION | Low | 60 | 0.1685 | 0.2833 |
| ACCUMULATION | Mid | 59 | 0.5815 | 0.4237 |
| ACCUMULATION | High | 60 | 1.6858 | 0.1833 |
| BEAR | Low | 300 | 0.0474 | 0.2233 |
| BEAR | Mid | 299 | 0.3058 | 0.2876 |
| BEAR | High | 300 | 2.5986 | 0.4333 |
| BULL | Low | 451 | 0.8699 | 0.1175 |
| BULL | Mid | 451 | 1.5457 | 0.2284 |
| BULL | High | 451 | 5.3966 | 0.5100 |
| DISTRIBUTION | Low | 192 | 0.7801 | 0.3177 |
| DISTRIBUTION | Mid | 192 | 1.3846 | 0.2448 |
| DISTRIBUTION | High | 192 | 5.0932 | 0.6094 |
| EARLY_RECOVERY | Low | 77 | 0.1784 | 0.3247 |
| EARLY_RECOVERY | Mid | 76 | 0.6013 | 0.3026 |
| EARLY_RECOVERY | High | 77 | 2.9248 | 0.5195 |
| LATE_BULL | Low | 91 | 1.2844 | 0.2088 |
| LATE_BULL | Mid | 90 | 2.8420 | 0.4667 |
| LATE_BULL | High | 91 | 9.9329 | 0.5824 |
| LATE_RECOVERY | Low | 64 | 0.1371 | 0.0625 |
| LATE_RECOVERY | Mid | 64 | 0.3117 | 0.3438 |
| LATE_RECOVERY | High | 64 | 1.5418 | 0.2656 |
![runup_from_low_365d vs pullback_10pct_14d](figures/pullback_rate_runup_from_low_365d_pullback_10pct_14d.png)

### pullback_10pct_30d by rsi_14 bucket, per regime
| regime | extension_bucket | n | extension_mean | pullback_rate |
|---|---|---|---|---|
| ALL | Low | 1345 | 33.8295 | 0.5026 |
| ALL | Mid | 1345 | 53.0765 | 0.4164 |
| ALL | High | 1345 | 74.1138 | 0.4067 |
| ACCUMULATION | Low | 60 | 28.3339 | 0.4833 |
| ACCUMULATION | Mid | 59 | 41.1309 | 0.5593 |
| ACCUMULATION | High | 60 | 51.3372 | 0.4667 |
| BEAR | Low | 300 | 23.7347 | 0.5333 |
| BEAR | Mid | 299 | 40.1784 | 0.4281 |
| BEAR | High | 300 | 56.7431 | 0.3633 |
| BULL | Low | 484 | 46.0158 | 0.4752 |
| BULL | Mid | 483 | 59.5144 | 0.4265 |
| BULL | High | 484 | 74.9589 | 0.3182 |
| DISTRIBUTION | Low | 197 | 29.5379 | 0.5584 |
| DISTRIBUTION | Mid | 197 | 40.4115 | 0.4873 |
| DISTRIBUTION | High | 197 | 53.6874 | 0.4924 |
| EARLY_RECOVERY | Low | 77 | 48.7882 | 0.5195 |
| EARLY_RECOVERY | Mid | 76 | 61.8737 | 0.4342 |
| EARLY_RECOVERY | High | 77 | 73.5913 | 0.5325 |
| LATE_BULL | Low | 103 | 77.1501 | 0.3398 |
| LATE_BULL | Mid | 102 | 82.2378 | 0.4314 |
| LATE_BULL | High | 103 | 90.0702 | 0.6311 |
| LATE_RECOVERY | Low | 64 | 45.9189 | 0.3125 |
| LATE_RECOVERY | Mid | 64 | 61.0293 | 0.4375 |
| LATE_RECOVERY | High | 64 | 74.7720 | 0.4688 |
![rsi_14 vs pullback_10pct_30d](figures/pullback_rate_rsi_14_pullback_10pct_30d.png)

### pullback_10pct_30d by dist_from_sma_50 bucket, per regime
| regime | extension_bucket | n | extension_mean | pullback_rate |
|---|---|---|---|---|
| ALL | Low | 1334 | -0.1135 | 0.4520 |
| ALL | Mid | 1333 | 0.0233 | 0.4171 |
| ALL | High | 1333 | 0.2116 | 0.4524 |
| ACCUMULATION | Low | 60 | -0.1344 | 0.5000 |
| ACCUMULATION | Mid | 59 | -0.0731 | 0.3898 |
| ACCUMULATION | High | 60 | -0.0280 | 0.6167 |
| BEAR | Low | 300 | -0.2183 | 0.4900 |
| BEAR | Mid | 299 | -0.0968 | 0.4314 |
| BEAR | High | 300 | -0.0276 | 0.4033 |
| BULL | Low | 484 | 0.0312 | 0.3678 |
| BULL | Mid | 483 | 0.1045 | 0.3975 |
| BULL | High | 484 | 0.2500 | 0.4545 |
| DISTRIBUTION | Low | 197 | -0.1261 | 0.5685 |
| DISTRIBUTION | Mid | 197 | -0.0459 | 0.4061 |
| DISTRIBUTION | High | 197 | -0.0162 | 0.5635 |
| EARLY_RECOVERY | Low | 77 | 0.0172 | 0.4805 |
| EARLY_RECOVERY | Mid | 76 | 0.0602 | 0.3684 |
| EARLY_RECOVERY | High | 77 | 0.1316 | 0.6364 |
| LATE_BULL | Low | 103 | 0.1035 | 0.2913 |
| LATE_BULL | Mid | 102 | 0.2701 | 0.4314 |
| LATE_BULL | High | 103 | 0.4955 | 0.6796 |
| LATE_RECOVERY | Low | 64 | 0.0115 | 0.3281 |
| LATE_RECOVERY | Mid | 64 | 0.0422 | 0.4062 |
| LATE_RECOVERY | High | 64 | 0.1146 | 0.4844 |
![dist_from_sma_50 vs pullback_10pct_30d](figures/pullback_rate_dist_from_sma_50_pullback_10pct_30d.png)

### pullback_10pct_30d by runup_from_low_365d bucket, per regime
| regime | extension_bucket | n | extension_mean | pullback_rate |
|---|---|---|---|---|
| ALL | Low | 1229 | 0.3000 | 0.3930 |
| ALL | Mid | 1228 | 1.2422 | 0.3225 |
| ALL | High | 1228 | 4.6716 | 0.6441 |
| ACCUMULATION | Low | 60 | 0.1685 | 0.3000 |
| ACCUMULATION | Mid | 59 | 0.5815 | 0.6610 |
| ACCUMULATION | High | 60 | 1.6858 | 0.5500 |
| BEAR | Low | 300 | 0.0474 | 0.3433 |
| BEAR | Mid | 299 | 0.3058 | 0.4415 |
| BEAR | High | 300 | 2.5986 | 0.5400 |
| BULL | Low | 446 | 0.8986 | 0.1996 |
| BULL | Mid | 445 | 1.5561 | 0.4022 |
| BULL | High | 446 | 5.4365 | 0.6637 |
| DISTRIBUTION | Low | 192 | 0.7801 | 0.4375 |
| DISTRIBUTION | Mid | 192 | 1.3846 | 0.3958 |
| DISTRIBUTION | High | 192 | 5.0932 | 0.7448 |
| EARLY_RECOVERY | Low | 77 | 0.1784 | 0.4286 |
| EARLY_RECOVERY | Mid | 76 | 0.6013 | 0.3553 |
| EARLY_RECOVERY | High | 77 | 2.9248 | 0.7013 |
| LATE_BULL | Low | 91 | 1.2844 | 0.2637 |
| LATE_BULL | Mid | 90 | 2.8420 | 0.4667 |
| LATE_BULL | High | 91 | 9.9329 | 0.6374 |
| LATE_RECOVERY | Low | 64 | 0.1371 | 0.2031 |
| LATE_RECOVERY | Mid | 64 | 0.3117 | 0.7188 |
| LATE_RECOVERY | High | 64 | 1.5418 | 0.2969 |
![runup_from_low_365d vs pullback_10pct_30d](figures/pullback_rate_runup_from_low_365d_pullback_10pct_30d.png)

### pullback_10pct_90d by rsi_14 bucket, per regime
| regime | extension_bucket | n | extension_mean | pullback_rate |
|---|---|---|---|---|
| ALL | Low | 1325 | 33.7593 | 0.6694 |
| ALL | Mid | 1325 | 53.1405 | 0.6332 |
| ALL | High | 1325 | 74.2598 | 0.5789 |
| ACCUMULATION | Low | 60 | 28.3339 | 0.7333 |
| ACCUMULATION | Mid | 59 | 41.1309 | 0.7288 |
| ACCUMULATION | High | 60 | 51.3372 | 0.7833 |
| BEAR | Low | 290 | 23.5239 | 0.6828 |
| BEAR | Mid | 290 | 39.8340 | 0.6828 |
| BEAR | High | 290 | 56.5654 | 0.6759 |
| BULL | Low | 484 | 46.0158 | 0.6674 |
| BULL | Mid | 483 | 59.5144 | 0.5859 |
| BULL | High | 483 | 74.9600 | 0.4886 |
| DISTRIBUTION | Low | 197 | 29.5379 | 0.7107 |
| DISTRIBUTION | Mid | 197 | 40.4115 | 0.6396 |
| DISTRIBUTION | High | 197 | 53.6874 | 0.6447 |
| EARLY_RECOVERY | Low | 77 | 48.7882 | 0.6104 |
| EARLY_RECOVERY | Mid | 76 | 61.8737 | 0.5921 |
| EARLY_RECOVERY | High | 77 | 73.5913 | 0.7013 |
| LATE_BULL | Low | 103 | 77.1501 | 0.5534 |
| LATE_BULL | Mid | 102 | 82.2378 | 0.5784 |
| LATE_BULL | High | 103 | 90.0702 | 0.7282 |
| LATE_RECOVERY | Low | 54 | 46.8168 | 0.6481 |
| LATE_RECOVERY | Mid | 54 | 63.3238 | 0.9074 |
| LATE_RECOVERY | High | 54 | 75.9371 | 0.6852 |
![rsi_14 vs pullback_10pct_90d](figures/pullback_rate_rsi_14_pullback_10pct_90d.png)

### pullback_10pct_90d by dist_from_sma_50 bucket, per regime
| regime | extension_bucket | n | extension_mean | pullback_rate |
|---|---|---|---|---|
| ALL | Low | 1314 | -0.1137 | 0.6613 |
| ALL | Mid | 1313 | 0.0246 | 0.5903 |
| ALL | High | 1313 | 0.2136 | 0.6306 |
| ACCUMULATION | Low | 60 | -0.1344 | 0.7833 |
| ACCUMULATION | Mid | 59 | -0.0731 | 0.6780 |
| ACCUMULATION | High | 60 | -0.0280 | 0.7833 |
| BEAR | Low | 290 | -0.2209 | 0.6276 |
| BEAR | Mid | 290 | -0.0978 | 0.6897 |
| BEAR | High | 290 | -0.0283 | 0.7241 |
| BULL | Low | 484 | 0.0312 | 0.5083 |
| BULL | Mid | 483 | 0.1047 | 0.5818 |
| BULL | High | 483 | 0.2502 | 0.6522 |
| DISTRIBUTION | Low | 197 | -0.1261 | 0.6701 |
| DISTRIBUTION | Mid | 197 | -0.0459 | 0.6396 |
| DISTRIBUTION | High | 197 | -0.0162 | 0.6853 |
| EARLY_RECOVERY | Low | 77 | 0.0172 | 0.5974 |
| EARLY_RECOVERY | Mid | 76 | 0.0602 | 0.4211 |
| EARLY_RECOVERY | High | 77 | 0.1316 | 0.8831 |
| LATE_BULL | Low | 103 | 0.1035 | 0.4466 |
| LATE_BULL | Mid | 102 | 0.2701 | 0.5882 |
| LATE_BULL | High | 103 | 0.4955 | 0.8252 |
| LATE_RECOVERY | Low | 54 | 0.0147 | 0.6852 |
| LATE_RECOVERY | Mid | 54 | 0.0528 | 0.7593 |
| LATE_RECOVERY | High | 54 | 0.1224 | 0.7963 |
![dist_from_sma_50 vs pullback_10pct_90d](figures/pullback_rate_dist_from_sma_50_pullback_10pct_90d.png)

### pullback_10pct_90d by runup_from_low_365d bucket, per regime
| regime | extension_bucket | n | extension_mean | pullback_rate |
|---|---|---|---|---|
| ALL | Low | 1209 | 0.3277 | 0.6146 |
| ALL | Mid | 1208 | 1.2637 | 0.5604 |
| ALL | High | 1208 | 4.7212 | 0.7781 |
| ACCUMULATION | Low | 60 | 0.1685 | 1.0000 |
| ACCUMULATION | Mid | 59 | 0.5815 | 0.6610 |
| ACCUMULATION | High | 60 | 1.6858 | 0.5833 |
| BEAR | Low | 290 | 0.0501 | 0.5793 |
| BEAR | Mid | 290 | 0.3343 | 0.6207 |
| BEAR | High | 290 | 2.6627 | 0.8414 |
| BULL | Low | 446 | 0.9010 | 0.4148 |
| BULL | Mid | 445 | 1.5574 | 0.6090 |
| BULL | High | 445 | 5.4446 | 0.7888 |
| DISTRIBUTION | Low | 192 | 0.7801 | 0.5729 |
| DISTRIBUTION | Mid | 192 | 1.3846 | 0.6146 |
| DISTRIBUTION | High | 192 | 5.0932 | 0.8594 |
| EARLY_RECOVERY | Low | 77 | 0.1784 | 0.4545 |
| EARLY_RECOVERY | Mid | 76 | 0.6013 | 0.4474 |
| EARLY_RECOVERY | High | 77 | 2.9248 | 1.0000 |
| LATE_BULL | Low | 91 | 1.2844 | 0.4176 |
| LATE_BULL | Mid | 90 | 2.8420 | 0.6556 |
| LATE_BULL | High | 91 | 9.9329 | 0.7692 |
| LATE_RECOVERY | Low | 54 | 0.1909 | 1.0000 |
| LATE_RECOVERY | Mid | 54 | 0.3788 | 1.0000 |
| LATE_RECOVERY | High | 54 | 1.7331 | 0.2407 |
![runup_from_low_365d vs pullback_10pct_90d](figures/pullback_rate_runup_from_low_365d_pullback_10pct_90d.png)
