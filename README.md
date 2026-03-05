# cycle-convexity-engine

Moteur de trading systématique robuste (trend following) orienté **croissance géométrique** long-terme, conçu pour survivre aux cycles plutôt que pour optimiser un backtest.

## Objectif

Construire un moteur **100% systématique**, modulaire et auditable, visant :
- maximisation de la croissance géométrique du capital (long terme)
- robustesse prioritaire sur la perf brute
- validation hors-échantillon (walk-forward) obligatoire
- aucune discrétion humaine en live

## Architecture

Trend-following multi-actifs **core / satellite** :

- **Core (≈90%)** : ETF macro/liquides, rôle stabilisateur et “beta trend”.
- **Satellite (≈10%)** : crypto opportuniste, rôle convexité (optionnel, activable ensuite).

> IMPORTANT : la branche `core-monthly` a surtout été testée en **core-only** récemment.
> La perf "très bonne" observée parfois venait souvent d’un mix de paramètres + contexte (univers, crypto on/off, selection active, etc.).

## Exécution / Hypothèses

- Signal : basé sur `close[t]`
- Entrée : `open[t+1]`
- Coûts : fee + slippage appliqués à l’entrée et à la sortie
- Gestion portefeuille : `max_positions`, `risk_cap_total`, `risk_per_trade`
- Régime : filtre MA weekly (MA52) (et option slope selon config)

## Paramètres (référence de travail)

Ces paramètres changent via tests; ne pas les considérer comme “définitifs”.

- Breakout : 150 jours (tests également à 120, 90)
- Stop : 2.5 × ATR(20)
- Régime : MA52 weekly
- Execution : close t -> open t+1
- Costs : fee = 0.1% ; slippage = 0.05%
- Risk : max_positions = 3 ; risk_cap_total = 0.06 ; risk_per_trade = 0.015

### Core selection (momentum cross-asset)

Le core peut être filtré par une sélection “Top-N momentum” :

- paramètre : `core_top_n`
- fréquence : mensuelle (ré-évaluée, mais pas de lookahead)
- mode 1 (schedule) : `data/universe/core_monthly.csv` existe -> sélection imposée par fichier
- mode 2 (dynamic) : si le schedule est absent -> sélection calculée on-the-fly depuis le panel

**Point clé découvert :**
- tant que `core_monthly.csv` existe, le sweep `core_top_n` peut être neutralisé car la sélection est déjà figée par le fichier.
- `core_top_n` a été initialement ignoré car absent de `Config` (bug corrigé).

## Univers

Core ETF (base + extensions en test) :
- SPY, QQQ, IWM, EFA, EEM, GLD, TLT, IEF, SHY
- (candidats ajoutés selon sprint : secteurs US, matières premières, pays, etc.)

Satellite crypto (large caps) :
- BTC, ETH, BNB, SOL, XRP, ADA, DOGE, TRX, LINK

### Univers crypto dynamique

Pipeline :
- `scripts/make_crypto_monthly.py` -> `data/universe/crypto_monthly.csv`
- recalcul mensuel
- univers figé pendant le mois
- anti-lookahead strict

## Repo / Modules

`src/`
- `config.py` : configuration et paramètres
- `indicators.py` : SMA/ATR/rolling highs/lows, momentum, etc.
- `strategy.py` : logique de signal
- `regime.py` : filtre de régime
- `portfolio_multi.py` : positions / sizing / risk caps
- `backtest_multi.py` : moteur backtest
- `sleeves.py` : core/sat + agrégation
- `universe.py` : schedules / univers dynamiques

`scripts/`
- `fetch_yahoo.py` : data fetch
- `make_crypto_monthly.py` : univers crypto mensuel
- `make_core_monthly.py` : (si présent) univers core mensuel
- `walk_forward.py` : tests WF
- `monte_carlo.py` : stress / bootstrap
- `collect_*` : agrégation de résultats (workflows)

`run_backtest_multi.py` : runner principal

Outputs :
- `data/outputs/<tag>/equity_curve.csv`
- `data/outputs/<tag>/trades.csv`
- `data/outputs/<tag>/summary.json`

## Workflows (GitHub Actions)

- `multi-mvp` : baseline + walk-forward (+ parfois sizing sweep)
- `core-topn-sweep` : sweep `core_top_n` (nécessite d’ignorer `core_monthly.csv` si on veut tester l’effet réel)
- `ablation` / `collect` : tests d’ablation + consolidation (si maintenus à jour)

## État actuel (résumé)

- Core selection : désormais testable et paramétrable via `core_top_n`
- Validation : walk-forward OK (survival) mais perf faible/modeste sur certaines périodes
- Le moteur est stable; l’edge est présent mais encore faible en CAGR sur core-only
- Prochain focus : consolider un protocole de tests “non-confusant” (mêmes univers, mêmes modes, mêmes paramètres) puis itérer sur les sorties / le portefeuille / la diversification de manière contrôlée.

Voir `docs/STATE.md` et `docs/robustness_results.md`.
