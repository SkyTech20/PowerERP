# Physical count {#inv.count}

Yearly counts and cycle counts: the system prepares a count sheet from the stock, you type what you count, and posting turns the differences into stock adjustments.

**Where:** **Inventory > Physical count**.

## List {#inv.count.list}

Columns: #, Date, Warehouse, Description, Lines, Counted (lines with a quantity typed) and Status (*Draft* or *Posted*).

Filters: Status and Warehouse. **New** creates a count.

## How a count goes {#inv.count.cycle}

1. **New:** choose the warehouse, and if needed the locations or products to count. When saved, the count sheet is filled with the stock of the warehouse (or of the locations / products chosen).
2. **Count:** type the quantity found on each line. A line left empty is not counted and changes nothing. Add a line for a product found where the system has none.
3. **Refresh from stock** if stock moved since the sheet was made: see [Refresh from stock](#inv.count.generate).
4. **Post the count:** see [Post](#inv.count.post).

## General {#inv.count.general}

### Warehouse {#inv.count.cWarehouse}

The warehouse counted. Required. It cannot be changed once the count is created.

### Date {#inv.count.dDate}

Date of the count. Today by default.

### Description {#inv.count.cDescription}

Free text, for example *Yearly count 2026* or *Aisle A-02*.

### Locations starting with {#inv.count.cLocationPrefix}

Counts only the locations whose code starts with this text, for example `A-02` for a cycle count of one aisle. Empty: every location.

### Products starting with {#inv.count.cProductPrefix}

Counts only the products whose code starts with this text. Empty: every product.

### Posted on {#inv.count.dPosted}

Date the count was posted. Posted counts only.

### Value of the differences {#inv.count.dValueDiff}

Total value of the adjustments made by the count (positive: stock found, negative: stock missing). Posted counts only.

## Count sheet {#inv.count.lines}

One line per product, location, lot and serial number in stock. The lines with a difference are highlighted.

### Product {#inv.count.lines.cProduct}

The product counted. A product added by hand must be stocked.

### Description {#inv.count.lines.cDescFR}

Description of the product. Read-only.

### Location {#inv.count.lines.cLocation}

Where the product was counted.

### Lot {#inv.count.lines.cLot}

The lot counted, for products followed by lot.

### Serial number {#inv.count.lines.cSerial}

The serial number counted, for products followed by serial number.

### Expected {#inv.count.lines.dQtyExpected}

The quantity the system has. Read-only. At posting it is taken again from the stock of that moment.

### Counted {#inv.count.lines.dQtyCounted}

The quantity found, in the stock unit. Empty: the line is not counted. 0: nothing was found, and the stock is set to zero.

### Difference {#inv.count.lines.dDiff}

Counted − expected. Read-only, filled in when the count is posted.

## Buttons {#inv.count.buttons}

### Refresh from stock {#inv.count.generate}

Drafts only. Rebuilds the sheet from the current stock, after a confirmation. The quantities already counted are kept.

### Post the count {#inv.count.post}

Asks for confirmation, then makes one *Count* movement for each counted line whose quantity differs from the stock at that moment. All or nothing: every movement is checked before the first is posted. The count is then read-only. At least one line must have a counted quantity.

### Delete {#inv.count.delete}

Drafts only. A posted count cannot be deleted: its movements are in **Stock movements**.
