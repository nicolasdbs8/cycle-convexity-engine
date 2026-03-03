from dataclasses import dataclass

@dataclass(frozen=True)
class Config:
    # Data
    csv_path: str = "data/BTCUSD_daily.csv"

    # Backtest window
    start_date: str | None = None  # e.g. "2013-01-01"
    end_date: str | None = None    # e.g. "2025-12-31"

    # Costs
    fee_rate: float = 0.001        # 0.10%
    slippage_rate: float = 0.0005  # 0.05%

    # Strategy params (round numbers, non-optimized)
    regime_ma_weeks: int = 100      # weekly MA
    regime_slope_weeks: int = 20    # slope window in weeks

    breakout_days: int = 180
    mom_days: int = 180             # keep simple: close/close[n]-1

    atr_days: int = 20
    stop_atr_mult: float = 2.0

    risk_per_trade: float = 0.02
    initial_capital: float = 10_000.0

    # Execution
    allow_one_position: bool = True
