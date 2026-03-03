import os
import itertools
import pandas as pd

from src.config import Config
from src.data_panel import load_panel
from src.backtest_multi import run_backtest_multi_mvp
from src.report import summarize

# === PARAM GRID ===
BREAKOUTS = [150, 180, 220]
STOPS = [2.0, 2.5, 3.0]
REGIME_MA = [40, 52, 75]
RISK_PER_TRADE = [0.015, 0.02]
RISK_CAP = [0.045, 0.06, 0.075]

SYMBOLS = ["BTC", "ETH", "SPY", "QQQ", "GLD", "TLT", "USO"]

def main():

    cfg = Config()

    sym_to_path = {s: f"data/raw/{s}.csv" for s in SYMBOLS}
    panel = load_panel(sym_to_path)

    results = []

    grid = itertools.product(
        BREAKOUTS,
        STOPS,
        REGIME_MA,
        RISK_PER_TRADE,
        RISK_CAP,
    )

    for breakout, stop, regime_ma, rpt, rcap in grid:

        # Skip incoherent combos
        if rpt * cfg.max_positions > rcap:
            continue

        cfg.breakout_days = breakout
        cfg.stop_atr_mult = stop
        cfg.regime_ma_weeks = regime_ma
        cfg.risk_per_trade = rpt
        cfg.risk_cap_total = rcap

        eq_df, tr_df = run_backtest_multi_mvp(
            panel=panel,
            fee_rate=cfg.fee_rate,
            slippage_rate=cfg.slippage_rate,
            initial_capital=cfg.initial_capital,
            risk_per_trade=cfg.risk_per_trade,
            risk_cap_total=cfg.risk_cap_total,
            max_positions=cfg.max_positions,
            breakout_days=cfg.breakout_days,
            mom_days=cfg.mom_days,
            atr_days=cfg.atr_days,
            stop_atr_mult=cfg.stop_atr_mult,
            regime_ma_weeks=cfg.regime_ma_weeks,
            regime_slope_weeks=cfg.regime_slope_weeks,
            regime_use_slope=bool(cfg.regime_use_slope),
        )

        summary = summarize(eq_df, tr_df)

        results.append({
            "breakout": breakout,
            "stop": stop,
            "regime_ma": regime_ma,
            "risk_per_trade": rpt,
            "risk_cap": rcap,
            **summary
        })

        print("Done:", breakout, stop, regime_ma, rpt, rcap)

    df = pd.DataFrame(results)

    os.makedirs("data/outputs", exist_ok=True)
    df.to_csv("data/outputs/sweep_results.csv", index=False)

    print("\nSweep finished.")
    print("Results saved to data/outputs/sweep_results.csv")

if __name__ == "__main__":
    main()
