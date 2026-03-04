import pandas as pd


def load_crypto_monthly_schedule(path: str) -> pd.DataFrame:
    """
    CSV format:
      month,symbols
      2017-11-01,BTC;ETH
      2017-12-01,BTC;ETH;SOL

    Returns a DataFrame with:
      - month: pd.Timestamp (start of month)
      - symbols: list[str]
    """
    df = pd.read_csv(path)
    if "month" not in df.columns or "symbols" not in df.columns:
        raise ValueError("crypto_monthly.csv must have columns: month,symbols")

    df["month"] = pd.to_datetime(df["month"]).dt.to_period("M").dt.to_timestamp()
    df["symbols"] = df["symbols"].fillna("").astype(str).apply(
        lambda s: [x.strip().upper() for x in s.split(";") if x.strip()]
    )
    df = df.sort_values("month").reset_index(drop=True)
    return df


def symbols_for_date(dt: pd.Timestamp, schedule_df: pd.DataFrame) -> set[str]:
    """
    For date dt, returns the latest schedule row with month <= dt's month start.
    Forward-fills the last known schedule.
    """
    if schedule_df is None or schedule_df.empty:
        return set()

    dt = pd.Timestamp(dt)
    month = dt.to_period("M").to_timestamp()

    # last row where month <= current month
    mask = schedule_df["month"] <= month
    if not mask.any():
        # if schedule starts after dt, use first row
        return set(schedule_df.loc[0, "symbols"])

    row = schedule_df.loc[mask].iloc[-1]
    return set(row["symbols"])
