# Statut des lots {#qa.lots}

Les lots qui peuvent être vendus et utilisés, et ceux qui sont retenus jusqu'à une décision. Un lot qui peut être dangereux ou hors spécification (rappel du fournisseur, résultat de labo attendu, livraison abîmée) est mis en attente ici, pour que personne ne le vende ou ne l'utilise en production par erreur. C'est la maîtrise des produits non conformes demandée par ISO 9001 (8.7), ISO 22000 et le Règlement sur la salubrité des aliments au Canada.

**Où :** **Qualité > Statut des lots**.

## Les quatre statuts {#qa.lots.statuses}

- **Libéré :** le lot peut être vendu et utilisé. Un lot jamais changé est libéré.
- **En attente :** en attente d'une décision (un contrôle, un résultat, une non-conformité encore ouverte).
- **Quarantaine :** mis à part jusqu'au contrôle (souvent déplacé vers un emplacement de quarantaine).
- **Rejeté :** il ne sort jamais vers un client ni vers la production : il est à mettre au rebut ou à retourner au fournisseur.

Un lot non libéré est **exclu des factures de vente et des ordres de production** : la comptabilisation d'une facture ou la sortie des matières d'un ordre prend le lot libéré suivant (dans l'ordre de la politique de prélèvement), et dit *Pas assez de stock libéré* quand il ne reste que des lots retenus. La quantité disponible affichée sur les ordres de production ne le compte pas non plus. Il peut quand même être déplacé, ajusté ou compté dans **Inventaire > Mouvements de stock** (vers un emplacement de quarantaine, sortie au rebut).

## Les chiffres du haut {#qa.lots.kpis}

Le nombre de lots en attente, en quarantaine, rejetés et libérés. Cliquez un chiffre pour ne voir que ces lots ; cliquez-le encore pour tout revoir.

## Statut {#qa.lots.status}

Affiche un statut, ou **Non libérés** (en attente, quarantaine et rejetés ensemble). Les lots qui demandent une décision viennent en premier.

## Produit {#qa.lots.product}

Les lots d'un produit.

## Recherche {#qa.lots.search}

Trouve les lots dont le produit, la description, le lot, le motif ou l'emplacement contient le texte.

## Colonnes {#qa.lots.columns}

- **Produit** et sa description.
- **Lot**, avec sa date d'expiration dessous.
- **En stock :** la quantité en stock, dans l'unité de stock, tous entrepôts ensemble, avec dessous les entrepôts et emplacements qui en ont.
- **Statut** (un lot retenu est sur une ligne jaune).
- **Motif** du dernier changement, avec l'utilisateur, la date et la non-conformité qui l'a fait (un lien).

La liste montre les lots en stock, et les lots non libérés même quand il n'en reste rien.

## Changer le statut {#qa.lots.change}

Ouvre le changement sous le lot. Choisissez le nouveau statut, écrivez le motif et cliquez **Enregistrer** (ou Entrée). Le motif est obligatoire : il est gardé dans l'historique, avec votre nom et l'heure. Une non-conformité peut faire la même chose pour son lot ([Non-conformités](#qa.nc)).

Seuls les rôles qui ont la permission **Changer** de cet écran voient le bouton (Administration > Rôles).

## Nouveau statut {#qa.lots.newStatus}

Le statut que prend le lot : les statuts autres que l'actuel.

## Motif {#qa.lots.reason}

Pourquoi le statut change, ex. *rappel fournisseur 2026-114*, *résultat de labo attendu*, *contrôlé : conforme*. Il s'affiche dans la liste et dans l'historique.

## Historique {#qa.lots.history}

Chaque changement de statut du lot, le plus récent en premier : quand, qui, de quel statut à quel statut, et pourquoi. L'historique n'est jamais modifié ni effacé.

## Tracer {#qa.lots.trace}

Ouvre le lot dans **Production > Lots et traçabilité** : d'où il vient, où il est allé, et le bouton qui retient tous les lots touchés par un rappel.
