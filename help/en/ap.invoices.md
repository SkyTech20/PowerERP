# Supplier invoices {#ap.invoices}

The invoices received from the suppliers, typed here or sent by SkyAI. An invoice bills the receptions of a purchase order: they are then no longer *Not invoiced yet*.

**Where:** **Accounts Payable > Invoices**.

## List {#ap.invoices.list}

Columns: Invoice number, Supplier code, Supplier, Invoice date, PO number, Invoice total, Status and Source (*Manual entry* or *SkyAI*). Filters: Status and Source. **New** creates an invoice. The dashboard counts the *Draft* and *Approved* invoices as open.

## General {#ap.invoices.general}

### Supplier code {#ap.invoices.cNoFourn}

The supplier of the invoice. Required.

### Supplier {#ap.invoices.cNomFourn}

Name of the supplier. Read only, filled from the code.

### Status {#ap.invoices.cStatut}

*Draft*, *Approved*, *Posted* or *Paid*. Chosen by hand for now. An invoice from SkyAI arrives as *Posted*, or *Draft* when SkyAI found it incomplete.

### Invoice number {#ap.invoices.cNoFacture}

The supplier's number of the invoice. Required. The same supplier cannot have two invoices with the same number.

### Invoice date {#ap.invoices.dDateFacture}

Date on the invoice. Required. Today by default.

### PO number {#ap.invoices.cNoCommAch}

The purchase order billed. When no line gives a reception number, the invoice bills every open reception of this order; when all its receptions are billed, the order is no longer *Not invoiced yet*.

### Currency {#ap.invoices.cDevise}

*CAD*, *USD* or *EUR*: the currency of the amounts.

## Lines {#ap.invoices.lines}

One line per item or charge billed. A line with no item, no description and no amount is dropped when saved. The amount of a line is the quantity × the unit cost.

### Item {#ap.invoices.lines.cCodeProduit}

Code of the product billed. Empty = `LINE`.

### Description {#ap.invoices.lines.cDescription}

What is billed.

### Qty {#ap.invoices.lines.dQuantite}

Quantity billed. Empty = 1.

### Unit cost {#ap.invoices.lines.dCoutUnitaire}

Price of one unit.

### GL {#ap.invoices.lines.cGL}

The GL account the line is charged to.

### CC1 {#ap.invoices.lines.cCC1}

The department (cost center) the line is for, picked from the list (**General Ledger > GL Accounts / Cost Centers**, tab **Cost centers**). Required when the GL account of the line has *Requires a cost center*.

### CC2 {#ap.invoices.lines.cCC2}

A sub-department of the department in CC1 (the list shows only its own). Empty: the department itself.

### Reception {#ap.invoices.lines.iNoReception}

The reception this line bills. Saving the invoice marks that reception as invoiced.

## Totals {#ap.invoices.totals}

Subtotal (the lines), freight, taxes and invoice total. Type the taxes as they are on the supplier's invoice: they are not calculated here.

### Freight {#ap.invoices.dTransport}

Shipping cost on the invoice.

### TPS {#ap.invoices.dTotalTPS}

The GST on the invoice.

### TVQ {#ap.invoices.dTotalTVP}

The QST on the invoice.
