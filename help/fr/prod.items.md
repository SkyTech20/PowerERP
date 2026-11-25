# Articles fabriqués {#prod.items}

Les données de fabrication des produits : fabriqué ou acheté, famille de réglage, lot de fabrication, traçabilité et attributs. Seul un produit fabriqué (*Fabriquer*, ou *Fabriquer ou acheter*) peut avoir une recette. Le produit lui-même est dans **Inventaire > Produits** : son onglet **Fabrication** montre un résumé de ces données, avec un lien ici.

**Où :** **Production > Articles fabriqués**.

## Liste {#prod.items.list}

Colonnes : Produit, Description, Fabriquer ou acheter, Famille de réglage, Lot minimum, Délai (jours) et Traçabilité. Filtres : Fabriquer ou acheter et Famille de réglage. **Nouveau** ajoute les données de fabrication d'un produit.

## Fabrication {#prod.items.mfg}

### Produit {#prod.items.cProduct}

Le produit (**Inventaire > Produits**). Obligatoire. Un produit a une seule ligne ici. Il ne peut plus être changé ensuite.

### Fabriquer ou acheter {#prod.items.cMakeBuy}

*Fabriquer*, *Acheter* ou *Fabriquer ou acheter*. Seul un produit fabriqué (*Fabriquer*, *Fabriquer ou acheter*) a des recettes et des ordres de fabrication.

### Fantôme {#prod.items.lPhantom}

Un sous-ensemble jamais stocké : ses matières remontent dans l'ordre du produit parent. Un fantôme est fabriqué, il ne peut donc pas être *Acheter*.

### Famille de réglage {#prod.items.cSetupFamily}

Quelle ligne de la [Matrice de réglage](#prod.setupmatrix) s'applique quand ce produit en suit un autre sur une machine.

## Lot de fabrication {#prod.items.lots}

Minimum et multiple de la quantité à fabriquer, et le délai : ce que la planification (PBM) proposera.

### Lot minimum {#prod.items.dMfgLotMin}

La plus petite quantité à fabriquer d'un coup, dans l'unité de stock.

### Multiple du lot {#prod.items.dMfgLotMultiple}

La quantité à fabriquer est arrondie vers le haut à un multiple de ce nombre (par exemple des plaques de 24).

### Délai (jours) {#prod.items.iMfgLeadDays}

Les jours nécessaires pour fabriquer le produit.

## Traçabilité {#prod.items.trace}

### Traçabilité {#prod.items.cTraceLevel}

*Aucune*, *Par lot* ou *Par numéro de série*. *Par lot* demande le suivi des lots du produit, et *Par numéro de série* son suivi des numéros de série (**Inventaire > Produits**, onglet **Inventaire**). Sinon l'enregistrement est refusé.

### Notes {#prod.items.cNotes}

Texte libre.

## Attributs {#prod.items.attributes}

Les mesures du produit (largeur, grammage, couleur...). Les recettes les comparent aux limites des ressources (**Production > Ressources (machines)**, onglet **Capacités et attributs**) et avertissent quand le produit est en dehors. Un attribut est listé une seule fois.

### Attribut {#prod.items.attributes.cAttribute}

Nom de l'attribut, par exemple `Largeur`. Utilisez le même nom que dans les ressources.

### Unité {#prod.items.attributes.cUOM}

Unité de la valeur (par exemple `M`).

### Nombre {#prod.items.attributes.dNumber}

La valeur du produit quand c'est un nombre. C'est elle qui est comparée aux limites des ressources.

### Texte {#prod.items.attributes.cValue}

La valeur quand ce n'est pas un nombre (par exemple une couleur).
