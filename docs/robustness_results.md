# Robustness Results

Document de suivi des tests de robustesse.

Objectif :

identifier une configuration stable et institutionnelle.

---

# Baseline actuelle

Breakout : 150 jours  
Stop : 2.5 × ATR(20)  
Régime : MA52 weekly  
Execution : next open  
Costs : 0.15 % round trip  

Max positions : 3  
Risk cap total : 0.06  

Architecture :

core = 90 %  
sat = 10 %

---

# Univers

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

---

# Tests sous-périodes récents

### 2005–2012

CAGR ≈ 2 %  
MaxDD ≈ −9 %

Observation :

performance modeste mais robuste.

---

### 2013–2018

CAGR légèrement négatif.

Observation :

période défavorable au trend following.

---

### 2019–2026

CAGR ≈ 3–10 %

Observation :

crypto apporte une convexité importante.

---

# Interprétation

Le moteur présente :

- edge structurel de trend following
- robustesse multi-actifs
- convexité apportée par crypto

Architecture logique :

Core ETF robuste  
+  
Satellite crypto opportuniste

---

# Limites actuelles

- nombre de trades faible
- dépendance aux tendances longues

---

# Prochaines améliorations

1. position sizing par volatilité actif
2. amélioration exit ATR
3. volatility targeting portefeuille
4. diversification core

# Résultats récents (v0.4)

Configuration :

Breakout : 150 jours
Stop : 2.5 × ATR(20)
Régime : MA52 weekly
Max positions : 3
Risk cap total : 0.06

Univers :

Core ETF
+ satellite crypto dynamique

---

## Backtest global

CAGR ≈ 3.1 %
MaxDD ≈ −25 %
Profit Factor ≈ 1.8
Trades ≈ 155

Observation :

edge structurel de trend following
distribution de gains saine (Top5 ≈ 30 %)

---

## Walk-forward

2005–2012

CAGR ≈ 0.5 %
MaxDD ≈ −20 %

Observation :
edge faible mais stratégie survivante.

---

2013–2018

CAGR ≈ 0 %
MaxDD ≈ −16 %

Observation :
période défavorable au trend following.

---

2019–2026

CAGR ≈ 5.8 %
MaxDD ≈ −18 %

Observation :
forte capture des tendances récentes.

---

## Test position sizing

Risk per trade testé :

0.0075
0.01
0.0125
0.015

Conclusion :

l’edge est stable.
le sizing agit surtout sur la volatilité et le drawdown.

Configuration retenue :

risk_per_trade = 0.015
