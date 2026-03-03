from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict
import pandas as pd

@dataclass
class Position:
    symbol: str
    qty: float
    entry_price: float
    entry_date: pd.Timestamp
    stop_price: float
    entry_fee: float = 0.0

    def mv(self, price: float) -> float:
        return self.qty * price

    def stop_risk_cash(self) -> float:
        return max(0.0, self.entry_price - self.stop_price) * self.qty

@dataclass
class PortfolioMulti:
    cash: float
    positions: Dict[str, Position] = field(default_factory=dict)

    def has(self, symbol: str) -> bool:
        return symbol in self.positions

    def equity(self, marks: Dict[str, float]) -> float:
        eq = self.cash
        for sym, pos in self.positions.items():
            eq += pos.mv(marks[sym])
        return eq

    def total_stop_risk(self) -> float:
        return sum(p.stop_risk_cash() for p in self.positions.values())

    def can_open(self, symbol: str, max_positions: int) -> bool:
        return (symbol not in self.positions) and (len(self.positions) < max_positions)

    def open_long(self, symbol: str, qty: float, px: float, dt: pd.Timestamp, stop: float, fee: float):
        total = qty * px + fee
        if total > self.cash + 1e-9:
            return False
        self.cash -= total
        self.positions[symbol] = Position(symbol, qty, px, dt, stop, fee)
        return True

    def close_long(self, symbol: str, px: float, dt: pd.Timestamp, fee: float) -> Position:
        pos = self.positions.pop(symbol)
        self.cash += pos.qty * px - fee
        return pos
