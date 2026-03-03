# SPRINT_CHECKLIST.md
Projet: cycle-convexity-engine

Ce document est la checklist opérationnelle. Il sert à:
- ne rien oublier,
- éviter les dérives,
- garder une progression vérifiable.

---

## Sprint 0 — Repo & continuité (DONE quand validé)
- [ ] `docs/PROJECT_SPEC.md` présent et à jour
- [ ] `docs/STATE.md` présent et à jour
- [ ] `docs/CHATGPT_BOOTSTRAP.md` présent et à jour
- [ ] Workflow GitHub Actions `backtest.yml` OK
- [ ] Données BTC daily en CSV dans `data/`
- [ ] Premier run Actions OK (artefacts `equity_curve.csv`, `trades.csv`)

---

## Sprint 1 — MVP backtester (BTC single-asset)
### 1.1 Data & indicateurs
- [ ] Loader robuste (tri dates, numeric coercion, NaN handling)
- [ ] Indicateurs:
  - [ ] SMA
  - [ ] ATR (TR + moyenne)
  - [ ] rolling high + `shift(1)` anti-lookahead
  - [ ] momentum return (simple)
- [ ] Alignement weekly -> daily pour le régime

### 1.2 Exécution & coûts
- [ ] Entrée: signal au close t, exécution au open t+1
- [ ] Sortie régime: décision au close t, exécution open t+1
- [ ] Stop intraday: si low <= stop, exit stop (avec slippage/fees)
- [ ] Fees + slippage appliqués sur chaque entrée/sortie (notional)
- [ ] Mode spot-only (pas de levier) pour MVP

### 1.3 Logs & artefacts
- [ ] `data/outputs/equity_curve.csv`
- [ ] `data/outputs/trades.csv` avec colonnes:
  - entry_date, entry_price, entry_fee, signal_date, qty, stop_price,
    exit_date, exit_price, exit_fee, exit_reason, pnl
- [ ] Résumé console JSON:
  - StartEquity, EndEquity, CAGR, MaxDD, NumTrades, HitRate, ProfitFactor

### 1.4 Sanity checks obligatoires
- [ ] Run reproductible (mêmes inputs => mêmes outputs)
- [ ] Test coûts=0 vs coûts>0 (PnL doit baisser)
- [ ] Vérif anti-lookahead:
  - rolling high utilisé via `shift(1)`
  - régime weekly forward-fill uniquement
- [ ] Vérifier qu’on n’ouvre jamais une position sans pouvoir la payer (spot)

---

## Sprint 2 — Robustesse (GATES avant multi-assets)

### 2.0 Baseline & gouvernance
- [ ] Baseline fixée et commitée (régime MA100 weekly par défaut)
- [ ] Chaque modification stratégique = 1 commit + tag output + note dans STATE.md
- [ ] Résultats clés consignés dans `docs/robustness_results.md`

### 2.1 Sensibilité paramètres (non-optimisée)
- [ ] breakout_days: 150 / 180 / 220
- [ ] stop_atr_mult: 2 / 3
- [ ] coûts: x1 / x2 (fee+slippage)
- [ ] régime: MA100 / MA200 (weekly) avec warmup

### 2.2 Tests sous-périodes (avec warmup correct)
- [ ] 2014+ : MA100 vs MA200
- [ ] 2016+ : MA100 vs MA200
- [ ] 2018+ : MA100 vs MA200
- [ ] 2020+ : MA100 vs MA200
- [ ] Vérifier que l’equity_curve commence bien à start_date

### 2.3 Audit anti-lookahead (obligatoire)
- [ ] rolling high utilisé via `shift(1)` (preuve par test)
- [ ] pas de futur dans ATR (preuve par test)
- [ ] régime weekly forward-fill uniquement (preuve par test)
- [ ] entrée toujours au next open (preuve par test)
- [ ] stop intraday ne lit pas high/low futur (preuve par logique + test)

### 2.4 Monte Carlo (MVP)
- [ ] Bootstrap des trades (PnL ou returns) 5 000 itérations
- [ ] Distribution EndEquity (p10/p50/p90)
- [ ] Distribution MaxDD (p10/p50/p90)
- [ ] Estimation simple probabilité EndEquity < StartEquity

### Definition of Done Sprint 2
- [ ] Baseline MA100 confirmée OU rejetée par résultats
- [ ] robustesse documentée (docs/robustness_results.md)
- [ ] lookahead audit terminé
- [ ] monte carlo terminé

---

## Sprint 3 — Multi-assets (top N liquidité)
- [ ] Définir univers mensuel (règle figée)
- [ ] Filtre volume minimum
- [ ] Max positions (3–5)
- [ ] Sizing par volatilité (budget risque total)
- [ ] Logs par symbol

---

## Sprint 4 — Carry overlay (phase 2)
- [ ] Data funding/basis (source définie)
- [ ] Implémentation cash-and-carry (spot + short perp)
- [ ] Risk caps stricts (allocation max, levier minimal)
- [ ] Gestion marge/liquidation
- [ ] Tests d’incidents (missing funding data, gaps, etc.)

---

## Sprint 5 — Paper trading / pré-prod
- [ ] Génération orders “paper”
- [ ] Journal quotidien
- [ ] Règles d’arrêt (kill switch, limites exposition)
- [ ] Checklist opérationnelle exchange

---
