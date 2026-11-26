# PowerERP — Maple products demo: test script

Script to check the **Maple products** demo scenario (the default of the ERP): Érablière Démo inc., a plant in Saint-Georges (Beauce) that buys maple syrup in barrels from three sugar bushes and makes syrup in cans and bottles, maple butter, maple candy and maple fudge. The demo opens with October and November 2026 already done through the ERP itself: production orders, recipe steps, posted invoices, a credit note, lots on hold and nonconformances. Screen labels are in English, as shown with the **EN** button.

**Before you start:** log in as an administrator, go to **Administration > System settings**, choose **Maple products** and click **Reset demo data**.

---

## 1. The scenario

| Step | Expected |
|---|---|
| **Administration > System settings**, list *Data set* | *Maple products (syrup, butter, candy; production, sales, quality)* first, then *SkyAI* and *Manufacturing*. *Pastry shop* no longer exists. |
| **FR** button | The option reads *Produits de l'érable (sirop, beurre, bonbons ; production, ventes, qualité)*. The **?** of the card explains the demo. |
| **Dashboard** | 6 suppliers, 8 purchase orders (1 open), 7 receptions, stock value $11,966.96. |
| **Sales > Customers** | 4 customers: EPICERIE-STDENIS, BOUTIQUE-VQ, LAURENTIAN-HOTELS (in English) and DISTRIB-CHAUDIERE (3% discount). |
| **Sales > Price lists** | RETAIL, DISTRIB (pallet price from 300 cans) and HOTELS. |
| An installation that already had data and never chose a scenario | After the upgrade it keeps the same data (the ERP does not switch to the maple demo by itself). |

## 2. Master data

| Step | Expected |
|---|---|
| **Inventory > Items** | 21 products. Finished products: MAPLE-SYRUP-540, MAPLE-SYRUP-250, MAPLE-BUTTER-200, MAPLE-CANDY-12, MAPLE-FUDGE-250. Kit/Assembly: SYRUP-STD. Raw materials: SYRUP-BULK-AMB, SYRUP-BULK-DRK, CREAM-35, BUTTER and the packaging. Fixed assets: CANDY-COOKER, FILLER. |
| Open MAPLE-SYRUP-540 | *Sales tax group* ZERO (pure syrup is a basic grocery, zero-rated). MAPLE-CANDY-12 and MAPLE-FUDGE-250: QC (GST + QST). Lot and expiry controlled, *Pick policy* FEFO. |
| Open SYRUP-BULK-AMB | Lot and expiry controlled (730 days). Three suppliers on the purchasing tab: GAGNON (preferred), CANTONS and TREMBLAY. |
| **Inventory > Warehouses**, PLANT | Locations BAR-01 to BAR-12 (one barrel per location), TANK-01/02, COLD-01 to 04, PACK-01, PROD-01 and FG-01 to 12. |
| **Production > Recipes**, MAPLE-BUTTER-200 A | Steps *Cook to 112 °C* (111 to 113, critical, holds the lot) and *Cool below 10 °C before whipping* (10 at most, critical, holds the lot). |
| MAPLE-FUDGE-250 A | Materials SYRUP-STD, CREAM-35, BUTTER; critical step *Label shows the allergen "milk"* that blocks. |
| SYRUP-STD A | Critical step *Syrup Brix (66 to 68.9)* that blocks, and *Taste and smell of the barrels are right*. |

## 3. The story of October and November

| Step | Expected |
|---|---|
| **Production > Production orders** | 13 orders: 10 *Closed*, order 9 (MAPLE-CANDY-12) *Completed*, order 12 *Released* (cans for Nov. 30) and order 13 *Draft*. |
| Open order 9 | Card *Recipe steps*: *Cook to 115 °C* at 118.5 °C, deviation "Above the maximum", comment "Sonde du cuiseur 2 décalée...". Lot MO9. Completed one day after its due date. |
| **Sales > Invoices** | Invoices 1 to 9 *Posted*, credit note NC-1 (6 trays of fudge crushed, not returned to stock) and 2 drafts (DISTRIB-CHAUDIERE and LAURENTIAN-HOTELS). |
| Open invoice 2 (BOUTIQUE-VQ) | The syrup without tax; candy and fudge with GST and QST. |
| Draft of LAURENTIAN-HOTELS (48 boxes of candy), **Post** | Error "Not enough released stock...": only 22 released boxes are left, lot MO9 is on hold. Nothing changes. |
| Draft of DISTRIB-CHAUDIERE, **Check** | Everything is available; it can be posted. |
| **Quality > Nonconformances** | 1: Reception, barrel T-140 (lot 900106-3) tasting of "bourgeon", *Closed*, *Return to supplier*. 2: Customer, MAPLE-FUDGE-250 MO5, *Closed*, *Use as is*. 3: Production, MAPLE-CANDY-12 MO9, *Open*. |
| **Quality > Lot status** | MAPLE-CANDY-12 MO9 *On hold* ("Order 9, step 10/20 Cook to 115 °C: 118.5 °C"). Barrel 900106-3 *Rejected* (it left the stock: returned to Sucrerie Tremblay). |
| **Inventory > Stock on hand**, SYRUP-BULK-AMB | Lot 900106-3 is not there (stock movement OUT of Oct. 30, "Retour au fournisseur"). |

## 4. Traceability back to the sugar bush

| Step | Expected |
|---|---|
| **Production > Lots and traceability**, MAPLE-SYRUP-540, lot MO8 | *Origin*: made by order 8 from the standardized syrup MO1 and MO7; each comes from the barrels, down to the supplier and the supplier lot (e.g. GAGNON, "B-0412 / récolte 2026-03-24"). GAGNON, CANTONS and TREMBLAY appear, never barrel T-140. |
| Card *Customers* | DISTRIB-CHAUDIERE (invoice 6), LAURENTIAN-HOTELS (8) and EPICERIE-STDENIS (9). |
| Card *Stock on hand* | MO8, 236 UN in FG-06. |
| SYRUP-BULK-AMB, lot 900102-1 | *Uses*: order 1 made SYRUP-STD MO1, which made cans, butter, candy and fudge: the recall reaches every customer of those lots. |

## 5. SCOR indicators

**Reports > Supply chain indicators** (last 90 days up to 2026-11-26)

| Card | Expected |
|---|---|
| *Perfect orders* | 88.9%, 8 of 9 invoices (invoice 5 has a credit note). |
| *Production on time* | 90.9%, 10 of 11 orders (order 9 was late). |
| *Production yield* | 99.7% (796 cans of 800 and 388 boxes of candy of 400). |
| *Supplier fill rate* | 99.9% (barrel T-118 came with 266 kg of 280). |
| *Receptions without a problem* | 85.7%, 6 of 7. |
| *Steps right first time* | 97.6%, 41 of 42. |
| *Lots held back* | $681.20: MO9. |
| *Lots to expire* | Cream 900105-1 expired on Oct. 27, cream 900107-1 and the butter about to expire. |
| Card *Deviations on the shop floor* | Order 9, 118.5 °C, *the lot is held*. |

Every card has a value. As the days go by, the 90 days stop covering October: use *From* 2026-09-01.

## 6. Rebuilding the demo (developer)

| Step | Expected |
|---|---|
| `pip install time-machine`; `MAPLE_DATABASE_URL=postgresql+psycopg://...powererp_scratch python tools/make_maple_data.py` | Rewrites `data/maple/*.json` and `story.json`. Two runs give the same result. A database whose name has neither "scratch" nor "test" is refused (it is emptied). |
