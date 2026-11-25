# Inventaire physique {#inv.count}

Inventaires annuels et décomptes cycliques : le système prépare une feuille de décompte à partir du stock, vous tapez ce que vous comptez, et le report transforme les écarts en ajustements de stock.

**Où :** **Inventaire > Inventaire physique**.

## Liste {#inv.count.list}

Colonnes : #, Date, Entrepôt, Description, Lignes, Comptées (lignes avec une quantité saisie) et Statut (*Brouillon* ou *Comptabilisée*).

Filtres : Statut et Entrepôt. **Nouveau** crée un inventaire.

## Déroulement d'un inventaire {#inv.count.cycle}

1. **Nouveau :** choisissez l'entrepôt et, au besoin, les emplacements ou produits à compter. À l'enregistrement, la feuille de décompte est remplie avec le stock de l'entrepôt (ou des emplacements / produits choisis).
2. **Compter :** tapez la quantité trouvée sur chaque ligne. Une ligne laissée vide n'est pas comptée et ne change rien. Ajoutez une ligne pour un produit trouvé là où le système n'en a pas.
3. **Rafraîchir à partir du stock** si du stock a bougé depuis la préparation de la feuille : voir [Rafraîchir à partir du stock](#inv.count.generate).
4. **Reporter l'inventaire :** voir [Reporter](#inv.count.post).

## Général {#inv.count.general}

### Entrepôt {#inv.count.cWarehouse}

L'entrepôt compté. Obligatoire. Il ne peut plus être changé une fois l'inventaire créé.

### Date {#inv.count.dDate}

Date de l'inventaire. Aujourd'hui par défaut.

### Description {#inv.count.cDescription}

Texte libre, par exemple *Inventaire annuel 2026* ou *Allée A-02*.

### Emplacements commençant par {#inv.count.cLocationPrefix}

Ne compte que les emplacements dont le code commence par ce texte, par exemple `A-02` pour le décompte cyclique d'une allée. Vide : tous les emplacements.

### Produits commençant par {#inv.count.cProductPrefix}

Ne compte que les produits dont le code commence par ce texte. Vide : tous les produits.

### Reporté le {#inv.count.dPosted}

Date du report de l'inventaire. Inventaires reportés seulement.

### Valeur des écarts {#inv.count.dValueDiff}

Valeur totale des ajustements faits par l'inventaire (positive : stock trouvé, négative : stock manquant). Inventaires reportés seulement.

## Feuille de décompte {#inv.count.lines}

Une ligne par produit, emplacement, lot et numéro de série en stock. Les lignes avec un écart sont mises en évidence.

### Produit {#inv.count.lines.cProduct}

Le produit compté. Un produit ajouté à la main doit être tenu en stock.

### Description {#inv.count.lines.cDescFR}

Description du produit. Lecture seule.

### Emplacement {#inv.count.lines.cLocation}

Où le produit a été compté.

### Lot {#inv.count.lines.cLot}

Le lot compté, pour les produits suivis par lot.

### Numéro de série {#inv.count.lines.cSerial}

Le numéro de série compté, pour les produits suivis par numéro de série.

### Prévu {#inv.count.lines.dQtyExpected}

La quantité que le système a. Lecture seule. Au report, elle est reprise du stock à ce moment.

### Compté {#inv.count.lines.dQtyCounted}

La quantité trouvée, dans l'unité de stock. Vide : la ligne n'est pas comptée. 0 : rien n'a été trouvé, et le stock est mis à zéro.

### Écart {#inv.count.lines.dDiff}

Compté − prévu. Lecture seule, rempli au report de l'inventaire.

## Boutons {#inv.count.buttons}

### Rafraîchir à partir du stock {#inv.count.generate}

Brouillons seulement. Refait la feuille à partir du stock actuel, après une confirmation. Les quantités déjà comptées sont gardées.

### Reporter l'inventaire {#inv.count.post}

Demande une confirmation, puis fait un mouvement *Inventaire* pour chaque ligne comptée dont la quantité diffère du stock à ce moment. Tout ou rien : chaque mouvement est vérifié avant que le premier soit reporté. L'inventaire passe ensuite en lecture seule. Au moins une ligne doit avoir une quantité comptée.

### Supprimer {#inv.count.delete}

Brouillons seulement. Un inventaire reporté ne peut pas être supprimé : ses mouvements sont dans **Mouvements de stock**.
