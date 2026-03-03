import pandas as pd
from .indicators import rolling_high, atr, momentum_return

def build_signals(df: pd.DataFrame, breakout_days: int, mom_days: int, atr_days: int):
    """
    Adds indicator columns needed for the MVP:
      - breakout_level: rolling HH (prior days)
      - mom: simple return over mom_days
      - atr
    """
    out = df.copy()
    # Use prior HH to avoid lookahead: breakout if close > HH_prev
    out["hh"] = rolling_high(out["high"], breakout_days)
    out["hh_prev"] = out["hh"].shift(1)

    out["mom"] = momentum_return(out["close"], mom_days)
    out["atr"] = atr(out, atr_days)

    return out
