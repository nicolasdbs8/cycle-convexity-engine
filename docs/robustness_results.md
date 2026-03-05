# Robustness Results

Document de suivi des tests de robustesse.
Objectif : identifier une configuration stable, compréhensible et reproductible.

## Règle d’or
Un test n’est comparable que si :
- même univers (mêmes tickers)
- même mode de sélection (core schedule ON/OFF)
- mêmes coûts
- même runner / même tag
- mêmes dates

## Baseline de travail (référence, non figée)
- Breakout : 150 jours
- Stop : 2.5 × ATR(20)
- Régime : MA52 weekly
- Execution : close t -> open t+1
- Costs : 0.15% round trip (fee 0.1% + slippage 0.05%)
- Risk : max_positions = 3 ; risk_cap_total = 0.06 ; risk_per_trade = 0.015
- Allocation : core 90% / sat 10% (sat souvent OFF dans les runs récents)
- Core selection : `core_top_n` (testé via sweep)

## Événements de dev importants

### E1 — Activation réelle de `core_top_n`
Problème initial : `core_top_n` absent du Config -> sweep “bloqué”.
Fix : ajout au Config, puis relance du sweep => résultats variables => paramètre effectif.

### E2 — Neutralisation possible via `core_monthly.csv`
Si `core_monthly.csv` est présent, le sweep `core_top_n` peut ne rien changer car sélection imposée.
Protocole : supprimer `core_monthly.csv` (ou flag équivalent) lors du sweep.

## Résultats (qualitatif)

### Walk-forward
- 2005–2012 : performance modeste mais généralement survivante
- 2013–2018 : période fréquemment défavorable au trend-following (risque PF < 1 selon config)
- 2019–2026 : meilleure capture des tendances (souvent meilleure perf)

### Sweep `core_top_n`
- l’impact est réel une fois le paramètre activé
- il existe un sweet spot dépendant de l’univers et du mode schedule/dynamic
- règle actuelle : choisir N qui maximise CAGR sans dégrader DD de manière disproportionnée, et avec concentration winners raisonnable

## Interprétation (factuelle)
- le moteur a un “edge trend” mais faible sur core-only
- l’amélioration la plus probable vient :
  - de diversification core + sélection forward (anti-overfit)
  - d’exits (capture winners)
  - de risk portfolio (vol targeting / exposure) mais seulement après protocole stable

## TODO Robustesse (priorité)
1) formaliser un “benchmark run” immuable (tag + univers + dates)
2) produire un tableau standard: baseline + WF + stress MC, à chaque PR
3) intégrer les résultats dans `data/outputs/analysis/` + collect automatique
