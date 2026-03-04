from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    # Data
    csv_path: str = "data/BTCUSD_daily.csv"

    # Backtest window (optional)
    start_date: str | None = None
    end_date: str | None = None

    # Costs
    fee_rate: float = 0.001
    slippage_rate: float = 0.0005

    # Strategy params
    regime_ma_weeks: int = 26
    regime_slope_weeks: int = 20
    regime_use_slope: int = 1  # 1=ON, 0=OFF

    breakout_days: int = 120
    mom_days: int = 180

    atr_days: int = 20
    stop_atr_mult: float = 2.5

    # Risk (base)
    risk_per_trade: float = 0.02
    initial_capital: float = 10_000.0

    # Portfolio (multi-asset)
    max_positions: int = 3
    risk_cap_total: float = 0.06

    # --- Core / Satellite sleeves ---
    core_weight: float = 0.90
    sat_weight: float = 0.10

    # Crypto candidates (the “satellite candidate set”)
    crypto_symbols: tuple[str, ...] = (
        "BTC", "ETH", "BNB", "SOL", "XRP", "ADA", "DOGE", "TRX", "LINK", "TON"
    )

    # --- Volatility targeting (per sleeve) ---
    # If None: disabled for that sleeve.
    core_target_vol_annual: float | None = 0.10
    sat_target_vol_annual: float | None = 0.20

    # Realized-vol window and scaler clamps.
    # vol_scaler_max=1.0 => no leverage (only scales DOWN risk when vol is high)
    vol_window_days: int = 30
    vol_scaler_min: float = 0.25
    vol_scaler_max: float = 1.0
