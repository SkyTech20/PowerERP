# Réceptions {#pur.receptions}

Les marchandises reçues sur un bon de commande. Ce qui est reçu fait baisser la quantité *en commande* des produits. **Mettre en stock** fait ensuite entrer les marchandises en stock, avec leur lot, le lot du fournisseur, la date d'expiration et l'emplacement : c'est ce qui permet de remonter d'un lot à son fournisseur (une étape en arrière de la traçabilité des aliments, RSAC).

**Où :** **Achats > Réceptions**.

## Liste {#pur.receptions.list}

Colonnes : No de réception, Date de réception, No de BC, Code fournisseur, Nom du fournisseur, Statut, Lignes, Total, Non facturé et En stock. Filtres : Non facturé, En stock. **Nouveau** crée une réception.

## Vie d'une réception {#pur.receptions.cycle}

1. **Nouveau**, choisissez le BC : le fournisseur et les lignes sont remplis. Changez les quantités reçues, saisissez le lot du fournisseur de chaque ligne, **Enregistrer**.
2. **Vérifier** : montre où ira chaque ligne (emplacement, lot, expiration) et ce qu'il faut corriger d'abord. Rien n'est changé.
3. **Mettre en stock** : les marchandises entrent en stock. La réception affiche *En stock* et ne peut plus être modifiée ni supprimée.

Une erreur trouvée plus tard se corrige par un mouvement dans **Inventaire > Mouvements de stock** (un ajustement ou un transfert).

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

### Mise en stock le {#pur.receptions.dStockPosted}

Quand la réception a été mise en stock. Affiché une fois en stock.

### Mise en stock par {#pur.receptions.cStockPostedBy}

L'utilisateur qui a mis la réception en stock.

## Lignes {#pur.receptions.lines}

Une ligne par article reçu. Une ligne sans article ni description est retirée à l'enregistrement. Le montant d'une ligne est la quantité reçue × le coût unitaire. Les quantités sont dans l'**unité de stock** du produit (comme les lignes du BC).

Pour recevoir un article en deux lots, ajoutez une deuxième ligne avec le même article et partagez la quantité.

### Article {#pur.receptions.lines.CodeArticle}

Code du produit reçu (rempli à partir du bon de commande). Une ligne sans article (transport, un service) n'est pas mise en stock.

### Description {#pur.receptions.lines.Description}

Ce qui est reçu.

### Qté commandée {#pur.receptions.lines.QuantiteCommandee}

Quantité sur le bon de commande. Pour comparer.

### Qté reçue {#pur.receptions.lines.QuantiteRecue}

Quantité vraiment reçue, en unités de stock. Elle est retirée de la quantité en commande, et c'est la quantité qui entre en stock. 0 = rien de reçu sur cette ligne.

### Coût unitaire {#pur.receptions.lines.PrixUnitaire}

Prix d'une unité. C'est le coût du stock reçu ; il met à jour le coût moyen et le dernier coût du produit. Des montants dans une autre devise que le CAD sont pris comme des CAD (Vérifier le signale).

### Lot fournisseur {#pur.receptions.lines.cSupplierLot}

Le numéro de lot du fournisseur, tel qu'imprimé sur l'emballage ou le bon de livraison. Gardé avec le lot et affiché sur le mouvement de stock : il répond à « quel lot du fournisseur est dans notre lot? » lors d'un rappel.

### Lot {#pur.receptions.lines.cLot}

Notre numéro de lot en stock. Laissez-le vide : pour un produit suivi par lot, l'ERP donne `<réception>-<ligne>` (par exemple `900107-1`). N'en saisissez un que si vous numérotez vos lots vous-même. Les produits sans suivi par lot n'ont pas de lot.

### Expiration {#pur.receptions.lines.dExpiry}

Date d'expiration des marchandises. Laissez-la vide : pour un produit avec date d'expiration, l'ERP prend la date de réception + la durée de conservation du produit (**Inventaire > Produits**, onglet Inventaire). Obligatoire quand le produit a une date d'expiration et pas de durée de conservation.

### Emplacement {#pur.receptions.lines.cLocation}

Où les marchandises sont rangées dans l'entrepôt. Laissez-le vide : l'ERP prend l'emplacement par défaut du produit dans cet entrepôt (**Inventaire > Paramètres de réapprovisionnement**), sinon l'emplacement de réception de l'entrepôt. Quand l'emplacement par défaut contient déjà un autre lot du produit (un lot par emplacement), il prend l'emplacement de réception à la place. Un emplacement saisi est gardé tel quel.

### No de série {#pur.receptions.lines.cSerial}

Pour un produit avec numéros de série : une ligne par unité, quantité 1, avec son numéro de série.

### GL {#pur.receptions.lines.cGL}

Le compte du grand livre de la ligne, pour la facture fournisseur.

### CC1 {#pur.receptions.lines.cCC1}

Le département (centre de coûts) de la ligne, choisi dans la liste (**Grand livre > Comptes GL / Centres de coûts**, onglet **Centres de coûts**). Obligatoire quand le compte GL de la ligne a *Exige un centre de coûts*.

### CC2 {#pur.receptions.lines.cCC2}

Un sous-département du département en CC1 (la liste ne montre que les siens). Vide : le département lui-même.

## Totaux {#pur.receptions.totals}

Sous-total (les lignes), transport, taxes et total, dans la devise de la réception. La TPS (5 %) et la TVQ (9,975 %) sont calculées sur le sous-total + transport lorsque le fournisseur a un numéro de TPS / TVQ.

### Transport {#pur.receptions.Transport}

Frais de livraison de la réception. Ils sont taxés avec les lignes.

### TPS {#pur.receptions.TPS}

La taxe fédérale. Calculée, lecture seule.

### TVQ {#pur.receptions.TVQ}

La taxe du Québec. Calculée, lecture seule.

## Boutons {#pur.receptions.buttons}

### Enregistrer {#pur.receptions.save}

Enregistre la réception. Rien n'entre encore en stock.

### Vérifier {#pur.receptions.check}

Enregistre, puis montre *Ce qui entre en stock* : pour chaque ligne la quantité, l'emplacement, le lot, le lot fournisseur, l'expiration et le numéro de série qui seront utilisés, ou pourquoi la ligne est ignorée (sans article, produit non stocké, rien de reçu). Au-dessus, *Prête* ou *À corriger avant la mise en stock* avec les problèmes : par exemple un article qui n'est pas dans les produits, un numéro de série manquant, un emplacement bloqué, un emplacement qui contient déjà un autre lot. Rien n'est changé.

### Mettre en stock {#pur.receptions.post}

Demande une confirmation, vérifie de nouveau et met toutes les lignes en stock d'un coup (un mouvement de stock par ligne, document *Réception* et le numéro de la réception). Si quelque chose échoue, rien n'entre. Ensuite la réception est en lecture seule et *Mis en stock* liste ses mouvements ; cliquez sur un numéro de mouvement pour l'ouvrir. Demande le droit *Comptabiliser* de l'écran Réceptions (**Administration > Rôles**).

### Supprimer {#pur.receptions.delete}

Seulement une réception qui n'est pas encore en stock.
