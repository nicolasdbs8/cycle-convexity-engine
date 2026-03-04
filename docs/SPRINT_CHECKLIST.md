# SPRINT_CHECKLIST.md

Projet : cycle-convexity-engine

Checklist opérationnelle.

---

# Baseline actuelle

breakout = 150  
stop = 2.5 ATR  
regime = MA52  
max_positions = 3  
risk_cap_total = 0.06  

Allocation :

core = 90 %  
sat = 10 %

---

# Sprints terminés

Sprint 1 — Backtester multi-actifs  
Sprint 2 — Filtre de régime  
Sprint 3 — Validation robustesse  
Sprint 4 — Architecture core / satellite  
Sprint 5 — Univers crypto dynamique  

---

# Sprint actuel

Stabilisation du moteur.

---

# Sprint suivant

### Sprint 6 — Position sizing volatilité actif

Objectif :

équilibrer le risque entre actifs.

Implémentation :

position_size ∝ 1 / ATR

---

### Sprint 7 — Exit amélioré

Objectif :

améliorer capture de tendance.

Pistes :

ATR trailing  
ou  
stop Donchian

---

### Sprint 8 — Volatility targeting portefeuille

Objectif :

stabiliser la volatilité du portefeuille.

---

### Sprint 9 — Diversification core

Objectif :

augmenter le nombre de trades.

Pistes :

- nouveaux ETF
- futures proxies
- secteurs equity

---

### Sprint 10 — Execution layer

Objectif :

paper trading.

Script :

make_orders.py
