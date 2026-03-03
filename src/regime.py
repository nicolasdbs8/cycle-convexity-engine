import pandas as pd
from .indicators import sma

def compute_weekly_regime(
    daily: pd.DataFrame,
    ma_weeks: int,
    slope_weeks: int,
    use_slope: bool = True,
) -> pd.Series:
    """
    Regime ON if:
      weekly close > weekly SMA(ma_weeks)
      and (optionally) SMA slope over slope_weeks is positive
    Returns a daily-aligned boolean Series (forward-filled from weekly).
    """
    weekly = daily["close"].resample("W-FRI").last().dropna()

    ma = sma(weekly, ma_weeks)

    if use_slope:
        slope = ma - ma.shift(slope_weeks)
        regime_weekly = (weekly > ma) & (slope > 0)
    else:
        regime_weekly = (weekly > ma)

    regime_daily = regime_weekly.reindex(daily.index, method="ffill").fillna(False)
    return regime_daily
