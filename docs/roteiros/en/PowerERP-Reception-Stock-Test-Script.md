# PowerERP — Receptions into the stock: test script

> **Note:** this script was written for the *Pastry shop* scenario, which was removed (the default is now *Maple products*, see PowerERP-Maple-Demo-Test-Script.md). It will be rewritten with the maple products; until then, the codes and figures quoted here are not in the demo.

Script to test putting a reception into the stock, with lot, supplier lot, expiry and location. The values expected are those of the **Pastry shop** scenario right after the demo data is restored.

**Before you start:** log in as administrator, go to **Administration > System settings**, pick the **Pastry shop** scenario and restore the demo data. Restoring again puts everything back as it was.

---

## 1. The old receptions are already in stock

**Purchasing > Receptions**

| Step | Expected |
|---|---|
| Look at the *In stock* column of the list | The 6 demo receptions (900101 to 900106) show *In stock*. |
| Open 900102 (MEATCO) | Badge *In stock*, read-only. On the lines: lots 900102-1 and 900102-2, supplier lots MEA-261110-1 and MEA-261110-2, expiry 2027-05-09, location COLD-01. |
| Card *Put into the stock* | Two movements (BEEF-RAW 40, CHICKEN-RAW 50) with their value. Clicking the number opens the movement in **Inventory > Stock movements**. |
| Filter *In stock* = No | Empty list. |

## 2. Receive the open order 800107

| Step | Expected |
|---|---|
| **New**, *Reception number* 900107, *PO number* 800107 | Supplier MEATCO and two lines filled: BEEF-RAW 40 and CHICKEN-RAW 50. |
| *Warehouse* KITCHEN | |
| Line 1 *Supplier lot* MC-88231; line 2 MC-88232. Leave *Lot*, *Expiry* and *Location* empty | The *Lot* field shows "Automatic". |
| **Save** | Badge *Not in stock yet*. |
| **Check** | Card *What goes into the stock* with "Ready: nothing to fix". Line 1: lot 900107-1, expiry = reception date + 180 days, location REC. Line 2: lot 900107-2, REC. |
| Why REC and not COLD-01? | COLD-01 already holds another lot of these products, and the rule is one lot per location. The ERP takes the receiving location of the kitchen instead. |
| **Inventory > Stock on hand**, filter BEEF-RAW | Still only lot 900102-1: Check changes nothing. |

## 3. Put in stock

| Step | Expected |
|---|---|
| **Put in stock** and confirm | Message *Reception put in stock*. Badge *In stock*, read-only, *Put in stock on* and *Put in stock by* filled. |
| Card *Put into the stock* | 2 movements, BEEF-RAW 40 (580.00) and CHICKEN-RAW 50 (340.00). |
| **Inventory > Stock on hand**, BEEF-RAW | New lot 900107-1 in REC, 40 KG, with its expiry. |
| **Inventory > Stock movements**, last movement | Type *Receipt*, document *Reception* 900107, reason MEATCO, comment "PO 800107 · MC-88231". |
| Try to delete reception 900107 | The button is not shown. Through the API the answer is 409 *posted*. |

## 4. Problems that block

Create reception 900108 on PO 800107, warehouse KITCHEN:

| Line | What to type | Expected on **Check** |
|---|---|---|
| 1 | BEEF-RAW, qty 20, *Location* COLD-01 | "Line 1 (BEEF-RAW): This location already holds another lot..." because the location was typed. Clear it and the ERP picks another one. |
| 2 | Item XYZ-99, qty 1 | "Line 2 (XYZ-99): This code does not exist. — Item". |
| 3 | No item, description Transport, qty 1, cost 25 | Shown in grey: "No item: not stocked". Not a problem. |

**Put in stock** refuses with the first message and nothing goes into the stock. Fix it (clear the location of line 1, remove line 2) and put it in stock.

## 5. Permission

**Administration > Roles**: the **WAREHOUSE** role has *Post* on Receptions. Make a role with Receptions on *Edit* only: its user sees **Check** but not **Put in stock**.

## 6. Help

On the reception, click **?**: the page explains the life of a reception, each new column (Supplier lot, Lot, Expiry, Location, Serial no.) and the Check and Put in stock buttons. The same in FR.
