# Convention USD/MT pour les deltas

`deltas --price` attend toujours des dollars par tonne métrique. Les prix natifs restent stockés sans conversion ; seule la référence utilisée pour le calcul est normalisée.

```text
référence USD/MT = prix natif × coefficient du catalogue × change
```

Le change vaut 1 pour les USD. Pour les EUR, `--eur-usd` est obligatoire : 1.10 signifie 1 EUR = 1,10 USD. Ce taux fourni par l’utilisateur s’applique à toutes les dates. Aucun taux historique n’est téléchargé.

## Table explicite

La section `conversions` de `oilgas/catalog.json` contient une entrée pour chaque couple exact benchmark/unité pris en charge. `currency` doit correspondre à la devise de la série ; `factor` convertit le prix en devise principale par tonne, avant le change. Les cents sont donc déjà pris en compte dans le coefficient.

| Benchmarks | Unité native exacte | Coefficient | Convention |
| --- | --- | ---: | --- |
| `oman`, `wti`, `brent` | USD/BBL | 7.33 | 7,33 barils/tonne de brut |
| `ulsd` | USD/Gallon | 312.9 | 7,45 × 42 gallons/tonne |
| `ulsd` | US Cents/Gallon | 3.129 | 7,45 × 42 / 100 |
| `rbob` | USD/Gallon | 357 | 8,50 × 42 gallons/tonne |
| `rbob` | US Cents/Gallon | 3.57 | 8,50 × 42 / 100 |
| `propane` | US Cents/Gallon | 5.208 | 12,40 × 42 / 100 |
| `gasoil-singapore`, `gasoil-ice` | USD/MT | 1 | Prix déjà par tonne |
| `hsfo-singapore`, `hsfo-us`, `hsfo-rotterdam` | USD/MT | 1 | Prix déjà par tonne |
| `vlsfo-singapore`, `vlsfo-us`, `vlsfo-rotterdam` | USD/MT | 1 | Prix déjà par tonne |
| `jkm`, `henry-hub` | USD/MMBtu | 52 | 52 MMBtu/tonne |
| `ttf` | EUR/MWh | 15.2396972 | 52 × 0,2930711 MWh/tonne, avant change |

Les moyennes volume/masse et énergie/masse viennent du tableau 3 des [travaux préliminaires](travaux_preliminaires_oil_gas.md). Ce sont des approximations : aucune densité réelle ou composition énergétique n’est déduite. La convention GNL est systématiquement 52 MMBtu/tonne, sans examen de certificat qualité.

Conversions physiques utilisées : [42 gallons US par baril — EIA](https://www.eia.gov/energyexplained/units-and-calculators/) et [0,2930711 Wh/Btu, soit 0,2930711 MWh/MMBtu — Nebraska DWEE](https://dwee.nebraska.gov/state-energy-information/energy-statistics/miscellaneous/conversion-factors/b-conversionequivalency-factors).

## Cas particuliers et erreurs

- La correspondance porte sur le benchmark et l’unité exacte, pas sur la famille de routage. Le Brent utilisé pour l’essence garde 7,33 ; le gasoil utilisé pour le jet reste en USD/MT avec coefficient 1.
- Le jet de Singapour (`jet-singapore`, USD/BBL) n’a pas de coefficient : son calcul de delta est refusé. Aucun coefficient de gasoil ou de brut ne lui est attribué par défaut.
- Une série externe utilise les mêmes entrées explicites. Une nouvelle unité exige une entrée documentée dans le catalogue, même si elle semble convertible ; il n’existe pas de repli automatique.
- Coefficients et taux doivent être finis et strictement positifs. Une devise incompatible, une référence nulle ou un résultat non fini provoque une erreur sans JSON partiel. Les prix négatifs restent acceptés.
- La sortie reste limitée à `ref` et `deltas`. `ref.expected_unit` devient `USD/MT` ; l’unité du benchmark dans SQLite et les valeurs de `prices` restent natives.

Modifier cette table modifie les calculs futurs, sans toucher aux observations stockées. Il n’y a ni versionnement de coefficients ni migration de données.
