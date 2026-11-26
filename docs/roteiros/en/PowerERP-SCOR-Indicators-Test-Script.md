# PowerERP — Supply chain indicators (SCOR): test script

Script to test the **Reports > Supply chain indicators** screen (step 7 of the SCOR / ISO plan: SCOR performance attributes, ISO 9001 9.1 monitoring and measurement). There is nothing to type on this screen: every figure comes from the invoices, receptions, production orders, shop floor records, nonconformances and stock movements of the ERP. The screen labels are in English, as the ERP shows them with the **EN** button. The expected values are those of the **Maple products** scenario right after restoring the demo, with the 90-day period up to 2026-11-26.

**Before you start:** log in as the administrator, go to **Administration > System settings**, pick the **Maple products** scenario and restore the demo data. The demo holds October and November 2026; if today is after 2026-11-26, set *From* 2026-08-29 and *To* 2026-11-26 to see the same figures. The lots to expire are always counted from today.

---

## 1. The screen with the demo data

**Reports > Supply chain indicators**

| Step | Expected |
|---|---|
| Open the screen | Filters on top: *Period* "Last 90 days", *From* (today − 89 days), *To* today, *Lots expiring within* "30 days", and "90 days" on the right. Four groups of cards: *Reliability* (6), *Responsiveness* (2), *Cost* (2), *Assets* (5). Every card has a value. |
| *Perfect orders* | 88.9%, "8 of 9 invoices" (invoice 5 has credit note NC-1). |
| *Production on time* | 90.9%, "10 of 11 orders" (order 9, the candy, was completed one day after its due date). |
| *Production yield* | 99.7%, "6,184.00 made of 6,200.00 ordered" (796 cans of 800 and 388 boxes of candy of 400). |
| *Supplier fill rate* | 99.9% (barrel T-118 came with 266 kg of 280). |
| *Receptions without a problem* | 85.7%, "6 of 7 receptions" (reception 900106 has the nonconformance of barrel T-140). |
| *Steps right first time* | 97.6%, "41 of 42 records" (the 118.5 °C of order 9). |
| *Production cycle time* | 0.51 day between **Release** and **Complete**, the average of the 11 orders. |
| *Time to close a nonconformance* | 3.21 days (average of nonconformances 1 and 2). |
| *Production cost variance* | 0.1% of the actual cost against the estimate of the closed orders. |
| *Gross margin* | 43.3%: (sales − cost) / sales of the posted invoices, less the credit note. |
| *Stock value* | $11,966.96, the same total as **Inventory > Inventory valuation**. |
| *Stock turns* and *Days of supply* | 14.92 turns and 24.47 days. |
| *Lots held back* | $681.20, "1 lot(s) on hold, in quarantine or rejected": the candy MO9. In the *Lots to watch* card, under *Held back by quality*, MAPLE-CANDY-12 MO9 *On hold*. Clicking the line opens the trace of the lot. |
| *Lots to expire* and the *Lots to watch* card | $160.30: cream CREAM-35 900105-1, expired on 2026-10-27, cream 900107-1 (2026-12-01) and butter BUTTER 900105-2 (2026-12-05), each with the badge "N day(s) left" (the expired one with *Expired*). Change *Lots expiring within* to 7 days: the butter is gone (if more than 7 days are left). |
| Card *Nonconformances* | "3 found in the period", "1 open today"; bars *Reception* 1, *Production* 1, *Customer* 1, *Major* 2, *Minor* 1. |
| Card *Deviations on the shop floor* | Order 9: *10/20 Cook to 115 °C*, 118.5 °C *Above the maximum*, *the lot is held*, "Sonde du cuiseur 2 décalée...", admin. Clicking opens the order. |
| Card *Stock by product* | The products in stock; the ones that did not go out in the period come first with the badge *Not used* (GLOVES). The others show *Used in the period* and *Days of supply*. |
| **?** | Opens the help of the screen; the filters have their own **?**. |

## 2. Change the data and watch the indicators move

| Step | Expected |
|---|---|
| **Sales > Invoices**, the draft of DISTRIB-CHAUDIERE, **Post** | Invoice 10 is posted. |
| **Quality > Nonconformances**, open number 3 (MAPLE-CANDY-12 MO9), *Disposition* Scrap, *Root cause* "Probe of cooker 2 out of calibration.", *Corrective action* "Probe recalibrated; check it every Monday.", **Close** | The nonconformance is closed; lot MO9 becomes *Rejected*. |
| **New**: *Found at* Reception, *Document* 900107, *Severity* Minor, CREAM-35 900107-1, *Quantity affected* 12, "Cream delivered at 7 °C, limit 4 °C", **Save** | Nonconformance 4 is open and the cream lot is held. |
| Back to **Reports > Supply chain indicators** | *Perfect orders* 90%, "9 of 10 invoices". *Receptions without a problem* 71.4%, "5 of 7". *Gross margin* 42.6%. *Stock value* $10,573.67 (the cost of invoice 10 went out); *Stock turns* 17.42 and *Days of supply* 20.96. |
| *Time to close a nonconformance* | Goes up: nonconformance 3 stayed open from Nov. 6 until today and joins the average. |
| *Lots held back* | $755.60, 2 lots: MO9 *Rejected* (a rejected lot stays out of sales) and cream 900107-1 *On hold*. |
| Card *Nonconformances* | "4 found in the period", "1 open today"; *Reception* 2, *Minor* 2. |
| Click the *Gross margin* card | Opens **Sales > Invoices**. Each card opens the screen its figure comes from. |

## 3. Period and permissions

| Step | Expected |
|---|---|
| *Period* "Last 30 days", "Last 12 months", "This year" | The dates change and the figures are computed again. With 30 days, the October orders and invoices leave the count. |
| *From* after *To* | Notice "The start of the period is after its end." |
| An old period (e.g. 2025) | Every period card shows "—" and "No data in the period"; *Stock value* and the lots stay (they are as of today). |
| **Administration > Roles**: a role without *Supply chain indicators* | The menu entry is gone for the users of that role. With *View*, it shows. The demo roles PRODUCTION and WAREHOUSE already have it. |
| Phone (narrow screen) | The cards go one under the other, with no side scrolling. |
