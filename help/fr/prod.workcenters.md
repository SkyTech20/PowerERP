# Centres de travail {#prod.workcenters}

Un groupe de machines, une ligne, une équipe ou un sous-traitant qui fait le même genre de travail. Les ressources appartiennent à un centre de travail, et les opérations des recettes disent sur quel centre elles se font. Le centre leur donne son calendrier, sa capacité, ses taux horaires et l'endroit de ses matières.

**Où :** **Production > Centres de travail**.

## Liste {#prod.workcenters.list}

Colonnes : Code, Description, Type, Calendrier, Capacité finie, Taux de production / h et Actif. Filtres : Type et Calendrier. **Nouveau** crée un centre de travail. Un centre utilisé par une ressource ou une recette ne peut pas être supprimé.

## Général {#prod.workcenters.general}

### Code {#prod.workcenters.cCode}

Code court du centre (par exemple `FOUR`, `EMBAL`). Obligatoire. Enregistré en majuscules. Il ne peut plus être changé ensuite.

### Type {#prod.workcenters.cType}

*Machines*, *Ligne*, *Main-d'œuvre* ou *Sous-traitant*. Un centre *Main-d'œuvre* coûte par personne : ses taux sont multipliés par l'équipe de l'opération. Un centre *Sous-traitant* est un fournisseur qui fait le travail : il n'a pas besoin de calendrier, n'a pas de ressources à lui et sa capacité n'est jamais finie.

### Actif {#prod.workcenters.lActive}

Marque un centre qui n'est plus utilisé.

### Description (français) {#prod.workcenters.cDescFR}

Nom du centre en français. Obligatoire.

### Description (anglais) {#prod.workcenters.cDescEN}

Nom du centre en anglais.

### Sous-traitant {#prod.workcenters.cSupplier}

Le fournisseur qui fait le travail (**Comptes fournisseurs > Fournisseurs**). Montré et obligatoire pour le type *Sous-traitant* seulement.

## Capacité {#prod.workcenters.capacity}

Ce que l'ordonnancement utilise : quand le centre travaille et combien il peut prendre.

### Calendrier {#prod.workcenters.cCalendar}

Le temps de travail du centre ([Calendriers](#prod.calendars)). Obligatoire, sauf pour un sous-traitant. Ses ressources l'utilisent, sauf si elles ont le leur.

### Capacité finie {#prod.workcenters.lFinite}

Coché : l'ordonnancement ne charge jamais plus que le temps du calendrier. Décoché : pas de limite (par exemple une équipe qui peut grandir).

### Efficacité % {#prod.workcenters.dEfficiencyPct}

Production réelle par rapport aux temps standards, de 1 à 500. 90 = le travail prend 10 % de plus que les temps standards. Vide = 100.

### Utilisation % {#prod.workcenters.dUtilizationPct}

Part du temps du calendrier vraiment disponible (micro-arrêts, réunions...), de 1 à 100. Capacité = temps du calendrier × utilisation. Vide = 100.

### File d'attente (min) {#prod.workcenters.iQueueMin}

Attente habituelle avant qu'une opération commence ici.

### Déplacement (min) {#prod.workcenters.iMoveMin}

Temps pour amener les pièces à l'opération suivante.

## Taux horaires {#prod.workcenters.costs}

Pour le coût prévu des recettes (onglet **Quantité et coût**) et, plus tard, le coût réel des ordres de fabrication.

### Taux de réglage / h {#prod.workcenters.dSetupRateHr}

Coût d'une heure de réglage.

### Taux de production / h {#prod.workcenters.dRunRateHr}

Coût d'une heure de production.

### Frais indirects / h {#prod.workcenters.dBurdenRateHr}

Frais ajoutés à chaque heure de production (bâtiment, énergie...).

### Centre de coûts {#prod.workcenters.cCostCenter}

Le centre de coûts du centre de travail, pour la comptabilité à venir.

## Stock {#prod.workcenters.stock}

Où les matières sont préparées pour ce centre et où sa production est déposée.

### Entrepôt {#prod.workcenters.cWarehouse}

L'entrepôt du centre. Obligatoire quand un emplacement est donné.

### Emplacement d'approvisionnement {#prod.workcenters.cInLocation}

Où les matières attendent le centre. Ce doit être un emplacement de l'entrepôt ci-dessus.

### Emplacement de sortie {#prod.workcenters.cOutLocation}

Où le centre dépose ce qu'il fabrique. Ce doit être un emplacement de l'entrepôt ci-dessus.

## Notes {#prod.workcenters.notes}

### Notes {#prod.workcenters.cNotes}

Texte libre.

## Ressources et temps disponible {#prod.workcenters.preview}

Sous un centre enregistré : ses ressources (**＋ Nouvelle ressource** en crée une dans ce centre), et son temps disponible pour une semaine, avec la capacité après l'utilisation.

### Semaine du {#prod.workcenters.week}

N'importe quel jour de la semaine à montrer ; la semaine commence le lundi.
