# Paramètres de réapprovisionnement {#inv.params}

Le point de commande, le minimum et le maximum d'un produit dans un entrepôt. Ils décident de ce que [Réapprovisionnement](#inv.replenishment) propose : un produit est proposé quand disponible + en commande est au point de commande ou plus bas.

**Où :** **Inventaire > Paramètres de réappro.**

## Liste {#inv.params.list}

Colonnes : Produit, Description, Entrepôt, Point de commande, Minimum, Maximum, Quantité à commander, Disponible (mis en évidence quand il est au point de commande ou plus bas) et Emplacement par défaut.

Filtre : Entrepôt. **Nouveau** crée les paramètres d'un produit dans un entrepôt.

## Général {#inv.params.general}

### Produit {#inv.params.cProduct}

Un produit tenu en stock. Obligatoire. Un produit a une ligne de paramètres par entrepôt.

### Entrepôt {#inv.params.cWarehouse}

L'entrepôt de ces paramètres. Obligatoire.

### Emplacement par défaut {#inv.params.cDefaultLocation}

L'emplacement habituel du produit dans cet entrepôt. Ce doit être un emplacement de cet entrepôt. Une réception mise en stock y range le produit quand sa ligne n'a pas d'emplacement.

### Actif {#inv.params.lActive}

Décoché : le produit n'est pas proposé dans cet entrepôt.

### Point de commande {#inv.params.dReorderPoint}

Quand disponible + en commande descend à cette quantité ou plus bas, le produit est proposé. Vide : le minimum est utilisé.

### Minimum {#inv.params.dMinQty}

Le stock le plus bas voulu. Utilisé comme point de commande quand il n'y en a pas.

### Maximum {#inv.params.dMaxQty}

La suggestion remplit le stock jusqu'à cette quantité. Il ne peut pas être plus petit que le minimum.

### Quantité à commander {#inv.params.dOrderQty}

Une quantité économique à commander chaque fois, utilisée quand il n'y a pas de maximum. La suggestion n'est jamais plus petite.

### Délai de livraison (jours) {#inv.params.iLeadTimeDays}

Le délai de livraison dans cet entrepôt, utilisé quand le fournisseur du produit n'en donne pas.

Toutes les quantités sont dans l'unité de stock du produit.
