import pandas as pd
import numpy as np
from src.config import Config
from src.report import summarize

# Charger trades baseline
trades = pd.read_csv("data/outputs/ma100_slope_off_full/trades.csv")

initial_capital = 10000
n_sim = 5000

# On reconstruit les multiplicateurs réels par trade
# Hypothèse : pnl = capital_before_trade * r
# Donc r = pnl / capital_before_trade
# On reconstruit dynamiquement à partir du backtest réel

# Rejouer la vraie séquence pour récupérer les r exacts
capital = initial_capital
r_list = []

for _, row in trades.iterrows():
    r = row["pnl"] / capital
    r_list.append(r)
    capital = capital * (1 + r)

r_array = np.array(r_list)

# Monte Carlo
end_equities = []
max_dds = []

for _ in range(n_sim):
    capital = initial_capital
    peak = capital
    max_dd = 0

    sampled_r = np.random.choice(r_array, size=len(r_array), replace=True)

    for r in sampled_r:
        capital = capital * (1 + r)
        peak = max(peak, capital)
        dd = (capital - peak) / peak
        max_dd = min(max_dd, dd)

    end_equities.append(capital)
    max_dds.append(max_dd)

end_equities = np.array(end_equities)
max_dds = np.array(max_dds)

print("=== MONTE CARLO RESULTS ===")
print("Median End Equity:", np.median(end_equities))
print("P10 End Equity:", np.percentile(end_equities, 10))
print("P90 End Equity:", np.percentile(end_equities, 90))
print("Prob End < Initial:", np.mean(end_equities < initial_capital))

print("Median MaxDD:", np.median(max_dds))
print("P10 MaxDD:", np.percentile(max_dds, 10))
print("P90 MaxDD:", np.percentile(max_dds, 90))
print("Worst MaxDD:", np.min(max_dds))
