# SPRINT_CHECKLIST — cycle-convexity-engine

## Baseline (référence de travail)
- breakout: 150
- stop: 2.5 * ATR(20)
- regime: MA52 weekly
- costs: fee 0.1% / slippage 0.05%
- max_positions: 3
- risk_cap_total: 0.06
- risk_per_trade: 0.015
- core_top_n: variable (sweep)
- core schedule: ON/OFF selon test

## Sprints terminés
1) Backtester multi-actifs + outputs standard
2) Filtre de régime
3) Validation robustesse initiale (WF + MC)
4) Architecture core/satellite (`sleeves.py`)
5) Univers crypto mensuel (anti-lookahead)
6) Core selection (Top-N) + debug param `core_top_n`

## Sprint actuel — Normalisation des tests
Objectif : arrêter les comparaisons “non-comparables”.

Checklist :
- [ ] benchmark universe figé (liste tickers)
- [ ] benchmark dates figées
- [ ] benchmark mode : core schedule ON/OFF explicite
- [ ] tags standardisés (baseline / wf_2005_2012 / etc.)
- [ ] collect automatique des summaries en un CSV unique

## Sprint suivant — Forward universe (core)
Objectif : sélectionner un univers ETF élargi sans lookahead.

Livrables :
- workflow “forward_universe” (build -> evaluate -> select)
- output: data/universe/core_forward.csv
- rapport : perf OOS par ajout d’actifs (greedy / stepwise)

## Sprint 8 — Exits
Objectif : améliorer capture des winners sans complexité excessive.
- candidates : Donchian exit / MA exit / ATR trailing “proper”
- protocole : A/B strict avec benchmark immuable

## Sprint 9 — Volatility targeting portefeuille
Objectif : stabiliser la vol sans tuer le CAGR.
- scaler borné (min/max)
- métriques : vol réalisée, DD, CAGR

## Sprint 10 — Execution layer (paper trading)
Objectif : produire orders + logs journaliers, sans discrétion.
