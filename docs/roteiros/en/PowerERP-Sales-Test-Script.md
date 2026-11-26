# PowerERP — Sales: test script (V1 to V6)

> **Note:** this script was written for the *Pastry shop* scenario, which was removed (the default is now *Maple products*, see PowerERP-Maple-Demo-Test-Script.md). It will be rewritten with the maple products; until then, the codes and figures quoted here are not in the demo.

Script to test the B2B sales module (Quebec, CAD) in the demo. Screen labels are in English, as the ERP shows them with the **EN** button. The expected values are those of the **Manufacturing** scenario right after the demo data is restored.

**Before you start:** log in as the administrator and go to **Administration > System settings**. Choose the **Manufacturing** scenario and restore the demo data. Restoring again puts everything back to the starting point, so the script can be repeated as often as needed.

---

## 1. Company data (V1)

**Administration > System settings > Company profile**

| Step | Expected |
|---|---|
| Open the *Company profile* card | Shows Industries Démo PowerERP inc., an address in Montréal and NEQ 1170000001. |
| Look at *GST / HST and QST numbers* | GST 123456789 RT0001 and QST 1234567890 TQ0001. These numbers come from the tax codes (**Administration > Taxes**) and are not typed here. |
| *Invoice numbers start at* | Empty or 0, so the first invoice will be number 1. If you enter 1001 and save, the next posted invoice gets number 1001. |

## 2. Customers (V1)

**Sales > Customers**

| Customer | What to check |
|---|---|
| HOTEL-LAURIER | Language FR, tax group QC, terms n30 (*net 30 jours*), price list HORECA. Has two ship-to addresses: HOTEL (default, Gatineau, QC) and OTTAWA (group ON). |
| MAPLE-FOODS | Language EN, Ontario, terms n45, price list DIST. |
| CPE-SOLEIL | Tax-exempt daycare: group EXO, with an exemption number. |

Try to delete customer HOTEL-LAURIER. The system refuses, because the customer is on an invoice.

## 3. Price lists and price check (V2)

**Sales > Price lists** and the customer's **Price check** tab.

| Step | Expected |
|---|---|
| HOTEL-LAURIER > *Price check*: TUBE-T8, qty 1 | Price 15.75 (HORECA), discount 3 % (the customer's discount), net 15.2775. |
| Same check with qty 60 | Price 13.95, because HORECA has a quantity break from 50. |
| MAPLE-FOODS: DOCK-USBC | Price 249.00, discount 4 %, net 239.04. |

## 4. Draft invoice (V3)

**Sales > Invoices.** The demo comes with 3 drafts:

| Draft | Customer | Taxes | Total |
|---|---|---|---|
| #1 | HOTEL-LAURIER (QC) | GST 24.84 + QST 49.55 on 496.79 | **571.18** |
| #2 | MAPLE-FOODS (shipped to Toronto) | HST-ON 13 % = 110.70 on 851.52 | **962.22** |
| #3 | CPE-SOLEIL (exempt) | none | **170.57** |

**Check on draft #1:**
- Lines: TUBE-T8 with 12 × 15.2775 = 183.33; CLAV-SF with 2 × 76.63 = 153.26; EXT-5LB with 2 × 80.10 = 160.20.
- *Discounts given*: 28.21.

**Create a new invoice (New button):**
1. Choose customer HOTEL-LAURIER. The system proposes ship-to HOTEL, warehouse ENT-01, language French and terms n30.
2. Click *Add line*, choose TUBE-T8 and type qty 10. Price, discount, taxes and totals appear as you type: amount 152.78, GST 7.64, QST 15.24, total 175.66.
3. Change *Ship to* to OTTAWA. The taxes become HST-ON 13 %, because the tax follows the ship-to location.
4. Add PAIN-BL-675 (bread). The line gets group ZERO, with no tax, and the other products stay taxed.
5. Type a price by hand (for example 16) and save. The price is kept.
6. To test the minimum price, set a *Min price* on the product above the net price. When the invoice is saved, the below-minimum-price error appears.

## 5. Post the invoice (V4)

**Stock-out order per product:** in **Inventory > Products >** product **> Inventory tab**, the *Stock out order* field has these options:
- *Automatic*: FEFO if the product has an expiry date, otherwise FIFO.
- *FEFO*: what expires first goes out first.
- *FIFO*: what came in first goes out first.
- *LIFO*: what came in last goes out first.

**An expired lot is never sold.**

| Step | Expected |
|---|---|
| Draft #1 > **Check** | *Ready to post*. *Stock to take out*: TUBE-T8 12 from B-01-02-A, CLAV-SF 2 from A-01-02-A, EXT-5LB 2 from lot L2026-09 (expiry 2032-09-30). Nothing is changed. |
| Change TUBE-T8 to 500 and click **Check** | *To fix before posting*: not enough stock on line 1 (500 UN > 100 UN). **Post** refuses and nothing leaves the stock. |
| Set it back to 12, click **Post** and confirm | The invoice gets number **1** (or the configured starting number) and becomes *Posted*, read-only. *Cost of goods sold* = 418.88. *Stock taken out* shows the cost per line. |
| **Inventory > Stock movements** | 3 OUT movements, document SO 1. |
| **Inventory > Stock** | TUBE-T8 in B-01-02-A went from 100 to 88. |
| On the posted invoice | There is no Save or Delete. The API answers 409 if someone tries to change or delete it. |

**FEFO, FIFO and LIFO test with EXT-5LB:**
1. Make a manual receipt (**Inventory > Stock movements**, type IN) of 2 units of lot L2027-03, expiry 2031-03-31, in B-01-02-A.
2. Create an invoice with 3 EXT-5LB and click **Check**.
   - *Automatic* (= FEFO): L2027-03 × 2 goes out, then L2026-09 × 1.
   - FIFO: L2026-09 × 3 goes out, since it came in first.
   - LIFO: L2027-03 × 2 and L2026-09 × 1 go out, because L2027-03 came in last.

## 6. FR/EN printing (V5)

**Print** button on the invoice. Opens the page to print, or to save as PDF from the browser.

| Step | Expected |
|---|---|
| Posted invoice 1 | In French: FACTURE, n° 1, company with GST/QST and NEQ, *Facturer à* and *Livrer à*, *Échéance* = date + 30 days, customer PO, lines with the extinguisher lot, taxes with the registration number, total in CAD and the company note. |
| Draft #2 (MAPLE-FOODS) | In English: INVOICE — DRAFT, DRAFT watermark, *Draft no.* 2, HST-ON, due in 45 days. |
| Force a language | Add `?lang=en` (or `fr`) to the address of the print page. |

## 7. Credit note (V6)

| Step | Expected |
|---|---|
| On posted invoice 1, click **Credit note** and confirm | A draft credit note opens with every line of the invoice. Customer, ship-to, language and taxes come from the invoice and cannot be changed. *Invoice credited* = 1. Each line has *Return* checked. |
| Keep only the TUBE-T8 line with qty 2 (delete the others) | Subtotal 30.56, taxes 4.58, total 35.14, at the invoice's price and discount. |
| Try qty 13 on TUBE-T8 | Error: more than the quantity invoiced and not yet credited. |
| **Check**, then **Post** | Number **NC-1**. *Stock brought back*: 2 UN in B-01-02-A, at the cost it went out (25.48). **Stock movements** shows an ADJ +2 adjustment, document SO NC-1. |
| Uncheck *Return* on a line | The line only credits the price (price adjustment) and nothing comes back to stock. |
| **Credit note** again on invoice 1 | Brings only what is left to credit (TUBE-T8 10, CLAV-SF 2, EXT-5LB 2). With everything credited: *Every line of this invoice is already credited*. |
| Lots and serials | A line with a lot goes back to the same lot and expiry. A notebook with a serial number (LAP-14I7) goes back with the same serial. |
| **Print** on the posted note | NOTE DE CRÉDIT, n° NC-1, *Facture créditée* 1. |
| **Sales > Invoices** list | *Type* column (Invoice / Credit note) and a filter by type. |

## 8. Pastry shop scenario

In **Administration > System settings**, switch to **Pastry shop**. The demo comes with:
- 3 drafts: Café du Plateau, Traiteur Royal and Ottawa Deli (this one with HST-ON).
- Starting stock of finished pastels (lot from 11/18 in location SHOP-01 and lot from 11/19 in SHOP-02, one lot of a product per location), so that the drafts can be posted.

The pastels use FIFO (they have no expiry date). When the Café du Plateau draft is posted, the 11/18 lots go out first.

---

## API quick reference

| Action | Call |
|---|---|
| List and create | `GET/POST /api/sales-invoices` |
| Read, change and delete a draft | `GET/PUT/DELETE /api/sales-invoices/<no>` |
| Calculate without saving | `POST /api/sales-invoices/calc`, `/<no>/calc` |
| Check and post | `POST /api/sales-invoices/<no>/check`, `/<no>/post` |
| Credit note from the invoice | `POST /api/sales-invoices/<no>/credit` |
| Print | `GET /api/sales-invoices/<no>/print?lang=fr\|en` |
| Check a price | `GET /api/pricing?customer=&product=&qty=&uom=&date=` |
