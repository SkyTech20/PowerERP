# Matrice de réglage {#prod.setupmatrix}

Le temps pour passer d'une famille de réglage à une autre, sur un centre de travail ou une ressource. Elle fait dépendre le temps de réglage de l'ordre des travaux : passer du blanc au noir est plus rapide que du noir au blanc. Les familles sont dans **Production > Paramètres de production**, et chaque produit reçoit sa famille dans **Production > Articles fabriqués**.

**Où :** **Production > Matrice de réglage**.

## Liste {#prod.setupmatrix.list}

Colonnes : Pour, Code, Notes, Changements et Actif. Filtre : Pour. **Nouveau** crée une matrice. Un centre de travail ou une ressource a au plus une matrice.

## Général {#prod.setupmatrix.general}

La matrice d'un centre de travail s'applique à toutes ses ressources ; la matrice d'une ressource remplace celle de son centre de travail.

### Pour {#prod.setupmatrix.cScope}

*Centre de travail* ou *Ressource* : à qui appartient la matrice. Il ne peut plus être changé ensuite.

### Centre de travail / Ressource {#prod.setupmatrix.cScopeCode}

Le centre de travail ou la ressource de la matrice. Obligatoire. Il ne peut plus être changé ensuite.

### Actif {#prod.setupmatrix.lActive}

Décoché : la matrice n'est pas utilisée.

### Notes {#prod.setupmatrix.cNotes}

Texte libre.

## Changements {#prod.setupmatrix.lines}

Une ligne par paire de familles. Vide ou `*` = toute famille. Pour trouver le changement, la paire exacte passe en premier, puis *de la famille → toute*, puis *toute → vers la famille*, puis *toute → toute*. Sans ligne pour la paire : la même famille = pas de changement (0), sinon le réglage de l'opération.

### De la famille {#prod.setupmatrix.lines.cFromFamily}

La famille du travail précédent. Vide ou `*` = toute famille.

### Vers la famille {#prod.setupmatrix.lines.cToFamily}

La famille du travail suivant. Vide ou `*` = toute famille.

### Réglage (min) {#prod.setupmatrix.lines.dSetupMin}

Minutes du changement. Elles remplacent le réglage de l'opération.

### Coût {#prod.setupmatrix.lines.dSetupCost}

Coût du changement (produit de nettoyage, matière perdue...).

### Perte (qté) {#prod.setupmatrix.lines.dScrapQty}

Quantité perdue pendant le changement.

## Grille des changements {#prod.setupmatrix.grid}

Sous une matrice enregistrée : chaque famille vers chaque famille, comme l'ordonnancement la lira. Lignes : de ; colonnes : vers. Une valeur marquée `*` vient d'une ligne avec *toute famille*. En gris : absent de la matrice (même famille = 0, sinon le réglage de l'opération). Passez sur une case pour voir quelle règle l'a donnée.

### Réglage de l'opération (min) {#prod.setupmatrix.grid.default}

Le réglage à montrer quand la matrice n'a pas de ligne pour la paire. Pour cette grille seulement : la vraie valeur vient de chaque opération. 30 par défaut.
