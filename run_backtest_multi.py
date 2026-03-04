import os, json, argparse
from src.config import Config
from src.data_panel import load_panel
from src.sleeves import run_backtest_core_satellite
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

    # NEW: core/satellite sleeves orchestrator (equity total + trades with 'sleeve')
    eq_df, tr_df = run_backtest_core_satellite(panel=panel, cfg=cfg, symbols=symbols)

    out_dir = f"data/outputs/{args.tag}"
    os.makedirs(out_dir, exist_ok=True)
    eq_df.to_csv(f"{out_dir}/equity_curve.csv")
    tr_df.to_csv(f"{out_dir}/trades.csv", index=False)

    summary = summarize(eq_df, tr_df)
    payload = {"tag": args.tag, "symbols": symbols, "summary": summary}
    print(json.dumps(payload, indent=2))

if __name__ == "__main__":
    main()
