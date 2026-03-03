import json
import os
import argparse

import pandas as pd

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
    p.add_argument("--regime-use-slope", type=int, default=0)  # 1=ON, 0=OFF

    # Costs overrides
    p.add_argument("--fee-rate", type=float, default=None)
    p.add_argument("--slippage-rate", type=float, default=None)

    # Output tag (for matrix runs)
    p.add_argument("--tag", type=str, default="default")

    # Trade window
    p.add_argument("--start-date", type=str, default=None)  # trading starts here
    p.add_argument("--end-date", type=str, default=None)

    # Warmup control
    p.add_argument("--warmup-days", type=int, default=None)  # if None => auto

    return p.parse_args()


def auto_warmup_days(
    breakout_days: int,
    mom_days: int,
    atr_days: int,
    regime_ma_weeks: int,
    regime_slope_weeks: int,
) -> int:
    """
    Warmup is ONLY for computing indicators/regime.
    We keep it simple and conservative (round-ish + buffer).
    """
    # weekly components in days (approx)
    regime_days = (regime_ma_weeks + regime_slope_weeks) * 7
    base = max(breakout_days, mom_days, atr_days, regime_days)
    return int(base + 30)  # small buffer


def main():
    args = parse_args()
    cfg = Config()

    # Resolve params (defaults from Config, override by CLI)
    breakout_days = args.breakout_days if args.breakout_days is not None else cfg.breakout_days
    mom_days = args.mom_days if args.mom_days is not None else cfg.mom_days
    atr_days = args.atr_days if args.atr_days is not None else cfg.atr_days
    stop_atr_mult = args.stop_atr_mult if args.stop_atr_mult is not None else cfg.stop_atr_mult
    risk_per_trade = args.risk_per_trade if args.risk_per_trade is not None else cfg.risk_per_trade

    regime_ma_weeks = args.regime_ma_weeks if args.regime_ma_weeks is not None else cfg.regime_ma_weeks
    regime_slope_weeks = args.regime_slope_weeks if args.regime_slope_weeks is not None else cfg.regime_slope_weeks

    # Regime slope switch
    if args.regime_use_slope not in (0, 1):
        raise ValueError("--regime-use-slope must be 0 or 1")
    use_slope = bool(args.regime_use_slope)

    fee_rate = args.fee_rate if args.fee_rate is not None else cfg.fee_rate
    slippage_rate = args.slippage_rate if args.slippage_rate is not None else cfg.slippage_rate

    start_date = args.start_date if args.start_date is not None else cfg.start_date
    end_date = args.end_date if args.end_date is not None else cfg.end_date

    # Warmup days
    warmup_days = args.warmup_days
    if warmup_days is None:
        warmup_days = auto_warmup_days(
            breakout_days=breakout_days,
            mom_days=mom_days,
            atr_days=atr_days,
            regime_ma_weeks=regime_ma_weeks,
            regime_slope_weeks=regime_slope_weeks,
        )

    # Load full data
    df = load_ohlc_csv(cfg.csv_path)

    # Determine calculation window (includes warmup before start_date)
    calc_start = None
    if start_date:
        sd = pd.to_datetime(start_date)
        calc_start = (sd - pd.Timedelta(days=warmup_days)).strftime("%Y-%m-%d")

    if calc_start:
        df_calc = df[df.index >= calc_start]
    else:
        df_calc = df

    if end_date:
        df_calc = df_calc[df_calc.index <= end_date]

    # Build indicators/regime on calc window (includes warmup)
    df2 = build_signals(df_calc, breakout_days=breakout_days, mom_days=mom_days, atr_days=atr_days)
    regime = compute_weekly_regime(
        df2,
        ma_weeks=regime_ma_weeks,
        slope_weeks=regime_slope_weeks,
        use_slope=use_slope,
    )

    # Trade window slice (THIS fixes the subperiod bias)
    df_trade = df2
    regime_trade = regime
    if start_date:
        df_trade = df_trade[df_trade.index >= start_date]
        regime_trade = regime_trade.reindex(df_trade.index)

    # Backtest
    eq_df, trades_df = run_backtest_btc_mvp(
        df=df_trade,
        regime=regime_trade,
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
            "regime_use_slope": int(use_slope),
            "fee_rate": fee_rate,
            "slippage_rate": slippage_rate,
            "start_date": start_date,
            "end_date": end_date,
            "warmup_days": warmup_days,
            "calc_start": calc_start,
        },
        "summary": summary,
    }
    print(json.dumps(payload, indent=2))

    print(f"\nWrote: {eq_path}")
    print(f"Wrote: {tr_path}")


if __name__ == "__main__":
    main()
