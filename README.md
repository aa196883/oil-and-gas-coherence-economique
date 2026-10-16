# Prix spot Oil & Gas autour d’une date

Le script récupère les prix quotidiens EIA du WTI, du Brent et du gaz Henry Hub et sauvegarde un JSON et un graphique PNG. La fenêtre inclut la date d’ancrage et les `n` jours calendaires de chaque côté : elle contient donc `2n + 1` dates par série.

## Installation

Python 3.10 ou plus récent :

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

Une clé gratuite est disponible sur https://www.eia.gov/opendata/register.php. Placez-la dans le fichier `.env` à côté du script :

```dotenv
EIA_API_KEY=votre_cle
```

Une variable d’environnement déjà définie est prioritaire. `.env` est exclu de Git ; la clé n’est pas exportée dans le JSON ni affichée dans les messages d’erreur réseau.

## Utilisation

```bash
.venv/bin/python eia_prices.py --anchor 2024-01-15 --days 30
.venv/bin/python eia_prices.py --anchor 2020-04-20 --days 10 --series wti brent --output-dir outputs
```

`--anchor` et `--days` sont obligatoires. `--days` accepte zéro. `--series` accepte `wti`, `brent` et `henry-hub` (tous par défaut). Les sorties vont dans `outputs` par défaut. Un suffixe horodaté évite d’écraser des résultats existants.

Chaque panneau du PNG indique sa série et son unité : USD/baril pour le pétrole, USD/MMBtu pour le gaz. La ligne verticale indique l’ancrage. Les courbes sont interrompues aux jours sans prix ; aucun remplissage ni interpolation n’est effectué. Les marqueurs permettent de voir les observations isolées.

Le JSON contient la fenêtre demandée, l’horodatage UTC de récupération et une liste `series`. Chaque série expose son identifiant EIA, sa source, ses unités, ses avertissements, sa couverture réelle et ses `observations` (`date`, `value`). Les prix sont des nombres, les dates sans valeur sont `null`. Les prix négatifs sont conservés. Un jour vide peut correspondre à un week-end, un jour férié, un délai de publication ou un historique indisponible ; le script ne prétend pas identifier sa cause.

Les données partiellement disponibles sont exportées avec avertissement si les bornes ne sont pas couvertes. Une série vide reste présente dans les sorties. Si toutes sont vides, le JSON et le PNG sont produits mais le code de retour vaut 1. Les erreurs réseau/API produisent aussi un code 1, sans export d’un jeu incomplet dû à une requête échouée. Le code 0 indique qu’au moins une cotation a été exportée ; le code 2 signale des arguments invalides.

## Sources et limites

- WTI `RWTC` et Brent `RBRTE` : https://api.eia.gov/v2/petroleum/pri/spt/data/
- Henry Hub spot `RNGWHHD` : https://api.eia.gov/v2/natural-gas/pri/fut/data/ (cette route contient aussi du spot).
- Documentation : https://www.eia.gov/opendata/documentation.php

Les requêtes filtrent la série, les dates et la fréquence quotidienne, et paginent par 5 000 lignes. Les erreurs réseau et HTTP 429/500/502/503/504 donnent lieu à quatre tentatives au maximum. Les données EIA peuvent être révisées : le JSON est un instantané au moment de la récupération, pas une reconstitution de l’information connue à l’ancrage.

Cette version ne traite que le spot. Les futures NYMEX EIA ne sont plus disponibles après le 5 avril 2024 : https://www.eia.gov/dnav/pet/PET_PRI_FUT_S1_W.htm. Aucun roll ni contrat générique n’est reconstruit. Les jours postérieurs à l’ancrage sont des observations historiques, jamais des prévisions.

La récupération EIA est séparée de la normalisation et du tracé pour permettre un futur fournisseur, sans intégration Bloomberg pour l’instant.

## Tests

```bash
.venv/bin/python -m unittest -v
```

Les tests simulent l’API et ne nécessitent pas de clé. Pour vérifier la connexion réelle, exécuter la commande d’exemple après configuration du `.env`.
