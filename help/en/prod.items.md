# Manufactured items {#prod.items}

The manufacturing data of the products: made or bought, setup family, manufacturing lot, traceability and attributes. Only a product that is made (*Make*, or *Make or buy*) can get a recipe. The product itself is in **Inventory > Products**: its tab **Manufacturing** shows a summary of these data, with a link here.

**Where:** **Production > Manufactured items**.

## List {#prod.items.list}

Columns: Product, Description, Make or buy, Setup family, Minimum lot, Lead time (days) and Traceability. Filters: Make or buy and Setup family. **New** adds the manufacturing data of a product.

## Manufacturing {#prod.items.mfg}

### Product {#prod.items.cProduct}

The product (**Inventory > Products**). Required. A product has one line here. It cannot be changed later.

### Make or buy {#prod.items.cMakeBuy}

*Make*, *Buy* or *Make or buy*. Only a made product (*Make*, *Make or buy*) gets recipes and production orders.

### Phantom {#prod.items.lPhantom}

A sub-assembly never stocked: its materials go up to the order of the parent product. A phantom is made, so it cannot be *Buy*.

### Setup family {#prod.items.cSetupFamily}

Which line of the [Setup matrix](#prod.setupmatrix) applies when this product follows another on a machine.

## Manufacturing lot {#prod.items.lots}

Minimum and multiple of the quantity to make, and the lead time: what the planning (MRP) will suggest.

### Minimum lot {#prod.items.dMfgLotMin}

The smallest quantity to make at once, in the stock unit.

### Lot multiple {#prod.items.dMfgLotMultiple}

The quantity to make is rounded up to a multiple of this (for example trays of 24).

### Lead time (days) {#prod.items.iMfgLeadDays}

Days needed to make the product.

## Traceability {#prod.items.trace}

### Traceability {#prod.items.cTraceLevel}

*None*, *By lot* or *By serial number*. *By lot* needs the lot control of the product, and *By serial number* its serial control (**Inventory > Products**, tab **Inventory**). Otherwise saving is refused.

### Notes {#prod.items.cNotes}

Free text.

## Attributes {#prod.items.attributes}

The measures of the product (width, basis weight, colour...). The recipes compare them with the limits of the resources (**Production > Resources (machines)**, tab **Capabilities and attributes**) and warn when the product is outside them. An attribute is listed once.

### Attribute {#prod.items.attributes.cAttribute}

Name of the attribute, for example `Width`. Use the same name as in the resources.

### Unit {#prod.items.attributes.cUOM}

Unit of the value (for example `M`).

### Number {#prod.items.attributes.dNumber}

The value of the product when it is a number. This is what is compared with the limits of the resources.

### Text {#prod.items.attributes.cValue}

The value when it is not a number (for example a colour).
