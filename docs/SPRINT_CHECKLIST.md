# SPRINT_CHECKLIST.md

Projet: cycle-convexity-engine

Checklist opérationnelle (anti-dérive).

Objectif : progression vérifiable.

---

# État actuel

Implémenté :

- backtest multi-actifs
- architecture core / satellite
- univers crypto dynamique mensuel
- CI GitHub Actions
- génération d’artefacts

---

# Baseline actuelle

Paramètres :


breakout = 150
stop = 2.5 ATR
regime = MA52
max_positions = 3
risk_cap_total = 0.06


Allocation :


core = 90 %
sat = 10 %


---

# Sprint actuel

Objectif :

stabilisation du moteur.

---

# Sprint 4 — Core / Satellite

Status : ✅ implémenté

- sleeves core / satellite
- aggregation equity
- trades taggés par sleeve

---

# Sprint 5 — Univers crypto dynamique

Status : ✅ implémenté

- univers mensuel
- anti-lookahead
- pipeline reproductible

---

# Sprint 6 — Volatility targeting portefeuille

Objectif :

réduire les drawdowns.

Implémentation prévue :


target_vol ≈ 12 %
rolling window ≈ 30 jours


Scaling exposition portefeuille.

---

# Sprint 7 — Diversification

Objectif :

augmenter le nombre de trades.

Pistes :

- nouveaux ETF core
- futures proxies
- secteurs equity

---

# Sprint 8 — Signals additionnels

Objectif :

réduire la dépendance aux tendances rares.

Possibilité :


Donchian 100
+
Donchian 150


---

# Sprint 9 — Execution layer

Objectif :

production d’ordres paper trading.

Scripts :


make_orders.py


---

# Règle de gouvernance

Aucune optimisation sans :

- sensibilité paramètres
- sous-périodes
- Monte Carlo
- justification écrite.
