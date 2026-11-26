# Paramètres système {#admin.settings}

Le profil de l'entreprise imprimé sur les factures, les données de démonstration et l'entretien des données. Seul le rôle administrateur voit cet écran.

**Où :** **Administration > Paramètres système**.

## Profil de l'entreprise {#admin.settings.company}

Tout ce qui est ici est imprimé en haut des factures et des notes de crédit. **Enregistrer** garde les changements ; ils comptent pour les prochaines impressions, y compris celles des factures déjà comptabilisées.

### Nom {#admin.settings.cName}

Le nom usuel de l'entreprise. Obligatoire.

### Raison sociale {#admin.settings.cLegalName}

Le nom légal. Quand il est rempli, c'est lui qui est imprimé sur la facture.

### Adresse ligne 1 {#admin.settings.cAddress1}

Adresse de l'entreprise sur la facture. Il en va de même pour les champs suivants.

### Adresse ligne 2 {#admin.settings.cAddress2}

Deuxième ligne de l'adresse.

### Ville {#admin.settings.cCity}

Ville de l'entreprise.

### Province / État {#admin.settings.cProvince}

Province de l'entreprise (par exemple QC).

### Code postal {#admin.settings.cZipCode}

Code postal de l'entreprise.

### Pays {#admin.settings.cCountry}

Pays de l'entreprise.

### Téléphone {#admin.settings.cPhone}

Imprimé sous l'adresse.

### Courriel {#admin.settings.cEmail}

Imprimé sous l'adresse.

### Site web {#admin.settings.cWebsite}

Imprimé sous l'adresse.

### Numéro d'entreprise du Québec (NEQ) {#admin.settings.cNEQ}

Le numéro d'entreprise du Québec, imprimé à côté des numéros de taxes.

### Les numéros de facture commencent à {#admin.settings.iInvoiceStart}

Le premier numéro de facture. Vide ou 0 commence à 1. Avec 1001, la prochaine facture comptabilisée reçoit 1001. Ne compte que pour la suite : les factures déjà comptabilisées ne sont pas renumérotées.

### Note de facture (français) {#admin.settings.cInvoiceNoteFR}

Texte au bas de la facture pour les clients francophones (par exemple les conditions de paiement, les coordonnées bancaires, un remerciement).

### Note de facture (anglais) {#admin.settings.cInvoiceNoteEN}

La même chose pour les clients anglophones.

### Numéros d'inscription aux taxes {#admin.settings.taxNumbers}

Les numéros de TPS / TVH et de TVQ ne sont pas tapés ici. Ils viennent des codes de taxe dans **Administration > Taxes** (le numéro d'inscription de chaque taxe) et sont affichés ici seulement pour vérification.

## Données de démonstration {#admin.settings.demo}

### Jeu de données {#admin.settings.scenario}

Les données de démonstration à charger :

- *Produits de l'érable* (par défaut) : Érablière Démo inc., une usine de Saint-Georges (Beauce) qui achète le sirop d'érable en barils à trois érablières et fabrique du sirop en cannes et en bouteilles, du beurre d'érable, des bonbons d'érable et du sucre à la crème. Elle s'ouvre avec deux mois d'historique (octobre et novembre 2026) : ordres de fabrication faits et fermés, étapes des recettes enregistrées (Brix, températures de cuisson et de remplissage), factures reportées et une note de crédit, lots retenus et non-conformités. Chaque baril est un lot dont le lot du fournisseur est le numéro du baril du producteur et la date de récolte : **Production > Lots et traçabilité** suit une canne vendue jusqu'à son érablière, et **Rapports > Indicateurs de la chaîne d'approvisionnement** a une valeur pour chaque indicateur.
- *SkyAI* (achats, sans production).
- *Fabrication* (papier, boulangerie, métal).

**↺ Réinitialiser les données** charge le jeu choisi, après une confirmation. Toutes les modifications faites depuis sont perdues. Le jeu choisi est conservé au redémarrage de l'ERP. Les rôles d'exemple SALES, PRODUCTION et WAREHOUSE sont remis comme dans la démo ; les rôles que vous avez créés ne sont pas touchés.

## Vider toutes les données {#admin.settings.clear}

**🗑 Vider toutes les données** supprime toutes les données, après une confirmation : comptes GL, centres de coûts, fournisseurs, produits, stock, bons de commande, réceptions, factures, production, clients et profil de l'entreprise. Les utilisateurs et les paramètres sont conservés. **Réinitialiser les données** ramène la démo.
