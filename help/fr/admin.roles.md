# Rôles {#admin.roles}

Un rôle dit ce que ses utilisateurs peuvent ouvrir et faire dans PowerERP, écran par écran. Seul le rôle administrateur voit cet écran.

- Chaque utilisateur a **un rôle** (**Administration > Utilisateurs et sécurité**, champ *Rôle*).
- Le rôle donne, pour chaque écran, les **actions** permises : voir, créer, modifier, supprimer, comptabiliser, et ainsi de suite.
- Il n'y a pas d'exception par utilisateur. Pour donner un accès différent à une personne, créez un autre rôle pour elle.
- Un écran sans accès **n'est pas dans le menu**. Un bouton sans permission **n'est pas à l'écran**.
- Le serveur vérifie la permission à chaque opération : taper l'adresse d'un écran ou appeler l'API directement est refusé aussi.

**Où :** **Administration > Rôles**.

## Liste {#admin.roles.list}

| Colonne | Ce qu'elle montre |
|---|---|
| Code | Code du rôle (par exemple `SALES`). |
| Description | Description dans la langue de l'écran. |
| Utilisateurs | Combien d'utilisateurs ont ce rôle. |
| Écrans | Combien d'écrans le rôle peut ouvrir. L'administrateur affiche *Tous*. |
| Actif | Un rôle inactif n'ouvre aucun écran pour ses utilisateurs. |

**＋ Nouveau** crée un rôle. Cliquez sur une ligne pour ouvrir le rôle.

## Rôles fournis avec le système {#admin.roles.builtin}

- **ADMIN** (Administrateur) : toutes les permissions, y compris Utilisateurs et sécurité, Rôles, Sauvegardes et Paramètres système. Il ne peut être ni modifié ni supprimé, et s'ouvre en lecture seule avec l'avis *Le rôle administrateur a toutes les permissions et ne peut pas être modifié*.
- **USER** (Utilisateur) : garde l'accès que les utilisateurs ordinaires avaient avant l'arrivée des rôles : tous les écrans sauf l'approbation des recettes et les écrans d'administration.

**Rôles d'exemple de la démo :** restaurer les données de démonstration (**Administration > Paramètres système**) remet ces trois rôles comme dans l'exemple. Les rôles que vous avez créés ne sont pas touchés.

- **SALES** (Comptoir des ventes) : Clients : voir, créer et modifier. Listes de prix : voir seulement. Factures : tout (créer, modifier, supprimer un brouillon, Comptabiliser, Imprimer) sauf Note de crédit. Produits, Stock en main et Taxes : voir seulement.
- **PRODUCTION** (Planification de la production) : tous les écrans de Production, sauf approuver et supprimer les recettes. Produits, Stock en main et Catégories / unités : voir seulement.
- **WAREHOUSE** (Entrepôt et inventaires) : Mouvements de stock : voir, créer et modifier. Inventaire physique : voir, créer, modifier et Comptabiliser. Paramètres de réappro. : voir et modifier. Réceptions : voir, créer, modifier et Comptabiliser (mettre en stock). Produits, Stock en main, Réapprovisionnement et Entrepôts : voir seulement (sans Créer commande).

## Le rôle {#admin.roles.general}

En haut : **👁 Aperçu du menu**, **Annuler**, **Supprimer** et **Enregistrer**.

### Code {#admin.roles.cCode}

Code court en majuscules, avec des chiffres, `-` ou `_` (jusqu'à 30 caractères, par exemple `ACHETEUR`). Obligatoire. Il ne peut plus être changé ensuite.

### Copier d'un rôle {#admin.roles.cCopyFrom}

Nouveau rôle seulement. Le rôle commence avec les permissions du rôle choisi, et vous changez ce qui diffère avant d'enregistrer. *— partir de zéro —* commence sans aucune permission.

### Description (français) {#admin.roles.cDescFR}

Description en français. Obligatoire.

### Description (anglais) {#admin.roles.cDescEN}

Description en anglais.

### Actif {#admin.roles.lActive}

Décoché : le rôle reste, mais ses utilisateurs ne voient que le tableau de bord et leur propre compte. L'avis *Inactif : ses utilisateurs n'ouvrent aucun écran* est affiché.

## Accès {#admin.roles.access}

À gauche, les **modules** (Grand livre, Comptes fournisseurs, Achats, Ventes, Inventaire, Production, Administration), chacun avec un résumé : **Aucun accès**, **Voir**, **Modifier** ou **Complet** quand tous les écrans du module sont à ce niveau, ou **k sur n** quand le rôle ouvre k des n écrans du module, à des niveaux différents.

Cliquez sur un module pour voir ses écrans à droite. Chaque écran a **un niveau** :

| Niveau | Ce que l'utilisateur peut faire |
|---|---|
| Aucun accès | L'écran n'est pas dans le menu. |
| Voir | Ouvrir l'écran et consulter. Là où l'écran imprime, imprimer aussi. |
| Modifier | Voir, plus créer et changer des enregistrements. |
| Complet | Toutes les actions de l'écran : aussi supprimer et les actions spéciales (Comptabiliser, Note de crédit, Approuver, Créer commande). |
| Personnalisé | Un ensemble d'actions choisies une à une (voir *Personnaliser*). |

Un écran qui ne fait que montrer des données, comme *Stock en main* ou *Valeur des stocks*, n'offre que **Aucun accès** et **Voir**. *Réapprovisionnement* offre **Aucun accès**, **Voir** et **Complet**, parce que sa seule action en plus de voir est *Créer commande*.

Les écrans Utilisateurs et sécurité, Rôles, Sauvegardes et Paramètres système sont toujours réservés au rôle administrateur, et ne sont pas dans cet onglet.

### Tous les écrans {#admin.roles.setAll}

Met tous les écrans du module ouvert au même niveau d'un coup. Vous pouvez ensuite ajuster écran par écran.

### Personnaliser {#admin.roles.customize}

Ouvre les actions de l'écran une à une (*Actions sur …*). Le niveau affiche **Personnalisé** quand les actions cochées ne forment pas exactement un niveau.

- Cocher une action coche aussi **Voir** : sans voir l'écran, on ne peut rien y faire.
- Décocher **Voir** décoche toutes les actions de l'écran.

### Les actions des écrans {#admin.roles.actions}

| Action | Où | Ce qu'elle permet |
|---|---|---|
| Voir | Tous les écrans | Voir l'écran dans le menu et ouvrir ses enregistrements. |
| Créer | Fiches et documents | Le bouton **Nouveau** et les boutons qui créent un enregistrement (par exemple *Copier* une recette). |
| Modifier | Fiches et documents | Changer et enregistrer. Sans Modifier, le formulaire s'ouvre en lecture seule, sans **Enregistrer**. |
| Supprimer | Fiches et documents | Le bouton **Supprimer**. |
| Comptabiliser | Ventes > Factures, Inventaire > Inventaire physique | Comptabiliser la facture (le stock sort) ou l'inventaire (le stock est ajusté). |
| Note de crédit | Ventes > Factures | Faire la note de crédit d'une facture comptabilisée. |
| Imprimer | Ventes > Factures | Imprimer la facture et la note de crédit. |
| Approuver | Production > Recettes | Approuver, rejeter, rendre par défaut et rendre obsolète une recette. |
| Lancer | Production > Ordres de fabrication | Lancer un ordre, le remettre en brouillon et l'annuler. |
| Créer commande | Inventaire > Réapprovisionnement | Faire des bons de commande à partir des propositions de réapprovisionnement. |

## Utilisateurs {#admin.roles.users}

Les utilisateurs qui ont le rôle : Nom d'utilisateur, Nom et Actif. Pour changer le rôle de quelqu'un, utilisez **Administration > Utilisateurs et sécurité**.

## Historique {#admin.roles.history}

Chaque changement du rôle, du plus récent au plus ancien.

| Colonne | Ce qu'elle montre |
|---|---|
| Date | Date et heure du changement. |
| Utilisateur | Qui a fait le changement. |
| Changement | *Création*, *Description / statut*, *Permissions*, *Données de démo restaurées* ou *Suppression*. |
| Détails | Ce qui a changé : le rôle d'où il a été copié, l'ancienne et la nouvelle description ou Actif, ou les permissions ajoutées (+) et retirées (−), comme *Ventes › Factures : Note de crédit*. |

## Aperçu du menu {#admin.roles.preview}

Montre le menu qu'un utilisateur de ce rôle verra, avec les changements pas encore enregistrés. Servez-vous-en pour vérifier avant d'enregistrer. Tout utilisateur voit toujours le tableau de bord et son propre compte.

## Supprimer {#admin.roles.delete}

Supprime le rôle. Le système refuse quand le rôle est ADMIN, ou quand un utilisateur a le rôle : changez d'abord le rôle de ces utilisateurs, ou décochez *Actif*. La suppression reste dans l'historique.

## Ce que voit l'utilisateur {#admin.roles.effect}

| Où | Ce qui change avec le rôle |
|---|---|
| Menu | Seulement les écrans avec Voir. Un groupe du menu sans aucun écran disparaît. |
| Adresse d'un écran | Ouvrir un écran sans accès par son adresse (ou un favori) ramène au tableau de bord. Ouvrir *Nouveau* sans Créer ramène à la liste. |
| Liste | **Nouveau** seulement avec Créer. |
| Formulaire | Sans Modifier, lecture seule et pas d'**Enregistrer**. **Supprimer** seulement avec Supprimer. Comptabiliser, Note de crédit, Imprimer, Approuver et Créer commande seulement avec l'action. |
| Liens entre écrans | Un lien vers un autre écran (par exemple le produit d'une ligne de facture) ne fonctionne que si le rôle peut ouvrir cet écran. Sinon, il s'affiche comme du texte. |
| Tableau de bord | Seulement les indicateurs des écrans que le rôle peut ouvrir. Sans aucun : *Votre rôle n'affiche aucun indicateur ici : ouvrez vos écrans depuis le menu*. |
| Aide | Seulement les pages des écrans que le rôle ouvre, et seulement les boutons qu'il a. |

**Quand un changement compte :** le serveur applique le nouveau rôle tout de suite, à chaque opération. Le menu et les boutons de l'utilisateur changent quand il recharge la page ou se reconnecte.
