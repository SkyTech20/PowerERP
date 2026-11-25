# PowerERP — Production orders (M3a): test script

Script to test the production orders: create from the approved recipe, see the materials, availability and cost, release, back to draft and cancel. The stock does not move yet in this step (issue and output reporting come with M3b). Screen labels are in English, as shown with the **EN** button. Expected values are those of the **Pastry shop** scenario right after the demo is restored.

**Before you start:** log in as administrator, go to **Administration > System settings**, choose the **Pastry shop** scenario and restore the demo data. The demo starts with no orders.

---

## 1. New order

**Production > Production orders**

| Step | Expected |
|---|---|
| Open the screen | Empty list, filters *Status*, *Product* and *Warehouse*. |
| **New** | Card *What to make*, *Start* = today. The material cards say "Pick a product to see the materials of its recipe." |
| Open the *Product* list | Only products with an approved recipe (BOILED-EGG, DOUGH, PASTEL-BEEF, PASTEL-CHICKEN...). Raw materials such as FLOUR are not listed. |
| Pick PASTEL-BEEF | With nothing else typed: *Quantity to make* 100 (the base quantity of the recipe), *Unit* UN, *Warehouse* KITCHEN (the product's default), *Revision* A ★. |
| Card *Materials* | Yellow shortage alert. DOUGH 6 KG, available 0, short 6 KG (red); FILL-BEEF-EGG 8 KG, short 8 KG; OIL-FRY 2 L, available 60 L ✓; PAPER-BAG 100 UN, available 2,000 UN ✓. |
| Card *Operations and cost* | 3 operations (PST-SHAPE, PST-FRY, PST-PACK). Total time 80 min, *Estimated cost* $60.07, cost per unit 0.6007 / UN. |
| Change *Quantity to make* to 200 and leave the field | Everything is recalculated: DOUGH 12 KG, FILL-BEEF-EGG 16 KG, OIL-FRY 4 L, PAPER-BAG 200 UN; time 135 min (2.25 h); estimated cost $110.13. |
| **Save** | Message *Created*. Order 1, badge *Draft*. Card *Tracking* with *Created by* and *Created on*. Card *History* with "Created". |

## 2. Refusals

On a new order:

| What to do | Expected |
|---|---|
| **Save** with no product | "This field is required" on *Product*. |
| PASTEL-BEEF, *Quantity to make* 0, **Save** | "Must be greater than zero." |
| *Start* 2026-12-10 and *Due* 2026-12-01 | "The end is before the start." on *Due*. |
| Through the API, `POST /api/production-orders` with `cProduct` FLOUR | 400 *not_made* (a bought product). |

## 3. Release

On order 1:

| Step | Expected |
|---|---|
| **Release** and confirm | Message *Order released*. Badge *Released*, read-only screen, *Released by* and *Released on* filled in. |
| Card *History* | "Created" and "Released" (Draft → Released). |
| Buttons | **Back to draft** and **Cancel order**. No **Save** or **Delete**. |
| The DOUGH shortage | Still shown in the *Materials* card: a shortage warns, it does not block. |

## 4. Back to draft and cancel

| Step | Expected |
|---|---|
| **Back to draft**, reason "change the quantity" | Badge *Draft*, fields editable, *Released by/on* gone. History with the reason. |
| Change to 150 and **Save** | Materials and cost recalculated. |
| **Cancel order**, reason "no dough" | Badge *Cancelled*, read-only, no action buttons. History with 4 lines. |
| List filtered on *Status* = Cancelled | Order 1. |

## 5. Delete and numbering

| Step | Expected |
|---|---|
| Create order 2 (DOUGH, 10 KG) | Every material available: green alert "All the materials are available". Estimated cost $20.77. |
| **Delete** on order 2 | Gone from the list. |
| Create another order | It gets number 3: numbers are never reused. |

## 6. Links with other screens

| Step | Expected |
|---|---|
| **Inventory > Items**, try to delete PAPER-BAG | Refused: the product is used by an order. |
| **Production > Recipes**, PASTEL-BEEF A, **Make obsolete**; then try **Release** on a draft order of PASTEL-BEEF | "This product has no approved recipe." The order stays a draft. (Restore the demo afterwards.) |

## 7. Permissions

| Step | Expected |
|---|---|
| **Administration > Roles**, role PRODUCTION | *Production orders* at *Full*, with the *Release* action. |
| Role SALES | No access: the entry is not in the menu of users with that role. |
| A custom role with *Production orders* at *Edit* (no *Release*) | Creates and changes drafts, but the **Release**, **Back to draft** and **Cancel order** buttons are not shown. |

## 8. Help

| Step | Expected |
|---|---|
| The **?** button on the screen | Panel with the *Production orders* help (EN/FR). |
| The ⓘ icon next to each field | Explains the field. |
