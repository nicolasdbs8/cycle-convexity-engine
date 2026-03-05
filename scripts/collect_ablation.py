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
        s = json.load(f)

    rows.append({
        "tag": d.name,
        "CAGR": s.get("CAGR"),
        "MaxDD": s.get("MaxDD"),
        "ProfitFactor": s.get("ProfitFactor"),
        "NumTrades": s.get("NumTrades"),
        "HitRate": s.get("HitRate"),
    })

df = pd.DataFrame(rows)

df = df.sort_values("CAGR", ascending=False)

out = OUTPUT / "ablation_summary.csv"

df.to_csv(out, index=False)

print("Saved:", out)
print(df)
