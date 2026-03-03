# cycle-convexity-engine
## Architecture systématique de croissance asymétrique multi-régime

---

# 1. Objectif

Maximiser la croissance géométrique du capital (log-growth) sur un horizon de 10 ans.

Contraintes :
- Pas de ruine technique (liquidation totale).
- Risque opérationnel maîtrisé.
- Drawdowns acceptés mais structurellement contrôlés.
- Approche 100 % systématique.

---

# 2. Philosophie

- Aucune discrétion en live.
- Règles mathématiquement définies.
- Backtestable, falsifiable.
- Complexité ajoutée uniquement si edge démontré.
- Pas d’optimisation paramétrique au départ.

---

# 3. Architecture Générale

## Phase 1 : Trend Convexity Engine v1
Bloc directionnel basé sur :
- Régime BTC weekly
- Momentum / breakout structurel
- Volatility targeting
- Kill switch strict

## Phase 2 : Carry Overlay v1
Bloc non directionnel basé sur :
- Funding / basis
- Allocation plafonnée
- Levier minimal
- Gestion stricte du risque exchange

---

# 4. Spécification Trend v1 (gelée)

## Régime
- BTC weekly close > MA200 weekly
- MA200 slope positive

## Univers
- BTC + top N actifs par market cap/liquidité
- Univers figé mensuellement
- Exclusion volume insuffisant
- Pas d’optimisation du N

## Entrée
- Close > highest high rolling N jours
- Momentum 90–180 jours positif

## Sizing
- Basé sur ATR / volatilité
- 3–5 positions max
- Levier modéré uniquement si régime bull confirmé

## Sortie
- Kill switch si régime OFF
- Stop structurel mathématique (rolling low ou ATR)

---

# 5. Anti-biais

- Paramètres ronds uniquement
- Validation par sous-périodes
- Monte Carlo obligatoire avant live
- Sensibilité aux coûts testée
- Aucune modification post hoc sur equity curve

---

# 6. Métriques de Validation

- CAGR
- Log-growth
- Max Drawdown
- Temps en drawdown
- Profit factor
- Skew
- Distribution Monte Carlo
- Benchmark vs BTC buy & hold

---

# 7. Règles non négociables

- Pas de scalping retail
- Pas d’interprétation visuelle
- Pas d’ajustement discrétionnaire
- Discipline stricte de versioning
