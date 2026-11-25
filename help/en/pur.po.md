# Purchase orders {#pur.po}

The orders sent to the suppliers, with their lines and totals. The receptions are made against them, and the supplier invoices bill them.

**Where:** **Purchasing > Purchase orders**.

## List {#pur.po.list}

Columns: PO number, Order date, Supplier code, Supplier name, Buyer name, Lines, Total, Blanket order and Not invoiced yet. Filter: Not invoiced yet. **New** creates a purchase order. **Inventory > Replenishment** can also create them from its suggestion.

## General {#pur.po.general}

### PO number {#pur.po.cPO}

Number of the order. Required, unique. It cannot be changed later.

### Order date {#pur.po.dCreationDate}

Date of the order. Today by default.

### Supplier code {#pur.po.cSupplierCode}

The supplier (**Accounts Payable > Suppliers**). Required. Choosing it fills the supplier name, and its TPS / TVQ numbers decide the taxes.

### Supplier name {#pur.po.cSupplierName}

Filled from the supplier. Empty = the name of the supplier when saved.

### Buyer code {#pur.po.cBuyerCode}

Who buys. Choose from the list or type a code; choosing fills the buyer name.

### Buyer name {#pur.po.cBuyerName}

Name of the buyer.

### Requester {#pur.po.cApplicantCode}

Who asked for the purchase. Free text.

### Company {#pur.po.COMPANY}

The company of the order. Read only.

### Blanket order {#pur.po.lBlanketOrder}

An open order for a period, received and billed in several times.

### Not invoiced yet {#pur.po.lUnbilled}

Checked: the order still waits for a supplier invoice (checked on a new order). A supplier invoice unchecks it when it bills all the receptions of the order. The quantity *on order* of a product (Stock on hand, Replenishment) counts only the orders not invoiced yet, minus what was received.

## Lines {#pur.po.lines}

One line per item ordered. A line with no item and no description is dropped when saved. The amount of a line is the quantity × the unit cost.

### # {#pur.po.lines.cUnique}

Number of the line. Given in order.

### Item {#pur.po.lines.cProductcode}

Code of the product ordered.

### Description {#pur.po.lines.cProductDesc}

What is ordered.

### Qty {#pur.po.lines.dQuantity}

Quantity ordered, in the stock unit.

### Unit cost {#pur.po.lines.dUnitCost}

Price of one unit.

## Totals {#pur.po.totals}

Subtotal (the lines), freight, taxes and total. TPS 5 % and TVQ 9.975 % are calculated on the subtotal + freight when the supplier has a TPS / TVQ number.

### Freight {#pur.po.dFreight}

Shipping cost added to the order. It is taxed with the lines.

### TPS {#pur.po.dGST}

The federal tax (GST). Calculated, read only.

### TVQ {#pur.po.dPST}

The Quebec tax (QST). Calculated, read only.
