# Factures fournisseurs {#ap.invoices}

Les factures reçues des fournisseurs, saisies ici ou envoyées par SkyAI. Une facture facture les réceptions d'un bon de commande : elles ne sont alors plus *Non facturé*.

**Où :** **Comptes fournisseurs > Factures**.

## Liste {#ap.invoices.list}

Colonnes : No de facture, Code fournisseur, Fournisseur, Date de facture, No de BC, Total de la facture, Statut et Source (*Saisie manuelle* ou *SkyAI*). Filtres : Statut et Source. **Nouveau** crée une facture. Le tableau de bord compte les factures *Brouillon* et *Approuvée* comme ouvertes.

## Général {#ap.invoices.general}

### Code fournisseur {#ap.invoices.cNoFourn}

Le fournisseur de la facture. Obligatoire.

### Fournisseur {#ap.invoices.cNomFourn}

Nom du fournisseur. Lecture seule, rempli à partir du code.

### Statut {#ap.invoices.cStatut}

*Brouillon*, *Approuvée*, *Comptabilisée* ou *Payée*. Choisi à la main pour le moment. Une facture de SkyAI arrive *Comptabilisée*, ou *Brouillon* quand SkyAI l'a trouvée incomplète.

### No de facture {#ap.invoices.cNoFacture}

Le numéro de la facture du fournisseur. Obligatoire. Un même fournisseur ne peut pas avoir deux factures avec le même numéro.

### Date de facture {#ap.invoices.dDateFacture}

Date sur la facture. Obligatoire. Aujourd'hui par défaut.

### No de BC {#ap.invoices.cNoCommAch}

Le bon de commande facturé. Quand aucune ligne ne donne de numéro de réception, la facture facture toutes les réceptions ouvertes de cette commande ; quand toutes ses réceptions sont facturées, la commande n'est plus *Non facturé*.

### Devise {#ap.invoices.cDevise}

*CAD*, *USD* ou *EUR* : la devise des montants.

## Lignes {#ap.invoices.lines}

Une ligne par article ou frais facturé. Une ligne sans article, sans description et sans montant est retirée à l'enregistrement. Le montant d'une ligne est la quantité × le coût unitaire.

### Article {#ap.invoices.lines.cCodeProduit}

Code du produit facturé. Vide = `LINE`.

### Description {#ap.invoices.lines.cDescription}

Ce qui est facturé.

### Qté {#ap.invoices.lines.dQuantite}

Quantité facturée. Vide = 1.

### Coût unitaire {#ap.invoices.lines.dCoutUnitaire}

Prix d'une unité.

### GL {#ap.invoices.lines.cGL}

Le compte du grand livre où la ligne est imputée.

### CC1 {#ap.invoices.lines.cCC1}

Le département (centre de coûts) de la ligne, choisi dans la liste (**Grand livre > Comptes GL / Centres de coûts**, onglet **Centres de coûts**). Obligatoire quand le compte GL de la ligne a *Exige un centre de coûts*.

### CC2 {#ap.invoices.lines.cCC2}

Un sous-département du département en CC1 (la liste ne montre que les siens). Vide : le département lui-même.

### Réception {#ap.invoices.lines.iNoReception}

La réception que cette ligne facture. Enregistrer la facture marque cette réception comme facturée.

## Totaux {#ap.invoices.totals}

Sous-total (les lignes), transport, taxes et total de la facture. Tapez les taxes comme elles sont sur la facture du fournisseur : elles ne sont pas calculées ici.

### Transport {#ap.invoices.dTransport}

Frais de livraison sur la facture.

### TPS {#ap.invoices.dTotalTPS}

La TPS sur la facture.

### TVQ {#ap.invoices.dTotalTVP}

La TVQ sur la facture.
