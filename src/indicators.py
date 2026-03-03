import numpy as np
import pandas as pd

def sma(s: pd.Series, window: int) -> pd.Series:
    return s.rolling(window=window, min_periods=window).mean()

def true_range(df: pd.DataFrame) -> pd.Series:
    prev_close = df["close"].shift(1)
    tr1 = (df["high"] - df["low"]).abs()
    tr2 = (df["high"] - prev_close).abs()
    tr3 = (df["low"] - prev_close).abs()
    return pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

def atr(df: pd.DataFrame, window: int) -> pd.Series:
    # Simple moving average ATR (good enough for MVP)
    tr = true_range(df)
    return tr.rolling(window=window, min_periods=window).mean()

def rolling_high(s: pd.Series, window: int) -> pd.Series:
    return s.rolling(window=window, min_periods=window).max()

def momentum_return(s: pd.Series, window: int) -> pd.Series:
    # Simple total return over window
    return s / s.shift(window) - 1.0
