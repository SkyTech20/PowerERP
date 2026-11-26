# PowerERP — Lot status and nonconformances: test script

Script to test the **Quality** menu (step 5 of the SCOR / ISO plan): **Quality > Lot status** (release, hold, quarantine or reject a lot) and **Quality > Nonconformances** (record a problem, hold the lot, close it with the decision and the corrective action), plus the button that holds the lots of a recall in **Production > Lots and traceability**. A lot that is not released does not go out on a sales invoice nor on a production order. The screen labels are in English, as the ERP shows them with the **EN** button. The expected values are those of the **Maple products** scenario right after restoring the demo.

**Before you start:** log in as the administrator, go to **Administration > System settings**, pick the **Maple products** scenario and restore the demo data. The demo already has 3 nonconformances (1 and 2 closed, 3 open), the candy lot MO9 on hold and barrel 900106-3 rejected; the new nonconformance of this script will be number 4.

---

## 1. The Lot status screen

**Quality > Lot status**

| Step | Expected |
|---|---|
| Open the screen | 4 figures at the top: *On hold* 1, *Quarantine* 0, *Rejected* 1, *Released* 14. The lots: product and description, lot with its expiry under it, quantity with the warehouse/location under it, and *Status*. On top, the ones that need a decision: MAPLE-CANDY-12 MO9 *On hold* (yellow, reason "Order 9, step 10/20 Cook to 115 °C: 118.5 °C") and SYRUP-BULK-AMB 900106-3 *Rejected* (0, returned to the supplier, reason "NC 1 closed: return to supplier"). |
| **?** | Opens the help of the screen; the filters and the fields have their own **?**. |
| *Product* filter SYRUP-BULK-AMB | 900106-3 *Rejected*, 900102-4 95 KG in PLANT/BAR-04 and 900106-2 276 KG in PLANT/BAR-10, both *Released*. Back to *All*. |
| Search "TANK" | Only SYRUP-STD MO7, 146 KG in PLANT/TANK-02. Clear the search. |

## 2. A nonconformance at reception (holds the lot)

The case: the lab analysis of barrel B-0431 from Érablière Gagnon (lot 900102-4, still 95 kg in BAR-04) found lead above the limit. Part of the barrel already went into the standardized syrup MO7.

**Quality > Nonconformances**, **New**

| Step | Expected |
|---|---|
| Open | *Date found* today, *Found at* Internal check, *Severity* Minor, *Hold the lot* ticked, *Disposition* To decide. |
| **Save** with nothing | Error on *What is wrong* (required). |
| *Found at* Reception, *Document* REC 900102, *Severity* Critical, *Product* SYRUP-BULK-AMB, *Lot* 900102-4, *Quantity affected* 95, *What is wrong* "Lab analysis of barrel B-0431: lead 0.6 ppm, limit 0.5 ppm", **Save** | "Created." Nonconformance 4 — SYRUP-BULK-AMB · 900102-4, *Open* badge. *Lot status*: On hold. *Unit*: KG. Card *History*: Created; Lot put on hold. |
| **Quality > Lot status** | *On hold* figure 2. SYRUP-BULK-AMB 900102-4 on top, yellow line, *On hold*, reason "NC 4: Lab analysis of barrel B-0431...", under it admin, the date and the link *Nonconformance 4*. |
| **History** on the line | Released → On hold, who, when and the reason. **Hide history** closes it. |

## 3. Recall: hold the lots made with the barrel

| Step | Expected |
|---|---|
| On the 900102-4 line, **Trace** | Opens **Production > Lots and traceability** with SYRUP-BULK-AMB 900102-4. Card "Status of this lot: *On hold* · Lot status". Figures: *Lots reached* 6, *Customers* 4, *Stock lines* 6, *Open orders* 1 (order 9, *Completed*). |
| *Lots reached* | SYRUP-BULK-AMB 900102-4 *On hold*, SYRUP-STD MO7 *Released*, MAPLE-SYRUP-540 MO8 *Released*, MAPLE-CANDY-12 MO9 *On hold*, MAPLE-FUDGE-250 MO10 *Released*, MAPLE-BUTTER-200 MO11 *Released*. |
| Card *Customers* | DISTRIB-CHAUDIERE (invoice 6), LAURENTIAN-HOTELS (8), EPICERIE-STDENIS (9) and BOUTIQUE-VQ (7). |
| Click **Put the 4 released lot(s) on hold** without a reason | Notice "Write the reason of the change." |
| *Reason* "Barrel 900102-4 (B-0431): lead above the limit (NC 4)", the button | "4 lot(s) put on hold." MO7, MO8, MO10 and MO11 become *On hold*; the card says "Every lot the recall reaches is already held back." |
| **Quality > Lot status** | *On hold* 6, *Rejected* 1, *Released* 9. |

## 4. A held lot does not go out

| Step | Expected |
|---|---|
| **Sales > Invoices**, the draft of DISTRIB-CHAUDIERE, **Check** | *To fix before posting*: "MAPLE-SYRUP-540 200 UN > 0 UN" and "MAPLE-FUDGE-250 60 UN > 0 UN". **Post** is refused with "Not enough released stock: lots on hold, in quarantine or rejected cannot go out (Quality > Lot status)." The invoice stays a draft. |
| **Production > Production orders**, **New**: MAPLE-SYRUP-540 100 UN, **Save** | Order 14. In the materials, SYRUP-STD 72 KG with *Available* 0 (the held MO7 does not count). |
| **Release**, **Issue** | Error on SYRUP-STD: "Not enough released stock..." (72 > 0 KG). Order 12, already released, cannot take the syrup either. (Cancel order 14.) |
| **Inventory > Stock movements**, transfer SYRUP-BULK-AMB 900102-4 from BAR-04 to an empty location (for example BAR-12) | It works: a held lot can still be moved, adjusted or counted in the stock. |

## 5. Close the nonconformance

**Quality > Nonconformances**, open number 4

| Step | Expected |
|---|---|
| **Close** (confirm) without a decision | Error on *Disposition* (required). |
| *Disposition* Return to supplier, **Close** | Error on *Corrective action* (required). |
| *Root cause* "Old evaporator pan at the sugar bush (lead solder).", *Corrective action* "Return the barrel to Érablière Gagnon; ask for a lead analysis with every barrel.", **Close**, confirm | "Nonconformance closed." *Closed* badge, read-only fields, *Lot status* Rejected, *Closed by* / *Closed on* filled in. *History*: Closed (Return to supplier), Lot rejected, Lot put on hold, Created. Buttons: **Back to list** and **Reopen** (no Save nor Delete). |
| **Quality > Lot status** | SYRUP-BULK-AMB 900102-4 *Rejected*, reason "NC 4 closed: return to supplier". The lots made with it stay *On hold*: each one needs its own decision (section 6). |
| **Quality > Nonconformances** (list) | 1 *Closed* (Reception, 900106-3, Return to supplier), 2 *Closed* (Customer, MAPLE-FUDGE-250 MO5, Use as is), 3 *Open* (Production, MAPLE-CANDY-12 MO9) and 4 *Closed*, *Critical*, Reception, SYRUP-BULK-AMB, 900102-4, *Rejected*, 95 KG, Return to supplier. Filters *Status*, *Found at*, *Severity*, *Product*. |
| Open number 4, **Reopen**, reason "More barrels of B-04xx to check" | "Nonconformance reopened." *Open* badge, the fields can be changed again; the lot stays *Rejected*. Close it again with Return to supplier. |

Rules of the dispositions on closing: **Use as is** releases the lot (only if this nonconformance held it); **Scrap** and **Return to supplier** reject it; **Rework** keeps it on hold.

## 6. Change a status by hand

**Quality > Lot status**

| Step | Expected |
|---|---|
| On the MAPLE-SYRUP-540 MO8 line, **Change status** | Opens under it: *New status* (the other 3 statuses), *Reason*, **Save**, **Cancel** and the explanation. |
| **Save** without a reason | "Write the reason of the change." |
| *Quarantine*, reason "Cans sent to the lab for lead", **Save** (or Enter) | "Lot MO8: Quarantine." Figures: *Quarantine* 1, *On hold* 4. |
| **Change status** again: *Released*, reason "Lab result: lead 0.02 ppm, conform", **Save** | MO8 *Released*; it goes to the end of the list (the lots that need a decision come first). **History** shows the 3 changes. |
| The draft of DISTRIB-CHAUDIERE, **Check** | Only the fudge problem is left (MO10 still on hold). |
| The *Rejected* figure | Filters the rejected lots only (900106-3 and 900102-4). Click again to remove the filter. The *Status* filter "Not released" shows on hold + quarantine + rejected. |

## 7. Roles

| Step | Expected |
|---|---|
| **Administration > Roles**, role PRODUCTION | *Quality* module: Lot status (View, Change status) and Nonconformances (View, Create, Edit, Close). |
| Role WAREHOUSE | Lot status View; Nonconformances View and Create. |
| Sign in with a WAREHOUSE user | Sees **Quality > Lot status** without the *Change status* button; on the traceability screen (if allowed) the hold button does not show. Can create a nonconformance but does not see **Close**. |
| **Administration > Audit log** | The changes are there: Change status (Lot status), Create / Edit / Close (Nonconformances). |

## 8. French

| Step | Expected |
|---|---|
| **FR** button | Menu **Qualité > Statut des lots / Non-conformités**; statuses *Libéré, En attente, Quarantaine, Rejeté*; dispositions *Utiliser tel quel, Retouche, Rebut, Retour au fournisseur*. The help opens in French. |
