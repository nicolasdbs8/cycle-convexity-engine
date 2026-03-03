import pandas as pd
from src.config import Config
from src.data_loader import load_ohlc_csv
from src.strategy import build_signals

cfg = Config()
df = load_ohlc_csv(cfg.csv_path)

# Build indicators
df2 = build_signals(
    df,
    breakout_days=cfg.breakout_days,
    mom_days=cfg.mom_days,
    atr_days=cfg.atr_days,
)

print("=== AUDIT LOOKAHEAD ===")

# 1️⃣ Breakout rolling high must use shift(1)
rolling_high_raw = df["high"].rolling(cfg.breakout_days).max()
rolling_high_shifted = rolling_high_raw.shift(1)

diff = (df2["hh_prev"] - rolling_high_shifted).abs().sum()

if diff < 1e-9:
    print("OK: hh_prev correctly uses shift(1)")
else:
    print("FAIL: hh_prev may be leaking future data")

# 2️⃣ ATR must not use future values
# Simple sanity: ATR today should not equal ATR tomorrow unless flat
atr_diff_future = (df2["atr"].shift(-1) - df2["atr"]).abs().mean()

if atr_diff_future != 0:
    print("OK: ATR not constant, likely computed correctly")
else:
    print("WARNING: ATR suspiciously constant")

# 3️⃣ Ensure no NaN leakage at beginning of series
if df2["hh_prev"].iloc[cfg.breakout_days:].isna().sum() == 0:
    print("OK: No unexpected NaNs after warmup")
else:
    print("WARNING: Unexpected NaNs detected")

# 4️⃣ Ensure breakout signal uses previous high only
breakout_today = df2["close"] > df2["hh_prev"]
future_high = df["high"].shift(-1)
leak_test = (df2["hh_prev"] == future_high).sum()

if leak_test == 0:
    print("OK: hh_prev not equal to future high")
else:
    print("FAIL: hh_prev equals future high somewhere")

print("=== END AUDIT ===")
