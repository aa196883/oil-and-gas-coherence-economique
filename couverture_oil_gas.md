# Couverture des prix Oil & Gas

Import réel vérifié le 16 octobre 2026, période demandée du 1er janvier 2020 au 15 octobre 2026. Base : `data/oil_gas.sqlite`.

**11,957 observations**, 7 séries, 8/20 routes couvertes par des données. Les 18 benchmarks restent au catalogue ; 11 n’ont aucun prix. Les alternatives et la qualification partielle de JKM sont incluses dans ce décompte.

| Série | Symbole | Unité native | Qualification | Première date | Dernière date | Observations |
| --- | --- | --- | --- | --- | --- | --- |
| yahoo-brent | BZ=F | USD/BBL | alternative | 2020-01-02 | 2026-10-15 | 1709 |
| yahoo-henry-hub | NG=F | USD/MMBtu | same_underlying | 2020-01-02 | 2026-10-15 | 1709 |
| yahoo-jkm | JKM=F | USD/MMBtu | partially_qualified | 2020-01-02 | 2026-10-15 | 1705 |
| yahoo-rbob | RB=F | USD/Gallon | same_underlying | 2020-01-02 | 2026-10-15 | 1709 |
| yahoo-ttf | TTF=F | EUR/MWh | alternative | 2020-01-02 | 2026-10-15 | 1708 |
| yahoo-ulsd | HO=F | USD/Gallon | same_underlying | 2020-01-02 | 2026-10-15 | 1709 |
| yahoo-wti | CL=F | USD/BBL | same_underlying | 2020-01-02 | 2026-10-15 | 1708 |

## Références sans données

| Identifiant | Référence |
| --- | --- |
| gasoil-ice | ICE Gasoil |
| gasoil-singapore | Singapore Gasoil 10ppm (Platts) |
| hsfo-rotterdam | Rotterdam Fuel Oil 3.5% Barges Swap |
| hsfo-singapore | Singapore Fuel Oil 380 CST Swap |
| hsfo-us | US Gulf Coast Fuel Oil 3.0% Swap |
| jet-singapore | Singapore Jet Kerosene Swap |
| oman | DME Oman |
| propane | Propane Mt Belvieu |
| vlsfo-rotterdam | Marine Fuel 0.5% Barges FOB Rdam Swap |
| vlsfo-singapore | Singapore Marine Fuel 0.5% Swap |
| vlsfo-us | US Gulf Coast Marine Fuel 0.5% Swap |

## Vérifications effectuées

- Import initial : 49 tranches annuelles archivées ; aucune tranche en erreur ou vide.
- Réimport intégral WTI et mise à jour des sept séries : nombre total de prix inchangé, aucun doublon.
- Intégrité SQLite et clés étrangères vérifiées.
- 18 tests passent, dont les 6 tests EIA existants.
- Clôture WTI négative du 20 avril 2020 conservée.

Les tranches initiales portent des avertissements de bornes ou de valeurs manquantes ; JKM porte aussi un avertissement de métadonnées incomplètes. Une borne tombant un jour sans cotation est signalée sans supposer de calendrier boursier. Aucune interpolation ne complète les séries.

Les règles de roll des génériques Yahoo restent non vérifiées, et `close` n’est pas certifié comme settlement. Les contrats historiques effectifs ne sont pas disponibles dans ces réponses. Les alternatives Brent/TTF ne sont pas les références ICE de la note. Voir le [catalogue des sources](sources_donnees_oil_gas.md).

Ce rapport est un instantané. Utiliser `.venv/bin/python -m oilgas coverage` pour consulter la base actualisée.
