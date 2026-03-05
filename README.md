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

Pipeline logique :

1. Détection d’un breakout structurel
2. Filtrage par régime de marché
3. position sizing basé sur le risque
4. gestion du risque portefeuille
5. architecture **core ETF + satellite crypto**

---

# Paramètres actuels

Configuration de référence :

Breakout : 150 jours  
Stop : 2.5 × ATR(20)  
Régime : MA52 weekly  
Max positions : 3  
Risk cap total : 0.06  

Execution :

signal close t  
entry open t+1  

Costs :

fee = 0.1 %  
slippage = 0.05 %

---

# Univers actuel

## Core ETF

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

- capter les tendances macro
- stabiliser la volatilité du portefeuille

---

## Satellite crypto

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

- univers recalculé mensuellement
- basé sur liquidité / momentum
- univers figé pendant le mois
- anti-lookahead strict

Pipeline :

scripts/make_crypto_monthly.py

---

# Structure du portefeuille

Architecture actuelle :

core = 90 %  
satellite = 10 %

Les deux sleeves sont :

- backtestées séparément
- puis agrégées dans le portefeuille final

---

# Résultats indicatifs

Sous-périodes :

2005–2012  
CAGR ≈ 2 %  
MaxDD ≈ −9 %

2013–2018  
CAGR ≈ −1 %  
MaxDD ≈ −17 %

2019–2026  
CAGR ≈ 3–10 % selon configuration

Long run (avec crypto) :

CAGR ≈ 10–15 %  
MaxDD ≈ −16 à −26 %

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

1. position sizing par volatilité d’actif
2. amélioration des exits ATR
3. volatility targeting portefeuille
4. diversification supplémentaire du core
5. execution layer (paper trading)

## Statut actuel

Le moteur a passé :

- tests de robustesse
- walk-forward
- tests de sensibilité
- validation anti-lookahead

Edge observé :

CAGR ≈ 3 %
Profit factor ≈ 1.8
MaxDD ≈ −25 %

Le moteur sert de base à une architecture core / satellite
destinée à être amplifiée par diversification et volatility targeting.
