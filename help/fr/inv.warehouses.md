# Entrepôts et emplacements {#inv.warehouses}

Les entrepôts, et les emplacements à l'intérieur (zone > allée > rangée > niveau > case). Le stock est tenu par entrepôt, et par emplacement dans les entrepôts qui gèrent les emplacements.

**Où :** **Inventaire > Entrepôts / emplacements**. Les emplacements sont un onglet dans chaque entrepôt (ouvrir l'entrepôt, onglet **Emplacements**).

## Entrepôts {#inv.warehouses.list}

Colonnes : Code, Nom, Type, Ville, Gère les emplacements et Actif. **Nouveau** crée un entrepôt. Un entrepôt utilisé par le stock ne peut pas être supprimé.

### Code {#inv.warehouses.cCode}

Code court de l'entrepôt (par exemple `ENT-01`). Obligatoire. Il ne peut plus être changé ensuite.

### Type {#inv.warehouses.cType}

*Entrepôt*, *En transit*, *Consignation*, *Quarantaine* ou *Virtuel*. À titre d'information : il aide à classer les entrepôts.

### Responsable {#inv.warehouses.cManager}

Qui dirige l'entrepôt. À titre d'information.

### Actif {#inv.warehouses.lActive}

Marque un entrepôt qui n'est plus utilisé. À titre d'information pour le moment : il est encore proposé dans les listes.

### Nom (français) {#inv.warehouses.cNameFR}

Nom de l'entrepôt en français. Obligatoire.

### Nom (anglais) {#inv.warehouses.cNameEN}

Nom de l'entrepôt en anglais.

### Adresse ligne 1 {#inv.warehouses.cAddress1}

Adresse de l'entrepôt. À titre d'information, comme les autres champs de l'adresse.

### Ville {#inv.warehouses.cCity}

Ville de l'entrepôt.

### Province / État {#inv.warehouses.cProvince}

Province de l'entrepôt.

### Code postal {#inv.warehouses.cZipCode}

Code postal de l'entrepôt.

### Pays {#inv.warehouses.cCountry}

Pays de l'entrepôt.

### Téléphone {#inv.warehouses.cPhone}

Numéro de téléphone de l'entrepôt.

### Courriel {#inv.warehouses.cEmail}

Courriel de l'entrepôt.

### Gère les emplacements {#inv.warehouses.lUseLocations}

Coché : chaque mouvement dans cet entrepôt demande l'emplacement (dès que l'entrepôt a des emplacements). Décoché : le stock est tenu par entrepôt seulement.

### Permettre le stock négatif {#inv.warehouses.lAllowNegative}

Coché : une sortie, un transfert ou un ajustement négatif peut prendre plus que le stock disponible, et le solde passe sous zéro. Décoché (le choix habituel) : c'est refusé avec *Stock disponible insuffisant*.

### Emplacement de réception {#inv.warehouses.cReceivingLoc}

L'emplacement où arrivent les marchandises. Ce doit être un emplacement de cet entrepôt. Une réception mise en stock l'utilise pour une ligne sans emplacement, quand le produit n'a pas d'emplacement par défaut ici (ou que son emplacement par défaut contient un autre lot).

### Emplacement d'expédition {#inv.warehouses.cShippingLoc}

L'emplacement d'où partent les marchandises. Ce doit être un emplacement de cet entrepôt. À titre d'information, prêt pour l'expédition par emplacement.

## Onglet Emplacements {#inv.warehouses.locationsTab}

Chaque entrepôt a un onglet **Emplacements** (à côté de **Entrepôt**) avec ses propres emplacements, dans l'ordre de préparation. Cliquez sur une ligne pour ouvrir l'emplacement ; **Retour** ou **Annuler** y ramène à cet onglet. **Nouvel emplacement** ouvre un emplacement vide déjà rattaché à cet entrepôt. Un nouvel entrepôt doit d'abord être enregistré.

### Chercher un emplacement {#inv.warehouses.locFind}

Affiché à partir de 10 emplacements : ne garde que les lignes dont le code, la zone, l'allée, la rangée, le niveau, la case ou la description contient ce qui est tapé.

## Générer des emplacements {#inv.warehouses.gen}

Crée d'un coup toute une zone de stockage : chaque allée × rangée × niveau (× case) des plages tapées. Le code est zone-allée-rangée-niveau-case, par exemple `R-A-01-1` pour la zone R, l'allée A, la rangée 01, le niveau 1. **Aperçu** montre combien d'emplacements seront créés et leurs premiers et derniers codes ; **Créer** les enregistre. Les emplacements qui existent déjà sont sautés : on peut relancer les mêmes plages après avoir ajouté une allée. 2 000 emplacements au plus d'un coup.

Exemple pour des palettiers : zone `R`, allées `A` à `C`, rangées `01` à `05`, niveaux `1` à `4` = 60 emplacements, de `R-A-01-1` à `R-C-05-4`.

### Zone {#inv.warehouses.gen.cZone}

Préfixe facultatif des codes (par exemple `R` pour les palettiers, `MP` pour les matières premières). Laissez vide si l'entrepôt n'a qu'une zone.

### Type {#inv.warehouses.gen.cType}

Le type de chaque emplacement créé (souvent *Réserve* pour les palettiers, *Préparation* pour la face de préparation).

### Plusieurs produits {#inv.warehouses.gen.lMixProducts}

Coché : plusieurs produits peuvent partager chaque emplacement créé. La règle des lots s'applique toujours (un lot par produit par emplacement).

### Allée — de {#inv.warehouses.gen.cAisleFrom}

Première allée, une lettre (`A`) ou un nombre (`1`). Obligatoire.

### Allée — à {#inv.warehouses.gen.cAisleTo}

Dernière allée (`C` donne A, B, C). Vide : seulement la première allée.

### Rangée — de {#inv.warehouses.gen.cRackFrom}

Première rangée (la colonne du palettier le long de l'allée). Avec des zéros (`01`), les codes les gardent : 01, 02 … 10.

### Rangée — à {#inv.warehouses.gen.cRackTo}

Dernière rangée. Vide : seulement la première ; les deux vides : pas de rangée dans le code.

### Niveau — de {#inv.warehouses.gen.cLevelFrom}

Premier niveau (l'étage du palettier, 1 = au sol).

### Niveau — à {#inv.warehouses.gen.cLevelTo}

Dernier niveau. Vide : seulement le premier ; les deux vides : pas de niveau dans le code.

### Case — de {#inv.warehouses.gen.cBinFrom}

Première case dans un niveau, quand les niveaux sont divisés (le plus souvent vide).

### Case — à {#inv.warehouses.gen.cBinTo}

Dernière case.

## Emplacements {#inv.warehouses.locations}

La fiche d'un emplacement (ouverte depuis l'onglet **Emplacements** de son entrepôt). Un emplacement qui a ou a eu du stock ne peut pas être supprimé : décochez *Actif* ou cochez *Bloqué* à la place.

### Entrepôt {#inv.warehouses.locations.cWarehouse}

L'entrepôt de l'emplacement. Obligatoire. Il ne peut plus être changé ensuite.

### Emplacement {#inv.warehouses.locations.cCode}

Code de l'emplacement, en majuscules. Laissé vide, il est construit à partir de zone / allée / rangée / niveau / case, par exemple `A-03-02-B`. Il ne peut plus être changé ensuite.

### Type {#inv.warehouses.locations.cType}

*Préparation*, *Réserve*, *Réception*, *Expédition*, *Quarantaine* ou *Transit / quai*. À titre d'information pour le moment.

### En main {#inv.warehouses.locations.dQtyOnHand}

La quantité dans l'emplacement, tous produits confondus. Lecture seule.

### Description {#inv.warehouses.locations.cDescription}

Texte libre (par exemple *Chambre froide*).

### Actif {#inv.warehouses.locations.lActive}

Un emplacement inactif refuse tout mouvement, comme un emplacement bloqué.

### Bloqué {#inv.warehouses.locations.lBlocked}

Rien n'entre ni ne sort (par exemple pendant un inventaire, ou une rangée endommagée). Les mouvements sont refusés avec *Cet emplacement est bloqué ou inactif*.

### Zone {#inv.warehouses.locations.cZone}

Partie de l'entrepôt (par exemple `A`, `FROID`). Construit le code quand il est laissé vide.

### Allée {#inv.warehouses.locations.cAisle}

Numéro d'allée. Construit le code.

### Rangée {#inv.warehouses.locations.cRack}

Numéro de rangée. Construit le code.

### Niveau {#inv.warehouses.locations.cLevel}

Niveau (hauteur de la tablette). Construit le code.

### Case {#inv.warehouses.locations.cBin}

Case sur le niveau. Construit le code.

### Ordre de préparation {#inv.warehouses.locations.iPickSeq}

Le parcours dans l'entrepôt : les emplacements sont listés dans cet ordre. Prêt pour les listes de préparation.

### Poids max. (kg) {#inv.warehouses.locations.dMaxWeight}

À titre d'information, prêt pour un WMS (rangement).

### Volume max. (m³) {#inv.warehouses.locations.dMaxVolume}

À titre d'information, prêt pour un WMS.

### Palettes max. {#inv.warehouses.locations.iMaxPallets}

À titre d'information, prêt pour un WMS.

### Plusieurs produits {#inv.warehouses.locations.lMixProducts}

Décoché : l'emplacement ne contient qu'un seul produit. Un mouvement qui fait entrer un autre produit est refusé (*Cet emplacement n'accepte qu'un seul produit*).

Lots : un emplacement contient toujours un seul lot d'un produit à la fois, coché ou non. Plusieurs produits peuvent partager un emplacement, chacun avec son lot, mais un deuxième lot du même produit va dans un autre emplacement jusqu'à ce que le premier soit vide (*Cet emplacement contient déjà un autre lot de ce produit*).
