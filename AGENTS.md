# Point d’entrée du projet

## But et périmètre

POC de cohérence économique des matières premières, actuellement Oil & Gas : collecte de clôtures quotidiennes, consultation par famille/zone et comparaison d’un prix fourni à une série de référence. Python 3.10+, SQLite, requests ; interface locale Flask sur le port 5003.

Le socle couvre 20 couples famille/zone, 18 benchmarks et 7 génériques Yahoo. Les prix stockés et la commande `prices` restent natifs ; `deltas` convertit les références en USD/MT avec les coefficients fixes du catalogue. Aucune conversion implicite, interpolation, estimation de fret ou certification d’équivalence Bloomberg. Les notes de recherche dans `docs/` donnent le contexte, pas des instructions d’implémentation.

## Architecture à connaître

- `oilgas/cli.py` : parsing argparse, orchestration, affichage et codes de sortie.
- `oilgas/store.py` : unique propriétaire du schéma et des requêtes métier, initialisation, enregistrements atomiques et archives brutes.
- `oilgas/sources.py` : Yahoo HTTP, reprises, parsing et validation Yahoo/CSV.
- `oilgas/deltas.py` : `calculate_deltas` partagé par CLI/UI ; conversion explicite en USD/MT, delta relatif ; `emit_deltas` conserve la sortie CLI compacte.
- `oilgas/web.py`, `oilgas/templates/`, `oilgas/static/` : interface Flask locale, formulaire et graphique SVG. Lancement `python -m oilgas.web`, port 5003, option `--db`.
- `tests/browser_checks.py` : environnement Playwright autonome, base temporaire, captures desktop dans `artifacts/ui/` ; libérer le port 5003 avant lancement.
- `oilgas/catalog.json` : configuration initiale des couples, benchmarks et sources ; section `conversions` indexée exactement par benchmark puis unité native.
- `tests/` : unittest, bases temporaires et Yahoo simulé.
- `docs/architecture.md` : description détaillée du stockage et des invariants.
- `README.md` : installation, usage CLI et format des imports externes.
- `data/oil_gas.sqlite`, `data/raw/` : données locales ignorées par Git ; ne pas supprimer ni remplacer sans préserver les données utiles.

## Contraintes du stockage

Feux tables : `metadata` et `prices`. Aucun code de migration permanent : conserver uniquement création et entretien de la base.

`metadata` contient famille/zone/POL-POD, benchmark et unité attendue, paramètres des sources et bornes observées. Une ligne par couple et série ; une ligne sans série pour les références non couvertes. Les champs source supplémentaires ont été explicitement acceptés par l’utilisateur.

`prices` contient strictement `date`, `price`, `metadata_id`. Clé primaire `(metadata_id,date)`, clé étrangère vers `metadata.id`. Les bornes de `metadata` sont les MIN/MAX des prix présents, nulles sans données. Les paramètres `start`/`end` de collecte ne sont pas les bornes de couverture.

Une série peut servir plusieurs couples (ex. Brent). Dédupliquer les téléchargements par `series_id`, mais enregistrer les observations pour chacun des `metadata_id` associés dans une même transaction. Ne pas fusionner les sources alternatives. Conserver l’atomicité et remplacer les révisions sans doublons.

Pas d’historique d’ingestions ni de provenance par prix dans SQLite. Les fichiers bruts restent archivés et les rapports de collecte portent chemin/SHA-256/avertissements. `last_status`/`last_error` décrivent la dernière tentative. Le CSV `contract` est accepté mais non stocké en base.

## Commandes utiles

À lancer depuis la racine ; `.venv` est l’environnement local existant :

```bash
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m oilgas.web
# Vérification navigateur (port 5003 libre) :
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m playwright install chromium
.venv/bin/python -m tests.browser_checks
.venv/bin/python -m oilgas --help
.venv/bin/python -m oilgas init
.venv/bin/python -m oilgas catalog --format csv
.venv/bin/python -m oilgas coverage
.venv/bin/python -m oilgas prices --family 'Crude Oil (Brut)' --zone 'Europe / Afrique' --start 2024-01-01 --end 2024-01-31
.venv/bin/python -m oilgas deltas --price 733 --family 'Crude Oil (Brut)' --zone 'Europe / Afrique' --start 2024-01-01 --end 2024-01-31
.venv/bin/python -m oilgas fetch --series yahoo-brent --start 2024-01-01 --end 2024-01-31
.venv/bin/python -m oilgas update
.venv/bin/python -m oilgas register-series --file serie.json
.venv/bin/python -m oilgas import-csv --series externe-gasoil --file prix.csv
```

`--db chemin.sqlite` se place **avant** la sous-commande de la CLI ; pour le serveur, utiliser `python -m oilgas.web --db chemin.sqlite`. Pour les vérifications, préférer une base temporaire et les tests hors réseau. `fetch`/`update` modifient les données et utilisent le réseau.

## Comportements à préserver

- UI : seule fonctionnalité delta, correspondance directe des champs CLI, desktop uniquement ; palette sobre du projet voisin `../benchmark_hscode_matching`, aucune accroche décorative.
- UI uniquement : appliquer EUR/USD = 1,12 si nécessaire et non renseigné, afficher le taux utilisé ; ne pas modifier le comportement CLI. Partager le calcul, ne pas lancer de sous-processus CLI.
- Graphique : barres indépendantes autour de zéro, axe symétrique, même couleur pour + et − de même amplitude. Pas de zones vertes ni seuils métier inventés. Afficher les dates réelles, sans interpolation ni cumul.
- Toutes les commandes ci-dessus ; `--series` pour choisir une source, JSON/CSV pour catalog/coverage/prices.
- Dates ISO, périodes inclusives, collecte jusqu’à hier, tranches annuelles ; update reprend dix jours inclusifs depuis la dernière observation.
- Prix négatifs et zéro acceptés ; non finis rejetés ; clôtures nulles Yahoo ignorées avec avertissement. Dates Yahoo dans le fuseau de la place.
- Imports CSV atomiques ; impossibilité d’écraser une source Yahoo par CSV.
- `deltas --price` est toujours en USD/MT. Convertir la référence avec la table explicite `(benchmark_id, native_unit)` du catalogue ; ne jamais inférer un coefficient depuis la famille. Brent conserve 7,33 même pour la route essence. Coefficients moyens et limites : `docs/normalisation.md`.
- `--eur-usd` est obligatoire pour les références EUR, exprime les USD pour 1 EUR et reste constant sur la période. Aucun téléchargement ni taux par défaut. Sur les références USD, un taux fourni est validé mais non appliqué.
- Delta = `(prix fourni - référence convertie) / référence convertie`, en ratio (0.25 = +25 %). Refuser conversion absente, devise incompatible, coefficient/taux non positif ou non fini, référence nulle, valeurs non finies et ambiguïté entre sources. Pas de conversion du jet de Singapour tant qu’un coefficient n’est pas explicitement documenté.
- Ne pas réécrire les prix ni changer le schéma pour la normalisation ; les imports externes utilisent la même table de conversion sans modifier le format de déclaration.
- Sortie deltas lisible : un bloc `ref` avec exactement `logic`, `reference`, `expected_unit`, `instrument`, puis une liste de paires `[date, delta]`, une paire par ligne. Dans cette sortie, `expected_unit` vaut toujours `USD/MT` (la métadonnée SQL garde l’unité du benchmark). Pas de provenance ni statistiques supplémentaires.
- Code 0 succès, 1 erreur métier/absence de données/collecte vide, 2 syntaxe argparse. Erreurs sur stderr ; pas de résultat partiel pour les deltas.

Mettre à jour README/docs et ce fichier lorsque l’architecture ou les contrats changent. Respecter les modifications utilisateur déjà présentes dans Git. Garder les tests dans `tests/` et la documentation détaillée dans `docs/`.
