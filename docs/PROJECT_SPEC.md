# cycle-convexity-engine
## Architecture systématique de croissance asymétrique multi-actifs

---

# 1. Objectif

Maximiser la croissance géométrique du capital sur un horizon long terme.

Contraintes :

- risque de ruine exclu
- drawdowns acceptés mais contrôlés
- approche entièrement systématique
- validation hors échantillon obligatoire

---

# 2. Philosophie

- aucune discrétion en live
- règles simples et testables
- complexité ajoutée uniquement si edge démontré
- priorité à la robustesse

---

# 3. Architecture générale

## Core Trend Engine

Trend-following multi-actifs basé sur :

- breakout structurel
- filtre de régime
- sizing basé sur volatilité
- risk cap portefeuille

---

# 4. Spécification actuelle

## Régime

MA52 weekly.

Objectif :

- éviter les marchés bear prolongés
- rester exposé en bull markets.

---

## Univers

Core :

ETF liquides :

- SPY
- QQQ
- GLD
- TLT
- USO

Satellite :

crypto large cap :

- BTC
- ETH

Extension future :

top N crypto par liquidité.

---

## Entrée

Close > highest high rolling N jours.

Momentum positif sur 90–180 jours.

---

## Sortie

Stop structurel :

2.5 × ATR.

Sortie régime si marché bear.

---

## Sizing

- volatilité ajustée
- max 3 positions
- risk cap total = 0.06

---

# 5. Anti-biais

- paramètres ronds
- validation sous-périodes
- walk-forward
- Monte Carlo
- audit anti-lookahead

---

# 6. Métriques

- CAGR
- Max Drawdown
- Profit Factor
- temps en drawdown
- distribution Monte Carlo

---

# 7. Architecture cible

Core ETF robuste  
+  
Satellite crypto opportuniste

Objectif :

- stabilité du capital
- convexité dans les phases bull crypto.
