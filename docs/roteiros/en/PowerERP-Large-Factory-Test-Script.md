# PowerERP — A factory from scratch with three warehouses: test script

A script to test the whole ERP **starting from nothing**, like a new customer: company setup (with the logo), chart of accounts and cost centers, taxes, units, three warehouses with aisles, racks and levels, suppliers, products, recipes, purchasing, receptions, two-stage production, quality, sales, a credit note and traceability back to the supplier.

The factory is **Les Aliments Nordiques inc.**, in Lévis (QC). It buys frozen strawberries, sugar, pectin and packaging, cooks a **strawberry puree** (the semi-finished product) and uses it for **two finished products**: strawberry jam in a 250 ml jar and strawberry fruit jellies in a 200 g pouch.

| Warehouse | For | Locations (zone-aisle-rack-level) |
|---|---|---|
| **MP** | Raw materials and packaging | R-A-01-1 to R-B-03-3 (2 aisles × 3 racks × 3 levels = 18) + QUAI (receiving) |
| **INT** | Semi-finished goods (puree) | T-A-01 to T-A-04 (4 tanks) |
| **PF** | Finished goods | F-A-01-1 to F-B-04-2 (2 aisles × 4 racks × 2 levels = 16) + EXPED (shipping) |

Screen labels are in English, as the ERP shows them with the **EN** button. The expected values were checked in the ERP on 2026-11-28. Use the dates given (December 1 to 3, 2026) to get the same expiry dates.

**Before you start:** log in as an administrator. Have a logo image at hand (PNG, JPEG, GIF or WEBP, 5 MB at most).

---

## 0. Start from scratch

| Step | Expected |
|---|---|
| **Administration > System settings**, card *Data*, **Clear all data** and confirm | "All data cleared." Users, roles and settings are kept. |
| **Inventory > Products**, **Suppliers**, **GL Accounts / Cost Centers** | Empty lists. |

> Production order, nonconformance and credit note numbers carry on from where they were (they are never reused, not even after clearing). Write down the number the ERP gives and use it in the next steps. Invoices start again at the number set on the company.

## 1. The company and the logo

**Administration > System settings**, card *Company*

| Field | Value |
|---|---|
| *Name* | Aliments Nordiques |
| *Legal name* | Les Aliments Nordiques inc. |
| Address | 2400, boulevard de la Rive-Sud, Lévis, QC, G6W 6N9, CA |
| *Phone* / *E-mail* / *Website* | 418 555-0700 / factures@aliments-nordiques.ca / www.aliments-nordiques.ca |
| *Quebec enterprise number (NEQ)* | 1170000099 |
| *Invoice numbers start at* | 5001 |
| *Invoice note (French)* | Merci de votre confiance ! Paiement par virement : voir les coordonnées au verso. |
| *Invoice note (English)* | Thank you for your business! Payment by bank transfer: see the details overleaf. |

| Step | Expected |
|---|---|
| **Save** | "Company profile saved." |
| *Logo* shows "No logo". **Choose an image…** and pick a .pdf or .txt file | Refused: "This file is not an image the ERP can read (use PNG, JPEG, GIF or WebP)." |
| Pick an image over 5 MB | Refused: "The image is too big (5 MB at most)." |
| Pick the right logo | "Logo saved." The preview shows; the button becomes **Change the logo…** and **Remove the logo** appears. A large image is made smaller (it fits 600 × 240) and turned upright like the photo. |
| Reload the page (F5) | The logo is still there. |
| **Remove the logo**, confirm, then pick it again | It goes ("No logo") and comes back. Keep the logo for the rest of the script. |
| The card's **?** icon | The help says where the logo is printed (invoices, credit notes and the traceability Excel file). |

## 2. Chart of accounts (GL accounts)

**General Ledger > GL Accounts / Cost Centers**, tab *GL accounts*, **New** for each account. Leave *Type* empty: the ERP suggests it from the first digit.

| Account | Description (French) | Description (English) | Requires a cost center |
|---|---|---|---|
| 1100 | Banque | Bank | |
| 1310 | Stock - matières premières | Inventory - raw materials | |
| 1320 | Stock - produits semi-finis | Inventory - semi-finished goods | |
| 1330 | Stock - produits finis | Inventory - finished goods | |
| 2100 | Comptes fournisseurs | Accounts payable | |
| 2310 | TPS à recevoir | GST receivable | |
| 2320 | TVQ à recevoir | QST receivable | |
| 2330 | TPS à payer | GST payable | |
| 2340 | TVQ à payer | QST payable | |
| 4100 | Ventes - confitures | Sales - jams | |
| 4200 | Ventes - confiseries | Sales - confectionery | |
| 5100 | Achats - matières premières | Purchases - raw materials | |
| 5110 | Achats - emballages | Purchases - packaging | |
| 5200 | Coût des produits vendus | Cost of goods sold | |
| 5700 | Entretien et réparations | Maintenance and repairs | ✔ |

| Step | Expected |
|---|---|
| List | 15 accounts with a coloured type: 1xxx *Asset*, 2xxx *Liability*, 4xxx *Revenue*, 5xxx *Expense*. Filters *Type* and *Active*. |
| **EN**/**FR** button | The description changes language. |
| Open 5700 | *Requires a cost center* ticked. |
| Create 1100 again | Refused: the code already exists. |

## 3. Cost centers (department and sub-department)

The GL account and the cost center are **independent**: neither sits inside the other. They only meet on the line of a purchase (supplier invoice or reception): the account says **what** (e.g. 5700 maintenance), the cost center says **who** spent it (e.g. 200-210 cooking).

Tab *Cost centers*:

| Department (CC1) | Sub-department (CC2) | Description (French) | Description (English) |
|---|---|---|---|
| 100 | | Administration | Administration |
| 200 | | Production | Production |
| 200 | 210 | Cuisson (purée) | Cooking (puree) |
| 200 | 220 | Remplissage et emballage | Filling and packing |
| 300 | | Entrepôts | Warehouses |
| 400 | | Ventes | Sales |
| 500 | | Qualité | Quality |

| Step | Expected |
|---|---|
| For 210 and 220: open 200 and use **＋ Sub-department** | A new form with *Department* 200 already filled. |
| List | A tree: 200 Production and, under it, ↳ 210 and ↳ 220. |
| Create 600 / 610 (a sub-department without its department) | "Create the department (CC1 alone) first, then its sub-departments." |
| Delete 200 | Refused: it has sub-departments. |

## 4. Taxes

**Administration > Taxes**

| Step | Value / expected |
|---|---|
| *Tax code* TPS | *Kind* GST, jurisdiction CA, number 701234567 RT0001, GL collected 2330, GL recoverable 2310, 100 % recoverable, rate 5 % from 2008-01-01. |
| *Tax code* TVQ | *Kind* PST, jurisdiction QC, number 1201234567 TQ0001, GL 2340 / 2320, rate 9.975 % from 2013-01-01. |
| *Tax group* QC | Québec - TPS + TVQ, *Treatment* Taxable, lines TPS and TVQ (no tax on tax). |
| *Tax group* ZERO | Détaxé (aliments de base), *Treatment* Zero-rated, no lines. |
| Calculate $100.00 with group QC | TPS 5.00 + TVQ 9.98 = $114.98. |
| **Administration > System settings**, *Tax registration numbers* | The TPS and TVQ numbers show (they are printed on the invoice). |

## 5. Units and categories

**Inventory > Categories / units**

| Step | Value |
|---|---|
| Units | KG (Kilogramme / Kilogram, weight), G (Gramme / Gram, weight), UN (Unité / Each, count). |
| Conversion | 1 KG = 1000 G. |
| Categories | RAW Matières premières / Raw materials; PACK Emballages / Packaging; WIP Produits semi-finis / Semi-finished products; FG Produits finis / Finished products. |

## 6. Warehouses and locations (aisle, rack, level)

**Inventory > Warehouses / locations**, **New** for each warehouse (factory address, *Type* Main, *Uses locations* ticked):

| Code | Name (French) | Name (English) |
|---|---|---|
| MP | Entrepôt des matières premières | Raw materials warehouse |
| INT | Entrepôt des produits semi-finis | Semi-finished goods warehouse |
| PF | Entrepôt des produits finis | Finished goods warehouse |

| Step | Expected |
|---|---|
| Open MP | Two tabs: *General* and *Locations*. The *Locations* tab says "No location yet…". |
| Tab *Locations*, card *Generate locations*: *Zone* R, *Aisle* A to B, *Rack* 01 to 03, *Level* 1 to 3, *Type* Reserve, **Preview** | "18 location(s) will be created.": R-A-01-1, R-A-01-2 … R-B-03-3. Nothing is saved yet. |
| **Create** | 18 locations in the tab's list, in picking order (10, 20, 30…). |
| **Create** again with the same values | None new: the 18 show as already existing and skipped. |
| *Aisle* A to Z, *Rack* 01 to 99, *Level* 1 to 9 | Refused: "Too many locations at once (2000 at most): make smaller ranges." |
| *Rack* 03 to 01 | Refused: "Invalid range: … the first one not after the last." |
| **New location** (in the tab): QUAI, "Quai de réception", *Type* Receiving, mixed products allowed | Back on MP's *Locations* tab with QUAI in the list. **Back** from a location always returns to its warehouse. |
| MP's *General* tab: *Receiving location* QUAI, **Save** | Saved. |
| INT: *Zone* T, *Aisle* A, *Rack* 01 to 04, no *Level*, *Type* Picking | 4 locations: T-A-01 to T-A-04. *Receiving location* T-A-01. |
| PF: *Zone* F, *Aisle* A to B, *Rack* 01 to 04, *Level* 1 to 2, *Type* Reserve | 16 locations: F-A-01-1 to F-B-04-2. |
| PF: **New location** EXPED, "Quai d'expédition", *Type* Shipping | *Shipping location* EXPED, *Receiving location* F-A-01-1. |
| A warehouse with more than 10 locations | The search box shows: typing "B-02" filters the list. |

## 7. Suppliers

**Accounts Payable > Suppliers**, all in QC, CA, *Payment term* n30 (net 30 jours):

| Code | Name | Address | TPS number | TVQ number |
|---|---|---|---|---|
| FERME-ORLEANS | Ferme de l'île d'Orléans | 1830, chemin Royal, Saint-Laurent-de-l'Île-d'Orléans, G0A 3Z0 | 811111111RT0001 | 1211111111TQ0001 |
| SUCRES-LAUR | Sucres Laurentiens inc. | 500, rue des Raffineurs, Montréal, H1B 2C3 | 822222222RT0001 | 1222222222TQ0001 |
| EMBAL-QC | Emballages Québec ltée | 75, rue Industrielle, Saint-Hyacinthe, J2R 1C4 | 833333333RT0001 | 1233333333TQ0001 |

## 8. Products

**Inventory > Products**. All physical, stocked, average cost, CAD. Those with lots have *Lot numbers* and expiry ticked, *Stock out order* FEFO.

| Code | Class | Cat. | Description (FR / EN) | Unit | Warehouse | Tax | Lot / shelf life (days) | Supplier and price | GL |
|---|---|---|---|---|---|---|---|---|---|
| FRAISE-IQF | Raw material | RAW | Fraises surgelées IQF / Frozen IQF strawberries | KG | MP | ZERO | yes / 365 | FERME-ORLEANS 4.20 | purchase 5100, inventory 1310 |
| SUCRE | Raw material | RAW | Sucre granulé / Granulated sugar | KG | MP | ZERO | yes / 730 | SUCRES-LAUR 1.10 | 5100 / 1310 |
| PECTINE | Raw material | RAW | Pectine de pomme / Apple pectin | KG | MP | ZERO | yes / 730 | SUCRES-LAUR 18.00 | 5100 / 1310 |
| POT-250 | Raw material | PACK | Pot en verre 250 ml / Glass jar 250 ml | UN | MP | QC | no | EMBAL-QC 0.38 | 5110 / 1310 |
| COUV-63 | Raw material | PACK | Couvercle 63 mm / Lid 63 mm | UN | MP | QC | no | EMBAL-QC 0.09 | 5110 / 1310 |
| ETIQ-CONF | Raw material | PACK | Étiquette confiture / Jam label | UN | MP | QC | no | EMBAL-QC 0.04 | 5110 / 1310 |
| SACHET-200 | Raw material | PACK | Sachet refermable 200 g / Resealable pouch 200 g | UN | MP | QC | no | EMBAL-QC 0.12 | 5110 / 1310 |
| PUREE-FRAISE | Kit/Assembly | WIP | Purée de fraises cuite / Cooked strawberry puree | KG | INT | ZERO | yes / 30 | (not bought) | inventory 1320 |
| CONF-FRAISE-250 | Finished product | FG | Confiture de fraises, pot 250 ml / Strawberry jam, 250 ml jar | UN | PF | ZERO | yes / 540 | sales price 4.25 | sales 4100, inventory 1330, COGS 5200 |
| PATE-FRUIT-200 | Finished product | FG | Pâtes de fruits aux fraises, sachet 200 g / Strawberry fruit jellies, 200 g pouch | UN | PF | QC | yes / 365 | sales price 5.50 | 4200 / 1330 / 5200 |

| Step | Expected |
|---|---|
| List | 10 products. |
| On a product, *GL - inventory* 9999 | Only existing accounts are accepted (the chart of accounts list). |

## 9. Shop floor and recipes

**Production > Calendars**: USINE-1X5, "Usine : 1 équipe, lundi au vendredi", Monday to Friday, shift JOUR 07:00–15:30, 30 min break.

**Production > Work centers**:

| Code | Description | Type | Warehouse | Setup/run rate (h) | Burden (h) | Cost center |
|---|---|---|---|---|---|---|
| CUISSON | Marmites de cuisson / Cooking kettles | Machine | INT | 40 | 15 | 200-210 |
| REMPLISSAGE | Ligne de remplissage / Filling line | Machine | PF | 35 | 15 | 200-220 |

**Production > Standard operations** (all *min per lot*, reporting point):

| Code | Description | Work center | Setup (min) | Run (min) | Crew |
|---|---|---|---|---|---|
| CUIRE | Cuire la purée / Cook the puree | CUISSON | 20 | 90 | 1 |
| REMPLIR | Remplir et capsuler les pots / Fill and cap the jars | REMPLISSAGE | 15 | 60 | 2 |
| MOULER | Couler, sécher et ensacher / Pour, dry and bag | REMPLISSAGE | 15 | 120 | 2 |

**Production > Manufactured items**: PUREE-FRAISE, CONF-FRAISE-250 and PATE-FRUIT-200 with *Make or buy* = Make and lot tracing.

**Production > Recipes**, revision A, *Batch*, then **Submit** and **Approve**:

| Recipe | Base | Materials (operation 10) | Steps |
|---|---|---|---|
| PUREE-FRAISE | 100 KG | FRAISE-IQF 105 KG, manual, from MP. Note: "100 kg de purée : 105 kg de fraises (5 % d'évaporation)." | 10 *Material add* "Verser les fraises (lire le lot)"; 20 *Measure* "Température de cuisson (85 °C ou plus)", TEMP_CUISSON °C, target 90, min 85, max 98, required, **critical**, out of limits **holds the lot** |
| CONF-FRAISE-250 | 100 UN | PUREE-FRAISE 15 KG (from **INT**), SUCRE 12 KG, PECTINE **300 G** (manual, from MP); POT-250, COUV-63, ETIQ-CONF 100 UN each, *backflush* | 10 *Measure* "Brix de la confiture (61 à 65)", BRIX, target 63, critical, **blocks**; 20 *Check* "Pots bien scellés", critical, blocks |
| PATE-FRUIT-200 | 100 UN | PUREE-FRAISE 10 KG (INT), SUCRE 11 KG, PECTINE 600 G; SACHET-200 100 UN *backflush* | — |

| Step | Expected |
|---|---|
| PECTINE in G while the stock is in KG | Accepted thanks to the conversion 1 KG = 1000 G (it becomes 0.3 KG on the order). |
| Cost of the PUREE-FRAISE recipe (100 KG) | Materials $441.00 (105 × 4.20), operations $95.83, total $536.83 = 5.3683 / KG. |
| Recipe list | All three *Approved*. |

## 10. Purchasing and receptions

**Purchasing > Purchase orders** (date 2026-11-30):

| PO | Supplier | Lines | Subtotal |
|---|---|---|---|
| PO-1001 | FERME-ORLEANS | FRAISE-IQF 400 KG × 4.20 | $1,680.00 |
| PO-1002 | SUCRES-LAUR | SUCRE 500 KG × 1.10; PECTINE 10 KG × 18.00 | $730.00 |
| PO-1003 | EMBAL-QC | POT-250 1200 × 0.38; COUV-63 1200 × 0.09; ETIQ-CONF 1200 × 0.04; SACHET-200 600 × 0.12 | $684.00 |

**Purchasing > Receptions** (date 2026-12-01, *Warehouse* MP). Type the location and the supplier lot on each line:

| Reception | PO | Lines (location, supplier lot) |
|---|---|---|
| 700001 | PO-1001 | FRAISE-IQF 200 KG in R-A-01-1 (IO-2611-A) and another 200 KG in R-A-01-2 (IO-2611-B) |
| 700002 | PO-1002 | SUCRE 500 KG in R-A-02-1 (SL-88231); PECTINE 10 KG in R-A-02-2 (PC-5512) |
| 700003 | PO-1003 | POT-250 in R-B-01-1, COUV-63 in R-B-01-2, ETIQ-CONF in R-B-01-3, SACHET-200 in R-B-02-1 |

| Step | Expected |
|---|---|
| Reception line: *Department* 999 | "Unknown or inactive cost center on a line". The field only lists active centers; *Sub-department* only lists those of the department picked. |
| **Check** of 700001 | No problem: lots 700001-1 and 700001-2, expiry 2027-12-01 (365 days), $4.20/KG. |
| **Post** all three | They go into the stock. |
| **Inventory > Stock on hand** | Each lot in its location: FRAISE-IQF 200 in R-A-01-1 and 200 in R-A-01-2, SUCRE 500, PECTINE 10, jars, lids and labels 1200, pouches 600. |
| **Inventory > Products**, FRAISE-IQF | Average cost **$4.20** (two lines of the same product in the same reception keep the average). |
| **Inventory > Inventory valuation** | $3,094.00 (1,680 + 730 + 684). |

## 11. Supplier invoice: account and cost center

**Accounts Payable > Invoices**, **New**, supplier SUCRES-LAUR, one expense line without a product (e.g. "Réparation brûleur", 1 × 250.00):

| Step | Expected |
|---|---|
| *GL* 5700 without a cost center, **Save** | "This GL account requires a cost center on the line" (line 1). |
| *GL* 9999 | "Unknown or inactive GL account on a line". |
| *Department* 200, *Sub-department* 210 | Saved. The *Sub-department* list only shows 210 and 220. |
| Deactivate center 500 (*Active* unticked) and open the *Department* list on a line | 500 is not listed any more. Activate it again afterwards. |

## 12. Making the puree (INT) and the temperature deviation

**Production > Production orders**, **New**: PUREE-FRAISE 100 KG, *Warehouse* INT, start and due 2026-12-02.

| Step | Expected |
|---|---|
| Card *Materials* | FRAISE-IQF 105 KG from MP. Estimated cost $536.83 (5.3683 / KG). |
| **Save**, **Release**, **Show the lots** | 105 KG of lot 700001-1 (R-A-01-1). |
| **Issue** | Materials issued. |
| Step 10 (pour) and step 20 temperature **92** | Within the limits. |
| **Report**: *Quantity made* 100, *Location* T-A-01 | Lot MO&lt;n&gt; (e.g. MO16), 30-day expiry, cost 5.3683 / KG. |
| **Complete** and **Close** | Actual cost $536.83: materials 441.00 + operations 95.83. |
| A second identical order; temperature **81** with the comment "Brûleur 2 en panne"; *Quantity made* 98 in T-A-02 | The step is out of its limits and the new lot goes **on hold automatically**. Lots used: 95 KG of 700001-1 and 10 KG of 700001-2 (FEFO). Actual cost $534.91 = 5.4583 / KG (98 KG made). |
| **Quality > Lot status** | The second order's lot *On hold*, reason "Order &lt;n&gt;, step 10/20 Cooking temperature (85 °C or more): 81 °C". |

## 13. Quality: nonconformance

**Quality > Nonconformances**, **New**:

| Field | Value |
|---|---|
| *Source* / *Ref* | Production / the second order's lot |
| *Product* / *Lot* / *Qty* | PUREE-FRAISE / MO&lt;n&gt; / 98 KG |
| *Severity* | Major |
| *Description* | Température de cuisson 81 °C (minimum 85 °C). |
| *Cause* | Brûleur 2 en panne. |
| *Disposition* | Scrap |
| *Action* | Brûleur réparé; vérification du brûleur ajoutée à l'entretien hebdomadaire. |

| Step | Expected |
|---|---|
| **Save** | An open NC, with its number. |
| **Quality > Lot status**, the lot, change to *Rejected* with the reason "NC &lt;n&gt; : cuisson à 81 °C, lot détruit." | History: Released → On hold → Rejected. |
| **Close** the NC | *Closed*, *Disposition* Scrap. |

## 14. Finished products (PF)

| Order | Steps | Expected |
|---|---|---|
| CONF-FRAISE-250 100 UN, *Warehouse* PF | Materials | PUREE-FRAISE 15 KG from INT, SUCRE 12 KG, PECTINE 0.3 KG, jars, lids and labels 100 UN. Estimated cost $208.87. |
| | **Show the lots** | The puree comes from the **good** lot (the first order's, in T-A-01). The rejected lot is never used. |
| | **Issue**; Brix 60 without a comment | "The value is out of its limits: write the corrective action". With the comment "Trop liquide" it is saved, but **Report** refuses: "A critical step is out of its limits: record it again within its limits first". |
| | Brix 63; *Pots bien scellés* = Yes; **Report** 100 in F-A-01-1 | Lot MO&lt;n&gt;, 540-day expiry. Jars, lids and labels go out by themselves (*backflush*). |
| | **Complete**, **Close** | Actual $208.87: materials 150.12 + operations 58.75 = 2.0887 / UN. |
| PATE-FRUIT-200 100 UN, PF | **Report** 100 in F-B-01-1 | Actual $197.33: materials 88.58 + operations 108.75 = 1.9733 / UN. |
| **Inventory > Stock on hand** | | PF: jam 100 in F-A-01-1, fruit jellies 100 in F-B-01-1. INT: good puree 75 KG (100 − 15 − 10) and the rejected one 98 KG. MP: FRAISE-IQF 190 KG (lot 700001-2), SUCRE 477, PECTINE 9.1, jars/lids/labels 1100, pouches 500. |

## 15. Customers and price list

**Sales > Price lists**: GROCERS, Épiceries / Grocers: CONF-FRAISE-250 3.95 from 1 and **3.75 from 48**; PATE-FRUIT-200 4.95.

**Sales > Customers**:

| Code | Name | Language | Address | Tax group | Price list | Warehouse |
|---|---|---|---|---|---|---|
| EPICERIE-BEAUCE | Épicerie de la Beauce | French | 120, avenue du Palais, Saint-Joseph-de-Beauce, QC, G0S 2V0 | QC | GROCERS | PF |
| CAFE-VIEUX-QC | Café du Vieux-Québec | English | 35, rue Saint-Louis, Québec, QC, G1R 3Z2 | QC | (none) | PF |

## 16. Sales, printing with the logo and a credit note

**Sales > Invoices** (date 2026-12-03):

| Invoice | Lines | Expected |
|---|---|---|
| EPICERIE-BEAUCE | 48 jams + 24 fruit jellies | Jam 3.75 (price list, 48 break), no tax (ZERO) = 180.00; jellies 4.95 with QC = 118.80. Subtotal 298.80, TPS 5.94, TVQ 11.85, **total $316.59**. |
| | **Check** | Taken from the jam lot in F-A-01-1 and the jellies lot in F-B-01-1. |
| | **Post** | Number **5001**. Cost $147.62. |
| | **Print** | The logo at the top of the invoice, next to the company name; French text; TPS and TVQ numbers; the invoice note. |
| CAFE-VIEUX-QC | 12 jams + 6 jellies | Product price (4.25 and 5.50): 51.00 + 33.00 = 84.00, TPS 1.65, TVQ 3.29, **total $88.94**. **Post**: number **5002**. **Print** in English, with the logo. |
| On 5001, **Credit** | Keep only the jam, quantity 2, without *Return to stock* (broken jars) | Total $7.50, no tax. **Post**: NC-&lt;n&gt;. |
| **Inventory > Stock on hand**, PF | | Jam 40 (100 − 48 − 12), jellies 70 (100 − 24 − 6). |

## 17. Traceability back to the supplier (with the logo in Excel)

**Production > Lots and traceability**

| Step | Expected |
|---|---|
| FRAISE-IQF, lot 700001-1 | *Origin*: reception 700001, PO-1001, FERME-ORLEANS, supplier lot IO-2611-A. Movements: in 200, out 105 and 95 to the two puree orders. |
| *Uses* / *Customers* | Both puree lots, the jam and the jellies, and the customers EPICERIE-BEAUCE and CAFE-VIEUX-QC (recall). |
| The jam lot | Goes back to the good puree, then to strawberry lot 700001-1 and the supplier. |
| **Export** (Excel) | The *Summary* sheet opens with the **logo** at the top, above the summary. |

## 18. Screen help

| Step | Expected |
|---|---|
| **?** on *System settings* | A *Logo* item. |
| **?** on *Warehouses / locations* | The *Locations* tab, the search, the generator (*Zone*, *Aisle*, *Rack*, *Level*, *Bin*, from/to, preview). |
| **?** on *GL Accounts / Cost Centers* | Explains *Type*, *Requires a cost center*, department and sub-department, and that the account and the cost center only meet on purchase lines. |
| **FR** button | The same help in French. |
