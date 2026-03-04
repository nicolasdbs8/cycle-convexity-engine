import pandas as pd
from typing import Dict, Optional


def load_symbol_csv(path: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> pd.DataFrame:
    """
    Robust CSV loader for OHLC daily files.

    Accepts:
    - Date as first column (index_col=0), regardless of its header name ("Date", "", "Unnamed: 0", etc.)
    - Single-level columns or mixed casing ("Open"/"open")
    - Extra columns (Adj Close, Volume, Ticker, etc.) -> ignored
    - Occasional non-date junk rows in index -> dropped safely

    Returns a DataFrame indexed by datetime with columns: open, high, low, close
    Filter window (optional): [start_date, end_date]
    """
    df = pd.read_csv(path, index_col=0)

    # Normalize index to datetime; drop any non-parsable rows (e.g., "Ticker")
    df.index = pd.to_datetime(df.index, errors="coerce")
    df = df[~df.index.isna()].copy()
    df = df.sort_index()
    df.index.name = "date"

    # Normalize column names to lowercase
    df.columns = [str(c).strip().lower() for c in df.columns]

    required = ["open", "high", "low", "close"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(
            f"{path}: missing columns {missing}. "
            f"Found columns={list(df.columns)}"
        )

    out = df[required].copy()

    # Ensure numeric
    for c in required:
        out[c] = pd.to_numeric(out[c], errors="coerce")

    # Drop rows where any OHLC is missing/non-numeric
    out = out.dropna(subset=required)

    # --- Date filtering (inclusive) ---
    if start_date is not None:
        start_ts = pd.to_datetime(start_date)
        out = out.loc[out.index >= start_ts]
    if end_date is not None:
        end_ts = pd.to_datetime(end_date)
        out = out.loc[out.index <= end_ts]

    return out


def load_panel(symbol_to_path, start_date=None, end_date=None):
    panel = {}
    for sym, p in symbol_to_path.items():
        df = load_symbol_csv(p, start_date=start_date, end_date=end_date)
        if df is None or df.empty:
            print(f"[warn] {sym}: no rows in date window (skipped)")
            continue
        panel[sym] = df
    return panel
