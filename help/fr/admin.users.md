# Utilisateurs et sécurité {#admin.users}

Les personnes qui peuvent se connecter à PowerERP, et le rôle de chacune. Le rôle décide des écrans et des boutons de l'utilisateur : voir [Rôles](#admin.roles). Seul le rôle administrateur voit cet écran.

**Où :** **Administration > Utilisateurs et sécurité**.

## Liste {#admin.users.list}

Colonnes : Nom d'utilisateur, Nom complet, Courriel, Rôle, Langue, Statut et Dernière connexion.

Filtres : Rôle et Statut. **Nouveau** crée un utilisateur.

## Général {#admin.users.general}

### Nom d'utilisateur {#admin.users.username}

Le nom tapé pour se connecter. Obligatoire, et unique (les majuscules ne comptent pas : `Marie` et `marie` sont le même utilisateur). Il ne peut plus être changé ensuite.

### Nom complet {#admin.users.name}

Le nom de la personne. Obligatoire.

### Courriel {#admin.users.email}

Courriel de la personne. À titre d'information.

### Rôle {#admin.users.role}

Le rôle de l'utilisateur : ce qu'il peut ouvrir et faire. Obligatoire. La liste ne montre que les rôles actifs. Un utilisateur a un seul rôle ; pour donner un accès différent à quelqu'un, créez un autre rôle pour cette personne dans **Administration > Rôles**.

Il doit toujours rester au moins un utilisateur actif avec le rôle administrateur : le système refuse de changer le rôle du dernier (*Il doit rester au moins un administrateur actif*).

### Langue {#admin.users.lang}

English ou Français : la langue des écrans quand cet utilisateur se connecte. Il peut quand même changer avec le bouton **EN** / **FR**.

### Actif {#admin.users.active}

Décoché : l'utilisateur ne peut plus se connecter. Le dernier administrateur actif ne peut pas être rendu inactif.

## Mot de passe {#admin.users.passwordSection}

### Nouveau mot de passe {#admin.users.password}

Au moins 6 caractères. Obligatoire pour un nouvel utilisateur. En modification, laissez vide pour garder le mot de passe actuel. Chaque utilisateur peut aussi changer son propre mot de passe dans **Mon compte**.

## Quand un changement compte {#admin.users.when}

Le serveur applique le nouveau rôle tout de suite, à chaque opération. Le menu et les boutons de l'utilisateur changent quand il recharge la page ou se reconnecte.

## Supprimer {#admin.users.delete}

Supprime l'utilisateur. Vous ne pouvez pas supprimer votre propre utilisateur, ni le dernier administrateur. Pour quelqu'un qui part, décocher *Actif* suffit et garde l'utilisateur au dossier.
