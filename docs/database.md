# Base de données

## Table `metadata`

Description des familles, corridors, références et sources de prix. Une ligne par couple famille/corridor et source ; une ligne sans source pour les couples non couverts.

| Attribut | Type SQLite | Contenu |
| --- | --- | --- |
| `id` | INTEGER | Identifiant unique de la ligne, clé primaire. |
| `family` | TEXT NOT NULL | Famille de matière première. |
| `zone` | TEXT NOT NULL | Corridor ou zone géographique. |
| `logic` | TEXT NOT NULL | Port de chargement (`POL`) ou de déchargement (`POD`). |
| `benchmark_id` | TEXT NOT NULL | Identifiant de la référence de prix. |
| `reference` | TEXT NOT NULL | Nom de la référence de prix. |
| `expected_unit` | TEXT NOT NULL | Unité attendue pour la référence. |
| `bloomberg_ticker` | TEXT NOT NULL | Code Bloomberg de la référence. |
| `series_id` | TEXT | Identifiant de la série de prix. |
| `provider` | TEXT | Fournisseur des données. |
| `symbol` | TEXT | Code de la série chez le fournisseur. |
| `instrument` | TEXT | Nom de l’instrument dont proviennent les prix. |
| `exchange` | TEXT | Place de marché. |
| `currency` | TEXT | Devise des prix. |
| `unit` | TEXT | Unité des prix stockés. |
| `price_field` | TEXT | Champ de prix utilisé chez le fournisseur. |
| `roll_rule` | TEXT | Règle de passage d’un contrat à l’autre. |
| `qualification` | TEXT | Qualification de la correspondance entre la série et la référence. |
| `notes` | TEXT | Notes sur la source. |
| `enabled` | INTEGER NOT NULL | Activation de la collecte : `0` ou `1`, valeur par défaut `0`. |
| `start_date` | TEXT | Première date de prix présente, au format `YYYY-MM-DD` ; NULL sans prix. |
| `end_date` | TEXT | Dernière date de prix présente, au format `YYYY-MM-DD` ; NULL sans prix. |
| `last_status` | TEXT | État de la dernière tentative de collecte : `ok`, `partial`, `empty` ou `error`. |
| `last_error` | TEXT | Message d’erreur de la dernière tentative, s’il existe. |

Les attributs sans `NOT NULL`, hors clé primaire, peuvent contenir NULL.

## Table `prices`

Prix quotidiens rattachés à une ligne de `metadata`. Une ligne par date et identifiant de métadonnées.

| Attribut | Type SQLite | Contenu |
| --- | --- | --- |
| `date` | TEXT NOT NULL | Date du prix au format `YYYY-MM-DD`. |
| `price` | REAL NOT NULL | Prix dans l’unité indiquée par `metadata.unit`. |
| `metadata_id` | INTEGER NOT NULL | Identifiant de la ligne associée dans `metadata` ; clé étrangère vers `metadata.id`. |

Clé primaire : (`metadata_id`, `date`).
