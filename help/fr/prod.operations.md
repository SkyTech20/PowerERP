# Opérations standards {#prod.operations}

Le catalogue des opérations que les recettes réutilisent : où l'opération se fait, combien de temps elle prend et combien de personnes elle demande. Une opération de recette part d'une opération standard et prend ses valeurs pour les champs laissés vides ; la recette peut ensuite les changer pour son produit.

**Où :** **Production > Opérations standards**.

## Liste {#prod.operations.list}

Colonnes : Code, Description, Où elle se fait, Temps de production, Réglage (min) et Actif. Filtres : Centre de travail et Capacité. **Nouveau** crée une opération. Une opération utilisée par une recette ne peut pas être supprimée.

## Général {#prod.operations.general}

### Code {#prod.operations.cCode}

Code court de l'opération (par exemple `PETRIR`, `CUIRE`). Obligatoire. Enregistré en majuscules. Il ne peut plus être changé ensuite.

### Actif {#prod.operations.lActive}

Marque une opération qui n'est plus utilisée.

### Description (français) {#prod.operations.cDescFR}

Nom de l'opération en français. Obligatoire.

### Description (anglais) {#prod.operations.cDescEN}

Nom de l'opération en anglais.

## Où elle se fait {#prod.operations.where}

Choisissez l'un ou l'autre : un centre de travail, ou une capacité. Avec une capacité, toute ressource qui l'a peut faire l'opération. Les deux, ou aucun, est refusé (*Choisissez un centre de travail ou une capacité, pas les deux*).

### Sous-traitée {#prod.operations.lSubcontract}

Coché : un fournisseur fait l'opération. Le centre de travail et la capacité sont cachés, et les champs du sous-traitant sont montrés. Choisir un centre de travail de type *Sous-traitant* le coche aussi.

### Centre de travail {#prod.operations.cWorkCenter}

Le centre de travail où se fait l'opération.

### Capacité {#prod.operations.cCapability}

La capacité que demande l'opération (**Production > Paramètres de production**). Toute ressource qui l'a peut faire l'opération.

### Sous-traitant {#prod.operations.cSupplier}

Le fournisseur qui fait l'opération. Obligatoire pour une opération sous-traitée.

### Coût unitaire {#prod.operations.dSubcontractCost}

Ce que le sous-traitant facture par unité fabriquée. Utilisé dans le coût prévu des recettes.

### Délai (jours) {#prod.operations.iSubcontractDays}

Les jours dont le sous-traitant a besoin.

## Temps standard {#prod.operations.time}

Copié dans les recettes, où il peut être changé par produit.

### Temps donné en {#prod.operations.cRunFormat}

Comment le temps de production se mesure : *min / unité* (6,5 minutes par pièce), *unités / heure* (1 200 unités par heure sur une ligne d'emballage) ou *min / lot* (25 minutes par fournée quelle que soit la quantité : un four, un pétrin).

### Temps de production {#prod.operations.dRunValue}

Le temps dans le format choisi ci-dessus. En *unités / heure*, il ne peut pas être 0.

### Réglage (min) {#prod.operations.dSetupMin}

Minutes pour préparer la machine, une fois par ordre. La [Matrice de réglage](#prod.setupmatrix) peut le remplacer par un temps de changement qui dépend du travail précédent.

### Équipe {#prod.operations.iCrew}

Opérateurs nécessaires. 0 = sans surveillance (par exemple la fermentation). Le temps de main-d'œuvre est le temps × l'équipe.

### Point de déclaration {#prod.operations.lReportingPoint}

Coché : l'opérateur déclare à l'atelier la quantité faite à cette opération.

## Instruction {#prod.operations.instruction}

Montrée à l'opérateur. La recette ajoute ses propres étapes.

### Instruction (français) {#prod.operations.cInstructionFR}

L'instruction en français.

### Instruction (anglais) {#prod.operations.cInstructionEN}

L'instruction en anglais.

## Temps pour une quantité {#prod.operations.calc}

Sous une opération enregistrée : le temps de réglage, de production et total d'une quantité, au standard ou sur une ressource (avec son facteur de vitesse et l'efficacité de son centre de travail), et le temps de main-d'œuvre (× équipe).

### Quantité {#prod.operations.calc.qty}

La quantité à fabriquer. 100 par défaut.

### Taille du lot {#prod.operations.calc.lot}

Pour un temps en *min / lot* seulement : la taille d'un lot. Le temps compte par lot commencé. Vide = un seul lot.

### Ressource {#prod.operations.calc.resource}

*Standard* : le temps tel qu'il est écrit. Une ressource : le temps sur elle. La liste montre les ressources qui ont la capacité, sinon les ressources du centre de travail.
