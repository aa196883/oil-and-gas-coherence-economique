# Couverture des données

Base `data/oil_gas.sqlite`, consultée le 20 octobre 2026.

| Famille | Corridor | Présence de données | Première date | Dernière date | Unité | instrument |
| --- | --- | --- | --- | --- | --- | --- |
| Crude Oil (Brut) | Amériques | Oui | 2020-01-02 | 2026-10-15 | Dollars US par baril | NYMEX WTI |
| Crude Oil (Brut) | Europe / Afrique | Oui | 2020-01-02 | 2026-10-15 | Dollars US par baril | NYMEX Brent Last Day Financial |
| Crude Oil (Brut) | Orient | Non | — | — | — | — |
| Fuel Oil HSFO | Amériques | Non | — | — | — | — |
| Fuel Oil HSFO | Europe / Afrique | Non | — | — | — | — |
| Fuel Oil HSFO | Orient | Non | — | — | — | — |
| Fuel Oil VLSFO | Amériques | Non | — | — | — | — |
| Fuel Oil VLSFO | Europe / Afrique | Non | — | — | — | — |
| Fuel Oil VLSFO | Orient | Non | — | — | — | — |
| GNL (LNG) | Asie | Oui | 2020-01-02 | 2026-10-15 | Dollars US par million de BTU | NYMEX LNG Japan/Korea Marker (Platts) |
| GNL (LNG) | Europe | Oui | 2020-01-02 | 2026-10-15 | Euros par MWh | NYMEX Dutch TTF Natural Gas Calendar |
| GNL (LNG) | USA | Oui | 2020-01-02 | 2026-10-15 | Dollars US par million de BTU | NYMEX Henry Hub |
| GPL (Propane / Butane) | Monde | Non | — | — | — | — |
| Gasoil / Diesel | Amériques | Oui | 2020-01-02 | 2026-10-15 | Dollars US par gallon | NYMEX ULSD / Heating Oil |
| Gasoil / Diesel | Europe / Afrique | Non | — | — | — | — |
| Gasoil / Diesel | Orient | Non | — | — | — | — |
| Gasoline (Essence) | Amériques | Oui | 2020-01-02 | 2026-10-15 | Dollars US par gallon | NYMEX RBOB |
| Gasoline (Essence) | Reste du Monde | Oui | 2020-01-02 | 2026-10-15 | Dollars US par baril | NYMEX Brent Last Day Financial |
| Jet Fuel | Europe / Afrique | Non | — | — | — | — |
| Jet Fuel | Orient | Non | — | — | — | — |

## Source mise en œuvre

L’endpoint public Yahoo Chart est accessible sans compte ni clé lors des essais :

```text
GET https://query1.finance.yahoo.com/v8/finance/chart/{symbole_encodé}
    ?period1={timestamp_UTC}&period2={timestamp_UTC_exclusif}&interval=1d
```

| Référence de la note | Instrument réel / qualification |
| --- | --- |
| WTI / CL1 | NYMEX WTI ; même sous-jacent, générique non certifié |
| ICE Brent / CO1 | **Alternative** NYMEX Brent Last Day Financial, pas ICE Brent |
| Heating Oil / HO1 | NYMEX ULSD / Heating Oil ; même sous-jacent, générique non certifié |
| RBOB / XB1 | NYMEX RBOB ; même sous-jacent, générique non certifié |
| Henry Hub / NG1 | NYMEX Henry Hub ; même sous-jacent, générique non certifié |
| ICE Endex TTF / TZT1 | **Alternative** NYMEX Dutch TTF Natural Gas Calendar |
| JKM / JKL1 | NYMEX JKM candidat ; **qualification partielle**, nom et devise Yahoo incomplets |