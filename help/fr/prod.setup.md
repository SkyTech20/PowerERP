# Paramètres de production {#prod.setup}

Les listes de référence de l'atelier : les capacités des ressources, les familles de réglage des produits, et les motifs d'arrêt et de rebut.

**Où :** **Production > Paramètres de production**, onglets **Capacités**, **Familles de réglage**, **Motifs d'arrêt** et **Motifs de rebut**.

## Capacités {#prod.setup.capabilities}

Colonnes : Code, Description et Actif. Ce qu'une ressource sait faire (par exemple `CUIRE`, `LAMINER`). Une ressource liste ses capacités (**Production > Ressources (machines)**, onglet **Capacités et attributs**), et une opération standard ou une opération de recette peut demander une capacité au lieu d'un centre de travail : alors toute ressource qui l'a peut faire l'opération. Une capacité utilisée ailleurs ne peut pas être supprimée.

### Code {#prod.setup.cCode}

Code court de la capacité. Obligatoire. Enregistré en majuscules. Il ne peut plus être changé ensuite.

### Actif {#prod.setup.lActive}

Marque une capacité qui n'est plus utilisée.

### Description (français) {#prod.setup.cDescFR}

Nom de la capacité en français. Obligatoire.

### Description (anglais) {#prod.setup.cDescEN}

Nom de la capacité en anglais.

## Familles de réglage {#prod.setup.setupfamilies}

Colonnes : Code, Description et Actif. Des produits qui demandent le même réglage de la machine (même moule, même couleur, même format). Un produit reçoit sa famille dans **Production > Articles fabriqués** ; la [Matrice de réglage](#prod.setupmatrix) donne le temps de changement d'une famille à une autre.

### Code {#prod.setup.setupfamilies.cCode}

Code court de la famille. Obligatoire. Enregistré en majuscules. Il ne peut plus être changé ensuite.

### Actif {#prod.setup.setupfamilies.lActive}

Marque une famille qui n'est plus utilisée.

### Description (français) {#prod.setup.setupfamilies.cDescFR}

Nom de la famille en français. Obligatoire.

### Description (anglais) {#prod.setup.setupfamilies.cDescEN}

Nom de la famille en anglais.

## Motifs d'arrêt {#prod.setup.downtimereasons}

Colonnes : Code, Description, Groupe, Compte dans le TRG et Actif. Filtre : Groupe. Pourquoi une machine s'est arrêtée. Utilisé dès maintenant par les arrêts planifiés des ressources, et plus tard par les arrêts déclarés à l'atelier.

### Code {#prod.setup.downtimereasons.cCode}

Code court du motif (par exemple `PAUSE`, `EP`). Obligatoire. Enregistré en majuscules. Il ne peut plus être changé ensuite.

### Groupe {#prod.setup.downtimereasons.cGroup}

*Panne*, *Réglage / changement*, *Micro-arrêt*, *Vitesse réduite*, *Manque de matière*, *Manque d'opérateur*, *Qualité*, *Arrêt planifié* ou *Autre*. Regroupe les motifs dans les rapports de temps perdu.

### Compte dans le TRG {#prod.setup.downtimereasons.lAffectsOEE}

Coché : l'arrêt est du temps perdu et fait baisser le TRG (taux de rendement global). Décoché pour les arrêts planifiés (pauses, entretien préventif).

### Actif {#prod.setup.downtimereasons.lActive}

Marque un motif qui n'est plus utilisé.

### Description (français) {#prod.setup.downtimereasons.cDescFR}

Nom du motif en français. Obligatoire.

### Description (anglais) {#prod.setup.downtimereasons.cDescEN}

Nom du motif en anglais.

## Motifs de rebut {#prod.setup.scrapreasons}

Colonnes : Code, Description, Groupe et Actif. Filtre : Groupe. Pourquoi une pièce ou une quantité a été mise au rebut, pour les rebuts déclarés à l'atelier.

### Code {#prod.setup.scrapreasons.cCode}

Code court du motif. Obligatoire. Enregistré en majuscules. Il ne peut plus être changé ensuite.

### Groupe {#prod.setup.scrapreasons.cGroup}

*Matière*, *Procédé*, *Machine*, *Opérateur*, *Démarrage* ou *Autre*. Regroupe les motifs dans les rapports de rebut.

### Actif {#prod.setup.scrapreasons.lActive}

Marque un motif qui n'est plus utilisé.

### Description (français) {#prod.setup.scrapreasons.cDescFR}

Nom du motif en français. Obligatoire.

### Description (anglais) {#prod.setup.scrapreasons.cDescEN}

Nom du motif en anglais.
