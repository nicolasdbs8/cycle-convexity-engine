import json
import os
import argparse

from src.config import Config
from src.data_loader import load_ohlc_csv
from src.strategy import build_signals
from src.regime import compute_weekly_regime
from src.backtest import run_backtest_btc_mvp
from src.report import summarize


def parse_args():
    p = argparse.ArgumentParser(description="cycle-convexity-engine BTC MVP backtest")

    # Strategy overrides
    p.add_argument("--breakout-days", type=int, default=None)
    p.add_argument("--mom-days", type=int, default=None)
    p.add_argument("--atr-days", type=int, default=None)
    p.add_argument("--stop-atr-mult", type=float, default=None)
    p.add_argument("--risk-per-trade", type=float, default=None)

    # Regime overrides
    p.add_argument("--regime-ma-weeks", type=int, default=None)
    p.add_argument("--regime-slope-weeks", type=int, default=None)

    # Costs overrides
    p.add_argument("--fee-rate", type=float, default=None)
    p.add_argument("--slippage-rate", type=float, default=None)

    # Output tag (for matrix runs)
    p.add_argument("--tag", type=str, default="default")

    # Optional window
    p.add_argument("--start-date", type=str, default=None)
    p.add_argument("--end-date", type=str, default=None)

    return p.parse_args()


def main():
    args = parse_args()
    cfg = Config()

    # Override config if CLI args provided
    breakout_days = args.breakout_days if args.breakout_days is not None else cfg.breakout_days
    mom_days = args.mom_days if args.mom_days is not None else cfg.mom_days
    atr_days = args.atr_days if args.atr_days is not None else cfg.atr_days
    stop_atr_mult = args.stop_atr_mult if args.stop_atr_mult is not None else cfg.stop_atr_mult
    risk_per_trade = args.risk_per_trade if args.risk_per_trade is not None else cfg.risk_per_trade

    regime_ma_weeks = args.regime_ma_weeks if args.regime_ma_weeks is not None else cfg.regime_ma_weeks
    regime_slope_weeks = args.regime_slope_weeks if args.regime_slope_weeks is not None else cfg.regime_slope_weeks

    fee_rate = args.fee_rate if args.fee_rate is not None else cfg.fee_rate
    slippage_rate = args.slippage_rate if args.slippage_rate is not None else cfg.slippage_rate

    start_date = args.start_date if args.start_date is not None else cfg.start_date
    end_date = args.end_date if args.end_date is not None else cfg.end_date

    # Load data
    df = load_ohlc_csv(cfg.csv_path)
    if start_date:
        df = df[df.index >= start_date]
    if end_date:
        df = df[df.index <= end_date]

    # Build indicators
    df2 = build_signals(df, breakout_days=breakout_days, mom_days=mom_days, atr_days=atr_days)

    # Regime (daily-aligned)
    regime = compute_weekly_regime(df2, ma_weeks=regime_ma_weeks, slope_weeks=regime_slope_weeks)

    # Backtest
    eq_df, trades_df = run_backtest_btc_mvp(
        df=df2,
        regime=regime,
        fee_rate=fee_rate,
        slippage_rate=slippage_rate,
        initial_capital=cfg.initial_capital,
        risk_per_trade=risk_per_trade,
        stop_atr_mult=stop_atr_mult,
    )

    # Outputs (tagged)
    out_dir = f"data/outputs/{args.tag}"
    os.makedirs(out_dir, exist_ok=True)

    eq_path = f"{out_dir}/equity_curve.csv"
    tr_path = f"{out_dir}/trades.csv"
    eq_df.to_csv(eq_path)
    trades_df.to_csv(tr_path, index=False)

    summary = summarize(eq_df, trades_df)

    # Print summary + run params (so logs are self-contained)
    payload = {
        "tag": args.tag,
        "params": {
            "breakout_days": breakout_days,
            "mom_days": mom_days,
            "atr_days": atr_days,
            "stop_atr_mult": stop_atr_mult,
            "risk_per_trade": risk_per_trade,
            "regime_ma_weeks": regime_ma_weeks,
            "regime_slope_weeks": regime_slope_weeks,
            "fee_rate": fee_rate,
            "slippage_rate": slippage_rate,
            "start_date": start_date,
            "end_date": end_date,
        },
        "summary": summary,
    }
    print(json.dumps(payload, indent=2))

    print(f"\nWrote: {eq_path}")
    print(f"Wrote: {tr_path}")


if __name__ == "__main__":
    main()
