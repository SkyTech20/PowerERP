# Indicateurs de la chaîne d'approvisionnement {#rep.scor}

Les chiffres qui disent comment va la chaîne d'approvisionnement sur une période, groupés par les quatre attributs de performance SCOR : **fiabilité**, **réactivité**, **coût** et **actifs**. Ils répondent à ISO 9001 9.1 (surveillance, mesure, analyse et évaluation) et donnent ses données à la revue de direction. Rien n'est saisi ici : chaque chiffre est calculé à partir des factures, réceptions, ordres de fabrication, enregistrements d'atelier, non-conformités et mouvements de stock déjà dans l'ERP.

**Où :** **Rapports > Indicateurs de la chaîne**. L'écran est en lecture seule ; il demande la permission *Voir* de l'écran.

## Période {#rep.scor.period}

Les jours sur lesquels les chiffres sont calculés : les 30 derniers jours, les 90 derniers jours (par défaut), les 12 derniers mois, cette année, ou **Autres dates** (saisies dans *Du* et *Au*). Le nombre de jours de la période est affiché à droite. La valeur du stock, les lots et les non-conformités ouvertes sont toujours ceux d'aujourd'hui.

## Du {#rep.scor.from}

Le premier jour de la période. Le changer choisit *Autres dates*.

## Au {#rep.scor.to}

Le dernier jour de la période (aujourd'hui par défaut). Un début après la fin est refusé.

## Lots qui expirent dans {#rep.scor.horizon}

Jusqu'où les lots qui expirent sont montrés (7 à 90 jours, 30 par défaut) : le chiffre *Lots qui expirent* et la liste *Expirés ou qui expirent dans*. Les lots déjà expirés sont toujours montrés.

## Fiabilité {#rep.scor.reliability}

Bien faire : le bon produit, la bonne quantité, la bonne qualité, à temps. Chaque chiffre montre de quoi il est fait (par exemple *2 sur 3 factures*) ; un tiret veut dire qu'il n'y a rien à mesurer sur la période.

- **Commandes parfaites :** les factures de vente comptabilisées de la période qu'aucune note de crédit ne crédite. Une facture avec une note de crédit a eu un problème (quantité, prix, produit erroné, ou marchandise retournée).
- **Production à temps :** les ordres de fabrication terminés sur la période à leur échéance ou avant. Les ordres sans échéance sont laissés de côté.
- **Rendement de production :** la quantité fabriquée / la quantité de l'ordre, des ordres terminés sur la période.
- **Taux de service fournisseurs :** la quantité reçue / la quantité commandée sur les réceptions de la période (une ligne compte au plus ce qui a été commandé).
- **Réceptions sans problème :** les réceptions de la période sans non-conformité trouvée à la réception (une non-conformité avec *Trouvée à* Réception et le numéro de la réception dans *Document*).
- **Étapes bonnes du premier coup :** les enregistrements des étapes de recette à l'atelier dans leurs limites, sur la période.

## Réactivité {#rep.scor.responsiveness}

La vitesse à laquelle les choses passent.

- **Délai de production :** les jours du lancement à la fin des ordres terminés sur la période, en moyenne.
- **Délai de fermeture des non-conformités :** les jours de la création à la fermeture des non-conformités fermées sur la période, en moyenne.

## Coût {#rep.scor.cost}

- **Écart de coût de production :** (coût réel − coût estimé de la quantité fabriquée) / coût estimé, des ordres fermés sur la période. Au-dessus de 0 : les ordres ont coûté plus que prévu.
- **Marge brute :** (ventes − coût des produits vendus) / ventes, des factures comptabilisées sur la période, avant taxes. Les notes de crédit se soustraient.

## Actifs {#rep.scor.assets}

Le stock : combien il y en a, à quelle vitesse il tourne et ce qui est à risque.

- **Valeur du stock :** le stock d'aujourd'hui dans tous les entrepôts, au coût unitaire de chaque produit (comme dans **Inventaire > Valeur des stocks**).
- **Rotation du stock :** la valeur du stock utilisé sur la période (sorti pour les factures de vente et les ordres de fabrication), comptée sur un an, / la valeur du stock. 12 veut dire que le stock est utilisé environ une fois par mois.
- **Jours de couverture :** la valeur du stock / la valeur utilisée par jour sur la période : combien de jours le stock dure à ce rythme.
- **Lots retenus :** la valeur des lots en stock en attente, en quarantaine ou rejetés (**Qualité > Statut des lots**).
- **Lots qui expirent :** la valeur des lots en stock expirés ou qui expirent dans l'horizon.

Cliquez sur un chiffre pour ouvrir l'écran derrière lui (quand le rôle le peut).

## Lots à surveiller {#rep.scor.lots}

Deux listes : les lots en stock expirés ou qui expirent dans l'horizon (les plus proches d'abord, en rouge quand il reste 7 jours ou moins), et les lots retenus par la qualité (la plus grande valeur d'abord). Cliquez sur un lot pour le tracer dans **Production > Lots et traçabilité**.

## Non-conformités {#rep.scor.nc}

Combien de non-conformités ont été trouvées sur la période et combien sont ouvertes aujourd'hui, par endroit où elles ont été trouvées (réception, production, contrôle interne, plainte client) et par gravité.

## Stock par produit {#rep.scor.products}

Les produits en stock avec leur quantité, leur valeur, la valeur utilisée sur la période, les jours de couverture et le dernier jour où le stock est sorti. Les produits non utilisés sur la période viennent d'abord (*Non utilisé* : le stock qui ne tourne pas), puis ceux qui ont le plus de jours de couverture. Les 15 premiers sont affichés ; cliquez sur l'un pour l'ouvrir.

## Écarts à l'atelier {#rep.scor.deviations}

Les valeurs hors limites enregistrées sur les étapes des ordres de fabrication sur la période, les plus récentes d'abord : quand, l'ordre, l'étape, la valeur et pourquoi elle était hors limites, son effet (bloque, retient le lot, avertissement), l'action corrective et qui. Cliquez sur une ligne pour ouvrir l'ordre.
