# Ordres de fabrication {#prod.orders}

Un ordre de fabrication dit quoi fabriquer, combien, dans quel entrepôt et quand. Il est fait à partir d'une recette approuvée : les matières, les opérations et le coût estimé viennent de la recette, pour la quantité de l'ordre.

**Où :** **Production > Ordres de fabrication**.

## Liste {#prod.orders.list}

Colonnes : N° d'ordre, Statut, Produit, Description, Quantité, Fabriqué (quantité déclarée), Entrepôt, Début, Échéance, Révision et Coût estimé.

Filtres : Statut, Produit et Entrepôt. **Nouveau** crée un ordre en brouillon.

## Vie d'un ordre {#prod.orders.cycle}

1. **Brouillon :** créé avec **Nouveau**. Il peut être modifié ou supprimé librement. Les matières, les opérations et le coût sont recalculés après chaque changement.
2. **Lancé :** l'ordre est prêt pour l'atelier. La recette est vérifiée de nouveau (elle doit toujours être approuvée) et l'ordre ne peut plus être modifié. Voir [Lancer](#prod.orders.release).
3. **En cours :** la première matière sortie ou la première quantité déclarée à l'[atelier](#prod.orders.floor) démarre l'ordre.
4. **Terminé :** la production est finie. Voir [Terminer](#prod.orders.complete). Plus rien ne peut être sorti ni déclaré ; [Rouvrir](#prod.orders.reopen) le remet en cours.
5. **Fermé :** le [coût réel](#prod.orders.actual) est gardé et l'ordre ne peut plus changer. Voir [Fermer](#prod.orders.close).
6. **Annulé :** un ordre brouillon ou lancé qui ne sera pas fabriqué. Voir [Annuler l'ordre](#prod.orders.cancel).

Un ordre lancé revient en brouillon avec [Retour en brouillon](#prod.orders.unrelease), tant que rien n'a été sorti ni produit. Une fois que le stock a bougé, un ordre ne peut plus revenir en brouillon ni être annulé : il est terminé puis fermé. Chaque changement de statut est gardé dans l'[historique](#prod.orders.history).

Les matières manquantes sont montrées sur l'ordre ; elles avertissent, elles ne bloquent pas le lancement. Le stock ne bouge qu'à l'atelier, par des mouvements de stock de document *Production* avec le numéro de l'ordre (**Inventaire > Mouvements de stock**).

## Quoi fabriquer {#prod.orders.what}

### Produit {#prod.orders.cProduct}

Le produit à fabriquer. Obligatoire. Seuls les produits avec une recette approuvée sont listés. Un produit marqué *Acheter* dans **Production > Articles fabriqués** est refusé. Choisir un autre produit reprend sa recette et son entrepôt par défaut.

### Quantité à fabriquer {#prod.orders.dQty}

Combien fabriquer, dans l'unité de la recette (affichée à côté). Obligatoire, plus grande que zéro. Les matières et les temps de la recette sont calculés pour cette quantité.

### Unité {#prod.orders.cUOM}

Lecture seule. L'unité de la recette, dans laquelle la quantité est donnée.

### Entrepôt {#prod.orders.cWarehouse}

D'où les matières sont prises et où le produit entrera. Vide : l'entrepôt par défaut du produit (Inventaire > Articles). La disponibilité des matières est vérifiée dans cet entrepôt.

### Révision {#prod.orders.cRevision}

La version de la recette utilisée. Seules les versions approuvées sont listées (★ = celle par défaut). Vide : la recette approuvée par défaut valide à la date de début est prise, et sa révision est alors écrite ici.

### Début {#prod.orders.dStart}

Le jour où la production commence. Vide : aujourd'hui. Il décide quelle recette est valide (dates *En vigueur du / au* de la recette).

### Échéance {#prod.orders.dDue}

Le jour où le produit doit être prêt. Facultatif. Elle ne peut pas être avant le début.

### Notes {#prod.orders.cNotes}

Texte libre pour l'atelier ou le planificateur.

## Suivi {#prod.orders.tracking}

### Créé par {#prod.orders.cUser}

L'utilisateur qui a créé l'ordre. Lecture seule.

### Créé le {#prod.orders.dCreated}

Date et heure de création. Lecture seule.

### Lancé par {#prod.orders.cReleasedBy}

L'utilisateur qui a lancé l'ordre. Affiché une fois lancé.

### Lancé le {#prod.orders.dReleased}

Date et heure du lancement. Affiché une fois lancé.

### Terminé par {#prod.orders.cCompletedBy}

L'utilisateur qui a terminé l'ordre. Affiché une fois terminé.

### Terminé le {#prod.orders.dCompleted}

Date et heure de la fin.

### Fermé par {#prod.orders.cClosedBy}

L'utilisateur qui a fermé l'ordre. Affiché une fois fermé.

### Fermé le {#prod.orders.dClosed}

Date et heure de la fermeture.

### Lot fabriqué {#prod.orders.cLot}

Le lot du produit fabriqué par l'ordre (celui de la première déclaration). Affiché une fois quelque chose déclaré.

### Quantité fabriquée {#prod.orders.dQtyDone}

La quantité totale déclarée, dans l'unité de la recette.

## Matières {#prod.orders.materials}

Les matières de la recette pour la quantité de l'ordre, en unités de stock (les conversions du produit sont appliquées), avec la perte de la recette incluse.

- **Requis :** ce dont l'ordre a besoin.
- **Disponible :** stock en main moins réservé dans l'entrepôt de la matière (ou de l'ordre), sans les lots expirés.
- **Manque :** ce qui manque (requis − sorti − disponible). Un badge rouge indique un manque : recevez ou déplacez le stock avant la production. Un ✓ vert indique que la matière est là.
- **Sorti :** ce qui a déjà été sorti pour l'ordre, moins les retours (affiché une fois la production commencée). La colonne **Entrepôt** apparaît quand une matière est prise dans un autre entrepôt que celui de l'ordre.
- **Coût unitaire / Coût :** le coût de la matière dans la fiche article, pour la quantité.

## Atelier {#prod.orders.floor}

Affiché sur les ordres lancés et en cours, pour les rôles qui ont la permission *Atelier*. Chaque étape fait des mouvements de stock de l'ordre ; rien ne bouge tant qu'il reste un problème.

### 1. Sortir les matières {#prod.orders.floor.issue}

Sort les matières du stock, lot par lot, de l'entrepôt de l'ordre (ou de la matière). Les lots qui expirent en premier partent en premier (la politique de prélèvement du produit : PEPS par expiration, PEPS ou DEPS) ; un lot expiré et un emplacement bloqué ne sont jamais utilisés. **Voir les lots** liste les lots, emplacements et quantités qui seraient pris, sans rien bouger, ou ce qui manque. **Sortir** les sort.

Les matières en consommation auto (méthode *Consommation auto*) ne sont pas sorties ici : elles sortent automatiquement à la déclaration de la production.

### À sortir {#prod.orders.floor.issueQty}

La quantité de chaque matière à sortir, dans son unité de stock. Elle commence à ce qui reste à sortir (requis − sorti). Changez-la pour en sortir une partie, ou laissez 0.

### Date (sortie) {#prod.orders.floor.issueDate}

La date des mouvements de stock. Elle décide aussi quels lots sont expirés.

### 2. Déclarer la production {#prod.orders.floor.report}

Met la quantité fabriquée dans le stock de l'entrepôt de l'ordre, au coût unitaire estimé de l'ordre. Les matières en consommation auto sortent en même temps, pour cette quantité (requis × quantité déclarée / quantité de l'ordre). On peut déclarer plusieurs fois (par exemple une fois par quart).

### Quantité fabriquée {#prod.orders.floor.reportQty}

La quantité bonne fabriquée, dans l'unité de la recette. Elle commence à ce qui reste à fabriquer.

### Lot (déclaration) {#prod.orders.floor.reportLot}

Le lot du produit fabriqué. Vide : le lot de l'ordre, sinon **MO** + le numéro de l'ordre (par exemple MO12), pour un produit suivi par lot.

### Expiration (déclaration) {#prod.orders.floor.reportExpiry}

La date d'expiration du lot fabriqué. Vide : la date + la durée de conservation du produit (Inventaire > Articles), pour un produit avec date d'expiration.

### Emplacement (déclaration) {#prod.orders.floor.reportLocation}

Où le produit entre dans l'entrepôt. *Automatique* : l'emplacement par défaut du produit dans l'entrepôt (Inventaire > Paramètres de réapprovisionnement), sinon l'emplacement de réception de l'entrepôt ; l'emplacement de réception est aussi pris quand l'emplacement par défaut contient un autre lot du produit (un lot par emplacement).

### Date (déclaration) {#prod.orders.floor.reportDate}

La date des mouvements de stock ; l'expiration est comptée à partir d'elle.

## Lots fabriqués et lots utilisés {#prod.orders.lots}

La généalogie de l'ordre : les lots du produit fabriqués (date, lot, expiration, emplacement, quantité, valeur, mouvement de stock, qui) et les lots des matières utilisés (sortie, consommation auto ou retour). Un clic sur un numéro de mouvement l'ouvre dans **Inventaire > Mouvements de stock**.

### Retourner {#prod.orders.return}

Sur un lot utilisé, remet en stock une quantité qui n'a pas été consommée : elle revient dans le même lot et le même emplacement, au coût auquel elle est sortie. Au plus ce qui a été sorti de ce lot.

## Coût réel {#prod.orders.actual}

Affiché une fois que le stock a bougé : la valeur des matières sorties (moins les retours), le coût estimé des opérations pour la quantité fabriquée (la main-d'œuvre n'est pas encore déclarée), le coût réel et le coût réel par unité, le coût estimé pour la quantité fabriquée et l'**écart** (réel − estimé : rouge quand l'ordre a coûté plus). Il est gardé tel quel à la fermeture de l'ordre.

## Opérations et coût {#prod.orders.operations}

Les opérations de la recette avec le temps sur leur ressource (réglage, exécution, attente) pour la quantité, puis les totaux : temps total, coût des matières, coût des opérations, **coût estimé** et coût par unité du produit.

## Historique {#prod.orders.history}

Qui a créé l'ordre et changé son statut, quand, et le commentaire donné.

## Boutons {#prod.orders.buttons}

### Enregistrer {#prod.orders.save}

Enregistre le brouillon. L'ordre reçoit son numéro au premier enregistrement.

### Lancer {#prod.orders.release}

Enregistre le brouillon et le lance : la recette est vérifiée de nouveau (toujours approuvée) et les quantités recalculées. L'ordre est ensuite verrouillé. Demande la permission *Lancer* de l'écran.

### Retour en brouillon {#prod.orders.unrelease}

Ordres lancés seulement, tant que rien n'a été sorti ni produit. L'ordre peut de nouveau être modifié. Vous pouvez donner une raison ; elle va dans l'historique.

### Annuler l'ordre {#prod.orders.cancel}

Ordres brouillons ou lancés, tant que rien n'a été sorti ni produit. L'ordre reste dans la liste comme *Annulé*. Vous pouvez donner une raison ; elle va dans l'historique.

### Terminer {#prod.orders.complete}

Ordres en cours avec une quantité fabriquée. La production est finie : plus rien ne peut être sorti ni déclaré. Demande la permission *Lancer*.

### Rouvrir {#prod.orders.reopen}

Ordres terminés : de nouveau en cours, pour sortir ou déclarer plus. Vous pouvez donner une raison.

### Fermer {#prod.orders.close}

Ordres terminés. Garde le coût réel et l'écart ; l'ordre ne peut plus changer. Demande la permission *Lancer*.

### Supprimer {#prod.orders.delete}

Brouillons seulement. Supprime l'ordre pour de bon. Un ordre lancé est annulé à la place, pour garder son historique.
