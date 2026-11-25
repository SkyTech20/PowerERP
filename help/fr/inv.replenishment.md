# Réapprovisionnement {#inv.replenishment}

Les produits à recommander : ceux dont le stock disponible plus ce qui est déjà en commande est au point de commande ou plus bas. L'écran propose une quantité et le fournisseur préféré, et fait les bons de commande, un par fournisseur.

**Où :** **Inventaire > Réapprovisionnement**.

## Quels produits sont listés {#inv.replenishment.rule}

Un produit est listé pour un entrepôt quand :

- il a des [paramètres de réapprovisionnement](#inv.params) actifs pour cet entrepôt ;
- le produit est *Actif* et a *Achetable* coché ;
- disponible (en main − réservé) + en commande (bons de commande ouverts) est au **point de commande** ou plus bas, ou au **minimum** quand il n'y a pas de point de commande.

Les bons de commande ouverts comptent pour l'entrepôt par défaut du produit (ou son seul entrepôt avec des paramètres).

## La quantité suggérée {#inv.replenishment.suggestion}

1. Jusqu'au **maximum** des paramètres, quand il y en a un : maximum − (disponible + en commande).
2. Sinon la **quantité à commander** des paramètres.
3. Sinon de quoi revenir au minimum ou au point de commande.
4. Jamais moins que la quantité à commander, ni moins que la **Qté min.** du fournisseur préféré (produit, onglet **Fournisseurs**).
5. Arrondie à des **unités d'achat** entières : avec 1 CS = 25 UN et 60 UN nécessaires, la suggestion est 3 CS (75 UN).

## Colonnes {#inv.replenishment.columns}

- **Commander :** les lignes cochées vont dans les bons de commande. Un produit sans fournisseur ne peut pas être choisi.
- **Produit**, **Description**, **Entrepôt.**
- **Disponible**, **En commande**, **Point de commande**, **Maximum :** les chiffres du calcul, en unités de stock.
- **Suggéré :** la suggestion, en unités de stock.
- **À commander (unité d'achat) :** la quantité qui va sur le bon de commande, dans l'unité d'achat. Elle peut être changée.
- **Nom du fournisseur :** le fournisseur préféré du produit (*Préféré* dans l'onglet **Fournisseurs** du produit, sinon le premier). *Aucun fournisseur* quand le produit n'en a pas.
- **Coût / unité d'achat :** le prix du fournisseur, sinon le dernier coût (ou le coût moyen) du produit × l'unité d'achat.
- **Montant :** à commander × coût. Le total en bas est celui des lignes cochées, avant taxes.

La liste **Entrepôt** en haut montre les suggestions d'un entrepôt.

## Créer les bons de commande {#inv.replenishment.create_po}

Fait les bons de commande des lignes cochées, après une confirmation : **un bon de commande par fournisseur**. Les quantités et les prix sont convertis en unités de stock sur les lignes du bon de commande, et les taxes viennent du groupe de taxes d'achat du produit (sinon des numéros de TPS / TVQ du fournisseur). Des liens vers les nouveaux bons de commande sont affichés en haut. Les suggestions sont ensuite recalculées : les nouvelles commandes comptent maintenant comme *En commande*.

Affiché seulement pour les rôles qui ont *Créer commande* sur cet écran.
