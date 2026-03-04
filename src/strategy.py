import pandas as pd
from .indicators import rolling_high, atr, momentum_return

def build_signals(
    df: pd.DataFrame,
    breakout_days: int,
    mom_days: int,
    atr_days: int,
    exit_ll_days: int = 50,
):
    """
    Adds indicator columns needed for the MVP:
      - hh_prev: rolling HH (prior days) for breakout entry
      - mom: simple return over mom_days
      - atr
      - ll_prev: rolling LL (prior days) for Donchian exit (trend break)
    """
    out = df.copy()

    # Entry breakout (anti-lookahead)
    out["hh"] = rolling_high(out["high"], breakout_days)
    out["hh_prev"] = out["hh"].shift(1)

    out["mom"] = momentum_return(out["close"], mom_days)
    out["atr"] = atr(out, atr_days)

    # Donchian exit (anti-lookahead): use PRIOR LL to decide exit at next open
    ll = out["low"].rolling(exit_ll_days, min_periods=exit_ll_days).min()
    out["ll_prev"] = ll.shift(1)

    return out
