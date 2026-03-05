import subprocess
import json
import pandas as pd
from pathlib import Path

# -----------------------------
# Configuration
# -----------------------------

UNIVERSE = [
    "BTC","ETH","BNB","SOL","XRP","ADA","DOGE","TRX","LINK",
    "SPY","QQQ","IWM","EFA","EEM","GLD","TLT","IEF","SHY",
    "XLK","XLF","XLE","XLY","XLI","XLP","XLV","XLB",
    "DBC","EWJ","EWU","FXI","EWT","INDA"
]

TAG_BASE = "ablation_baseline"
OUTPUT_DIR = Path("data/outputs")


# -----------------------------
# Helpers
# -----------------------------

def run_backtest(symbols, tag):

    symbols_str = ",".join(symbols)

    cmd = [
        "python",
        "run_backtest_multi.py",
        "--tag",
        tag,
        "--symbols",
        symbols_str
    ]

    subprocess.run(cmd, check=True)


def load_summary(tag):

    path = OUTPUT_DIR / tag / "summary.json"

    with open(path) as f:
        return json.load(f)


# -----------------------------
# Baseline
# -----------------------------

print("Running baseline...")

run_backtest(UNIVERSE, TAG_BASE)

baseline = load_summary(TAG_BASE)

baseline_metrics = {
    "CAGR": baseline["CAGR"],
    "MaxDD": baseline["MaxDD"],
    "ProfitFactor": baseline["ProfitFactor"],
    "NumTrades": baseline["NumTrades"],
}

print("Baseline:", baseline_metrics)


# -----------------------------
# Ablation loop
# -----------------------------

results = []

for sym in UNIVERSE:

    print(f"Testing removal of {sym}")

    reduced_universe = [s for s in UNIVERSE if s != sym]

    tag = f"ablation_minus_{sym}"

    run_backtest(reduced_universe, tag)

    summary = load_summary(tag)

    row = {
        "symbol_removed": sym,

        "CAGR": summary["CAGR"],
        "MaxDD": summary["MaxDD"],
        "ProfitFactor": summary["ProfitFactor"],
        "NumTrades": summary["NumTrades"],

        "delta_CAGR": summary["CAGR"] - baseline_metrics["CAGR"],
        "delta_MaxDD": summary["MaxDD"] - baseline_metrics["MaxDD"],
        "delta_PF": summary["ProfitFactor"] - baseline_metrics["ProfitFactor"],
        "delta_Trades": summary["NumTrades"] - baseline_metrics["NumTrades"],
    }

    results.append(row)


# -----------------------------
# Save results
# -----------------------------

df = pd.DataFrame(results)

df = df.sort_values("delta_CAGR", ascending=False)

output_path = OUTPUT_DIR / "universe_ablation_results.csv"

df.to_csv(output_path, index=False)

print("\nSaved results to:", output_path)
print(df)
