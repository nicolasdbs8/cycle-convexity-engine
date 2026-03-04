import argparse
import os
from dataclasses import dataclass
from typing import List, Tuple

import pandas as pd


DEFAULT_CANDIDATES = ["BTC", "ETH", "BNB", "SOL", "XRP", "ADA", "DOGE", "TRX", "TON", "LINK"]


@dataclass
class SymSeries:
    sym: str
    df: pd.DataFrame  # indexed by date


def _read_ohlcv(path: str) -> pd.DataFrame:
    # This handles Yahoo-style exports like:
    # Price,Open,High,Low,Close
    # Ticker,BTC-USD,BTC-USD,BTC-USD,BTC-USD
    # Date,,,,
    # 2014-09-17,465.86,468.17,452.42,457.33
    df = pd.read_csv(path, header=None)

    if df.shape[1] < 5:
        raise ValueError(f"{path}: expected at least 5 columns")

    # Drop the first 3 rows (metadata), keep the rest as data
    df = df.iloc[3:].copy()
    df.columns = ["date", "open", "high", "low", "close"] + [f"col_{i}" for i in range(5, df.shape[1])]

    # Coerce types
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    for c in ["open", "high", "low", "close"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    # Optional volume if present
    if "col_5" in df.columns:
        # if the 6th column is volume in your exports, rename it
        # (if not, it will just be ignored later)
        df.rename(columns={"col_5": "volume"}, inplace=True)
        df["volume"] = pd.to_numeric(df["volume"], errors="coerce")

    df = df.dropna(subset=["date", "open", "high", "low", "close"])
    df = df.sort_values("date").drop_duplicates("date").set_index("date")

    return df


def _last_date_before(df: pd.DataFrame, dt: pd.Timestamp) -> pd.Timestamp | None:
    idx = df.index[df.index < dt]
    if len(idx) == 0:
        return None
    return idx[-1]


def _momentum_asof(df: pd.DataFrame, asof: pd.Timestamp, lookback_bars: int) -> float | None:
    sub = df.loc[:asof]
    if len(sub) <= lookback_bars:
        return None
    close_now = float(sub["close"].iloc[-1])
    close_then = float(sub["close"].iloc[-1 - lookback_bars])
    if close_then <= 0:
        return None
    return (close_now / close_then) - 1.0


def _liquidity_ok_asof(
    df: pd.DataFrame,
    asof: pd.Timestamp,
    window_bars: int,
    min_median_dvol_usd: float,
) -> bool:
    """
    Dollar-volume proxy: close * volume.
    Uses median over last window_bars ending at asof (inclusive).
    Anti-lookahead: only uses data <= asof.
    """
    if "volume" not in df.columns:
        return False

    sub = df.loc[:asof]
    if len(sub) < window_bars:
        return False

    # Take last window_bars
    tail = sub.iloc[-window_bars:]
    vol = pd.to_numeric(tail["volume"], errors="coerce")
    close = pd.to_numeric(tail["close"], errors="coerce")
    dvol = close * vol

    med = float(dvol.median(skipna=True)) if dvol.notna().any() else float("nan")
    if not (med == med):  # NaN check
        return False
    return med >= float(min_median_dvol_usd)


def _month_starts(min_dt: pd.Timestamp, max_dt: pd.Timestamp) -> List[pd.Timestamp]:
    start = min_dt.to_period("M").to_timestamp()
    end = max_dt.to_period("M").to_timestamp()
    months = pd.date_range(start=start, end=end, freq="MS")
    return [pd.Timestamp(x) for x in months]


def build_crypto_monthly_schedule(
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
            asof = _last_date_before(s.df, m)  # end of previous month (or last trading day before m)
            if asof is None:
                continue

            # Liquidity gate (skip illiquid)
            if not _liquidity_ok_asof(s.df, asof, liq_window_bars, min_median_dvol_usd):
                continue

            mom = _momentum_asof(s.df, asof, mom_bars)
            if mom is None:
                continue

            scores.append((s.sym, mom))

        # forward-fill if no valid scores
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
    p.add_argument("--n", type=int, default=3)
    p.add_argument("--mom_bars", type=int, default=180)

    # Liquidity filter
    p.add_argument("--liq_window_bars", type=int, default=30)
    p.add_argument("--min_dvol_usd", type=float, default=10_000_000.0)

    p.add_argument("--out", type=str, default="data/universe/crypto_monthly.csv")
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
    if args.min_dvol_usd <= 0:
        raise ValueError("--min_dvol_usd must be > 0")

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
        print("[warn] CSVs missing 'volume' (will fail liquidity gate):", ",".join(no_volume))

    out_df = build_crypto_monthly_schedule(
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
