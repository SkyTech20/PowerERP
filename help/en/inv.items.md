# Products {#inv.items}

The product record is the centre of the ERP: purchasing, stock, production recipes and sales all read it. A product can be a good or a service, stocked or not.

**Where:** **Inventory > Products**. Click a product to open it, or **New** to create one.

Some fields are marked *For information only*: they are kept and shown, but nothing uses them yet. They are there for modules to come (accounting, shipping, labels).

## List {#inv.items.list}

Columns: Product, Description, Category, Product or service, Class, Unit, On hand, Available, Price 1 and Status.

Filters: Status, Product or service, Stock type, Class and Category. The search looks in the code, the French and English descriptions, the category, the brand, the barcode (UPC), the manufacturer part number and the manufacturer.

*On hand* and *Available* are shown only for products with *Stocked* checked. The others show "—".

## General {#inv.items.general}

### Product {#inv.items.cCode}

The unique code of the product, in English and without spaces (for example `TUBE-T8`). Required. It cannot be changed once saved.

### Status {#inv.items.cStatus}

*Active*, *Inactive* or *Discontinued*. Only an active product can be put on an invoice and is bought by the replenishment.

### Category {#inv.items.cCategory}

The category of the product (**Inventory > Categories / units**). It groups the products and is the base of the discounts by category of the price lists.

### Product or service {#inv.items.cNature}

*Product* is a good. *Service* is labour, freight or consulting. When a service is saved, the system sets *Stock type* to *Non-physical* and clears the *Class*.

### Stock type {#inv.items.cStockType}

*Physical*: something that sits on a shelf. *Non-physical*: a licence, a subscription or a digital item, with no stock. Shown for products only.

### Class {#inv.items.cClass}

The role of the product: *Raw material*, *Kit / assembly*, *Finished product*, *Consumable* or *Fixed asset*. Leave it empty for goods bought for resale. Used to filter and sort the list of products.

### Description (French) {#inv.items.cDescFR}

Short description in French. Required. It goes on the invoices of French-speaking customers.

### Description (English) {#inv.items.cDescEN}

Short description in English. It goes on the invoices of English-speaking customers. When empty, the French one is used.

### Long description (French) {#inv.items.cLongDescFR}

Longer free text, for a spec sheet or a catalogue. For information only.

### Long description (English) {#inv.items.cLongDescEN}

The same in English. For information only.

### Brand {#inv.items.cBrand}

Brand of the product. The search finds a product by its brand. For information only.

### Model {#inv.items.cModel}

Model of the product. For information only.

### Manufacturer {#inv.items.cManufacturer}

Who makes the product. The search finds a product by its manufacturer. For information only.

### Manufacturer part number {#inv.items.cMfrPartNo}

The manufacturer's code for the product. The search finds a product by this number. For information only.

### Barcode (UPC / EAN) {#inv.items.cUPC}

The barcode of the product. The search finds a product by its barcode. It will be scanned at reception and picking once scanners are used.

### Picture (link) {#inv.items.cImageUrl}

Link to a picture of the product. For information only.

### Spec sheet (link) {#inv.items.cSpecUrl}

Link to the technical sheet. For information only.

### Safety data sheet (link) {#inv.items.cSdsUrl}

Link to the safety data sheet (SDS / WHMIS). For information only.

## Units and dimensions {#inv.items.units}

### Stock unit {#inv.items.cStockUOM}

The unit the stock is counted in (UN, KG, L...). Required. Every balance, cost and movement is in this unit.

### Purchase unit {#inv.items.cPurchaseUOM}

The unit the supplier sells in (for example CS, a case). It needs a conversion to the stock unit, in [Other units of this product](#inv.items.conversions) (for example 1 CS = 25 UN) or in the general conversions. Without one, the screen shows a warning and the product cannot be saved. The replenishment uses this conversion to suggest the purchase in the supplier's unit.

### Sales unit {#inv.items.cSalesUOM}

The unit the product is sold in. It is the default unit of the invoice lines and of the price check. Like the purchase unit, it needs a conversion to the stock unit.

### Weight {#inv.items.dWeight}

Weight of one stock unit. For information only.

### Weight unit {#inv.items.cWeightUOM}

kg or lb. For information only.

### Volume (m³) {#inv.items.dVolume}

Volume of one stock unit. For information only.

### Length {#inv.items.dLength}

For information only.

### Width {#inv.items.dWidth}

For information only.

### Height {#inv.items.dHeight}

For information only.

### Dimension unit {#inv.items.cDimUOM}

cm or inches, for the length, width and height. For information only.

## Other units of this product {#inv.items.conversions}

The packagings of this product, in stock units. This is where you say how much the purchase or sales unit is worth when it is not the stock unit. Example: `1 BAG = 25` (KG). Recipes, invoices and movements can then use BAG, and the system converts it to KG.

The general conversions, valid for every product (1 KG = 1000 G), are in **Inventory > Categories / units > Conversions** and apply here too. The stock unit cannot be converted into itself.

### 1 unit of {#inv.items.conversions.cUOM}

The other unit (for example BAG, CS).

### Equals (stock units) {#inv.items.conversions.dFactor}

How many stock units one of this unit holds. `25` on a BAG line of a product counted in KG: 1 BAG = 25 KG.

### Notes {#inv.items.conversions.cNotes}

Free text, for example the size of the packaging.

## Costs and prices {#inv.items.prices}

### Costing method {#inv.items.cCostMethod}

*Moving average*: the stock is valued at the average cost of the receipts. *Standard*: the standard cost is used when there is one, otherwise the average cost.

### Standard cost {#inv.items.dStdCost}

Cost set by the company. Used by the *Standard* method and by the cost roll-up of the recipes.

### Average cost {#inv.items.dAvgCost}

Calculated by the system from the stock receipts. Read-only.

### Last cost {#inv.items.dLastCost}

Cost of the last receipt. Read-only. Used when there is no average cost yet.

### Currency {#inv.items.cCurrency}

Currency of the product's prices. Sales are in CAD only for now. For information only.

### Price 1 (list) {#inv.items.dPrice1}

The list price, per sales unit. It is the invoice price when the customer has no price list, or when the customer's price list does not have the product.

### Price 2 {#inv.items.dPrice2}

Alternative price (wholesale, resale...). For information only: the prices by customer are set in the price lists (**Sales > Price lists**). The same goes for Price 3 to Price 5.

### Price 3 {#inv.items.dPrice3}

See [Price 2](#inv.items.dPrice2).

### Price 4 {#inv.items.dPrice4}

See [Price 2](#inv.items.dPrice2).

### Price 5 {#inv.items.dPrice5}

See [Price 2](#inv.items.dPrice2).

### Minimum price {#inv.items.dMinPrice}

The lowest net price, per sales unit. An invoice line whose net price (after the discount) is below it is refused when saving.

### Margin % (price 1) {#inv.items.dMarginPct}

Margin of Price 1 over the average cost. Calculated, read-only, shown once the product is saved.

## Taxes and accounting {#inv.items.tax}

### Sales tax group {#inv.items.cSalesTaxGroup}

Tax group of the product when sold (**Administration > Taxes**). The taxes of an invoice come from the customer and the place of delivery. This field changes the line only when the product's group is zero-rated or exempt, for example ZERO for basic groceries (bread): the line has no tax even if the customer is taxed. With a normal group (QC), the customer's taxes apply.

### Purchase tax group {#inv.items.cPurchaseTaxGroup}

Tax group when bought. For information only.

### Eco fee {#inv.items.dEcoFee}

Environmental fee, when one applies. For information only.

### Eco fee program {#inv.items.cEcoFeeCode}

The program of the eco fee (for example electronics, batteries). For information only.

### GL - sales {#inv.items.cGLSales}

Sales account of the product. Will be used once the accounting is linked. For information only.

### GL - purchases / expenses {#inv.items.cGLPurchase}

Purchases or expenses account. For information only.

### GL - inventory {#inv.items.cGLInventory}

Inventory account. For information only.

### GL - cost of sales {#inv.items.cGLCOGS}

Cost of goods sold account. For information only.

### Cost center {#inv.items.cCostCenter}

Cost center for the accounting. For information only.

### Project {#inv.items.cProject}

Project for the accounting. For information only.

## Inventory {#inv.items.inv}

The fields of this tab are shown for physical products only.

### Stocked {#inv.items.lStocked}

Checked: the system keeps the quantity and value of the product. Unchecked: the product can be sold or bought, but it has no balance and nothing leaves the stock when the invoice is posted. It cannot be unchecked while there is stock.

### Default warehouse {#inv.items.cDefaultWarehouse}

The main warehouse of the product. The replenishment uses it when there is no parameter by warehouse.

### ABC class {#inv.items.cABCClass}

A, B or C ranking by importance (turnover or value). For information only.

### Shelf life (days) {#inv.items.iShelfLifeDays}

Usual shelf life in days. For information only.

### Lot numbers {#inv.items.lLotControl}

Every receipt and issue needs a lot number. The balance is kept by lot. On a credit note, the goods come back into the same lot. A location holds one lot of the product at a time.

### Serial numbers {#inv.items.lSerialControl}

Every unit needs a serial number. The product moves one unit at a time (for example the laptop LAP-14I7).

### Expiry date {#inv.items.lExpiryControl}

Receipts need an expiry date. An expired lot is never sold, and with *Stock out order* on *Automatic* the stock goes out FEFO.

### Stock out order {#inv.items.cPickPolicy}

Which stock goes out first when an invoice is posted. *Automatic*: FEFO if the product has an expiry date, otherwise FIFO. *FEFO*: first expired, first out. *FIFO*: first in, first out. *LIFO*: last in, first out.

## Sales and logistics {#inv.items.log}

### Can be sold {#inv.items.lSellable}

Only a product with this checked is found by the product search of the invoice and of the price check. An invoice refuses a product that cannot be sold.

### Can be purchased {#inv.items.lPurchasable}

Only a product with this checked is suggested by **Inventory > Replenishment**.

### PO required {#inv.items.lPORequired}

The purchase needs a purchase order. For information only.

### Dangerous goods {#inv.items.lHazardous}

Dangerous goods (TDG). For information only.

### Warranty (months) {#inv.items.iWarrantyMonths}

For information only.

### Country of origin {#inv.items.cCountryOrigin}

For export and customs. For information only.

### HS code (customs tariff) {#inv.items.cHSCode}

Customs tariff code. For information only.

### Freight class {#inv.items.cFreightClass}

For the carriers. For information only.

### Notes {#inv.items.cNotes}

Free notes. For information only.

## Suppliers {#inv.items.lines}

One line per supplier of the product. The price is per purchase unit.

### Supplier code {#inv.items.lines.cSupplierCode}

A supplier from **Accounts Payable > Suppliers**.

### Supplier item number {#inv.items.lines.cSupplierItem}

The code of the product in the supplier's catalogue.

### Price {#inv.items.lines.dPurchasePrice}

Purchase price per purchase unit.

### Currency {#inv.items.lines.cCurrency}

Currency of the purchase price.

### Lead time (days) {#inv.items.lines.iLeadTimeDays}

Delivery time. The replenishment uses it.

### Min. qty {#inv.items.lines.dMinOrderQty}

Minimum order quantity. The replenishment rounds its suggestion up to it.

### Preferred {#inv.items.lines.lPreferred}

The preferred supplier is the one the replenishment uses. When none is checked, the first line is used.

## Stock {#inv.items.stock}

Read-only. The balance by warehouse: *On hand*, *Reserved*, *Available*, *Reorder point* and *Value*, with the totals on hand, available and on order. **Movement** opens a new stock movement with the product filled in. **Stock on hand** opens the full view, with lot, serial number and location. Shown for stocked products only.

## Manufacturing {#inv.items.mfg}

A summary of the production data of the product: *Make or buy*, *Setup family*, *Manufacturing lot* (minimum, multiple and lead time), *Traceability* and *Attributes*. **Edit** opens the full record in **Production > Manufactured items**. When the product has no production data yet, **Add the manufacturing data** creates it.

- **Make or buy:** *Make* (made here), *Buy* (bought) or *Make or buy* (both). *Phantom* is shown next to it for a sub-assembly that is never stocked: its materials go straight to the order of the parent product.
- **Setup family:** which line of the setup matrix applies when this product follows another on the same machine (for example sweet dough after savoury).
- **Manufacturing lot:** the smallest quantity to make, the multiple (for example batches of 60) and the lead time in days.
- **Traceability:** *None*, *By lot* or *By serial number*. For a lot or serial number, the matching control of the [Inventory](#inv.items.inv) tab must be checked.
- **Attributes:** characteristics of the product (width, basis weight, colour...), compared with the limits of the machines in the recipes.

## Saving and deleting {#inv.items.rules}

- *Product*, *Stock unit* and *Description (French)* are required.
- The category, units, tax groups, warehouse and suppliers must exist.
- The purchase and sales units need a conversion to the stock unit (on the product or in the general conversions).
- A service becomes non-physical, with no class. A non-physical product never has stock.
- A product with stock cannot stop being *Stocked*.

### Delete {#inv.items.delete}

A product used in a movement, an invoice or a recipe cannot be deleted. Set its *Status* to *Inactive* or *Discontinued* instead.
