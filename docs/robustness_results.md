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
