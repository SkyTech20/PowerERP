# PowerERP — Records of the recipe steps on the shop floor: test script

Script to test the **Recipe steps** card of **Production > Production orders** (step 6 of the SCOR / ISO plan, M4: ISO 9001 8.5.1, HACCP / ISO 22000 8.5.4 monitoring of the critical control points, SFCR preventive control records). The operator follows the steps of the order's recipe and records each one: the value measured or set, or "done". A value out of its limits is a deviation and needs the corrective action; on a critical step the deviation **blocks** the order or **holds the lot** in **Quality > Lot status**. Screen labels are in English, as the ERP shows them with the **EN** button. The expected values are those of the **Maple products** scenario.

**Before you start:** log in as administrator, go to **Administration > System settings**, choose the **Maple products** scenario and restore the demo data. The demo already has orders 1 to 13: new ones start at 14. Order 9 (candy cooked at 118.5 °C) is a ready example of a deviation that held the lot.

---

## 1. The standardized syrup: a step within its limits

**Production > Production orders**, **New**

| Step | Expected |
|---|---|
| SYRUP-STD, 100 KG, **Save** | Order 14 as a draft: the *Recipe steps* card is **not** shown (only once released). |
| **Release** | The **Recipe steps** card appears above *Shop floor*: badge "Required steps: 0 of 2 done", the steps grouped by operation (10 — MPL-BLEND, 20 — MPL-FILTER), each with its number, icon, title and the *To do* badge. |
| On step *Syrup Brix (66 to 68.9)*: field *BRIX (°Bx)* with "min 66 · max 68.9" under it | The limits of the recipe. Badges *Critical · blocks the next step* and *Required*. |
| Type 70 and leave the field | Right under it: red badge "Above the maximum → blocks the next step" and "Write the corrective action." The *Corrective action* field turns red. Nothing is recorded. |
| Change to 67.2 and leave the field | Green badge "✓ Within its limits". |
| **Record** | "Step recorded." The step is *Done* (green background) with the line "✓ 67.2 °Bx · admin · date and time". The badge on top: "Required steps: 1 of 2 done". "Record again" appears (closed). |
| On the steps without a value (*Empty the barrels (scan the lot)*, *Filter for 60 minutes*) **Mark as done** | Each one is *Done* with "✓ Done · admin · date". |

## 2. The taste of the barrels: a critical step that blocks

On the same order 14:

| Step | Expected |
|---|---|
| *Taste and smell of the barrels are right* | Red border, badges *Critical · blocks the next step* and *Required*. |
| *Value* **No**, **Record** without a corrective action | Error on the step and in the notice: "The value is out of its limits: write the corrective action (Not confirmed)". The choice stays in the field. |
| *Corrective action* "Baril 900106-2 : goût de bourgeon", **Record** | The step is a *Deviation* (pink background) with "⛔ Out of its limits: record it again within its limits to go on". On top of the card: badge "1 deviation(s)" and the red box "Reporting and completing are blocked until these critical steps are recorded again within their limits: 10/20 Taste and smell of the barrels are right". |
| *Shop floor*: **Issue**, then *Quantity made* 100, **Report** | **Issue** goes through; **Report** is refused: "A critical step is out of its limits: record it again within its limits first (10/20 Taste and smell of the barrels are right)". Nothing goes into the stock. |
| *Taste and smell...*: *Value* **Yes**, **Record** | The step is *Done* again; both records stay in the list (newest on top). The block is gone. |
| **Report** (100, *Location* TANK-01) | Accepted: lot MO14. |
| Card *History* | A *Deviation* line with "10/20 Taste and smell of the barrels are right: no (not_confirmed) — Baril 900106-2 : goût de bourgeon". |

## 3. The maple butter: a critical step that holds the lot

**New**: MAPLE-BUTTER-200, 100 UN, **Save**, **Release**, **Issue** (order 15)

| Step | Expected |
|---|---|
| Steps *Cook to 112 °C* (TEMP_CUISSON, 111 to 113) and *Cool below 10 °C before whipping* (TEMP_REFROID, 10 at most) | Badges *Critical · the lot is held* and *Required*; "Each lot" under the title; fields for the value, *Lot* (empty: the lot does not exist yet) and *Corrective action*. |
| *Cook to 112 °C*: 112.1, **Record** | *Done*. |
| *Cool below 10 °C...*: 14, *Corrective action* "Bac de refroidissement trop plein ; refroidi de nouveau", **Record** | *Deviation* "Above the maximum → the lot is held". There is no lot yet: nothing is held now, and nothing is blocked. |
| *Shop floor*: **Report** (100) | Accepted (holding the lot does not block): lot MO15. |
| **Quality > Lot status** | Box *On hold* 2: MAPLE-BUTTER-200 MO15 *On hold*, reason "Order 15, step 20/10 Cool below 10 °C before whipping: 14 °C", admin and the date; and the candy MO9 of the demo. |
| Back on order 15, *Cool below 10 °C...*: **Record again**, 8, *Lot* MO15, **Record** | *Done*. The lot **stays** *On hold*: quality releases it (**Change status** in *Lot status*, with the reason). |
| In *Lot status*, MO15 **Change status** → *Released*, reason "Refroidi à 8 °C, texture vérifiée" | The lot is *Released* again and can be sold. |

## 4. A deviation that only warns, second signature and required role (Manufacturing scenario, optional)

In the maple demo every valued step is critical, and none needs a second signature. To test it: **Administration > System settings**, scenario **Manufacturing**, restore; **Administration > Users**, **New**: user *op1*, role USER, password *Secret-123*.

| Step | Expected |
|---|---|
| **Production > Production orders**, **New**: PAIN-BL-675, 400, **Save**, **Release** | *Recipe steps* card. The step *Mixer clean (cleaning checked)* has the badge *✍️ 2nd signature* and the fields *Second signer (user)* and *Their password*. The step *Dough too cold: correction* is greyed, *Does not apply* ("Only if TEMP_PATE < 24"). |
| *Mixer clean*: Yes, **Record** without a second user | "Required" on the user. |
| *Second signer* admin (the user logged in), right password | Refused: "The second signature must be another user". |
| *Second signer* op1, wrong password | "Wrong user or password for the second signature". In **Administration > Audit log**: event *Second signature refused* of op1. |
| *Second signer* op1, password *Secret-123*, **Record** | *Done*; the line shows "admin + op1". |
| *Dough temperature* 22, corrective action "Warm water", **Record** | *Deviation* (warning). The step *Dough too cold: correction* becomes *To do*. |
| An order of SUPP-ALU-01: step *Release by quality control* (badge "Signed by: quality") with op1 | "This step must be signed by a user of the role (quality)". With an administrator: accepted. |

## 5. Permissions

| Step | Expected |
|---|---|
| With a role that has *Production orders* in **View** only | The *Recipe steps* card shows the records, without fields or buttons. |
| A *Completed* or *Closed* order | The card is read only. |
