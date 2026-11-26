# Nonconformances {#qa.nc}

A nonconformance records a product or a lot found not to meet its requirements: a delivery received damaged or too warm, a batch out of its limits, a customer complaint, a defect found in a check. It says what was found, what is done with the product (the disposition) and what is done so that it does not happen again (the corrective action), as asked by ISO 9001 (8.7 and 10.2) and ISO 22000 (8.9). With **Hold the lot**, the lot is held back as soon as the nonconformance is saved ([Lot status](#qa.lots)).

**Where:** **Quality > Nonconformances**.

## List {#qa.nc.list}

Columns: No., Status (open or closed), Date found, Found at, Severity, Product, Lot, Lot status, Quantity (affected), What is wrong and Disposition.

Filters: Status, Found at, Severity and Product. **New** records a nonconformance.

## Life of a nonconformance {#qa.nc.cycle}

1. **Open:** it is created (anyone with the Create permission). While it is open it can be changed and completed (the cause, the decision).
2. **Close:** when the decision is taken. The disposition (other than *To decide*) and the corrective action are required. Closing gives the lot the status of the disposition:
   - **Use as is:** the lot is released again (only when this nonconformance had put it on hold; a lot held by something else keeps its status).
   - **Scrap** and **Return to supplier:** the lot is rejected: it never goes out. Take it out of the stock in Inventory > Stock movements (scrap) or return it to the supplier.
   - **Rework:** the lot stays on hold until it is reworked and released in Lot status.
3. A closed nonconformance is read only. **Reopen** (with the reason) opens it again; the lot keeps its status.

A nonconformance is never deleted once its lot is held: only an open one that holds no lot can be deleted (a mistake).

## What was found {#qa.nc.what}

### Date found {#qa.nc.dDate}

The day the problem was found. Today by default.

### Found at {#qa.nc.cSource}

Where it was found: **Internal check**, **Reception** (a delivery of a supplier), **Production** (on the shop floor) or **Customer complaint**.

### Document {#qa.nc.cRef}

The document it comes from, as text: the reception (REC 12), the production order (order 7), the invoice, the number of the complaint. It is found by the search of the list.

### Severity {#qa.nc.cSeverity}

**Minor** (no risk for the customer), **Major** (the product does not meet its requirements) or **Critical** (a risk for health or safety: hold the lot and trace it at once).

### Product {#qa.nc.cProduct}

The product concerned. Leave it empty for a problem that is not about a product (a process, a document).

### Lot {#qa.nc.cLot}

The lot concerned, chosen among the lots of the product known to the stock (the list shows their status, expiry and quantity on hand). Needs the product.

### Quantity affected {#qa.nc.dQty}

How much is concerned, in the stock unit of the product (shown in the list). Optional.

### Unit {#qa.nc.cUOM}

The stock unit of the product, filled in when the nonconformance is saved.

### What is wrong {#qa.nc.cDescription}

The problem as it was found: what, how much, how it was seen (e.g. *temperature 9 °C at reception, limit 4 °C*). Required.

### Hold the lot {#qa.nc.lHoldLot}

Ticked by default: when you save, the lot is put **on hold** (if it is released), with the reason *NC n: what is wrong*. It is then left out of the sales and the production orders until the nonconformance is closed. Untick it for a problem that does not make the lot unsafe.

### Lot status {#qa.nc.cLotStatus}

The current status of the lot (released, on hold, quarantine, rejected). To change it by hand, use [Lot status](#qa.lots).

## Decision {#qa.nc.decision}

### Root cause {#qa.nc.cCause}

Why it happened (e.g. *the cold room door was left open*, *the supplier's truck was not refrigerated*).

### Disposition {#qa.nc.cDisposition}

What is done with the product: **To decide**, **Use as is**, **Rework**, **Scrap** or **Return to supplier**. It decides the status of the lot when the nonconformance is closed (see the life above).

### Corrective action {#qa.nc.cAction}

What is done so that it does not happen again (e.g. *alarm on the cold room door*, *temperature check of every delivery*). Required to close.

## Tracking {#qa.nc.tracking}

### Created by {#qa.nc.cUser}

The user who recorded it.

### Created on {#qa.nc.dCreated}

When it was recorded.

### Closed by {#qa.nc.cClosedBy}

The user who closed it.

### Closed on {#qa.nc.dClosed}

When it was closed.

## History {#qa.nc.history}

Every step of the nonconformance, newest first: created, changed, lot put on hold, lot released or rejected, closed (with the disposition), reopened (with the reason). Every change is also in the [audit log](#admin.audit).

## Close {#qa.nc.close}

Saves what is on the screen and closes the nonconformance (see the life above). Only the roles with the **Close** permission see the button.

## Reopen {#qa.nc.reopen}

Opens a closed nonconformance again; the reason is asked and kept in the history.
