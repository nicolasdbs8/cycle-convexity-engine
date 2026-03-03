from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional, Iterable

import pandas as pd


@dataclass
class Position:
    symbol: str
    qty: float
    entry_price: float
    entry_date: pd.Timestamp
    stop_price: float
    entry_fee: float = 0.0

    def market_value(self, mark_price: float) -> float:
        return self.qty * mark_price


@dataclass
class Portfolio:
    cash: float
    positions: Dict[str, Position] = field(default_factory=dict)

    # --- convenience ---
    def has_position(self, symbol: str) -> bool:
        return symbol in self.positions and self.positions[symbol].qty > 0

    def symbols(self) -> Iterable[str]:
        return self.positions.keys()

    # --- valuation ---
    def equity(self, marks: Dict[str, float]) -> float:
        eq = self.cash
        for sym, pos in self.positions.items():
            if sym not in marks:
                raise KeyError(f"Missing mark price for {sym}")
            eq += pos.market_value(marks[sym])
        return eq

    def gross_exposure(self, marks: Dict[str, float]) -> float:
        exp = 0.0
        for sym, pos in self.positions.items():
            exp += pos.market_value(marks[sym])
        return exp

    # --- risk budget ---
    def total_stop_risk(self) -> float:
        """
        Total $ risk to stops (sum over open positions): qty * (entry - stop)
        Assumes long-only and stop < entry.
        """
        risk = 0.0
        for pos in self.positions.values():
            per_unit = max(0.0, pos.entry_price - pos.stop_price)
            risk += pos.qty * per_unit
        return risk

    def can_open_position(
        self,
        symbol: str,
        max_positions: int,
        risk_cap_total: float,
        new_pos_stop_risk: float,
        equity_now: float,
    ) -> bool:
        """
        risk_cap_total is a fraction of equity (e.g. 0.06 for 6%).
        new_pos_stop_risk is absolute $ risk of the candidate position (qty*(entry-stop)).
        """
        if self.has_position(symbol):
            return False
        if len(self.positions) >= max_positions:
            return False
        if equity_now <= 0:
            return False

        budget = risk_cap_total * equity_now
        return (self.total_stop_risk() + new_pos_stop_risk) <= budget

    # --- execution primitives ---
    def open_long(
        self,
        symbol: str,
        qty: float,
        entry_price: float,
        entry_date: pd.Timestamp,
        stop_price: float,
        fee: float = 0.0,
    ) -> None:
        cost = qty * entry_price + fee
        if cost > self.cash + 1e-9:
            raise ValueError(f"Not enough cash to open {symbol}: need {cost}, have {self.cash}")
        self.cash -= cost
        self.positions[symbol] = Position(
            symbol=symbol,
            qty=qty,
            entry_price=entry_price,
            entry_date=entry_date,
            stop_price=stop_price,
            entry_fee=fee,
        )

    def close_long(
        self,
        symbol: str,
        exit_price: float,
        exit_date: pd.Timestamp,
        fee: float = 0.0,
    ) -> Position:
        if not self.has_position(symbol):
            raise KeyError(f"No open position for {symbol}")
        pos = self.positions.pop(symbol)
        proceeds = pos.qty * exit_price - fee
        self.cash += proceeds
        return pos

    def update_stop(self, symbol: str, new_stop: float) -> None:
        if not self.has_position(symbol):
            raise KeyError(f"No open position for {symbol}")
        # long-only: stop can only go up
        self.positions[symbol].stop_price = max(self.positions[symbol].stop_price, new_stop)
