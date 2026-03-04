# cycle-convexity-engine

Architecture systématique de croissance asymétrique multi-actifs.

---

# Objectif

Construire un moteur de trading systématique robuste visant à maximiser la croissance géométrique du capital sur un horizon long terme.

Contraintes fondamentales :

- approche 100 % systématique
- aucune discrétion en live
- robustesse prioritaire sur l’optimisation
- architecture modulaire et auditée
- validation hors-échantillon obligatoire

Le projet suit une logique **institutionnelle** :

- règles simples
- validation par robustesse
- contrôle du risque strict
- versioning discipliné

---

# Architecture actuelle

Le moteur est un **trend-following multi-actifs core / satellite**.

Principe :

1. Détection d’un breakout structurel
2. Filtrage par régime de marché
3. sizing basé sur volatilité
4. gestion du risque portefeuille
5. architecture **core ETF + satellite crypto**

---

# Paramètres actuels

Configuration de référence :

- Breakout : 150 jours
- Stop : 2.5 × ATR(20)
- Régime : MA52 weekly
- Max positions : 3
- Risk cap total : 0.06

---

# Univers actuel

## Core ETF

Univers macro diversifié :

SPY  
QQQ  
IWM  
EFA  
EEM  
GLD  
TLT  
IEF  
SHY  

Objectif :

- capter les grandes tendances macro
- stabiliser la volatilité du portefeuille

---

## Satellite crypto

Univers large caps :

BTC  
ETH  
BNB  
SOL  
XRP  
ADA  
DOGE  
TRX  
LINK  

Sélection dynamique :

- **top N momentum mensuel**
- univers figé par mois
- anti-lookahead strict

---

# Structure core / satellite

Allocation actuelle :


core = 90 %
satellite = 10 %


Les deux sleeves sont backtestés séparément puis agrégés.

---

# Validation actuelle

Tests réalisés :

- sensibilité paramètres
- audit anti-lookahead
- Monte Carlo
- walk-forward
- tests sous-périodes

Résultats typiques :


2005-2014
CAGR ≈ 3 %
MaxDD ≈ -17 %

2015-2026
CAGR ≈ 10 %
MaxDD ≈ -35 %


Interprétation :

- core stabilise le portefeuille
- crypto apporte la convexité

---

# Structure du repo


src/
config.py
indicators.py
strategy.py
regime.py
portfolio_multi.py
backtest_multi.py
sleeves.py
universe.py

scripts/
fetch_yahoo.py
make_crypto_monthly.py
walk_forward.py
monte_carlo.py

run_backtest_multi.py


Outputs :


data/outputs/<tag>/
equity_curve.csv
trades.csv
summary.json


---

# Philosophie

Le projet ne cherche pas :

- un indicateur miracle
- du scalping
- de l’optimisation fragile

Il cherche :

- un moteur robuste
- survivant aux cycles
- capable de convexité dans les phases de tendance.

---

# Roadmap

Prochaines améliorations :

1. volatility targeting portefeuille
2. diversification supplémentaire du core
3. éventuel second breakout
4. execution layer (paper trading)
