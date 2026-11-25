# Categories and units {#inv.setup}

The product categories (families and sub-families), the units of measure, and the general conversions between units.

**Where:** **Inventory > Categories / units**, tabs **Categories**, **Units of measure** and **Conversions**.

## Categories {#inv.setup.categories}

Columns: Code, Description, Parent category and Active. A category groups the products (**Inventory > Products**, field *Category*) and is the base of the discounts by category of the price lists. A category used by a product or a price list, or that has sub-categories, cannot be deleted.

### Code {#inv.setup.cCode}

Short code of the category (for example `LIGHT`). Required. It cannot be changed later.

### Parent category {#inv.setup.cParent}

Empty for a family; the family for a sub-family. A discount by category in a price list also applies to the sub-categories. A category cannot be its own parent.

### Active {#inv.setup.lActive}

Marks a category no longer used.

### Description (French) {#inv.setup.cDescFR}

Name of the category in French. Required.

### Description (English) {#inv.setup.cDescEN}

Name of the category in English.

## Units of measure {#inv.setup.uom}

Columns: Code, Description, Type and Active. The units the products are counted, bought and sold in (UN, KG, CS, L...). A unit used by a product or a document cannot be deleted.

### Code {#inv.setup.uom.cCode}

Short code of the unit (for example `KG`, `CS`). Required. It cannot be changed later.

### Type {#inv.setup.uom.cType}

*Count*, *Weight*, *Length*, *Area*, *Volume* or *Time*: the kind of quantity.

### Active {#inv.setup.uom.lActive}

Marks a unit no longer used.

### Description (French) {#inv.setup.uom.cDescFR}

Name of the unit in French. Required.

### Description (English) {#inv.setup.uom.cDescEN}

Name of the unit in English.

## Conversions {#inv.setup.uomconv}

The conversions valid for **every product**, for example 1 KG = 1000 G. Type a pair once: the reverse (1 G = 0.001 KG) is deduced. With them, a product counted in KG can be bought in LB or used in G in a recipe.

The packaging of one product (1 BAG = 25 KG) does not go here: it goes in the product, tab **Units and dimensions**, [Other units of this product](#inv.items.conversions).

**Add the standard conversions** adds the usual units (KG, G, MG, LB, L, ML, M, CM...) and their conversions that are missing. It changes nothing that is already there.

### 1 unit of {#inv.setup.uomconv.cFromUOM}

The first unit. Required.

### Equals {#inv.setup.uomconv.dFactor}

How many units of the second unit make one of the first: `1000` for 1 KG = 1000 G. Required, greater than zero.

### Unit {#inv.setup.uomconv.cToUOM}

The second unit. Required. It cannot be the same as the first, and a pair already entered the other way is refused.

### Active {#inv.setup.uomconv.lActive}

Unchecked: the conversion is not used.

### Notes {#inv.setup.uomconv.cNotes}

Free text.
