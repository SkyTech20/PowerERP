# Stock en main {#inv.stock}

Les soldes de stock, ligne par ligne : une ligne par produit, entrepôt, emplacement, lot et numéro de série. Lecture seule : le stock ne change que par les [mouvements de stock](#inv.movements), les réceptions, les factures comptabilisées et les inventaires.

**Où :** **Inventaire > Stock en main**.

## Colonnes {#inv.stock.columns}

- **Produit** et **Description.** Cliquez sur une ligne pour ouvrir sa [fiche de stock](#inv.stock.card) (les mouvements de cette ligne). Cliquez sur le code du produit pour ouvrir le produit.
- **Entrepôt** et **Emplacement.** L'emplacement est vide dans un entrepôt qui ne gère pas les emplacements.
- **Lot**, **Numéro de série** et **Date d'expiration**, pour les produits suivis ainsi.
- **En main :** la quantité en stock, dans l'unité de stock du produit.
- **Réservé :** la partie mise de côté par des réservations (mouvement de type *Réservation*). Elle est toujours en main mais ne peut pas sortir.
- **Disponible :** en main − réservé. C'est ce qu'une facture ou une sortie peut prendre.
- **Unité :** l'unité de stock du produit.
- **Valeur :** en main × le coût du produit (moyen ou standard, selon le produit).

Seules les lignes avec une quantité sont affichées. Le filtre **Entrepôt** montre un entrepôt ; la recherche trouve un produit, un lot ou un numéro de série.


## Fiche de stock {#inv.stock.card}

Cliquez sur une ligne de **Stock en main** pour voir d'où vient sa quantité : chaque mouvement de ce produit dans cet entrepôt, cet emplacement, ce lot et ce numéro de série, du plus ancien au plus récent, avec le solde après chacun. Le dernier solde est la quantité en main de la ligne. La page est en lecture seule.

- En haut : l'entrepôt et l'emplacement, le lot, le numéro de série et la date d'expiration, puis **En main**, **Réservé** et **Disponible** aujourd'hui.
- **Ouvrir le produit** ouvre le produit. **Tracer le lot** (une ligne avec un lot) ouvre **Production > Lots et traçabilité** sur ce lot.
- Le lien **Stock en main** au-dessus du titre revient à la liste.

### Les colonnes de la fiche de stock {#inv.stock.card.columns}

- **Date :** la date du mouvement (la date du document, pas l'heure de la saisie).
- **Quoi :** ce qui s'est passé, en clair : *Réception*, *Fabriqué par un ordre de production*, *Utilisé par un ordre de production*, *Retourné d'un ordre de production*, *Facture*, *Note de crédit (retour)*, *Inventaire physique*, *Transfert depuis / vers* un autre endroit, ou le type d'un mouvement manuel (*Entrée (Manuel)*, *Sortie (Manuel)*, *Ajustement (Manuel)*...).
- **Document :** la réception, l'ordre de production, l'inventaire, la facture ou la note de crédit derrière le mouvement. Cliquez dessus pour ouvrir le document (si votre rôle peut ouvrir cet écran). Un mouvement manuel n'a pas de document.
- **Client / fournisseur / note :** la raison du mouvement : le client d'une facture, le fournisseur d'une réception, le produit fabriqué par un ordre, la description d'un inventaire, ou ce que l'utilisateur a saisi.
- **Entrée** et **Sortie :** la quantité entrée ou sortie, dans l'unité de stock du produit.
- **Solde :** la quantité dans la ligne après le mouvement. Une réservation ne le change pas : elle affiche *réservé* avec la quantité mise de côté. Une ligne rouge veut dire que le solde est passé sous zéro (possible seulement dans un entrepôt qui accepte le stock négatif, ou avec un mouvement antidaté).
- **Coût unitaire** et **Valeur :** le coût du mouvement (entrée ou sortie) et sa valeur.
- **Utilisateur :** qui a comptabilisé le mouvement.
- **Mouvement n°** (sous la date) : le numéro du mouvement de stock ; cliquez dessus pour l'ouvrir dans **Inventaire > Mouvements de stock**.

### Du {#inv.stock.card.from}

N'affiche que les mouvements à partir de cette date. Les mouvements d'avant sont additionnés dans la première ligne, **Solde d'ouverture**, pour que la colonne du solde reste juste.

### Au {#inv.stock.card.to}

N'affiche que les mouvements jusqu'à cette date. La dernière ligne est alors le solde à la fin de la période. **Toutes les dates** efface les deux dates.

## D'où vient le stock {#inv.stock.sources}

- Les **réceptions** des bons de commande, et les entrées (*Entrée*) saisies dans **Mouvements de stock**, font entrer du stock.
- Les **factures comptabilisées** le font sortir, dans l'ordre de sortie de chaque produit (FEFO, PEPS ou DEPS) ; une **note de crédit** avec *Retour* le fait revenir.
- Les **transferts** le déplacent entre entrepôts ou emplacements.
- Les **ajustements** et les **inventaires physiques** le corrigent.

Chacun d'eux est une ligne dans **Inventaire > Mouvements de stock**, qui est l'historique derrière chaque solde.
