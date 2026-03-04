# STATE.md

## Version actuelle
v0.2.0

---

# Implémenté

## Moteur de backtest

- exécution next open
- stops intraday
- gestion du risque portefeuille
- fees + slippage

Artefacts :

- equity_curve.csv
- trades.csv
- summary.json

---

## Indicateurs

- SMA
- ATR
- rolling high (anti-lookahead)
- momentum

---

## Multi-assets

Univers :

- BTC
- ETH
- SPY
- QQQ
- GLD
- TLT
- USO

Loader panel multi-symbol.

---

## Validation

Tests réalisés :

- sensibilité paramètres
- Monte Carlo
- walk-forward
- audit anti-lookahead

---

## Résultats principaux

Configuration actuelle :

- breakout = 150
- stop = 2.5 ATR
- regime = MA52 weekly
- max positions = 3
- risk cap total = 0.06

Performance ETF walk-forward :

- CAGR médian ≈ 7 %
- PF toujours > 1
- MaxDD ≈ -22 %

---

# Limites actuelles

- univers crypto réduit (BTC/ETH)
- pas encore de sélection top N
- pas encore d’allocation core / satellite
- pas encore d’execution layer réel

---

# Prochain objectif

Implémenter :

core ETF  
+  
satellite crypto

Architecture portefeuille séparée.
