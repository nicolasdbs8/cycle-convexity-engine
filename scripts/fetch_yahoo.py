import os
import yfinance as yf
import pandas as pd

SYMBOLS = {
    # --- Crypto (start with 9; add TON later once ticker confirmed) ---
    "BTC": "BTC-USD",
    "ETH": "ETH-USD",
    "BNB": "BNB-USD",
    "SOL": "SOL-USD",
    "XRP": "XRP-USD",
    "ADA": "ADA-USD",
    "DOGE": "DOGE-USD",
    "TRX": "TRX-USD",
    "LINK": "LINK-USD",
    # "TON": "TON11419-USD",  # add later after confirming on Yahoo

    # --- Core ETFs (14) ---
    "SPY": "SPY",
    "QQQ": "QQQ",
    "IWM": "IWM",
    "EFA": "EFA",
    "EEM": "EEM",

    "TLT": "TLT",
    "IEF": "IEF",
    "SHY": "SHY",
    "LQD": "LQD",
    "HYG": "HYG",

    "GLD": "GLD",
    "SLV": "SLV",
    "USO": "USO",
    "UNG": "UNG",

    # --- Core ETFs (extended) ---
    "XLF": "XLF",
    "XLE": "XLE",
    "XLK": "XLK",
    "XLV": "XLV",
    "XLI": "XLI",
    "VNQ": "VNQ",
    "DBC": "DBC",
    
}

OUT_DIR = "data/raw"
START = "2005-01-01"

def _flatten_columns(df: pd.DataFrame) -> pd.DataFrame:
    # yfinance can return MultiIndex columns; flatten to single level
    if isinstance(df.columns, pd.MultiIndex):
        # keep the OHLC field name level if present
        # common structure: ('Open','BTC-USD') or ('BTC-USD','Open') depending on version
        cols = []
        for a, b in df.columns.to_list():
            # pick the one that looks like OHLC
            x = str(a).strip()
            y = str(b).strip()
            if x.lower() in {"open","high","low","close","adj close","volume"}:
                cols.append(x)
            elif y.lower() in {"open","high","low","close","adj close","volume"}:
                cols.append(y)
            else:
                cols.append(x)
        df.columns = cols
    return df

def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    for sym, ticker in SYMBOLS.items():
        print(f"Fetching {sym} ({ticker})...")
        df = yf.download(tickers=ticker, start=START, progress=False, auto_adjust=False)

        if df is None or df.empty:
            raise RuntimeError(f"No data returned for {sym}/{ticker}")

        df = _flatten_columns(df)

        # Standardize exactly to Date + OHLC (single header row)
        out = df[["Open", "High", "Low", "Close"]].copy()
        out.index.name = "Date"

        path = os.path.join(OUT_DIR, f"{sym}.csv")
        out.to_csv(path, index=True)
        print(f"Wrote {path} rows={len(out)}")

    print("Done.")

if __name__ == "__main__":
    main()
