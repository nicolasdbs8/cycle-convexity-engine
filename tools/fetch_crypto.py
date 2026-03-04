import os
import yfinance as yf

SYMBOLS = {
    "BTC": "BTC-USD",
    "ETH": "ETH-USD",
    "BNB": "BNB-USD",
    "SOL": "SOL-USD",
}

OUT_DIR = "data/raw"
os.makedirs(OUT_DIR, exist_ok=True)

for sym, ticker in SYMBOLS.items():
    print(f"Fetching {ticker}...")
    df = yf.download(ticker, start="2010-01-01", progress=False)

    if df.empty:
        print(f"Warning: no data for {ticker}")
        continue

    path = f"{OUT_DIR}/{sym}.csv"
    df.to_csv(path)
    print(f"Saved {path}")
