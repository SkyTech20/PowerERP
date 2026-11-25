# Reorder parameters {#inv.params}

The reorder point, minimum and maximum of a product in a warehouse. They decide what [Replenishment](#inv.replenishment) suggests: a product is suggested when available + on order is at or below the reorder point.

**Where:** **Inventory > Reorder parameters**.

## List {#inv.params.list}

Columns: Product, Description, Warehouse, Reorder point, Minimum, Maximum, Order quantity, Available (highlighted when at or below the reorder point) and Default location.

Filter: Warehouse. **New** creates the parameters of a product in a warehouse.

## General {#inv.params.general}

### Product {#inv.params.cProduct}

A stocked product. Required. A product has one line of parameters per warehouse.

### Warehouse {#inv.params.cWarehouse}

The warehouse these parameters are for. Required.

### Default location {#inv.params.cDefaultLocation}

The usual location of the product in this warehouse. It must be a location of that warehouse. A reception put in stock puts the product there when its line has no location.

### Active {#inv.params.lActive}

Unchecked: the product is not suggested in this warehouse.

### Reorder point {#inv.params.dReorderPoint}

When available + on order falls to this quantity or below, the product is suggested. Empty: the minimum is used.

### Minimum {#inv.params.dMinQty}

The lowest stock wanted. Used as the reorder point when there is none.

### Maximum {#inv.params.dMaxQty}

The suggestion fills the stock up to this quantity. It cannot be below the minimum.

### Order quantity {#inv.params.dOrderQty}

An economic quantity to order each time, used when there is no maximum. The suggestion is never smaller.

### Lead time (days) {#inv.params.iLeadTimeDays}

Delivery time in this warehouse, used when the supplier of the product gives none.

All the quantities are in the stock unit of the product.
