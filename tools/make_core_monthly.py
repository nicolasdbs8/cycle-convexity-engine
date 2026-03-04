# tools/make_core_monthly.py
import argparse
import os
from dataclasses import dataclass
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd

DEFAULT_CANDIDATES = [
    # Core ETFs (tu peux ajuster)
    "DBC","SPY","QQQ","IWM","EFA","EEM",
    "TLT","IEF","SHY","LQD","HYG",
    "GLD","SLV","USO","UNG","VNQ","XLF",
    "XLE","XLK","XLV","XLI",
]

REQUIRED = {"open", "high", "low", "close"}

def _normalize_cols(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip().lower() for c in df.columns]
    # handle Yahoo CSV: Date column can be "Date" (index) or "date"
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
        df = df.set_index("date")
    elif df.index.name and str(df.index.name).lower() in {"date", "datetime"}:
        df.index = pd.to_datetime(df.index)
    else:
        # last resort: assume first col is date
        if len(df.columns) >= 1:
            df.iloc[:, 0] = pd.to_datetime(df.iloc[:, 0])
            df = df.set_index(df.columns[0])
    df.index = pd.to_datetime(df.index).tz_localize(None)
    return df

def _read_ohlcv(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df = _normalize_cols(df)

    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        raise ValueError(f"{path}: missing columns: {missing}")

    # standardize names to open/high/low/close/volume (lowercase)
    cols = ["open","high","low","close"]
    if "volume" in df.columns:
        cols.append("volume")
    df = df[cols].sort_index()
    return df

def _last_date_before(df: pd.DataFrame, dt: pd.Timestamp) -> Optional[pd.Timestamp]:
    # last row strictly before dt
    idx = df.index[df.index < dt]
    if len(idx) == 0:
        return None
    return pd.Timestamp(idx[-1])

def _month_starts(min_dt: pd.Timestamp, max_dt: pd.Timestamp) -> List[pd.Timestamp]:
    start = min_dt.to_period("M").to_timestamp()
    end = max_dt.to_period("M").to_timestamp()
    months = pd.date_range(start=start, end=end, freq="MS")
    return [pd.Timestamp(x) for x in months]

def _momentum_asof(df: pd.DataFrame, asof: pd.Timestamp, mom_bars: int) -> Optional[float]:
    # use close-to-close momentum over mom_bars (trading days)
    loc = df.index.get_indexer([asof], method="pad")[0]
    if loc < mom_bars:
        return None
    c0 = float(df["close"].iloc[loc - mom_bars])
    c1 = float(df["close"].iloc[loc])
    if c0 <= 0:
        return None
    return (c1 / c0) - 1.0

def _liquidity_ok_asof(df: pd.DataFrame, asof: pd.Timestamp, liq_window_bars: int, min_median_dvol_usd: float) -> bool:
    if min_median_dvol_usd <= 0:
        return True
    if "volume" not in df.columns:
        return False
    loc = df.index.get_indexer([asof], method="pad")[0]
    if loc < liq_window_bars:
        return False
    window = df.iloc[loc - liq_window_bars + 1 : loc + 1]
    dvol = window["close"] * window["volume"]
    med = float(dvol.median(skipna=True)) if dvol.notna().any() else float("nan")
    if not (med == med):  # NaN
        return False
    return med >= float(min_median_dvol_usd)

@dataclass
class SymSeries:
    sym: str
    df: pd.DataFrame

def build_core_monthly_schedule(
    series: List[SymSeries],
    n: int,
    mom_bars: int,
    liq_window_bars: int,
    min_median_dvol_usd: float,
) -> pd.DataFrame:
    min_dt = min(s.df.index.min() for s in series)
    max_dt = max(s.df.index.max() for s in series)
    months = _month_starts(min_dt, max_dt)

    rows = []
    last_symbols: List[str] = []

    for m in months:
        scores: List[Tuple[str, float]] = []

        for s in series:
            asof = _last_date_before(s.df, m)  # end of previous month
            if asof is None:
                continue

            if not _liquidity_ok_asof(s.df, asof, liq_window_bars, min_median_dvol_usd):
                continue

            mom = _momentum_asof(s.df, asof, mom_bars)
            if mom is None:
                continue

            scores.append((s.sym, float(mom)))

        if len(scores) == 0:
            picked = last_symbols
        else:
            scores.sort(key=lambda x: x[1], reverse=True)
            picked = [sym for sym, _ in scores[:n]]
            last_symbols = picked

        rows.append({"month": m.strftime("%Y-%m-%d"), "symbols": ";".join(picked)})

    return pd.DataFrame(rows)

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--raw_dir", type=str, default="data/raw")
    p.add_argument("--candidates", type=str, default=",".join(DEFAULT_CANDIDATES))
    p.add_argument("--n", type=int, default=8)               # <= recommandation: core plus large que crypto
    p.add_argument("--mom_bars", type=int, default=180)
    p.add_argument("--liq_window_bars", type=int, default=30)
    p.add_argument("--min_dvol_usd", type=float, default=50_000_000.0)  # 0 pour désactiver
    p.add_argument("--out", type=str, default="data/universe/core_monthly.csv")
    return p.parse_args()

def main():
    args = parse_args()

    cands = [x.strip().upper() for x in args.candidates.split(",") if x.strip()]
    if args.n <= 0:
        raise ValueError("--n must be > 0")
    if args.mom_bars <= 0:
        raise ValueError("--mom_bars must be > 0")
    if args.liq_window_bars <= 0:
        raise ValueError("--liq_window_bars must be > 0")
    if args.min_dvol_usd < 0:
        raise ValueError("--min_dvol_usd must be >= 0 (use 0 to disable)")

    series: List[SymSeries] = []
    missing = []
    no_volume = []

    for sym in cands:
        path = os.path.join(args.raw_dir, f"{sym}.csv")
        if not os.path.exists(path):
            missing.append(sym)
            continue
        df = _read_ohlcv(path)
        if "volume" not in df.columns:
            no_volume.append(sym)
        series.append(SymSeries(sym=sym, df=df))

    if len(series) == 0:
        raise RuntimeError("No candidate CSVs found. Add data/raw/<SYMBOL>.csv first.")

    if missing:
        print("[warn] missing CSVs for:", ",".join(missing))
    if no_volume:
        if args.min_dvol_usd > 0:
            print("[warn] CSVs missing 'volume' (will fail liquidity gate):", ",".join(no_volume))
        else:
            print("[warn] CSVs missing 'volume' (liquidity filter disabled):", ",".join(no_volume))

    out_df = build_core_monthly_schedule(
        series=series,
        n=args.n,
        mom_bars=args.mom_bars,
        liq_window_bars=args.liq_window_bars,
        min_median_dvol_usd=args.min_dvol_usd,
    )

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    out_df.to_csv(args.out, index=False)
    print(f"Wrote: {args.out} (rows={len(out_df)})")

if __name__ == "__main__":
    main()
