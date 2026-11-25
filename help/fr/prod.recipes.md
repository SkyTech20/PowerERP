# Recettes {#prod.recipes}

Comment chaque produit est fabriqué, pour une quantité de base : ses matières, ses opérations (où, combien de temps), le pas à pas que suit l'opérateur, et les coproduits fabriqués avec lui. Une recette est une version (révision A, B, C...) d'un produit, approuvée avant d'être utilisée.

**Où :** **Production > Recettes**, onglets **Général**, **Opérations**, **Matières**, **Étapes**, **Coproduits et sous-produits**, **Quantité et coût**, **Vue opérateur** et **Versions et historique**.

## Liste {#prod.recipes.list}

Colonnes : Produit, Révision, Description, Type de procédé, Quantité de base, Matières, Opérations, Étapes et Statut (★ = la version par défaut du produit). Filtres : Statut et Type de procédé. **Nouveau** crée une recette.

## Vie d'une recette {#prod.recipes.cycle}

1. **Brouillon :** la recette est écrite et peut être changée ou supprimée.
2. **Soumettre pour révision :** la version est figée pendant qu'elle est révisée.
3. **Approuver** ou **Renvoyer :** approuver en fait la version par défaut du produit, celle que prennent les nouveaux ordres de fabrication ; renvoyer la remet en brouillon avec un commentaire qui dit quoi changer.
4. **Rendre obsolète :** les nouveaux ordres ne l'utilisent plus.

Seul un brouillon peut être changé. Pour changer une version approuvée, faites une **Nouvelle version à partir de celle-ci** : elle commence en brouillon avec la lettre de révision suivante. Approuver, renvoyer, mettre par défaut et rendre obsolète demandent la permission **Approuver** des Recettes (**Administration > Rôles**), et la recette doit avoir au moins une opération. Chaque changement de statut est gardé dans **Versions et historique**.

## Général {#prod.recipes.general}

### Produit {#prod.recipes.cProduct}

Le produit fabriqué. Obligatoire. Ce doit être un produit fabriqué dans **Production > Articles fabriqués** (*Fabriquer*, ou *Fabriquer ou acheter*). Il ne peut plus être changé ensuite.

### Révision {#prod.recipes.cRevision}

La version : A, B, C... Enregistrée en majuscules. Obligatoire. Elle ne peut plus être changée ensuite.

### Type de procédé {#prod.recipes.cProcessType}

*Discret (pièces)*, *Par lots* ou *Continu* : comment le produit est fabriqué. À titre d'information pour le moment.

### Description (français) {#prod.recipes.cDescFR}

Nom de la recette en français. Vide = la description du produit.

### Description (anglais) {#prod.recipes.cDescEN}

Nom de la recette en anglais. Vide = la description du produit.

### Raison de cette version {#prod.recipes.cChangeReason}

Pourquoi cette version existe (par exemple *moins de sel*). Rempli par **Nouvelle version à partir de celle-ci**.

### Valide du {#prod.recipes.dEffectiveFrom}

Premier jour où la version peut être utilisée. Vide = pas de limite.

### Valide jusqu'au {#prod.recipes.dEffectiveTo}

Dernier jour où la version peut être utilisée. Il ne peut pas être avant *Valide du*. Vide = pas de limite. Un jour donné, les ordres prennent la version approuvée par défaut valide ce jour-là, sinon la dernière version approuvée valide ce jour-là.

## Quantités {#prod.recipes.quantities}

Les matières et les temps sont écrits pour la quantité de base, et mis à l'échelle pour la quantité de chaque ordre.

### Quantité de base {#prod.recipes.dBaseQty}

La quantité pour laquelle la recette est écrite (par exemple 60 croissants). Obligatoire, plus grande que zéro.

### Unité {#prod.recipes.cUOM}

L'unité de la quantité de base. Vide = l'unité de stock du produit. Une autre unité demande une conversion vers l'unité de stock.

### Lot minimum {#prod.recipes.dMinBatch}

La plus petite quantité fabriquée d'un coup.

### Lot maximum {#prod.recipes.dMaxBatch}

La plus grande quantité fabriquée d'un coup : un ordre plus grand est divisé en lots. Aussi la taille d'un lot pour les temps donnés par lot. Il ne peut pas être plus petit que le minimum.

### Rendement % {#prod.recipes.dYieldPct}

Production bonne pour les matières, de 1 à 100 : 98 = 2 % de matières en plus. Vide = 100.

## Notes {#prod.recipes.notes}

### Notes {#prod.recipes.cNotes}

Texte libre.

## Opérations {#prod.recipes.operations}

Les opérations, dans l'ordre. Une opération standard (**Production > Opérations standards**) remplit les champs vides à l'enregistrement. Où elle se fait : une ressource, une capacité ou un centre de travail ; une ressource donne aussi son centre de travail. Une opération sans aucun des trois est refusée.

### Op. {#prod.recipes.operations.iOpSeq}

Numéro de l'opération (10, 20, 30...). Unique dans la recette.

### Opération {#prod.recipes.operations.cOperation}

L'opération standard de départ. Ses valeurs remplissent les champs laissés vides.

### Description (français) {#prod.recipes.operations.cDescFR}

Nom de l'opération dans cette recette.

### Centre de travail {#prod.recipes.operations.cWorkCenter}

Où se fait l'opération.

### Ressource {#prod.recipes.operations.cResource}

La machine exacte. Elle passe avant la capacité et le centre de travail, et donne le centre de travail.

### Capacité {#prod.recipes.operations.cCapability}

Ce que demande l'opération : toute ressource qui l'a peut la faire.

### Réglage (min) {#prod.recipes.operations.dSetupMin}

Minutes pour préparer la machine, une fois par ordre.

### Temps donné en {#prod.recipes.operations.cRunFormat}

*min / unité*, *unités / heure* ou *min / lot*. Voir [Opérations standards](#prod.operations.cRunFormat).

### Temps de production {#prod.recipes.operations.dRunValue}

Le temps de production dans le format choisi.

### Équipe {#prod.recipes.operations.iCrew}

Opérateurs nécessaires. 0 = sans surveillance (par exemple la fermentation).

### Attente min {#prod.recipes.operations.dMinWaitMin}

Minutes à attendre au moins après l'opération avant la suivante (par exemple fermentation, séchage).

### Attente max {#prod.recipes.operations.dMaxWaitMin}

Minutes que l'opération suivante peut attendre au plus. Elle ne peut pas être plus petite que *Attente min*.

### Après {#prod.recipes.operations.cPredecessors}

Les opérations qui doivent finir avant celle-ci : `10, 20` permet des opérations en parallèle. Vide = l'opération précédente. Une opération ne peut pas s'attendre elle-même, aussi à travers d'autres (*Les prédécesseurs forment une boucle*).

## Matières {#prod.recipes.materials}

Ce qui est consommé, pour la quantité de base.

### Séq. {#prod.recipes.materials.iSeq}

Ordre de la ligne. Vide = 10, 20, 30...

### Composant {#prod.recipes.materials.cComponent}

Le produit consommé. Il ne peut pas être le produit de la recette.

### Quantité {#prod.recipes.materials.dQtyPer}

Quantité pour la quantité de base de la recette. Plus grande que zéro.

### Unité {#prod.recipes.materials.cUOM}

Unité de la quantité. Vide = l'unité de stock du composant. Une autre unité (500 G de farine stockée en KG) demande une conversion.

### Perte % {#prod.recipes.materials.dScrapPct}

Quantité en plus perdue pendant la fabrication, de 0 à 99. 5 = 5 % de plus est utilisé.

### Fixe {#prod.recipes.materials.lFixedQty}

Coché : la quantité est par lot, quelle que soit la quantité fabriquée (par exemple la graisse d'un moule).

### Op. {#prod.recipes.materials.iOpSeq}

L'opération où la matière est consommée. Ce doit être une opération de la recette.

### Sortie {#prod.recipes.materials.cIssueMethod}

*Manuelle* (sortie à la main), *Consommation auto* (prise du stock automatiquement quand l'opération est déclarée) ou *Liste de prélèvement* (préparée à l'avance).

## Étapes {#prod.recipes.steps}

Le pas à pas de chaque opération, dans l'ordre, comme l'opérateur le suivra à l'atelier. À gauche, les étapes groupées par opération ; cliquez-en une pour la modifier à droite. **Ajouter une étape** en ajoute une après l'étape choisie. Les champs montrés dépendent du type de l'étape.

### Opération {#prod.recipes.steps.iOpSeq}

L'opération de l'étape.

### Étape {#prod.recipes.steps.iStep}

Numéro de l'étape dans son opération (10, 20...). Unique dans l'opération.

### Type d'étape {#prod.recipes.steps.cKind}

*Instruction* (lire et confirmer), *Ajouter une matière* (peser une matière de la recette et scanner son lot), *Régler un paramètre* (four à 230 degrés), *Mesurer* (saisir une valeur comparée aux limites), *Vérifier* (oui / non), *Minuterie* (attendre N minutes), *Déclarer la production* (lot, numéro de série, étiquette) ou *Deuxième signature* (une autre personne confirme).

### Titre (français) {#prod.recipes.steps.cTitleFR}

Ce que voit l'opérateur, en français. Obligatoire.

### Titre (anglais) {#prod.recipes.steps.cTitleEN}

Ce que voit l'opérateur, en anglais.

### Instruction (français) {#prod.recipes.steps.cInstructionFR}

Le détail de l'étape, en français.

### Instruction (anglais) {#prod.recipes.steps.cInstructionEN}

Le détail de l'étape, en anglais.

### Pièce jointe {#prod.recipes.steps.cAttachmentUrl}

Lien vers une photo, un plan, une vidéo ou une fiche de données de sécurité.

### Matière {#prod.recipes.steps.iMaterialSeq}

*Ajouter une matière* seulement : une matière de la recette consommée à cette opération (onglet **Matières**). Obligatoire.

### Code de la valeur {#prod.recipes.steps.cParam}

*Régler un paramètre*, *Mesurer* et *Vérifier* : le code court de la valeur (`TEMP_PATE`), lettres, chiffres et `_`. Enregistré en majuscules. Unique dans la recette ; *Seulement si* des étapes suivantes l'utilise. Obligatoire sauf pour *Vérifier*.

### Type de valeur {#prod.recipes.steps.cDataType}

*Nombre*, *Texte*, *Oui / non*, *Liste* ou *Photo*. Un *Vérifier* est toujours *Oui / non*.

### Obligatoire {#prod.recipes.steps.lRequired}

Coché : l'opérateur doit donner la valeur.

### Unité {#prod.recipes.steps.cUOM}

Unité d'un nombre (par exemple `°C`).

### Min {#prod.recipes.steps.dMin}

La plus petite valeur acceptée.

### Cible {#prod.recipes.steps.dTarget}

La valeur visée. Elle doit être entre le minimum et le maximum.

### Max {#prod.recipes.steps.dMax}

La plus grande valeur acceptée. Il ne peut pas être plus petit que le minimum.

### Valeurs de la liste {#prod.recipes.steps.cOptions}

*Liste* seulement : les choix, séparés par des virgules (`OK, Retouche, Rebut`). Obligatoire.

### Critique {#prod.recipes.steps.lCritical}

Point critique : une valeur hors de ses limites fait ce que dit *Si hors limites*. Non critique : seulement un avertissement.

### Si hors limites {#prod.recipes.steps.cOnFail}

*Bloquer* (l'étape suivante attend), *Avertir* ou *Retenir le lot*. Étapes critiques seulement.

### Durée (min) {#prod.recipes.steps.dDurationMin}

*Minuterie* seulement : les minutes. Obligatoire, plus grande que zéro.

### Rôle requis {#prod.recipes.steps.cRequiredRole}

*Deuxième signature* seulement : qui signe (par exemple superviseur, qualité). Vide = toute autre personne.

### Fréquence {#prod.recipes.steps.cFrequency}

*Une fois*, *Toutes les N unités*, *Toutes les N minutes* ou *Chaque lot*.

### N {#prod.recipes.steps.dFrequencyValue}

Pour *Toutes les N unités* ou *Toutes les N minutes* : le N. Obligatoire, plus grand que zéro.

### Seulement si {#prod.recipes.steps.cCondition}

L'étape se fait seulement quand une valeur précédente correspond, par exemple `TEMP_PATE < 24` (une étape de correction). Opérateurs : `=`, `!=`, `<`, `<=`, `>`, `>=`. Le code doit être saisi par une étape précédente.

### 2e signature {#prod.recipes.steps.lSecondSignature}

Coché : une deuxième personne confirme l'étape.

## Coproduits et sous-produits {#prod.recipes.outputs}

Fabriqués avec le produit (par exemple des rognures), pour la quantité de base, avec leur part du coût.

### Produit {#prod.recipes.outputs.cProduct}

Le produit aussi fabriqué. Il ne peut pas être le produit de la recette.

### Type {#prod.recipes.outputs.cKind}

*Coproduit* (un produit de valeur fabriqué en même temps) ou *Sous-produit* (un reste).

### Quantité {#prod.recipes.outputs.dQtyPer}

Quantité pour la quantité de base. Plus grande que zéro.

### Unité {#prod.recipes.outputs.cUOM}

Unité de la quantité. Vide = l'unité de stock du produit.

### Coût % {#prod.recipes.outputs.dCostPct}

Part du coût prise par cette sortie. Toutes les lignes ensemble doivent rester sous 100 % : le produit principal garde une part.

## Quantité et coût {#prod.recipes.explode}

La recette enregistrée pour une quantité : les matières (avec la perte et le rendement, converties dans l'unité de stock), les opérations (temps sur leur ressource, avec sa vitesse et l'efficacité de son centre de travail), le nombre de lots, le temps total et le coût prévu (matières, plus machine et main-d'œuvre selon les taux horaires des centres de travail, plus la sous-traitance). Un avertissement est montré quand un attribut du produit est hors des limites d'une ressource.

### Quantité {#prod.recipes.explode.qty}

La quantité à fabriquer, dans l'unité de la recette. La quantité de base par défaut.

## Vue opérateur {#prod.recipes.preview}

Les étapes d'une opération comme l'opérateur les suivra à l'atelier. Saisissez une valeur dans une étape pour tester ses limites : le résultat dit ce qui arrive (bloque l'étape suivante, avertissement, le lot est retenu). Elle utilise la recette enregistrée.

### Opération {#prod.recipes.preview.op}

L'opération dont les étapes sont montrées.

## Versions et historique {#prod.recipes.versions}

Les versions du produit (★ = celle par défaut ; cliquez une révision pour l'ouvrir), l'historique de cette version (quand, qui, action, statut, commentaire), et une comparaison avec une autre version : ce qui a été ajouté, retiré ou modifié dans l'en-tête, les matières, les opérations, les étapes et les coproduits.

### Une autre version {#prod.recipes.versions.compare}

La version à comparer avec celle-ci.

## Boutons {#prod.recipes.buttons}

### Soumettre pour révision {#prod.recipes.edit}

Brouillons seulement. Enregistre la recette et l'envoie en révision, après une confirmation. Elle ne peut plus être changée tant qu'elle n'est pas renvoyée.

### Approuver, renvoyer, par défaut, obsolète {#prod.recipes.approve}

Demandent la permission **Approuver**. **Approuver** (en révision ; un commentaire peut être donné) fait de la version celle par défaut du produit. **Renvoyer** (en révision) demande *Que faut-il changer?* et la remet en brouillon. **En faire la version par défaut** (approuvée) en fait la version que prennent les nouveaux ordres. **Rendre obsolète** (approuvée) demande une confirmation ; les nouveaux ordres ne l'utilisent plus.

### Nouvelle version à partir de celle-ci {#prod.recipes.create}

Tout statut. Demande pourquoi, puis copie la recette dans un nouveau brouillon avec la lettre de révision suivante (A → B), sans les dates de validité.

### Supprimer {#prod.recipes.delete}

Brouillons seulement. Une version approuvée ou obsolète est gardée : rendez-la obsolète à la place.
