# Travaux préliminaires — POC de cohérence économique Oil & Gas / TBML

> **Statut : défrichage préliminaire.** Ce document synthétise la note de recherche du 12 mai 2026 pour conserver le contexte de réflexion du projet, notamment à l’usage de l’assistant. Les choix présentés sont ceux explorés par la note ; ils ne constituent ni des directives de développement, ni des décisions validées pour le POC, ni une description des fonctionnalités déjà implémentées. Les seuils et pondérations restent des hypothèses indicatives.

Source : [note_recherche_oil_gas_tbml_final.docx](note_recherche_oil_gas_tbml_final.docx). Domaine : Trade Finance Compliance / risque de marché. La synthèse conserve les 13 tableaux de la source, leurs valeurs et leurs libellés, ainsi que les principales formules. Elle ne procède à aucune validation externe, correction de fond ou critique des propositions. Les numéros de tableaux ci-dessous suivent leur ordre d’apparition dans le Word, y compris pour les tableaux initialement non numérotés.

## 1. Finalité et éléments saillants

La note explore un contrôle de premier niveau de la **plausibilité économique d’un prix facturé** : repérer des écarts susceptibles de correspondre à une erreur opérationnelle, une anomalie de valorisation, une sur/sous-facturation ou un risque de blanchiment par le commerce (*Trade-Based Money Laundering*, TBML). Le contexte documentaire bancaire donne rarement accès à la formule contractuelle exacte ou au différentiel commercial négocié.

Les principaux choix méthodologiques explorés sont les suivants :

- Ancrer l’analyse sur le **Shipped on Board Date** du connaissement (*Bill of Lading*, BL), avec une fenêtre de cotations autour de cette date.
- Étudier une **série de prix théoriques et la distribution des Deltas journaliers**, plutôt qu’une seule cotation.
- Normaliser le produit par la chaîne **description documentaire → HS Code → famille économique**, avec affinage et intervention utilisateur possibles.
- Router le benchmark selon la famille et la géographie : **POL** (port de chargement) pour brut, raffinés et GPL ; **POD** (port de déchargement) pour GNL.
- Utiliser des références financières standardisées, généralement **Generic Front Month**, et des proxies pour certains segments.
- Homogénéiser monnaies et unités, puis intégrer une estimation du fret selon l’Incoterm et le détail de la facture.
- Interpréter les écarts avec des bandes indicatives tenant compte du produit, du benchmark et de l’incertitude logistique.
- Envisager ultérieurement des raffinements du fret, la contextualisation par volatilité, l’analyse comportementale et les différentiels physiques observables.

## 2. Ancrage temporel et construction du prix

*Source : sections 2, 4.3 et 5.1.*

Le Shipped on Board Date est l’ancrage documentaire proposé pour obtenir une référence homogène. La fenêtre est paramétrable selon le produit, les pratiques de pricing et les besoins de contrôle ; elle peut inclure des jours avant et après le chargement ou correspondre à une période contractuelle connue. La note ne fixe pas de durée unique.

Le cadre conceptuel distingue benchmark et différentiel implicite :

```text
Prix_théorique(t) = Prix_marché(t) + Différentiel_implicite(t)

Avec composante logistique explicite :
Prix_théorique(t) = Prix_marché(t) + Fret_estimé(t) + Différentiel_résiduel(t)
```

Le différentiel implicite peut recouvrir transport, qualité, contraintes régionales, crédit et marges commerciales. Dans l’approche de calcul initiale décrite ensuite, la référence est le benchmark en FOB et le benchmark augmenté du fret estimé en CFR/CIF lorsque le transport n’est pas séparé sur la facture ; les autres composantes se retrouvent dans l’écart observé.

```text
Delta(t) = [Prix_facturé − Prix_théorique(t)] / Prix_théorique(t)
Delta_en_pourcentage(t) = 100 × Delta(t)

FOB :
Prix_théorique(t) = Prix_marché(t)

CFR / CIF, facture sans ventilation du transport :
Prix_théorique(t) = Prix_marché(t) + Fret_estimé(t)
```

Les composantes sont exprimées sur une base économique homogène avant comparaison. Si la facture sépare marchandise et transport, la note propose un **Delta Marchandise**, un **Delta Fret** et un **Delta Global** sur le total de la transaction.

L’objectif est d’apprécier la plausibilité de l’écart, sans rechercher un Delta nul ni reproduire exactement la formule commerciale négociée.

## 3. Classification des produits et sélection des benchmarks

### 3.1. Normalisation documentaire

*Source : section 3.1.*

Un utilitaire suggère un HS Code à partir de la description libre ; une table le rattache à une famille économique. Les appellations « Low Sulfur Gasoil 10ppm », « ULSD 10 PPM », « Diesel EN590 » et « Automotive Diesel Fuel » illustrent la diversité des descriptions d’une même famille.

**Tableau 1 — Correspondance HS Codes / familles produit**

| HS Code | Description Simplifiée | Famille Produit |
| --- | --- | --- |
| 2709.00 | Pétrole brut et huiles brutes de pétrole ou de minéraux bitumineux | Crude Oil (Brut) |
| 2710.12 | Essences légères et préparations essence | Gasoline (Essence) |
| 2710.19.43 | Gasoil faible teneur en soufre | Gasoil / Diesel |
| 2710.19.46 | Diesel routier | Gasoil / Diesel |
| 2710.19.62 | Fuel oils et distillats lourds | Gasoil / Diesel |
| 2710.19.68 | Fuel oils (HSFO, VLSFO et autres fuels marins) | Fuel Oil |
| 2710.19.21 | Jet Fuel / Kerosene type aviation | Jet Fuel |
| 2710.20 | Huiles de pétrole contenant du biodiesel | Gasoil / Diesel |
| 2711.11 | Gaz naturel liquéfié (LNG) | GNL (LNG) |
| 2711.12 | Propane liquéfié | GPL (Propane / Butane) |
| 2711.13 | Butane liquéfié | GPL (Propane / Butane) |
| 2711.14 | Éthylène, propylène, butylène et butadiène liquéfiés | GPL (Propane / Butane) |
| 2711.19 | Autres gaz de pétrole et hydrocarbures gazeux liquéfiés | GPL (Propane / Butane) |
| 2711.21 | Gaz naturel à l’état gazeux | GNL (LNG) |
| 2711.29 | Autres gaz de pétrole et hydrocarbures gazeux, à l’état gazeux | GPL (Propane / Butane) |

La note présente cette table comme un référentiel de normalisation économique couvrant le périmètre étudié. Les codes à six chiffres constituent un niveau généralement suffisant dans l’approche, avec affinage pour les catégories ambiguës de 2710.19.

Pour le Fuel Oil, l’analyse de mots-clés (`0.5%`, `VLSFO`, `3.5%`, `HSFO`, `380 CST`, `180 CST`) complète la classification douanière. La distinction explorée oppose le VLSFO à 0,5 % de soufre, associé au bunkering et aux distillats moyens, au HSFO à 3,5 %, associé notamment aux navires équipés de scrubbers et à certains usages industriels ; la note évoque leur écart de valorisation (*Hi-5 Spread*).

Les cas ambigus peuvent être soumis à validation utilisateur. Une correction de famille peut être historisée pour affiner progressivement le référentiel.

### 3.2. Géographie, instruments et maturités

*Source : sections 3.2 à 3.3.4.*

La logique proposée est celle du bassin exportateur pour le brut, les raffinés et le GPL (POL), et du bassin consommateur pour le GNL (POD).

Le choix des données cherche à concilier représentativité économique, disponibilité sur les plateformes financières usuelles, coûts de licences et simplicité d’exploitation. La note privilégie les Futures liquides et les Swaps compensés indexés sur les évaluations physiques des agences ; les établissements utilisateurs fourniraient les séries sous forme d’exports Bloomberg.

Le **Generic Front Month** est la convention proposée en l’absence d’échéance contractuelle connue : contrat proche, renouvellement automatique (*roll*), nombre limité de séries à maintenir. La note distingue les mouvements liés au roll des mouvements du sous-jacent : passage généralement vers un contrat plus cher en contango, moins cher en backwardation ; l’écart entre échéances correspond au *calendar spread* ou *roll spread*.

Deux proxies structurels sont explorés : **ICE Brent pour l’essence hors Amériques** et **ICE Gasoil pour le Jet Fuel Europe/Afrique**. Leur justification repose sur les mécanismes de formation des prix, avec analyses de corrélation et de cointégration lorsque des historiques représentatifs sont disponibles. L’incertitude supplémentaire est prise en compte dans les bandes de tolérance.

**Tableau 2 — Matrice de routage des benchmarks**

| Famille de Produit | Zone Pivot | Logique | Type de Benchmark | Référence de Marché | Ticker Bloomberg | Unité Principale |
| --- | --- | --- | --- | --- | --- | --- |
| Crude Oil (Brut) | Orient | POL | Future générique Front Month | DME Oman | OQA1 Comdty | USD/BBL |
| Crude Oil (Brut) | Amériques | POL | Future générique Front Month | NYMEX WTI | CL1 Comdty | USD/BBL |
| Crude Oil (Brut) | Europe / Afrique | POL | Future générique Front Month | ICE Brent | CO1 Comdty | USD/BBL |
| Gasoil / Diesel | Orient | POL | Swap Future générique Front Month | Singapore Gasoil 10ppm (Platts) | SGB1 Comdty | USD/MT |
| Gasoil / Diesel | Amériques | POL | Future générique Front Month | NYMEX Heating Oil | HO1 Comdty | US Cents/Gallon |
| Gasoil / Diesel | Europe / Afrique | POL | Future générique Front Month | ICE Gasoil | QS1 Comdty | USD/MT |
| Gasoline (Essence) | Amériques | POL | Future générique Front Month | NYMEX RBOB | XB1 Comdty | US Cents/Gallon |
| Gasoline (Essence) | Reste du Monde | POL | Benchmark Proxy | ICE Brent | CO1 Comdty | USD/BBL |
| Fuel Oil HSFO | Orient | POL | Swap Future générique Front Month | Singapore Fuel Oil 380 CST Swap | SYS1 Comdty | USD/MT |
| Fuel Oil HSFO | Amériques | POL | Swap Future générique Front Month | US Gulf Coast Fuel Oil 3.0% Swap | MFB1 Comdty | USD/MT |
| Fuel Oil HSFO | Europe / Afrique | POL | Swap Future générique Front Month | Rotterdam Fuel Oil 3.5% Barges Swap | BAR1 Comdty | USD/MT |
| Fuel Oil VLSFO | Orient | POL | Swap Future générique Front Month | Singapore Marine Fuel 0.5% Swap | MFT1 Comdty | USD/MT |
| Fuel Oil VLSFO | Amériques | POL | Swap Future générique Front Month | US Gulf Coast Marine Fuel 0.5% Swap | AMR1 Comdty | USD/MT |
| Fuel Oil VLSFO | Europe / Afrique | POL | Swap Future générique Front Month | Marine Fuel 0.5% Barges FOB Rdam Swap | S5FN1 Comdty | USD/MT |
| Jet Fuel | Orient | POL | Swap Future générique Front Month | Singapore Jet Kerosene Swap | JKS1 Comdty | USD/BBL |
| Jet Fuel | Europe / Afrique | POL | Benchmark Proxy | ICE Gasoil | QS1 Comdty | USD/MT |
| GPL (Propane / Butane) | Monde | POL | Swap Future générique Front Month | Propane Mt Belvieu | PNL1 Comdty | US Cents/Gallon |
| GNL (LNG) | Asie | POD | Swap Future générique Front Month | JKM (Japan Korea Marker) | JKL1 Comdty | USD/MMBtu |
| GNL (LNG) | Europe | POD | Future générique Front Month | TTF Pays-Bas | TZT1 Comdty | EUR/MWh |
| GNL (LNG) | USA | POD | Future générique Front Month | Henry Hub | NG1 Comdty | USD/MMBtu |

Le benchmark proposé est une référence de premier niveau. Une modification utilisateur est envisagée lorsque les caractéristiques du produit ou de la transaction le justifient, avec traçabilité des hypothèses et recalcul des résultats.

### 3.3. Unités et normalisation

*Source : section 3.4.*

La séquence proposée identifie l’unité native, réalise la conversion monétaire éventuelle, applique les conversions volume/masse/énergie et exprime le benchmark dans l’unité de la facture. La note rattache les coefficients moyens aux références industrielles BP/IEA et à la densité des produits (API Gravity).

**Tableau 3 — Facteurs moyens de conversion**

| Produit | Conversion Moyenne |
| --- | --- |
| Pétrole Brut | 1 MT ≈ 7,33 BBL |
| Gasoil / Diesel | 1 MT ≈ 7,45 BBL |
| Essence | 1 MT ≈ 8,50 BBL |
| GPL (Propane) | 1 MT ≈ 12,40 BBL |
| GNL (LNG) | 1 MT ≈ 52 MMBtu |

Ces coefficients sont des moyennes industrielles. Pour le GNL, la composition du gaz et le pouvoir calorifique supérieur (PCS) motivent une hiérarchie spécifique : données énergétiques du certificat qualité (BTU/lb, MJ/kg, PCS) en priorité ; à défaut, **52 MMBtu/MT**, accompagné d’un indicateur de vigilance signalant l’absence de données qualité exactes.

## 4. Estimation du fret maritime

*Source : chapitre 4.*

La note privilégie une estimation explicable des conditions générales de marché. Elle regroupe les produits en quatre segments : brut ; raffinés (essence, diesel, Jet Fuel, Fuel Oil) ; GPL ; GNL. L’identification éventuelle du navire et du trajet AIS ne fournit pas à elle seule les conditions économiques exactes de l’affrètement.

**Tableau 4 — Référentiels de fret**

| Segment Transporté | Référentiel Économique de Fret | Nature du Référentiel | Ticker Bloomberg |
| --- | --- | --- | --- |
| Pétrole Brut | Route Worldscale composite | Référence composite construite à partir d'un panier de routes Worldscale |  |
| Produits Raffinés | Route Worldscale composite | Référence composite construite à partir d'un panier de routes Worldscale |  |
| GPL (LPG) | BLPG1 (USD/MT) | Future freight LPG indexé Baltic | FLR1 COMB Comdty |
| GNL (LNG) | Baltic BLNG1-174 (USD/charter day) | Future de fret LNG indexé sur le Baltic Exchange (Australie → Japon, méthanier de 174 000 m³) | IKA1 Comdty |

### 4.1. GPL et GNL : références directes

Pour le GPL, BLPG1 représente la route Golfe Arabo-Persique → Japon pour une cargaison de référence de 44 000 MT. Pour le GNL, BLNG1-174 représente Australie → Japon aller-retour pour un méthanier de 174 000 m³.

```text
Fret_unitaire_GPL = Indice_BLPG1                         [USD/MT]
Fret_total_GPL = Fret_unitaire_GPL × Quantité_transportée_MT

Taux_journalier_GNL = Indice_BLNG1-174                  [USD/jour]
Fret_total_GNL = Taux_journalier_GNL × Durée_affrètement_jours
```

Ces références sont employées comme proxies du segment, même lorsque la route de la transaction diffère de la route de référence.

### 4.2. Brut et raffinés : composite Worldscale initial

Dans le modèle décrit, chaque route combine un **flat rate annuel en USD/MT**, renouvelé au 1er janvier, et un **niveau Worldscale (WS)** reflétant le marché de cette route. WS100 représente 100 % du flat rate.

```text
Fret_unitaire_route = FlatRate_route × WS_route / 100
```

La première approche utilise un panier de quatre routes par segment.

**Tableau 5 — Panier brut / Dirty Tankers**

| Route Worldscale | Corridor Couvert | Ticker Bloomberg |
| --- | --- | --- |
| TD3C | Moyen-Orient → Chine | TD3CM1 SPEC Index |
| TD20 | Afrique de l’Ouest → Europe | TD20M1 MRXI Index |
| TD23 | Moyen-Orient → Europe | TD23M1 SPEC Index |
| TD25 | Golfe US → Europe | DD25M1 EGFI Index |

**Tableau 6 — Panier raffinés / Clean Tankers**

| Route Worldscale | Corridor Couvert | Ticker Bloomberg |
| --- | --- | --- |
| TC2 | Europe → Côte Est américaine | TC2FM1 MRXI Index |
| TC5 | Moyen-Orient → Japon | TC5FM1 MRXI Index |
| TC7 | Singapour → Australie | CD7FBOM EGFI Index |
| TC14 | Golfe US → Europe | TC14M1 MRXI Index |

Les deux composantes sont moyennées séparément, puis combinées :

```text
FlatRate_composite_dirty = (FR_TD3C + FR_TD20 + FR_TD23 + FR_TD25) / 4
WS_composite_dirty = (WS_TD3C + WS_TD20 + WS_TD23 + WS_TD25) / 4

FlatRate_composite_clean = (FR_TC2 + FR_TC5 + FR_TC7 + FR_TC14) / 4
WS_composite_clean = (WS_TC2 + WS_TC5 + WS_TC7 + WS_TC14) / 4

Fret_unitaire_proxy = FlatRate_composite × WS_composite / 100
Fret_total_proxy = Fret_unitaire_proxy × Quantité_transportée_MT
```

Le choix de la moyenne simple est motivé par la simplicité, la reproductibilité, l’auditabilité et l’absence de dépendance à des statistiques détaillées de flux.

### 4.3. Évolutions du fret envisagées

Une variante pondérée appliquerait les mêmes poids aux flat rates et aux niveaux WS :

```text
Poids_i = Volume_annuel_i / Somme_des_volumes_annuels
X_composite = Somme(X_i × Poids_i), avec X = FlatRate ou WS
```

Les pondérations ci-dessous sont des hypothèses indicatives à recalibrer, et non des statistiques officielles de trafic.

**Tableau 7 — Pondération indicative Dirty Tankers**

| Route | Corridor Couvert | Pondération Indicative | Justification Économique |
| --- | --- | --- | --- |
| TD3C | Moyen-Orient → Chine / Asie | 40 % | Principal corridor mondial d’exportation de brut vers les bassins asiatiques importateurs |
| TD20 | Afrique de l’Ouest → Europe | 15 % | Flux structurants du bassin Atlantique alimentant les raffineries européennes |
| TD23 | Moyen-Orient → Europe | 20 % | Corridor représentatif des arbitrages énergétiques entre Golfe et Europe |
| TD25 | Golfe US → Europe | 25 % | Importance croissante des exportations américaines de brut dans les équilibres énergétiques mondiaux |

**Tableau 8 — Pondération indicative Clean Tankers**

| Route | Corridor Couvert | Pondération Indicative | Justification Économique |
| --- | --- | --- | --- |
| TC2 | Europe → Côte Est américaine | 25 % | Flux importants de middle distillates entre Europe et Amérique du Nord |
| TC5 | Moyen-Orient → Japon / Asie | 30 % | Corridor majeur d’exportation de produits raffinés vers les marchés asiatiques |
| TC7 | Singapour → Australie | 20 % | Représentatif des flux intra-Asie Pacifique et du rôle central du hub de Singapour |
| TC14 | Golfe US → Europe | 25 % | Importance croissante des exportations américaines de produits raffinés vers l’Europe |

Une évolution supplémentaire rapprocherait les corridors POL/POD des routes réellement pertinentes, puis intégrerait tailles de navires et flat rates spécifiques. Une étape intermédiaire utiliserait les quatre routes déjà collectées : route unique en cas de correspondance (par exemple TD20 pour Afrique de l’Ouest → Europe), sinon repli sur le composite arithmétique. Ces évolutions sont présentées comme une trajectoire progressive, sans constituer un prérequis à l’approche initiale.

## 5. Deltas et bandes de plausibilité économique

*Source : sections 5.1 et 5.2.*

Les bandes proposées combinent deux sources d’incertitude : représentativité du benchmark (direct ou proxy) et estimation du fret (FOB ou CFR/CIF). Les proxies et l’ajout d’une estimation logistique motivent des bandes plus larges.

La note retient une première définition experte des seuils, faute de corpus représentatif de transactions à conformité économique établie et de paramètres contractuels complets. Une calibration ultérieure est envisagée à partir de données validées.

**Tableau 9 — Bandes indicatives de conformité (tableau 5 du Word)**

| Famille de Produit | Zone | Type de Benchmark | Seuil FOB | Seuil CFR / CIF | Justification et Logique d'Expert |
| --- | --- | --- | --- | --- | --- |
| Crude Oil (Brut) | Toutes zones | Futures directs (DME, WTI, Brent) | -15% à +10% | -20% à +15% | Benchmark direct très liquide, mais forte dispersion physique des qualités de brut (API/Soufre) et volatilité importante des taux de fret (Dirty Tankers / VLCC). |
| Gasoil / Diesel | Toutes zones | Futures / Swaps directs (ICE Gasoil, HO1, GAS10) | -2% à +5% | -7% à +10% | Forte standardisation du produit (ex: EN590 / ULSD) et très haute liquidité du marché dérivé. |
| Gasoline (Essence) | Amériques | Future direct (NYMEX RBOB) | -3% à +6% | -8% à +11% | Marché à terme direct liquide et très représentatif du bassin US. |
| Gasoline (Essence) | Reste du Monde | Benchmark Proxy (ICE Brent) | -8% à +10% | -12% à +15% | Incertitude Proxy : Nécessité d'absorber la variabilité structurelle des marges de raffinage (crack spread) non capturées par le brut. |
| Fuel Oil HSFO | Toutes zones | Swaps directs (380 CST / 3.5% Swaps) | -5% à +8% | -10% à +13% | Couverture directe via Swaps, mais décote structurelle et sensibilité forte aux spécifications techniques. |
| Fuel Oil VLSFO | Toutes zones | Swaps directs (Marine Fuel 0.5% Swaps) | -3% à +6% | -8% à +11% | Standard mondial du ravitaillement maritime post-IMO 2020. Prix fortement corrélé aux distillats. |
| Jet Fuel / Kerosene | Orient | Swap direct (Singapore Jet Swap) | -3% à +6% | -8% à +11% | Swaps boursiers dédiés très utilisés par la profession. |
| Jet Fuel / Kerosene | Europe / Afrique | Benchmark Proxy (ICE Gasoil) | -8% à +10% | -12% à +15% | Incertitude Proxy : Le différentiel résiduel absorbe les ajustements de spécifications aviation et les tensions de marché locales par rapport au Gasoil. |
| GPL (Propane / Butane) | Monde | Swap direct (Propane Mt Belvieu) | -5% à +8% | -6% à +10% | Marché régionalisé mais logistique dédiée (BLPG1) avec volatilité modérée du fret. |
| GNL (LNG) | Asie / Europe / USA | Futures / Swaps directs (JKM, TTF, Henry Hub) | -10% à +10% | -10% à +15% | Complexité des équivalences énergétiques (MMBtu/MT) et forte variabilité des taux d'affrètement journaliers (BLNG1). |

Ces valeurs constituent des **hypothèses initiales de plausibilité économique**, sans caractère réglementaire ni définitif. La lecture porte sur la distribution des Deltas de la fenêtre : moyenne, médiane, dispersion, minimum/maximum, stabilité et persistance d’un écart atypique. Elle cherche à limiter l’influence d’une anomalie journalière isolée.

## 6. Extensions statistiques envisagées

### 6.1. Volatilité : contextualisation du Delta

*Source : sections 5.3 et 6.3 — version ultérieure.*

Une fenêtre historique plus longue, par exemple **les six mois précédant le Shipped on Board Date**, servirait à contextualiser les résultats. Elle est distincte de la fenêtre courte de calcul des Deltas. La série historique serait le benchmark en FOB, ou le benchmark augmenté du fret estimé en CFR/CIF.

```text
r(t) = [P(t) − P(t−1)] / P(t−1)
Variance_initiale = Var(r(1), …, r(n))
Variance_EWMA(t) = λ × Variance_EWMA(t−1) + (1−λ) × r(t)²
λ indicatif = 0,94
```

Le calibrage serait propre au benchmark, avec comparaison aux niveaux et percentiles historiques.

**Tableau 10 — Régimes de volatilité illustratifs**

| Régime de marché | Positionnement statistique |
| --- | --- |
| Stable | Volatilité < percentile médian historique |
| Normal | Volatilité comprise entre le percentile médian et le percentile élevé |
| Stressé | Volatilité > percentile élevé historique |

Cette couche apporterait un contexte pour interpréter un dépassement et prioriser les investigations, sans modifier automatiquement les seuils ni valider une transaction de façon autonome.

### 6.2. Historique comportemental des Deltas

*Source : sections 5.4 et 6.4 — version ultérieure.*

L’autre extension porte sur les écarts historiques des transactions. Les Deltas seraient historisés avec produit, benchmark, Incoterm, corridor, acheteur, vendeur et date. Les populations comparables seraient segmentées par ces dimensions et, éventuellement, par caractéristiques logistiques.

Les indicateurs proposés sont la moyenne, la médiane, l’écart-type, les percentiles et la dispersion. Exemple de la note : un Delta de **+8 %**, compris dans une bande générale **−10 % à +10 %**, peut rester atypique si la population comparable se situe habituellement entre **+2 % et +4 %**.

Cette couche vise les dérives progressives et ruptures de comportement. La note mentionne comme conditions et limites la profondeur d’historique, les changements structurels, la qualité de segmentation et le surapprentissage. Son rôle reste complémentaire à l’analyse économique principale.

## 7. Différentiels de marché observables : extension optionnelle

*Source : chapitre 7 — version ultérieure.*

La note distingue les **différentiels physiques cotés** des autres composantes du prix (fret, assurance, crédit, conditions commerciales). Un différentiel est une prime ou une décote relative à un benchmark déterminé, publiée en série temporelle par des fournisseurs tels que Bloomberg, Platts ou Argus.

```text
Prix_physique = Prix_benchmark + Différentiel_marché
```

**Tableau 11 — Exemples de différentiels**

| Produit | Benchmark de Référence | Différentiel |
| --- | --- | --- |
| Brut Moyen-Orient | Oman | +1.25 USD/BBL |
| Diesel Europe | ICE Gasoil | -4 USD/MT |
| LNG Asie | JKM | +0.45 USD/MMBtu |

L’intégration envisagée suppose un benchmark de rattachement pris en charge, des unités cohérentes et une profondeur temporelle couvrant la période d’analyse. Un format d’import standardisé, par exemple CSV, contiendrait au minimum les champs suivants.

**Tableau 12 — Exemple de structure d’import**

| Date de validité | Produit | Benchmark de rattachement | Différentiel | Unité | Source |
| --- | --- | --- | --- | --- | --- |
| 2026-05-12 | Diesel 10ppm | ICE Gasoil | +3.25 | USD/MT | Argus |

L’effet attendu dans la note serait d’expliquer une partie des écarts de qualité et de marché actuellement absorbés par le Delta résiduel. Une dispersion moindre pourrait permettre un resserrement progressif des tolérances, notamment sur les produits standardisés et les corridors liquides.

**Tableau 13 — Illustration des bandes avec différentiels observables**

| Famille de Produit | Zone | Type de Benchmark | Seuil FOB Actuel | Seuil FOB avec Différentiel | Seuil CFR / CIF Actuel | Seuil CFR / CIF avec Différentiel |
| --- | --- | --- | --- | --- | --- | --- |
| Crude Oil (Brut) | Toutes zones | Futures directs (DME, WTI, Brent) | -15% à +10% | -8% à +6% | -20% à +15% | -12% à +10% |
| Gasoil / Diesel | Toutes zones | Futures / Swaps directs (ICE Gasoil, HO1, GAS10) | -2% à +5% | -2% à +3% | -7% à +10% | -5% à +6% |
| Gasoline (Essence) | Amériques | Future direct (NYMEX RBOB) | -3% à +6% | -2% à +4% | -8% à +11% | -6% à +8% |
| Gasoline (Essence) | Reste du Monde | Benchmark Proxy (ICE Brent) | -8% à +10% | -5% à +6% | -12% à +15% | -8% à +10% |
| Fuel Oil HSFO | Toutes zones | Swaps directs (380 CST / 3.5% Swaps) | -5% à +8% | -3% à +5% | -10% à +13% | -7% à +9% |
| Fuel Oil VLSFO | Toutes zones | Swaps directs (Marine Fuel 0.5% Swaps) | -3% à +6% | -2% à +4% | -8% à +11% | -5% à +8% |
| Jet Fuel / Kerosene | Orient | Swap direct (Singapore Jet Swap) | -3% à +6% | -2% à +4% | -8% à +11% | -5% à +8% |
| Jet Fuel / Kerosene | Europe / Afrique | Benchmark Proxy (ICE Gasoil) | -8% à +10% | -5% à +6% | -12% à +15% | -8% à +10% |
| GPL (Propane / Butane) | Monde | Swap direct (Propane Mt Belvieu) | -5% à +8% | -4% à +5% | -5% à +10% | -5% à +7% |
| GNL (LNG) | Asie / Europe / USA | Futures / Swaps directs (JKM, TTF, Henry Hub) | -10% à +10% | -6% à +6% | -10% à +15% | -8% à +10% |

Les colonnes « Actuel » reprennent les libellés et valeurs de ce tableau source. L’ensemble du tableau reste une illustration méthodologique : aucun de ces seuils ne constitue un paramètre opérationnel définitif. L’intégration de différentiels est une amélioration optionnelle de l’approche.

## 8. Restitution envisagée et mémoire du POC

*Source : chapitre 6 et conclusion.*

La restitution envisagée rend visibles la famille produit, le benchmark et l’Incoterm, avec modification explicite de la famille ou du benchmark, historisation et recalcul. Elle présente benchmark, fret estimé, prix théorique, prix facturé, Delta et positionnement dans les bandes.

Deux représentations sont proposées : un **waterfall** pour les contributions au prix et une **vue temporelle** pour comparer la facture aux références reconstruites sur la fenêtre. Les extensions ajouteraient régime de volatilité et positionnement dans une population comparable.

Pour la mémoire du projet, cette note conserve une exploration d’ensemble : **classification → routage → normalisation → estimation du fret selon l’Incoterm → série de prix théoriques → distribution des Deltas → restitution explicable**. Le socle initial décrit dans la source et ses extensions fournissent du contexte de recherche ; leur présence ici ne vaut ni adoption pour le POC, ni instruction d’implémentation.
