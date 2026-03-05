# STATE.md

## Version actuelle
v0.4.0

---

# Implémenté

## Backtest multi-actifs

- exécution next open
- stops intraday
- gestion du risque portefeuille
- fees + slippage

Artefacts générés :

equity_curve.csv  
trades.csv  
summary.json

---

## Indicateurs

- SMA
- ATR
- rolling high (anti-lookahead)
- momentum

---

## Architecture core / satellite

Implémentée via :

src/sleeves.py

Structure :

core ETF  
+  
satellite crypto

---

## Univers

### Core ETF

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

### Satellite crypto

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

## Univers crypto dynamique

Pipeline :

scripts/make_crypto_monthly.py

Produit :

data/universe/crypto_monthly.csv

Univers figé par mois.

---

# Validation

Tests réalisés :

- sensibilité paramètres
- Monte Carlo
- walk-forward
- audit anti-lookahead
- tests sous-périodes

---

# Résultats récents

Tests sous-périodes :

2005–2012  
CAGR ≈ 2 %

2013–2018  
CAGR ≈ −1 %

2019–2026  
CAGR ≈ 3–10 %

Observation :

- le core stabilise le portefeuille
- la crypto apporte la convexité

---

# Limites actuelles

- nombre de trades encore faible
- diversification core limitée
- dépendance partielle aux cycles crypto

---

# Prochain objectif

1. position sizing par volatilité d’actif
2. amélioration du stop ATR
3. volatility targeting portefeuille

## Tests récents

Walk-forward :

2005–2012
2013–2018
2019–2026

Résultat :

la stratégie survit à toutes les périodes testées.

Profit factor > 1 sur la majorité des configurations.

---

## Position sizing

Tests :

risk_per_trade = 0.0075 → DD faible
risk_per_trade = 0.01
risk_per_trade = 0.0125
risk_per_trade = 0.015 → performance maximale

Configuration retenue :

risk_per_trade = 0.015
