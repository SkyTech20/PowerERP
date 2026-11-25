# Sauvegardes {#admin.backups}

Des copies automatiques de toute la base de données, faites sur le serveur de l'ERP avec `pg_dump` de PostgreSQL. Pour l'administrateur seulement.

**Où :** **Administration > Sauvegardes**.

## État {#admin.backups.status}

La dernière sauvegarde (date et fichier), la prochaine, et l'erreur de la dernière tentative quand elle a échoué. **Sauvegarder maintenant** fait une sauvegarde tout de suite, peu importe la planification. Une seule sauvegarde se fait à la fois, même avec plusieurs serveurs ERP sur la même base.

## Planification {#admin.backups.settings}

**Enregistrer** vérifie et enregistre les quatre paramètres.

### Sauvegardes automatiques {#admin.backups.enabled}

Coché : une sauvegarde est faite toutes les *Toutes les (heures)*. La première est faite tout de suite quand aucune sauvegarde n'a encore été faite. Décoché : seul **Sauvegarder maintenant** fait des sauvegardes.

### Toutes les (heures) {#admin.backups.intervalHours}

Heures entre deux sauvegardes, de 1 à 720 (24 = une fois par jour). La prochaine sauvegarde se compte à partir de la dernière réussie.

### Sauvegardes conservées {#admin.backups.keep}

Combien de fichiers de sauvegarde sont gardés, de 1 à 365. Au-delà, les plus anciens fichiers de sauvegarde du dossier sont supprimés.

### Dossier des sauvegardes {#admin.backups.path}

Le dossier des fichiers de sauvegarde, sur le serveur de l'ERP (avec Docker : un dossier monté, par exemple `/app/backups`). Créé s'il n'existe pas. Obligatoire.

## Fichiers de sauvegarde {#admin.backups.files}

Les sauvegardes du dossier, les plus récentes d'abord, avec leur date et leur taille. **Télécharger** en enregistre une copie sur votre ordinateur. Chaque fichier s'appelle `powererp-AAAAMMJJ-HHMMSS.dump`.

Pour restaurer une sauvegarde, sur le serveur : `pg_restore --clean --if-exists --no-owner -d <base> <fichier>`. Cela remplace tout dans cette base : arrêtez d'abord l'ERP, et demandez de l'aide en cas de doute.
