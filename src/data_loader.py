import pandas as pd

def load_ohlc_csv(path: str) -> pd.DataFrame:
    """
    Loads a CSV with columns: Date,Open,High,Low,Close,(optional Volume)
    Returns a DataFrame indexed by datetime with standardized lower-case columns.
    """
    df = pd.read_csv(path)

    # Normalize column names
    df.columns = [c.strip().lower() for c in df.columns]

    if "date" not in df.columns:
        raise ValueError("CSV must contain a 'Date' column.")

    # Parse date
    df["date"] = pd.to_datetime(df["date"], utc=False)
    df = df.sort_values("date").set_index("date")

    # Required OHLC
    for c in ["open", "high", "low", "close"]:
        if c not in df.columns:
            raise ValueError(f"CSV must contain column '{c}' (case-insensitive).")

    # Ensure numeric
    for c in ["open", "high", "low", "close"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    df = df.dropna(subset=["open", "high", "low", "close"])

    return df
