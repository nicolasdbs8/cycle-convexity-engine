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

## Sprint 2 — Robustesse (avant multi-assets)
### 2.1 Sensibilité paramètres (non-optimisée)
- [ ] breakout_days: 150 / 180 / 220
- [ ] stop_atr_mult: 2 / 3
- [ ] coûts: x1 / x2 (fee+slippage)
- [ ] régime: slope_weeks 10 / 20 / 30 (ronds)

### 2.2 Découpage par régimes
- [ ] Sous-périodes bull / bear / range (qualitatif)
- [ ] Vérifier: “convexité” (gains concentrés) vs “ruine”

### 2.3 Monte Carlo (MVP)
- [ ] Bootstrap des trades (ou shuffle) sur R/PnL
- [ ] Distribution EndEquity
- [ ] Distribution MaxDD
- [ ] Estimation probabilité de ruine technique

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
