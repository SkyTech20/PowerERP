# Entrepôts et emplacements {#inv.warehouses}

Les entrepôts, et les emplacements à l'intérieur (zone > allée > rangée > niveau > case). Le stock est tenu par entrepôt, et par emplacement dans les entrepôts qui gèrent les emplacements.

**Où :** **Inventaire > Entrepôts / emplacements**, onglets **Entrepôts** et **Emplacements**.

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

L'emplacement où arrivent les marchandises. Ce doit être un emplacement de cet entrepôt. À titre d'information, prêt pour les réceptions par emplacement.

### Emplacement d'expédition {#inv.warehouses.cShippingLoc}

L'emplacement d'où partent les marchandises. Ce doit être un emplacement de cet entrepôt. À titre d'information, prêt pour l'expédition par emplacement.

## Emplacements {#inv.warehouses.locations}

Colonnes : Entrepôt, Emplacement, Zone, Allée, Rangée, Niveau, Case, Type, Description, Ordre de préparation et Bloqué. Filtres : Entrepôt, Type et Bloqué. Un emplacement qui a ou a eu du stock ne peut pas être supprimé : décochez *Actif* ou cochez *Bloqué* à la place.

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

### Plusieurs lots {#inv.warehouses.locations.lMixLots}

Décoché : l'emplacement ne contient qu'un seul lot d'un produit. Un mouvement qui fait entrer un autre lot est refusé (*Cet emplacement n'accepte qu'un seul lot*).
