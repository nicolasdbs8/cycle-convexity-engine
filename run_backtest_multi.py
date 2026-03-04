import os, json, argparse
from src.config import Config
from src.data_panel import load_panel
from src.sleeves import run_backtest_core_satellite
from src.report import summarize


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--tag", type=str, default="multi_default")
    p.add_argument("--symbols", type=str, default="BTC,ETH")  # comma list
    p.add_argument("--start", type=str, default=None)         # YYYY-MM-DD
    p.add_argument("--end", type=str, default=None)           # YYYY-MM-DD
    return p.parse_args()


def main():
    args = parse_args()
    cfg = Config()

    symbols = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]
    sym_to_path = {s: f"data/raw/{s}.csv" for s in symbols}

    panel = load_panel(sym_to_path, start_date=args.start, end_date=args.end)

    eq_df, tr_df, eq_core, eq_sat = run_backtest_core_satellite(
        panel=panel,
        cfg=cfg,
        symbols=symbols,
    )

    out_dir = f"data/outputs/{args.tag}"
    os.makedirs(out_dir, exist_ok=True)

    eq_df.to_csv(f"{out_dir}/equity_curve.csv")

    if eq_core is not None:
        eq_core.to_csv(f"{out_dir}/equity_core.csv")
    if eq_sat is not None:
        eq_sat.to_csv(f"{out_dir}/equity_sat.csv")

    tr_df.to_csv(f"{out_dir}/trades.csv", index=False)

    summary = summarize(eq_df, tr_df)

    if "sleeve" in tr_df.columns and len(tr_df) > 0:
        summary["TradesBySleeve"] = tr_df["sleeve"].value_counts().to_dict()
    else:
        summary["TradesBySleeve"] = {"core": 0, "sat": 0}

    payload = {"tag": args.tag, "symbols": symbols, "summary": summary}
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
