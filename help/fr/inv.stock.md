# Stock en main {#inv.stock}

Les soldes de stock, ligne par ligne : une ligne par produit, entrepôt, emplacement, lot et numéro de série. Lecture seule : le stock ne change que par les [mouvements de stock](#inv.movements), les réceptions, les factures comptabilisées et les inventaires.

**Où :** **Inventaire > Stock en main**.

## Colonnes {#inv.stock.columns}

- **Produit** et **Description.** Cliquez sur une ligne pour ouvrir le produit.
- **Entrepôt** et **Emplacement.** L'emplacement est vide dans un entrepôt qui ne gère pas les emplacements.
- **Lot**, **Numéro de série** et **Date d'expiration**, pour les produits suivis ainsi.
- **En main :** la quantité en stock, dans l'unité de stock du produit.
- **Réservé :** la partie mise de côté par des réservations (mouvement de type *Réservation*). Elle est toujours en main mais ne peut pas sortir.
- **Disponible :** en main − réservé. C'est ce qu'une facture ou une sortie peut prendre.
- **Unité :** l'unité de stock du produit.
- **Valeur :** en main × le coût du produit (moyen ou standard, selon le produit).

Seules les lignes avec une quantité sont affichées. Le filtre **Entrepôt** montre un entrepôt ; la recherche trouve un produit, un lot ou un numéro de série.

## D'où vient le stock {#inv.stock.sources}

- Les **réceptions** des bons de commande, et les entrées (*Entrée*) saisies dans **Mouvements de stock**, font entrer du stock.
- Les **factures comptabilisées** le font sortir, dans l'ordre de sortie de chaque produit (FEFO, PEPS ou DEPS) ; une **note de crédit** avec *Retour* le fait revenir.
- Les **transferts** le déplacent entre entrepôts ou emplacements.
- Les **ajustements** et les **inventaires physiques** le corrigent.

Chacun d'eux est une ligne dans **Inventaire > Mouvements de stock**, qui est l'historique derrière chaque solde.
