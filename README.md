# cycle-convexity-engine

Architecture systématique de croissance asymétrique multi-actifs.

---

# Objectif

Construire un moteur de trading systématique robuste visant à maximiser la croissance géométrique du capital sur un horizon long terme.

Contraintes :

- approche 100 % systématique
- aucune discrétion en live
- robustesse prioritaire sur l’optimisation
- architecture modulaire et auditée
- validation hors-échantillon obligatoire

Le projet privilégie une logique **institutionnelle** :

- règles simples
- validation par robustesse
- contrôle du risque strict
- versioning discipliné

---

# Architecture actuelle

Le moteur est basé sur un **trend-following multi-actifs**.

Principe :

1. Détection d’un breakout structurel
2. Filtrage par régime de marché
3. sizing basé sur volatilité
4. gestion du risque portefeuille

Paramètres actuels :

- Breakout : 150 jours
- Stop : 2.5 × ATR(20)
- Régime : MA52 weekly
- Max positions : 3
- Risk cap total : 0.06

---

# Univers actuel

Core ETF :

- SPY
- QQQ
- GLD
- TLT
- USO

Crypto satellite :

- BTC
- ETH

Objectif futur :

- univers crypto dynamique (top N liquidité)

---

# Validation actuelle

Tests réalisés :

- sensibilité paramètres
- audit anti-lookahead
- Monte Carlo
- walk-forward

Walk-forward ETF (2006-2026) :

- Median CAGR ≈ 7 %
- Profit Factor toujours > 1
- MaxDD ≈ -22 %

Conclusion :

le moteur présente un **edge robuste sur ETF**.

---

# Structure du repo


src/
config.py
indicators.py
strategy.py
regime.py
portfolio.py
backtest.py
backtest_multi.py
data_panel.py

scripts/
audit_lookahead.py
monte_carlo.py
walk_forward.py
sweep_params.py

run_backtest.py
run_backtest_multi.py


Outputs :


data/outputs/<tag>/
equity_curve.csv
trades.csv
summary.json


---

# Philosophie du projet

Le projet ne cherche pas :

- un indicateur miracle
- du scalping
- une optimisation fragile

Il cherche :

- un moteur robuste
- survivant aux cycles
- capable de convexité dans les phases de tendance.

---

# Roadmap

Sprint actuel :

- core ETF validé

Prochaines étapes :

1. séparation core ETF / satellite crypto
2. univers crypto dynamique (top N)
3. filtre liquidité crypto
4. extension walk-forward multi-actifs
5. execution layer
