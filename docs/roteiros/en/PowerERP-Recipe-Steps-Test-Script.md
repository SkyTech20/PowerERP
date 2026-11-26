# PowerERP — Records of the recipe steps on the shop floor: test script

> **Note:** this script was written for the *Pastry shop* scenario, which was removed (the default is now *Maple products*, see PowerERP-Maple-Demo-Test-Script.md). It will be rewritten with the maple products; until then, the codes and figures quoted here are not in the demo.

Script to test the **Recipe steps** card of **Production > Production orders** (step 6 of the SCOR / ISO plan, M4: ISO 9001 8.5.1, HACCP / ISO 22000 8.5.4 monitoring of the critical control points, SFCR preventive control records). The operator follows the steps of the order's recipe and records each one: the value measured or set, or "done". A value out of its limits is a deviation and needs the corrective action; on a critical step the deviation **blocks** the order or **holds the lot** in **Quality > Lot status**. The expected values are those of the **Pastry shop** scenario.

**Before you start:** log in as administrator, go to **Administration > System settings**, choose the **Pastry shop** scenario and restore the demo data.

---

## 1. The dough: a step within its limits

**Production > Production orders**, **New**

| Step | Expected |
|---|---|
| DOUGH, 10 KG, **Save** | Order 1 in draft: **no** *Recipe steps* card (only once released). |
| **Release** | The **Recipe steps** card appears above *Shop floor*: badge "Required steps: 0 of 1 done", the steps grouped by operation (10 — ..., 20 — ..., 30 — ...), each with its number, icon, title and the *To do* badge. |
| On *Add warm water*: field *EAU (L)* with "min 3.4 · max 3.8" under it | The limits of the recipe. |
| Type 4 and leave the field | Right under it: red badge "Above the maximum → warning" and "Write the corrective action." The *Corrective action* field turns red. Nothing is recorded. |
| Change to 3.6 and leave the field | Green badge "✓ Within its limits". |
| **Record** | "Step recorded." The step is *Done* (green background) with the line "✓ 3.6 L · admin · date and time". Top badge: "Required steps: 1 of 1 done". "Record again" appears (closed). |
| On the steps without a value (*Weigh the flour*, *Mix for 15 minutes*, *Rest the dough*) **Mark as done** | Each is *Done* with "✓ Done · admin · date". |
| *Shop floor*: **Issue**, *Quantity made* 9.8, **Report** | Order in progress, lot MO1. |

## 2. The pastel: a critical step that blocks

**New**: PASTEL-HAM-CHEESE, 40 UN, **Save**, **Release**, **Issue**

| Step | Expected |
|---|---|
| *Recipe steps* card | "Required steps: 0 of 2 done". *Pastels well sealed* has the red border and the badges *Critical · blocks the next step* and *Required*. |
| *Pastels well sealed*: *Value* **No**, **Record** without a corrective action | Error on the step itself and in the toast: "The value is out of its limits: write the corrective action (Not confirmed)". The choice stays in the field. |
| *Corrective action* "3 pastels open: closed again by hand", **Record** | The step is *Deviation* (pink background) with "⛔ Out of its limits: record it again within its limits to go on". The record line: "⚠ No · admin · date" and under it "Not confirmed → blocks the next step · Corrective action: 3 pastels open...". At the top of the card: badge "1 deviation(s)" and the red box "Reporting and completing are blocked until these critical steps are recorded again within their limits: 10/30 Pastels well sealed". |
| *Shop floor*: above **Report** | The same red block message. |
| **Report** (40) | Refused: "A critical step is out of its limits: record it again within its limits first (10/30 Pastels well sealed)". Nothing goes into the stock. |
| *Pastels well sealed*: *Value* **Yes**, **Record** | The step is *Done* again; both records are listed (newest first). The block is gone. |
| **Report** (40) | Accepted now: lot MO2. |
| *History* card | A *Deviation* line with "10/30 Pastels well sealed: no (not_confirmed) — 3 pastels open...". |

## 3. The oil temperature: a deviation that only warns

| Step | Expected |
|---|---|
| *Oil temperature* (TEMP_HUILE, 175 to 185 °C): 190, **Record** without an action | Refused: asks for the corrective action. |
| *Corrective action* "Burner turned down, 180 °C after 2 min", **Record** | *Deviation*, but no block (not critical: "Above the maximum → warning"). **Report** and **Complete** stay possible. Badge "2 deviation(s)". |
| 180, **Record** | *Done*; the deviation stays listed on the step and counted in the badge. |

## 4. The ground beef: a critical step that holds the lot

**New**: GROUND-BEEF, 5 KG, **Save**, **Release**, **Issue**

| Step | Expected |
|---|---|
| Step *Core temperature* (TEMP_COEUR, min 71 °C, *Each lot*) | Badges *Critical · the lot is held* and *Required*; "Each lot" under the title; fields *TEMP_COEUR (°C)*, *Lot* (empty: the lot does not exist yet) and *Corrective action*. |
| 65, *Corrective action* "Cooked 5 more minutes, probe again", **Record** | *Deviation* "Below the minimum → the lot is held". No lot yet: nothing is held now. |
| *Shop floor*: **Report** (5) | Accepted (holding the lot does not block): lot MO3. |
| **Quality > Lot status** | *On hold* box 1: GROUND-BEEF MO3 *On hold*, reason "Order 3, step 20/10 Core temperature: 65 °C", admin and the date. |
| Back to order 3, *Core temperature*: **Record again**, 75, *Lot* MO3, **Record** | *Done* (1/1). The lot **stays** *On hold*: quality releases it (**Change status** in *Lot status*, with the reason). |
| In *Lot status*, MO3 **Change status** → *Released*, reason "Cooked again, probed 75 °C" | The lot is *Released* again. Another **Report** of the same lot MO3 does not hold it again. |

## 5. Second signature and required role (Manufacturing scenario, optional)

The pastry demo has no step with a second signature. To test it: **Administration > System settings**, scenario **Manufacturing**, restore; **Administration > Users**, **New**: user *op1*, role USER, password *Secret-123*.

| Step | Expected |
|---|---|
| **Production > Production orders**, **New**: PAIN-BL-675, 400, **Save**, **Release** | *Recipe steps* card. The step *Mixer clean (cleaning checked)* has the badge *✍️ 2nd signature* and the fields *Second signer (user)* and *Their password*. The step *Dough too cold: correction* is greyed, *Does not apply* ("Only if TEMP_PATE < 24"). |
| *Mixer clean*: Yes, **Record** without a second user | "Required" on the user. |
| *Second signer* admin (the user logged in), right password | Refused: "The second signature must be another user". |
| *Second signer* op1, wrong password | "Wrong user or password for the second signature". In **Administration > Audit log**: event *Second signature refused* of op1. |
| *Second signer* op1, password *Secret-123*, **Record** | *Done*; the line shows "admin + op1". |
| *Dough temperature* 22, corrective action "Warm water", **Record** | *Deviation* (warning). The step *Dough too cold: correction* becomes *To do*. |
| An order of SUPP-ALU-01: step *Release by quality control* (badge "Signed by: quality") with op1 | "This step must be signed by a user of the role (quality)". With an administrator: accepted. |

## 6. Permissions

| Step | Expected |
|---|---|
| With a role that has *Production orders* in **View** only | The *Recipe steps* card shows the records, without fields or buttons. |
| A *Completed* or *Closed* order | The card is read only. |
