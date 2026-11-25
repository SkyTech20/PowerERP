# Lots and traceability {#prod.traceability}

Where a lot comes from, where it went, and what a recall must reach. Pick a product and one of its lots: the screen follows the lot one step back (the supplier and, for a lot made here, the lots of the materials) and one step forward (the production orders that used it, the lots they made and the customers they were sold to), as the food traceability rules ask (SFCR, ISO 22000). Nothing is changed here: the screen only reads the stock movements, the receptions, the production orders and the sales invoices.

**Where:** **Production > Lots and traceability**.

## Product {#prod.traceability.product}

The products that have at least one lot in the stock movements: raw materials received with a lot, and products made with a lot. A product with a single lot shows its trace at once.

## Lot {#prod.traceability.lot}

The lots of the product, with their expiry date and the quantity still on hand (all warehouses). The trace is shown as soon as a lot is picked. The address of the page keeps the product and the lot: it can be saved as a favourite or sent to a colleague.

## The recall summary {#prod.traceability.recall}

The four figures at the top count what a recall of this lot must reach, for the lot **and every lot made from it** (directly or through several orders):

- **Lots reached:** the lot itself and the lots made from it.
- **Customers:** the customers who still hold some of it (what was invoiced less what came back on a credit note).
- **Stock lines:** the warehouse and location lines where some is still on hand: these are to put on hold.
- **Open orders:** the released, in progress or completed orders that use or make one of these lots.

The yellow box says the same in one sentence. A green box means nothing is left to recall.

## Origin (one step back) {#prod.traceability.origin}

How the lot came in:

- **Received:** the reception that put it in stock, its date, the **supplier**, the **supplier lot** and the purchase order. The link opens the reception.
- **Made:** the production order that reported it, with its status. Under it, each lot of material the order used (quantity used), followed back the same way, down to the suppliers.
- **Entered:** any other entry (manual movement, count adjustment).

Only the materials kept by lot are followed: a material issued without a lot (e.g. flour not tracked by lot) is not shown.

## Uses (one step forward) {#prod.traceability.uses}

The production orders that used the lot (net of what was given back), the quantity used, and the lots they made; each lot made is followed forward the same way. *Nothing reported yet* means the order used the lot but has not reported any production.

## Customers {#prod.traceability.customers}

The sales invoices and credit notes of the lot and of the lots made from it: customer, document, date, product, lot and quantity. A credit note shows the quantity that came back as negative.

## Stock on hand {#prod.traceability.stock}

Where the lot and the lots made from it still are: product, lot, expiry, warehouse, location and quantity.

## Open production orders {#prod.traceability.orders}

Shown only when there are some: the orders not closed nor cancelled that use or make one of the lots reached. Check them before going on with the production.

## Stock movements {#prod.traceability.movements}

Every stock movement of the lot, oldest first: number (the link opens the movement), date, type, document (reception, production order, invoice number…), warehouse, location, quantity, reason and user.

## Export to Excel {#prod.traceability.export}

Downloads the trace as a spreadsheet (.xlsx), in the language of the screen, with one sheet each: *Summary*, *Origin* (one line per entry, with its level), *Uses*, *Customers*, *Stock* and *Movements*. This is the file to send to the CFIA or to a customer during a recall, or to keep for a mock recall exercise.
