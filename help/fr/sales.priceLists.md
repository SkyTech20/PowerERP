# Listes de prix {#sales.priceLists}

Les prix de vos clients : par produit, unité et quantité, avec des escomptes par catégorie. Une liste de prix peut être partagée par plusieurs clients (par exemple HORECA pour les hôtels et restaurants, DIST pour les distributeurs) ou appartenir à un seul client, avec les prix négociés avec lui. Chaque client pointe vers sa liste de prix dans son champ *Liste de prix*.

**Où :** **Ventes > Listes de prix**.

## Liste {#sales.priceLists.list}

Colonnes : Code, Description, Valide du, Valide au, nombre de produits, nombre de clients et Actif. **Nouveau** crée une liste de prix.

## Général {#sales.priceLists.general}

### Code {#sales.priceLists.cCode}

Code de la liste de prix (par exemple `HORECA`, `DIST`, ou le code du client pour ses propres prix). Obligatoire. Il ne peut plus être changé ensuite.

### Valide du {#sales.priceLists.dStartDate}

Premier jour où la liste de prix compte. Vide : pas de début. Hors de ses dates, ou quand elle n'est pas active, ses clients paient le prix de liste (Prix 1 du produit).

### Valide au {#sales.priceLists.dEndDate}

Dernier jour où la liste de prix compte. Vide : pas de fin. Ne peut pas être avant *Valide du*.

### Actif {#sales.priceLists.lActive}

Décoché : la liste de prix ne compte pas, et ses clients paient le prix de liste.

### Description (français) {#sales.priceLists.cDescFR}

Nom de la liste de prix en français. Obligatoire.

### Description (anglais) {#sales.priceLists.cDescEN}

Nom de la liste de prix en anglais.

### Notes {#sales.priceLists.cNotes}

Notes internes.

### Clients {#sales.priceLists.customers}

Lecture seule. Les clients qui utilisent cette liste de prix (leur champ *Liste de prix* dans **Ventes > Clients**). Cliquez sur un client pour l'ouvrir.

## Prix {#sales.priceLists.lines}

Une ligne par produit et par palier de quantité.

### Produit {#sales.priceLists.lines.cProduct}

Un produit vendable.

### Unité {#sales.priceLists.lines.cUOM}

L'unité du prix. Vide : l'unité de vente du produit. La liste ne montre que les unités du produit. Sur une facture dans une autre unité, le prix est converti (1 CS = 12 UN).

### À partir de {#sales.priceLists.lines.dMinQty}

La quantité à partir de laquelle cette ligne compte. Parmi plusieurs lignes du même produit, celle avec la plus grande quantité *À partir de* atteinte par la quantité de la facture donne le prix. Exemple : TUBE-T8 à 15,75 de 1 à 49 et à 13,95 à partir de 50. Un produit, une unité et une quantité *À partir de* ne peuvent être que sur une ligne.

### Prix unitaire {#sales.priceLists.lines.dPrice}

Prix par unité. Obligatoire, et pas négatif.

### Escompte % {#sales.priceLists.lines.dDiscountPct}

Escompte de cette ligne. Il remplace l'escompte de la catégorie et celui du client. Mettez 0 pour un prix net, sans aucun escompte. Vide : les autres escomptes s'appliquent.

## Escomptes par catégorie {#sales.priceLists.discounts}

Un escompte sur les produits d'une catégorie, quand leur ligne de prix n'a pas son propre escompte.

### Catégorie de produits {#sales.priceLists.discounts.cCategory}

La catégorie de produits. L'escompte s'applique aussi à ses sous-catégories. Une catégorie ne peut être que sur une ligne.

### Escompte % {#sales.priceLists.discounts.dDiscountPct}

Escompte pour les produits de la catégorie. Obligatoire, entre 0 et 100. Il remplace l'*Escompte %* du client.

## Comment le prix est trouvé {#sales.priceLists.order}

1. **Prix :** la liste de prix du client, si elle est active, valide à la date de la facture et contient le produit. Sinon, le Prix 1 du produit.
2. **Escompte :** celui de la ligne de la liste de prix. Sinon, celui de la catégorie dans la liste de prix. Sinon, celui du client. Sinon, aucun.
3. **Prix net** = prix × (1 − escompte %). Sous le *Prix minimum* du produit, la facture est refusée.

L'onglet **Vérifier un prix** d'un client montre ce calcul pour un produit et la règle qui s'est appliquée.

## Supprimer {#sales.priceLists.delete}

Une liste de prix utilisée par un client ne peut pas être supprimée. Retirez-la d'abord de ces clients, ou décochez *Actif*.
