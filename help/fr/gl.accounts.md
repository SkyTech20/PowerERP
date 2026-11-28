# Comptes GL et centres de coûts {#gl.accounts}

Le plan comptable et les centres de coûts. **Ce sont deux listes séparées : aucune n'est à l'intérieur de l'autre.**

- Un **compte GL** dit *ce qu'est* un montant : banque, stock, fournisseur, vente, dépense (par exemple `5100` Fournitures de bureau).
- Un **centre de coûts** dit *qui* le dépense : un département (par exemple `200` Production) ou un sous-département sous lui (`200-210` Ligne de sirop).
- Ils se rencontrent sur chaque **ligne d'achat** (facture fournisseur, réception), qui indique le compte **et**, à part, le centre de coûts : `5100` + `200-210` = fournitures de bureau de la ligne de sirop. Le même compte sert à tous les départements, et un département utilise plusieurs comptes.

Les produits (onglet **Taxes et comptabilité**) et les centres de travail prennent aussi leurs comptes et centres de coûts dans ces listes. Il n'y a pas encore d'écritures : les listes préparent la comptabilité à venir.

**Où :** **Grand livre > Comptes GL / Centres de coûts**, onglets **Comptes GL** et **Centres de coûts**.

## Comptes GL {#gl.accounts.list}

Colonnes : Code, Description (dans la langue de l'écran), Type, Exige un centre de coûts et Actif. Filtres : Type et Actif. **Nouveau** crée un compte.

### Code {#gl.accounts.cCode}

Numéro du compte (par exemple `5700`). Obligatoire, unique. Il ne peut plus être changé ensuite.

### Type {#gl.accounts.cType}

- **Actif**, **Passif**, **Avoir** : le bilan (banque, stock, comptes fournisseurs, capital).
- **Revenus**, **Dépenses** : l'état des résultats (ventes, achats, salaires, fournitures).

Laissé sur **Selon le code**, le type vient du premier chiffre, comme dans la plupart des plans comptables canadiens : 1 actif, 2 passif, 3 avoir, 4 revenus, 5 à 9 dépenses.

### Actif {#gl.accounts.lActive}

Décoché : le compte est gardé (son historique reste) mais n'est plus proposé dans les listes, et une nouvelle ligne d'achat ne peut plus l'utiliser.

### Description (français) {#gl.accounts.cDesc}

Nom du compte en français (par exemple *Fournitures de bureau*). Obligatoire. C'est lui qui est montré quand l'anglais est vide.

### Description (anglais) {#gl.accounts.cDescEN}

Nom du compte en anglais (par exemple *Office supplies*), montré quand l'écran est en anglais.

### Exige un centre de coûts {#gl.accounts.lRequiresCC}

Coché : une ligne de facture fournisseur ou de réception sur ce compte ne peut pas être enregistrée sans centre de coûts (CC1). Habituel pour les comptes de dépenses, pour connaître chaque dépense par département.

## Centres de coûts {#gl.accounts.cc}

La liste montre chaque **département** en gras, avec ses **sous-départements** sous lui (`↳ 200-210`). Colonnes : Centre de coûts, Description, Niveau (Département ou Sous-département) et Actif. Sur un département, **＋ Sous-département** ouvre un nouveau sous-département déjà rattaché.

Exemple d'une usine : `100` Administration, `200` Production avec `200-210` Ligne de sirop et `200-220` Emballage, `300` Entrepôt, `400` Ventes, `500` Qualité.

### Département (CC1) {#gl.accounts.cc.cCC1}

Code du département. Obligatoire. Il ne peut plus être changé ensuite.

### Sous-département (CC2) {#gl.accounts.cc.cCC2}

Vide : le département lui-même. Rempli : un sous-département du département CC1, qui doit exister avant. La paire CC1 + CC2 est unique et ne peut plus être changée. Un département qui a encore des sous-départements ne peut pas être supprimé.

### Actif {#gl.accounts.cc.lActive}

Décoché : gardé, mais plus proposé sur les lignes d'achat.

### Description (français) {#gl.accounts.cc.cDesc}

Nom en français. Obligatoire.

### Description (anglais) {#gl.accounts.cc.cDescEN}

Nom en anglais, montré quand l'écran est en anglais.
