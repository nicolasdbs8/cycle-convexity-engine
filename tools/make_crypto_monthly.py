#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd


DEFAULT_CANDIDATES = ["BTC", "ETH", "BNB", "SOL", "XRP", "ADA", "DOGE", "TRX", "TON", "LINK"]


@dataclass(frozen=True)
class Row:
    date: pd.Timestamp
    symbols: List[str]


def _warn(msg: str) -> None:
    print(f"[warn] {msg}")


def _read_ohlcv(path: str) -> Optional[pd.DataFrame]:
    """
    Accepts either:
      - "normal" schema: date,open,high,low,close,adj_close,volume
      - yfinance "weird" schema (multi header like Price/Ticker/Date rows)

    Returns None if file missing/empty/unreadable.
    """
    if not os.path.exists(path):
        return None

    # Empty file => EmptyDataError
    try:
        df0 = pd.read_csv(path)
    except pd.errors.EmptyDataError:
        _warn(f"{path}: empty csv (skipped)")
        return None
    except Exception as e:
        _warn(f"{path}: read failed ({e}) (skipped)")
        return None

    if df0 is None or df0.empty:
        _warn(f"{path}: no rows (skipped)")
        return None

    cols = [c.lower().strip() for c in df0.columns]

    # Normal case: has date column
    if "date" in cols:
        df = df0.copy()
        # normalize column names
        df.columns = [c.lower().strip() for c in df.columns]
        if "adj close" in df.columns and "adj_close" not in df.columns:
            df = df.rename(columns={"adj close": "adj_close"})
        if "adj_close" not in df.columns:
            df["adj_close"] = np.nan
        if "volume" not in df.columns:
            df["volume"] = np.nan

        df["date"] = pd.to_datetime(df["date"], errors="coerce", utc=True).dt.tz_convert(None)
        df = df.dropna(subset=["date"]).set_index("date").sort_index()

        # required columns
        for c in ["open", "high", "low", "close"]:
            if c not in df.columns:
                _warn(f"{path}: missing '{c}' column (skipped)")
                return None
            df[c] = pd.to_numeric(df[c], errors="coerce")

        df["volume"] = pd.to_numeric(df["volume"], errors="coerce")
        df = df.dropna(subset=["close"])
        if df.empty:
            _warn(f"{path}: no valid close after cleaning (skipped)")
            return None
        return df

    # Weird yfinance export with rows like:
    # Price,Open,High,Low,Close
    # Ticker,BTC-USD,BTC-USD,...
    # Date,,,,
    # 2014-..., 465..., ...
    # We try: read with header=None then locate a "Date" row and re-read.
    try:
        raw = pd.read_csv(path, header=None)
    except pd.errors.EmptyDataError:
        _warn(f"{path}: empty csv (skipped)")
        return None
    except Exception as e:
        _warn(f"{path}: read failed ({e}) (skipped)")
        return None

    if raw.empty:
        _warn(f"{path}: empty csv (skipped)")
        return None

    # find the row where first cell == "Date"
    date_row_idx = None
    for i in range(min(len(raw), 10)):
        v = str(raw.iloc[i, 0]).strip().lower()
        if v == "date":
            date_row_idx = i
            break

    if date_row_idx is None:
        _warn(f"{path}: cannot find Date row (skipped)")
        return None

    # Now re-read starting from that row as header
    try:
        df = pd.read_csv(path, skiprows=date_row_idx)
    except pd.errors.EmptyDataError:
        _warn(f"{path}: no data after Date row (skipped)")
        return None
    except Exception as e:
        _warn(f"{path}: read failed after Date row ({e}) (skipped)")
        return None

    df.columns = [c.lower().strip() for c in df.columns]
    if "date" not in df.columns:
        _warn(f"{path}: missing date column after normalize (skipped)")
        return None

    for c in ["open", "high", "low", "close"]:
        if c not in df.columns:
            _warn(f"{path}: missing '{c}' column (skipped)")
            return None

    if "volume" not in df.columns:
        df["volume"] = np.nan

    df["date"] = pd.to_datetime(df["date"], errors="coerce", utc=True).dt.tz_convert(None)
    df = df.dropna(subset=["date"]).set_index("date").sort_index()

    for c in ["open", "high", "low", "close", "volume"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    df = df.dropna(subset=["close"])
    if df.empty:
        _warn(f"{path}: no valid close after cleaning (skipped)")
        return None
    return df


def _month_ends(idx: pd.DatetimeIndex) -> pd.DatetimeIndex:
    # month-end dates present in idx
    s = pd.Series(index=idx, data=1)
    return s.resample("M").last().index


def _compute_mom(close: pd.Series, mom_bars: int) -> pd.Series:
    # simple momentum: close / close.shift(mom_bars) - 1
    return close / close.shift(mom_bars) - 1.0


def build_schedule(
    panels: Dict[str, pd.DataFrame],
    n: int,
    mom_bars: int,
    min_dvol_usd: float,
) -> List[Row]:
    # Determine common month-ends across all panels (union)
    all_idx = None
    for df in panels.values():
        all_idx = df.index if all_idx is None else all_idx.union(df.index)
    if all_idx is None:
        return []

    month_ends = _month_ends(all_idx.sort_values())

    rows: List[Row] = []
    for dt in month_ends:
        scored: List[Tuple[str, float]] = []
        for sym, df in panels.items():
            if dt not in df.index:
                continue

            close = df["close"]
            mom = _compute_mom(close, mom_bars)
            m = mom.loc[dt] if dt in mom.index else np.nan
            if pd.isna(m):
                continue

            # liquidity filter: use last 20 bars avg dollar volume if possible
            if min_dvol_usd > 0 and "volume" in df.columns and df["volume"].notna().any():
                dv = (df["close"] * df["volume"]).rolling(20).mean()
                d = dv.loc[dt] if dt in dv.index else np.nan
                if pd.isna(d) or float(d) < float(min_dvol_usd):
                    continue

            scored.append((sym, float(m)))

        if not scored:
            rows.append(Row(date=dt, symbols=[]))
            continue

        scored.sort(key=lambda x: x[1], reverse=True)
        picked = [s for s, _ in scored[: int(n)]]
        rows.append(Row(date=dt, symbols=picked))

    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, required=True)
    ap.add_argument("--mom_bars", type=int, default=180)
    ap.add_argument("--min_dvol_usd", type=float, default=0.0)
    ap.add_argument("--candidates", type=str, default=",".join(DEFAULT_CANDIDATES))
    ap.add_argument("--in_dir", type=str, default="data/raw")
    ap.add_argument("--out", type=str, default="data/universe/crypto_monthly.csv")
    args = ap.parse_args()

    if args.n <= 0:
        raise ValueError("--n must be > 0")
    if args.mom_bars <= 0:
        raise ValueError("--mom_bars must be > 0")
    if args.min_dvol_usd < 0:
        raise ValueError("--min_dvol_usd must be >= 0")

    cands = [s.strip().upper() for s in args.candidates.split(",") if s.strip()]
    missing = []
    panels: Dict[str, pd.DataFrame] = {}

    for sym in cands:
        path = os.path.join(args.in_dir, f"{sym}.csv")
        df = _read_ohlcv(path)
        if df is None:
            missing.append(sym)
            continue
        panels[sym] = df

    if missing:
        _warn(f"missing/invalid CSVs for: {','.join(missing)}")

    if not panels:
        _warn("no valid crypto panels. Writing empty schedule.")
        os.makedirs(os.path.dirname(args.out), exist_ok=True)
        pd.DataFrame({"date": [], "symbols": []}).to_csv(args.out, index=False)
        print(f"Wrote: {args.out} (rows=0)")
        return

    # warn if volume missing (liquidity filter becomes partial)
    no_vol = [s for s, df in panels.items() if "volume" not in df.columns or df["volume"].isna().all()]
    if no_vol and args.min_dvol_usd > 0:
        _warn(f"CSVs missing 'volume' (liquidity filter may skip less): {','.join(no_vol)}")

    rows = build_schedule(panels, args.n, args.mom_bars, args.min_dvol_usd)
    out_df = pd.DataFrame(
        {
            "date": [r.date.strftime("%Y-%m-%d") for r in rows],
            "symbols": [",".join(r.symbols) for r in rows],
        }
    )

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    out_df.to_csv(args.out, index=False)
    print(f"Wrote: {args.out} (rows={len(out_df)})")


if __name__ == "__main__":
    main()
