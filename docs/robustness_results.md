# Robustness Results

Ce document consigne les résultats de robustesse obtenus au cours des différents sprints du projet.

L’objectif est d’identifier une configuration **stable et institutionnelle**, plutôt qu’un optimum opportuniste.

---

# Baseline actuelle (provisoire)

Configuration retenue après itérations :

Breakout : **150 jours**  
Stop : **2.5 × ATR(20)**  
Régime : **MA52 weekly**  
Execution : signal close t, entry open t+1  
Costs : fee 0.1 % + slippage 0.05 %  
Max positions : **3**  
Risk cap total : **0.06**

Architecture portefeuille :

core = 90 %  
satellite = 10 %

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
- stabiliser le portefeuille
- réduire la dépendance aux crypto cycles

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

L’univers crypto est :

- recalculé **mensuellement**
- basé sur liquidité / momentum
- **figé pendant le mois**
- anti-lookahead strict

Pipeline :

scripts/make_crypto_monthly.py

Produit :

data/universe/crypto_monthly.csv

---

# Historique des tests de sensibilité

## Breakout / Stop / Costs (phase initiale)

Tests réalisés initialement sur BTC uniquement.

Breakout / Stop / Coûts (MA200 initial) :

b180_s2_cost1 : CAGR 18.11 %, MaxDD -81.47 %, Trades 6  
b150_s2_cost1 : identique à b180  
b220_s2_cost1 : CAGR 7.00 %, MaxDD -73.95 %, Trades 12  
b180_s3_cost1 : CAGR 14.50 %, MaxDD -80.12 %, Trades 6  
b180_s2_cost2 : CAGR 17.96 %, MaxDD -81.44 %, Trades 6  

Observation :

- très peu de trades
- dépendance forte à quelques cycles crypto

---

# Sensibilité du filtre de régime

### Régime MA (full history)

MA200_full : CAGR 18.11 %, MaxDD -81.47 %, Trades 6  
MA100_full : CAGR 22.99 %, MaxDD -73.29 %, Trades 10  

Observation :

- MA100 augmente la réactivité
- drawdown légèrement réduit
- nombre de trades plus cohérent

Décision provisoire :

→ abandon MA200

---

# Tests sous-périodes (BTC)

## 2014+

MA100 : CAGR 9.67 %, MaxDD -65.01 %, Trades 9  
MA200 : CAGR 23.83 %, MaxDD -81.47 %, Trades 6  

## 2016+

MA100 : CAGR 11.68 %, MaxDD -65.01 %, Trades 9  
MA200 : CAGR 11.43 %, MaxDD -73.95 %, Trades 10  

## 2018+

MA100 : CAGR 4.76 %, MaxDD -38.60 %, Trades 6  
MA200 : CAGR 4.57 %, MaxDD -53.44 %, Trades 8  

## 2020+

MA100 : CAGR 7.06 %, MaxDD -38.60 %, Trades 4  
MA200 : CAGR 7.17 %, MaxDD -53.44 %, Trades 5  

Observation générale :

- MA100 domine MA200
- MA200 produit des drawdowns extrêmes

Décision finale :

→ abandon MA200  
→ adoption **MA52 weekly**

---

# Passage au multi-asset

Extension du moteur vers un univers multi-actifs :

BTC  
ETH  
SPY  
QQQ  
GLD  
TLT  
USO  

Objectif :

tester si le breakout possède un **edge structurel au-delà de la crypto**.

Résultat typique :

CAGR ≈ 8–9 %  
MaxDD ≈ -25 %  
Profit Factor ≈ 2–3  
Trades ≈ 20–25  

Observation :

Le moteur reste profitable **hors crypto**, ce qui indique un edge structurel.

---

# Validation Walk-Forward (ETF only)

Walk-forward réalisé sur :

SPY  
QQQ  
GLD  
TLT  
USO  

Configuration :

train : 10 ans  
test : 3 ans  
step : 2 ans  

Période totale :

2006–2026

### Statistiques globales

Median CAGR : **6.98 %**  
Min CAGR : **0.28 %**  

Median Profit Factor : **6.61**  
Min Profit Factor : **1.45**

Median MaxDD : **-17.7 %**  
Worst MaxDD : **-21.7 %**

Observation :

- aucun split perdant
- profit factor toujours > 1
- drawdown contenu

Conclusion :

→ **le moteur est robuste sur ETF hors échantillon**

---

# Passage à l’architecture Core / Satellite

Implémentation :

src/sleeves.py

Structure :

Core ETF trend engine  
+  
Satellite crypto opportuniste

Allocation actuelle :

core = 90 %  
sat = 10 %

Les deux sleeves sont backtestées séparément puis agrégées.

---

# Tests sous-périodes (architecture actuelle)

## 2005–2014

Univers :

ETF core uniquement (crypto inexistantes sur la période)

Résultat :

CAGR ≈ **2.9 %**  
MaxDD ≈ **-17 %**  
Trades ≈ **29**  
Profit Factor ≈ **1.57**

Observation :

- performance modeste mais positive
- drawdown contenu
- robustesse du moteur hors crypto

---

## 2015–2026

Univers :

ETF + crypto large caps

Résultat :

CAGR ≈ **10.2 %**  
MaxDD ≈ **-35 %**  
Trades ≈ **57**  
Profit Factor ≈ **7.14**

Observation :

- crypto augmente fortement la convexité
- core stabilise le portefeuille
- dépendance partielle aux tendances crypto

---

# Interprétation

Le moteur présente les propriétés suivantes :

Edge structurel de trend following  
Robustesse multi-actifs  
Validation walk-forward ETF  
Convexité apportée par crypto

Architecture logique :

Core ETF robuste  
+  
Satellite crypto opportuniste

---

# Limites actuelles

Nombre de trades encore faible :

≈ 5 trades / an

Conséquences :

- forte dépendance à quelques tendances
- diversification imparfaite

---

# Prochaines améliorations

1. Volatility targeting portefeuille
2. Diversification supplémentaire du core
3. Extension univers crypto
4. Ajout potentiel d’un second breakout
5. Walk-forward du moteur combiné
