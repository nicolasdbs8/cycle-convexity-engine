from dataclasses import dataclass
import pandas as pd

@dataclass
class Position:
    qty: float = 0.0
    entry_price: float = 0.0
    entry_date: pd.Timestamp | None = None
    stop_price: float = 0.0

@dataclass
class Portfolio:
    cash: float
    position: Position

    @property
    def is_in_market(self) -> bool:
        return self.position.qty > 0

    def equity(self, mark_price: float) -> float:
        return self.cash + self.position.qty * mark_price
