# PowerERP — Lots and traceability: test script

> **Note:** this script was written for the *Pastry shop* scenario, which was removed (the default is now *Maple products*, see PowerERP-Maple-Demo-Test-Script.md). It will be rewritten with the maple products; until then, the codes and figures quoted here are not in the demo.

Script to test the **Production > Lots and traceability** screen (step 3 of the SCOR / ISO plan): from a lot, see where it comes from (supplier, supplier lot, purchase order; for a lot made here, the lots of the materials), where it went (production orders, lots made from it, customers), what a recall must reach, and export it all to Excel. The screen labels are in English, as the ERP shows them with the **EN** button. The expected values are those of the **Pastry shop** scenario after the preparation of section 1.

**Before you start:** log in as the administrator, go to **Administration > System settings**, pick the **Pastry shop** scenario and restore the demo data.

---

## 1. Prepare: make and sell

| Step | Expected |
|---|---|
| **Production > Production orders**, **New**: DOUGH, 10 KG, **Save**, **Release** | Order 1 released. |
| Card *Shop floor*: **Issue**; then *Quantity made* 9.8 and **Report** | Order 1 *In progress*, lot made MO1 (9.8 KG). |
| **New**: PASTEL-HAM-CHEESE, 40 UN, **Save**, **Release**, **Issue**, *Quantity made* 40, **Report** | Order 2 *In progress*. Under *Lots used*: DOUGH MO1 2.4 KG, HAM 900104-1 1.6 KG, CHEESE 900104-2 1.6 KG. Lot made MO2 (40 UN). |
| **Sales > Invoices**, **New**: CAFE-PLATEAU, PASTEL-HAM-CHEESE 100 UN, **Save**, **Post** | Invoice 1. The stock goes out FEFO: 45 from HAM-CHEESE-20261118, 45 from HAM-CHEESE-20261119 and 10 from MO2. |
| **New**: TRAITEUR-ROYAL, PASTEL-HAM-CHEESE 15 UN, **Save**, **Post** | Invoice 2, the 15 come from MO2. |

## 2. The screen

**Production > Lots and traceability**

| Step | Expected |
|---|---|
| Open the screen | Lists *Product* and *Lot* and the message "Pick a product and a lot to see its trace." The *Lot* list is disabled until a product is picked. |
| Open the *Product* list | Only products with a lot in the stock: BEEF-RAW, CHEESE, CHICKEN-RAW, DOUGH, EGG, HAM, PASTEL-... Products without lots, like FLOUR, are not listed. |
| Pick HAM | It has a single lot, so it is picked already: 900104-1 — 2027-01-11 · 13.4. The trace shows at once. The address becomes `#/prod/traceability/HAM/900104-1` (it can be kept or sent). |
| **?** | Opens the help of the screen; each field has its own **?**. |

## 3. One step back and one step forward (HAM 900104-1)

| What to look at | Expected |
|---|---|
| The 4 figures at the top | *Lots reached* 2, *Customers* 2, *Stock lines* 2, *Open orders* 1. |
| Yellow box | "For a recall: 2 lot(s) reached, 2 customer(s) to call, 2 stock line(s) to put on hold and 1 open order(s) to check." |
| Card *Origin* | "Received 2026-11-12 · Reception 900104 · supplier DELIQC — Distribution Fromages et Charcuteries QC · supplier lot DEL-261112-1 · PO 800104 · 15 KG". The link opens the reception. |
| Card *Uses* | Order 2 *In progress* used 1.6 KG → made 40 UN: PASTEL-HAM-CHEESE lot MO2. The link opens the order. |
| Card *Customers* | "Lots reached: HAM 900104-1, PASTEL-HAM-CHEESE MO2". CAFE-PLATEAU, *Invoice* 1, MO2, 10 UN; TRAITEUR-ROYAL, *Invoice* 2, MO2, 15 UN. |
| Card *Stock on hand* | HAM 900104-1 13.4 KG in COLD-01; PASTEL-HAM-CHEESE MO2 15 UN in REC. |
| Card *Open production orders* | Order 2 *In progress*. |
| Card *Stock movements* | *Receipt* of Reception 900104 (15) and *Issue* Production 2 (1.6). The number opens the movement. |

## 4. Backwards (lot made MO2)

| Step | Expected |
|---|---|
| *Product* PASTEL-HAM-CHEESE, *Lot* MO2 | The lots of the 18th and 19th show 0 on hand; MO2 shows 15. |
| Card *Origin* | "Made 2026-11-25 · Order 2 · 40 UN". Below, each lot used: DOUGH MO1 (made by Order 1), HAM 900104-1 and CHEESE 900104-2, each down to its reception and supplier lot (DEL-261112-1, DEL-261112-2). |
| Card *Uses* | "No production order used this lot." |
| Figures at the top | *Lots reached* 1, *Customers* 2, *Stock lines* 1, *Open orders* 1. |
| Card *Stock movements* | *Receipt* Production 2 (40), *Issue* Invoice 1 (10), *Issue* Invoice 2 (15). |

## 5. Credit note

| Step | Expected |
|---|---|
| **Sales > Invoices**, invoice 2, **Credit note**, keep 5 UN with *Return* checked, **Save**, **Post** | Credit note NC-1; 5 UN go back into MO2. |
| Back to MO2 | Under *Customers*, a new line TRAITEUR-ROYAL *Credit note* NC-1 with -5 UN. *Stock on hand*: MO2 20 UN. *Customers* stays 2 (TRAITEUR-ROYAL still holds 10). |

## 6. Export to Excel

| Step | Expected |
|---|---|
| **Export to Excel** (HAM 900104-1) | Downloads `trace-HAM-900104-1.xlsx` and the message "The spreadsheet is being downloaded." |
| Open the file | Sheets *Summary*, *Origin*, *Uses*, *Customers*, *Stock*, *Movements*, with the same data as the screen; the first row bold and frozen. |
| **FR** button and export again | The file in French: sheets *Résumé*, *Origine*, *Utilisations*, *Clients*, *Stock*, *Mouvements*. |

## 7. Access and refusals

| What to do | Expected |
|---|---|
| A role without *Lots and traceability* (Administration > Roles) | The menu entry is gone; through the API `/api/traceability` answers 403. |
| The demo PRODUCTION role | Sees the screen (read only: the screen never changes anything). |
| Through the API, a lot that does not exist: `/api/traceability?product=HAM&lot=XYZ` | 404 "This lot is not in the stock of this product." |
| A material without a lot (FLOUR) | Not shown in the origin of DOUGH MO1: only materials kept by lot are traced. |
| Phone (narrow screen) | The figures go on 2 columns and nothing runs off the screen. |

## 8. Help

| Step | Expected |
|---|---|
| **Help > Production > Lots and traceability** (EN and FR) | Sections: Product, Lot, The recall summary, Origin, Uses, Customers, Stock on hand, Open production orders, Stock movements, Export to Excel. |
