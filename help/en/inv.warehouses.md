# Warehouses and locations {#inv.warehouses}

The warehouses, and the locations inside them (zone > aisle > rack > level > bin). The stock is kept by warehouse, and by location in the warehouses that use locations.

**Where:** **Inventory > Warehouses / locations**, tabs **Warehouses** and **Locations**.

## Warehouses {#inv.warehouses.list}

Columns: Code, Name, Type, City, Uses locations and Active. **New** creates a warehouse. A warehouse used by the stock cannot be deleted.

### Code {#inv.warehouses.cCode}

Short code of the warehouse (for example `ENT-01`). Required. It cannot be changed later.

### Type {#inv.warehouses.cType}

*Warehouse*, *In transit*, *Consignment*, *Quarantine* or *Virtual*. For information only: it helps to sort the warehouses.

### Manager {#inv.warehouses.cManager}

Who runs the warehouse. For information only.

### Active {#inv.warehouses.lActive}

Marks a warehouse that is no longer used. For information only for now: it is still proposed in the lists.

### Name (French) {#inv.warehouses.cNameFR}

Name of the warehouse in French. Required.

### Name (English) {#inv.warehouses.cNameEN}

Name of the warehouse in English.

### Address line 1 {#inv.warehouses.cAddress1}

Address of the warehouse. For information only, like the other address fields.

### City {#inv.warehouses.cCity}

City of the warehouse.

### Province / State {#inv.warehouses.cProvince}

Province of the warehouse.

### Postal code {#inv.warehouses.cZipCode}

Postal code of the warehouse.

### Country {#inv.warehouses.cCountry}

Country of the warehouse.

### Phone {#inv.warehouses.cPhone}

Phone number of the warehouse.

### Email {#inv.warehouses.cEmail}

E-mail of the warehouse.

### Uses locations {#inv.warehouses.lUseLocations}

Checked: every movement in this warehouse asks for the location (once the warehouse has locations). Unchecked: the stock is kept by warehouse only.

### Allow negative stock {#inv.warehouses.lAllowNegative}

Checked: an issue, a transfer or a negative adjustment can take more than the available stock, and the balance goes below zero. Unchecked (the usual choice): it is refused with *Not enough stock available*.

### Receiving location {#inv.warehouses.cReceivingLoc}

The location where the goods arrive. It must be a location of this warehouse. For information only, ready for the receptions by location.

### Shipping location {#inv.warehouses.cShippingLoc}

The location the goods leave from. It must be a location of this warehouse. For information only, ready for the shipping by location.

## Locations {#inv.warehouses.locations}

Columns: Warehouse, Location, Zone, Aisle, Rack, Level, Bin, Type, Description, Picking order and Blocked. Filters: Warehouse, Type and Blocked. A location that holds or held stock cannot be deleted: uncheck *Active* or check *Blocked* instead.

### Warehouse {#inv.warehouses.locations.cWarehouse}

The warehouse of the location. Required. It cannot be changed later.

### Location {#inv.warehouses.locations.cCode}

Code of the location, in capitals. Left empty, it is built from zone / aisle / rack / level / bin, for example `A-03-02-B`. It cannot be changed later.

### Type {#inv.warehouses.locations.cType}

*Picking*, *Reserve*, *Receiving*, *Shipping*, *Quarantine* or *Staging*. For information only for now.

### On hand {#inv.warehouses.locations.dQtyOnHand}

The quantity in the location, all products together. Read-only.

### Description {#inv.warehouses.locations.cDescription}

Free text (for example *Cold room*).

### Active {#inv.warehouses.locations.lActive}

An inactive location refuses every movement, like a blocked one.

### Blocked {#inv.warehouses.locations.lBlocked}

Nothing goes in or out (for example during a count, or a damaged rack). Movements are refused with *This location is blocked or inactive*.

### Zone {#inv.warehouses.locations.cZone}

Part of the warehouse (for example `A`, `FROID`). Builds the code when it is left empty.

### Aisle {#inv.warehouses.locations.cAisle}

Aisle number. Builds the code.

### Rack {#inv.warehouses.locations.cRack}

Rack number. Builds the code.

### Level {#inv.warehouses.locations.cLevel}

Level (shelf height). Builds the code.

### Bin {#inv.warehouses.locations.cBin}

Bin on the level. Builds the code.

### Picking order {#inv.warehouses.locations.iPickSeq}

The route through the warehouse: the locations are listed in this order. Ready for picking lists.

### Max. weight (kg) {#inv.warehouses.locations.dMaxWeight}

For information only, ready for a WMS (put-away).

### Max. volume (m³) {#inv.warehouses.locations.dMaxVolume}

For information only, ready for a WMS.

### Max. pallets {#inv.warehouses.locations.iMaxPallets}

For information only, ready for a WMS.

### Several products {#inv.warehouses.locations.lMixProducts}

Unchecked: the location holds one product only. A movement bringing in another product is refused (*This location accepts one product only*).

Lots: a location always holds one lot of a product at a time, checked or not. Several products can share a location, each with its own lot, but a second lot of the same product goes to another location until the first one is empty (*This location already holds another lot of this product*).
