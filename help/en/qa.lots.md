# Lot status {#qa.lots}

Which lots may be sold and used, and which are held back until a decision is taken. A lot that may be unsafe or out of specification (a supplier recall, a lab result awaited, a damaged delivery) is put on hold here, so that no one sells it or uses it in production by mistake. This is the control of nonconforming products asked by ISO 9001 (8.7), ISO 22000 and the Safe Food for Canadians Regulations.

**Where:** **Quality > Lot status**.

## The four statuses {#qa.lots.statuses}

- **Released:** the lot may be sold and used. A lot that was never changed is released.
- **On hold:** waiting for a decision (a check, a result, a nonconformance still open).
- **Quarantine:** kept apart until it is checked (often moved to a quarantine location).
- **Rejected:** it never goes out to a customer or to production: it is to scrap or to return to the supplier.

A lot that is not released is **left out of the sales invoices and of the production orders**: posting an invoice or issuing the materials of an order takes the next released lot (in the order of the pick policy), and says *Not enough released stock* when only held lots are left. The available quantity shown on the production orders does not count it either. It can still be moved, adjusted or counted in **Inventory > Stock movements** (to a quarantine location, out to scrap).

## The figures at the top {#qa.lots.kpis}

How many lots are on hold, in quarantine, rejected and released. Click a figure to show only those lots; click it again to show them all.

## Status {#qa.lots.status}

Shows one status, or **Not released** (on hold, quarantine and rejected together). The lots that need a decision come first.

## Product {#qa.lots.product}

The lots of one product.

## Search {#qa.lots.search}

Finds the lots whose product, description, lot, reason or location holds the text.

## Columns {#qa.lots.columns}

- **Product** and its description.
- **Lot**, with its expiry date under it.
- **On hand:** the quantity in stock, in the stock unit, all warehouses together, with the warehouses and locations that hold it under it.
- **Status** (a held lot is on a yellow line).
- **Reason** of the last change, with the user, the date and the nonconformance that set it (a link).

The list shows the lots in stock, and the lots that are not released even when nothing is left of them.

## Change status {#qa.lots.change}

Opens the change under the lot. Choose the new status, write the reason and click **Save** (or press Enter). The reason is required: it is kept in the history, with your name and the time. A nonconformance can do the same for its lot ([Nonconformances](#qa.nc)).

Only the roles with the **Change** permission of this screen see the button (Administration > Roles).

## New status {#qa.lots.newStatus}

The status the lot gets: the statuses other than its current one.

## Reason {#qa.lots.reason}

Why the status changes, e.g. *supplier recall 2026-114*, *awaiting the lab result*, *checked: conform*. It shows in the list and in the history.

## History {#qa.lots.history}

Every change of status of the lot, newest first: when, who, from which status to which, and why. The history is never changed or deleted.

## Trace {#qa.lots.trace}

Opens the lot in **Production > Lots and traceability**: where it comes from, where it went, and the button that holds every lot a recall reaches.
