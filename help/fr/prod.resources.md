# Ressources (machines) {#prod.resources}

La machine, la ligne, le poste ou l'équipe qui fait vraiment le travail, dans un centre de travail. Une ressource donne à l'ordonnancement son temps disponible (son calendrier moins ses arrêts planifiés), sa vitesse et combien d'ordres elle fait en même temps, et dit quelles capacités elle a.

**Où :** **Production > Ressources (machines)**, onglets **Général**, **Capacités et attributs**, **Pièces**, **Arrêts planifiés** et **Temps disponible**.

## Liste {#prod.resources.list}

Colonnes : Code, Description, Centre de travail, Capacités, Facteur de vitesse, Ordres en parallèle et Actif. Filtre : Centre de travail. **Nouveau** crée une ressource. Une ressource utilisée par une recette ne peut pas être supprimée.

## Général {#prod.resources.general}

### Code {#prod.resources.cCode}

Code court de la ressource (par exemple `FOUR-1`). Obligatoire. Enregistré en majuscules. Il ne peut plus être changé ensuite.

### Centre de travail {#prod.resources.cWorkCenter}

Le centre de travail de la ressource. Obligatoire. Un centre sous-traitant ne peut pas avoir de ressources.

### Actif {#prod.resources.lActive}

Marque une ressource qui n'est plus utilisée.

### Description (français) {#prod.resources.cDescFR}

Nom de la ressource en français. Obligatoire.

### Description (anglais) {#prod.resources.cDescEN}

Nom de la ressource en anglais.

## Capacité {#prod.resources.capacity}

L'ordonnancement planifie cette ressource avec son calendrier, sa vitesse et ses ordres en parallèle.

### Calendrier {#prod.resources.cCalendar}

Le temps de travail de la ressource. Vide = le calendrier du centre de travail.

### Facteur de vitesse {#prod.resources.dSpeedFactor}

1 = les temps standards ; 1,2 = 20 % plus vite ; 0,8 = 20 % plus lent. De 0,1 à 10. Vide = 1.

### Ordres en parallèle {#prod.resources.iParallel}

Combien d'ordres elle fait en même temps, de 1 à 100 (par exemple les plaques d'un four tunnel).

## Machine {#prod.resources.machine}

### Fabricant {#prod.resources.cManufacturer}

Le fabricant de la machine. À titre d'information.

### Modèle {#prod.resources.cModel}

Le modèle de la machine. À titre d'information.

### Numéro de série {#prod.resources.cSerialNo}

Le numéro de série de la machine. À titre d'information.

### Notes {#prod.resources.cNotes}

Texte libre.

## Capacités {#prod.resources.capabilities}

Ce que la ressource sait faire. Une opération qui demande une capacité peut se faire sur toute ressource qui l'a. Une capacité est listée une seule fois.

### Capacité {#prod.resources.capabilities.cCapability}

Une capacité de **Production > Paramètres de production**.

### Préférence {#prod.resources.capabilities.iPreference}

Classe les ressources qui ont la même capacité : 1 = la préférée. Vide = 1.

## Attributs {#prod.resources.attributes}

Les limites de la machine (largeur, nombre de couteaux, température...). Les recettes les comparent aux attributs du produit (**Production > Articles fabriqués**) et avertissent quand le produit est en dehors. Un attribut est listé une seule fois.

### Attribut {#prod.resources.attributes.cAttribute}

Nom de l'attribut, par exemple `Largeur`. Utilisez le même nom que dans les produits.

### Unité {#prod.resources.attributes.cUOM}

Unité de la valeur (par exemple `M`, `°C`).

### Min {#prod.resources.attributes.dMin}

La plus petite valeur que la machine accepte. Vide = pas de minimum.

### Max {#prod.resources.attributes.dMax}

La plus grande valeur que la machine accepte. Il ne peut pas être plus petit que le minimum. Vide = pas de maximum.

### Valeur {#prod.resources.attributes.cValue}

Une valeur texte quand l'attribut n'est pas un nombre (par exemple une couleur).

## Pièces de la machine {#prod.resources.subresources}

Pour dire à l'atelier où était un arrêt (par exemple les couteaux d'une rebobineuse).

### Code {#prod.resources.subresources.cCode}

Code court de la pièce. Enregistré en majuscules. Listé une seule fois.

### Description (français) {#prod.resources.subresources.cDescFR}

Nom de la pièce en français. Obligatoire.

### Description (anglais) {#prod.resources.subresources.cDescEN}

Nom de la pièce en anglais.

## Arrêts planifiés {#prod.resources.downtime}

Entretien préventif et arrêts planifiés. Ils sont retirés du temps disponible de la ressource.

### Du {#prod.resources.downtime.dStart}

Premier jour de l'arrêt.

### Début {#prod.resources.downtime.cStartTime}

Heure de début de l'arrêt, `HH:MM`. Vide = le début de la journée.

### Au {#prod.resources.downtime.dEnd}

Dernier jour de l'arrêt. Vide = le même jour. Il ne peut pas être avant le début.

### Fin {#prod.resources.downtime.cEndTime}

Heure de fin de l'arrêt, `HH:MM`. Vide = toute la journée de fin.

### Motif {#prod.resources.downtime.cReason}

Un motif d'arrêt de **Production > Paramètres de production**.

### Notes {#prod.resources.downtime.cNotes}

Texte libre.

## Temps disponible {#prod.resources.preview}

Les heures d'une semaine, jour par jour : le calendrier avec ses congés et exceptions, moins les arrêts planifiés, puis la capacité (× utilisation du centre de travail × ordres en parallèle).

### Semaine du {#prod.resources.week}

N'importe quel jour de la semaine à montrer ; la semaine commence le lundi.
