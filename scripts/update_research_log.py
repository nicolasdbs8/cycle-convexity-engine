# scripts/update_research_log.py
import json
import glob
from pathlib import Path
from datetime import datetime


def load_json(p: Path):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def main():
    root = Path(".")
    out_files = sorted(root.glob("data/outputs/**/summary.json"))

    rows = []
    for p in out_files:
        tag = p.parent.name
        data = load_json(p)
        if not data:
            continue

        # try to extract a stable shape
        summary = data.get("summary", data)  # depending on your file format
        meta = data.get("params", data.get("meta", {}))

        mtime = datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")

        rows.append(
            {
                "tag": tag,
                "mtime": mtime,
                "StartEquity": summary.get("StartEquity"),
                "EndEquity": summary.get("EndEquity"),
                "CAGR": summary.get("CAGR"),
                "MaxDD": summary.get("MaxDD"),
                "NumTrades": summary.get("NumTrades"),
                "HitRate": summary.get("HitRate"),
                "ProfitFactor": summary.get("ProfitFactor"),
                "params": meta,
            }
        )

    # sort newest first
    rows.sort(key=lambda r: r["mtime"], reverse=True)

    lines = []
    lines.append("# Research Log")
    lines.append("")
    lines.append("Generated automatically from `data/outputs/**/summary.json`. Do not edit manually.")
    lines.append("")

    if not rows:
        lines.append("_No results found._")
    else:
        for r in rows:
            lines.append(f"## {r['tag']}")
            lines.append(f"- updated: `{r['mtime']}`")
            lines.append(f"- StartEquity: {r['StartEquity']}")
            lines.append(f"- EndEquity: {r['EndEquity']}")
            lines.append(f"- CAGR: {r['CAGR']}")
            lines.append(f"- MaxDD: {r['MaxDD']}")
            lines.append(f"- NumTrades: {r['NumTrades']}")
            lines.append(f"- HitRate: {r['HitRate']}")
            lines.append(f"- ProfitFactor: {r['ProfitFactor']}")
            # Keep params short
            if r["params"]:
                # show only a few key params if present
                keys = ["breakout_days", "stop_atr_mult", "regime_ma_weeks", "risk_per_trade", "risk_cap_total", "fee_rate", "slippage_rate"]
                shown = {k: r["params"].get(k) for k in keys if k in r["params"]}
                if shown:
                    lines.append(f"- params: `{shown}`")
            lines.append("")

    Path("RESEARCH_LOG.md").write_text("\n".join(lines).strip() + "\n", encoding="utf-8")
    print("Wrote RESEARCH_LOG.md")


if __name__ == "__main__":
    main()
