# Phase 6 Backtest Comparison

Milestone 8's cycle+swing strategy vs. four benchmarks (RESEARCH_SPEC.md section 20), across four cost scenarios (section 19). No single composite score -- compare rows directly. `Cycle Only` vs `Cycle + Swing` isolates whether the tactical swing layer earns its complexity over the core allocation alone.


## optimistic costs
| strategy | total_return | cagr | annualized_volatility | max_drawdown | sharpe | sortino | calmar | avg_exposure | n_trades | total_fees_paid |
|---|---|---|---|---|---|---|---|---|---|---|
| Buy & Hold | 273.3503 | 0.6527 | 0.6667 | -0.8380 | 1.0896 | 1.4705 | 0.7788 | 1.0000 | 1 | 5.0000 |
| Cash | 0.0000 | 0.0000 | 0.0000 | 0.0000 | nan | nan | nan | 0.0000 | 0 | 0.0000 |
| Simple MA Trend | 162.3987 | 0.5778 | 0.5114 | -0.7066 | 1.1462 | 1.2256 | 0.8176 | 0.6134 | 71 | 29171.5971 |
| Cycle Only | 107.2819 | 0.5207 | 0.3779 | -0.5637 | 1.2974 | 1.5647 | 0.9239 | 0.4648 | 265 | 18176.3110 |
| Cycle + Swing (the strategy) | 30.7375 | 0.3626 | 0.3631 | -0.5681 | 1.0319 | 1.1875 | 0.6383 | 0.4796 | 255 | 6339.7139 |

## baseline costs
| strategy | total_return | cagr | annualized_volatility | max_drawdown | sharpe | sortino | calmar | avg_exposure | n_trades | total_fees_paid |
|---|---|---|---|---|---|---|---|---|---|---|
| Buy & Hold | 273.0486 | 0.6525 | 0.6667 | -0.8380 | 1.0894 | 1.4703 | 0.7786 | 1.0000 | 1 | 10.0000 |
| Cash | 0.0000 | 0.0000 | 0.0000 | 0.0000 | nan | nan | nan | 0.0000 | 0 | 0.0000 |
| Simple MA Trend | 150.1154 | 0.5668 | 0.5114 | -0.7091 | 1.1324 | 1.2124 | 0.7993 | 0.6134 | 71 | 55408.0015 |
| Cycle Only | 98.8167 | 0.5097 | 0.3779 | -0.5678 | 1.2780 | 1.5429 | 0.8976 | 0.4648 | 265 | 34342.6205 |
| Cycle + Swing (the strategy) | 27.9267 | 0.3513 | 0.3631 | -0.5728 | 1.0090 | 1.1626 | 0.6133 | 0.4796 | 255 | 11904.4587 |

## pessimistic costs
| strategy | total_return | cagr | annualized_volatility | max_drawdown | sharpe | sortino | calmar | avg_exposure | n_trades | total_fees_paid |
|---|---|---|---|---|---|---|---|---|---|---|
| Buy & Hold | 272.4191 | 0.6522 | 0.6667 | -0.8380 | 1.0891 | 1.4699 | 0.7782 | 1.0000 | 1 | 20.0000 |
| Cash | 0.0000 | 0.0000 | 0.0000 | 0.0000 | nan | nan | nan | 0.0000 | 0 | 0.0000 |
| Simple MA Trend | 127.3194 | 0.5440 | 0.5115 | -0.7144 | 1.1037 | 1.1845 | 0.7615 | 0.6134 | 71 | 99583.9733 |
| Cycle Only | 83.2096 | 0.4869 | 0.3779 | -0.5765 | 1.2376 | 1.4974 | 0.8447 | 0.4648 | 265 | 61055.2362 |
| Cycle + Swing (the strategy) | 22.8322 | 0.3281 | 0.3632 | -0.5825 | 0.9611 | 1.1105 | 0.5633 | 0.4796 | 255 | 20901.6779 |

## stress costs
| strategy | total_return | cagr | annualized_volatility | max_drawdown | sharpe | sortino | calmar | avg_exposure | n_trades | total_fees_paid |
|---|---|---|---|---|---|---|---|---|---|---|
| Buy & Hold | 271.6010 | 0.6517 | 0.6667 | -0.8380 | 1.0887 | 1.4694 | 0.7777 | 1.0000 | 1 | 30.0000 |
| Cash | 0.0000 | 0.0000 | 0.0000 | 0.0000 | nan | nan | nan | 0.0000 | 0 | 0.0000 |
| Simple MA Trend | 102.6549 | 0.5148 | 0.5117 | -0.7212 | 1.0660 | 1.1475 | 0.7138 | 0.6134 | 71 | 130234.2021 |
| Cycle Only | 66.4895 | 0.4578 | 0.3780 | -0.5874 | 1.1849 | 1.4383 | 0.7793 | 0.4648 | 265 | 78738.5073 |
| Cycle + Swing (the strategy) | 17.5183 | 0.2985 | 0.3634 | -0.5948 | 0.8986 | 1.0421 | 0.5018 | 0.4796 | 255 | 26546.4461 |

## Equity curves (baseline costs)
![Equity curves](figures/equity_curves.png)
