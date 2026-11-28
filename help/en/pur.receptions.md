# Receptions {#pur.receptions}

The goods received against a purchase order. What is received lowers the quantity *on order* of the products. **Put in stock** then brings the goods into the stock, with their lot, the supplier's lot, expiry date and location: this is what lets you trace a lot back to its supplier (one step back of the food traceability rules, SFCR).

**Where:** **Purchasing > Receptions**.

## List {#pur.receptions.list}

Columns: Reception number, Reception date, PO number, Supplier code, Supplier name, Status, Lines, Total, Not invoiced yet and In stock. Filters: Not invoiced yet, In stock. **New** creates a reception.

## Life of a reception {#pur.receptions.cycle}

1. **New**, pick the PO: the supplier and the lines are filled. Change the quantities received, type the supplier's lot of each line, **Save**.
2. **Check**: shows where each line will go (location, lot, expiry) and what must be fixed first. Nothing is changed.
3. **Put in stock**: the goods go into the stock. The reception shows the badge *In stock* and can no longer be changed or deleted.

A mistake found later is corrected with a movement in **Inventory > Stock movements** (an adjustment or a transfer).

## General {#pur.receptions.general}

### Reception number {#pur.receptions.NoReception}

Number of the reception, digits only. Required, unique. It cannot be changed later.

### Reception date {#pur.receptions.DateReception}

Day the goods arrived. Required. Today by default.

### PO number {#pur.receptions.NoBonCommande}

The purchase order received. Required. Choosing it fills the supplier (when empty) and, when the reception has no lines yet, one line per line of the order, with the quantity received equal to the quantity ordered.

### Status {#pur.receptions.Statut}

*Reçu*, *En cours* or *Partiellement reçu*, or any text. For information.

### Supplier code {#pur.receptions.CodeFournisseur}

The supplier. Filled from the purchase order; its TPS / TVQ numbers decide the taxes.

### Supplier name {#pur.receptions.Fournisseur}

Filled from the supplier. Empty = the name of the supplier when saved.

### Warehouse {#pur.receptions.Entrepot}

The warehouse that received the goods.

### Received by {#pur.receptions.ResponsableReception}

Who received the goods. Free text.

### Currency {#pur.receptions.Devise}

*CAD*, *USD* or *EUR*: the currency of the amounts.

### Not invoiced yet {#pur.receptions.lUnbilled}

Checked: the reception still waits for a supplier invoice (checked on a new reception). A supplier invoice that bills it unchecks it: an invoice line with its reception number, or an invoice on its purchase order with no reception numbers.

### Comments {#pur.receptions.Commentaires}

Free text (damage, missing boxes...).

### Put in stock on {#pur.receptions.dStockPosted}

When the reception was put into the stock. Shown once it is in stock.

### Put in stock by {#pur.receptions.cStockPostedBy}

The user who put the reception into the stock.

## Lines {#pur.receptions.lines}

One line per item received. A line with no item and no description is dropped when saved. The amount of a line is the quantity received × the unit cost. The quantities are in the **stock unit** of the product (like the PO lines).

To receive one item in two lots, add a second line with the same item and split the quantity.

### Item {#pur.receptions.lines.CodeArticle}

Code of the product received (filled from the purchase order). A line without an item (freight, a service) is not put in stock.

### Description {#pur.receptions.lines.Description}

What is received.

### Qty ordered {#pur.receptions.lines.QuantiteCommandee}

Quantity on the purchase order. For comparison.

### Qty received {#pur.receptions.lines.QuantiteRecue}

Quantity really received, in stock units. It is taken off the quantity on order, and it is the quantity that goes into the stock. 0 = nothing received on this line.

### Unit cost {#pur.receptions.lines.PrixUnitaire}

Price of one unit. It is the cost of the stock received, and it updates the average cost and the last cost of the product. Amounts in another currency than CAD are taken as CAD (Check warns about it).

### Supplier lot {#pur.receptions.lines.cSupplierLot}

The supplier's lot number, as printed on the package or the delivery slip. Kept with the lot and shown on the stock movement: it answers "which lot of the supplier is in our lot?" in a recall.

### Lot {#pur.receptions.lines.cLot}

Our lot number in the stock. Leave it empty: for a product with lot control the ERP gives `<reception>-<line>` (for example `900107-1`). Type one only if you number your lots yourself. Products without lot control have no lot.

### Expiry {#pur.receptions.lines.dExpiry}

Expiry date of the goods. Leave it empty: for a product with expiry control the ERP takes the reception date + the shelf life of the product (**Inventory > Products**, Inventory tab). Required when the product has expiry control and no shelf life.

### Location {#pur.receptions.lines.cLocation}

Where the goods are put in the warehouse. Leave it empty: the ERP takes the default location of the product in this warehouse (**Inventory > Reorder parameters**), else the receiving location of the warehouse. When the default location already holds another lot of the product (one lot per location), it takes the receiving location instead. A location you type is kept as typed.

### Serial no. {#pur.receptions.lines.cSerial}

For a product with serial numbers: one line per unit, quantity 1, with its serial number.

### GL {#pur.receptions.lines.cGL}

The GL account of the line, for the supplier invoice.

### CC1 {#pur.receptions.lines.cCC1}

The department (cost center) the line is for, picked from the list (**General Ledger > GL Accounts / Cost Centers**, tab **Cost centers**). Required when the GL account of the line has *Requires a cost center*.

### CC2 {#pur.receptions.lines.cCC2}

A sub-department of the department in CC1 (the list shows only its own). Empty: the department itself.

## Totals {#pur.receptions.totals}

Subtotal (the lines), freight, taxes and total, in the currency of the reception. TPS 5 % and TVQ 9.975 % are calculated on the subtotal + freight when the supplier has a TPS / TVQ number.

### Freight {#pur.receptions.Transport}

Shipping cost of the reception. It is taxed with the lines.

### TPS {#pur.receptions.TPS}

The federal tax (GST). Calculated, read only.

### TVQ {#pur.receptions.TVQ}

The Quebec tax (QST). Calculated, read only.

## Buttons {#pur.receptions.buttons}

### Save {#pur.receptions.save}

Saves the reception. It does not put anything in stock yet.

### Check {#pur.receptions.check}

Saves, then shows *What goes into the stock*: for each line the quantity, location, lot, supplier lot, expiry and serial number that will be used, or why the line is skipped (no item, product not stocked, nothing received). Above it, *Ready* or *To fix before putting in stock* with the problems: for example an item that is not in the products, a serial number missing, a blocked location, a location that already holds another lot. Nothing is changed.

### Put in stock {#pur.receptions.post}

Asks for confirmation, checks again and puts every line into the stock at once (one stock movement per line, document *Reception* and the reception number). If anything fails, nothing goes in. After that the reception is read-only and *Put into the stock* lists its movements; click a movement number to open it. Needs the *Post* right of the Receptions screen (**Administration > Roles**).

### Delete {#pur.receptions.delete}

Only a reception that is not in stock yet.
