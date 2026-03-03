# STATE.md

## Version actuelle
v0.1.0

## Implémenté (Sprint 1 — MVP BTC single-asset)

- Data loader CSV (Date,Open,High,Low,Close)
- Indicateurs :
  - SMA
  - ATR (True Range + moyenne)
  - Rolling High (anti-lookahead via shift(1))
  - Momentum return
- Régime BTC weekly :
  - Close > MA200 weekly
  - Slope MA positive
  - Forward-fill vers daily
- Moteur backtest :
  - Signal au close, exécution next open
  - Stop intraday (2×ATR)
  - Sortie régime next open
  - Spot-only
  - Fees + slippage appliqués
- Artefacts :
  - equity_curve.csv
  - trades.csv
- Résumé JSON (CAGR, MaxDD, ProfitFactor, etc.)

Résultat actuel (BTC 2010–2026 approx.) :
- CAGR ≈ 18%
- MaxDD ≈ -81%
- 6 trades
- ProfitFactor ≈ 15.7

---

## En cours (Sprint 2 — Robustesse)

- Sensibilité paramètres :
  - breakout_days
  - stop_atr_mult
  - coûts
- Vérification anti-lookahead
- Analyse distribution drawdowns
- Vérification cohérence sizing

---

## À faire (prochaines étapes)

- Matrice de tests robustesse (automatisée via Actions)
- Monte Carlo bootstrap des trades
- Analyse sous-périodes (bull/bear/range)
- Visualisation equity (export simple)

---

## Hypothèses critiques à tester

- Robustesse aux coûts (x2 fees/slippage)
- Robustesse breakout 150/180/220
- Robustesse stop 2×ATR vs 3×ATR
- Stabilité performance hors 2015–2017 et 2020–2021
- Impact du régime MA weekly

---

## Risques identifiés

- Concentration des gains sur 1–2 trades
- Max Drawdown extrême (-81%)
- Échantillon faible (6 trades)
- Forte dépendance aux cycles BTC

---

## Prochain objectif concret

Lancer matrice de robustesse simple via GitHub Actions
et comparer métriques (CAGR, MaxDD, ProfitFactor).
