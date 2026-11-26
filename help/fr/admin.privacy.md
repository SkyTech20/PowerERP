# Renseignements personnels {#admin.privacy}

Ce que PowerERP garde sur une personne, la copie à lui remettre, et comment l'anonymiser. Cet écran couvre ce que la Loi 25 du Québec (Loi sur la protection des renseignements personnels dans le secteur privé) demande au logiciel. Seul le profil administrateur voit cet écran.

**Où :** **Administration > Renseignements personnels**.

L'ERP garde des renseignements personnels sur ces personnes :

- **Utilisateur :** un utilisateur de l'ERP (Administration > Utilisateurs) : nom, courriel, nom d'utilisateur, langue, profil, dernière connexion. Le nom d'utilisateur est aussi écrit dans les documents que l'utilisateur a créés, lancés, comptabilisés ou signés, et dans le journal d'audit avec l'adresse IP.
- **Ancien utilisateur :** un nom d'utilisateur encore écrit dans les documents ou le journal d'audit, dont l'utilisateur a été supprimé.
- **Contact client :** un contact d'un client (nom, titre, téléphone, courriel).
- **Contact de livraison :** le contact d'une adresse de livraison d'un client (nom, téléphone).
- **Responsable d'entrepôt :** le responsable d'un entrepôt (nom, téléphone, courriel).

Les clients et les fournisseurs sont des entreprises : ils ne sont pas listés. Les textes libres (commentaires, notes) ne sont pas cherchés : lisez-les si une personne le demande.

## Trouver une personne {#admin.privacy.search}

Tapez au moins 2 caractères d'un nom, d'un nom d'utilisateur, d'un courriel ou d'un téléphone. La liste montre chaque personne trouvée, son type, où l'ERP la garde (le nom d'utilisateur, le client, l'entrepôt) et son statut. Cliquez **Ouvrir le dossier** pour tout voir sur la personne.

## Dossier de la personne {#admin.privacy.file}

- **Ce que l'ERP garde :** les champs gardés sur la personne.
- **Où le nom d'utilisateur est écrit :** pour un utilisateur, les documents qui le nomment (ordres de production lancés, factures comptabilisées, étapes signées...), avec le nombre de fiches et leurs numéros.
- **Journal d'audit :** les événements de l'utilisateur, et les événements dont les détails nomment la personne (par exemple la modification qui a créé un contact). Les 20 derniers sont affichés.

## Exporter vers Excel {#admin.privacy.export}

Un classeur avec tout le dossier : une feuille pour la personne, une pour les documents et une avec chaque événement du journal d'audit. C'est la copie à remettre à une personne qui demande ses renseignements (Loi 25, article 27). L'exportation est dans la langue de l'écran.

## Exporter (JSON) {#admin.privacy.exportJson}

Le même dossier en JSON, un format structuré et couramment utilisé : à remettre quand la personne demande que ses renseignements soient transmis à une autre organisation (portabilité, en vigueur depuis septembre 2024).

## Anonymiser {#admin.privacy.anonymize}

Retire la personne de l'ERP quand ses renseignements ne sont plus nécessaires (Loi 25, article 23). **C'est irréversible :** exportez d'abord le dossier si la personne l'a demandé.

- **Utilisateur :** il doit d'abord être désactivé (Administration > Utilisateurs), et vous ne pouvez pas vous anonymiser vous-même. Le nom d'utilisateur devient *anon-* suivi d'un numéro partout où il est écrit (documents, historiques, journal d'audit), le nom devient *Anonymized*, le courriel est vidé, les adresses IP de ses événements sont vidées et le mot de passe ne peut plus servir. L'utilisateur reste dans la liste des utilisateurs, inactif.
- **Ancien utilisateur :** le nom d'utilisateur est remplacé dans les documents et le journal d'audit.
- **Contact client :** le contact est retiré du client.
- **Contact de livraison** et **responsable d'entrepôt :** le nom, le téléphone et le courriel sont vidés.

Dans tous les cas, le nom, le courriel et le téléphone de la personne sont aussi remplacés dans ce que le journal d'audit a gardé des modifications. Les documents eux-mêmes (factures, ordres, lots, réceptions) restent : les règles fiscales et de salubrité alimentaire les demandent ; seul celui qui les a faits n'est plus une personne. L'anonymisation est elle-même gardée dans le journal d'audit (événement *Anonymiser*), sans le nom de la personne.

Les sauvegardes faites avant gardent les anciennes données jusqu'à leur remplacement ([Sauvegardes](#admin.backups)).

## Conservation {#admin.privacy.apply}

Les personnes gardées plus longtemps que la règle de conservation (voir **Conservation (mois)** plus bas) :

- les utilisateurs inactifs dont la dernière activité (connexion ou événement d'audit) est plus ancienne ;
- les contacts et contacts de livraison des clients inactifs sans facture depuis.

Vérifiez la liste (désactivez un client ou un utilisateur seulement quand vous n'en avez plus besoin), puis cliquez **Anonymiser les personnes** pour toutes les anonymiser d'un coup. L'ERP ne le fait pas tout seul : revenez sur cet écran au moins une fois par an.

## Politique de confidentialité {#admin.privacy.policy}

Ce que la Loi 25 demande à l'entreprise de décider et de publier. Enregistrez les champs avec **Enregistrer**.

### Responsable {#admin.privacy.cOfficerName}

La personne responsable de la protection des renseignements personnels. Par défaut, c'est la personne ayant la plus haute autorité dans l'entreprise (le président) ; la fonction peut être déléguée par écrit.

### Titre {#admin.privacy.cOfficerTitle}

Le titre du responsable. La Loi 25 demande à l'entreprise de publier le titre et les coordonnées sur son site web.

### Courriel du responsable {#admin.privacy.cOfficerEmail}

Où une personne écrit pour demander ses renseignements, les faire corriger ou porter plainte.

### Hébergé par {#admin.privacy.cHosting}

Qui héberge l'ERP et sa base de données (par exemple *Amazon Web Services* ou *serveur interne*).

### Région d'hébergement {#admin.privacy.cRegion}

Où sont les données (par exemple *ca-central-1, Montréal*). Hors du Québec, la Loi 25 (article 17) demande une évaluation des facteurs relatifs à la vie privée avant d'y transmettre les renseignements.

### Conservation (mois) {#admin.privacy.iRetentionMonths}

Combien de temps une personne est gardée après sa dernière activité : 24 mois par défaut (de 1 à 600). La liste **Conservation** l'utilise. Ne descendez pas sous ce que d'autres règles demandent : les registres de traçabilité alimentaire (RSAC) sont gardés 2 ans, et les registres fiscaux 6 ans (les documents restent, seules les personnes sont anonymisées).
