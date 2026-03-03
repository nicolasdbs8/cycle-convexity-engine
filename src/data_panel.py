import pandas as pd
from typing import Dict


def load_symbol_csv(path: str) -> pd.DataFrame:
    # Read assuming the first column is the date column (index), which is the most common for CSV exports
    df = pd.read_csv(path, index_col=0)

    # Normalize index to datetime
    df.index = pd.to_datetime(df.index, errors="raise")
    df = df.sort_index()

    # Normalize column names
    df.columns = [str(c).strip().lower() for c in df.columns]

    # Some exports might include "adj close" etc. We only keep OHLC
    required = ["open", "high", "low", "close"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"{path}: missing columns {missing}. Found={list(df.columns)}")

    out = df[required].copy()
    out.index.name = "date"
    return out


def load_panel(symbol_to_path: Dict[str, str]) -> Dict[str, pd.DataFrame]:
    return {sym: load_symbol_csv(p) for sym, p in symbol_to_path.items()}
