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
    """Compact performance summary + anti-lottery diagnostics.

    Adds:
      - Top1/Top3/Top5 PnL concentration (abs) to quantify tail dependency.
      - R-multiple distribution stats if 'r_multiple' exists.
    """
    if eq_df is None or eq_df.empty or "equity" not in eq_df.columns:
        return {
            "StartEquity": 0.0,
            "EndEquity": 0.0,
            "CAGR": 0.0,
            "MaxDD": 0.0,
            "NumTrades": int(len(trades_df)) if trades_df is not None else 0,
        }

    eq = eq_df["equity"]

    summary = {
        "StartEquity": float(eq.iloc[0]),
        "EndEquity": float(eq.iloc[-1]),
        "CAGR": cagr(eq),
        "MaxDD": max_drawdown(eq),
        "NumTrades": int(len(trades_df)) if trades_df is not None else 0,
    }

    if trades_df is None or len(trades_df) == 0:
        return summary

    wins = trades_df["pnl"] > 0
    summary["HitRate"] = float(wins.mean())
    gross_win = float(trades_df.loc[wins, "pnl"].sum())
    gross_loss = float(-trades_df.loc[~wins, "pnl"].sum())
    summary["ProfitFactor"] = float(gross_win / gross_loss) if gross_loss > 0 else float(np.inf)

    # Gain concentration (anti-lottery check)
    pnl = trades_df["pnl"].astype(float)
    abs_total = float(np.abs(pnl).sum())
    if abs_total > 0:
        abs_sorted = np.abs(pnl).sort_values(ascending=False).values
        summary["Top1_PnL_abs_pct"] = float(abs_sorted[0] / abs_total) if len(abs_sorted) >= 1 else 0.0
        summary["Top3_PnL_abs_pct"] = float(abs_sorted[: min(3, len(abs_sorted))].sum() / abs_total)
        summary["Top5_PnL_abs_pct"] = float(abs_sorted[: min(5, len(abs_sorted))].sum() / abs_total)

    # R-multiple distribution stats (if present)
    if "r_multiple" in trades_df.columns:
        r = trades_df["r_multiple"].astype(float).replace([np.inf, -np.inf], np.nan).dropna()
        if len(r) > 0:
            summary["AvgR"] = float(r.mean())
            summary["MedR"] = float(r.median())
            summary["P10R"] = float(r.quantile(0.10))
            summary["P90R"] = float(r.quantile(0.90))

    return summary
