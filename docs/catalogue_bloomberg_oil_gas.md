# Catalogue Bloomberg Oil & Gas — audit documentaire

Audit réalisé le **16 octobre 2026**. Objet : vérifier la correspondance entre les identifiants proposés et leurs attributs (produit, localisation, nature, unité). Les 53 lignes initiales sont conservées, dont 36 identifiants renseignés et 17 pistes sans ticker.

**Résultat : 10 correspondances corroborées publiquement, 8 partielles, 18 tickers non corroborés et 17 références à découvrir. Aucun ticker n’a été testé dans un Terminal Bloomberg.** Les statuts portent sur les preuves décrites dans chaque ligne, pas sur les droits d’accès, la disponibilité actuelle, la complétude historique ou la convention de roll.

## Méthode et niveaux de preuve

L’étude recoupe les publications Bloomberg, les spécifications de bourse (ICE, CME, JPX), les définitions Baltic, les prospectus et les documents d’acteurs utilisant ces données. Les recherches ont porté sur les identifiants complets, puis sur leurs racines et les instruments économiques correspondants. Une page inaccessible ou l’absence de résultat public ne prouve pas qu’une sécurité n’existe pas.

- **C — Corroboré** : lien ticker/produit étayé et principaux attributs recoupés ; les réserves restantes figurent dans la ligne.
- **P — Partiel** : ticker retrouvé en contexte, mais contrat exact, place, unité ou nature insuffisamment documentés.
- **N — Non corroboré** : ticker complet non confirmé ; une spécification de produit similaire ne suffit pas à valider son identifiant Bloomberg.
- **D — À découvrir** : aucun ticker n’était fourni ; il s’agit d’un besoin de recherche, pas d’une référence exploitable.

**Attention aux conventions d’identification.** Un code ICE/CME n’est pas nécessairement une racine Bloomberg. Ajouter `1 Comdty` à un code de bourse n’est pas une méthode de validation. `USd` signifie cents américains et diffère de `USD`. Les suffixes de contribution (`SPEC`, `MRXI`, `EGFI`, éventuellement `COMB`) font partie de l’identification à contrôler ; ils ne sont pas ajoutés ou supprimés arbitrairement.

Dans les lignes P/N, les attributs décrivent le **produit recherché**, sauf preuve contraire explicitée. Une unité « attendue » n’est pas une unité Bloomberg validée. La zone peut être un hub, une place de cotation, un bassin physique ou un corridor : elle n’est pas automatiquement une règle POL/POD.

## Conclusions et corrections importantes

1. **Conway est aux États-Unis, au Kansas.** Les deux lignes initialement localisées au Canada sont corrigées. AltaGas distingue bien les exports canadiens de leurs destinations Conway et Mont Belvieu. [AltaGas, p. 98][altagas]
2. **JX1 est du kérosène japonais, pas un Jet Fuel aviation confirmé.** La famille est corrigée ; JPX décrit un grade JIS K2203 Grade 1. [SEC][sec], [JPX][jpx-kerosene]
3. **HO1 et XB1 restent en cents/gallon.** Leurs unités Bloomberg ne doivent pas être remplacées par celles des séries Yahoo en dollars/gallon. [HO1 Bloomberg][ho], [Marchés Bloomberg][markets]
4. **QS1 reste rattaché à ICE.** Le libellé « Nymex » de la page agrégée Bloomberg est contradictoire avec le guide ICE et le dépôt SEC ; cette contradiction est signalée plutôt que propagée. [ICE/Bloomberg][ice-bbg], [SEC][sec]
5. **SGB1 : unité et identité à reprendre.** Les contrats Singapour identifiés cotent au baril, alors que le tableau indiquait USD/MT. SGB est aussi un code de crack chez ICE, tandis que CME l’a utilisé pour son gasoil. Aucun rapprochement direct avec le ticker Bloomberg proposé n’est établi. [CME][sg-rule], [codes CME][sg-codes], [ICE SGB][sgb]
6. **MFT1 et S5FN1 nécessitent un contrôle prioritaire.** MFT désigne un crack chez ICE ; S5F désigne Singapour chez CME alors que la ligne vise Rotterdam. Ce sont des alertes de confusion de codes, et non des preuves que ces tickers Bloomberg désignent ces produits. Aucun ticker de remplacement n’est inventé. [ICE][marine], [CME][s5f]
7. **Les huit tickers de fret ne sont pas validés comme indices spot Worldscale.** Les corridors sont précisés ; contribution, maturité et unité restent à contrôler. Pour BLNG1-174, le démarrage au 15 décembre 2023 interdit de présumer une continuité de cette même spécification depuis 2020. [Baltic routes][baltic-routes], [Baltic BLNG][blng]
8. **L’ancien statut « Web vérifié » est remplacé.** AltaGas confirme six associations de tickers, mais ne fournit pas toutes leurs métadonnées. Intesa confirme les associations JKL1/JKM et PSVGM1/PSV sans établir complètement les instruments de marché.

## Catalogue des références

### Références avec preuve publique directe ou partielle

| Famille | Zone / corridor | Benchmark / instrument | Ticker Bloomberg | Nature | Unité | Vérification | Sources | Conclusion / contrôle restant |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Crude | Europe / Atlantique | ICE Brent | CO1 Comdty | Future générique de rang 1 | USD/bbl | C — Corroboré | [ICE/Bloomberg, p. 1–2][ice-bbg] ; [SEC][sec] ; [Bloomberg Marchés][markets] | CO désigne le Brent ICE ; CO1 est explicitement documenté comme historique générique du premier contrat. USD/bbl confirmé par Bloomberg. |
| Crude | Amérique du Nord / USA | NYMEX WTI Cushing | CL1 Comdty | Future générique de rang 1 | USD/bbl | C — Corroboré | [SEC][sec] ; [CME WTI][wti] | WTI NYMEX corroboré. Ne pas confondre avec le WTI ICE, dont la racine Bloomberg documentée est EN. |
| Crude | Moyen-Orient | Oman — DME, désormais GME | OQA1 Comdty | Future générique de rang 1 | USD/bbl | C — Corroboré | [Société Générale, annexe A][oman-sg] ; [GME][gme] | Le prospectus relie explicitement OQA1 au premier contrat Oman et au settlement en USD/baril. Appellation de la bourse actualisée ; vérifier la continuité de série. |
| Crude | Japon / Asie | Tokyo Crude Oil | CP1 Comdty | Future générique de rang 1 | JPY/kL | C — Corroboré | [SEC][sec] ; [JPX Dubai][jpx-dubai] ; [Bloomberg Énergie][energy] | CP1 : brut TOCOM corroboré ; JPY/kL affiché par Bloomberg. Le contrat pétrolier japonais est référencé au Dubai : Japon est la place de cotation, pas une origine physique du brut. Rattachement actuel au contrat JPX à confirmer dans DES. |
| Diesel / Gasoil | Europe / ICE | ICE Low Sulphur Gasoil | QS1 Comdty | Future générique de rang 1 | USD/MT | C — Corroboré | [ICE/Bloomberg][ice-bbg] ; [SEC][sec] ; [Bloomberg QS1][qs] | QS est bien la racine ICE Gasoil. La page agrégée Bloomberg Énergie affiche « Nymex » : ce libellé entre en conflit avec ICE et le dépôt SEC ; ne pas l’utiliser comme preuve de place. |
| Diesel / Gasoil | USA New York Harbor | NYMEX ULSD (historical Heating Oil symbol) | HO1 Comdty | Future générique de rang 1 | US cents/gal | C — Corroboré | [SEC][sec] ; [Bloomberg HO1][ho] ; [CME ULSD][ulsd] | US cents/gal conservé : Bloomberg affiche USd/gal, distinct de USD/gal. Le contrat CME est ULSD ; Heating Oil est le nom historique. |
| Essence | USA | NYMEX RBOB Gasoline | XB1 Comdty | Future générique de rang 1 | US cents/gal | C — Corroboré | [SEC][sec] ; [Bloomberg Marchés][markets] ; [CME RBOB][rbob] | RBOB NYMEX corroboré. Bloomberg affiche USd/gal (cents), tandis que le contrat CME se décrit en dollars et cents/gallon : contrôler l’échelle du champ exporté. |
| Gaz naturel | USA / Henry Hub | NYMEX Henry Hub | NG1 Comdty | Future générique de rang 1 | USD/MMBtu | C — Corroboré | [SEC][sec] ; [Intesa p. 12 et 36][intesa] | Henry Hub NYMEX corroboré ; USD/MMBtu. Référence de gaz naturel américain, pas un prix physique de GNL livré. |
| Gaz naturel | Europe / TTF | ICE Endex Dutch TTF | TZT1 Comdty | Future générique de rang 1 | EUR/MWh | C — Corroboré | [Vontobel / NGM][ttf-issuer] ; [ICE TTF][ttf] ; [Intesa p. 12][intesa] | Correspondance ICE Endex Dutch TTF corroborée et unité EUR/MWh cohérente. Ne pas confondre avec le TTF NYMEX collecté via Yahoo. |
| GNL | Asie nord-est | JKM LNG | JKL1 Comdty | Générique JKM cité ; place et contrat exact à confirmer | USD/MMBtu | P — Partiel | [Intesa, p. 12 et 29][intesa] | Le document associe JKL1 à JKM LNG et décrit des futures premier mois en USD/MMBtu. Il ne démontre pas la place, le contrat exact ni le roll Bloomberg. Ne pas déduire une équivalence avec NYMEX JKM=F. |
| Gaz naturel | Italie / PSV | PSV Gas Natural | PSVGM1 Comdty | Référence PSV 1 mois citée ; instrument exact à confirmer | EUR/MWh — cohérent avec la présentation | P — Partiel | [Intesa, p. 12 et 34][intesa] | Ticker PSV retrouvé ; la présentation situe le marché italien à 1 mois en EUR/MWh. Elle ne suffit pas à certifier un future de bourse ou un générique de rang 1. |
| Kérosène | Japon | Kérosène japonais TOCOM — JIS K2203 Grade 1 | JX1 Comdty | Future générique de rang 1 | JPY/kL | C — Corroboré | [SEC][sec] ; [JPX Kerosene][jpx-kerosene] | Famille corrigée : le produit livrable est un kérosène JIS K2203 Grade 1 ; la correspondance Jet Fuel aviation n’est pas établie. JPY/kL corroboré ; ne pas assimiler au Jet Singapour. |
| GPL / Propane | Asie FEI | FEI Propane Far East Index | AFE1 Comdty | Référence FEI propane ; contrat et rang à confirmer | À confirmer | P — Partiel | [AltaGas, p. 98][altagas] | L’association ticker/propane FEI est explicite. La page n’établit ni l’unité native, ni la place, ni le contrat, ni la règle de roll : ne pas confondre indice physique et dérivé associé. |
| GPL / Propane | États-Unis / Mont Belvieu, Texas | Mont Belvieu propane price index | LPGSMBPP Index | Indice de prix cité ; fournisseur et méthode à confirmer | À confirmer | P — Partiel | [AltaGas, p. 98][altagas] | Association ticker/produit/hub explicite. Unité, fournisseur primaire, fréquence et méthode non établis par la page. Ce n’est pas une référence Generic Front Month démontrée. |
| GPL / Butane | États-Unis / Mont Belvieu, Texas | Mont Belvieu normal butane index | LPGSMBNB Index | Indice de prix cité ; fournisseur et méthode à confirmer | À confirmer | P — Partiel | [AltaGas, p. 98][altagas] | Association ticker/produit/hub explicite. Unité, fournisseur primaire, fréquence et méthode non établis par la page. Ce n’est pas une référence Generic Front Month démontrée. |
| GPL / Propane | États-Unis / Conway, Kansas | Conway propane index | LPGSCWPP Index | Indice de prix cité ; fournisseur et méthode à confirmer | À confirmer | P — Partiel | [AltaGas, p. 98][altagas] | Association ticker/produit/hub explicite. Unité, fournisseur primaire, fréquence et méthode non établis par la page. Ce n’est pas une référence Generic Front Month démontrée. Géographie corrigée : Canada → États-Unis (Kansas). |
| GPL / Butane | États-Unis / Conway, Kansas | Conway normal butane index | LPGSCWNB Index | Indice de prix cité ; fournisseur et méthode à confirmer | À confirmer | P — Partiel | [AltaGas, p. 98][altagas] | Association ticker/produit/hub explicite. Unité, fournisseur primaire, fréquence et méthode non établis par la page. Ce n’est pas une référence Generic Front Month démontrée. Géographie corrigée : Canada → États-Unis (Kansas). |
| Fret GPL | Moyen Orient vers Japon | Baltic LPG Freight | FLR1 Comdty | Référence de fret citée ; contrat exact à confirmer | USD/MT pour BLPG1 ; unité du ticker à confirmer | P — Partiel | [AltaGas, p. 98][altagas] ; [Baltic, BLPG1][baltic-gmb] | AltaGas cite FLR1 pour le fret Baltic, sans identifier BLPG1 ni le contrat. Le coefficient 75 % est une hypothèse propre à sa présentation, pas la définition du ticker. |

### Tickers proposés sans correspondance Bloomberg établie

| Famille | Zone / corridor | Benchmark / instrument | Ticker Bloomberg | Nature | Unité | Vérification | Sources | Conclusion / contrôle restant |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Diesel / Gasoil | Singapour / Asie | Singapore Gasoil 10ppm Platts swap | SGB1 Comdty | Instrument recherché ; ticker non validé | USD/bbl pour les contrats identifiés ; ticker à confirmer | N — Non corroboré | [CME ch. 669][sg-rule] ; [CME codes SG/SGB][sg-codes] ; [ICE GST][gst] ; [ICE SGB][sgb] | Unité USD/MT initiale non étayée : les références outright identifiées sont en USD/bbl. SGB existe comme code CME de gasoil et comme code ICE de crack gasoil/Brent ; aucun de ces codes ne prouve SGB1 Bloomberg. Vérifier aussi le grade 10 ppm et son historique. |
| Fuel Oil HSFO | Singapour | Singapore Fuel Oil 380 CST swap | SYS1 Comdty | Instrument recherché ; ticker non validé | USD/MT attendu ; ticker non validé | N — Non corroboré | [ICE liste historique][ice-otc] ; [ICE marge SYS/BAR][sys-bar] | SYS est un code ICE du 380 CST Singapour, et la taille de lot historique est 1 000 MT. Cela corrobore le produit, pas le ticker Bloomberg SYS1. Future/ancien swap et unité du champ à contrôler. |
| Fuel Oil HSFO | US Gulf Coast | US Gulf Coast Fuel Oil 3.0% swap | MFB1 Comdty | Instrument recherché ; ticker non validé | À confirmer — USD/MT initial non validé | N — Non corroboré | [Note][note] ; [ICE évolution USGC HSFO][usgc] | MFB1 non corroboré. Le libellé USGC 3.0 % doit être rapproché de la spécification et de sa période : ICE documente des changements de références HSFO et des cotations par baril. Ne pas fixer USD/MT par analogie avec Rotterdam. |
| Fuel Oil HSFO | Rotterdam / Europe | Rotterdam Fuel Oil 3.5% barges swap | BAR1 Comdty | Instrument recherché ; ticker non validé | USD/MT attendu ; ticker non validé | N — Non corroboré | [ICE BAR][bar] | ICE confirme BAR, un future à règlement financier sur le fioul 3,5 % FOB Rotterdam, en USD/MT. Le passage du code de bourse BAR au ticker Bloomberg BAR1 n’est pas démontré. |
| Fuel Oil VLSFO | Singapour | Singapore Marine Fuel 0.5% swap | MFT1 Comdty | Instrument recherché ; ticker non validé | USD/MT attendu ; ticker non validé | N — Non corroboré | [ICE liste Marine][marine] ; [ICE MF4 outright][mf4] | Alerte code : chez ICE, MFT est un crack Marine Fuel Singapour/Brent en barils. L’outright OTC identifié porte MF4. Cela ne prouve pas l’identité Bloomberg MFT1 ; conserver en attente, ne pas l’utiliser comme prix absolu. |
| Fuel Oil VLSFO | US Gulf Coast | US Gulf Coast Marine Fuel 0.5% swap | AMR1 Comdty | Instrument recherché ; ticker non validé | USD/MT attendu ; ticker non validé | N — Non corroboré | [Note de travail][note] | Aucune correspondance publique directe retrouvée. Vérifier spécifiquement USGC, grade 0,5 %, fournisseur de l’assessment, et distinction outright/crack ; ne pas réutiliser un produit Singapour ou Rotterdam. |
| Fuel Oil VLSFO | Rotterdam / Europe | Marine Fuel 0.5% barges FOB Rotterdam swap | S5FN1 Comdty | Instrument recherché ; ticker non validé | USD/MT attendu ; ticker non validé | N — Non corroboré | [CME S5F][s5f] ; [ICE MF3 Rotterdam][mf3] | Alerte géographique : le code CME S5F désigne Singapour, pas Rotterdam ; le swap OTC Rotterdam identifié chez ICE porte MF3. Le lien avec S5FN1 Bloomberg reste inconnu. Ne pas remplacer par un ticker construit à partir de ces codes. |
| Jet Fuel | Singapour / Asie | Singapore Jet Kerosene swap | JKS1 Comdty | Instrument recherché ; ticker non validé | USD/bbl attendu ; ticker non validé | N — Non corroboré | [Note de travail][note] | JKS1 non corroboré. Rechercher un prix absolu Singapore Jet/Kerosene, pas un crack Jet/Gasoil ou Jet/Brent ; confirmer qualité, place et USD/bbl dans DES. |
| GPL / Propane | Mont Belvieu / USA | Mont Belvieu propane swap | PNL1 Comdty | Instrument recherché ; ticker non validé | US cents/gal attendu ; ticker non validé | N — Non corroboré | [Note de travail][note] | PNL1 non corroboré. Identifier le fournisseur et le segment Mont Belvieu (TET/non-TET, LDH/non-LDH), puis vérifier future/indice et cents versus dollars/gallon. Les indices LPGSMBPP ne valident pas ce ticker. |
| Fret GNL | Australie -> Japon | Baltic LNG 174k cbm freight | IKA1 Comdty | Instrument recherché ; ticker non validé | USD/charter day attendu ; ticker non validé | N — Non corroboré | [Baltic BLNG1-174][blng] ; [CME BLNG1-174][cme-blng] | Route et unité du BLNG1-174 corroborées ; aucune preuve du ticker IKA1. La nouvelle référence 174 000 m³ démarre le 15 décembre 2023 : ne pas présumer un historique homogène depuis 2020. |
| Fret crude | Moyen-Orient → Chine | Baltic TD3C | TD3CM1 SPEC Index | Série contribuée / maturité à identifier | À confirmer : WS, USD/MT ou USD/jour selon série | N — Non corroboré | [Baltic routes][baltic-routes] ; [Note][note] | Le corridor Baltic est corroboré, pas cet identifiant Bloomberg ni sa contribution. Ne pas assimiler une série M1/forward/Balmo à l’indice spot ; vérifier source SPEC/MRXI/EGFI et unité. La formule flat rate × WS/100 ne vaut que pour une cotation WS. |
| Fret crude | Afrique de l’Ouest → Royaume-Uni / continent européen | Baltic TD20 | TD20M1 MRXI Index | Série contribuée / maturité à identifier | À confirmer : WS, USD/MT ou USD/jour selon série | N — Non corroboré | [Baltic routes][baltic-routes] ; [Note][note] | Le corridor Baltic est corroboré, pas cet identifiant Bloomberg ni sa contribution. Ne pas assimiler une série M1/forward/Balmo à l’indice spot ; vérifier source SPEC/MRXI/EGFI et unité. La formule flat rate × WS/100 ne vaut que pour une cotation WS. |
| Fret crude | Golfe du Moyen-Orient → Méditerranée | Baltic TD23 | TD23M1 SPEC Index | Série contribuée / maturité à identifier | À confirmer : WS, USD/MT ou USD/jour selon série | N — Non corroboré | [Baltic routes][baltic-routes] ; [Note][note] | Le corridor Baltic est corroboré, pas cet identifiant Bloomberg ni sa contribution. Ne pas assimiler une série M1/forward/Balmo à l’indice spot ; vérifier source SPEC/MRXI/EGFI et unité. La formule flat rate × WS/100 ne vaut que pour une cotation WS. |
| Fret crude | Golfe US → Amsterdam-Rotterdam-Anvers | Baltic TD25 | DD25M1 EGFI Index | Série contribuée / maturité à identifier | À confirmer : WS, USD/MT ou USD/jour selon série | N — Non corroboré | [Baltic routes][baltic-routes] ; [Note][note] | Le corridor Baltic est corroboré, pas cet identifiant Bloomberg ni sa contribution. Ne pas assimiler une série M1/forward/Balmo à l’indice spot ; vérifier source SPEC/MRXI/EGFI et unité. La formule flat rate × WS/100 ne vaut que pour une cotation WS. |
| Fret refined | Continent européen → côte atlantique US | Baltic TC2_37 | TC2FM1 MRXI Index | Série contribuée / maturité à identifier | À confirmer : WS, USD/MT ou USD/jour selon série | N — Non corroboré | [Baltic routes][baltic-routes] ; [Note][note] | Le corridor Baltic est corroboré, pas cet identifiant Bloomberg ni sa contribution. Ne pas assimiler une série M1/forward/Balmo à l’indice spot ; vérifier source SPEC/MRXI/EGFI et unité. La formule flat rate × WS/100 ne vaut que pour une cotation WS. |
| Fret refined | Golfe du Moyen-Orient → Japon | Baltic TC5 | TC5FM1 MRXI Index | Série contribuée / maturité à identifier | À confirmer : WS, USD/MT ou USD/jour selon série | N — Non corroboré | [Baltic routes][baltic-routes] ; [Note][note] | Le corridor Baltic est corroboré, pas cet identifiant Bloomberg ni sa contribution. Ne pas assimiler une série M1/forward/Balmo à l’indice spot ; vérifier source SPEC/MRXI/EGFI et unité. La formule flat rate × WS/100 ne vaut que pour une cotation WS. |
| Fret refined | Singapour → côte est de l’Australie | Baltic TC7 | CD7FBOM EGFI Index | Série contribuée / maturité à identifier | À confirmer : WS, USD/MT ou USD/jour selon série | N — Non corroboré | [Baltic routes][baltic-routes] ; [Note][note] | Le corridor Baltic est corroboré, pas cet identifiant Bloomberg ni sa contribution. Ne pas assimiler une série M1/forward/Balmo à l’indice spot ; vérifier source SPEC/MRXI/EGFI et unité. La formule flat rate × WS/100 ne vaut que pour une cotation WS. |
| Fret refined | Golfe US → continent européen | Baltic TC14 | TC14M1 MRXI Index | Série contribuée / maturité à identifier | À confirmer : WS, USD/MT ou USD/jour selon série | N — Non corroboré | [Baltic routes][baltic-routes] ; [Note][note] | Le corridor Baltic est corroboré, pas cet identifiant Bloomberg ni sa contribution. Ne pas assimiler une série M1/forward/Balmo à l’indice spot ; vérifier source SPEC/MRXI/EGFI et unité. La formule flat rate × WS/100 ne vaut que pour une cotation WS. |

### Pistes initiales sans ticker

Ces lignes sont conservées comme besoins de recherche. Aucune validation de ticker n’est possible tant qu’un identifiant n’a pas été sélectionné. Le fret demeure hors du périmètre fonctionnel de la collecte V1, mais a été inclus dans cet audit du catalogue.

| Famille | Zone / corridor | Benchmark / instrument | Ticker Bloomberg | Nature | Unité | Vérification | Sources | Conclusion / contrôle restant |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Crude | EAU / Fujairah | ICE Murban futures | À découvrir sur Terminal | Benchmark physique / future à définir | À confirmer | D — À découvrir | [Périmètre de recherche][note] | Aucun ticker fourni : correspondance non testable. Définir le produit exact puis rechercher la sécurité ; la page Bloomberg Énergie n’atteste pas cette ligne. |
| Crude | Dubai | Dubai crude physical assessment / swap | À découvrir sur Terminal | Benchmark physique / future à définir | À confirmer | D — À découvrir | [Périmètre de recherche][note] | Aucun ticker fourni : correspondance non testable. Définir le produit exact puis rechercher la sécurité ; la page Bloomberg Énergie n’atteste pas cette ligne. |
| Crude | Canada | Western Canadian Select WCS | À découvrir sur Terminal | Benchmark physique / future à définir | À confirmer | D — À découvrir | [Périmètre de recherche][note] | Aucun ticker fourni : correspondance non testable. Définir le produit exact puis rechercher la sécurité ; la page Bloomberg Énergie n’atteste pas cette ligne. |
| Crude | US Gulf Coast | Mars / LLS crude oil | À découvrir sur Terminal | Benchmark physique / future à définir | À confirmer | D — À découvrir | [Périmètre de recherche][note] | Aucun ticker fourni : correspondance non testable. Définir le produit exact puis rechercher la sécurité ; la page Bloomberg Énergie n’atteste pas cette ligne. |
| Diesel | Arabian Gulf | Gasoil 10ppm FOB Arab Gulf physical | À découvrir sur Terminal | Benchmark physique / future à définir | À confirmer | D — À découvrir | [Périmètre de recherche][note] | Aucun ticker fourni : correspondance non testable. Définir le produit exact puis rechercher la sécurité ; la page Bloomberg Énergie n’atteste pas cette ligne. |
| Diesel | Rotterdam / ARA | ULSD 10ppm FOB Rotterdam physical | À découvrir sur Terminal | Benchmark physique / future à définir | À confirmer | D — À découvrir | [Périmètre de recherche][note] | Aucun ticker fourni : correspondance non testable. Définir le produit exact puis rechercher la sécurité ; la page Bloomberg Énergie n’atteste pas cette ligne. |
| Essence | Singapour | Gasoline RON92 FOB Singapore | À découvrir sur Terminal | Benchmark physique / future à définir | À confirmer | D — À découvrir | [Périmètre de recherche][note] | Aucun ticker fourni : correspondance non testable. Définir le produit exact puis rechercher la sécurité ; la page Bloomberg Énergie n’atteste pas cette ligne. |
| Essence | Europe / ARA | Eurobob FOB Rotterdam | À découvrir sur Terminal | Benchmark physique / future à définir | À confirmer | D — À découvrir | [Périmètre de recherche][note] | Aucun ticker fourni : correspondance non testable. Définir le produit exact puis rechercher la sécurité ; la page Bloomberg Énergie n’atteste pas cette ligne. |
| Jet Fuel | Europe / ARA | Jet Fuel FOB ARA | À découvrir sur Terminal | Benchmark physique / future à définir | À confirmer | D — À découvrir | [Périmètre de recherche][note] | Aucun ticker fourni : correspondance non testable. Définir le produit exact puis rechercher la sécurité ; la page Bloomberg Énergie n’atteste pas cette ligne. |
| Jet Fuel | Arabian Gulf | Jet Fuel FOB Arab Gulf | À découvrir sur Terminal | Benchmark physique / future à définir | À confirmer | D — À découvrir | [Périmètre de recherche][note] | Aucun ticker fourni : correspondance non testable. Définir le produit exact puis rechercher la sécurité ; la page Bloomberg Énergie n’atteste pas cette ligne. |
| Fuel Oil | Fujairah | VLSFO bunker Fujairah | À découvrir sur Terminal | Benchmark physique / future à définir | À confirmer | D — À découvrir | [Périmètre de recherche][note] | Aucun ticker fourni : correspondance non testable. Définir le produit exact puis rechercher la sécurité ; la page Bloomberg Énergie n’atteste pas cette ligne. |
| GPL | Arabian Gulf | Saudi CP propane / butane | À découvrir sur Terminal | Benchmark physique / future à définir | À confirmer | D — À découvrir | [Périmètre de recherche][note] | Aucun ticker fourni : correspondance non testable. Définir le produit exact puis rechercher la sécurité ; la page Bloomberg Énergie n’atteste pas cette ligne. |
| Gaz naturel | Royaume-Uni | NBP futures | À découvrir sur Terminal | Benchmark physique / future à définir | À confirmer | D — À découvrir | [Périmètre de recherche][note] | Aucun ticker fourni : correspondance non testable. Définir le produit exact puis rechercher la sécurité ; la page Bloomberg Énergie n’atteste pas cette ligne. |
| Gaz naturel | France | PEG futures | À découvrir sur Terminal | Benchmark physique / future à définir | À confirmer | D — À découvrir | [Périmètre de recherche][note] | Aucun ticker fourni : correspondance non testable. Définir le produit exact puis rechercher la sécurité ; la page Bloomberg Énergie n’atteste pas cette ligne. |
| GNL | Europe / DES | LNG DES Northwest Europe physical assessment | À découvrir sur Terminal | Benchmark physique / future à définir | À confirmer | D — À découvrir | [Périmètre de recherche][note] | Aucun ticker fourni : correspondance non testable. Définir le produit exact puis rechercher la sécurité ; la page Bloomberg Énergie n’atteste pas cette ligne. |
| GNL | USA Gulf / FOB | LNG FOB US Gulf physical | À découvrir sur Terminal | Benchmark physique / future à définir | À confirmer | D — À découvrir | [Périmètre de recherche][note] | Aucun ticker fourni : correspondance non testable. Définir le produit exact puis rechercher la sécurité ; la page Bloomberg Énergie n’atteste pas cette ligne. |
| Fret | Moyen-Orient -> Europe | Route tanker-specific rates / voyage freight | À découvrir sur Terminal | Benchmark physique / future à définir | À confirmer | D — À découvrir | [Périmètre de recherche][note] | Aucun ticker fourni : correspondance non testable. Définir le produit exact puis rechercher la sécurité ; la page Bloomberg Énergie n’atteste pas cette ligne. |

## Guide d’extraction Bloomberg

### 1. Délimiter l’extraction

Pour cette première version du POC, sélectionner les références de **prix de produits**, selon la famille et la zone pivot. Les lignes de fret restent documentées dans le catalogue mais ne font pas partie de l’extraction V1. Ne réaliser ni conversion d’unité, ni normalisation, ni ajout de fret.

La convention visée est **Generic Front Month**, c’est-à-dire le générique de rang 1 du contrat retenu. Un indice physique, une référence « 1 mois » ou un ticker se terminant par `1` ne suffisent pas à démontrer cette convention. Les lignes P, N et D doivent être résolues avant d’être incluses ; les lignes C nécessitent également le contrôle opérationnel ci-dessous.

### 2. Identifier la sécurité et ses attributs sur Terminal

Saisir le ticker complet, avec son secteur (`Comdty` ou `Index`) et sa contribution lorsqu’elle est indiquée. Examiner sa description dans `DES`. Si l’identifiant ne résout pas la sécurité attendue, utiliser la recherche `SECF` avec le nom du produit, la bourse et la localisation. Pour les contrats ICE, le guide ICE documente aussi `CEM` puis `ICE`, ainsi que `CTM` pour rechercher les contrats. [Guide Bloomberg][blp-guide], [Guide ICE][ice-bbg]

Pour chaque sécurité retenue, relever le nom complet, l’identifiant exact, la bourse ou le contributeur, le produit et son grade, le lieu de livraison ou d’évaluation, la devise, l’unité et l’échelle de cotation. Contrôler notamment `USd` contre `USD`, le baril contre la tonne, le kérosène contre le carburant aviation et le prix absolu contre un crack ou un différentiel.

Conserver séparément la **zone du marché** et la **règle de sélection POL/POD du POC**. La première est une propriété de la référence ; la seconde est un choix méthodologique du projet. L’une ne se déduit pas automatiquement de l’autre.

### 3. Confirmer le générique et documenter son roll

Ouvrir la chaîne de contrats et vérifier que la série est bien celle du premier contrat selon la convention Bloomberg applicable. Le guide ICE distingue explicitement la racine suivie de `1` (premier générique) de la racine suivie de `A` (contrat le plus actif). Ces séries ne sont pas interchangeables. [Guide ICE][ice-bbg]

Relever la règle de bascule vers le contrat suivant, le calendrier et les éventuels réglages d’ajustement. Ne pas présumer que toutes les séries basculent le même jour, à l’échéance ou au premier avis de livraison. En cas de doute, consulter l’aide de la sécurité ou l’assistance Bloomberg avant de figer la définition.

Le résultat attendu est une série générique avec ses sauts éventuels au changement de contrat, **sans rétroajustement ajouté par notre traitement**. Vérifier si Bloomberg applique lui-même un ajustement et le consigner. Lorsque disponible, conserver le contrat daté sous-jacent à chaque observation ; sinon, signaler que cette traçabilité n’a pas été obtenue.

### 4. Choisir le champ de prix et faire un essai court

Utiliser `FLDS` pour vérifier la définition du champ et son admissibilité à l’historique pour la sécurité. `PX_LAST` est un candidat, mais ne signifie pas systématiquement « règlement officiel ». Si un règlement est recherché, vérifier un champ tel que `PX_SETTLE` dans `FLDS` avant de l’utiliser ; son existence et sa disponibilité ne sont pas supposées universelles. Consigner le champ réellement extrait et sa signification. [Guide Bloomberg, recherche des champs et données historiques][blp-guide]

Extraire d’abord une courte période, avec un échantillon entourant un changement de contrat connu. Comparer quelques observations à l’affichage Terminal et aux contrats datés. Vérifier l’échelle, la devise, les jours sans cotation et le comportement au roll. Un échec de droits ou de champ ne doit pas être interprété comme l’absence du ticker.

### 5. Télécharger l’historique

Dans Excel équipé de l’add-in Bloomberg, utiliser l’assistant de données historiques pour générer une requête `BDH`. Exemple minimal :

```excel
=BDH(A2,B2,C2,D2)
```

Ici, `A2` contient le ticker complet, `B2` le champ validé, et `C2` / `D2` les dates de début et de fin sous forme de dates Excel. Le séparateur dépend de la configuration d’Excel. Cet exemple ne fixe pas les options : sélectionner explicitement une périodicité quotidienne et contrôler le calendrier, le traitement des jours sans observation et les éventuels ajustements dans l’assistant. Ne pas demander de conversion de devise ou d’unité. [Guide Bloomberg, section 15.4][blp-guide]

Pour automatiser depuis un environnement autorisé, la Desktop API utilise le service `//blp/refdata` et une `HistoricalDataRequest` avec les sécurités, les champs et les bornes de dates. L’API reste soumise à l’accès Bloomberg disponible ; elle ne constitue pas une API publique gratuite. Enregistrer les erreurs de sécurité et les erreurs de champ séparément des observations. [Guide Bloomberg][blp-guide]

Télécharger ensuite la période utile, en respectant le début réel de chaque historique. Ne pas remplacer les données absentes par zéro ni propager automatiquement la dernière valeur. Conserver les valeurs négatives valides. Une série qui commence tard ne doit pas être prolongée artificiellement à partir d’un instrument voisin.

### 6. Conserver un export vérifiable

Produire deux fichiers, puis les importer dans les tables descriptives et de prix de SQLite :

- **`references.csv`** : identifiant interne, famille, zone pivot, logique POL/POD, référence de marché, ticker complet, nature, bourse/contributeur, unité principale native et devise, champ choisi, convention générique, règle de roll connue, réserves et date de vérification.
- **`prix.csv`** : identifiant de référence, date de cotation, valeur brute, champ, et contrat daté sous-jacent lorsqu’il est disponible. Conserver aussi la date de récupération et la provenance de l’extraction.

Archiver les exports bruts et les paramètres de requête. Séparer les erreurs et les absences de données des prix ; éviter les doublons lors d’une réimportation. La devise, l’unité et le champ doivent rester identifiables sans ambiguïté pour chaque observation.

Avant de déclarer une référence exploitable, vérifier que son identité économique, son unité, sa nature de prix et sa convention Generic Front Month sont documentées. Mettre alors à jour sa ligne avec les éléments obtenus sur Terminal. Une confirmation documentaire publique, seule, ne remplace pas ce contrôle.

## Sources de l’audit

Les liens ci-dessous sont cités dans les lignes concernées. Les documents anciens (notamment le dépôt SEC de 2013 et le guide ICE) établissent des correspondances historiques : ils ne certifient pas à eux seuls la disponibilité actuelle. Les pages de bourse définissent leurs contrats, pas nécessairement les tickers Bloomberg proposés.

- [Bloomberg — guide API et Excel][blp-guide] ; [ICE — guide des contrats dans Bloomberg][ice-bbg].
- [SEC — correspondances historiques de tickers][sec] ; [Intesa Sanpaolo — énergie, juin 2024][intesa] ; [AltaGas — Investor Day 2023, p. 98][altagas].
- Les spécifications ICE, CME, JPX et Baltic sont accessibles depuis chaque ligne du catalogue.

[sec]: https://www.sec.gov/Archives/edgar/data/904918/000110465913039965/a13-8578_1ex10d02.htm
[energy]: https://bloomberg.com/energy
[ice-bbg]: https://www.ice.com/publicdocs/data/ICE_on_Bloomberg.pdf
[wti]: https://www.cmegroup.com/markets/energy/crude-oil/light-sweet-crude.contractSpecs.html
[oman-sg]: https://usprogram.socgen.com/files/252.pdf
[gme]: https://www.gulfmerc.com/gme-product-services/gme-data
[jpx-dubai]: https://www.jpx.co.jp/english/derivatives/products/energy/platts-dubai-futures/01.html
[qs]: https://www.bloomberg.com/quote/QS1%3ACOM
[ho]: https://www.bloomberg.com/quote/HO1%3ACOM
[ulsd]: https://www.cmegroup.com/markets/energy/refined-products/heating-oil.contractSpecs.html
[markets]: https://bloomberg.com/markets/commodities
[rbob]: https://www.cmegroup.com/markets/energy/refined-products/rbob-gasoline.contractSpecs.html
[intesa]: https://world.intesasanpaolo.com/content/dam/portalgroup/repository-documenti/newsroom/area-media-dsr/2024/Focus_materie_prime_energia_giugno_2024.pdf
[ttf-issuer]: https://idoc.ngm.se/20250110133937011894.pdf
[ttf]: https://www.ice.com/products/27996665/Dutch-TTF-Natural-Gas-Futures/1000
[jpx-kerosene]: https://www.jpx.co.jp/english/derivatives/products/energy/kerosene-futures/01.html
[altagas]: https://www.altagas.ca/sites/default/files/2023-12/AltaGas%202023%20Investor%20Day.pdf
[baltic-gmb]: https://www.balticexchange.com/content/dam/balticexchange/consumer/data-services-/documents-/ocean-bulk/GMB.pdf
[note]: travaux_preliminaires_oil_gas.md
[sg-rule]: https://www.cmegroup.com/content/dam/cmegroup/rulebook/NYMEX/6/669.pdf
[sg-codes]: https://www.cmegroup.com/tools-information/lookups/advisories/ser/files/ser-6974.pdf
[gst]: https://www.ice.com/products/6753528/Gasoil-Outright---Singapore-Gasoil-%28Platts%29-Future
[sgb]: https://www.ice.com/products/79234930
[ice-otc]: https://www.ice.com/publicdocs/ICE_OTC_Cleared_Product_List.pdf
[sys-bar]: https://www.ice.com/api/productguide/margin-rates/6753479/pdf
[usgc]: https://www.ice.com/publicdocs/futures_us/exchange_notices/ICE_Futures_US_14Xand14WRelisting_2020_08_18.pdf
[bar]: https://www.ice.com/products/6753479/Fuel
[marine]: https://www.ice.com/products/?filter=marine
[mf4]: https://www.ice.com/api/productguide/spec/71857860/pdf
[s5f]: https://www.cmegroup.com/notices/electronic-trading/2018/12/20181203.html
[mf3]: https://www.ice.com/api/productguide/spec/71857845/pdf
[blng]: https://www.balticexchange.com/en/data-services/Circulars/market-announcements-/category-a/2023/circular-35-23---new-index--blng1-174--blng2-174--blng3-174-goes.html
[cme-blng]: https://www.cmegroup.com/markets/energy/freight/lng-freight-australia-to-japan-blng1-174.html
[baltic-routes]: https://www.balticexchange.com/en/data-services/market-information0/indices.html
[blp-guide]: https://data.bloomberglp.com/professional/sites/4/BLPAPI-Core-Developer-Guide.pdf
