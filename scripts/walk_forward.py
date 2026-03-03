# scripts/walk_forward.py
import os
import json
import argparse
from dataclasses import replace
from datetime import datetime
from dateutil.relativedelta import relativedelta

import pandas as pd

from src.config import Config
from src.data_panel import load_panel
from src.backtest_multi import run_backtest_multi_mvp
from src.report import summarize


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--tag", type=str, default="wf_default")
    p.add_argument("--symbols", type=str, default="BTC,ETH,SPY,QQQ,GLD,TLT,USO")
    p.add_argument("--train_years", type=int, default=8)
    p.add_argument("--test_years", type=int, default=2)
    p.add_argument("--step_years", type=int, default=2)
    # warmup en jours de marché (approx) ; 800 ~ 3 ans calendaires ~ OK pour MA weekly + breakout 150
    p.add_argument("--warmup_days", type=int, default=800)
    return p.parse_args()


def _to_dt(s: str) -> pd.Timestamp:
    return pd.Timestamp(s).tz_localize(None)


def _dt_to_str(ts: pd.Timestamp) -> str:
    return ts.strftime("%Y-%m-%d")


def common_range(panel: dict[str, pd.DataFrame]) -> tuple[pd.Timestamp, pd.Timestamp]:
    common_idx = None
    for df in panel.values():
        idx = df.index
        common_idx = idx if common_idx is None else common_idx.intersection(idx)
    common_idx = common_idx.sort_values()
    return common_idx[0].normalize(), common_idx[-1].normalize()


def slice_panel(panel: dict[str, pd.DataFrame], start: pd.Timestamp, end: pd.Timestamp) -> dict[str, pd.DataFrame]:
    out = {}
    for sym, df in panel.items():
        out[sym] = df.loc[(df.index >= start) & (df.index <= end)].copy()
    return out


def filter_to_test(eq_df: pd.DataFrame, tr_df: pd.DataFrame, test_start: pd.Timestamp, test_end: pd.Timestamp):
    eq = eq_df.copy()
    if "Date" in eq.columns:
        # si equity_curve.csv a une colonne Date
        eq["Date"] = pd.to_datetime(eq["Date"])
        eq = eq.set_index("Date")
    eq = eq.loc[(eq.index >= test_start) & (eq.index <= test_end)].copy()

    tr = tr_df.copy()
    if len(tr) > 0:
        tr["entry_date"] = pd.to_datetime(tr["entry_date"])
        tr["exit_date"] = pd.to_datetime(tr["exit_date"])
        tr = tr.loc[(tr["entry_date"] >= test_start) & (tr["entry_date"] <= test_end)].copy()
    return eq, tr


def make_splits(start: pd.Timestamp, end: pd.Timestamp, train_years: int, test_years: int, step_years: int):
    splits = []
    train_start = start
    train_end = train_start + relativedelta(years=train_years)
    while True:
        test_start = train_end
        test_end = test_start + relativedelta(years=test_years) - relativedelta(days=1)
        if test_end > end:
            break
        splits.append((train_start, train_end, test_start, test_end))
        train_end = train_end + relativedelta(years=step_years)
    return splits


def main():
    args = parse_args()

    base = Config()
    symbols = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]
    sym_to_path = {s: f"data/raw/{s}.csv" for s in symbols}
    panel = load_panel(sym_to_path)

    # base range (intersection across symbols)
    gstart, gend = common_range(panel)

    splits = make_splits(gstart, gend, args.train_years, args.test_years, args.step_years)
    if not splits:
        raise RuntimeError(f"No splits possible on common range {gstart}..{gend} with train={args.train_years}y test={args.test_years}y")

    out_dir = f"data/outputs/{args.tag}"
    os.makedirs(out_dir, exist_ok=True)

    split_rows = []
    all_test_summaries = []

    # on force ton réglage actuel (breakout 150) si tu l’as mis dans Config ; sinon tu peux le set ici via replace()
    cfg = base  # frozen dataclass

    for i, (train_start, train_end, test_start, test_end) in enumerate(splits, start=1):
        # warmup: reculer de warmup_days avant test_start
        calc_start = (test_start - pd.Timedelta(days=args.warmup_days))

        # dataset fourni au moteur = warmup -> test_end
        sub_panel = slice_panel(panel, calc_start, test_end)

        eq_df, tr_df = run_backtest_multi_mvp(
            panel=sub_panel,
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

        # ne scorer que la fenêtre test
        eq_test, tr_test = filter_to_test(eq_df, tr_df, test_start, test_end)
        summ = summarize(eq_test, tr_test)

        row = {
            "split": i,
            "train_start": _dt_to_str(train_start),
            "train_end": _dt_to_str(train_end - relativedelta(days=1)),
            "test_start": _dt_to_str(test_start),
            "test_end": _dt_to_str(test_end),
            "warmup_start": _dt_to_str(calc_start),
            **summ,
        }
        split_rows.append(row)
        all_test_summaries.append(summ)

        # sauver equity/trades test par split (optionnel mais utile)
        eq_test.to_csv(f"{out_dir}/equity_split_{i}.csv")
        tr_test.to_csv(f"{out_dir}/trades_split_{i}.csv", index=False)

        print(f"[WF] split {i}: test {row['test_start']}..{row['test_end']} CAGR={row.get('CAGR')} PF={row.get('ProfitFactor')}")

    splits_df = pd.DataFrame(split_rows)
    splits_df.to_csv(f"{out_dir}/walk_forward_splits.csv", index=False)

    # résumé global simple sur les splits (médiane + min)
    agg = {
        "tag": args.tag,
        "symbols": symbols,
        "common_start": _dt_to_str(gstart),
        "common_end": _dt_to_str(gend),
        "train_years": args.train_years,
        "test_years": args.test_years,
        "step_years": args.step_years,
        "warmup_days": args.warmup_days,
        "splits": len(splits),
        "median_CAGR": float(splits_df["CAGR"].median()),
        "min_CAGR": float(splits_df["CAGR"].min()),
        "median_ProfitFactor": float(splits_df["ProfitFactor"].median()),
        "min_ProfitFactor": float(splits_df["ProfitFactor"].min()),
        "median_MaxDD": float(splits_df["MaxDD"].median()),
        "worst_MaxDD": float(splits_df["MaxDD"].min()),
    }
    with open(f"{out_dir}/walk_forward_summary.json", "w", encoding="utf-8") as f:
        json.dump(agg, f, indent=2)

    print("\n[WF] Saved:", f"{out_dir}/walk_forward_splits.csv")
    print("[WF] Saved:", f"{out_dir}/walk_forward_summary.json")


if __name__ == "__main__":
    main()
