# Lots et traçabilité {#prod.traceability}

D'où vient un lot, où il est allé, et ce qu'un rappel doit toucher. Choisissez un produit et un de ses lots : l'écran suit le lot un pas en arrière (le fournisseur et, pour un lot fabriqué ici, les lots des matières) et un pas en avant (les ordres de fabrication qui l'ont utilisé, les lots qu'ils ont fabriqués et les clients à qui ils ont été vendus), comme le demandent les règles de traçabilité des aliments (RSAC, ISO 22000). L'écran lit les mouvements de stock, les réceptions, les ordres de fabrication et les factures de vente ; la seule chose qu'il peut changer est le statut des lots (pour les retenir pendant un rappel).

**Où :** **Production > Lots et traçabilité**.

## Produit {#prod.traceability.product}

Les produits qui ont au moins un lot dans les mouvements de stock : matières reçues avec un lot et produits fabriqués avec un lot. Un produit qui n'a qu'un lot montre sa traçabilité tout de suite.

## Lot {#prod.traceability.lot}

Les lots du produit, avec leur date d'expiration et la quantité encore en main (tous les entrepôts). La traçabilité s'affiche dès qu'un lot est choisi. L'adresse de la page garde le produit et le lot : elle peut être mise en favori ou envoyée à un collègue.

## Le résumé du rappel {#prod.traceability.recall}

Les quatre chiffres du haut comptent ce qu'un rappel de ce lot doit toucher, pour le lot **et chaque lot fabriqué avec** (directement ou par plusieurs ordres) :

- **Lots touchés :** le lot lui-même et les lots fabriqués avec.
- **Clients :** les clients qui en ont encore (ce qui a été facturé moins ce qui est revenu par note de crédit).
- **Lignes de stock :** les lignes d'entrepôt et d'emplacement où il en reste en main : à bloquer.
- **Ordres ouverts :** les ordres lancés, en cours ou terminés qui utilisent ou fabriquent un de ces lots.

L'encadré jaune dit la même chose en une phrase. Un encadré vert veut dire qu'il n'y a plus rien à rappeler.

## Statut du lot et retenue d'un rappel {#prod.traceability.hold}

Sous le résumé du rappel : le statut de ce lot (**Libéré**, **En attente**, **Quarantaine**, **Rejeté**, voir [Statut des lots](#qa.lots)). La liste des lots touchés et le stock en main montrent aussi le statut de chaque lot.

Tant que certains lots touchés sont encore libérés, les rôles qui peuvent changer le statut des lots (Qualité > Statut des lots, permission **Changer le statut**) voient le bouton **Mettre en attente les n lot(s) libéré(s)** : écrivez le motif et cliquez-le. Tous les lots touchés par le rappel encore libérés sont mis en attente d'un coup (les autres gardent leur statut), pour qu'aucun ne soit vendu ni utilisé pendant la décision. Chaque changement est gardé dans l'historique de son lot.

### Motif {#prod.traceability.holdReason}

Pourquoi les lots sont retenus, ex. *rappel du lot fournisseur L-2211*. Obligatoire ; il est écrit dans l'historique de chaque lot.

## Origine (un pas en arrière) {#prod.traceability.origin}

Comment le lot est entré :

- **Reçu :** la réception qui l'a mis en stock, sa date, le **fournisseur**, le **lot fournisseur** et le bon de commande. Le lien ouvre la réception.
- **Fabriqué :** l'ordre de fabrication qui l'a déclaré, avec son statut. Dessous, chaque lot de matière que l'ordre a utilisé (quantité utilisée), suivi en arrière de la même façon, jusqu'aux fournisseurs.
- **Entré :** toute autre entrée (mouvement manuel, ajustement d'inventaire).

Seules les matières gérées par lot sont suivies : une matière sortie sans lot (par exemple une farine non suivie par lot) n'apparaît pas.

## Utilisations (un pas en avant) {#prod.traceability.uses}

Les ordres de fabrication qui ont utilisé le lot (moins ce qui a été retourné), la quantité utilisée et les lots qu'ils ont fabriqués ; chaque lot fabriqué est suivi en avant de la même façon. *Rien de déclaré encore* veut dire que l'ordre a utilisé le lot mais n'a pas encore déclaré de production.

## Clients {#prod.traceability.customers}

Les factures de vente et notes de crédit du lot et des lots fabriqués avec : client, document, date, produit, lot et quantité. Une note de crédit montre la quantité revenue en négatif.

## Stock en main {#prod.traceability.stock}

Où sont encore le lot et les lots fabriqués avec : produit, lot, expiration, entrepôt, emplacement et quantité.

## Ordres de fabrication ouverts {#prod.traceability.orders}

Affiché seulement quand il y en a : les ordres ni fermés ni annulés qui utilisent ou fabriquent un des lots touchés. À vérifier avant de continuer la production.

## Mouvements de stock {#prod.traceability.movements}

Tous les mouvements de stock du lot, du plus ancien au plus récent : numéro (le lien ouvre le mouvement), date, type, document (réception, ordre de fabrication, numéro de facture…), entrepôt, emplacement, quantité, motif et utilisateur.

## Exporter vers Excel {#prod.traceability.export}

Télécharge la traçabilité en chiffrier (.xlsx), dans la langue de l'écran, avec une feuille pour chaque partie : *Résumé*, *Origine* (une ligne par entrée, avec son niveau), *Utilisations*, *Clients*, *Stock* et *Mouvements*. C'est le fichier à envoyer à l'ACIA ou à un client lors d'un rappel, ou à garder pour un exercice de rappel simulé. Le logo de l'entreprise (**Administration > Paramètres système**) est en haut de la feuille *Résumé*.
