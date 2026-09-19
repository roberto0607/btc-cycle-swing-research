"""
Portfolio accounting (RESEARCH_SPEC.md section 18: "initial capital, BTC
holdings, cash, orders, fills, fees, spread, slippage, portfolio value").

A Portfolio holds cash and BTC. rebalance_to_target is the only way it
changes: given a target allocation fraction (0.0-1.0) and a fill price,
it computes the trade needed to hit that target, applies spread+slippage
to the fill price (unfavorably: worse price when buying, worse when
selling), applies the fee to the traded notional, and updates cash/BTC.

No look-ahead risk here -- this module only acts on a price and target
handed to it by the caller (engine.py), which is responsible for using
the correct causal price per the execution model.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from src.backtesting.costs import CostModel


@dataclass
class Trade:
    timestamp: object
    direction: str  # "BUY" or "SELL"
    notional_before_fees: float
    fee_paid: float
    fill_price: float
    btc_delta: float


@dataclass
class Portfolio:
    cash: float
    btc: float = 0.0
    trades: list[Trade] = field(default_factory=list)

    def total_value(self, price: float) -> float:
        return self.cash + self.btc * price

    def current_allocation(self, price: float) -> float:
        value = self.total_value(price)
        if value <= 0:
            return 0.0
        return (self.btc * price) / value

    def rebalance_to_target(self, target_allocation: float, price: float, costs: CostModel, timestamp=None) -> None:
        """
        Trades cash <-> BTC to move current_allocation toward
        target_allocation, at `price` adjusted for spread+slippage, minus
        the fee on notional traded. No-op if the target is already
        (numerically) met -- avoids phantom zero-size trades cluttering
        the trade log.
        """
        value = self.total_value(price)
        if value <= 0:
            return

        current_btc_value = self.btc * price
        target_btc_value = target_allocation * value
        delta_value = target_btc_value - current_btc_value  # positive = need to buy more BTC

        if abs(delta_value) < 1e-9:
            return

        impact = costs.total_price_impact_bps / 10_000.0
        if delta_value > 0:
            direction = "BUY"
            fill_price = price * (1 + impact)  # buying: pay a worse (higher) price
        else:
            direction = "SELL"
            fill_price = price * (1 - impact)  # selling: receive a worse (lower) price

        notional = abs(delta_value)
        fee = notional * (costs.fee_bps / 10_000.0)

        if direction == "BUY":
            # Fee comes out of the cash spent; the BTC bought reflects
            # only the post-fee notional at the (already unfavorable) fill price.
            cash_spent = notional
            btc_bought = (cash_spent - fee) / fill_price
            self.cash -= cash_spent
            self.btc += btc_bought
            btc_delta = btc_bought
        else:
            btc_sold = notional / price  # BTC quantity is based on pre-impact price*allocation math
            proceeds = btc_sold * fill_price
            proceeds_after_fee = proceeds - fee
            self.cash += proceeds_after_fee
            self.btc -= btc_sold
            btc_delta = -btc_sold

        self.trades.append(
            Trade(
                timestamp=timestamp,
                direction=direction,
                notional_before_fees=notional,
                fee_paid=fee,
                fill_price=fill_price,
                btc_delta=btc_delta,
            )
        )
