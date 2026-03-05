# PROJECT_SPEC — cycle-convexity-engine

## 1) Objectif
Maximiser la croissance géométrique du capital long-terme avec un moteur robuste, modulaire et auditable.

Contraintes :
- 100% systématique (aucune discrétion live)
- règles simples, testables, versionnées
- validation hors-échantillon obligatoire
- robustesse > optimisation fragile

## 2) Architecture
Core / Satellite
- Core : ETF trend engine (macro, stabilisateur)
- Satellite : crypto opportuniste (convexité, optionnel)

## 3) Signal (concept)
Trend-following :
- breakout structurel
- filtre de régime
- sizing basé sur le risque
- risk caps portefeuille

Exécution :
- signal sur close[t]
- entry sur open[t+1]
- coûts sur chaque entrée/sortie

## 4) Sélection d’univers

### Crypto (satellite)
- univers mensuel recalculé
- figé dans le mois (anti-lookahead)
- output: data/universe/crypto_monthly.csv

### Core (ETF)
Deux modes :
1) schedule (fichier) : data/universe/core_monthly.csv
2) dynamic (calcul on-the-fly) : ranking momentum depuis le panel

Paramètre :
- core_top_n : nombre d’actifs autorisés par période (si mode dynamic)

## 5) Validation & protocole
- backtest global
- walk-forward
- sensitivity tests (param sweeps)
- Monte Carlo (stress)
- audit anti-lookahead

## 6) Mesures suivies
- CAGR
- MaxDD
- Profit Factor
- NumTrades
- distribution des gains (Top1/Top3/Top5)
- stabilité par segments WF

## 7) Critères de succès (phase core-only)
- PF > 1.2 global + non catastrophique sur segments WF
- DD contrôlé et stable
- pas d’edge “single-period only”
- protocole reproductible et automatisé via Actions

## 8) Phase suivante (une fois core stable)
- forward universe selection (out-of-sample)
- amélioration exits
- volatility targeting portefeuille
- paper trading
- réintégration satellite crypto (avec garde-fous)
