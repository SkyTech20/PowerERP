# PowerERP — Supply chain indicators (SCOR): test script

> **Note:** this script was written for the *Pastry shop* scenario, which was removed (the default is now *Maple products*, see PowerERP-Maple-Demo-Test-Script.md). It will be rewritten with the maple products; until then, the codes and figures quoted here are not in the demo.

Script to test **Reports > Supply chain indicators** (step 7 of the SCOR / ISO plan: SCOR performance attributes, ISO 9001 9.1 monitoring and measurement). Nothing is typed on this screen: every figure comes from the invoices, receptions, production orders, shop floor records, nonconformances and stock movements of the ERP. The expected values are those of the **Pastry shop** scenario after the preparation of section 2, done on the same day.

**Before you start:** log in as administrator, go to **Administration > System settings**, choose the **Pastry shop** scenario and restore the demo data.

---

## 1. The screen with the demo data

**Reports > Supply chain indicators** (new item of the **Reports** menu)

| Step | Expected |
|---|---|
| Open the screen | Filters at the top: *Period* "Last 90 days", *From* (today − 89 days), *To* today, *Lots expiring within* "30 days", and "90 days" on the right. Four groups of cards: *Reliability* (6), *Responsiveness* (2), *Cost* (2), *Assets* (5). |
| Cards without data (e.g. *Perfect orders*, *Production on time*) | A dash "—" and "No data in the period": the demo has no posted invoice nor completed order yet. |
| *Supplier fill rate* and *Receptions without a problem* | 100 %: everything ordered was received and no reception has a nonconformance. |
| *Stock value* | The same total as **Inventory > Inventory valuation**. |
| *Lots to expire* and the card *Lots to watch* | The egg EGG 900103-1 (expiry 2026-12-25) shows when 30 days or less are left, with the badge "N day(s) left". Change *Lots expiring within* to 7 days: it leaves the list when more than 7 days are left. |
| Card *Stock by product* | The products in stock; those that did not go out in the period come first with the badge *Not used*. |
| **?** | Opens the help of the screen; the filters have their **?**. |

## 2. Prepare: sell, make, find a problem

| Step | Expected |
|---|---|
| **Sales > Invoices**: open the draft invoices 1, 2 and 3 and **Post** each | Three posted invoices. |
| On posted invoice 1, **Credit note** and **Post** the credit note | A credit note that credits invoice 1. |
| **Production > Production orders**, **New**: DOUGH, 10 KG, *Start* 5 days ago, *Due* tomorrow, **Save**, **Release**, **Issue** | Order in progress. |
| Card *Recipe steps*: *Add warm water* 3.6, **Record**; *Shop floor*: **Report** 9.8; **Complete**; **Close** | Order closed on time, 9.8 of 10. |
| **New**: PASTEL-HAM-CHEESE, 40 UN, *Start* 5 days ago, *Due* 2 days ago, **Save**, **Release**, **Issue** | Order in progress. |
| *Oil temperature* 190 with the corrective action "Burner turned down", **Record**; then 180, **Record**; **Report** 38; **Complete** | Order completed late, 38 of 40, one deviation. |
| **Quality > Nonconformances**, **New**: *Found at* Reception, *Document* 900104, *Severity* Major, HAM 900104-1, "Too warm at reception", **Save** | NC open, HAM lot held. |

## 3. The indicators afterwards

**Reports > Supply chain indicators**

| Step | Expected |
|---|---|
| *Perfect orders* | 66.7 %, "2 of 3 invoices" (invoice 1 has a credit note). |
| *Production on time* | 50 %, "1 of 2 orders" (the pastel order was late). |
| *Production yield* | 95.6 %, "47.80 made of 50.00 ordered". |
| *Receptions without a problem* | 83.3 %, "5 of 6 receptions" (reception 900104 has the NC). |
| *Steps right first time* | 66.7 %, "2 of 3 records" (the 190 °C). |
| *Production cycle time* | The days between **Release** and **Complete** (0.0 when on the same day). |
| *Time to close a nonconformance* | "—": no NC closed yet. Close the NC (disposition + corrective action) and come back: the days show. |
| *Production cost variance* | The % of the actual cost against the estimate of the closed order (DOUGH). |
| *Gross margin* | (sales − cost) / sales of the posted invoices, less the credit note. |
| *Stock turns* and *Days of supply* | Now with a value: the stock went out for the invoices and the orders. |
| *Lots held back* | The value of HAM 900104-1, "1 lot(s) on hold...". In the card *Lots to watch*, under *Held back by quality*, HAM 900104-1 *On hold*. Clicking the line opens the trace of the lot. |
| Card *Nonconformances* | "1 found in the period", "1 open today"; bars *Reception* 1 and *Major* 1. |
| Card *Deviations on the shop floor* | The line of the pastel order: *20/10 Oil temperature*, 190 °C *Above the maximum*, *warning*, "Burner turned down", admin. Clicking opens the order. |
| Card *Stock by product* | The products used now have *Used in the period* and *Days of supply*; the others stay *Not used*. |
| Click the card *Gross margin* | Opens **Sales > Invoices**. Each card opens the screen it comes from. |

## 4. Period and permissions

| Step | Expected |
|---|---|
| *Period* "Last 30 days", "Last 12 months", "This year" | The dates change and the figures are calculated again. |
| *From* after *To* | Message "The start of the period is after its end." |
| An old period (e.g. 2025) | Every period card shows "—"; *Stock value* and the lots stay (they are today's). |
| **Administration > Roles**: a role without *Supply chain indicators* | The item leaves the menu of the users of that role. With *View*, it shows. The demo roles PRODUCTION and WAREHOUSE have it. |
| Screen on a phone (narrow width) | The cards go one under the other, without sideways scrolling. |
