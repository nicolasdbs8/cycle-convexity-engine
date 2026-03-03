import pandas as pd
from typing import Dict

def load_symbol_csv(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.set_index("Date").sort_index()
    df.columns = [c.lower() for c in df.columns]
    return df[["open", "high", "low", "close"]]

def load_panel(symbol_to_path: Dict[str, str]) -> Dict[str, pd.DataFrame]:
    return {sym: load_symbol_csv(p) for sym, p in symbol_to_path.items()}
