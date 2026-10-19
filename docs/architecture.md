# Architecture

Le projet collecte des prix quotidiens Oil & Gas, les consulte par famille et zone, puis calcule une série de deltas relatifs pour un prix fourni. Les prix stockés restent dans leur unité native ; `deltas` les convertit explicitement en USD/MT au moment du calcul. Il n’y a ni estimation de fret, ni interpolation, ni conversion implicite.

## Organisation

| Chemin | Rôle |
| --- | --- |
| `oilgas/__main__.py` | Entrée `python -m oilgas` |
| `oilgas/cli.py` | Arguments, orchestration de collecte/import, JSON/CSV, codes de sortie |
| `oilgas/store.py` | Schéma, initialisation idempotente, requêtes, enregistrement atomique, archives brutes |
| `oilgas/sources.py` | HTTP Yahoo avec reprises, validation Yahoo/CSV et prix finis |
| `oilgas/deltas.py` | Calcul partagé CLI/UI via `calculate_deltas` et restitution CLI via `emit_deltas` |
| `oilgas/web.py` | Application Flask locale, formulaire, validation et géométrie SVG |
| `oilgas/templates/`, `oilgas/static/` | Page desktop, CSS et interactions JavaScript sans dépendance externe |
| `oilgas/catalog.json` | Configuration initiale : 20 couples, 18 benchmarks, 7 sources Yahoo et table de conversion explicite |
| `tests/` | Tests unitaires et parcours CLI hors réseau |
| `docs/` | Architecture et notes de recherche |
| `data/` | SQLite et fichiers bruts locaux, ignorés par Git |

Les listes `routes`, `benchmarks` et `series` du JSON sont une configuration de démarrage ; elles ne correspondent pas à des tables SQL.

## Deux tables

### `metadata`

Une ligne correspond à un couple famille/zone et une série. Les références sans source ont une ligne dont `series_id` est nul.

| Colonnes | Signification |
| --- | --- |
| `id` | Identifiant de métadonnées référencé par les prix |
| `family`, `zone`, `logic` | Routage produit et logique POL/POD |
| `benchmark_id`, `reference`, `bloomberg_ticker` | Identifiant et description de la référence recherchée |
| `expected_unit` | Unité attendue du benchmark |
| `start_date`, `end_date` | Première et dernière dates effectivement présentes ; nulles sans prix |
| `series_id`, `provider`, `symbol`, `instrument`, `exchange` | Identification de la source à collecter/importer |
| `currency`, `unit`, `price_field` | Devise, unité native et champ de prix |
| `roll_rule`, `qualification`, `notes`, `enabled` | Qualification de la source et sélection pour collecte automatique |
| `last_status`, `last_error` | Résultat de la dernière tentative ; pas un historique |

Une contrainte d’unicité porte sur `(family, zone, series_id)`. Un index unique partiel interdit plusieurs lignes sans source pour le même couple. Le premier enregistrement externe sur une référence sans source réutilise cette ligne. L’initialisation ne la recrée pas ensuite.

### `prices`

| Colonne | Type | Rôle |
| --- | --- | --- |
| `date` | TEXT | Date de cotation ISO `YYYY-MM-DD` |
| `price` | REAL | Prix brut dans l’unité native, éventuellement nul ou négatif |
| `metadata_id` | INTEGER | Clé étrangère vers `metadata.id` |

La clé primaire est `(metadata_id, date)`. Les valeurs absentes sont rejetées ou ignorées à l’entrée selon le fournisseur ; un prix égal à zéro reste une observation valide.

## Entretien

`initialize` crée le schéma et complète le catalogue sans écraser les métadonnées déjà présentes. `register_series` déclare une source CSV pour tous les couples de son benchmark. Les déclarations invalides ou dupliquées échouent.

`selected` déduplique les séries : une source partagée n’est téléchargée qu’une fois. `record` enregistre les observations dans tous les couples associés, remplace les prix révisés et recalcule `MIN(date)`/`MAX(date)` dans la même transaction. Un échec d’écriture annule l’ensemble de la tranche. Une collecte vide ou en échec conserve les prix et leurs bornes, et actualise le dernier statut.

`fetch` découpe la période en années. `update` repart neuf jours avant la dernière observation (dix jours inclusifs), sans remonter avant 2020. Les bornes sont inclusives et les collectes s’arrêtent au plus tard hier. Les jours sans observation ne sont pas reconstruits.

Les réponses Yahoo et CSV sont archivées en gzip, nommées par SHA-256. Les rapports de collecte incluent le chemin, l’empreinte et les avertissements. Les tables ne conservent ni historique d’ingestion ni rattachement de chaque prix à une archive. La colonne CSV facultative `contract` est acceptée, mais reste seulement dans le fichier brut.

## Consultation et deltas

`prices` joint seulement `metadata` et `prices`, filtre les bornes inclusives et trie par série puis date. `catalog` et `coverage` incluent les références sans prix. La couverture est présentée par ligne de métadonnées : les références partagées apparaissent pour chaque couple.

`deltas` exige une seule série observée, à sélectionner avec `--series` si nécessaire. Il recherche exactement le couple `(benchmark_id, native_unit)` dans la section `conversions` du catalogue, vérifie la devise déclarée et applique le coefficient fixe. Les lignes renvoyées par `prices` comprennent aussi `benchmark_id` et `currency`, sans modification des prix natifs. Pour une référence en EUR, `--eur-usd` est obligatoire et constant sur la période. Le prix fourni est toujours en USD/MT. Le ratio est `(prix_fourni - référence_convertie) / référence_convertie` : `0.25` signifie +25 %. Une conversion absente, une devise incompatible, un coefficient/taux non positif ou non fini, une référence nulle ou un résultat non fini provoque une erreur sans sortie partielle. Sortie : uniquement `ref` (logic, reference, expected_unit, instrument) et `deltas` (paires date/ratio, une par ligne). `ref.expected_unit` vaut toujours `USD/MT` ; la colonne SQL `expected_unit` reste l’unité originale du benchmark. Les coefficients et leur usage sont détaillés dans [normalisation.md](normalisation.md).

## Interface Flask

`python -m oilgas.web` démarre sur `127.0.0.1:5003`, sans debug. `--db` sélectionne la base ; le schéma et le catalogue sont initialisés au lancement. GET `/` présente le formulaire ; POST `/` appelle `price_rows`, puis le même `calculate_deltas` que la CLI. Aucun sous-processus CLI ni redirection de stdout. Les requêtes de calcul ne modifient pas les observations.

Les champs correspondent à `price`, `family`, `zone`, `series`, `start`, `end`, `eur_usd`. La sélection des zones et sources est filtrée par les métadonnées. Seule différence de calcul entre CLI et UI : une référence EUR sans taux saisi reçoit 1,12 dans la couche Flask. Le taux utilisé est affiché. Toute valeur explicite est validée, y compris zéro ; elle ne déclenche jamais le défaut.

Le graphique SVG utilise des barres quotidiennes non cumulées, espacées selon leurs dates, sur un axe symétrique. Pour chaque delta `d`, la teinte interpole du terre clair au rouge sombre selon `abs(d)/(abs(d)+0.15)` : simple intensité visuelle continue, sans catégorie ni seuil de risque. Le signe ne change pas la couleur. L’amplitude moyenne est la moyenne des valeurs absolues. Le maximum affiché conserve son signe et sa date. Les longues séries défilent sans agrégation ; les valeurs sont accessibles au survol, au clavier et dans le tableau. Un changement de paramètres retire le résultat précédent.

Les erreurs métier répondent en HTTP 400 avec un message et le formulaire conservé, sans graphique partiel. La page est locale, desktop, sans moteur graphique distant ni collecte automatique.

## Validation

Depuis la racine : `.venv/bin/python -m unittest discover -s tests -v`. Les appels Yahoo sont simulés ; les tests n’exigent pas de réseau. Ils couvrent les validations de sources, les commandes, les deux tables, les clés étrangères, les bornes, les sources partagées, la réimportation, l’atomicité et le formulaire Flask.

Pour vérifier le rendu : installer `requirements-dev.txt` et Chromium avec `python -m playwright install chromium`, puis lancer `.venv/bin/python -m tests.browser_checks` avec le port 5003 libre. Le parcours utilise une base temporaire et produit les captures dans `artifacts/ui/`.

Les autres documents de `docs/` sont des notes de recherche ou des rapports datés : leurs propositions ne constituent pas des fonctionnalités déjà implémentées. Le README et ce document décrivent le fonctionnement actuel.
