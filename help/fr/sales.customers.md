# Clients {#sales.customers}

Les entreprises à qui vous vendez : adresse de facturation, taxes, terme de paiement, liste de prix, adresses de livraison et contacts. Ce qui est défini ici est proposé sur chaque nouvelle facture du client.

**Où :** **Ventes > Clients**.

## Liste {#sales.customers.list}

Colonnes : Code, Nom, Ville, Province, Groupe de taxes, Langue des factures, Liste de prix, nombre d'adresses de livraison et Actif.

Filtres : Groupe de taxes, Liste de prix et Actif. **Nouveau** crée un client.

## Général {#sales.customers.general}

### Code {#sales.customers.cCode}

Code court en majuscules (par exemple `HOTEL-LAURIER`). Obligatoire. Il ne peut plus être changé ensuite.

### Nom {#sales.customers.cName}

Le nom usuel du client. Obligatoire.

### Actif {#sales.customers.lActive}

Seul un client actif est trouvé par la recherche de client de la facture. Décochez-le pour ne plus utiliser un client qui a des factures.

### Raison sociale {#sales.customers.cLegalName}

Le nom légal. Quand il diffère du nom usuel, c'est lui qui est imprimé sur la facture.

### Langue des factures {#sales.customers.cLang}

*Français* ou *Anglais*. Elle détermine la langue de la facture et de la note de crédit imprimées, et quelle description du produit va sur les lignes. Une facture peut quand même être imprimée dans l'autre langue (*Langue des factures* de la facture).

## Adresse de facturation {#sales.customers.billTo}

### Adresse ligne 1 {#sales.customers.cAddress1}

L'adresse de facturation, imprimée sous *Facturer à*. Il en va de même pour les lignes suivantes.

### Adresse ligne 2 {#sales.customers.cAddress2}

Deuxième ligne de l'adresse de facturation.

### Ville {#sales.customers.cCity}

Ville de l'adresse de facturation.

### Province / État {#sales.customers.cProvince}

Province de l'adresse de facturation (par exemple QC).

### Pays {#sales.customers.cCountry}

Pays de l'adresse de facturation (par exemple CA).

### Code postal {#sales.customers.cZipCode}

Code postal de l'adresse de facturation.

### Téléphone {#sales.customers.cPhone}

Numéro de téléphone du client.

### Courriel {#sales.customers.cEmail}

Courriel de facturation, utilisé quand aucun contact n'est coché *Factures*. Les factures ne sont pas encore envoyées par courriel : à titre d'information pour le moment.

## Taxes et facturation {#sales.customers.billing}

### Groupe de taxes {#sales.customers.cTaxGroup}

Les taxes facturées au client. Obligatoire. QC = TPS + TVQ, ON = TVH 13 %, EXO = exonéré. Une adresse de livraison peut avoir son propre groupe, qui remplace celui-ci.

### No d'exemption {#sales.customers.cTaxExemptNo}

Le certificat ou le numéro d'exemption d'un client exonéré. Imprimé sur la facture.

### Terme de paiement {#sales.customers.cTermCode}

Le code du terme de paiement (par exemple `n30`). La liste propose les codes déjà utilisés par d'autres clients, et vous pouvez en taper un nouveau. Un code `nXX` fait afficher sur la facture imprimée l'échéance (*Échéance / Due*) = date de la facture + XX jours.

### Description du terme {#sales.customers.cTermDesc}

Texte du terme de paiement imprimé sur la facture (par exemple *net 30 jours*). Rempli à partir du code, et peut être changé.

### Liste de prix {#sales.customers.cPriceList}

La liste de prix du client (**Ventes > Listes de prix**). Vide : le client paie le Prix 1 du produit, avec l'*Escompte %* ci-dessous.

### Escompte % {#sales.customers.dDiscountPct}

Escompte sur chaque ligne des factures du client, sauf si la liste de prix donne un autre escompte (sur la ligne du produit ou sur sa catégorie). Entre 0 et 100.

### Entrepôt d'expédition {#sales.customers.cWarehouse}

L'entrepôt d'où part la marchandise du client. Proposé sur une nouvelle facture.

### Notes {#sales.customers.cNotes}

Notes internes.

## Adresses de livraison {#sales.customers.addresses}

Les endroits où la marchandise du client est livrée, une ligne par adresse. L'adresse par défaut est proposée sur chaque nouvelle facture.

### Code {#sales.customers.addresses.cCode}

Code court de l'adresse (par exemple `HOTEL`, `OTTAWA`). Obligatoire, et unique pour le client.

### Nom {#sales.customers.addresses.cName}

Nom de l'endroit, imprimé sous *Livrer à*.

### Adresse ligne 1 {#sales.customers.addresses.cAddress1}

Adresse de livraison. Obligatoire.

### Adresse ligne 2 {#sales.customers.addresses.cAddress2}

Deuxième ligne de l'adresse de livraison.

### Ville {#sales.customers.addresses.cCity}

Ville de la livraison.

### Prov. {#sales.customers.addresses.cProvince}

Province de la livraison.

### Code postal {#sales.customers.addresses.cZipCode}

Code postal de la livraison.

### Pays {#sales.customers.addresses.cCountry}

Pays de la livraison.

### Contact {#sales.customers.addresses.cContact}

Qui reçoit la marchandise à cet endroit.

### Téléphone {#sales.customers.addresses.cPhone}

Numéro de téléphone de l'endroit.

### Groupe de taxes {#sales.customers.addresses.cTaxGroup}

Les taxes de cet endroit. Quand il est rempli, il remplace celui du client, parce que les taxes suivent le lieu de livraison. Exemple : HOTEL-LAURIER est QC, mais la livraison à OTTAWA utilise ON (TVH 13 %).

### Défaut {#sales.customers.addresses.lDefault}

L'adresse par défaut est proposée sur chaque nouvelle facture. Une seule adresse peut être l'adresse par défaut.

## Contacts {#sales.customers.contacts}

Les personnes à joindre chez le client.

### Nom {#sales.customers.contacts.cName}

Nom de la personne. Obligatoire.

### Titre {#sales.customers.contacts.cTitle}

Fonction (par exemple *Responsable des achats*).

### Téléphone {#sales.customers.contacts.cPhone}

Numéro de téléphone de la personne.

### Courriel {#sales.customers.contacts.cEmail}

Courriel de la personne. Obligatoire quand *Factures* est coché.

### Factures {#sales.customers.contacts.lInvoices}

Les personnes qui reçoivent les factures. À titre d'information tant que les factures ne sont pas envoyées par courriel.

## Vérifier un prix {#sales.customers.check}

Combien le client paie pour un produit, et quelle règle donne ce prix. Rien n'est enregistré. Servez-vous-en pour expliquer un prix au client ou pour vérifier une liste de prix. Le calcul lit le client tel qu'il est enregistré : enregistrez vos modifications d'abord.

### Produit {#sales.customers.check.cProduct}

Le produit à vérifier. Seuls les produits vendables sont proposés.

### Quantité {#sales.customers.check.dQty}

La quantité. Elle change le prix quand la liste de prix a des paliers de quantité.

### Unité {#sales.customers.check.cUOM}

L'unité. Vide : l'unité de vente du produit.

### Date {#sales.customers.check.dDate}

La date du prix. Une liste de prix ne compte que pendant sa période de validité.

### Le résultat {#sales.customers.check.result}

- **Prix de liste :** le Prix 1 du produit.
- **Prix :** le prix qui s'applique et d'où il vient (liste de prix X à partir de N unités, ou le prix de liste).
- **Escompte :** l'escompte et d'où il vient (la ligne de la liste de prix, la catégorie ou le client).
- **Prix net :** prix × (1 − escompte %).
- Un avertissement quand le prix net est sous le prix minimum du produit : une telle ligne serait refusée sur une facture.

Voir [Comment le prix est trouvé](#sales.priceLists.order) dans l'aide des listes de prix.

## Supprimer {#sales.customers.delete}

Un client utilisé sur une facture ne peut pas être supprimé. Décochez plutôt *Actif*.
