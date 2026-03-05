# cycle-convexity-engine
## Architecture systématique de croissance asymétrique multi-actifs

---

# 1. Objectif

Maximiser la croissance géométrique du capital sur un horizon long terme.

Contraintes :

- risque de ruine exclu
- drawdowns acceptés mais contrôlés
- approche entièrement systématique
- validation hors échantillon obligatoire

---

# 2. Philosophie

Principes directeurs :

- aucune discrétion en live
- règles simples et testables
- complexité ajoutée uniquement si edge démontré
- priorité à la robustesse

---

# 3. Architecture générale

Architecture **core / satellite** :

Core ETF trend engine  
+  
Satellite crypto opportuniste

Core selection layer

Le core peut être filtré par :

- sélection mensuelle des actifs
- ranking momentum cross-asset
- limitation aux meilleurs trends

Objectif :

réduire le bruit
et concentrer le risque sur les tendances dominantes.

---

# 4. Core Trend Engine

Trend-following multi-actifs basé sur :

- breakout structurel
- filtre de régime
- position sizing basé sur le risque
- gestion du risque portefeuille

---

# 5. Paramètres principaux

Breakout :

N = 150 jours

Sortie :

Stop = 2.5 × ATR(20)

Régime :

MA52 weekly

Gestion du risque :

max_positions = 3  
risk_cap_total = 0.06

---

# 6. Univers

## Core

ETF macro liquides :

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

## Satellite

Crypto large caps :

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

# 7. Univers dynamique crypto

Univers satellite :

- recalculé mensuellement
- basé sur momentum / liquidité
- figé pendant le mois
- aucun lookahead

Pipeline :

scripts/make_crypto_monthly.py  
→ data/universe/crypto_monthly.csv

---

# 8. Allocation portefeuille

Structure actuelle :

core = 90 %  
sat = 10 %

---

# 9. Validation

Tests utilisés :

- sensibilité paramètres
- tests sous-périodes
- Monte Carlo
- walk-forward
- audit anti-lookahead

---

# 10. Métriques suivies

- CAGR
- Max Drawdown
- Profit Factor
- nombre de trades
- distribution Monte Carlo

---

# 11. Architecture cible

Objectif final :

Core ETF robuste  
+  
Satellite crypto opportuniste  
+  
gestion dynamique du risque portefeuille

But :

- stabilité du capital
- convexité dans les phases de tendance
