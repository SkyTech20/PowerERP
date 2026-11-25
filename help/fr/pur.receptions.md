# Réceptions {#pur.receptions}

Les marchandises reçues sur un bon de commande. Ce qui est reçu fait baisser la quantité *en commande* des produits. Pour le moment une réception ne change pas le stock en main : saisissez aussi l'entrée dans **Inventaire > Mouvements de stock**.

**Où :** **Achats > Réceptions**.

## Liste {#pur.receptions.list}

Colonnes : No de réception, Date de réception, No de BC, Code fournisseur, Nom du fournisseur, Statut, Lignes, Total et Non facturé. Filtre : Non facturé. **Nouveau** crée une réception.

## Général {#pur.receptions.general}

### No de réception {#pur.receptions.NoReception}

Numéro de la réception, en chiffres seulement. Obligatoire, unique. Il ne peut plus être changé ensuite.

### Date de réception {#pur.receptions.DateReception}

Jour où les marchandises sont arrivées. Obligatoire. Aujourd'hui par défaut.

### No de BC {#pur.receptions.NoBonCommande}

Le bon de commande reçu. Obligatoire. Le choisir remplit le fournisseur (s'il est vide) et, quand la réception n'a pas encore de lignes, une ligne par ligne de la commande, avec la quantité reçue égale à la quantité commandée.

### Statut {#pur.receptions.Statut}

*Reçu*, *En cours* ou *Partiellement reçu*, ou un autre texte. À titre d'information.

### Code fournisseur {#pur.receptions.CodeFournisseur}

Le fournisseur. Rempli à partir du bon de commande ; ses numéros de TPS / TVQ décident des taxes.

### Nom du fournisseur {#pur.receptions.Fournisseur}

Rempli à partir du fournisseur. Vide = le nom du fournisseur à l'enregistrement.

### Entrepôt {#pur.receptions.Entrepot}

L'entrepôt qui a reçu les marchandises.

### Reçu par {#pur.receptions.ResponsableReception}

Qui a reçu les marchandises. Texte libre.

### Devise {#pur.receptions.Devise}

*CAD*, *USD* ou *EUR* : la devise des montants.

### Non facturé {#pur.receptions.lUnbilled}

Coché : la réception attend encore une facture fournisseur (coché sur une nouvelle réception). Une facture fournisseur qui la facture le décoche : une ligne de facture avec son numéro de réception, ou une facture sur son bon de commande sans numéros de réception.

### Commentaires {#pur.receptions.Commentaires}

Texte libre (dommages, boîtes manquantes...).

## Lignes {#pur.receptions.lines}

Une ligne par article reçu. Une ligne sans article ni description est retirée à l'enregistrement. Le montant d'une ligne est la quantité reçue × le coût unitaire.

### Article {#pur.receptions.lines.CodeArticle}

Code du produit reçu.

### Description {#pur.receptions.lines.Description}

Ce qui est reçu.

### Qté commandée {#pur.receptions.lines.QuantiteCommandee}

Quantité sur le bon de commande. Pour comparer.

### Qté reçue {#pur.receptions.lines.QuantiteRecue}

Quantité vraiment reçue. Elle est retirée de la quantité en commande.

### Coût unitaire {#pur.receptions.lines.PrixUnitaire}

Prix d'une unité.

### GL {#pur.receptions.lines.cGL}

Le compte du grand livre de la ligne, pour la facture fournisseur.

### CC1 {#pur.receptions.lines.cCC1}

Premier centre de coûts de la ligne.

### CC2 {#pur.receptions.lines.cCC2}

Deuxième centre de coûts de la ligne.

## Totaux {#pur.receptions.totals}

Sous-total (les lignes), transport, taxes et total, dans la devise de la réception. La TPS (5 %) et la TVQ (9,975 %) sont calculées sur le sous-total + transport lorsque le fournisseur a un numéro de TPS / TVQ.

### Transport {#pur.receptions.Transport}

Frais de livraison de la réception. Ils sont taxés avec les lignes.

### TPS {#pur.receptions.TPS}

La taxe fédérale. Calculée, lecture seule.

### TVQ {#pur.receptions.TVQ}

La taxe du Québec. Calculée, lecture seule.
