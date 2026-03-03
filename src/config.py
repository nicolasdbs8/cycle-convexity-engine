from dataclasses import dataclass

@dataclass(frozen=True)
class Config:
    # Data
    csv_path: str = "data/BTCUSD_daily.csv"

    # Backtest window
    start_date: str | None = None
    end_date: str | None = None

    # Costs
    fee_rate: float = 0.001
    slippage_rate: float = 0.0005

    # Strategy params
    regime_ma_weeks: int = 100
    regime_slope_weeks: int = 20
    regime_use_slope: int = 0  # 1=ON, 0=OFF

    breakout_days: int = 180
    mom_days: int = 180

    atr_days: int = 20
    stop_atr_mult: float = 3.0

    risk_per_trade: float = 0.02
    initial_capital: float = 10_000.0

    # Portfolio (multi-asset)
    max_positions: int = 3
    risk_cap_total: float = 0.06
