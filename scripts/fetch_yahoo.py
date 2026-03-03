import os
import pandas as pd
import yfinance as yf

# Mapping symbol -> Yahoo ticker
SYMBOLS = {
    "BTC": "BTC-USD",
    "ETH": "ETH-USD",
    "SPY": "SPY",   # S&P 500 ETF
    "QQQ": "QQQ",   # Nasdaq 100 ETF
    "GLD": "GLD",   # Gold ETF
    "TLT": "TLT",   # US 20Y+ Treasuries ETF
    "USO": "USO",   # Oil ETF proxy
}

OUT_DIR = "data/raw"
START = "2005-01-01"  # enough for most ETFs


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    for sym, ticker in SYMBOLS.items():
        print(f"Fetching {sym} ({ticker})...")
        df = yf.download(
            tickers=ticker,
            start=START,
            auto_adjust=False,
            progress=False,
        )

        if df is None or df.empty:
            raise RuntimeError(f"No data returned for {sym}/{ticker}")

        # Normalize columns
        df = df.rename(columns={
            "Open": "Open",
            "High": "High",
            "Low": "Low",
            "Close": "Close",
        })

        out = df[["Open", "High", "Low", "Close"]].copy()
        out.index.name = "Date"

        path = os.path.join(OUT_DIR, f"{sym}.csv")
        out.to_csv(path)
        print(f"Wrote {path} rows={len(out)}")

    print("Done.")


if __name__ == "__main__":
    main()
