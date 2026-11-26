# PowerERP — Lots and traceability: test script

Script to test the **Production > Lots and traceability** screen (step 3 of the SCOR / ISO plan): from a lot, see where it comes from (supplier, supplier lot, purchase order; for a lot made here, the lots of the materials), where it went (production orders, lots made from it, customers), what a recall must reach, and export it all to Excel. The screen labels are in English, as the ERP shows them with the **EN** button. The expected values are those of the **Maple products** scenario right after restoring the demo.

**Before you start:** log in as the administrator, go to **Administration > System settings**, pick the **Maple products** scenario and restore the demo data. The demo already has October and November 2026 done (barrels received, orders closed, invoices posted), so there is nothing to prepare.

---

## 1. The screen

**Production > Lots and traceability**

| Step | Expected |
|---|---|
| Open the screen | Lists *Product* and *Lot* and the message "Pick a product and a lot to see its trace." The *Lot* list stays disabled until a product is picked. |
| Open the *Product* list | Only products kept by lot: BUTTER, CREAM-35, MAPLE-BUTTER-200, MAPLE-CANDY-12, MAPLE-FUDGE-250, MAPLE-SYRUP-540, SYRUP-BULK-AMB, SYRUP-STD... The packaging (CAN-540, BOX-12, LABEL) is not there. |
| Pick MAPLE-SYRUP-540 | *Lot* list: MO2 — 2028-10-01 · 0 and MO8 — 2028-11-02 · 236 (expiry and quantity on hand). |
| Pick MO8 | The trace shows at once. The address becomes `#/prod/traceability/MAPLE-SYRUP-540/MO8` (it can be bookmarked or sent). |
| **?** | Opens the help of the screen; each field has its own **?**. |

## 2. Backward: the lot of cans MO8

| What to see | Expected |
|---|---|
| The 4 figures on top | *Lots reached* 1, *Customers* 3, *Stock lines* 1, *Open orders* 0. |
| Yellow box | "For a recall: 1 lot(s) reached, 3 customer(s) to call, 1 stock line(s) to put on hold and 0 open order(s) to check." |
| Card *Origin* | "Made 2026-11-03 · Order 8 *Closed* · 1000 UN". Under it, the two lots of standardized syrup used: SYRUP-STD **MO1** (245 KG, made by Order 1) and **MO7** (475 KG, Order 7). |
| Open MO1 inside the origin | Barrels SYRUP-BULK-AMB 900102-1, 900102-2, 900102-3 (GAGNON, producer lots B-0412, B-0418, B-0425) and 900104-3 (CANTONS, C-2101). Each shows "Received ... · Reception 900102 (or 900104) · supplier ... · supplier lot ... · PO ...". |
| Open MO7 | Barrels 900102-3 and 900102-4 (GAGNON), 900104-4 (CANTONS, C-2124) and 900106-1 (TREMBLAY, T-118). Barrel T-140 (900106-3), returned for its "bourgeon" taste, does **not** appear. |
| Card *Uses* | "No production order used this lot." (a can is a finished product). |
| Card *Customers* | DISTRIB-CHAUDIERE *Invoice* 6, 364 UN; LAURENTIAN-HOTELS *Invoice* 8, 200 UN; EPICERIE-STDENIS *Invoice* 9, 200 UN. |
| Card *Stock on hand* | MAPLE-SYRUP-540 MO8, 236 UN in FG-06. |
| Card *Stock movements* | *Receipt* Production 8 (1000) and the issues of invoices 6 (364), 8 (200) and 9 (200). The number opens the movement. |

## 3. Forward: one barrel down to the customers (SYRUP-BULK-AMB 900102-1)

| What to see | Expected |
|---|---|
| *Product* SYRUP-BULK-AMB | *Lot* list with the barrels; the ones used up show 0 on hand (900102-1 — 2028-03-23 · 0). 900102-4 has 95 and 900106-2 has 276. |
| Card *Origin* of 900102-1 | "Received 2026-09-10 · Reception 900102 · supplier GAGNON — Érablière Gagnon et fils · supplier lot B-0412 / récolte 2026-03-24 · PO 810102 · 275 KG". The link opens the reception. |
| Card *Uses* | Order 1 *Closed* used 275 KG → made 1000 KG: SYRUP-STD MO1, used by orders 2 (cans MO2), 3 (butter MO3), 4 (candy MO4), 5 (fudge MO5) and 8 (cans MO8). Each link opens the order. |
| Figures on top | *Lots reached* 7, *Customers* 4, *Stock lines* 2, *Open orders* 0. |
| *Lots reached* (line under the yellow box) | SYRUP-BULK-AMB 900102-1, SYRUP-STD MO1, MAPLE-SYRUP-540 MO2, MAPLE-BUTTER-200 MO3, MAPLE-CANDY-12 MO4, MAPLE-FUDGE-250 MO5, MAPLE-SYRUP-540 MO8, all *Released*. |
| Card *Customers* | The 4 customers of the demo, with every invoice from 1 to 9 that took those lots. |
| Card *Stock on hand* | MAPLE-CANDY-12 MO4 22 UN in FG-03 and MAPLE-SYRUP-540 MO8 236 UN in FG-06. |
| Card *Stock movements* | *Receipt* Reception 900102 (275, BAR-01) and *Issue* Production 1 (275). |

The button that holds the lots of the recall is in the quality test script.

## 4. Another example: maple fudge MO5 (with cream and butter)

| Step | Expected |
|---|---|
| *Product* MAPLE-FUDGE-250, *Lot* MO5 | *Origin*: "Made 2026-10-08 · Order 5 · 300 UN", with SYRUP-STD MO1 (and its barrels), CREAM-35 900105-1 (LAITERIE, LT-80213-1) and BUTTER 900105-2 (LAITERIE, LT-80213-2). |
| Card *Customers* | BOUTIQUE-VQ (invoices 2 and 7), DISTRIB-CHAUDIERE (3) and EPICERIE-STDENIS (5): *Customers* 3. Credit note NC-1 is not listed, because it was a price credit only (nothing came back to stock). |
| Figures | MO5 has no stock left: *Stock lines* 0. |

## 5. A credit note that brings stock back

| Step | Expected |
|---|---|
| **Sales > Invoices**, invoice 8 (LAURENTIAN-HOTELS), **Credit note**: keep only MAPLE-SYRUP-540 with qty 4 and *Return* checked, **Save**, **Post** | Credit note NC-2, total 39.60. The 4 cans go back to MO8 in FG-06. |
| Back to MAPLE-SYRUP-540 MO8 | In *Customers*, a new line LAURENTIAN-HOTELS *Credit note* NC-2 with -4 UN. *Stock on hand*: MO8 240 UN. *Customers* is still 3. *Stock movements*: a new adjustment ADJ +4, SO NC-2. |

## 6. Export to Excel

| Step | Expected |
|---|---|
| **Export to Excel** (MAPLE-SYRUP-540 MO8) | Downloads `trace-MAPLE-SYRUP-540-MO8.xlsx` and the message "The spreadsheet is being downloaded." |
| Open the file | Sheets *Summary*, *Origin*, *Uses*, *Customers*, *Stock*, *Movements*, with the same data as the screen; the first row bold and frozen. |
| **FR** button and export again | File in French: sheets *Résumé*, *Origine*, *Utilisations*, *Clients*, *Stock*, *Mouvements*. |

## 7. Access and refusals

| What to do | Expected |
|---|---|
| A role without *Lots and traceability* (Administration > Roles) | The menu entry is gone; through the API `/api/traceability` answers 403. |
| The demo PRODUCTION role | Sees the screen (the trace itself never changes anything). |
| Through the API, a lot that does not exist: `/api/traceability?product=SYRUP-BULK-AMB&lot=XYZ` | 404 "This lot is not in the stock of this product." |
| A material without a lot (CAN-540, LABEL) | Not shown in the origin of the cans MO8: only materials kept by lot are traced. |
| Phone (narrow screen) | The figures go on 2 columns and nothing runs off the screen. |

## 8. Help

| Step | Expected |
|---|---|
| **Help > Production > Lots and traceability** (EN and FR) | Sections: Product, Lot, The recall summary, Origin, Uses, Customers, Stock on hand, Open production orders, Stock movements, Export to Excel. |
