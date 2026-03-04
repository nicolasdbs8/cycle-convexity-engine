# STATE.md

## Version actuelle
v0.3.0

---

# Implémenté

## Backtest multi-actifs

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

## Architecture core / satellite

Implémentée via :


src/sleeves.py


Structure :


core ETF
+
satellite crypto


Les sleeves sont backtestées séparément puis agrégées.

---

## Univers actuel

### Core

SPY  
QQQ  
IWM  
EFA  
EEM  
GLD  
TLT  
IEF  
SHY  

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

## Validation

Tests réalisés :

- sensibilité paramètres
- Monte Carlo
- walk-forward
- audit anti-lookahead
- tests sous-périodes

---

## Résultats récents

Tests sous-périodes :


2005-2014
CAGR ≈ 3 %
MaxDD ≈ -17 %

2015-2026
CAGR ≈ 10 %
MaxDD ≈ -35 %


Conclusion :

- core stabilise le portefeuille
- crypto apporte l’alpha

---

# Limites actuelles

- diversification core encore limitée
- drawdown portefeuille ~35 %
- dépendance partielle aux tendances crypto

---

# Prochain objectif

Implémenter :

1. volatility targeting portefeuille
2. diversification supplémentaire du core
3. second breakout potentiel
