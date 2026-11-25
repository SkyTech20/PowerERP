# Catégories et unités {#inv.setup}

Les catégories de produits (familles et sous-familles), les unités de mesure, et les conversions générales entre unités.

**Où :** **Inventaire > Catégories / unités**, onglets **Catégories**, **Unités de mesure** et **Conversions**.

## Catégories {#inv.setup.categories}

Colonnes : Code, Description, Catégorie parente et Actif. Une catégorie regroupe les produits (**Inventaire > Produits**, champ *Catégorie*) et sert de base aux escomptes par catégorie des listes de prix. Une catégorie utilisée par un produit ou une liste de prix, ou qui a des sous-catégories, ne peut pas être supprimée.

### Code {#inv.setup.cCode}

Code court de la catégorie (par exemple `LIGHT`). Obligatoire. Il ne peut plus être changé ensuite.

### Catégorie parente {#inv.setup.cParent}

Vide pour une famille ; la famille pour une sous-famille. Un escompte par catégorie dans une liste de prix s'applique aussi aux sous-catégories. Une catégorie ne peut pas être sa propre parente.

### Actif {#inv.setup.lActive}

Marque une catégorie qui n'est plus utilisée.

### Description (français) {#inv.setup.cDescFR}

Nom de la catégorie en français. Obligatoire.

### Description (anglais) {#inv.setup.cDescEN}

Nom de la catégorie en anglais.

## Unités de mesure {#inv.setup.uom}

Colonnes : Code, Description, Type et Actif. Les unités dans lesquelles les produits sont comptés, achetés et vendus (UN, KG, CS, L...). Une unité utilisée par un produit ou un document ne peut pas être supprimée.

### Code {#inv.setup.uom.cCode}

Code court de l'unité (par exemple `KG`, `CS`). Obligatoire. Il ne peut plus être changé ensuite.

### Type {#inv.setup.uom.cType}

*Nombre*, *Poids*, *Longueur*, *Surface*, *Volume* ou *Temps* : le genre de quantité.

### Actif {#inv.setup.uom.lActive}

Marque une unité qui n'est plus utilisée.

### Description (français) {#inv.setup.uom.cDescFR}

Nom de l'unité en français. Obligatoire.

### Description (anglais) {#inv.setup.uom.cDescEN}

Nom de l'unité en anglais.

## Conversions {#inv.setup.uomconv}

Les conversions valables pour **tous les produits**, par exemple 1 KG = 1000 G. Saisissez une paire une seule fois : l'inverse (1 G = 0,001 KG) est déduit. Grâce à elles, un produit compté en KG peut être acheté en LB ou utilisé en G dans une recette.

L'emballage d'un produit (1 SAC = 25 KG) ne va pas ici : il va dans le produit, onglet **Unités et dimensions**, [Autres unités de ce produit](#inv.items.conversions).

**Ajouter les conversions standard** ajoute les unités courantes (KG, G, MG, LB, L, ML, M, CM...) et leurs conversions qui manquent. Rien de ce qui existe déjà n'est changé.

### 1 unité de {#inv.setup.uomconv.cFromUOM}

La première unité. Obligatoire.

### Égale {#inv.setup.uomconv.dFactor}

Combien d'unités de la deuxième font une de la première : `1000` pour 1 KG = 1000 G. Obligatoire, plus grand que zéro.

### Unité {#inv.setup.uomconv.cToUOM}

La deuxième unité. Obligatoire. Elle ne peut pas être la même que la première, et une paire déjà saisie dans l'autre sens est refusée.

### Actif {#inv.setup.uomconv.lActive}

Décoché : la conversion n'est pas utilisée.

### Notes {#inv.setup.uomconv.cNotes}

Texte libre.
