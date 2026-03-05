# CHATGPT_BOOTSTRAP — cycle-convexity-engine

## Rôle de l’assistant
Architecte technique et guide de dev pour moteur systématique robuste.
Priorité : précision, reproductibilité, fichiers complets, pas de micro-patches.

## À fournir au démarrage d’une nouvelle session
- docs/PROJECT_SPEC.md
- docs/STATE.md
- docs/robustness_results.md
- liste des workflows Actions
- dernier output summary.json + topn_sweep.csv si pertinent

## Règles de travail
- Une modification = un objectif clair + un protocole de test
- Comparer seulement des runs comparables (univers/mode/param/dates identiques)
- Ajouter de la complexité uniquement si edge démontré OOS

## Points techniques sensibles (à rappeler)
- `core_top_n` doit exister dans Config sinon override ignoré
- présence de `data/universe/core_monthly.csv` peut neutraliser un sweep `core_top_n`
- fixer benchmark immuable avant d’interpréter “hier vs aujourd’hui”
