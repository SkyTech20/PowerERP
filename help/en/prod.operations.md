# Standard operations {#prod.operations}

The catalog of operations the recipes reuse: where the operation runs, how long it takes and how many people it needs. An operation of a recipe starts from a standard operation and takes its values for the fields left empty; the recipe can then change them for its product.

**Where:** **Production > Standard operations**.

## List {#prod.operations.list}

Columns: Code, Description, Where it runs, Run time, Setup (min) and Active. Filters: Work center and Capability. **New** creates an operation. An operation used by a recipe cannot be deleted.

## General {#prod.operations.general}

### Code {#prod.operations.cCode}

Short code of the operation (for example `MIX`, `BAKE`). Required. Saved in capitals. It cannot be changed later.

### Active {#prod.operations.lActive}

Marks an operation no longer used.

### Description (French) {#prod.operations.cDescFR}

Name of the operation in French. Required.

### Description (English) {#prod.operations.cDescEN}

Name of the operation in English.

## Where it runs {#prod.operations.where}

Choose one: a work center, or a capability. With a capability, any resource having it can run the operation. Both, or neither, is refused (*Choose a work center or a capability, not both*).

### Subcontracted {#prod.operations.lSubcontract}

Checked: a supplier does the operation. The work center and the capability are hidden, and the subcontractor fields are shown. Choosing a work center of type *Subcontractor* checks it too.

### Work center {#prod.operations.cWorkCenter}

The work center where the operation runs.

### Capability {#prod.operations.cCapability}

The capability the operation needs (**Production > Production setup**). Any resource that has it can run the operation.

### Subcontractor {#prod.operations.cSupplier}

The supplier doing the operation. Required for a subcontracted operation.

### Cost per unit {#prod.operations.dSubcontractCost}

What the subcontractor charges per unit made. Used in the estimated cost of the recipes.

### Lead time (days) {#prod.operations.iSubcontractDays}

The days the subcontractor needs.

## Standard time {#prod.operations.time}

Copied into the recipes, where it can be changed per product.

### Time given in {#prod.operations.cRunFormat}

How the run time is measured: *min / unit* (6.5 minutes per part), *units / hour* (1,200 units per hour on a packing line) or *min / lot* (25 minutes per batch whatever the quantity: an oven, a mixer).

### Run time {#prod.operations.dRunValue}

The time in the format chosen above. In *units / hour*, it cannot be 0.

### Setup (min) {#prod.operations.dSetupMin}

Minutes to prepare the machine, once per order. The [Setup matrix](#prod.setupmatrix) can replace it with a changeover time that depends on the previous job.

### Crew {#prod.operations.iCrew}

Operators needed. 0 = unattended (for example proofing). The labour time is the time × the crew.

### Reporting point {#prod.operations.lReportingPoint}

Checked: the operator reports the quantity done at this operation on the shop floor.

## Instruction {#prod.operations.instruction}

Shown to the operator. The recipe adds its own steps.

### Instruction (French) {#prod.operations.cInstructionFR}

The instruction in French.

### Instruction (English) {#prod.operations.cInstructionEN}

The instruction in English.

## Time of a quantity {#prod.operations.calc}

Below a saved operation: the setup, run and total time of a quantity, at the standard or on a resource (with its speed factor and the efficiency of its work center), and the labour time (× crew).

### Quantity {#prod.operations.calc.qty}

The quantity to make. 100 by default.

### Lot size {#prod.operations.calc.lot}

For a time in *min / lot* only: the size of one lot. The time is counted per lot started. Empty = one lot.

### Resource {#prod.operations.calc.resource}

*Standard*: the time as written. A resource: the time on it. The list shows the resources having the capability, else the resources of the work center.
