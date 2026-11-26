# Stock on hand {#inv.stock}

The stock balances, line by line: one line per product, warehouse, location, lot and serial number. Read-only: the stock changes only through [stock movements](#inv.movements), receptions, posted invoices and counts.

**Where:** **Inventory > Stock on hand**.

## Columns {#inv.stock.columns}

- **Product** and **Description.** Click a line to open its [stock card](#inv.stock.card) (the movements of that line). Click the product code to open the product.
- **Warehouse** and **Location.** The location is empty in a warehouse that does not use locations.
- **Lot**, **Serial number** and **Expiry date**, for the products followed that way.
- **On hand:** the quantity in stock, in the stock unit of the product.
- **Reserved:** the part set aside by reservations (movement type *Reservation*). It is still on hand but cannot go out.
- **Available:** on hand − reserved. This is what an invoice or an issue can take.
- **Unit:** the stock unit of the product.
- **Value:** on hand × the cost of the product (average or standard, as set on the product).

Only the lines with a quantity are listed. The filter **Warehouse** shows one warehouse; the search finds a product, a lot or a serial number.


## Stock card {#inv.stock.card}

Click a line of **Stock on hand** to see where its quantity comes from: every movement of that product in that warehouse, location, lot and serial number, oldest first, with the balance after each one. The last balance is the quantity on hand of the line. The page is read-only.

- At the top: the warehouse and location, the lot, the serial number and the expiry date, then **On hand**, **Reserved** and **Available** today.
- **Open the product** opens the product. **Trace the lot** (a line with a lot) opens **Production > Lots and traceability** on that lot.
- The link **Stock on hand** above the title goes back to the list.

### The columns of the stock card {#inv.stock.card.columns}

- **Date:** the date of the movement (the date of the document, not the time it was typed).
- **What:** what happened, in plain words: *Reception*, *Made by a production order*, *Used by a production order*, *Returned from a production order*, *Invoice*, *Credit note (return)*, *Physical count*, *Transfer from / to* another place, or the type of a manual movement (*Receipt (Manual)*, *Issue (Manual)*, *Adjustment (Manual)*...).
- **Document:** the reception, production order, count, invoice or credit note behind the movement. Click it to open the document (when your role may open that screen). A manual movement has no document.
- **Customer / supplier / note:** the reason of the movement: the customer of an invoice, the supplier of a reception, the product made by an order, the description of a count, or what the user typed.
- **In** and **Out:** the quantity that came in or went out, in the stock unit of the product.
- **Balance:** the quantity in the line after the movement. A reservation does not change it: it shows *reserved* with the quantity set aside. A red line means the balance went below zero (possible only in a warehouse that allows negative stock, or with a back-dated movement).
- **Unit cost** and **Value:** the cost of the movement (in or out) and its value.
- **User:** who posted the movement.
- **Movement #** (under the date): the number of the stock movement; click it to open it in **Inventory > Stock movements**.

### From {#inv.stock.card.from}

Shows only the movements from this date on. The movements before it are added up in the first line, **Opening balance**, so the balance column stays right.

### To {#inv.stock.card.to}

Shows only the movements up to this date. The last line is then the balance at the end of the period. **All dates** clears both dates.

## Where the stock comes from {#inv.stock.sources}

- **Receptions** of purchase orders, and receipts (*Receipt*) typed in **Stock movements**, bring stock in.
- **Posted invoices** take it out, in the stock out order of each product (FEFO, FIFO or LIFO); a **credit note** with *Return* brings it back.
- **Transfers** move it between warehouses or locations.
- **Adjustments** and **physical counts** correct it.

Each of these is a line in **Inventory > Stock movements**, which is the history behind every balance.
