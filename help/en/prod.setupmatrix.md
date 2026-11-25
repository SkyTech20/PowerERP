# Setup matrix {#prod.setupmatrix}

How long it takes to change over from one setup family to another, on a work center or a resource. It makes the setup time depend on the order of the jobs: going from white to black is faster than from black to white. The families are in **Production > Production setup**, and each product gets its family in **Production > Manufactured items**.

**Where:** **Production > Setup matrix**.

## List {#prod.setupmatrix.list}

Columns: For, Code, Notes, Changeovers and Active. Filter: For. **New** creates a matrix. A work center or a resource has one matrix at most.

## General {#prod.setupmatrix.general}

A matrix of a work center applies to all its resources; the matrix of a resource replaces the one of its work center.

### For {#prod.setupmatrix.cScope}

*Work center* or *Resource*: what the matrix belongs to. It cannot be changed later.

### Work center / Resource {#prod.setupmatrix.cScopeCode}

The work center or the resource of the matrix. Required. It cannot be changed later.

### Active {#prod.setupmatrix.lActive}

Unchecked: the matrix is not used.

### Notes {#prod.setupmatrix.cNotes}

Free text.

## Changeovers {#prod.setupmatrix.lines}

One line per pair of families. Empty or `*` = any family. To find the changeover, the exact pair wins, then *from family → any*, then *any → to family*, then *any → any*. With no line for the pair: the same family = no changeover (0), else the setup of the operation.

### From family {#prod.setupmatrix.lines.cFromFamily}

The family of the previous job. Empty or `*` = any family.

### To family {#prod.setupmatrix.lines.cToFamily}

The family of the next job. Empty or `*` = any family.

### Setup (min) {#prod.setupmatrix.lines.dSetupMin}

Minutes of the changeover. They replace the setup of the operation.

### Cost {#prod.setupmatrix.lines.dSetupCost}

Cost of the changeover (cleaning product, material lost...).

### Scrap (qty) {#prod.setupmatrix.lines.dScrapQty}

Quantity lost during the changeover.

## Grid of the changeovers {#prod.setupmatrix.grid}

Below a saved matrix: every family to every family, as the scheduler will read it. Rows: from; columns: to. A value marked `*` comes from a line with *any family*. In grey: not in the matrix (same family = 0, else the setup of the operation). Hover a cell to see which rule gave it.

### Setup of the operation (min) {#prod.setupmatrix.grid.default}

The setup to show when the matrix has no line for the pair. Only for this grid: the real value comes from each operation. 30 by default.
