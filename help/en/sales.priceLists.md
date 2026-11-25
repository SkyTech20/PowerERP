# Price lists {#sales.priceLists}

The prices of your customers: by product, unit and quantity, with discounts by category. A price list can be shared by several customers (for example HORECA for hotels and restaurants, DIST for distributors) or belong to one customer, with the prices negotiated with it. Each customer points to its price list in its *Price list* field.

**Where:** **Sales > Price lists**.

## List {#sales.priceLists.list}

Columns: Code, Description, Valid from, Valid to, number of products, number of customers and Active. **New** creates a price list.

## General {#sales.priceLists.general}

### Code {#sales.priceLists.cCode}

Code of the price list (for example `HORECA`, `DIST`, or the code of the customer for its own prices). Required. It cannot be changed later.

### Valid from {#sales.priceLists.dStartDate}

First day the price list counts. Empty: no start. Outside its dates, or when it is not active, its customers pay the list price (Price 1 of the product).

### Valid to {#sales.priceLists.dEndDate}

Last day the price list counts. Empty: no end. It cannot be before *Valid from*.

### Active {#sales.priceLists.lActive}

Unchecked: the price list does not count, and its customers pay the list price.

### Description (French) {#sales.priceLists.cDescFR}

Name of the price list in French. Required.

### Description (English) {#sales.priceLists.cDescEN}

Name of the price list in English.

### Notes {#sales.priceLists.cNotes}

Internal notes.

### Customers {#sales.priceLists.customers}

Read-only. The customers that use this price list (their *Price list* field in **Sales > Customers**). Click one to open it.

## Prices {#sales.priceLists.lines}

One line per product and quantity break.

### Product {#sales.priceLists.lines.cProduct}

A product that can be sold.

### Unit {#sales.priceLists.lines.cUOM}

The unit of the price. Empty: the sales unit of the product. The list shows only the product's units. On an invoice in another unit, the price is converted (1 CS = 12 UN).

### From qty {#sales.priceLists.lines.dMinQty}

The quantity from which this line counts. Among several lines of the same product, the one with the highest *From qty* that the invoice quantity reaches gives the price. Example: TUBE-T8 at 15.75 from 1 to 49 and at 13.95 from 50. A product, unit and *From qty* can be on one line only.

### Unit price {#sales.priceLists.lines.dPrice}

Price per unit. Required, and not negative.

### Discount % {#sales.priceLists.lines.dDiscountPct}

Discount of this line. It replaces the discount of the category and of the customer. Use 0 for a net price, with no discount at all. Empty: the other discounts apply.

## Discounts by category {#sales.priceLists.discounts}

A discount on the products of a category, when their price line has no discount of its own.

### Product category {#sales.priceLists.discounts.cCategory}

The category of products. The discount also applies to its subcategories. A category can be on one line only.

### Discount % {#sales.priceLists.discounts.dDiscountPct}

Discount for the products of the category. Required, between 0 and 100. It replaces the customer's *Discount %*.

## How the price is found {#sales.priceLists.order}

1. **Price:** the customer's price list, if it is active, valid on the invoice date and has the product. Otherwise, the Price 1 of the product.
2. **Discount:** the discount of the price list line. Otherwise, the category's in the price list. Otherwise, the customer's. Otherwise, none.
3. **Net price** = price × (1 − discount %). Below the product's *Minimum price*, the invoice is refused.

The **Price check** tab of a customer shows this calculation for one product and the rule that applied.

## Delete {#sales.priceLists.delete}

A price list used by a customer cannot be deleted. Remove it from those customers first, or uncheck *Active*.
