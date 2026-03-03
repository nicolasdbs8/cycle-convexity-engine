import numpy as np
import pandas as pd

def max_drawdown(equity: pd.Series) -> float:
    peak = equity.cummax()
    dd = equity / peak - 1.0
    return float(dd.min())

def cagr(equity: pd.Series) -> float:
    if len(equity) < 2:
        return 0.0
    start = float(equity.iloc[0])
    end = float(equity.iloc[-1])
    if start <= 0:
        return 0.0
    days = (equity.index[-1] - equity.index[0]).days
    years = days / 365.25 if days > 0 else 0.0
    if years <= 0:
        return 0.0
    return (end / start) ** (1.0 / years) - 1.0

def summarize(eq_df: pd.DataFrame, trades_df: pd.DataFrame) -> dict:
    eq = eq_df["equity"]
    summary = {
        "StartEquity": float(eq.iloc[0]),
        "EndEquity": float(eq.iloc[-1]),
        "CAGR": cagr(eq),
        "MaxDD": max_drawdown(eq),
        "NumTrades": int(len(trades_df)),
    }
    if len(trades_df) > 0:
        wins = trades_df["pnl"] > 0
        summary["HitRate"] = float(wins.mean())
        gross_win = trades_df.loc[wins, "pnl"].sum()
        gross_loss = -trades_df.loc[~wins, "pnl"].sum()
        summary["ProfitFactor"] = float(gross_win / gross_loss) if gross_loss > 0 else np.inf
    return summary
