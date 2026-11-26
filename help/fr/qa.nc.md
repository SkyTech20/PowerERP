# Non-conformités {#qa.nc}

Une non-conformité enregistre un produit ou un lot trouvé non conforme à ses exigences : une livraison reçue abîmée ou trop chaude, une fabrication hors limites, une plainte client, un défaut trouvé à un contrôle. Elle dit ce qui a été trouvé, ce qu'on fait du produit (le traitement) et ce qu'on fait pour que cela ne se reproduise pas (l'action corrective), comme le demandent ISO 9001 (8.7 et 10.2) et ISO 22000 (8.9). Avec **Retenir le lot**, le lot est retenu dès l'enregistrement de la non-conformité ([Statut des lots](#qa.lots)).

**Où :** **Qualité > Non-conformités**.

## Liste {#qa.nc.list}

Colonnes : N°, Statut (ouverte ou fermée), Date constatée, Constatée à, Gravité, Produit, Lot, Statut du lot, Quantité (touchée), Ce qui ne va pas et Traitement.

Filtres : Statut, Constatée à, Gravité et Produit. **Nouveau** enregistre une non-conformité.

## Vie d'une non-conformité {#qa.nc.cycle}

1. **Ouverte :** elle est créée (toute personne qui a la permission Créer). Tant qu'elle est ouverte, elle peut être modifiée et complétée (la cause, la décision).
2. **Fermer :** quand la décision est prise. Le traitement (autre que *À décider*) et l'action corrective sont obligatoires. La fermeture donne au lot le statut du traitement :
   - **Utiliser tel quel :** le lot est libéré à nouveau (seulement si cette non-conformité l'avait mis en attente ; un lot retenu par autre chose garde son statut).
   - **Rebut** et **Retour au fournisseur :** le lot est rejeté : il ne sort jamais. Sortez-le du stock dans Inventaire > Mouvements de stock (rebut) ou retournez-le au fournisseur.
   - **Retouche :** le lot reste en attente jusqu'à ce qu'il soit retouché puis libéré dans Statut des lots.
3. Une non-conformité fermée se lit seulement. **Rouvrir** (avec le motif) la rouvre ; le lot garde son statut.

Une non-conformité n'est jamais effacée une fois son lot retenu : seule une non-conformité ouverte qui ne retient aucun lot peut être supprimée (une erreur).

## Ce qui a été trouvé {#qa.nc.what}

### Date constatée {#qa.nc.dDate}

Le jour où le problème a été trouvé. Aujourd'hui par défaut.

### Constatée à {#qa.nc.cSource}

Où elle a été trouvée : **Contrôle interne**, **Réception** (une livraison d'un fournisseur), **Production** (à l'atelier) ou **Plainte client**.

### Document {#qa.nc.cRef}

Le document d'origine, en texte : la réception (REC 12), l'ordre de production (ordre 7), la facture, le numéro de la plainte. La recherche de la liste le trouve.

### Gravité {#qa.nc.cSeverity}

**Mineure** (aucun risque pour le client), **Majeure** (le produit ne respecte pas ses exigences) ou **Critique** (un risque pour la santé ou la sécurité : retenez le lot et tracez-le tout de suite).

### Produit {#qa.nc.cProduct}

Le produit concerné. Laissez vide pour un problème qui ne concerne pas un produit (un procédé, un document).

### Lot {#qa.nc.cLot}

Le lot concerné, choisi parmi les lots du produit connus du stock (la liste montre leur statut, leur expiration et la quantité en stock). Demande le produit.

### Quantité touchée {#qa.nc.dQty}

La quantité concernée, dans l'unité de stock du produit (affichée dans la liste). Facultative.

### Unité {#qa.nc.cUOM}

L'unité de stock du produit, remplie à l'enregistrement de la non-conformité.

### Ce qui ne va pas {#qa.nc.cDescription}

Le problème tel qu'il a été trouvé : quoi, combien, comment il a été vu (ex. *température 9 °C à la réception, limite 4 °C*). Obligatoire.

### Retenir le lot {#qa.nc.lHoldLot}

Coché par défaut : à l'enregistrement, le lot est mis **en attente** (s'il est libéré), avec le motif *NC n : ce qui ne va pas*. Il est alors exclu des ventes et des ordres de production jusqu'à la fermeture de la non-conformité. Décochez-le pour un problème qui ne rend pas le lot dangereux.

### Statut du lot {#qa.nc.cLotStatus}

Le statut actuel du lot (libéré, en attente, quarantaine, rejeté). Pour le changer à la main, utilisez [Statut des lots](#qa.lots).

## Décision {#qa.nc.decision}

### Cause première {#qa.nc.cCause}

Pourquoi c'est arrivé (ex. *la porte de la chambre froide est restée ouverte*, *le camion du fournisseur n'était pas réfrigéré*).

### Traitement {#qa.nc.cDisposition}

Ce qu'on fait du produit : **À décider**, **Utiliser tel quel**, **Retouche**, **Rebut** ou **Retour au fournisseur**. Il décide du statut du lot à la fermeture de la non-conformité (voir la vie plus haut).

### Action corrective {#qa.nc.cAction}

Ce qui est fait pour que cela ne se reproduise pas (ex. *alarme sur la porte de la chambre froide*, *contrôle de température de chaque livraison*). Obligatoire pour fermer.

## Suivi {#qa.nc.tracking}

### Créée par {#qa.nc.cUser}

L'utilisateur qui l'a enregistrée.

### Créée le {#qa.nc.dCreated}

Quand elle a été enregistrée.

### Fermée par {#qa.nc.cClosedBy}

L'utilisateur qui l'a fermée.

### Fermée le {#qa.nc.dClosed}

Quand elle a été fermée.

## Historique {#qa.nc.history}

Chaque étape de la non-conformité, la plus récente en premier : créée, modifiée, lot mis en attente, lot libéré ou rejeté, fermée (avec le traitement), rouverte (avec le motif). Chaque changement est aussi dans le [journal d'audit](#admin.audit).

## Fermer {#qa.nc.close}

Enregistre ce qui est à l'écran et ferme la non-conformité (voir la vie plus haut). Seuls les rôles qui ont la permission **Fermer** voient le bouton.

## Rouvrir {#qa.nc.reopen}

Rouvre une non-conformité fermée ; le motif est demandé et gardé dans l'historique.
