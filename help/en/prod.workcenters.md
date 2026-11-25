# Work centers {#prod.workcenters}

A group of machines, a line, a team or a subcontractor doing the same kind of work. The resources belong to a work center, and the operations of the recipes say on which work center they run. The work center gives them its calendar, its capacity, its hourly rates and where its materials are.

**Where:** **Production > Work centers**.

## List {#prod.workcenters.list}

Columns: Code, Description, Type, Calendar, Finite capacity, Run rate / h and Active. Filters: Type and Calendar. **New** creates a work center. A work center used by a resource or a recipe cannot be deleted.

## General {#prod.workcenters.general}

### Code {#prod.workcenters.cCode}

Short code of the work center (for example `OVEN`, `PACK`). Required. Saved in capitals. It cannot be changed later.

### Type {#prod.workcenters.cType}

*Machines*, *Line*, *Labour* or *Subcontractor*. A *Labour* work center costs per person: its rates are multiplied by the crew of the operation. A *Subcontractor* work center is a supplier doing the work: it needs no calendar, has no resources of its own and its capacity is never finite.

### Active {#prod.workcenters.lActive}

Marks a work center no longer used.

### Description (French) {#prod.workcenters.cDescFR}

Name of the work center in French. Required.

### Description (English) {#prod.workcenters.cDescEN}

Name of the work center in English.

### Subcontractor {#prod.workcenters.cSupplier}

The supplier doing the work (**Accounts Payable > Suppliers**). Shown and required for the type *Subcontractor* only.

## Capacity {#prod.workcenters.capacity}

What the scheduler uses: when the work center works and how much it can take.

### Calendar {#prod.workcenters.cCalendar}

The working time of the work center ([Calendars](#prod.calendars)). Required, except for a subcontractor. Its resources use it unless they have their own.

### Finite capacity {#prod.workcenters.lFinite}

Checked: the scheduler never loads more than the calendar time. Unchecked: no limit (for example a crew that can grow).

### Efficiency % {#prod.workcenters.dEfficiencyPct}

Real output against the standard times, 1 to 500. 90 = the work takes 10 % longer than the standard times. Empty = 100.

### Utilization % {#prod.workcenters.dUtilizationPct}

Share of the calendar time really available (small stops, meetings...), 1 to 100. Capacity = calendar time × utilization. Empty = 100.

### Queue time (min) {#prod.workcenters.iQueueMin}

Usual wait before an operation starts here.

### Move time (min) {#prod.workcenters.iMoveMin}

Time to take the parts to the next operation.

## Hourly rates {#prod.workcenters.costs}

For the estimated cost of the recipes (tab **Quantity and cost**) and, later, the actual cost of the production orders.

### Setup rate / h {#prod.workcenters.dSetupRateHr}

Cost of one hour of setup.

### Run rate / h {#prod.workcenters.dRunRateHr}

Cost of one hour of production.

### Overhead rate / h {#prod.workcenters.dBurdenRateHr}

Overhead added to each hour of production (building, energy...).

### Cost center {#prod.workcenters.cCostCenter}

The cost center of the work center, for the accounting to come.

## Stock {#prod.workcenters.stock}

Where the materials are staged for this work center and where its output is put.

### Warehouse {#prod.workcenters.cWarehouse}

The warehouse of the work center. Required when a location is given.

### Staging location {#prod.workcenters.cInLocation}

Where the materials wait for the work center. It must be a location of the warehouse above.

### Output location {#prod.workcenters.cOutLocation}

Where the work center puts what it makes. It must be a location of the warehouse above.

## Notes {#prod.workcenters.notes}

### Notes {#prod.workcenters.cNotes}

Free text.

## Resources and available time {#prod.workcenters.preview}

Below a saved work center: its resources (**＋ New resource** creates one in this work center), and its available time for a week, with the capacity after the utilization.

### Week of {#prod.workcenters.week}

Any day of the week to show; the week starts on Monday.
