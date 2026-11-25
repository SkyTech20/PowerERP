# Calendriers {#prod.calendars}

Le temps de travail de l'usine : les équipes de chaque jour de la semaine, et les congés et exceptions par date. Les centres de travail et les ressources prennent leur calendrier ici, et l'ordonnancement ne planifie le travail que pendant ses heures.

**Où :** **Production > Calendriers**, onglets **Horaires des équipes** et **Congés et exceptions**.

## Horaires des équipes {#prod.calendars.list}

Colonnes : Code, Description, Équipes, Heures par semaine et Actif. **Nouveau** crée un calendrier. Un calendrier utilisé par un centre de travail ou une ressource ne peut pas être supprimé ; supprimer un calendrier supprime aussi ses propres exceptions.

### Code {#prod.calendars.cCode}

Code court du calendrier (par exemple `JOUR`, `2EQUIPES`). Obligatoire. Enregistré en majuscules. Il ne peut plus être changé ensuite.

### Actif {#prod.calendars.lActive}

Marque un calendrier qui n'est plus utilisé.

### Description (français) {#prod.calendars.cDescFR}

Nom du calendrier en français. Obligatoire.

### Description (anglais) {#prod.calendars.cDescEN}

Nom du calendrier en anglais.

## Équipes {#prod.calendars.lines}

Une ligne par équipe et par jour. Deux équipes d'un calendrier ne peuvent pas se chevaucher, aussi par-dessus minuit et du dimanche au lundi (*Deux quarts de travail se chevauchent*).

### Jour {#prod.calendars.lines.iWeekday}

Le jour de la semaine de l'équipe, du lundi au dimanche.

### Équipe {#prod.calendars.lines.cShift}

Nom de l'équipe (par exemple `JOUR`, `NUIT`). Texte libre, montré dans le temps disponible.

### Début {#prod.calendars.lines.cStart}

Heure de début, `HH:MM`.

### Fin {#prod.calendars.lines.cEnd}

Heure de fin, `HH:MM`. Une fin avant ou à l'heure de début finit le lendemain : 22:00 à 06:00 est une équipe de nuit. L'équipe compte le jour où elle commence (l'équipe de nuit du vendredi est celle du vendredi).

### Pause (min) {#prod.calendars.lines.iBreakMin}

Minutes de pause retirées de l'équipe. Elle doit être plus courte que l'équipe.

## Temps disponible {#prod.calendars.preview}

Sous les équipes d'un calendrier enregistré : les heures disponibles chaque jour d'une semaine, avec les congés et les exceptions, et le total de la semaine.

### Semaine du {#prod.calendars.week}

N'importe quel jour de la semaine à montrer ; la semaine commence le lundi. Cette semaine par défaut.

## Congés et exceptions {#prod.calendars.calexceptions}

Colonnes : Date, Calendrier, Description et Fermé toute la journée. Filtre : Calendrier. Une exception remplace les équipes de la semaine pour sa date : fermé (un congé), ou d'autres heures (heures supplémentaires, journée courte). Une exception d'un calendrier passe avant une exception de tous les calendriers.

### Calendrier {#prod.calendars.calexceptions.cCalendar}

Le calendrier de l'exception. Vide = tous les calendriers (par exemple un congé de l'usine). Il ne peut plus être changé ensuite.

### Date {#prod.calendars.calexceptions.dDate}

Le jour de l'exception. Obligatoire. Elle ne peut plus être changée ensuite.

### Description (français) {#prod.calendars.calexceptions.cDescFR}

Ce qu'est ce jour, en français (par exemple *Fête nationale*). Obligatoire.

### Description (anglais) {#prod.calendars.calexceptions.cDescEN}

Ce qu'est ce jour, en anglais.

### Fermé toute la journée {#prod.calendars.calexceptions.lClosed}

Coché : pas de travail ce jour-là. Décoché : donnez les heures de ce jour plus bas.

### Début {#prod.calendars.calexceptions.cStart}

Heure de début de ce jour, `HH:MM`. Seulement quand le jour n'est pas fermé.

### Fin {#prod.calendars.calexceptions.cEnd}

Heure de fin de ce jour, `HH:MM`. Une fin avant ou à l'heure de début finit le lendemain.

### Pause (min) {#prod.calendars.calexceptions.iBreakMin}

Minutes de pause ce jour-là.
