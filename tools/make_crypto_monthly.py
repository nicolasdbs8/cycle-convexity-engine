import argparse
import os
from dataclasses import dataclass
from typing import Dict, List, Tuple

import pandas as pd


DEFAULT_CANDIDATES = ["BTC", "ETH", "BNB", "SOL", "XRP", "ADA", "DOGE", "TRX", "TON", "LINK"]


@dataclass
class SymSeries:
    sym: str
    df: pd.DataFrame  # indexed by date


def _read_ohlcv(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    if "date" not in df.columns:
        raise ValueError(f"{path}: missing 'date' column")
    for col in ["open", "high", "low", "close"]:
        if col not in df.columns:
            raise ValueError(f"{path}: missing '{col}' column")

    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").drop_duplicates("date")
    df = df.set_index("date")
    return df


def _last_date_before(df: pd.DataFrame, dt: pd.Timestamp) -> pd.Timestamp | None:
    # last index strictly < dt
    idx = df.index[df.index < dt]
    if len(idx) == 0:
        return None
    return idx[-1]


def _momentum_asof(df: pd.DataFrame, asof: pd.Timestamp, lookback_bars: int) -> float | None:
    # use trading bars, not calendar days
    sub = df.loc[:asof]
    if len(sub) <= lookback_bars:
        return None
    close_now = float(sub["close"].iloc[-1])
    close_then = float(sub["close"].iloc[-1 - lookback_bars])
    if close_then <= 0:
        return None
    return (close_now / close_then) - 1.0


def _month_starts(min_dt: pd.Timestamp, max_dt: pd.Timestamp) -> List[pd.Timestamp]:
    # month starts between min_dt and max_dt inclusive
    start = min_dt.to_period("M").to_timestamp()
    end = max_dt.to_period("M").to_timestamp()
    months = pd.date_range(start=start, end=end, freq="MS")
    return [pd.Timestamp(x) for x in months]


def build_crypto_monthly_schedule(
    series: List[SymSeries],
    n: int,
    mom_bars: int,
) -> pd.DataFrame:
    # determine global month range
    min_dt = min(s.df.index.min() for s in series)
    max_dt = max(s.df.index.max() for s in series)
    months = _month_starts(min_dt, max_dt)

    rows = []
    last_symbols: List[str] = []

    for m in months:
        # anti-lookahead: selection for month m uses info up to end of (m-1)
        scores: List[Tuple[str, float]] = []

        for s in series:
            asof = _last_date_before(s.df, m)
            if asof is None:
                continue
            mom = _momentum_asof(s.df, asof, mom_bars)
            if mom is None:
                continue
            scores.append((s.sym, mom))

        # if not enough data, forward-fill last known (or empty)
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
    p.add_argument("--out", type=str, default="data/universe/crypto_monthly.csv")
    return p.parse_args()


def main():
    args = parse_args()

    cands = [x.strip().upper() for x in args.candidates.split(",") if x.strip()]
    if args.n <= 0:
        raise ValueError("--n must be > 0")
    if args.mom_bars <= 0:
        raise ValueError("--mom_bars must be > 0")

    series: List[SymSeries] = []
    missing = []

    for sym in cands:
        path = os.path.join(args.raw_dir, f"{sym}.csv")
        if not os.path.exists(path):
            missing.append(sym)
            continue
        df = _read_ohlcv(path)
        series.append(SymSeries(sym=sym, df=df))

    if len(series) == 0:
        raise RuntimeError("No candidate CSVs found. Add data/raw/<SYMBOL>.csv first.")

    if missing:
        print("[warn] missing CSVs for:", ",".join(missing))

    out_df = build_crypto_monthly_schedule(series, n=args.n, mom_bars=args.mom_bars)

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    out_df.to_csv(args.out, index=False)
    print(f"Wrote: {args.out} (rows={len(out_df)})")


if __name__ == "__main__":
    main()
