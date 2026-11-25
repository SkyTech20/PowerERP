# Customers {#sales.customers}

The companies you sell to: billing address, taxes, payment term, price list, ship-to addresses and contacts. What is set here is proposed on every new invoice of the customer.

**Where:** **Sales > Customers**.

## List {#sales.customers.list}

Columns: Code, Name, City, Province, Tax group, Invoice language, Price list, number of ship-to addresses and Active.

Filters: Tax group, Price list and Active. **New** creates a customer.

## General {#sales.customers.general}

### Code {#sales.customers.cCode}

Short code in capitals (for example `HOTEL-LAURIER`). Required. It cannot be changed later.

### Name {#sales.customers.cName}

The usual name of the customer. Required.

### Active {#sales.customers.lActive}

Only an active customer is found by the customer search of the invoice. Uncheck it to stop using a customer that has invoices.

### Legal name {#sales.customers.cLegalName}

The registered name. When it differs from the usual name, it is the one printed on the invoice.

### Invoice language {#sales.customers.cLang}

*French* or *English*. It sets the language of the printed invoice and credit note, and which description of the product goes on the lines. An invoice can still be printed in the other language (*Invoice language* of the invoice).

## Billing address {#sales.customers.billTo}

### Address line 1 {#sales.customers.cAddress1}

The billing address, printed under *Bill to*. The same goes for the lines below.

### Address line 2 {#sales.customers.cAddress2}

Second line of the billing address.

### City {#sales.customers.cCity}

City of the billing address.

### Province / State {#sales.customers.cProvince}

Province of the billing address (for example QC).

### Country {#sales.customers.cCountry}

Country of the billing address (for example CA).

### Postal code {#sales.customers.cZipCode}

Postal code of the billing address.

### Phone {#sales.customers.cPhone}

Phone number of the customer.

### E-mail {#sales.customers.cEmail}

Billing e-mail, used when no contact is marked *Invoices*. Invoices are not sent by e-mail yet: for information only for now.

## Taxes and billing {#sales.customers.billing}

### Tax group {#sales.customers.cTaxGroup}

The taxes charged to the customer. Required. QC = GST + QST, ON = HST 13 %, EXO = exempt. A ship-to address can have its own group, which replaces this one.

### Tax exemption no. {#sales.customers.cTaxExemptNo}

The exemption certificate or number of an exempt customer. Printed on the invoice.

### Payment term {#sales.customers.cTermCode}

The code of the payment term (for example `n30`). The list proposes the codes already used by other customers, and you can type a new one. A code `nXX` makes the printed invoice show the due date (*Échéance / Due*) = invoice date + XX days.

### Term description {#sales.customers.cTermDesc}

Text of the payment term printed on the invoice (for example *net 30 jours*). Filled in from the code, and can be changed.

### Price list {#sales.customers.cPriceList}

The customer's price list (**Sales > Price lists**). Empty: the customer pays the product's Price 1, with the *Discount %* below.

### Discount % {#sales.customers.dDiscountPct}

Discount on every line of the customer's invoices, unless the price list gives another discount (on the product's line or on its category). Between 0 and 100.

### Shipping warehouse {#sales.customers.cWarehouse}

The warehouse the customer's goods leave from. Proposed on a new invoice.

### Notes {#sales.customers.cNotes}

Internal notes.

## Ship-to addresses {#sales.customers.addresses}

The places where the customer's goods are delivered, one line per address. The default address is proposed on every new invoice.

### Code {#sales.customers.addresses.cCode}

Short code of the address (for example `HOTEL`, `OTTAWA`). Required, and unique for the customer.

### Name {#sales.customers.addresses.cName}

Name of the place, printed under *Ship to*.

### Address line 1 {#sales.customers.addresses.cAddress1}

Delivery address. Required.

### Address line 2 {#sales.customers.addresses.cAddress2}

Second line of the delivery address.

### City {#sales.customers.addresses.cCity}

City of the delivery.

### Prov. {#sales.customers.addresses.cProvince}

Province of the delivery.

### Postal code {#sales.customers.addresses.cZipCode}

Postal code of the delivery.

### Country {#sales.customers.addresses.cCountry}

Country of the delivery.

### Contact {#sales.customers.addresses.cContact}

Who receives the goods there.

### Phone {#sales.customers.addresses.cPhone}

Phone number of the place.

### Tax group {#sales.customers.addresses.cTaxGroup}

The taxes of this place. When filled in, it replaces the customer's, because the taxes follow the place of delivery. Example: HOTEL-LAURIER is QC, but the delivery to OTTAWA uses ON (HST 13 %).

### Default {#sales.customers.addresses.lDefault}

The default address is proposed on every new invoice. Only one address can be the default.

## Contacts {#sales.customers.contacts}

The people to reach at the customer.

### Name {#sales.customers.contacts.cName}

Name of the person. Required.

### Title {#sales.customers.contacts.cTitle}

Job title (for example *Purchasing manager*).

### Phone {#sales.customers.contacts.cPhone}

Phone number of the person.

### E-mail {#sales.customers.contacts.cEmail}

E-mail of the person. Required when *Invoices* is checked.

### Invoices {#sales.customers.contacts.lInvoices}

The people who receive the invoices. For information only until invoices are sent by e-mail.

## Price check {#sales.customers.check}

How much the customer pays for a product, and which rule gives that price. Nothing is saved. Use it to explain a price to the customer or to check a price list. It reads the customer as saved: save your changes first.

### Product {#sales.customers.check.cProduct}

The product to check. Only products that can be sold are listed.

### Quantity {#sales.customers.check.dQty}

The quantity. It changes the price when the price list has quantity breaks.

### Unit {#sales.customers.check.cUOM}

The unit. Empty: the sales unit of the product.

### Date {#sales.customers.check.dDate}

The date of the price. A price list counts only within its validity dates.

### The result {#sales.customers.check.result}

- **List price:** the product's Price 1.
- **Price:** the price that applies and where it comes from (price list X from N units, or the list price).
- **Discount:** the discount and where it comes from (the price list line, the category or the customer).
- **Net price:** price × (1 − discount %).
- A warning when the net price is below the product's minimum price: such a line would be refused on an invoice.

See [How the price is found](#sales.priceLists.order) in the help of the price lists.

## Delete {#sales.customers.delete}

A customer used on an invoice cannot be deleted. Uncheck *Active* instead.
