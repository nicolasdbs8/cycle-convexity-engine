import pandas as pd
from typing import Dict, Optional
from pandas.errors import EmptyDataError


def load_symbol_csv(path: str) -> pd.DataFrame:
    """
    Robust CSV loader for OHLC daily files.

    Accepts:
    - Date as first column (index_col=0), regardless of its header name ("Date", "", "Unnamed: 0", etc.)
    - Single-level columns or mixed casing ("Open"/"open")
    - Extra columns (Adj Close, Volume, Ticker, etc.) -> ignored
    - Occasional non-date junk rows in index -> dropped safely

    Returns a DataFrame indexed by datetime with columns: open, high, low, close
    (can be empty if file is empty or contains no valid OHLC rows)
    """
    try:
        df = pd.read_csv(path, index_col=0)
    except EmptyDataError:
        # Empty file (0 bytes or no parsable columns)
        return pd.DataFrame(columns=["open", "high", "low", "close"]).astype(float)

    if df is None or df.empty:
        return pd.DataFrame(columns=["open", "high", "low", "close"]).astype(float)

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
        # If the file has content but doesn't contain OHLC, treat as empty for robustness
        return pd.DataFrame(columns=required).astype(float)

    out = df[required].copy()

    # Ensure numeric
    for c in required:
        out[c] = pd.to_numeric(out[c], errors="coerce")

    # Drop rows where any OHLC is missing/non-numeric
    out = out.dropna(subset=required)

    return out


def load_panel(
    symbol_to_path: Dict[str, str],
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> Dict[str, pd.DataFrame]:
    """
    Load a dict of symbol->csv_path into symbol->OHLC DataFrames.

    - Skips missing/empty symbols with a warning
    - Optional date window filtering (inclusive)
    """
    panel: Dict[str, pd.DataFrame] = {}

    start_ts = pd.to_datetime(start_date) if start_date else None
    end_ts = pd.to_datetime(end_date) if end_date else None

    for sym, path in symbol_to_path.items():
        df = load_symbol_csv(path)

        if df is None or df.empty:
            print(f"[warn] {sym}: empty/unreadable CSV ({path}) (skipped)")
            continue

        if start_ts is not None:
            df = df[df.index >= start_ts]
        if end_ts is not None:
            df = df[df.index <= end_ts]

        if df.empty:
            print(f"[warn] {sym}: no rows in date window (skipped)")
            continue

        panel[sym] = df

    return panel
