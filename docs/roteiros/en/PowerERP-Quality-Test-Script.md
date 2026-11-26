# PowerERP — Lot status and nonconformances: test script

> **Note:** this script was written for the *Pastry shop* scenario, which was removed (the default is now *Maple products*, see PowerERP-Maple-Demo-Test-Script.md). It will be rewritten with the maple products; until then, the codes and figures quoted here are not in the demo.

Script to test the **Quality** menu (step 5 of the SCOR / ISO plan): **Quality > Lot status** (release, hold, quarantine or reject a lot) and **Quality > Nonconformances** (record a problem, hold the lot, close it with the decision and the corrective action), and the button that holds the lots of a recall in **Production > Lots and traceability**. A lot that is not released does not go out on a sales invoice or a production order. The expected values are those of the **Pastry shop** scenario after the preparation of section 1.

**Before you start:** sign in as administrator, go to **Administration > System settings**, choose the **Pastry shop** scenario and restore the demo data.

---

## 1. Prepare: make and sell

| Step | Expected |
|---|---|
| **Production > Production orders**, **New**: DOUGH, 10 KG, **Save**, **Release**, **Issue**, *Quantity made* 9.8, **Report** | Order 1, lot made MO1. |
| **New**: PASTEL-HAM-CHEESE, 40 UN, **Save**, **Release**, **Issue**, *Quantity made* 40, **Report** | Order 2, uses HAM 900104-1 and makes lot MO2 (40 UN). |
| **Sales > Invoices**, **New**: CAFE-PLATEAU, PASTEL-HAM-CHEESE 100 UN, **Save**, **Post** | Invoice posted; 30 UN of MO2 are left. |

## 2. The Lot status screen

**Quality > Lot status** (the **Quality** menu is new, under Production)

| Step | Expected |
|---|---|
| Open the screen | 4 figures at the top: *On hold* 0, *Quarantine* 0, *Rejected* 0, *Released* 11. The lots in stock: product and description, lot with its expiry under it, quantity with the warehouse/location under it, *Status* (all *Released*, green). |
| **?** | Opens the help of the screen; the filters and fields have their **?**. |
| *Product* filter HAM | Only HAM 900104-1, 13.4 KG in KITCHEN/COLD-01. Back to *All*. |
| Search "COLD" | The lots of COLD-01. Clear the search. |

## 3. A nonconformance at reception (holds the lot)

**Quality > Nonconformances**, **New**

| Step | Expected |
|---|---|
| Open | *Date found* today, *Found at* Internal check, *Severity* Minor, *Hold the lot* ticked, *Disposition* To decide. |
| **Save** with nothing | Error on *What is wrong* (required). |
| *Found at* Reception, *Document* REC 900104, *Severity* Critical, *Product* HAM, *Lot* 900104-1, *Quantity affected* 13.4, *What is wrong* "Temperature 9 °C at reception, limit 4 °C", **Save** | "Created." Nonconformance 1 — HAM · 900104-1, *Open* badge. *Lot status*: On hold. *Unit*: KG. *History* card: Created; Lot put on hold. |
| **Quality > Lot status** | *On hold* figure 1. HAM 900104-1 at the top, yellow line, *On hold*, reason "NC 1: Temperature 9 °C...", under it admin, the date and the *Nonconformance 1* link. |
| **History** on the line | Released → On hold, who, when and the reason. **Hide history** closes it. |

## 4. Recall: hold the lots made with the ham

| Step | Expected |
|---|---|
| On the HAM line, **Trace** | Opens **Production > Lots and traceability** on HAM 900104-1. New card: "Status of this lot: *On hold* · Lot status". In *Customers*, the lots reached show their status: HAM *On hold*, PASTEL-HAM-CHEESE MO2 *Released*. |
| Click **Put the 1 released lot(s) on hold** with no reason | Message "Write the reason of the change." |
| *Reason* "Ham lot 900104-1 too warm at reception (NC 1)", the button | "1 lot(s) put on hold." MO2 becomes *On hold*; the card says "Every lot the recall reaches is already held back." |

## 5. A held lot does not go out

| Step | Expected |
|---|---|
| **Sales > Invoices**, **New**: CAFE-PLATEAU, PASTEL-HAM-CHEESE 10 UN, **Save**, **Post** | Error: "Not enough released stock: lots on hold, in quarantine or rejected cannot go out (Quality > Lot status)." The invoice stays a draft. (Delete it.) |
| **Production > Production orders**, **New**: PASTEL-HAM-CHEESE 40 UN, **Save** | In the materials, HAM with *Available* 0 (the held lot does not count). |
| **Release**, **Issue** | Error on HAM: "Not enough released stock...". (Cancel the order.) |
| **Inventory > Stock movements**, transfer HAM 900104-1 from COLD-01 to another location | Works: a held lot can still be moved, adjusted or counted in the stock. |

## 6. Close the nonconformance

**Quality > Nonconformances**, open number 1

| Step | Expected |
|---|---|
| **Close** (confirm) with no decision | Error on *Disposition* (required). |
| *Disposition* Scrap, **Close** | Error on *Corrective action* (required). |
| *Root cause* "The supplier truck refrigeration was off.", *Corrective action* "Probe every delivery of meat at reception; refuse above 4 °C.", **Close**, confirm | "Nonconformance closed." *Closed* badge, read-only fields, *Lot status* Rejected, *Closed by* / *Closed on* filled. *History*: Closed (Scrap), Lot rejected, Lot put on hold, Created. Buttons: **Back to list** and **Reopen** (no Save or Delete). |
| **Quality > Lot status** | HAM 900104-1 *Rejected*, reason "NC 1 closed: scrap". |
| **Quality > Nonconformances** (list) | Nonconformance 1 *Closed*, *Critical*, Reception, HAM, 900104-1, *Rejected*, 13.4 KG, Scrap. Filters *Status*, *Found at*, *Severity*, *Product*. |
| Open number 1, **Reopen**, reason "More boxes to check" | "Nonconformance reopened." *Open* badge, the fields can be changed again; the lot stays *Rejected*. Close it again with Scrap. |

Rules of the dispositions when closing: **Use as is** releases the lot (only if this nonconformance had held it); **Scrap** and **Return to supplier** reject it; **Rework** keeps it on hold.

## 7. Change a status by hand

**Quality > Lot status**

| Step | Expected |
|---|---|
| On the PASTEL-HAM-CHEESE MO2 line, **Change status** | Opens under it: *New status* (the other 3 statuses), *Reason*, **Save**, **Cancel** and the explanation. |
| **Save** with no reason | "Write the reason of the change." |
| *Quarantine*, reason "Sample sent to the lab", **Save** (or Enter) | "Lot MO2: Quarantine." Figures: *Quarantine* 1, *On hold* 0. |
| **Change status** again: *Released*, reason "Lab result: conform", **Save** | MO2 *Released*; it moves to the end of the list (the lots that need a decision come first). **History** shows the 3 changes. |
| The *Rejected* figure | Shows only the rejected lots (HAM). Click again to clear it. *Status* filter "Not released" shows on hold + quarantine + rejected. |

## 8. Roles

| Step | Expected |
|---|---|
| **Administration > Roles**, role PRODUCTION | *Quality* module: Lot status (View, Change status) and Nonconformances (View, Create, Edit, Close). |
| Role WAREHOUSE | Lot status View; Nonconformances View and Create. |
| Sign in with a WAREHOUSE user | Sees **Quality > Lot status** without the *Change status* button; on the traceability screen (if allowed) the hold button does not show. Can create a nonconformance but does not see **Close**. |
| **Administration > Audit log** | The changes are there: Change status (Lot status), Create / Edit / Close (Nonconformances). |

## 9. French

| Step | Expected |
|---|---|
| **FR** button | Menu **Qualité > Statut des lots / Non-conformités**; statuses *Libéré, En attente, Quarantaine, Rejeté*; dispositions *Utiliser tel quel, Retouche, Rebut, Retour au fournisseur*. The help opens in French. |
