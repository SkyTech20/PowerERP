# Bons de commande {#pur.po}

Les commandes envoyées aux fournisseurs, avec leurs lignes et leurs totaux. Les réceptions se font sur eux, et les factures fournisseurs les facturent.

**Où :** **Achats > Bons de commande**.

## Liste {#pur.po.list}

Colonnes : No de BC, Date de commande, Code fournisseur, Nom du fournisseur, Nom de l'acheteur, Lignes, Total, Commande ouverte et Non facturé. Filtre : Non facturé. **Nouveau** crée un bon de commande. **Inventaire > Réapprovisionnement** peut aussi en créer à partir de sa suggestion.

## Général {#pur.po.general}

### No de BC {#pur.po.cPO}

Numéro de la commande. Obligatoire, unique. Il ne peut plus être changé ensuite.

### Date de commande {#pur.po.dCreationDate}

Date de la commande. Aujourd'hui par défaut.

### Code fournisseur {#pur.po.cSupplierCode}

Le fournisseur (**Comptes fournisseurs > Fournisseurs**). Obligatoire. Le choisir remplit le nom du fournisseur, et ses numéros de TPS / TVQ décident des taxes.

### Nom du fournisseur {#pur.po.cSupplierName}

Rempli à partir du fournisseur. Vide = le nom du fournisseur à l'enregistrement.

### Code acheteur {#pur.po.cBuyerCode}

Qui achète. Choisissez dans la liste ou tapez un code ; le choisir remplit le nom de l'acheteur.

### Nom de l'acheteur {#pur.po.cBuyerName}

Nom de l'acheteur.

### Demandeur {#pur.po.cApplicantCode}

Qui a demandé l'achat. Texte libre.

### Compagnie {#pur.po.COMPANY}

La compagnie de la commande. Lecture seule.

### Commande ouverte {#pur.po.lBlanketOrder}

Une commande ouverte pour une période, reçue et facturée en plusieurs fois.

### Non facturé {#pur.po.lUnbilled}

Coché : la commande attend encore une facture fournisseur (coché sur une nouvelle commande). Une facture fournisseur le décoche quand elle facture toutes les réceptions de la commande. La quantité *en commande* d'un produit (Stock en main, Réapprovisionnement) ne compte que les commandes non facturées, moins ce qui a été reçu.

## Lignes {#pur.po.lines}

Une ligne par article commandé. Une ligne sans article ni description est retirée à l'enregistrement. Le montant d'une ligne est la quantité × le coût unitaire.

### # {#pur.po.lines.cUnique}

Numéro de la ligne. Donné dans l'ordre.

### Article {#pur.po.lines.cProductcode}

Code du produit commandé.

### Description {#pur.po.lines.cProductDesc}

Ce qui est commandé.

### Qté {#pur.po.lines.dQuantity}

Quantité commandée, dans l'unité de stock.

### Coût unitaire {#pur.po.lines.dUnitCost}

Prix d'une unité.

## Totaux {#pur.po.totals}

Sous-total (les lignes), transport, taxes et total. La TPS (5 %) et la TVQ (9,975 %) sont calculées sur le sous-total + transport lorsque le fournisseur a un numéro de TPS / TVQ.

### Transport {#pur.po.dFreight}

Frais de livraison ajoutés à la commande. Ils sont taxés avec les lignes.

### TPS {#pur.po.dGST}

La taxe fédérale. Calculée, lecture seule.

### TVQ {#pur.po.dPST}

La taxe du Québec. Calculée, lecture seule.
