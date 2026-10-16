# Sources de prix Oil & Gas — V1

État de la recherche et essais : 16 octobre 2026. Périmètre : les 20 routes du tableau 2 des [travaux préliminaires](travaux_preliminaires_oil_gas.md), soit 18 références distinctes. Le [catalogue Bloomberg](catalogue_bloomberg_oil_gas.md) reste un document de recherche ; ses tickers ne sont pas des identifiants Yahoo.

## Source mise en œuvre

L’endpoint public Yahoo Chart est accessible sans compte ni clé lors des essais :

```text
GET https://query1.finance.yahoo.com/v8/finance/chart/{symbole_encodé}
    ?period1={timestamp_UTC}&period2={timestamp_UTC_exclusif}&interval=1d
```

Les prix sont extraits de `chart.result[0].indicators.quote[0].close`. `adjclose` n’est pas utilisé. Les réponses brutes sont conservées pour rendre chaque import examinable. Cet endpoint n’est pas une API contractuelle garantie : une erreur d’accès est enregistrée sans contournement ni substitution silencieuse.

| Référence de la note | Série collectée | Instrument réel / qualification | Unité native | Accès / profondeur testée |
| --- | --- | --- | --- | --- |
| WTI / CL1 | `CL=F` | NYMEX WTI ; même sous-jacent, générique non certifié | USD/BBL | Gratuit sans clé ; depuis janvier 2020 |
| ICE Brent / CO1 | `BZ=F` | **Alternative** NYMEX Brent Last Day Financial, pas ICE Brent | USD/BBL | Gratuit sans clé ; depuis janvier 2020 |
| Heating Oil / HO1 | `HO=F` | NYMEX ULSD / Heating Oil ; même sous-jacent, générique non certifié | USD/Gallon | Gratuit sans clé ; depuis janvier 2020 |
| RBOB / XB1 | `RB=F` | NYMEX RBOB ; même sous-jacent, générique non certifié | USD/Gallon | Gratuit sans clé ; depuis janvier 2020 |
| Henry Hub / NG1 | `NG=F` | NYMEX Henry Hub ; même sous-jacent, générique non certifié | USD/MMBtu | Gratuit sans clé ; depuis janvier 2020 |
| ICE Endex TTF / TZT1 | `TTF=F` | **Alternative** NYMEX Dutch TTF Natural Gas Calendar | EUR/MWh | Gratuit sans clé ; depuis janvier 2020 |
| JKM / JKL1 | `JKM=F` | NYMEX JKM candidat ; **qualification partielle**, nom et devise Yahoo incomplets | USD/MMBtu, selon spécification CME JKM | Gratuit sans clé ; depuis janvier 2020 |

Les clôtures sont distinguées des settlements : aucun settlement n’est déduit d’un `close`. La règle de roll Yahoo et le contrat historique effectif ne sont pas fournis de manière vérifiable par ces réponses. Toutes les séries portent donc `provider_generic_unverified`. L’absence d’ajustement réalisé par notre collecteur n’est pas une certification du traitement historique du fournisseur. Le champ `contract` demeure vide pour Yahoo : le nom du contrat courant n’est jamais réutilisé comme contrat de chaque date passée.

Les unités natives sont conservées : HO et RB sont stockés en dollars/gallon, tandis que la matrice indique des cents/gallon. Il n’y a aucune conversion. La devise seule dans la réponse ne suffit pas à établir l’unité ; celle-ci est déclarée dans le référentiel d’instruments.

Sources primaires de qualification : [liste Yahoo des futures](https://finance.yahoo.com/markets/commodities/), [TTF Yahoo](https://finance.yahoo.com/quote/TTF%3DF/), [WTI CME](https://www.cmegroup.com/markets/energy/crude-oil/light-sweet-crude.contractSpecs.html), [ULSD CME](https://www.cmegroup.com/markets/energy/refined-products/heating-oil.contractSpecs.html), [RBOB CME](https://www.cmegroup.com/markets/energy/refined-products/rbob-gasoline.contractSpecs.html), [JKM CME](https://www.cmegroup.com/education/featured-reports/lng-stepping-up-to-the-asia-supply-boom). L’identité exacte de JKL1 par rapport au contrat CME n’a pas été établie.

## Couverture manquante et accès complémentaires

Aucune série de remplacement n’est inventée pour les 11 références suivantes. Elles restent visibles dans `catalog` et `coverage`, avec zéro prix tant qu’une source externe n’a pas été importée.

| Référence manquante | Piste d’accès | État de vérification |
| --- | --- | --- |
| DME/GME Oman | Bulletins GME à T+1 ; historique via DataMine | Accès annoncé par GME ; pas d’import historique implémenté |
| Singapore Gasoil 10ppm | Rapports ICE/CME ou distributeur spécialisé | Offre à qualifier instrument par instrument ; gratuité historique non établie |
| ICE Gasoil | ICE EOD ; Barchart | Offre documentée ; `LGO=F` Yahoo a renvoyé 404 |
| HSFO Singapour 380 CST | ICE EOD / distributeur | Historique gratuit non confirmé |
| HSFO US Gulf 3 % | ICE EOD / distributeur | Historique gratuit non confirmé |
| HSFO Rotterdam 3,5 % | ICE EOD / distributeur | Historique gratuit non confirmé |
| VLSFO Singapour 0,5 % | ICE EOD / distributeur | Historique gratuit non confirmé |
| VLSFO US Gulf 0,5 % | ICE EOD / distributeur | Historique gratuit non confirmé |
| VLSFO Rotterdam 0,5 % | ICE EOD / distributeur | Historique gratuit non confirmé |
| Jet Singapour | ICE/CME / distributeur | Historique gratuit non confirmé |
| Propane Mont Belvieu | Contrats CME / distributeur | `B0=F` existe, mais aucune clôture historique non nulle reçue sur 2020–2026 lors du test ; pas d’équivalence démontrée avec PNL1 |

**GME** publie ses bulletins à T+1 et oriente l’historique vers DataMine. Un bulletin récent ne démontre pas une disponibilité gratuite depuis 2020. [GME Data](https://www.gulfmerc.com/gme-product-services/gme-data)

**ICE** propose des packages EOD CSV sur abonnement ; les rapports distinguent notamment clôture et settlement. Les contrats livrés par échéance nécessiteraient une règle explicite de sélection du front month. Les prix et droits de stockage applicables au périmètre sont à confirmer auprès du fournisseur avant acquisition. [Report Center](https://www.ice.com/report-center), [format MFT](https://www.ice.com/publicdocs/futures/ICE_Futures_Data_MFT_User_Guide.pdf)

**Barchart OnDemand** documente `getHistory`, `type=dailyNearest`, `nearby=1`, `backAdjust=false` et `daysToExpiration`. L’offre exige un accès commercial à qualifier ; aucun prix ni droit de couverture intégrale n’est supposé. [API](https://www.barchart.com/ondemand/api/getHistory)

**Databento** expose des génériques sans rétroajustement, avec règles de roll calendaire, volume ou intérêt ouvert. Cela constitue une piste payante pour les marchés pris en charge, pas une preuve de couverture des 18 références. [Documentation](https://www.databento.tech/docs/examples/futures/futures-introduction)

**EIA** est accessible avec clé gratuite, mais ses Futures NYMEX s’arrêtent au 5 avril 2024. Le script EIA existant reste consacré au spot ; ses prix ne sont pas fusionnés avec les futures. [Historique EIA](https://www.eia.gov/dnav/pet/PET_PRI_FUT_S1_M.htm)

## Restitution de la couverture

Le [rapport de couverture](couverture_oil_gas.md) décrit l’import effectué. Pour une situation à jour :

```bash
.venv/bin/python -m oilgas coverage
.venv/bin/python -m oilgas catalog --format csv
```

Les bornes et nombres d’observations ne garantissent pas une série complète. Les dates absentes restent absentes, sans interpolation ; le programme n’attribue pas de cause aux jours manquants. Les archives sont des instantanés récupérés aujourd’hui, et non une reconstruction de ce qui était connu à la date historique.
