# Taxes {#admin.taxes}

Les codes de taxe (TPS, TVQ, TVH...) avec leurs taux dans le temps, et les groupes de taxes qui disent quelles taxes s'appliquent. Un produit, un client ou une facture de vente ne garde qu'un code de groupe (par exemple `QC`) ; le groupe donne les taxes, dans l'ordre.

**Où :** **Administration > Taxes**, onglets **Codes de taxe** et **Groupes de taxes**.

## Codes de taxe {#admin.taxes.list}

Colonnes : Code, Description, Genre, Juridiction, Taux en vigueur, Numéro d'inscription et Actif. **Nouveau** crée un code de taxe. Un code de taxe utilisé par un groupe de taxes ne peut pas être supprimé.

### Code {#admin.taxes.cCode}

Code court de la taxe (par exemple `TPS`, `TVQ`). Obligatoire. Il ne peut plus être changé ensuite.

### Genre {#admin.taxes.cKind}

*Fédérale (TPS)*, *Provinciale (TVQ / TVP)*, *Harmonisée (TVH)* ou *Autre*.

### Juridiction {#admin.taxes.cJurisdiction}

Qui perçoit la taxe (par exemple *Canada*, *Québec*). À titre d'information.

### Actif {#admin.taxes.lActive}

Marque une taxe qui n'est plus utilisée.

### Description (français) {#admin.taxes.cDescFR}

Nom de la taxe en français. Obligatoire.

### Description (anglais) {#admin.taxes.cDescEN}

Nom de la taxe en anglais.

### Numéro d'inscription {#admin.taxes.cRegistrationNo}

Le numéro d'inscription de la compagnie pour cette taxe (par exemple `123456789 RT0001` pour la TPS, `1234567890 TQ0001` pour la TVQ). Il est imprimé sur les factures de vente et montré dans **Administration > Paramètres système**.

## Comptabilité {#admin.taxes.accounting}

Les comptes de la taxe, pour la comptabilité à venir.

### GL - taxe perçue (ventes) {#admin.taxes.cGLCollected}

Où va la taxe facturée sur les ventes.

### GL - taxe à recouvrer (CTI / RTI) {#admin.taxes.cGLRecoverable}

Où va la taxe payée sur les achats et réclamée.

### % récupérable {#admin.taxes.dRecoverablePct}

Part de la taxe payée qui peut être réclamée. 100 sauf si les CTI / RTI sont restreints.

## Taux {#admin.taxes.lines}

Les taux de la taxe dans le temps. Gardez les anciens taux avec leurs dates : un document utilise le taux en vigueur à sa date (la ligne qui s'applique avec la date de début la plus récente). Une ligne demande un taux.

### Du {#admin.taxes.lines.dStartDate}

Premier jour du taux. Vide = depuis toujours.

### Au {#admin.taxes.lines.dEndDate}

Dernier jour du taux. Vide = sans fin. Il ne peut pas être avant *Du*.

### Taux % {#admin.taxes.lines.dRate}

Le taux en pour cent (par exemple `5` pour la TPS, `9.975` pour la TVQ). Obligatoire.

## Groupes de taxes {#admin.taxes.taxgroups}

Colonnes : Code, Description, Province / État, Traitement, Taxes et Actif. Un groupe dit quelles taxes s'appliquent, dans quel ordre. Un groupe utilisé par un produit, un client ou un document ne peut pas être supprimé.

### Code {#admin.taxes.taxgroups.cCode}

Code court du groupe (par exemple `QC`, `ON`, `EXEMPT`). Obligatoire. Il ne peut plus être changé ensuite.

### Traitement {#admin.taxes.taxgroups.cTreatment}

*Taxable* : les taxes du groupe sont facturées. *Détaxé (taux zéro)* ou *Exonéré* : aucune taxe n'est facturée.

### Province / État {#admin.taxes.taxgroups.cProvince}

La province du groupe. À titre d'information.

### Actif {#admin.taxes.taxgroups.lActive}

Marque un groupe qui n'est plus utilisé.

### Description (français) {#admin.taxes.taxgroups.cDescFR}

Nom du groupe en français. Obligatoire.

### Description (anglais) {#admin.taxes.taxgroups.cDescEN}

Nom du groupe en anglais.

## Taxes du groupe {#admin.taxes.taxgroups.lines}

Les codes de taxe du groupe, dans l'ordre.

### Ordre {#admin.taxes.taxgroups.lines.iSeq}

Ordre du calcul. Vide = 1, 2, 3...

### Code de taxe {#admin.taxes.taxgroups.lines.cTaxCode}

Un code de taxe du premier onglet.

### Taxe sur taxe {#admin.taxes.taxgroups.lines.lCompound}

Coché : la taxe est calculée sur le montant plus les taxes au-dessus. Décoché : sur le montant seulement (le cas habituel pour la TPS et la TVQ depuis 2013).

## Essayer le groupe {#admin.taxes.taxgroups.sim}

Sous un groupe enregistré : les taxes d'un montant à une date, avec chaque taxe, son taux, sa base et ses comptes, et le total. C'est ce que les autres écrans obtiennent du groupe.

### Montant {#admin.taxes.taxgroups.sim.amount}

Le montant avant taxes. 100,00 par défaut.

### Date {#admin.taxes.taxgroups.sim.date}

La date des taux. Aujourd'hui par défaut.
