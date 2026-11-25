# Replenishment {#inv.replenishment}

The products to reorder: those whose available stock plus what is already on order is at or below their reorder point. The screen proposes a quantity and the preferred supplier, and makes the purchase orders, one per supplier.

**Where:** **Inventory > Replenishment**.

## Which products are listed {#inv.replenishment.rule}

A product is listed for a warehouse when:

- it has [reorder parameters](#inv.params) for that warehouse, active;
- the product is *Active* and has *Can be purchased* checked;
- available (on hand − reserved) + on order (open purchase orders) is at or below the **reorder point**, or the **minimum** when there is no reorder point.

The open purchase orders count for the product's default warehouse (or its only warehouse with parameters).

## The suggested quantity {#inv.replenishment.suggestion}

1. Up to the **maximum** of the parameters, when there is one: maximum − (available + on order).
2. Otherwise the **order quantity** of the parameters.
3. Otherwise enough to get back to the minimum or the reorder point.
4. Never less than the order quantity, nor less than the **Min. qty** of the preferred supplier (product, **Suppliers** tab).
5. Rounded up to whole **purchase units**: with 1 CS = 25 UN and 60 UN needed, the suggestion is 3 CS (75 UN).

## Columns {#inv.replenishment.columns}

- **Order:** checked lines go into the purchase orders. A product with no supplier cannot be picked.
- **Product**, **Description**, **Warehouse.**
- **Available**, **On order**, **Reorder point**, **Maximum:** the figures of the calculation, in stock units.
- **Suggested:** the suggestion, in stock units.
- **To order (purchase unit):** the quantity that goes on the purchase order, in the purchase unit. It can be changed.
- **Supplier name:** the preferred supplier of the product (*Preferred* on the **Suppliers** tab of the product, else the first one). *No supplier* when the product has none.
- **Cost / purchase unit:** the supplier's price, else the last cost (or average cost) of the product × the purchase unit.
- **Amount:** to order × cost. The total at the bottom is for the lines checked, before taxes.

The **Warehouse** list at the top shows the suggestions of one warehouse.

## Create purchase orders {#inv.replenishment.create_po}

Makes the purchase orders for the lines checked, after a confirmation: **one purchase order per supplier**. The quantities and prices are converted to stock units on the purchase order lines, and the taxes come from the product's purchase tax group (else the supplier's GST / QST numbers). Links to the new purchase orders are shown at the top. The suggestions are then calculated again: the new orders now count as *On order*.

Shown only to the roles that have *Create PO* on this screen.
