# Sales invoices {#sales.invoices}

Invoices and credit notes to your customers (B2B, Quebec, in CAD). An invoice starts as a draft, is checked, then posted: only then does the stock go out and the invoice get its number. Payments are not followed yet (no accounts receivable).

**Where:** **Sales > Invoices**.

## List {#sales.invoices.list}

Columns: Draft #, Type (*Invoice* or *Credit note*), Invoice no., Invoice credited, Date, Customer, Name, Customer PO, number of lines, Total and Status.

Filters: Status, Type and Customer. **New** creates a draft invoice.

## Life of an invoice {#sales.invoices.cycle}

1. **Draft:** created with **New**. It gets a draft number (*Draft #*) and can be changed or deleted freely.
2. **Check:** tells whether the invoice can be posted and shows the stock that will go out. It changes nothing. See [Check](#sales.invoices.check).
3. **Post:** takes the stock out, gives the final invoice number and locks the document. A posted invoice can no longer be changed or deleted: to correct it, make a [credit note](#sales.invoices.creditnote). See [Post](#sales.invoices.post).
4. **Print:** prints or saves as PDF, in French or English. It also works on a draft, with a DRAFT watermark. See [Print](#sales.invoices.print).

## Header {#sales.invoices.header}

### Invoice credited {#sales.invoices.cOrigInvoice}

Credit notes only. The number of the invoice this note credits. Read-only.

### Customer {#sales.invoices.cCustomer}

The customer billed. Required. Only active customers can be picked. When you choose one, the system proposes the customer's default ship-to address, warehouse, language and payment term. On a credit note it comes from the invoice and cannot be changed.

### Date {#sales.invoices.dDate}

Date of the invoice. It decides the price (validity of the price list) and the tax rates.

### Customer PO {#sales.invoices.cCustomerPO}

The customer's purchase order number. Printed on the invoice.

### Ship to {#sales.invoices.cShipTo}

The customer's delivery address. The taxes follow the place of delivery: shipping a Quebec customer's goods to Ottawa gives HST-ON instead of GST + QST.

### Tax group {#sales.invoices.cTaxGroup}

Read-only. The tax group of the ship-to address, else the customer's.

### Shipping warehouse {#sales.invoices.cWarehouse}

The warehouse the goods leave from when the invoice is posted.

### Invoice language {#sales.invoices.cLang}

*The customer's* (the one on the customer record), *French* or *English*, for this invoice only. It sets the language of the printout and of the product descriptions on the lines.

### Payment term {#sales.invoices.cTermCode}

Payment term printed on the invoice. A code `nXX` (for example `n30`) calculates the due date: invoice date + XX days. Not shown on a credit note.

### Term description {#sales.invoices.cTermDesc}

Text of the payment term, printed (for example *net 30 days*). Filled in from the term code, and can be changed.

### Notes {#sales.invoices.cNotes}

Text printed on the invoice, above the company's note.

### Posted on {#sales.invoices.dPosted}

Date the invoice was posted. Posted invoices only.

### Posted by {#sales.invoices.cPostedBy}

User who posted the invoice. Posted invoices only.

### Cost of goods sold {#sales.invoices.dCost}

Cost of the stock that went out, at the cost of each lot. Posted invoices only.

## Lines {#sales.invoices.lines}

Prices, discounts, taxes and totals are recalculated as you type.

### Product {#sales.invoices.lines.cProduct}

A product that can be sold and is active. Choosing it fills in the description, the unit, the customer's price and discount.

### Description {#sales.invoices.lines.cDescription}

Comes from the product, in the language of the invoice. Can be changed.

### Quantity {#sales.invoices.lines.dQty}

Quantity sold, in the unit of the line.

### Unit {#sales.invoices.lines.cUOM}

Filled in with the product's sales unit. The list shows only the product's units: its stock unit, its packagings and the general conversions of the stock unit (for example KG, G and LB for flour).

### Unit price {#sales.invoices.lines.dPrice}

The customer's price: from the customer's price list, else the product's Price 1. A price typed by hand is kept. Changing the product, the quantity or the unit takes the customer's price again.

### Discount % {#sales.invoices.lines.dDiscountPct}

The customer's discount: from the price list line, else the price list category, else the customer. A discount typed by hand is kept.

### Net price {#sales.invoices.lines.dNetPrice}

Price × (1 − discount %). Calculated. Below the product's *Minimum price*, the invoice cannot be saved.

### Amount {#sales.invoices.lines.dAmount}

Quantity × net price. Calculated.

### Tax {#sales.invoices.lines.cTaxGroup}

Tax group of the line: the invoice's, except for zero-rated products (for example bread, group ZERO), which keep their own.

### Return {#sales.invoices.lines.lReturn}

Credit notes only. Checked: the goods come back into stock, into the same lot, expiry date, serial number and location they left from, at the cost they went out. Unchecked: only the price is credited (a price adjustment) and nothing comes back into stock. Only for stocked products.

## Totals {#sales.invoices.totals}

- **Discounts given:** how much the customer saved with the discounts.
- **Subtotal:** sum of the lines.
- **Taxes:** one line per tax (GST, QST, HST...), calculated on the total of the lines of each tax group, at the invoice date.
- **Total.**

## Buttons {#sales.invoices.buttons}

### Save {#sales.invoices.save}

Saves the draft. Refused when a line's net price is below the product's minimum price.

### Check {#sales.invoices.check}

Shows *Ready to post* or *To fix before posting*, with the problems (for example not enough stock on line 1, an invoice with no lines, no warehouse). Also shows *Stock to take out*: which lot, serial number and location will go out, in each product's stock out order (FEFO, FIFO or LIFO). An expired lot is never sold. Nothing is changed.

### Post {#sales.invoices.post}

Asks for confirmation, checks again and posts. If anything fails, nothing leaves the stock. After posting, the invoice is read-only and *Stock taken out* shows the cost of each line.

### Print {#sales.invoices.print}

Opens the print page, to print or save as PDF from the browser. The language is the invoice's; to force one, add `?lang=en` or `?lang=fr` to the address of the page.

### Credit note {#sales.invoices.credit}

Posted invoices only. Makes a credit note from the invoice: see [Credit note](#sales.invoices.creditnote).

### Delete {#sales.invoices.delete}

Drafts only. A deleted draft does not use up an invoice number, since the number is given when posting.

## Numbering {#sales.invoices.numbers}

- Drafts: *Draft #* 1, 2, 3...
- Posted invoices: 1, 2, 3... or from the number in *Invoice numbers start at* (**Administration > System settings > Company profile**).
- Posted credit notes: NC-1, NC-2...

## Credit note {#sales.invoices.creditnote}

Gives goods back, or a price reduction, on an invoice already posted.

**How:** open the posted invoice, click **Credit note** and confirm. A draft credit note opens with every line of the invoice not credited yet.

What changes compared with an invoice:

- *Invoice credited* shows the invoice's number.
- Customer, Ship to, Shipping warehouse and Tax group come from the invoice and cannot be changed. There is no payment term.
- Each line credits a line of the invoice, at the invoice's price and discount unless you type others. The quantity cannot be more than what was invoiced and not credited yet. You can delete lines or lower quantities. A product that is not on the invoice is refused.
- *Return* decides whether the goods come back into stock: see [Return](#sales.invoices.lines.lReturn).

When posted, the note gets the number NC-n and the panel shows *Stock brought back*. **Inventory > Stock movements** shows a positive ADJ adjustment with document SO NC-n. The original invoice stays posted, with the same number.

Clicking **Credit note** again on the invoice brings only what is left to credit. When everything is credited: *Every line of this invoice is already credited*.

The printout says NOTE DE CRÉDIT / CREDIT NOTE, with the number NC-n and the line *Facture créditée / Invoice credited*.

## Common error messages {#sales.invoices.errors}

| Message | Cause |
|---|---|
| The net price is below the minimum price of the product | The line's net price is lower than the product's *Minimum price*. |
| Not enough stock available | The warehouse does not have the quantity (expired lots do not count). |
| More than the quantity invoiced and not credited yet | A credit note with a quantity above what is left on the invoice line. |
| This product is not on the invoice credited | A credit note with a product that was not on the invoice. |
| Only a posted invoice can be credited | Trying to credit a draft. |
| This product is not sold | The product has *Can be sold* unchecked or is not active. |
| Every line of this invoice is already credited | The invoice is fully credited. |
