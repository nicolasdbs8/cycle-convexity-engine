import json
import pandas as pd
from pathlib import Path

OUTPUT = Path("data/outputs")

rows = []

for d in OUTPUT.iterdir():

    if not d.is_dir():
        continue

    summary_file = d / "summary.json"

    if not summary_file.exists():
        continue

    with open(summary_file) as f:
        data = json.load(f)

    summary = data.get("summary", {})

    if not summary:
        continue

    rows.append({
        "tag": d.name,
        "CAGR": summary.get("CAGR"),
        "MaxDD": summary.get("MaxDD"),
        "ProfitFactor": summary.get("ProfitFactor"),
        "NumTrades": summary.get("NumTrades"),
        "HitRate": summary.get("HitRate"),
    })

df = pd.DataFrame(rows)

if df.empty:
    raise ValueError("No summaries found in data/outputs")

df = df.sort_values("CAGR", ascending=False)

out = OUTPUT / "ablation_summary.csv"

df.to_csv(out, index=False)

print("Saved:", out)
print(df)
