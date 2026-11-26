# Journal d'audit {#admin.audit}

Qui a fait quoi dans PowerERP, et quand : chaque connexion (réussie ou refusée), chaque compte bloqué ou débloqué, chaque changement de mot de passe, chaque appel refusé par un rôle et chaque modification des données, avec l'écran, la fiche et ce qui a été envoyé. C'est la piste d'audit demandée par ISO 27001 (8.15 journalisation), ISO 9001 (enregistrements) et la Loi 25 du Québec. Seul le rôle administrateur voit cet écran.

**Où :** **Administration > Journal d'audit**.

Le journal est conservé pour de bon : aucun écran ni appel ne peut modifier ou supprimer un événement. Les mots de passe ne sont jamais écrits (ils apparaissent comme `***`).

## Du {#admin.audit.from}

Le premier jour montré. L'écran s'ouvre sur les 7 derniers jours. Vide : depuis le premier événement.

## Au {#admin.audit.to}

Le dernier jour montré (compris). Vide : jusqu'à maintenant.

## Utilisateur {#admin.audit.user}

Les événements d'un utilisateur. *api* est un appel fait avec la clé d'API (SkyAI, scripts) ; *system* est l'ERP lui-même. Pour une connexion refusée, l'utilisateur est le nom tapé, même s'il n'existe pas.

## Type {#admin.audit.kind}

- **Sécurité :** connexions, déconnexions, blocages, déblocages, changements de mot de passe et refus.
- **Modification :** ce qui a été créé, modifié, supprimé, comptabilisé, lancé...

## Événement {#admin.audit.event}

Ce qui s'est passé. La liste montre seulement les événements présents dans le journal.

Événements de sécurité :

- **Connexion** / **Déconnexion.**
- **Connexion refusée :** mauvais mot de passe, utilisateur inconnu ou inactif (*Détails* dit lequel). Les détails ne contiennent jamais le mot de passe tapé.
- **Compte bloqué :** trop de connexions refusées de suite (5 par défaut) : le compte est refusé pendant 15 minutes, même avec le bon mot de passe.
- **Refusé : bloqué :** une connexion essayée pendant que le compte était bloqué.
- **Débloqué :** l'administrateur a débloqué le compte ([Utilisateurs](#admin.users.unlock)) ; *Détails* dit qui.
- **Mot de passe changé** / **Changement de mot de passe refusé** (dans *Mon compte*, le mot de passe actuel était faux).
- **Seconde signature** / **Seconde signature refusée** (une étape d'un ordre de production signée par un second utilisateur avec son mot de passe ; refusée : utilisateur inconnu ou mot de passe erroné).
- **Accès refusé :** l'utilisateur a appelé quelque chose que son rôle ne permet pas (un écran ou un bouton qu'il n'a pas).

Les événements de modification sont les actions des écrans : **Créer**, **Modifier**, **Supprimer**, **Comptabiliser**, **Lancer**, **Sortir**, **Terminer**, **Fermer**... Les calculs et vérifications qui ne changent rien (l'aperçu d'un ordre, la vérification d'une comptabilisation) ne sont pas gardés.

## Recherche {#admin.audit.search}

Trouve les événements dont la fiche, l'adresse ou les détails contiennent le texte : un numéro de facture, un code de produit, un client, un lot...

## Colonnes {#admin.audit.columns}

- **Quand :** date et heure, dans le fuseau horaire de cet ordinateur.
- **Utilisateur**, avec dessous l'**adresse IP** de l'ordinateur d'où vient l'appel.
- **Événement :** violet pour un événement de sécurité, bleu pour une modification, vert pour une connexion, rouge pour un refus (sur une ligne rose). Sous une connexion refusée, la raison : mauvais mot de passe, utilisateur inconnu ou inactif.
- **Écran :** l'écran auquel appartient la modification.
- **Fiche :** la fiche modifiée (numéro d'ordre, code de produit, nom d'utilisateur...).
- **Appel :** la méthode et l'adresse de l'appel, pour le soutien technique.
- **Détails :** ce qui a été envoyé avec la modification (les valeurs du formulaire), ou la raison d'une connexion refusée. Cliquez pour le voir, encore pour le masquer.

## Exporter vers Excel {#admin.audit.export}

Télécharge les événements des filtres en chiffrier (.xlsx), du plus récent au plus ancien (50 000 lignes au plus), dans la langue de l'écran. Les dates du fichier sont en UTC.

## Le blocage {#admin.audit.lockout}

Après 5 connexions refusées de suite, un compte est bloqué pendant 15 minutes ; une connexion réussie remet le compte à zéro. Les paramètres du serveur `ERP_LOCKOUT_ATTEMPTS` (0 désactive le blocage) et `ERP_LOCKOUT_MINUTES` changent ces nombres.
