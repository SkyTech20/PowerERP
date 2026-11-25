# Production orders {#prod.orders}

A production order says what to make, how much, in which warehouse and when. It is made from an approved recipe: the materials, the operations and the estimated cost come from the recipe, for the quantity of the order.

**Where:** **Production > Production orders**.

## List {#prod.orders.list}

Columns: Order #, Status, Product, Description, Quantity, Warehouse, Start, Due, Revision and Estimated cost.

Filters: Status, Product and Warehouse. **New** creates a draft order.

## Life of an order {#prod.orders.cycle}

1. **Draft:** created with **New**. It can be changed or deleted freely. The materials, the operations and the cost are recalculated after each change.
2. **Released:** the order is ready for the shop floor. The recipe is checked again (it must still be approved) and the order can no longer be changed. See [Release](#prod.orders.release).
3. **In progress, Completed, Closed:** come with the next step (issue of the materials by lot, and report of the production with a new lot). Not available yet.
4. **Cancelled:** a draft or released order that will not be made. See [Cancel order](#prod.orders.cancel).

A released order goes back to draft with [Back to draft](#prod.orders.unrelease), as long as nothing was issued or produced. Every change of status is kept in the [history](#prod.orders.history).

The stock does not move yet: production orders only plan. Missing materials are shown, they do not block.

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

## Materials {#prod.orders.materials}

The materials of the recipe for the quantity of the order, in stock units (the conversions of the product are applied), with the scrap of the recipe included.

- **Required:** what the order needs.
- **Available:** stock on hand minus reserved in the warehouse of the material (or of the order), without expired lots.
- **Short:** what is missing (required − issued − available). A red badge means a shortage: receive or move the stock before production. A green ✓ means the material is there.
- **Issued:** what was already taken out for the order (shown once production has started, next step). The column **Warehouse** appears when a material is taken from another warehouse than the order's.
- **Unit cost / Cost:** the cost of the material in the item master, for the quantity.

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

### Delete {#prod.orders.delete}

Drafts only. Deletes the order for good. A released order is cancelled instead, so that its history is kept.
