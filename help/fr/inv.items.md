# Produits {#inv.items}

La fiche produit est le centre de l'ERP : les achats, le stock, les recettes de production et les ventes la lisent. Un produit peut être un bien ou un service, tenu en stock ou non.

**Où :** **Inventaire > Produits**. Cliquez sur un produit pour l'ouvrir, ou sur **Nouveau** pour en créer un.

Certains champs sont marqués *À titre d'information* : ils sont conservés et affichés, mais rien ne les utilise encore. Ils servent aux modules à venir (comptabilité, expédition, étiquettes).

## Liste {#inv.items.list}

Colonnes : Produit, Description, Catégorie, Produit ou service, Classe, Unité, En main, Disponible, Prix 1 et Statut.

Filtres : Statut, Produit ou service, Type de stock, Classe et Catégorie. La recherche porte sur le code, les descriptions en français et en anglais, la catégorie, la marque, le code à barres (UPC), le numéro de pièce du fabricant et le fabricant.

*En main* et *Disponible* ne sont affichés que pour les produits avec *Tenu en stock* coché. Les autres affichent « — ».

## Général {#inv.items.general}

### Produit {#inv.items.cCode}

Le code unique du produit, en anglais et sans espaces (par exemple `TUBE-T8`). Obligatoire. Il ne peut plus être changé une fois enregistré.

### Statut {#inv.items.cStatus}

*Actif*, *Inactif* ou *Discontinué*. Seul un produit actif peut être mis sur une facture et est acheté par le réapprovisionnement.

### Catégorie {#inv.items.cCategory}

La catégorie du produit (**Inventaire > Catégories / unités**). Elle regroupe les produits et sert de base aux escomptes par catégorie des listes de prix.

### Produit ou service {#inv.items.cNature}

*Produit* est un bien. *Service* est de la main-d'œuvre, du transport ou du conseil. À l'enregistrement d'un service, le système met le *Type de stock* à *Non physique* et vide la *Classe*.

### Type de stock {#inv.items.cStockType}

*Physique* : quelque chose qui se trouve sur une tablette. *Non physique* : une licence, un abonnement ou un article numérique, sans stock. Affiché pour les produits seulement.

### Classe {#inv.items.cClass}

Le rôle du produit : *Matière première*, *Ensemble / assemblage*, *Produit fini*, *Fourniture / consommable* ou *Immobilisation*. Laissez vide pour la marchandise achetée pour la revente. Sert à filtrer et à trier la liste des produits.

### Description (français) {#inv.items.cDescFR}

Description courte en français. Obligatoire. Elle va sur les factures des clients francophones.

### Description (anglais) {#inv.items.cDescEN}

Description courte en anglais. Elle va sur les factures des clients anglophones. Vide : la description française est utilisée.

### Description longue (français) {#inv.items.cLongDescFR}

Texte libre plus long, pour une fiche technique ou un catalogue. À titre d'information.

### Description longue (anglais) {#inv.items.cLongDescEN}

La même chose en anglais. À titre d'information.

### Marque {#inv.items.cBrand}

Marque du produit. La recherche trouve un produit par sa marque. À titre d'information.

### Modèle {#inv.items.cModel}

Modèle du produit. À titre d'information.

### Fabricant {#inv.items.cManufacturer}

Qui fabrique le produit. La recherche trouve un produit par son fabricant. À titre d'information.

### No pièce fabricant {#inv.items.cMfrPartNo}

Le code du produit chez le fabricant. La recherche trouve un produit par ce numéro. À titre d'information.

### Code à barres (UPC / EAN) {#inv.items.cUPC}

Le code à barres du produit. La recherche trouve un produit par son code à barres. Il sera lu à la réception et à la préparation quand des lecteurs seront utilisés.

### Photo (lien) {#inv.items.cImageUrl}

Lien vers une photo du produit. À titre d'information.

### Fiche technique (lien) {#inv.items.cSpecUrl}

Lien vers la fiche technique. À titre d'information.

### Fiche de données de sécurité (lien) {#inv.items.cSdsUrl}

Lien vers la fiche de données de sécurité (FDS / SIMDUT). À titre d'information.

## Unités et dimensions {#inv.items.units}

### Unité de stock {#inv.items.cStockUOM}

L'unité dans laquelle le stock est compté (UN, KG, L...). Obligatoire. Tout solde, coût et mouvement est dans cette unité.

### Unité d'achat {#inv.items.cPurchaseUOM}

L'unité dans laquelle le fournisseur vend (par exemple CS, une caisse). Elle doit avoir une conversion vers l'unité de stock, dans [Autres unités de ce produit](#inv.items.conversions) (par exemple 1 CS = 25 UN) ou dans les conversions générales. Sans conversion, l'écran affiche un avertissement et le produit ne peut pas être enregistré. Le réapprovisionnement utilise cette conversion pour proposer l'achat dans l'unité du fournisseur.

### Unité de vente {#inv.items.cSalesUOM}

L'unité dans laquelle le produit est vendu. C'est l'unité par défaut des lignes de facture et de la vérification de prix. Comme l'unité d'achat, elle doit avoir une conversion vers l'unité de stock.

### Poids {#inv.items.dWeight}

Poids d'une unité de stock. À titre d'information.

### Unité de poids {#inv.items.cWeightUOM}

kg ou lb. À titre d'information.

### Volume (m³) {#inv.items.dVolume}

Volume d'une unité de stock. À titre d'information.

### Longueur {#inv.items.dLength}

À titre d'information.

### Largeur {#inv.items.dWidth}

À titre d'information.

### Hauteur {#inv.items.dHeight}

À titre d'information.

### Unité de dimension {#inv.items.cDimUOM}

cm ou pouces, pour la longueur, la largeur et la hauteur. À titre d'information.

## Autres unités de ce produit {#inv.items.conversions}

Les emballages de ce produit, en unités de stock. C'est ici que l'on dit combien vaut l'unité d'achat ou de vente quand elle n'est pas l'unité de stock. Exemple : `1 SAC = 25` (KG). Les recettes, les factures et les mouvements peuvent alors utiliser SAC, et le système le convertit en KG.

Les conversions générales, valables pour tous les produits (1 KG = 1000 G), sont dans **Inventaire > Catégories / unités > Conversions** et s'appliquent aussi ici. L'unité de stock ne peut pas être convertie en elle-même.

### 1 unité de {#inv.items.conversions.cUOM}

L'autre unité (par exemple SAC, CS).

### Égale (unités de stock) {#inv.items.conversions.dFactor}

Combien d'unités de stock contient une unité de celle-ci. `25` sur une ligne SAC d'un produit compté en KG : 1 SAC = 25 KG.

### Notes {#inv.items.conversions.cNotes}

Texte libre, par exemple la taille de l'emballage.

## Coûts et prix {#inv.items.prices}

### Méthode de coût {#inv.items.cCostMethod}

*Coût moyen* : le stock est évalué au coût moyen des entrées. *Standard* : le coût standard est utilisé quand il existe, sinon le coût moyen.

### Coût standard {#inv.items.dStdCost}

Coût fixé par l'entreprise. Utilisé par la méthode *Standard* et par le calcul du coût des recettes.

### Coût moyen {#inv.items.dAvgCost}

Calculé par le système à partir des entrées de stock. Lecture seule.

### Dernier coût {#inv.items.dLastCost}

Coût de la dernière entrée. Lecture seule. Utilisé tant qu'il n'y a pas encore de coût moyen.

### Devise {#inv.items.cCurrency}

Devise des prix du produit. Les ventes sont en CAD seulement pour le moment. À titre d'information.

### Prix 1 (liste) {#inv.items.dPrice1}

Le prix de liste, par unité de vente. C'est le prix de la facture quand le client n'a pas de liste de prix, ou quand sa liste de prix n'a pas le produit.

### Prix 2 {#inv.items.dPrice2}

Prix de rechange (gros, revente...). À titre d'information : les prix par client se font dans les listes de prix (**Ventes > Listes de prix**). Il en va de même pour les Prix 3 à 5.

### Prix 3 {#inv.items.dPrice3}

Voir [Prix 2](#inv.items.dPrice2).

### Prix 4 {#inv.items.dPrice4}

Voir [Prix 2](#inv.items.dPrice2).

### Prix 5 {#inv.items.dPrice5}

Voir [Prix 2](#inv.items.dPrice2).

### Prix minimum {#inv.items.dMinPrice}

Le prix net le plus bas, par unité de vente. Une ligne de facture dont le prix net (après escompte) est inférieur est refusée à l'enregistrement.

### Marge % (prix 1) {#inv.items.dMarginPct}

Marge du Prix 1 sur le coût moyen. Calculée, en lecture seule, affichée une fois le produit enregistré.

## Taxes et comptabilité {#inv.items.tax}

### Groupe de taxes - ventes {#inv.items.cSalesTaxGroup}

Groupe de taxes du produit à la vente (**Administration > Taxes**). Les taxes d'une facture viennent du client et du lieu de livraison. Ce champ ne change la ligne que lorsque le groupe du produit est détaxé ou exonéré, par exemple ZERO pour les produits alimentaires de base (le pain) : la ligne n'a pas de taxe même si le client est taxé. Avec un groupe normal (QC), les taxes du client s'appliquent.

### Groupe de taxes - achats {#inv.items.cPurchaseTaxGroup}

Groupe de taxes à l'achat. À titre d'information.

### Écofrais {#inv.items.dEcoFee}

Frais environnementaux, quand ils s'appliquent. À titre d'information.

### Programme d'écofrais {#inv.items.cEcoFeeCode}

Le programme des écofrais (par exemple électronique, piles). À titre d'information.

### GL - ventes (revenus) {#inv.items.cGLSales}

Compte de ventes du produit. Sera utilisé quand la comptabilité sera reliée. À titre d'information.

### GL - achats / dépenses {#inv.items.cGLPurchase}

Compte d'achats ou de dépenses. À titre d'information.

### GL - inventaire {#inv.items.cGLInventory}

Compte d'inventaire. À titre d'information.

### GL - coût des ventes {#inv.items.cGLCOGS}

Compte du coût des marchandises vendues. À titre d'information.

### Centre de coûts {#inv.items.cCostCenter}

Centre de coûts pour la comptabilité. À titre d'information.

### Projet {#inv.items.cProject}

Projet pour la comptabilité. À titre d'information.

## Inventaire {#inv.items.inv}

Les champs de cet onglet ne sont affichés que pour les produits physiques.

### Tenu en stock {#inv.items.lStocked}

Coché : le système suit la quantité et la valeur du produit. Décoché : le produit peut être vendu ou acheté, mais il n'a pas de solde et rien ne sort du stock quand la facture est comptabilisée. Ne peut pas être décoché tant qu'il reste du stock.

### Entrepôt par défaut {#inv.items.cDefaultWarehouse}

L'entrepôt principal du produit. Le réapprovisionnement l'utilise quand il n'y a pas de paramètre par entrepôt.

### Classe ABC {#inv.items.cABCClass}

Classement A, B ou C selon l'importance (rotation ou valeur). À titre d'information.

### Durée de conservation (jours) {#inv.items.iShelfLifeDays}

Durée de conservation habituelle, en jours. À titre d'information.

### Numéros de lot {#inv.items.lLotControl}

Chaque entrée et chaque sortie demande un numéro de lot. Le solde est tenu par lot. Sur une note de crédit, la marchandise revient dans le même lot.

### Numéros de série {#inv.items.lSerialControl}

Chaque unité demande un numéro de série. Le produit se déplace une unité à la fois (par exemple le portable LAP-14I7).

### Date d'expiration {#inv.items.lExpiryControl}

Les entrées demandent une date d'expiration. Un lot expiré n'est jamais vendu, et avec *Ordre de sortie du stock* sur *Automatique* le stock sort en FEFO.

### Ordre de sortie du stock {#inv.items.cPickPolicy}

Quel stock sort en premier quand une facture est comptabilisée. *Automatique* : FEFO si le produit a une date d'expiration, sinon PEPS. *FEFO* : premier expiré, premier sorti. *PEPS* : premier entré, premier sorti. *DEPS* : dernier entré, premier sorti.

## Ventes et logistique {#inv.items.log}

### Vendable {#inv.items.lSellable}

Seul un produit coché est trouvé par la recherche de produit de la facture et de la vérification de prix. Une facture refuse un produit qui n'est pas vendable.

### Achetable {#inv.items.lPurchasable}

Seul un produit coché est proposé par **Inventaire > Réapprovisionnement**.

### BC obligatoire {#inv.items.lPORequired}

L'achat demande un bon de commande. À titre d'information.

### Matières dangereuses {#inv.items.lHazardous}

Marchandises dangereuses (TMD). À titre d'information.

### Garantie (mois) {#inv.items.iWarrantyMonths}

À titre d'information.

### Pays d'origine {#inv.items.cCountryOrigin}

Pour l'exportation et les douanes. À titre d'information.

### Code SH (tarif douanier) {#inv.items.cHSCode}

Code du tarif des douanes. À titre d'information.

### Classe de transport {#inv.items.cFreightClass}

Pour les transporteurs. À titre d'information.

### Notes {#inv.items.cNotes}

Notes libres. À titre d'information.

## Fournisseurs {#inv.items.lines}

Une ligne par fournisseur du produit. Le prix est par unité d'achat.

### Code fournisseur {#inv.items.lines.cSupplierCode}

Un fournisseur de **Comptes fournisseurs > Fournisseurs**.

### No article fournisseur {#inv.items.lines.cSupplierItem}

Le code du produit dans le catalogue du fournisseur.

### Prix {#inv.items.lines.dPurchasePrice}

Prix d'achat par unité d'achat.

### Devise {#inv.items.lines.cCurrency}

Devise du prix d'achat.

### Délai de livraison (jours) {#inv.items.lines.iLeadTimeDays}

Le délai de livraison. Le réapprovisionnement l'utilise.

### Qté min. {#inv.items.lines.dMinOrderQty}

Quantité minimale de commande. Le réapprovisionnement arrondit sa proposition jusqu'à elle.

### Préféré {#inv.items.lines.lPreferred}

Le fournisseur préféré est celui que le réapprovisionnement utilise. Si aucun n'est coché, la première ligne est utilisée.

## Stock {#inv.items.stock}

Lecture seule. Le solde par entrepôt : *En main*, *Réservé*, *Disponible*, *Point de commande* et *Valeur*, avec les totaux en main, disponible et en commande. **Mouvement** ouvre un nouveau mouvement de stock avec le produit déjà rempli. **Stock en main** ouvre la consultation complète, avec lot, numéro de série et emplacement. Affiché pour les produits tenus en stock seulement.

## Fabrication {#inv.items.mfg}

Un résumé des données de production du produit : *Fabriquer ou acheter*, *Famille de réglage*, *Lot de fabrication* (minimum, multiple et délai), *Traçabilité* et *Attributs*. **Modifier** ouvre la fiche complète dans **Production > Articles fabriqués**. Quand le produit n'a pas encore de données de production, **Ajouter les données de fabrication** les crée.

- **Fabriquer ou acheter :** *Fabriquer* (fait ici), *Acheter* (acheté) ou *Fabriquer ou acheter* (les deux). *Fantôme* est affiché à côté pour un sous-ensemble jamais stocké : ses matières vont directement dans l'ordre du produit parent.
- **Famille de réglage :** quelle ligne de la matrice de réglage s'applique quand ce produit suit un autre sur la même machine (par exemple une pâte sucrée après une pâte salée).
- **Lot de fabrication :** la plus petite quantité à fabriquer, le multiple (par exemple des fournées de 60) et le délai en jours.
- **Traçabilité :** *Aucune*, *Par lot* ou *Par numéro de série*. Pour un lot ou un numéro de série, le contrôle correspondant de l'onglet [Inventaire](#inv.items.inv) doit être coché.
- **Attributs :** caractéristiques du produit (largeur, grammage, couleur...), comparées aux limites des machines dans les recettes.

## Enregistrer et supprimer {#inv.items.rules}

- *Produit*, *Unité de stock* et *Description (français)* sont obligatoires.
- La catégorie, les unités, les groupes de taxes, l'entrepôt et les fournisseurs doivent exister.
- Les unités d'achat et de vente doivent avoir une conversion vers l'unité de stock (sur le produit ou dans les conversions générales).
- Un service devient non physique, sans classe. Un produit non physique n'a jamais de stock.
- Un produit qui a du stock ne peut plus cesser d'être *Tenu en stock*.

### Supprimer {#inv.items.delete}

Un produit utilisé dans un mouvement, une facture ou une recette ne peut pas être supprimé. Mettez plutôt son *Statut* à *Inactif* ou *Discontinué*.
