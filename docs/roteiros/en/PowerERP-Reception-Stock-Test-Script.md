# PowerERP — Receptions into the stock: test script

Script to test putting a reception into the stock, with lot, supplier lot, expiry and location. Screen labels are in English, as the ERP shows them with the **EN** button. The values expected are those of the **Maple products** scenario right after the demo data is restored.

**Before you start:** log in as administrator, go to **Administration > System settings**, pick the **Maple products** scenario and restore the demo data. Restoring again puts everything back as it was.

In the demo, each barrel of maple syrup is a lot and has its own location (BAR-01 to BAR-12): the ERP's rule is one lot of a product per location.

---

## 1. The old receptions are already in stock

**Purchasing > Receptions**

| Step | Expected |
|---|---|
| Look at the *In stock* column of the list | The 7 receptions of the demo (900101 to 900107) show *In stock*. |
| Open 900102 (GAGNON, Érablière Gagnon et fils) | Badge *In stock*, everything read only. Four SYRUP-BULK-AMB barrels: lots 900102-1 to 900102-4, supplier lots "B-0412 / récolte 2026-03-24", "B-0418 / récolte 2026-03-29", "B-0425 / récolte 2026-04-02" and "B-0431 / récolte 2026-04-08" (the producer's barrel number and harvest date), expiry 2028-03-23 to 2028-04-07, locations BAR-01 to BAR-04. |
| Card *Put into the stock* | Four movements with their value: 2,035.00, 1,983.20, 2,079.40 and 1,998.00. Clicking the number opens the movement in **Inventory > Stock movements**. |
| Open 900106 (TREMBLAY) | The comment "Baril T-118 : 266 kg reçus sur 280 kg commandés." and line 1 with 280 ordered and 266 received. |
| Filter *In stock* = No | Empty list. |

## 2. Receive the open purchase order 810108

Purchase order 810108 (GAGNON) has 4 barrels of amber syrup of 275 kg.

| Step | Expected |
|---|---|
| **New**, *Reception number* 900108, *PO number* 810108 | Supplier GAGNON and four SYRUP-BULK-AMB lines of 275 KG filled in. |
| *Warehouse* PLANT | |
| On each line, the barrel's *Supplier lot*: B-0510, B-0514, B-0519, B-0523. Leave *Lot*, *Expiry* and *Location* empty | The *Lot* field shows "Automatic". |
| **Save** | Badge *Not in stock yet*. |
| **Check** | Card *What goes into the stock*: lots 900108-1 to 900108-4, expiry = reception date + 730 days, location REC on all of them. Problem on lines 2, 3 and 4: "This location already holds another lot of this product: one lot per product per location." |
| Why? | Bulk syrup has no default location, so the ERP proposes the receiving location (REC) for every barrel, and REC can hold one lot of the product only. |
| Type the *Location* of each barrel: BAR-01, BAR-02, BAR-03 and BAR-07 (they are empty), **Save**, **Check** | "Ready: nothing to fix. Click Put in stock." |
| **Inventory > Stock on hand**, filter SYRUP-BULK-AMB | Still only lots 900102-4 (BAR-04, 95 KG) and 900106-2 (BAR-10, 276 KG): Check changes nothing. |

The expiry proposed counts from the reception date. To use the harvest date, type the *Expiry* (harvest + 2 years) on each line before putting it in stock.

## 3. Put it in stock

| Step | Expected |
|---|---|
| **Put in stock** and confirm | Message *Reception put in stock*. Badge *In stock*, screen read only, *Put in stock on* and *Put in stock by* filled in. |
| Card *Put into the stock* | 4 movements of SYRUP-BULK-AMB, 275 KG at 7.40, 2,035.00 each. |
| **Inventory > Stock on hand**, SYRUP-BULK-AMB | The new lots 900108-1 to 900108-4 in BAR-01, BAR-02, BAR-03 and BAR-07. |
| **Inventory > Stock movements**, last movement | Type *Receipt*, document *Reception* 900108, reason GAGNON, comment "PO 810108 · B-0523". |
| **Production > Lots and traceability**, SYRUP-BULK-AMB, lot 900108-1 | *Origin*: reception 900108, supplier GAGNON, supplier lot B-0510, PO 810108. |
| Try to delete reception 900108 | The button is not there. Through the API the answer is 409 *posted*. |

## 4. Problems that block

Restore the demo and create reception 900109 on PO 810108, warehouse PLANT:

| Line | What to type | Expected on **Check** |
|---|---|---|
| 1 | SYRUP-BULK-AMB, qty 100, *Location* BAR-04 | "Line 1 (SYRUP-BULK-AMB): This location already holds another lot..." because BAR-04 holds barrel 900102-4. Pick an empty location (e.g. BAR-08). |
| 2 | Item XYZ-99, qty 1 | "Line 2 (XYZ-99): This code does not exist. — Item". |
| 3 | No item, description Transport, qty 1, cost 25 | Shown in grey: "No item: not stocked". Not a problem. |

**Put in stock** refuses with the first message and nothing goes into the stock. Fix it (location of line 1, delete line 2) and put it in stock.

## 5. Permission

**Administration > Roles**: the **WAREHOUSE** role has *Post* on Receptions. Create a role with Receptions on *Edit* only: the user sees **Check** but not **Put in stock**.

## 6. Help

On the reception, click **?**: the page explains the life of a reception, each new column (Supplier lot, Lot, Expiry, Location, Serial no.) and the Check and Put in stock buttons. The same in FR.
