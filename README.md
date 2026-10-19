# Collecte Oil & Gas et base SQLite

La V1 collecte des clôtures quotidiennes de sept génériques Yahoo, en unités natives, et conserve les 20 routes famille/zone de la note. Les alternatives, les références sans données et les limites du roll sont détaillées dans le [catalogue des sources](sources_donnees_oil_gas.md) et le [rapport de couverture](couverture_oil_gas.md).

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

Les imports sont atomiques par série et tranche annuelle. Une réimportation remplace une observation révisée sans doublon ; la nouvelle observation pointe vers sa collecte, et les anciennes réponses brutes restent archivées. Le code 1 indique un échec, une réponse vide ou une absence de prix consultables ; les erreurs de syntaxe CLI donnent le code 2. Le code 0 n’atteste pas une couverture complète : `partial` signale notamment des bornes non cotées, des observations nulles ou des métadonnées incomplètes. Aucune cause de jour manquant n’est inférée.

Les requêtes HTTP 429/500/502/503/504 et les erreurs réseau sont retentées jusqu’à quatre fois. Un échec d’une tranche est enregistré et les autres tranches peuvent être importées. Relancer `fetch` sur la période concernée permet de reprendre les échecs anciens ; `update` seul ne répare pas les trous historiques antérieurs à sa fenêtre.

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

Le CSV UTF-8 contient `date,price` et éventuellement `contract`, avec dates ISO et point décimal. Dates dupliquées, dates invalides, prix non numériques/non finis ou fichier vide entraînent un rejet complet. Les prix négatifs et nuls sont conservés. Une série externe n’est jamais téléchargée automatiquement par `update`, et un CSV ne peut pas écraser une série Yahoo.

## Modèle SQLite et limites

`routes` porte famille/zone/POL-POD ; `benchmarks` la référence recherchée et son unité attendue ; `series` l’instrument effectivement collecté et son unité native ; `prices` les observations ; `ingestions` leur provenance et les avertissements. La clé `(series_id,date)` empêche les doublons. Les séries partagent un benchmark sans être fusionnées.

Aucune conversion, interpolation, estimation de fret, reconstruction du contrat Bloomberg ou analyse de cohérence de facture n’est réalisée. Les génériques Yahoo ont une règle de roll non vérifiée ; les alternatives et la qualification partielle de JKM restent visibles dans les résultats.

Tests hors réseau : `.venv/bin/python -m unittest -v`.
