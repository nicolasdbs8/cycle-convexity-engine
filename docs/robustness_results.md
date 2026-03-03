# Robustness Results

Ce document consigne les résultats Sprint 2.

## Baseline actuelle
- Breakout: 180
- Stop: 2×ATR(20)
- Régime: weekly MA100 + slope(20w) > 0
- Execution: signal close t, entry open t+1
- Costs: fee 0.1% + slippage 0.05%

## Matrice de sensibilité (résumé)

### Breakout / Stop / Coûts (MA200 initial)
- b180_s2_cost1: CAGR 18.11%, MaxDD -81.47%, Trades 6
- b150_s2_cost1: identique à b180
- b220_s2_cost1: CAGR 7.00%, MaxDD -73.95%, Trades 12
- b180_s3_cost1: CAGR 14.50%, MaxDD -80.12%, Trades 6
- b180_s2_cost2: CAGR 17.96%, MaxDD -81.44%, Trades 6

### Régime MA (full)
- MA200_full: CAGR 18.11%, MaxDD -81.47%, Trades 6
- MA100_full: CAGR 22.99%, MaxDD -73.29%, Trades 10

## Sous-périodes (warmup corrigé)

### 2014+
- MA100: CAGR 9.67%, MaxDD -65.01%, Trades 9
- MA200: CAGR 23.83%, MaxDD -81.47%, Trades 6

### 2016+
- MA100: CAGR 11.68%, MaxDD -65.01%, Trades 9
- MA200: CAGR 11.43%, MaxDD -73.95%, Trades 10

### 2018+
- MA100: CAGR 4.76%, MaxDD -38.60%, Trades 6
- MA200: CAGR 4.57%, MaxDD -53.44%, Trades 8

### 2020+
- MA100: CAGR 7.06%, MaxDD -38.60%, Trades 4
- MA200: CAGR 7.17%, MaxDD -53.44%, Trades 5

## Conclusion provisoire
- MA100 domine MA200 sur 2016+, 2018+, 2020+ (DD plus faible et PF meilleur).
- MA200 surperforme sur 2014+ en CAGR mais avec drawdown extrême.
- Décision baseline (à confirmer): MA100.
