# PowerERP — Production orders (M3a and M3b): test script

Script to test the production orders: create from the approved recipe, see the materials, availability and cost, release, back to draft and cancel (M3a); then the shop floor: issue the materials by lot, report the production with a new lot, give back, see the genealogy, complete and close with the actual cost (M3b, sections 9 to 13). Screen labels are in English, as the ERP shows them with the **EN** button. The values expected are those of the **Maple products** scenario right after the demo data is restored, done on 2026-11-26 (the costs do not depend on the date).

**Before you start:** log in as administrator, go to **Administration > System settings**, choose the **Maple products** scenario and restore the demo data. The demo already has orders 1 to 13 of October and November (10 closed, 9 completed, 12 released and 13 a draft): the orders created by this script start at 14.

---

## 1. New order

**Production > Production orders**

| Step | Expected |
|---|---|
| Open the screen | The 13 orders of the demo, filters *Status*, *Product* and *Warehouse*. |
| **New** | Card *What to make*, *Start* = today. The material cards say "Pick a product to see the materials of its recipe." |
| Open the *Product* list | Only products with an approved recipe: MAPLE-BUTTER-200, MAPLE-CANDY-12, MAPLE-FUDGE-250, MAPLE-SYRUP-250, MAPLE-SYRUP-540 and SYRUP-STD. Raw materials such as SYRUP-BULK-AMB are not there. |
| Choose MAPLE-CANDY-12 | Without typing anything else: *Quantity to make* 100 (base quantity of the recipe), *Unit* UN, *Warehouse* PLANT, *Revision* A ★. |
| Card *Materials* | Green alert "All the materials are available": SYRUP-STD 14 KG (146 available), BOX-12 100 UN (112 available), LABEL 100 UN. |
| Card *Operations and cost* | 2 operations (MPL-COOK, MPL-MOULD). Total time 85 min, *Estimated cost* $195.53, unit cost 1.9553 / UN. |
| Change *Quantity to make* to 200 and leave the field | Everything is recalculated: SYRUP-STD 28 KG, BOX-12 200 UN, LABEL 200 UN; yellow shortage alert: BOX-12 short 88 UN (red); time 105 min; estimated cost $357.47. |
| **Save** | Message *Created*. Order 14, badge *Draft*. Card *Tracking* with *Created by* and *Created on*. Card *History* with "Created". |

## 2. Refusals

On a new order:

| What to do | Expected |
|---|---|
| **Save** without a product | "This field is required" on *Product*. |
| MAPLE-CANDY-12, *Quantity to make* 0, **Save** | "Must be greater than zero." |
| *Start* 2026-12-10 and *Due* 2026-12-01 | "The end is before the start." on *Due*. |
| Through the API, `POST /api/production-orders` with `cProduct` SYRUP-BULK-AMB | 400 *no_approved_recipe* (a purchased product, no recipe). |

## 3. Release

On order 14:

| Step | Expected |
|---|---|
| **Release** and confirm | Message *Order released*. Badge *Released*, screen read only, *Released by* and *Released on* filled in. |
| Card *History* | "Created" and "Released" (Draft → Released). |
| Buttons | **Back to draft** and **Cancel order**. No **Save** or **Delete**. |
| The BOX-12 shortage | Still in the *Materials* card: a shortage warns, it does not block. |

## 4. Back to draft and cancel

| Step | Expected |
|---|---|
| **Back to draft**, reason "change the quantity" | Badge *Draft*, fields editable, *Released by/on* gone. History with the reason. |
| Change to 100 and **Save** | Materials and cost recalculated ($195.53), green alert. |
| **Cancel order**, reason "no boxes" | Badge *Cancelled*, screen read only, no action buttons. History with 4 lines. |
| List with filter *Status* = Cancelled | Order 14. |

## 5. Delete and numbering

| Step | Expected |
|---|---|
| Create order 15 (SYRUP-STD, 100 KG) | Every material available: SYRUP-BULK-AMB 101 KG (371 available), FILTER-PAPER 0.5 UN. Estimated cost $807.64. |
| **Delete** on order 15 | It leaves the list. |
| Create another order | It gets number 16: numbers are never reused. |

## 6. Links with other screens

| Step | Expected |
|---|---|
| **Inventory > Items**, try to delete BOX-12 | Refused: the product is in use. |
| **Production > Recipes**, MAPLE-CANDY-12 A, **Make obsolete**; then **Release** order 13 (a draft of MAPLE-CANDY-12) | "This product has no approved recipe." The order stays a draft. (Restore the demo afterwards.) |

## 7. Permissions

| Step | Expected |
|---|---|
| **Administration > Roles**, role PRODUCTION | *Production orders* at *Full*, with the *Release* action. |
| Role SALES | No access: the entry is not in the menu of users with that role. |
| A custom role with *Production orders* at *Edit* (no *Release*) | Creates and changes drafts, but the **Release**, **Back to draft** and **Cancel order** buttons are not shown. |

## 9. Issue the materials (M3b)

Restore the demo. Create an order of SYRUP-STD, 100 KG (order 14), **Save** and **Release**.

| Step | Expected |
|---|---|
| Card *Shop floor*, part *1. Issue the materials* | SYRUP-BULK-AMB 101 KG, with *To issue* already filled in. FILTER-PAPER is *backflush*: it goes out by itself when the production is reported. |
| **Show the lots** | "Ready: the stock is there." and the table, FEFO (expires first, out first): 95 KG of barrel 900102-4 (BAR-04) and 6 KG of barrel 900106-2 (BAR-10). Nothing moves (check **Inventory > Stock movements**). |
| **Issue** | Message *Materials issued*. Badge *In progress*. History with "Production started". Column *Issued* of the *Materials* card filled in. |
| Card *Lots made and lots used* | Under *Lots used*: 2 *Issue* lines with their value ($701.46 and $44.30) and the movement number; clicking it opens the movement. |
| **Inventory > Stock movements** | 2 movements out with document *Production* 14. |
| **Issue** again | Error "Nothing to issue: every material is issued, or the quantities are empty." |

## 10. Report the production

| Step | Expected |
|---|---|
| Part *2. Report the production*: *Quantity made* 99; leave *Lot*, *Expiry* and *Location* automatic; **Report** | Message *Production reported*. Under *Lots made*: lot MO14, 99 KG, in REC (standardized syrup has no default location), expiry 2027-11-26 (365 days), unit cost 8.0764, value $799.56. To put it in a tank, type *Location* TANK-01 (empty) before **Report**. |
| Card *Tracking* | *Lot made* MO14 and *Quantity made* 99. |
| **Inventory > Stock on hand**, SYRUP-STD | Lot MO14 with 99 KG, besides MO7 (146 KG in TANK-02). |
| List of the orders | Column *Made* with 99 KG. |

## 11. Give a material back

| Step | Expected |
|---|---|
| Under *Lots used*, line of barrel 900106-2, **Return**, type 2 | Return message. New *Return* line with -2 KG and -$14.77. *Issued* of SYRUP-BULK-AMB = 99 KG. The barrel goes back to BAR-10. |
| **Return** of 50 KG on the same line | Error "More than what went out of the stock for this line." (4 KG of that barrel are left). |

## 12. Complete and close

| Step | Expected |
|---|---|
| Card *Actual cost* | Materials $732.35, operations $59.90 (for 99 KG), actual cost $792.25, per unit 8.0025 / KG, estimated 8.0764 / KG, variance -$7.32 (green). |
| **Complete** and confirm | Badge *Completed*. The *Shop floor* card is gone. Buttons **Reopen** and **Close**. |
| **Reopen** | Back to *In progress*. **Complete** again. |
| **Close** and confirm | Badge *Closed*, no buttons. *Actual cost* says "Kept when the order was closed". History: Created, Released, Production started, Completed, Reopened, Completed, Closed. |
| **Cancel order** on an order that moved stock | Not shown; through the API the answer is 409. |
| Orders of the demo (e.g. 4, MAPLE-CANDY-12) | Already closed with their actual cost: 388 boxes made of 400, note "12 boîtes de bonbons cassés au démoulage." |

## 13. Stock rules and refusals

| What to do | Expected |
|---|---|
| A released order of MAPLE-FUDGE-250 100 UN, **Show the lots** | The cream comes out of lot 900107-1: lot 900105-1 (12 L) expired on 2026-10-27 and is never used. The butter comes out 1 KG of lot 900105-2 (expires first) and 0.5 KG of 900107-2. |
| On the same order, *To issue* of SYRUP-STD 500 | **Show the lots** lists the problem "Not enough stock available" (500 > 146 KG); **Issue** refuses and nothing moves. |
| A normal **Issue**, then **Complete** without reporting | "Report a quantity made before completing the order." |
| A draft order | The *Shop floor* card is not shown. |
| A role without the *Shop floor* action (Administration > Roles) | The *Shop floor* card and the **Return** buttons are not shown. |

## 14. Help

| Step | Expected |
|---|---|
| The **?** button on the screen | Panel with the *Production orders* help (EN/FR). |
| The ⓘ icon next to each field | Explains the field. |
