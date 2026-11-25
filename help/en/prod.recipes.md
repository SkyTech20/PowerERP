# Recipes {#prod.recipes}

How each product is made, for a base quantity: its materials, its operations (where, how long), the step-by-step the operator follows, and the co-products made with it. A recipe is a version (revision A, B, C...) of a product, approved before it is used.

**Where:** **Production > Recipes**, tabs **General**, **Operations**, **Materials**, **Steps**, **Co-products and by-products**, **Quantity and cost**, **Operator view** and **Versions and history**.

## List {#prod.recipes.list}

Columns: Product, Revision, Description, Process type, Base quantity, Materials, Operations, Steps and Status (★ = the default version of the product). Filters: Status and Process type. **New** creates a recipe.

## Life of a recipe {#prod.recipes.cycle}

1. **Draft:** the recipe is written and can be changed or deleted.
2. **Submit for review:** the version is frozen while it is reviewed.
3. **Approve** or **Send back:** approving makes it the default version of the product, the one new production orders take; sending back returns it to draft with a comment saying what to change.
4. **Make obsolete:** new orders no longer use it.

Only a draft can be changed. To change an approved version, make a **New version from this one**: it starts as a draft with the next revision letter. Approving, sending back, making default and making obsolete need the **Approve** permission of Recipes (**Administration > Roles**), and the recipe must have at least one operation. Every change of status is kept in **Versions and history**.

## General {#prod.recipes.general}

### Product {#prod.recipes.cProduct}

The product made. Required. It must be a made product in **Production > Manufactured items** (*Make*, or *Make or buy*). It cannot be changed later.

### Revision {#prod.recipes.cRevision}

The version: A, B, C... Saved in capitals. Required. It cannot be changed later.

### Process type {#prod.recipes.cProcessType}

*Discrete (parts)*, *Batch* or *Continuous*: how the product is made. For information for now.

### Description (French) {#prod.recipes.cDescFR}

Name of the recipe in French. Empty = the description of the product.

### Description (English) {#prod.recipes.cDescEN}

Name of the recipe in English. Empty = the description of the product.

### Reason for this version {#prod.recipes.cChangeReason}

Why this version exists (for example *less salt*). Filled by **New version from this one**.

### Valid from {#prod.recipes.dEffectiveFrom}

First day the version can be used. Empty = no limit.

### Valid until {#prod.recipes.dEffectiveTo}

Last day the version can be used. It cannot be before *Valid from*. Empty = no limit. On a given day, orders take the default approved version valid that day, else the latest approved one valid that day.

## Quantities {#prod.recipes.quantities}

The materials and the times are written for the base quantity, and scaled to the quantity of each order.

### Base quantity {#prod.recipes.dBaseQty}

The quantity the recipe is written for (for example 60 croissants). Required, greater than zero.

### Unit {#prod.recipes.cUOM}

The unit of the base quantity. Empty = the stock unit of the product. Another unit needs a conversion to the stock unit.

### Minimum batch {#prod.recipes.dMinBatch}

The smallest quantity made at once.

### Maximum batch {#prod.recipes.dMaxBatch}

The largest quantity made at once: a bigger order is split into batches. Also the size of a lot for the times given per lot. It cannot be smaller than the minimum.

### Yield % {#prod.recipes.dYieldPct}

Good output for the input, 1 to 100: 98 = 2 % more materials are used. Empty = 100.

## Notes {#prod.recipes.notes}

### Notes {#prod.recipes.cNotes}

Free text.

## Operations {#prod.recipes.operations}

The operations, in order. A standard operation (**Production > Standard operations**) fills the empty fields when the recipe is saved. Where it runs: a resource, a capability or a work center; a resource also gives its work center. An operation with none of them is refused.

### Op. {#prod.recipes.operations.iOpSeq}

Number of the operation (10, 20, 30...). Unique in the recipe.

### Operation {#prod.recipes.operations.cOperation}

The standard operation it starts from. Its values fill the fields left empty.

### Description (French) {#prod.recipes.operations.cDescFR}

Name of the operation in this recipe.

### Work center {#prod.recipes.operations.cWorkCenter}

Where the operation runs.

### Resource {#prod.recipes.operations.cResource}

The exact machine. It wins over the capability and the work center, and sets the work center.

### Capability {#prod.recipes.operations.cCapability}

What the operation needs: any resource having it can run it.

### Setup (min) {#prod.recipes.operations.dSetupMin}

Minutes to prepare the machine, once per order.

### Time given in {#prod.recipes.operations.cRunFormat}

*min / unit*, *units / hour* or *min / lot*. See [Standard operations](#prod.operations.cRunFormat).

### Run time {#prod.recipes.operations.dRunValue}

The run time in the format chosen.

### Crew {#prod.recipes.operations.iCrew}

Operators needed. 0 = unattended (for example proofing).

### Wait min {#prod.recipes.operations.dMinWaitMin}

Minutes to wait at least after the operation before the next one (for example proofing, curing).

### Wait max {#prod.recipes.operations.dMaxWaitMin}

Minutes the next operation can wait at most. It cannot be smaller than *Wait min*.

### After {#prod.recipes.operations.cPredecessors}

The operations that must end before this one: `10, 20` lets operations run in parallel. Empty = the previous operation. An operation cannot wait for itself, also through others (*The predecessors make a loop*).

## Materials {#prod.recipes.materials}

What is consumed, for the base quantity.

### Seq. {#prod.recipes.materials.iSeq}

Order of the line. Empty = 10, 20, 30...

### Component {#prod.recipes.materials.cComponent}

The product consumed. It cannot be the product of the recipe.

### Quantity {#prod.recipes.materials.dQtyPer}

Quantity for the base quantity of the recipe. Greater than zero.

### Unit {#prod.recipes.materials.cUOM}

Unit of the quantity. Empty = the stock unit of the component. Another unit (500 G of flour stocked in KG) needs a conversion.

### Scrap % {#prod.recipes.materials.dScrapPct}

Extra quantity lost while making, 0 to 99. 5 = 5 % more is used.

### Fixed {#prod.recipes.materials.lFixedQty}

Checked: the quantity is per batch, whatever the quantity made (for example the grease of a mould).

### Op. {#prod.recipes.materials.iOpSeq}

The operation where the material is consumed. It must be an operation of the recipe.

### Issue {#prod.recipes.materials.cIssueMethod}

*Manual* (issued by hand), *Backflush* (taken from stock automatically when the operation is reported) or *Picking list* (prepared in advance).

## Steps {#prod.recipes.steps}

The step-by-step of each operation, in order, as the operator will follow it on the shop floor. On the left, the steps grouped by operation; click one to edit it on the right. **Add step** adds one after the selected step. The fields shown depend on the kind of the step.

### Operation {#prod.recipes.steps.iOpSeq}

The operation of the step.

### Step {#prod.recipes.steps.iStep}

Number of the step in its operation (10, 20...). Unique in the operation.

### Step kind {#prod.recipes.steps.cKind}

*Instruction* (read and confirm), *Add material* (weigh a material of the recipe and scan its lot), *Set a parameter* (oven at 230 degrees), *Measure* (record a value checked against limits), *Check* (yes / no), *Timer* (wait N minutes), *Report production* (lot, serial number, label) or *Second signature* (another person confirms).

### Title (French) {#prod.recipes.steps.cTitleFR}

What the operator sees, in French. Required.

### Title (English) {#prod.recipes.steps.cTitleEN}

What the operator sees, in English.

### Instruction (French) {#prod.recipes.steps.cInstructionFR}

The detail of the step, in French.

### Instruction (English) {#prod.recipes.steps.cInstructionEN}

The detail of the step, in English.

### Attachment {#prod.recipes.steps.cAttachmentUrl}

Link to a photo, drawing, video or safety data sheet.

### Material {#prod.recipes.steps.iMaterialSeq}

*Add material* only: a material of the recipe consumed at this operation (tab **Materials**). Required.

### Value code {#prod.recipes.steps.cParam}

*Set a parameter*, *Measure* and *Check*: the short code of the value (`TEMP_DOUGH`), letters, digits and `_`. Saved in capitals. Unique in the recipe; *Only if* of the next steps uses it. Required except for *Check*.

### Value type {#prod.recipes.steps.cDataType}

*Number*, *Text*, *Yes / no*, *List* or *Photo*. A *Check* is always *Yes / no*.

### Required {#prod.recipes.steps.lRequired}

Checked: the operator must give the value.

### Unit {#prod.recipes.steps.cUOM}

Unit of a number (for example `°C`).

### Min {#prod.recipes.steps.dMin}

Lowest value accepted.

### Target {#prod.recipes.steps.dTarget}

The value aimed at. It must be between the minimum and the maximum.

### Max {#prod.recipes.steps.dMax}

Highest value accepted. It cannot be smaller than the minimum.

### List values {#prod.recipes.steps.cOptions}

*List* only: the choices, separated by commas (`OK, Rework, Scrap`). Required.

### Critical {#prod.recipes.steps.lCritical}

Critical control point: a value out of its limits does what *If out of limits* says. Not critical: only a warning.

### If out of limits {#prod.recipes.steps.cOnFail}

*Block* (the next step waits), *Warn* or *Hold the lot*. Critical steps only.

### Duration (min) {#prod.recipes.steps.dDurationMin}

*Timer* only: the minutes. Required, greater than zero.

### Required role {#prod.recipes.steps.cRequiredRole}

*Second signature* only: who signs (for example supervisor, quality). Empty = any other person.

### Frequency {#prod.recipes.steps.cFrequency}

*Once*, *Every N units*, *Every N minutes* or *Each lot*.

### N {#prod.recipes.steps.dFrequencyValue}

For *Every N units* or *Every N minutes*: the N. Required, greater than zero.

### Only if {#prod.recipes.steps.cCondition}

The step is done only when an earlier value matches, for example `TEMP_DOUGH < 24` (a correction step). Operators: `=`, `!=`, `<`, `<=`, `>`, `>=`. The code must be recorded by an earlier step.

### 2nd signature {#prod.recipes.steps.lSecondSignature}

Checked: a second person confirms the step.

## Co-products and by-products {#prod.recipes.outputs}

Made with the product (for example trimmings), for the base quantity, with their share of the cost.

### Product {#prod.recipes.outputs.cProduct}

The product also made. It cannot be the product of the recipe.

### Kind {#prod.recipes.outputs.cKind}

*Co-product* (a product of value made together) or *By-product* (a leftover).

### Quantity {#prod.recipes.outputs.dQtyPer}

Quantity for the base quantity. Greater than zero.

### Unit {#prod.recipes.outputs.cUOM}

Unit of the quantity. Empty = the stock unit of the product.

### Cost % {#prod.recipes.outputs.dCostPct}

Share of the cost taken by this output. All the lines together must stay under 100 %: the main product keeps a share.

## Quantity and cost {#prod.recipes.explode}

The saved recipe for a quantity: the materials (with scrap and yield, converted to the stock unit), the operations (time on their resource, with its speed and the efficiency of its work center), the number of batches, the total time and the estimated cost (materials, plus machine and labour from the hourly rates of the work centers, plus the subcontracting). A warning is shown when an attribute of the product is outside the limits of a resource.

### Quantity {#prod.recipes.explode.qty}

The quantity to make, in the unit of the recipe. The base quantity by default.

## Operator view {#prod.recipes.preview}

The steps of an operation as the operator will follow them on the shop floor. Type a value in a step to test its limits: the result says what happens (blocks the next step, warning, the lot is held). It uses the saved recipe.

### Operation {#prod.recipes.preview.op}

The operation whose steps are shown.

## Versions and history {#prod.recipes.versions}

The versions of the product (★ = the default one; click a revision to open it), the history of this version (when, who, action, status, comment), and a comparison with another version: what was added, removed or changed in the header, materials, operations, steps and co-products.

### Another version {#prod.recipes.versions.compare}

The version to compare with this one.

## Buttons {#prod.recipes.buttons}

### Submit for review {#prod.recipes.edit}

Drafts only. Saves the recipe and sends it for review, after a confirmation. It can no longer be changed until it is sent back.

### Approve, send back, default, obsolete {#prod.recipes.approve}

Need the **Approve** permission. **Approve** (in review; a comment can be given) makes the version the default of the product. **Send back** (in review) asks *What has to be changed?* and returns it to draft. **Make it the default** (approved) makes it the version new orders take. **Make obsolete** (approved) asks a confirmation; new orders no longer use it.

### New version from this one {#prod.recipes.create}

Any status. Asks why, then copies the recipe into a new draft with the next revision letter (A → B), without the validity dates.

### Delete {#prod.recipes.delete}

Drafts only. An approved or obsolete version is kept: make it obsolete instead.
