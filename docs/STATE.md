# STATE.md

## Version
v0.5.0 (branche `core-monthly`)

## Ce qui est implémenté

### Backtest multi-actifs
- Exécution : signal sur `close[t]`, entrée sur `open[t+1]`
- Coûts : fee + slippage
- Stops intraday (selon implémentation)
- Logs : `equity_curve.csv`, `trades.csv`, `summary.json`

### Indicateurs
- SMA (daily + weekly aggregate selon modules)
- ATR
- Rolling highs/lows anti-lookahead
- Momentum (cross-asset)

### Architecture core / satellite
- `src/sleeves.py` orchestre :
  - sleeve core (ETF)
  - sleeve satellite (crypto, optionnel)
  - agrégation et éventuel vol targeting

### Univers dynamique
- crypto : `scripts/make_crypto_monthly.py` -> `data/universe/crypto_monthly.csv`
- core : `data/universe/core_monthly.csv` (si utilisé) ou sélection “dynamic” via panel

## Découvertes / fixes récents

### Fix 1 — `core_top_n` ignoré
Cause : `core_top_n` absent de `Config`, donc les overrides CLI/workflows n’avaient aucun effet.
Fix : ajout du champ `core_top_n` dans `src/config.py`.

### Fix 2 — confusion “schedule vs dynamic”
Si `data/universe/core_monthly.csv` existe, la sélection core est figée par fichier et peut neutraliser un sweep `core_top_n`.
Protocole : pour tester l’effet de `core_top_n`, supprimer/ignorer le schedule core dans le workflow.

## Résultats récents (core-only)

Observations générales :
- Le moteur “survit” aux cycles (pas d’effondrement complet)
- Certaines périodes sont défavorables (trend faible/latent)
- La perf agrégée core-only est modeste (CAGR typiquement ~2–3% dans plusieurs runs), avec DD ~15–20%

⚠️ Les variations proviennent souvent de :
- univers (taille/constituants)
- mode selection core (schedule/dynamic)
- paramètres modifiés (breakout, max_positions, vol target)
- activation/désactivation satellite crypto

## Limites actuelles (factuelles)
- CAGR faible en core-only sur plusieurs configurations
- périodes 2013–2018 fréquemment difficiles (PF proche de 1 ou <1 dans certains runs)
- concentration winners encore limitée sur certains runs (top winners pas “énormes”)

## Prochain objectif (ordre)
1) verrouiller un protocole d’évaluation reproductible (mêmes univers + même mode selection + mêmes tags)
2) forward-universe (sélection out-of-sample) sur un pool ETF élargi
3) améliorer les sorties / la capture des winners (exit logic) avec tests A/B stricts
4) (optionnel) réintégration satellite crypto avec garde-fous
5) préparation paper trading
