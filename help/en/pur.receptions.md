# Receptions {#pur.receptions}

The goods received against a purchase order. What is received lowers the quantity *on order* of the products. For now a reception does not change the stock on hand: enter the receipt in **Inventory > Stock movements** too.

**Where:** **Purchasing > Receptions**.

## List {#pur.receptions.list}

Columns: Reception number, Reception date, PO number, Supplier code, Supplier name, Status, Lines, Total and Not invoiced yet. Filter: Not invoiced yet. **New** creates a reception.

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

## Lines {#pur.receptions.lines}

One line per item received. A line with no item and no description is dropped when saved. The amount of a line is the quantity received × the unit cost.

### Item {#pur.receptions.lines.CodeArticle}

Code of the product received.

### Description {#pur.receptions.lines.Description}

What is received.

### Qty ordered {#pur.receptions.lines.QuantiteCommandee}

Quantity on the purchase order. For comparison.

### Qty received {#pur.receptions.lines.QuantiteRecue}

Quantity really received. It is taken off the quantity on order.

### Unit cost {#pur.receptions.lines.PrixUnitaire}

Price of one unit.

### GL {#pur.receptions.lines.cGL}

The GL account of the line, for the supplier invoice.

### CC1 {#pur.receptions.lines.cCC1}

First cost center of the line.

### CC2 {#pur.receptions.lines.cCC2}

Second cost center of the line.

## Totals {#pur.receptions.totals}

Subtotal (the lines), freight, taxes and total, in the currency of the reception. TPS 5 % and TVQ 9.975 % are calculated on the subtotal + freight when the supplier has a TPS / TVQ number.

### Freight {#pur.receptions.Transport}

Shipping cost of the reception. It is taxed with the lines.

### TPS {#pur.receptions.TPS}

The federal tax (GST). Calculated, read only.

### TVQ {#pur.receptions.TVQ}

The Quebec tax (QST). Calculated, read only.
