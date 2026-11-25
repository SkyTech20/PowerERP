# Ordres de fabrication {#prod.orders}

Un ordre de fabrication dit quoi fabriquer, combien, dans quel entrepôt et quand. Il est fait à partir d'une recette approuvée : les matières, les opérations et le coût estimé viennent de la recette, pour la quantité de l'ordre.

**Où :** **Production > Ordres de fabrication**.

## Liste {#prod.orders.list}

Colonnes : N° d'ordre, Statut, Produit, Description, Quantité, Entrepôt, Début, Échéance, Révision et Coût estimé.

Filtres : Statut, Produit et Entrepôt. **Nouveau** crée un ordre en brouillon.

## Vie d'un ordre {#prod.orders.cycle}

1. **Brouillon :** créé avec **Nouveau**. Il peut être modifié ou supprimé librement. Les matières, les opérations et le coût sont recalculés après chaque changement.
2. **Lancé :** l'ordre est prêt pour l'atelier. La recette est vérifiée de nouveau (elle doit toujours être approuvée) et l'ordre ne peut plus être modifié. Voir [Lancer](#prod.orders.release).
3. **En cours, Terminé, Fermé :** viennent avec la prochaine étape (sortie des matières par lot et déclaration de la production avec un nouveau lot). Pas encore disponibles.
4. **Annulé :** un ordre brouillon ou lancé qui ne sera pas fabriqué. Voir [Annuler l'ordre](#prod.orders.cancel).

Un ordre lancé revient en brouillon avec [Retour en brouillon](#prod.orders.unrelease), tant que rien n'a été sorti ni produit. Chaque changement de statut est gardé dans l'[historique](#prod.orders.history).

Le stock ne bouge pas encore : les ordres de fabrication ne font que planifier. Les matières manquantes sont montrées, elles ne bloquent pas.

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

## Matières {#prod.orders.materials}

Les matières de la recette pour la quantité de l'ordre, en unités de stock (les conversions du produit sont appliquées), avec la perte de la recette incluse.

- **Requis :** ce dont l'ordre a besoin.
- **Disponible :** stock en main moins réservé dans l'entrepôt de la matière (ou de l'ordre), sans les lots expirés.
- **Manque :** ce qui manque (requis − sorti − disponible). Un badge rouge indique un manque : recevez ou déplacez le stock avant la production. Un ✓ vert indique que la matière est là.
- **Sorti :** ce qui a déjà été sorti pour l'ordre (affiché une fois la production commencée, prochaine étape). La colonne **Entrepôt** apparaît quand une matière est prise dans un autre entrepôt que celui de l'ordre.
- **Coût unitaire / Coût :** le coût de la matière dans la fiche article, pour la quantité.

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

### Supprimer {#prod.orders.delete}

Brouillons seulement. Supprime l'ordre pour de bon. Un ordre lancé est annulé à la place, pour garder son historique.
