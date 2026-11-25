# Stock on hand {#inv.stock}

The stock balances, line by line: one line per product, warehouse, location, lot and serial number. Read-only: the stock changes only through [stock movements](#inv.movements), receptions, posted invoices and counts.

**Where:** **Inventory > Stock on hand**.

## Columns {#inv.stock.columns}

- **Product** and **Description.** Click a line to open the product.
- **Warehouse** and **Location.** The location is empty in a warehouse that does not use locations.
- **Lot**, **Serial number** and **Expiry date**, for the products followed that way.
- **On hand:** the quantity in stock, in the stock unit of the product.
- **Reserved:** the part set aside by reservations (movement type *Reservation*). It is still on hand but cannot go out.
- **Available:** on hand − reserved. This is what an invoice or an issue can take.
- **Unit:** the stock unit of the product.
- **Value:** on hand × the cost of the product (average or standard, as set on the product).

Only the lines with a quantity are listed. The filter **Warehouse** shows one warehouse; the search finds a product, a lot or a serial number.

## Where the stock comes from {#inv.stock.sources}

- **Receptions** of purchase orders, and receipts (*Receipt*) typed in **Stock movements**, bring stock in.
- **Posted invoices** take it out, in the stock out order of each product (FEFO, FIFO or LIFO); a **credit note** with *Return* brings it back.
- **Transfers** move it between warehouses or locations.
- **Adjustments** and **physical counts** correct it.

Each of these is a line in **Inventory > Stock movements**, which is the history behind every balance.
