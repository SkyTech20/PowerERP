# Factures clients {#sales.invoices}

Les factures et notes de crédit à vos clients (B2B, Québec, en CAD). Une facture commence en brouillon, est vérifiée, puis comptabilisée : c'est seulement à ce moment que le stock sort et que la facture reçoit son numéro. Les paiements ne sont pas encore suivis (pas de comptes clients).

**Où :** **Ventes > Factures**.

## Liste {#sales.invoices.list}

Colonnes : Brouillon no, Type (*Facture* ou *Note de crédit*), No de facture, Facture créditée, Date, Client, Nom, BC du client, nombre de lignes, Total et Statut.

Filtres : Statut, Type et Client. **Nouveau** crée une facture en brouillon.

## Vie d'une facture {#sales.invoices.cycle}

1. **Brouillon :** créé avec **Nouveau**. Il reçoit un numéro de brouillon (*Brouillon no*) et peut être modifié ou supprimé librement.
2. **Vérifier :** dit si la facture peut être comptabilisée et montre le stock qui va sortir. Rien n'est modifié. Voir [Vérifier](#sales.invoices.check).
3. **Comptabiliser :** sort le stock, donne le numéro définitif de la facture et verrouille le document. Une facture comptabilisée ne peut plus être modifiée ni supprimée : pour la corriger, faites une [note de crédit](#sales.invoices.creditnote). Voir [Comptabiliser](#sales.invoices.post).
4. **Imprimer :** imprime ou enregistre en PDF, en français ou en anglais. Fonctionne aussi sur un brouillon, avec le filigrane BROUILLON. Voir [Imprimer](#sales.invoices.print).

## En-tête {#sales.invoices.header}

### Facture créditée {#sales.invoices.cOrigInvoice}

Notes de crédit seulement. Le numéro de la facture que la note crédite. Lecture seule.

### Client {#sales.invoices.cCustomer}

Le client facturé. Obligatoire. Seuls les clients actifs peuvent être choisis. Au choix du client, le système propose son adresse de livraison par défaut, son entrepôt, sa langue et son terme de paiement. Sur une note de crédit, il vient de la facture et ne peut pas être changé.

### Date {#sales.invoices.dDate}

Date de la facture. Elle détermine le prix (validité de la liste de prix) et les taux de taxes.

### BC du client {#sales.invoices.cCustomerPO}

Le numéro de bon de commande du client. Imprimé sur la facture.

### Livrer à {#sales.invoices.cShipTo}

L'adresse de livraison du client. Les taxes suivent le lieu de livraison : livrer à Ottawa la marchandise d'un client du Québec donne la TVH-ON au lieu de la TPS + TVQ.

### Groupe de taxes {#sales.invoices.cTaxGroup}

Lecture seule. Le groupe de taxes de l'adresse de livraison, sinon celui du client.

### Entrepôt d'expédition {#sales.invoices.cWarehouse}

L'entrepôt d'où sort la marchandise quand la facture est comptabilisée.

### Langue des factures {#sales.invoices.cLang}

*Celle du client* (celle de la fiche client), *Français* ou *Anglais*, pour cette facture seulement. Elle fixe la langue de l'impression et des descriptions de produits sur les lignes.

### Terme de paiement {#sales.invoices.cTermCode}

Terme de paiement imprimé sur la facture. Un code `nXX` (par exemple `n30`) calcule l'échéance : date de la facture + XX jours. N'apparaît pas sur une note de crédit.

### Description du terme {#sales.invoices.cTermDesc}

Texte du terme de paiement, imprimé (par exemple *net 30 jours*). Rempli à partir du code, et modifiable.

### Notes {#sales.invoices.cNotes}

Texte imprimé sur la facture, au-dessus de la note de l'entreprise.

### Comptabilisée le {#sales.invoices.dPosted}

Date de comptabilisation. Factures comptabilisées seulement.

### Comptabilisée par {#sales.invoices.cPostedBy}

Utilisateur qui a comptabilisé la facture. Factures comptabilisées seulement.

### Coût des marchandises vendues {#sales.invoices.dCost}

Coût du stock sorti, au coût de chaque lot. Factures comptabilisées seulement.

## Lignes {#sales.invoices.lines}

Les prix, escomptes, taxes et totaux sont recalculés à la saisie.

### Produit {#sales.invoices.lines.cProduct}

Un produit vendable et actif. Le choisir remplit la description, l'unité, le prix et l'escompte du client.

### Description {#sales.invoices.lines.cDescription}

Vient du produit, dans la langue de la facture. Modifiable.

### Quantité {#sales.invoices.lines.dQty}

Quantité vendue, dans l'unité de la ligne.

### Unité {#sales.invoices.lines.cUOM}

Remplie avec l'unité de vente du produit. La liste ne montre que les unités du produit : son unité de stock, ses emballages et les conversions générales de l'unité de stock (par exemple KG, G et LB pour la farine).

### Prix unitaire {#sales.invoices.lines.dPrice}

Le prix du client : celui de sa liste de prix, sinon le Prix 1 du produit. Un prix tapé à la main est conservé. Changer le produit, la quantité ou l'unité reprend le prix du client.

### Escompte % {#sales.invoices.lines.dDiscountPct}

L'escompte du client : celui de la ligne de la liste de prix, sinon de la catégorie dans la liste, sinon du client. Un escompte tapé à la main est conservé.

### Prix net {#sales.invoices.lines.dNetPrice}

Prix × (1 − escompte %). Calculé. Sous le *Prix minimum* du produit, la facture ne peut pas être enregistrée.

### Montant {#sales.invoices.lines.dAmount}

Quantité × prix net. Calculé.

### Taxe {#sales.invoices.lines.cTaxGroup}

Groupe de taxes de la ligne : celui de la facture, sauf pour les produits détaxés (par exemple le pain, groupe ZERO), qui gardent le leur.

### Retour {#sales.invoices.lines.lReturn}

Notes de crédit seulement. Cochée : la marchandise revient en stock, dans le même lot, la même date d'expiration, le même numéro de série et le même emplacement d'où elle est sortie, au coût de sortie. Décochée : seul le prix est crédité (ajustement de prix) et rien ne revient en stock. Seulement pour les produits stockés.

## Totaux {#sales.invoices.totals}

- **Escomptes accordés :** ce que le client a économisé avec les escomptes.
- **Sous-total :** somme des lignes.
- **Taxes :** une ligne par taxe (TPS, TVQ, TVH...), calculée sur le total des lignes de chaque groupe de taxes, à la date de la facture.
- **Total.**

## Boutons {#sales.invoices.buttons}

### Enregistrer {#sales.invoices.save}

Enregistre le brouillon. Refusé quand le prix net d'une ligne est sous le prix minimum du produit.

### Vérifier {#sales.invoices.check}

Affiche *Prête à comptabiliser* ou *À corriger avant de comptabiliser*, avec les problèmes (par exemple stock insuffisant à la ligne 1, facture sans lignes, aucun entrepôt). Affiche aussi *Stock à sortir* : quel lot, numéro de série et emplacement vont sortir, dans l'ordre de sortie de chaque produit (FEFO, PEPS ou DEPS). Un lot expiré n'est jamais vendu. Rien n'est modifié.

### Comptabiliser {#sales.invoices.post}

Demande une confirmation, vérifie de nouveau et comptabilise. Si quelque chose échoue, rien ne sort du stock. Après la comptabilisation, la facture est en lecture seule et *Stock sorti* montre le coût de chaque ligne.

### Imprimer {#sales.invoices.print}

Ouvre la page d'impression, pour imprimer ou enregistrer en PDF à partir du navigateur. La langue est celle de la facture; pour en forcer une, ajoutez `?lang=en` ou `?lang=fr` à l'adresse de la page.

### Note de crédit {#sales.invoices.credit}

Factures comptabilisées seulement. Fait une note de crédit à partir de la facture : voir [Note de crédit](#sales.invoices.creditnote).

### Supprimer {#sales.invoices.delete}

Brouillons seulement. Un brouillon supprimé n'utilise pas de numéro de facture, puisque le numéro est donné à la comptabilisation.

## Numérotation {#sales.invoices.numbers}

- Brouillons : *Brouillon no* 1, 2, 3...
- Factures comptabilisées : 1, 2, 3... ou à partir du numéro de *Les numéros de facture commencent à* (**Administration > Paramètres système > Profil de l'entreprise**).
- Notes de crédit comptabilisées : NC-1, NC-2...

## Note de crédit {#sales.invoices.creditnote}

Sert à reprendre de la marchandise, ou à accorder une réduction de prix, sur une facture déjà comptabilisée.

**Comment :** ouvrez la facture comptabilisée, cliquez sur **Note de crédit** et confirmez. Une note de crédit en brouillon s'ouvre avec toutes les lignes de la facture pas encore créditées.

Ce qui change par rapport à une facture :

- *Facture créditée* montre le numéro de la facture.
- Client, Livrer à, Entrepôt d'expédition et Groupe de taxes viennent de la facture et ne peuvent pas être changés. Il n'y a pas de terme de paiement.
- Chaque ligne crédite une ligne de la facture, au prix et à l'escompte de la facture sauf si vous en tapez d'autres. La quantité ne peut pas dépasser ce qui a été facturé et pas encore crédité. Vous pouvez supprimer des lignes ou baisser des quantités. Un produit qui n'est pas sur la facture est refusé.
- *Retour* décide si la marchandise revient en stock : voir [Retour](#sales.invoices.lines.lReturn).

À la comptabilisation, la note reçoit le numéro NC-n et le panneau montre *Stock remis*. **Inventaire > Mouvements de stock** montre un ajustement ADJ positif avec le document SO NC-n. La facture d'origine reste comptabilisée, avec le même numéro.

Cliquer de nouveau sur **Note de crédit** sur la facture ne reprend que ce qui reste à créditer. Quand tout est crédité : *Toutes les lignes de cette facture sont déjà créditées*.

L'impression indique NOTE DE CRÉDIT / CREDIT NOTE, avec le numéro NC-n et la ligne *Facture créditée / Invoice credited*.

## Messages d'erreur fréquents {#sales.invoices.errors}

| Message | Cause |
|---|---|
| Le prix net est sous le prix minimum du produit | Le prix net de la ligne est plus bas que le *Prix minimum* du produit. |
| Stock disponible insuffisant | L'entrepôt n'a pas la quantité (les lots expirés ne comptent pas). |
| Plus que la quantité facturée et pas encore créditée | Une note de crédit avec une quantité au-dessus de ce qui reste sur la ligne de la facture. |
| Ce produit n'est pas sur la facture créditée | Une note de crédit avec un produit qui n'était pas sur la facture. |
| Seule une facture comptabilisée peut être créditée | Tentative de créditer un brouillon. |
| Ce produit n'est pas vendu | Le produit a *Vendable* décoché ou n'est pas actif. |
| Toutes les lignes de cette facture sont déjà créditées | La facture est entièrement créditée. |
