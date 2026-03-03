import json
from src.config import Config
from src.data_loader import load_ohlc_csv
from src.strategy import build_signals
from src.regime import compute_weekly_regime
from src.backtest import run_backtest_btc_mvp
from src.report import summarize

def main():
    cfg = Config()

    df = load_ohlc_csv(cfg.csv_path)

    if cfg.start_date:
        df = df[df.index >= cfg.start_date]
    if cfg.end_date:
        df = df[df.index <= cfg.end_date]

    # Build indicators
    df2 = build_signals(df, breakout_days=cfg.breakout_days, mom_days=cfg.mom_days, atr_days=cfg.atr_days)

    # Regime (daily-aligned)
    regime = compute_weekly_regime(df2, ma_weeks=cfg.regime_ma_weeks, slope_weeks=cfg.regime_slope_weeks)

    # Backtest
    eq_df, trades_df = run_backtest_btc_mvp(
        df=df2,
        regime=regime,
        fee_rate=cfg.fee_rate,
        slippage_rate=cfg.slippage_rate,
        initial_capital=cfg.initial_capital,
        risk_per_trade=cfg.risk_per_trade,
        stop_atr_mult=cfg.stop_atr_mult,
    )

    # Outputs
    out_dir = "data/outputs"
    import os
    os.makedirs(out_dir, exist_ok=True)

    eq_path = f"{out_dir}/equity_curve.csv"
    tr_path = f"{out_dir}/trades.csv"
    eq_df.to_csv(eq_path)
    trades_df.to_csv(tr_path, index=False)

    summary = summarize(eq_df, trades_df)
    print(json.dumps(summary, indent=2))

    print(f"\nWrote: {eq_path}")
    print(f"Wrote: {tr_path}")

if __name__ == "__main__":
    main()
