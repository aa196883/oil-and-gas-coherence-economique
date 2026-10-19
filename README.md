# Collecte Oil & Gas et base SQLite

La V1 collecte des clôtures quotidiennes de sept génériques Yahoo, en unités natives, et conserve les 20 routes famille/zone de la note. Les alternatives, les références sans données et les limites du roll sont détaillées dans le [catalogue des sources](docs/sources_donnees_oil_gas.md) et le [rapport de couverture](docs/couverture_oil_gas.md).

Python **3.10+**, avec les dépendances de `requirements.txt`, suffit. Aucune clé ni inscription n’est nécessaire pour Yahoo.

## Installation

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

## Collecter et consulter les futures

```bash
.venv/bin/python -m oilgas init
.venv/bin/python -m oilgas fetch --start 2020-01-01 --end 2026-10-15
.venv/bin/python -m oilgas update
.venv/bin/python -m oilgas coverage
.venv/bin/python -m oilgas catalog --format csv
.venv/bin/python -m oilgas prices --family 'Crude Oil (Brut)' --zone 'Europe / Afrique' --start 2024-01-01 --end 2024-01-31
```

`fetch` accepte `--series yahoo-wti yahoo-brent` et, sans dates, importe depuis 2020 jusqu’à hier. `update` repart de dix jours calendaires incluant la dernière observation ; une série vide repart de 2020. Les périodes sont inclusives et la collecte s’arrête au plus tard à la veille pour exclure les clôtures intrajournalières. `prices` accepte `--format csv` et `--series` pour sélectionner une série lorsque plusieurs sources sont associées au benchmark. Les noms de famille et de zone sont les libellés exacts de `catalog`.

Pour un autre fichier SQLite : placer `--db chemin.sqlite` **avant** la commande. La base par défaut est `data/oil_gas.sqlite`, et les réponses brutes compressées sont archivées dans `data/raw/`. Ces fichiers locaux sont exclus de Git. Les commandes initialisent automatiquement le schéma et le référentiel si nécessaire ; elles ne réécrivent pas les métadonnées déjà présentes.

Les imports sont atomiques par série et tranche annuelle, sur tous les couples famille/zone associés. Une réimportation remplace une observation révisée sans doublon et recalcule les bornes observées. Les réponses brutes restent archivées ; les rapports de collecte donnent leur chemin et leur empreinte SHA-256. Le code 1 indique un échec, une réponse vide ou une absence de prix consultables ; les erreurs de syntaxe CLI donnent le code 2. Le code 0 n’atteste pas une couverture complète : `partial` signale notamment des bornes non cotées, des observations nulles ou des métadonnées incomplètes. Aucune cause de jour manquant n’est inférée.

Les requêtes HTTP 429/500/502/503/504 et les erreurs réseau sont retentées jusqu’à quatre fois. Un échec d’une tranche est signalé dans le rapport et les autres tranches peuvent être importées. `coverage` expose le statut et l’erreur de la dernière tentative pour chaque ligne de métadonnées. Relancer `fetch` sur la période concernée permet de reprendre les échecs anciens ; `update` seul ne répare pas les trous historiques antérieurs à sa fenêtre.

## Calculer les deltas

```bash
python -m oilgas deltas --price 100 --family 'Crude Oil (Brut)' --zone 'Europe / Afrique' --start 2024-01-01 --end 2024-01-31
```

`--price` est le prix à comparer, exprimé dans `expected_unit`. Pour chaque date disponible dans la période inclusive, le delta est `(price − prix_de_référence) / prix_de_référence` : `0.25` signifie +25 %. Cette V1 utilise directement les prix stockés, sans fret ni conversion, et ne complète pas les jours manquants.

La sortie JSON contient uniquement un bloc `ref` (`logic`, `reference`, `expected_unit`, `instrument`) et une liste `deltas` de paires `[date, delta]`, une paire par ligne. Par exemple, pour des références de 80 et 125 et un prix fourni de 100 :

```json
{
  "ref": {
    "logic": "POL",
    "reference": "Référence du catalogue",
    "expected_unit": "USD/BBL",
    "instrument": "Instrument de la série sélectionnée"
  },
  "deltas": [
    ["2024-01-02", 0.25],
    ["2024-01-03", -0.2]
  ]
}
```

Si plusieurs séries ont des observations, choisir avec `--series`. Une référence nulle, une unité native différente de l’unité attendue, un nombre non fini ou l’absence de données produit une erreur explicite sans résultat partiel.

## Importer un téléchargement externe

Déclarer d’abord une série distincte avec un JSON contenant **tous** les champs suivants. Les valeurs sont à renseigner d’après la source réelle, notamment la nature du prix, l’unité et le roll ; l’exemple est un gabarit, pas un instrument validé :

```json
{
  "id": "externe-gasoil",
  "benchmark_id": "gasoil-ice",
  "provider": "nom-du-fournisseur",
  "symbol": "identifiant-source",
  "instrument": "libelle-instrument-reel",
  "exchange": "place-source",
  "currency": "USD",
  "unit": "USD/MT",
  "price_field": "settlement",
  "roll_rule": "regle-documentee-ou-inconnue",
  "qualification": "qualification-documentee",
  "notes": "Origine du téléchargement, écarts au benchmark et références documentaires"
}
```

```bash
.venv/bin/python -m oilgas register-series --file serie.json
.venv/bin/python -m oilgas import-csv --series externe-gasoil --file prix.csv
```

Le CSV UTF-8 contient `date,price` et éventuellement `contract`, avec dates ISO et point décimal. La colonne facultative `contract` reste acceptée et conservée dans le fichier brut archivé, mais n’est pas stockée dans la table des prix. Dates dupliquées, dates invalides, prix non numériques/non finis ou fichier vide entraînent un rejet complet. Les prix négatifs et nuls sont conservés. Une série externe n’est jamais téléchargée automatiquement par `update`, et un CSV ne peut pas écraser une série Yahoo.

## Modèle SQLite et limites

La base contient **exactement deux tables** :

- `metadata` : `id`, `family`, `zone`, `logic` (POL/POD), `benchmark_id`, `reference`, `expected_unit`, `start_date`, `end_date`, ainsi que les paramètres des sources nécessaires aux commandes (série, fournisseur, symbole, instrument, unité native, etc.) et le dernier statut de collecte.
- `prices` : uniquement `date`, `price`, `metadata_id`. La clé `(metadata_id, date)` empêche les doublons ; `metadata_id` référence `metadata.id`.

Une ligne de métadonnées représente un couple famille/zone et une source. Sans source, la référence reste visible dans le catalogue, avec une série et des bornes nulles. Les bornes sont les dates minimale et maximale des observations présentes, pas les dates demandées à la collecte. Lorsqu’une série dessert plusieurs couples, ses prix sont enregistrés pour chacun, au cours d’une même transaction ; elle n’est téléchargée qu’une fois.

`register-series` conserve son format JSON et associe la nouvelle source aux couples du benchmark choisi. `--series` permet toujours de sélectionner une source. Les prix ne sont jamais fusionnés entre sources.

La provenance par observation et l’historique des ingestions ne sont plus stockés en base. `prices` conserve les métadonnées de source, mais ne renvoie plus `contract`, `retrieved_at`, `raw_path` et `sha256` pour chaque prix. Les fichiers bruts et les rapports de collecte servent à inspecter les téléchargements. Le code crée et entretient ce schéma ; il ne contient pas de migration.

Architecture et invariants : [docs/architecture.md](docs/architecture.md). Consignes de développement et commandes : [AGENTS.md](AGENTS.md).

Aucune conversion, interpolation, estimation de fret, reconstruction du contrat Bloomberg ou analyse de cohérence de facture n’est réalisée. Les génériques Yahoo ont une règle de roll non vérifiée ; les alternatives et la qualification partielle de JKM restent visibles dans les résultats.

Tests hors réseau dans `tests/` : `.venv/bin/python -m unittest discover -s tests -v`.
