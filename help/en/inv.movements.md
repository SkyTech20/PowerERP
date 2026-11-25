# Stock movements {#inv.movements}

Every change of the stock: receipts, issues, transfers, adjustments, counts and reservations. A movement is posted when it is saved and can no longer be changed or deleted: a mistake is corrected by another movement (for example an adjustment the other way).

**Where:** **Inventory > Stock movements**. The movements made by the other screens (receptions, invoices, counts, production) are listed here too, with their document.

## List {#inv.movements.list}

Columns: #, Date, Type, Product, Description, Warehouse / location (with → for a transfer), Lot / serial, Quantity, Value, Document and User. The newest first.

Filters: Type and Warehouse. **New** creates a movement.

## Types of movement {#inv.movements.types}

| Type | What it does | Quantity |
|---|---|---|
| Receipt | Stock comes in (outside a purchase order reception). | Positive. |
| Issue | Stock goes out (consumption, sample, loss). | Positive: the quantity that leaves. |
| Transfer | Stock moves from a warehouse / location to another. | Positive. |
| Adjustment | Corrects the stock. | Positive adds, negative removes. |
| Count | The difference found by a physical count (usually made by **Physical count** when it is posted). | Positive or negative. |
| Reservation | Sets stock aside: it stays on hand but is no longer available. | Positive reserves, negative releases. |

## General {#inv.movements.general}

### Type {#inv.movements.cType}

The kind of movement: see [Types of movement](#inv.movements.types). *Transfer* shows the destination fields.

### Date {#inv.movements.dDate}

Date of the movement. Required. Today by default.

### Product {#inv.movements.cProduct}

The product that moves. Only stocked products can be chosen: a product with *Stocked* unchecked has no stock.

### Description {#inv.movements.cDescFR}

Description of the product. Read-only.

### Quantity {#inv.movements.dQty}

In the stock unit of the product. Required, not zero. Receipts, issues and transfers take a positive quantity. Adjustments and reservations take a negative quantity to remove or to release. A product with serial numbers moves one unit at a time.

An issue, a transfer or a negative adjustment cannot take more than the available stock (on hand − reserved), unless the warehouse allows negative stock.

### Unit cost {#inv.movements.dUnitCost}

Cost of one stock unit of the stock that comes in. Empty: the average cost of the product. Shown for the movements that bring stock in. It changes the average cost of the product.

### Value {#inv.movements.dValue}

Quantity × cost of the movement. Read-only, shown once posted.

### Average cost after {#inv.movements.dAvgCostAfter}

The average cost of the product after this movement. Read-only, shown once posted.

## Warehouse and location {#inv.movements.place}

### Warehouse {#inv.movements.cWarehouse}

The warehouse of the stock (the origin, for a transfer). Required.

### Location {#inv.movements.cLocation}

The location inside the warehouse. Required in a warehouse that uses locations. A blocked or inactive location is refused. A location that does not accept several products refuses a second one. A location holds one lot of a product only: another lot of the same product is refused.

### To warehouse {#inv.movements.cWhTo}

Transfers only: the warehouse the stock goes to. Required.

### To location {#inv.movements.cLocTo}

Transfers only: the location the stock goes to. The destination cannot be the same as the origin.

## Traceability {#inv.movements.tracking}

### Lot {#inv.movements.cLot}

Required when the product has *Lot numbers* checked. The balance is kept by lot. A location holds one lot of a product at a time: a receipt, transfer or count bringing a second lot of the product into a location that still has the first one is refused; put it in another location.

### Serial number {#inv.movements.cSerial}

Required when the product has *Serial numbers* checked. A serial number can be in stock only once.

### Expiry date {#inv.movements.dExpiry}

Required on a receipt when the product has *Expiry date* checked. An expired lot is never sold.

## Reference {#inv.movements.reference}

### Document type {#inv.movements.cDocType}

Where the movement comes from: *Manual* (typed here), *PO*, *Reception*, *Invoice*, *Sales order*, *Count* or *Production*. The other screens fill it in.

### Document number {#inv.movements.cDocNo}

The number of that document (for example the invoice number, or SO NC-3 for a credit note).

### Reason {#inv.movements.cReason}

Why the movement was made (for example *Breakage*, *Sample*).

### Comments {#inv.movements.cComment}

Free text.

## Common error messages {#inv.movements.errors}

| Message | Cause |
|---|---|
| Not enough stock available | The warehouse / location / lot does not have the quantity available (reserved stock does not count). |
| Not that much reserved | Releasing more than what is reserved. |
| This product is not stocked | The product has *Stocked* unchecked. |
| This location is blocked or inactive | Nothing goes in or out of a blocked location. |
| A lot number is required for this product | The product has *Lot numbers* checked. |
| A product with serial numbers moves one unit at a time | Quantity other than 1 for a product with serial numbers. |
| This location accepts one product only | The location has *Several products* unchecked. |
| This location already holds another lot of this product | The location still has stock of another lot of the product (shown in brackets). One lot per product per location. |
| The destination is the same as the origin | A transfer to the same warehouse and location. |
