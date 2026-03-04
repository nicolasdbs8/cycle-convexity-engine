# Robustness Results

Ce document consigne les résultats de robustesse obtenus au cours des différents sprints du projet.

L’objectif est d’identifier une configuration **stable et institutionnelle**, plutôt qu’un optimum opportuniste.

---

# Baseline actuelle (provisoire)

Configuration retenue après itérations :

- Breakout: **150 jours**
- Stop: **2.5 × ATR(20)**
- Régime: **weekly MA52**
- Execution: signal close t, entry open t+1
- Costs: fee 0.1% + slippage 0.05%
- Max positions: **3**
- Risk cap total: **0.06**

Univers actuel :

ETF core  
- SPY  
- QQQ  
- GLD  
- TLT  
- USO  

Crypto satellite (tests exploratoires)  
- BTC  
- ETH  

---

# Historique des tests de sensibilité

## Breakout / Stop / Costs (baseline initiale)

Première phase réalisée sur BTC uniquement.

### Breakout / Stop / Coûts (MA200 initial)

- b180_s2_cost1: CAGR 18.11%, MaxDD -81.47%, Trades 6
- b150_s2_cost1: identique à b180
- b220_s2_cost1: CAGR 7.00%, MaxDD -73.95%, Trades 12
- b180_s3_cost1: CAGR 14.50%, MaxDD -80.12%, Trades 6
- b180_s2_cost2: CAGR 17.96%, MaxDD -81.44%, Trades 6

Observation :
- très peu de trades
- dépendance forte à quelques cycles crypto

---

# Sensibilité du filtre de régime

### Régime MA (full history)

- MA200_full: CAGR 18.11%, MaxDD -81.47%, Trades 6
- MA100_full: CAGR 22.99%, MaxDD -73.29%, Trades 10

Observation :
- MA100 augmente la réactivité
- drawdown légèrement réduit
- nombre de trades plus cohérent

Décision provisoire :
→ abandon MA200

---

# Tests sous-périodes (warmup corrigé)

## 2014+

- MA100: CAGR 9.67%, MaxDD -65.01%, Trades 9
- MA200: CAGR 23.83%, MaxDD -81.47%, Trades 6

## 2016+

- MA100: CAGR 11.68%, MaxDD -65.01%, Trades 9
- MA200: CAGR 11.43%, MaxDD -73.95%, Trades 10

## 2018+

- MA100: CAGR 4.76%, MaxDD -38.60%, Trades 6
- MA200: CAGR 4.57%, MaxDD -53.44%, Trades 8

## 2020+

- MA100: CAGR 7.06%, MaxDD -38.60%, Trades 4
- MA200: CAGR 7.17%, MaxDD -53.44%, Trades 5

Observation générale :

- MA100 domine MA200 sur toutes les sous-périodes récentes
- MA200 produit des drawdowns extrêmes

Décision :
→ abandon définitif MA200

---

# Passage au multi-asset

Extension du moteur vers un univers multi-actifs :

- BTC
- ETH
- SPY
- QQQ
- GLD
- TLT
- USO

Objectif :
tester la robustesse du signal breakout au-delà de la crypto.

Résultat :

Configuration retenue après sweep :

- breakout ≈ 150
- stop ≈ 2.5 ATR
- regime ≈ MA52 weekly

Performance typique :

- CAGR ≈ 8–9 %
- MaxDD ≈ -25 %
- Profit Factor ≈ 2–3
- Trades ≈ 20–25

Observation :

Le moteur reste profitable **hors crypto**, ce qui indique un edge structurel.

---

# Validation Walk-Forward (ETF only)

Walk-forward réalisé sur :

- SPY
- QQQ
- GLD
- TLT
- USO

Configuration :

- train: 10 ans
- test: 3 ans
- step: 2 ans
- période totale: 2006–2026

Résultats :

- Splits: **4**

### Statistiques globales

- Median CAGR: **6.98%**
- Min CAGR: **0.28%**
- Median ProfitFactor: **6.61**
- Min ProfitFactor: **1.45**
- Median MaxDD: **-17.7%**
- Worst MaxDD: **-21.7%**

Observation :

- aucun split perdant
- profit factor toujours > 1
- drawdown contenu

Conclusion :

→ **le moteur est robuste sur ETF hors échantillon**

---

# Analyse crypto

Tests exploratoires sur :

- BTC
- ETH

Résultat :

- amélioration possible du CAGR
- volatilité accrue
- risque de dépendance aux bull markets crypto

Décision actuelle :

→ crypto utilisé comme **satellite**, pas comme cœur du moteur.

---

# Conclusion actuelle

Le moteur présente les caractéristiques suivantes :

- Edge structurel de trend following
- Robustesse multi-actifs
- Validation walk-forward ETF
- Paramètres relativement stables

Configuration provisoire retenue :

- breakout = 150
- stop = 2.5 ATR
- regime = MA52 weekly
- max positions = 3
- risk cap total = 0.06

Architecture cible :

Core ETF  
+  
Satellite crypto

---

# Prochaines étapes

1. Implémenter **allocation core / satellite**
2. Ajouter **univers crypto dynamique (top N mensuel)**
3. Ajouter **filtre liquidité crypto**
4. Ajouter **sensibilité volatilité**
5. Étendre walk-forward au moteur combiné
