# Comptes GL et centres de coûts {#gl.accounts}

Le plan comptable et les centres de coûts. Les produits (onglet **Taxes et comptabilité**), les lignes des réceptions et des factures fournisseurs, et les centres de travail prennent leurs comptes et centres de coûts dans ces listes. Il n'y a pas encore d'écritures de journal : les listes préparent la comptabilité à venir.

**Où :** **Grand livre > Comptes GL / Centres de coûts**, onglets **Comptes GL** et **Centres de coûts**.

## Comptes GL {#gl.accounts.list}

Colonnes : Code et Description. **Nouveau** crée un compte.

### Code {#gl.accounts.cCode}

Numéro du compte (par exemple `5700`). Obligatoire, unique. Il ne peut plus être changé ensuite.

### Description {#gl.accounts.cDesc}

Nom du compte (par exemple *Fournitures de bureau*). Obligatoire.

## Centres de coûts {#gl.accounts.cc}

Colonnes : Centre de coûts (CC1), Sous-centre (CC2) et Description. Un centre de coûts peut être divisé en sous-centres : `170` seul, ou `170` avec `751`. Les listes les montrent comme `170-751`.

### Centre de coûts (CC1) {#gl.accounts.cc.cCC1}

Code du centre de coûts (par exemple un département). Obligatoire. Il ne peut plus être changé ensuite.

### Sous-centre (CC2) {#gl.accounts.cc.cCC2}

Code du sous-centre à l'intérieur de CC1. Vide = le centre de coûts lui-même. La paire CC1 + CC2 est unique, et elle ne peut plus être changée ensuite.

### Description {#gl.accounts.cc.cDesc}

Nom du centre de coûts. Obligatoire.
