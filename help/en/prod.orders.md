# Production orders {#prod.orders}

A production order says what to make, how much, in which warehouse and when. It is made from an approved recipe: the materials, the operations and the estimated cost come from the recipe, for the quantity of the order.

**Where:** **Production > Production orders**.

## List {#prod.orders.list}

Columns: Order #, Status, Product, Description, Quantity, Made (quantity reported), Warehouse, Start, Due, Revision and Estimated cost.

Filters: Status, Product and Warehouse. **New** creates a draft order.

## Life of an order {#prod.orders.cycle}

1. **Draft:** created with **New**. It can be changed or deleted freely. The materials, the operations and the cost are recalculated after each change.
2. **Released:** the order is ready for the shop floor. The recipe is checked again (it must still be approved) and the order can no longer be changed. See [Release](#prod.orders.release).
3. **In progress:** the first material issued or the first quantity reported on the [shop floor](#prod.orders.floor) starts the order.
4. **Completed:** production is over. See [Complete](#prod.orders.complete). Nothing more can be issued or reported; [Reopen](#prod.orders.reopen) puts it back in progress.
5. **Closed:** the [actual cost](#prod.orders.actual) is kept and the order can no longer change. See [Close](#prod.orders.close).
6. **Cancelled:** a draft or released order that will not be made. See [Cancel order](#prod.orders.cancel).

A released order goes back to draft with [Back to draft](#prod.orders.unrelease), as long as nothing was issued or produced. Once the stock has moved, an order can no longer go back to draft or be cancelled: it is completed and closed. Every change of status is kept in the [history](#prod.orders.history).

Missing materials are shown on the order; they warn, they do not block the release. The stock moves only on the shop floor, with stock movements of document *Production* and the order number (**Inventory > Stock movements**).

## What to make {#prod.orders.what}

### Product {#prod.orders.cProduct}

The product to make. Required. Only products with an approved recipe are listed. A product marked *Buy* in **Production > Manufactured items** is refused. Choosing another product takes its recipe and its default warehouse again.

### Quantity to make {#prod.orders.dQty}

How much to make, in the unit of the recipe (shown next to it). Required, greater than zero. The materials and the times of the recipe are calculated for this quantity.

### Unit {#prod.orders.cUOM}

Read-only. The unit of the recipe, in which the quantity is given.

### Warehouse {#prod.orders.cWarehouse}

Where the materials are taken from and where the product will go in. Empty: the default warehouse of the product (Inventory > Items). The availability of the materials is checked in this warehouse.

### Revision {#prod.orders.cRevision}

The version of the recipe used. Only approved versions are listed (★ = the default one). Empty: the default approved recipe valid on the start date is taken, and its revision is then written here.

### Start {#prod.orders.dStart}

The day production starts. Empty: today. It decides which recipe is valid (dates *Effective from / to* of the recipe).

### Due {#prod.orders.dDue}

The day the product must be ready. Optional. It cannot be before the start.

### Notes {#prod.orders.cNotes}

Free text for the shop floor or the planner.

## Tracking {#prod.orders.tracking}

### Created by {#prod.orders.cUser}

The user who created the order. Read-only.

### Created on {#prod.orders.dCreated}

Date and time of creation. Read-only.

### Released by {#prod.orders.cReleasedBy}

The user who released the order. Shown once released.

### Released on {#prod.orders.dReleased}

Date and time of the release. Shown once released.

### Completed by {#prod.orders.cCompletedBy}

The user who completed the order. Shown once completed.

### Completed on {#prod.orders.dCompleted}

Date and time of the completion.

### Closed by {#prod.orders.cClosedBy}

The user who closed the order. Shown once closed.

### Closed on {#prod.orders.dClosed}

Date and time of the closing.

### Lot made {#prod.orders.cLot}

The lot of the product made by the order (the one of the first report). Shown once something was reported.

### Quantity made {#prod.orders.dQtyDone}

The total quantity reported, in the unit of the recipe.

## Materials {#prod.orders.materials}

The materials of the recipe for the quantity of the order, in stock units (the conversions of the product are applied), with the scrap of the recipe included.

- **Required:** what the order needs.
- **Available:** stock on hand minus reserved in the warehouse of the material (or of the order), without expired lots.
- **Short:** what is missing (required − issued − available). A red badge means a shortage: receive or move the stock before production. A green ✓ means the material is there.
- **Issued:** what was already taken out for the order, net of returns (shown once production has started). The column **Warehouse** appears when a material is taken from another warehouse than the order's.
- **Unit cost / Cost:** the cost of the material in the item master, for the quantity.

## Recipe steps {#prod.orders.steps}

Shown on released, in-progress, completed and closed orders: the steps of the recipe of the order (**Production > Recipes**, tab *Steps*), grouped by operation, as the operator follows them. Each step shows its state:

- **To do:** not recorded yet (or not enough records: see the frequency below).
- **Done:** recorded within its limits.
- **Deviation:** the last record is out of its limits. Red with *blocks the next step*: see below.
- **Does not apply:** the step has a condition (for example *Only if TEMP_PATE < 24*) that the values recorded so far do not meet.

At the top: how many required steps are done, and how many deviations were recorded. Each record is listed on its step (newest first): the value, who, the second signer, when, and for a deviation the reason, what it does and the corrective action. Records are never changed or deleted: a step is recorded again.

What a deviation does, for a **critical** step (the *If out of limits* of the step in the recipe):

- **Blocks the next step:** the order cannot report production or be completed until the step is recorded again within its limits.
- **Holds the lot:** the lot made is put *On hold* in **Quality > Lot status** (the lot of the record, else every lot the order made, and the lots it reports later), until quality decides.
- **Warning:** recorded and shown; nothing is stopped. A deviation of a step that is not critical is always a warning.

The required steps that are not recorded warn; they do not stop the order. The records need the *Shop floor* permission of the role.

**Frequency:** *Once*: one record within limits. *Each lot*: one for each lot made. *Every N units*: one for each N units reported (at least one). *Every N minutes*: as often as needed, at least once. The badge shows the good records and the records needed (for example 1/2).

### Value {#prod.orders.steps.value}

What was measured, set or checked, for the steps of kind *Set a parameter*, *Measure* and *Check*: a number (in the unit shown, with its limits under it), Yes / No, or a choice of the list. Required. As soon as it is typed it is compared with the limits: a green ✓ or the reason (for example *Below the minimum*). The other steps (instruction, add material, timer, report production, second signature) are recorded with **Mark as done**.

### Lot (step) {#prod.orders.steps.lot}

For a step done *Each lot*: the lot it was done for. It starts at the lot of the order; the lots already made are proposed. Empty before the first lot is reported: the record counts for the lot reported next.

### Corrective action {#prod.orders.steps.comment}

What was done about a value out of its limits (for example *Baked 5 more minutes, probe again*). Required when the value is out of its limits; it is written in the history of the order with the value.

### Second signer (user) {#prod.orders.steps.signer}

For a step with a *2nd signature* (and a *Second signature* step): the user name of the person who checks and signs, another user than the one logged in. When the step has a required role (*Signed by*), the second signer must have that role (an administrator always may).

### Their password {#prod.orders.steps.password}

The password of the second signer, typed by them. It is checked and never kept; a wrong password is refused and written in **Administration > Audit log**.

### Record / Mark as done {#prod.orders.steps.record}

Records the step with who (the user logged in), when, the value, the limits of the step at that time and whether it is within them. On a step already done, **Record again** opens the form again (a new measure, another lot).

## Shop floor {#prod.orders.floor}

Shown on released and in-progress orders, to the roles with the *Shop floor* permission. Each step makes stock movements of the order; nothing moves while one problem is left.

### 1. Issue the materials {#prod.orders.floor.issue}

Takes the materials out of the stock, lot by lot, from the warehouse of the order (or of the material). The lots expiring first go first (the pick policy of the product: FEFO, FIFO or LIFO); an expired lot and a blocked location are never used. **Show the lots** lists the lots, locations and quantities that would be taken, without moving anything, or what is missing. **Issue** takes them out.

The backflushed materials (issue method *Backflush*) are not issued here: they go out automatically when the production is reported.

### To issue {#prod.orders.floor.issueQty}

The quantity of each material to take out, in its stock unit. It starts at what is left to issue (required − issued). Change it to issue part of it, or leave 0.

### Date (issue) {#prod.orders.floor.issueDate}

The date of the stock movements. It also decides which lots are expired.

### 2. Report the production {#prod.orders.floor.report}

Puts the quantity made into the stock of the order's warehouse, at the estimated unit cost of the order. The backflushed materials go out at the same time, for that quantity (required × quantity reported / quantity of the order). Several reports can be made (for example one per shift).

### Quantity made {#prod.orders.floor.reportQty}

The good quantity made, in the unit of the recipe. It starts at what is left to make.

### Lot (report) {#prod.orders.floor.reportLot}

The lot of the product made. Empty: the lot of the order, else **MO** + the order number (for example MO12), for a product followed by lot.

### Expiry (report) {#prod.orders.floor.reportExpiry}

The expiry date of the lot made. Empty: the date + the shelf life of the product (Inventory > Items), for a product with an expiry date.

### Location (report) {#prod.orders.floor.reportLocation}

Where the product goes in the warehouse. *Automatic*: the default location of the product in the warehouse (Inventory > Replenishment parameters), else the receiving location of the warehouse; the receiving location is also taken when the default location holds another lot of the product (one lot per location).

### Date (report) {#prod.orders.floor.reportDate}

The date of the stock movements; the expiry is counted from it.

## Lots made and lots used {#prod.orders.lots}

The genealogy of the order: the lots of the product made (date, lot, expiry, location, quantity, value, stock movement, who) and the lots of the materials used (issue, backflush or return). A click on a movement number opens it in **Inventory > Stock movements**.

### Return {#prod.orders.return}

On a lot used, gives back a quantity that was not consumed: it goes back into the same lot and location, at the cost it went out at. At most what was issued from that lot.

## Actual cost {#prod.orders.actual}

Shown once the stock has moved: the value of the materials issued (net of returns), the estimated operation cost for the quantity made (no labour is reported yet), the actual cost and actual cost per unit, the estimated cost for the quantity made and the **variance** (actual − estimated: red when the order cost more). It is kept as it is when the order is closed.

## Operations and cost {#prod.orders.operations}

The operations of the recipe with the time on their resource (setup, run, wait) for the quantity, then the totals: total time, material cost, operation cost, **estimated cost** and cost per unit of the product.

## History {#prod.orders.history}

Who created the order and changed its status, when, and the comment given.

## Buttons {#prod.orders.buttons}

### Save {#prod.orders.save}

Saves the draft. The order gets its number at the first save.

### Release {#prod.orders.release}

Saves the draft and releases it: the recipe is checked again (still approved) and the quantities are recalculated. Then the order is locked. Needs the *Release* permission of the screen.

### Back to draft {#prod.orders.unrelease}

Released orders only, while nothing was issued or produced. The order can be changed again. You can give a reason; it goes into the history.

### Cancel order {#prod.orders.cancel}

Draft or released orders, while nothing was issued or produced. The order stays in the list as *Cancelled*. You can give a reason; it goes into the history.

### Complete {#prod.orders.complete}

In-progress orders with a quantity made. Production is over: nothing more can be issued or reported. Refused while a critical step that blocks is out of its limits (see [Recipe steps](#prod.orders.steps)). Needs the *Release* permission.

### Reopen {#prod.orders.reopen}

Completed orders: back in progress, to issue or report more. You can give a reason.

### Close {#prod.orders.close}

Completed orders. Keeps the actual cost and the variance; the order can no longer change. Needs the *Release* permission.

### Delete {#prod.orders.delete}

Drafts only. Deletes the order for good. A released order is cancelled instead, so that its history is kept.
