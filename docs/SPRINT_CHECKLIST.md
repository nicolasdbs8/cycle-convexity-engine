# SPRINT_CHECKLIST.md
Projet: cycle-convexity-engine

Checklist opérationnelle (anti-dérive). Objectif: progression vérifiable, pas d’optimisation opportuniste.

## État actuel (snapshot)
- Backtest multi-actifs MVP en place (`src/backtest_multi.py`, `src/portfolio_multi.py`), runner `run_backtest_multi.py`.
- CI GitHub Actions opérationnel (workflow multi) et artifacts (`equity_curve.csv`, `trades.csv`) générés.
- Robustesse déjà explorée (sweep, walk-forward, Monte Carlo) et paramètres “compromis” identifiés.
- Prochaine marche: **structurer proprement CORE ETF (80%) + SAT crypto (20%)** sans casser CI, sans lookahead.

Règles de gouvernance (non négociables)
- 1 changement structurant = 1 PR = 1 note dans `docs/STATE.md` + sortie taggée dans `data/outputs/<tag>/`.
- Aucune “optimisation” sans protocole (sensibilité / sous-périodes / coûts / WFO / MC).
- Toute dynamique d’univers = planifiée, datée, **laggée** (pas de lookahead), et auditable via fichier schedule.

---

## Sprint 0 — Repo & continuité (base CI)
### Definition of Done
- [ ] `docs/PROJECT_SPEC.md` présent et à jour (reflet de l’architecture réelle)
- [ ] `docs/STATE.md` présent et à jour (dernier run de référence + params)
- [ ] `docs/CHATGPT_BOOTSTRAP.md` présent et à jour (comment relancer/itérer sans perdre le contexte)
- [ ] Workflows GitHub Actions OK (run automatique, artefacts uploadés)
- [ ] Données (CSV) présentes dans `data/` + conventions documentées (colonnes, timezone, index)
- [ ] Un run CI “golden” reproductible (mêmes inputs => mêmes outputs)

---

## Sprint 1 — MVP backtester (single-asset)  ✅ (historiquement)
> Sprint conservé pour traçabilité. Le moteur a dépassé ce stade (multi-actifs OK).

### Gates (doivent rester vrais)
- [ ] No-lookahead (breakout via `shift(1)` / warmup cohérent)
- [ ] Exécution next open (entrées/sorties)
- [ ] Coûts appliqués (fees + slippage)
- [ ] Logs/trades et equity cohérents et reproductibles

---

## Sprint 2 — Multi-assets + Risk budget  ✅ (en place)
### Definition of Done (à maintenir)
- [ ] Multi-actifs: univers passé en `--symbols` et panel chargé proprement
- [ ] `PortfolioMulti` gère positions, cash, equity, mark-to-market
- [ ] Risk cap global via **stop-risk budget** + `max_positions`
- [ ] Artifacts: `equity_curve.csv`, `trades.csv` (cols stables) + summary JSON (console)

### Sanity checks (régression)
- [ ] Coûts=0 vs coûts>0 (perf baisse)
- [ ] `max_positions` respecté
- [ ] Risk cap respecté (aucune entrée si budget dépassé)
- [ ] Intersection calendrier maîtrisée (pas de “trous” silencieux)

---

## Sprint 3 — Robustesse (gates “institutionnels”) ✅/⚠️ (à formaliser)
Objectif: figer une baseline et prouver que ce n’est pas un artefact.

### 3.0 Baseline & gouvernance
- [ ] Baseline fixée (params) + commit + tag output
- [ ] `docs/robustness_results.md` mis à jour (résultats synthétiques + conclusions)
- [ ] `docs/STATE.md` inclut: univers, params, période, coûts, hash commit, lien artifact CI

### 3.1 Sensibilité (non-optimisée)
- [ ] breakout_days: 150 / 180 / 220
- [ ] stop_atr_mult: 2.0 / 2.5 / 3.0
- [ ] régime weekly: MA 52 / MA 100 / MA 200 (+ slope on/off si flag)
- [ ] coûts: x1 / x2 (fee + slippage)
- [ ] risk_per_trade: 0.5% / 1.0% / 1.5% (en gardant risk_cap_total constant)

### 3.2 Sous-périodes & WFO
- [ ] Sous-périodes fixes (ex: 2014+, 2016+, 2018+, 2020+ — adapter à la dispo des données)
- [ ] Walk-forward (fenêtres fixées + protocole écrit)
- [ ] Vérifier warmup (equity commence bien à start_date)

### 3.3 Monte Carlo
- [ ] Bootstrap trade returns / R-multiples (5 000 itérations min)
- [ ] EndEquity p10/p50/p90
- [ ] MaxDD p10/p50/p90
- [ ] P(EndEquity < StartEquity) estimée

### Definition of Done Sprint 3
- [ ] Baseline officiellement retenue (ou rejetée) avec justification
- [ ] Robustesse documentée et réplicable (commande + tag + artifact)

---

## Sprint 4 — CORE ETF (80%) + SAT crypto (20%) : sleeves statiques (priorité)
Objectif: 2 sous-portefeuilles **sans casser** le moteur ni le workflow CI.

### Implémentation (minimal, compatible CI)
- [ ] Ajouter dans `src/config.py`:
  - [ ] `core_weight` (0.80)
  - [ ] `sat_weight` (0.20)
  - [ ] `crypto_symbols` (ex: BTC, ETH)
- [ ] Créer `src/sleeves.py`:
  - [ ] split core vs sat
  - [ ] run `run_backtest_multi_mvp` par sleeve (si non vide)
  - [ ] somme des equity curves (index commun)
  - [ ] concat trades + colonne `sleeve`
- [ ] Modifier `run_backtest_multi.py` pour utiliser l’orchestrateur sleeves
- [ ] Artifacts inchangés (au moins): `equity_curve.csv`, `trades.csv`
  - [ ] `trades.csv` inclut `sleeve` (core/sat)
- [ ] Summary JSON conserve les champs existants (compat CI), + champs optionnels sleeve (si facile)

### Gates
- [ ] Risk cap global respecté **par budget**: `risk_cap_total` réparti par poids
- [ ] No-lookahead inchangé (on ne modifie pas la logique de signal/exec)
- [ ] CI passe sans changer la commande (mêmes args `--symbols`, `--tag`)

### Definition of Done Sprint 4
- [ ] Un run CI produit un equity total + trades sleeve-tagés
- [ ] Résultat “golden” taggé (core/sat activés) + note `STATE.md`

---

## Sprint 5 — Config d’univers “propre” (sans code changes pour composer l’univers)
Objectif: piloter core/sat et leurs listes depuis un fichier, pas depuis le code.

- [ ] Ajouter option CLI `--universe_file` (JSON)
- [ ] Format JSON:
  - [ ] `core_symbols`, `sat_symbols`
  - [ ] `core_weight`, `sat_weight`
- [ ] Runner lit le fichier et override `--symbols` (ou ignore `--symbols` si file fournie)
- [ ] CI: décider si on bascule sur `--universe_file` (optionnel)
- [ ] Doc: format, exemple, et “how-to add symbol”

Definition of Done
- [ ] Universe composable sans modifier Python
- [ ] CI stable + artifacts identiques

---

## Sprint 6 — Univers crypto top N mensuel (anti-lookahead, auditable)
Objectif: satellite crypto dynamique **sans biais** (lag 1 mois, univers figé mensuellement).

### Data contract (obligatoire)
- [ ] Définir une source et une proxy (market cap/liquidité) ou un dataset déjà présent
- [ ] Définir candidats (liste large) + critères d’éligibilité (volume min, prix, historique min)

### Pipeline univers
- [ ] `scripts/build_crypto_universe.py`
  - [ ] génère `data/universe/crypto_topN_monthly.csv`
  - [ ] colonnes: month (YYYY-MM-01), symbols (séparés par `;`)
  - [ ] règle: univers du mois M calculé avec données <= fin M-1
- [ ] `src/universe.py`:
  - [ ] loader schedule
  - [ ] `universe_for_date(dt)` (retourne set symbols autorisés)
- [ ] Sleeves SAT:
  - [ ] filtre l’univers **au mois courant** (figé)
  - [ ] pas d’ajout “en cours de mois”

### Tests anti-lookahead (non négociables)
- [ ] test: pour une date au milieu d’un mois, univers == celui du 1er du mois
- [ ] test: pas d’accès à data postérieure à fin mois-1 pour déterminer univers mois M
- [ ] test: si un symbole apparait le mois M, il n’a pas contribué à décider M

Definition of Done
- [ ] Univers mensuel dynamique activé sur SAT, reproductible et auditable
- [ ] Résultats de robustesse mis à jour (WFO/MC au moins sur une période)

---

## Sprint 7 — Execution layer (paper) + ordre du jour quotidien
Objectif: produire des “orders” paper fiables, sans toucher à la logique backtest.

- [ ] `make_orders.py`:
  - [ ] lit le dernier panel + config + univers (core/sat)
  - [ ] produit `orders_today.csv` (ou “EMPTY” explicite)
- [ ] Contrats d’ordres:
  - [ ] symbol, side, qty, limit/market (choix), reason, stop, sleeve, risk
- [ ] Journal quotidien (logs) + kill switch (exposition max, stop global)
- [ ] CI “daily paper” (optionnel): run planifié + artifact orders

Definition of Done
- [ ] Un run quotidien produit des ordres cohérents (ou vide explicite)
- [ ] Checklist opérationnelle exchange rédigée (`docs/ops_checklist.md`)

---

## Sprint 8 — Hardening (qualité “institutionnelle”)
Objectif: réduire les risques d’erreurs silencieuses.

- [ ] Data validation (schéma OHLCV, monotonic dates, duplicates, gaps)
- [ ] Determinism: seed unique + pin deps + export env
- [ ] Tests unitaires minimaux: indicators (ATR, SMA), signal anti-lookahead, sizing/risk cap
- [ ] Lint/format (ruff/black) + pre-commit
- [ ] Packaging minimal (ex: `pyproject.toml`) si pas déjà
- [ ] Documentation “How to reproduce a run” (commande + tag + artifacts)

---

## Backlog (ne pas attaquer avant Sprint 6–8)
- Carry overlay / cash-and-carry
- Dérivés/levier (à traiter comme produit séparé)
- Optimisation (au sens “search”) : seulement après protocole complet et critères d’arrêt
