# Mouvements de stock {#inv.movements}

Chaque changement du stock : entrées, sorties, transferts, ajustements, inventaires et réservations. Un mouvement est reporté à l'enregistrement et ne peut plus être modifié ni supprimé : une erreur se corrige par un autre mouvement (par exemple un ajustement dans l'autre sens).

**Où :** **Inventaire > Mouvements de stock**. Les mouvements faits par les autres écrans (réceptions, factures, inventaires, production) sont aussi listés ici, avec leur document.

## Liste {#inv.movements.list}

Colonnes : #, Date, Type, Produit, Description, Entrepôt / emplacement (avec → pour un transfert), Lot / série, Quantité, Valeur, Document et Utilisateur. Les plus récents d'abord.

Filtres : Type et Entrepôt. **Nouveau** crée un mouvement.

## Types de mouvement {#inv.movements.types}

| Type | Ce qu'il fait | Quantité |
|---|---|---|
| Entrée | Du stock entre (hors réception d'un bon de commande). | Positive. |
| Sortie | Du stock sort (consommation, échantillon, perte). | Positive : la quantité qui sort. |
| Transfert | Du stock passe d'un entrepôt / emplacement à un autre. | Positive. |
| Ajustement | Corrige le stock. | Positive ajoute, négative retire. |
| Inventaire | L'écart trouvé par un inventaire physique (fait d'habitude par **Inventaire physique** au report). | Positive ou négative. |
| Réservation | Met du stock de côté : il reste en main mais n'est plus disponible. | Positive réserve, négative libère. |

## Général {#inv.movements.general}

### Type {#inv.movements.cType}

Le genre de mouvement : voir [Types de mouvement](#inv.movements.types). *Transfert* affiche les champs de destination.

### Date {#inv.movements.dDate}

Date du mouvement. Obligatoire. Aujourd'hui par défaut.

### Produit {#inv.movements.cProduct}

Le produit qui bouge. Seuls les produits tenus en stock peuvent être choisis : un produit avec *Tenu en stock* décoché n'a pas de stock.

### Description {#inv.movements.cDescFR}

Description du produit. Lecture seule.

### Quantité {#inv.movements.dQty}

Dans l'unité de stock du produit. Obligatoire, pas zéro. Les entrées, sorties et transferts prennent une quantité positive. Les ajustements et réservations prennent une quantité négative pour retirer ou pour libérer. Un produit avec numéros de série se déplace une unité à la fois.

Une sortie, un transfert ou un ajustement négatif ne peut pas prendre plus que le stock disponible (en main − réservé), sauf si l'entrepôt permet le stock négatif.

### Coût unitaire {#inv.movements.dUnitCost}

Coût d'une unité de stock du stock qui entre. Vide : le coût moyen du produit. Affiché pour les mouvements qui font entrer du stock. Il change le coût moyen du produit.

### Valeur {#inv.movements.dValue}

Quantité × coût du mouvement. Lecture seule, affichée une fois reporté.

### Coût moyen après {#inv.movements.dAvgCostAfter}

Le coût moyen du produit après ce mouvement. Lecture seule, affiché une fois reporté.

## Entrepôt et emplacement {#inv.movements.place}

### Entrepôt {#inv.movements.cWarehouse}

L'entrepôt du stock (l'origine, pour un transfert). Obligatoire.

### Emplacement {#inv.movements.cLocation}

L'emplacement dans l'entrepôt. Obligatoire dans un entrepôt qui gère les emplacements. Un emplacement bloqué ou inactif est refusé. Un emplacement qui n'accepte pas plusieurs produits en refuse un deuxième. Un emplacement ne contient qu'un seul lot d'un produit : un autre lot du même produit est refusé.

### Vers l'entrepôt {#inv.movements.cWhTo}

Transferts seulement : l'entrepôt où va le stock. Obligatoire.

### Vers l'emplacement {#inv.movements.cLocTo}

Transferts seulement : l'emplacement où va le stock. La destination ne peut pas être la même que l'origine.

## Traçabilité {#inv.movements.tracking}

### Lot {#inv.movements.cLot}

Obligatoire quand le produit a *Numéros de lot* coché. Le solde est tenu par lot. Un emplacement contient un seul lot d'un produit à la fois : une entrée, un transfert ou un inventaire qui fait entrer un deuxième lot du produit dans un emplacement qui a encore le premier est refusé ; utilisez un autre emplacement.

### Numéro de série {#inv.movements.cSerial}

Obligatoire quand le produit a *Numéros de série* coché. Un numéro de série ne peut être en stock qu'une seule fois.

### Date d'expiration {#inv.movements.dExpiry}

Obligatoire sur une entrée quand le produit a *Date d'expiration* coché. Un lot expiré n'est jamais vendu.

## Référence {#inv.movements.reference}

### Type de document {#inv.movements.cDocType}

D'où vient le mouvement : *Manuel* (saisi ici), *BC*, *Réception*, *Facture*, *Commande client*, *Inventaire* ou *Production*. Les autres écrans le remplissent.

### Numéro de document {#inv.movements.cDocNo}

Le numéro de ce document (par exemple le numéro de facture, ou SO NC-3 pour une note de crédit).

### Raison {#inv.movements.cReason}

Pourquoi le mouvement a été fait (par exemple *Bris*, *Échantillon*).

### Commentaires {#inv.movements.cComment}

Texte libre.

## Messages d'erreur fréquents {#inv.movements.errors}

| Message | Cause |
|---|---|
| Stock disponible insuffisant | L'entrepôt / emplacement / lot n'a pas la quantité disponible (le stock réservé ne compte pas). |
| Quantité réservée insuffisante | Libérer plus que ce qui est réservé. |
| Ce produit n'est pas tenu en stock | Le produit a *Tenu en stock* décoché. |
| Cet emplacement est bloqué ou inactif | Rien n'entre ni ne sort d'un emplacement bloqué. |
| Un numéro de lot est obligatoire pour ce produit | Le produit a *Numéros de lot* coché. |
| Un produit avec numéros de série se déplace une unité à la fois | Quantité autre que 1 pour un produit avec numéros de série. |
| Cet emplacement n'accepte qu'un seul produit | L'emplacement a *Plusieurs produits* décoché. |
| Cet emplacement contient déjà un autre lot de ce produit | L'emplacement a encore du stock d'un autre lot du produit (indiqué entre parenthèses). Un seul lot par produit et par emplacement. |
| La destination est la même que l'origine | Un transfert vers le même entrepôt et le même emplacement. |
