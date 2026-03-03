import os, json, argparse
from src.config import Config
from src.data_panel import load_panel
from src.backtest_multi import run_backtest_multi_mvp
from src.report import summarize

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--tag", type=str, default="multi_default")
    p.add_argument("--symbols", type=str, default="BTC,ETH")  # comma list
    return p.parse_args()

def main():
    args = parse_args()
    cfg = Config()

    symbols = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]
    sym_to_path = {s: f"data/raw/{s}.csv" for s in symbols}

    panel = load_panel(sym_to_path)

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

    out_dir = f"data/outputs/{args.tag}"
    os.makedirs(out_dir, exist_ok=True)
    eq_df.to_csv(f"{out_dir}/equity_curve.csv")
    tr_df.to_csv(f"{out_dir}/trades.csv", index=False)

    summary = summarize(eq_df, tr_df)
    payload = {"tag": args.tag, "symbols": symbols, "summary": summary}
    print(json.dumps(payload, indent=2))

if __name__ == "__main__":
    main()
