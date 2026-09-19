"""
Transaction cost model (RESEARCH_SPEC.md section 19: "Run multiple cost
assumptions... optimistic, baseline, pessimistic, stress. The strategy
should not only work under unrealistically low transaction costs.").

Three distinct cost components, matching section 18/19's explicit
breakdown:
  - fee_bps: exchange taker fee, charged on notional traded (both buys
    and sells), deducted from cash.
  - spread_bps: bid-ask spread -- modeled as an unfavorable adjustment to
    the fill price (buy slightly above the quoted price, sell slightly
    below).
  - slippage_bps: additional unfavorable price movement from market
    impact/execution delay, same mechanism as spread, kept as a separate
    documented number so each cost source's contribution stays visible.

All values are basis points (1 bps = 0.01%). Scenario numbers below are
DOCUMENTED GUESSES informed by typical major-exchange BTC-USD spot
trading costs, not fitted to this project's data -- per RESEARCH_SPEC.md
section 49, treat them as a parameter region for Phase 7, not settled
values.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CostModel:
    fee_bps: float
    spread_bps: float
    slippage_bps: float

    @property
    def total_price_impact_bps(self) -> float:
        """Spread + slippage combine into one unfavorable price
        adjustment; fee is applied separately to notional, not price."""
        return self.spread_bps + self.slippage_bps


COST_SCENARIOS: dict[str, CostModel] = {
    "optimistic": CostModel(fee_bps=5.0, spread_bps=1.0, slippage_bps=0.0),
    "baseline": CostModel(fee_bps=10.0, spread_bps=2.0, slippage_bps=5.0),
    "pessimistic": CostModel(fee_bps=20.0, spread_bps=5.0, slippage_bps=15.0),
    "stress": CostModel(fee_bps=30.0, spread_bps=10.0, slippage_bps=30.0),
}


def get_cost_model(scenario: str) -> CostModel:
    if scenario not in COST_SCENARIOS:
        raise ValueError(f"Unknown cost scenario: {scenario!r}. Options: {list(COST_SCENARIOS)}")
    return COST_SCENARIOS[scenario]
