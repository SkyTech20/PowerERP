# Fournisseurs {#ap.suppliers}

Le fichier des fournisseurs : chez qui la compagnie achète, leur adresse, leur terme de paiement, leurs numéros de taxes et leur acheteur. Les bons de commande, les réceptions, les factures fournisseurs et les fournisseurs des produits les utilisent.

**Où :** **Comptes fournisseurs > Fournisseurs**.

## Liste {#ap.suppliers.list}

Colonnes : Code fournisseur, Nom, Ville, Province / État, Terme de paiement, Nom de l'acheteur et Statut achat. Filtre : Statut achat. **Nouveau** crée un fournisseur.

## Général {#ap.suppliers.general}

### Code fournisseur {#ap.suppliers.cCode}

Code court du fournisseur (par exemple `ISECO`). Obligatoire, unique. Il ne peut plus être changé ensuite.

### Nom {#ap.suppliers.cName}

Nom du fournisseur. Obligatoire. Il est copié dans les bons de commande, les réceptions et les factures.

## Adresse {#ap.suppliers.address}

### Adresse ligne 1 {#ap.suppliers.cAddress1}

Adresse civique du fournisseur.

### Adresse ligne 2 {#ap.suppliers.cAddress2}

Bureau, édifice, deuxième ligne.

### Ville {#ap.suppliers.cCity}

Ville du fournisseur.

### Province / État {#ap.suppliers.cProvince}

Province ou État. `QC` par défaut.

### Pays {#ap.suppliers.cCountry}

Pays. `CA` par défaut.

### Code postal {#ap.suppliers.cZipCode}

Code postal ou ZIP.

## Termes et taxes {#ap.suppliers.terms}

### Terme de paiement {#ap.suppliers.cTermCode}

Quand le fournisseur est payé (par exemple `n30`). Choisissez un terme déjà utilisé par un autre fournisseur, ou tapez un nouveau code ; le choisir remplit la description. `n30` par défaut.

### Description du terme {#ap.suppliers.cTermDesc}

Le terme en mots (par exemple *net 30 jours*).

### No TPS {#ap.suppliers.cNoTPS}

Le numéro d'inscription à la TPS du fournisseur. Rempli : les bons de commande et réceptions de ce fournisseur calculent la TPS (5 %). Vide : pas de TPS.

### No TVQ {#ap.suppliers.cNoTVQ}

Le numéro d'inscription à la TVQ du fournisseur. Rempli : les bons de commande et réceptions calculent la TVQ (9,975 %). Vide : pas de TVQ.

## Achats {#ap.suppliers.purchasing}

### Code acheteur {#ap.suppliers.cCodeAch}

L'acheteur habituel de ce fournisseur. Choisissez un acheteur déjà utilisé, ou tapez un nouveau code ; le choisir remplit le nom.

### Nom de l'acheteur {#ap.suppliers.cDescAch}

Nom de l'acheteur.

### Département {#ap.suppliers.cDeptSauv}

Le département qui fait affaire avec le fournisseur. Texte libre.

### Statut achat {#ap.suppliers.iStatutAch}

*Actif* ou *Inactif*. À titre d'information : un fournisseur inactif est encore proposé dans les listes.

### Type de BC {#ap.suppliers.iTypePO}

*1 - Avec BC*, *2 - Sans BC* ou *3 - Commande ouverte* : comment on achète habituellement chez ce fournisseur. À titre d'information.
