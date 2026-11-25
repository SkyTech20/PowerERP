# Production setup {#prod.setup}

The reference lists of the shop floor: the capabilities of the resources, the setup families of the products, and the reasons of the stops and of the scrap.

**Where:** **Production > Production setup**, tabs **Capabilities**, **Setup families**, **Downtime reasons** and **Scrap reasons**.

## Capabilities {#prod.setup.capabilities}

Columns: Code, Description and Active. What a resource knows how to do (for example `BAKE`, `LAMINATE`). A resource lists its capabilities (**Production > Resources (machines)**, tab **Capabilities and attributes**), and a standard operation or a recipe operation can ask for a capability instead of a work center: then any resource having it can run the operation. A capability used elsewhere cannot be deleted.

### Code {#prod.setup.cCode}

Short code of the capability. Required. Saved in capitals. It cannot be changed later.

### Active {#prod.setup.lActive}

Marks a capability no longer used.

### Description (French) {#prod.setup.cDescFR}

Name of the capability in French. Required.

### Description (English) {#prod.setup.cDescEN}

Name of the capability in English.

## Setup families {#prod.setup.setupfamilies}

Columns: Code, Description and Active. Products that need the same setup of the machine (same mould, same colour, same format). A product gets its family in **Production > Manufactured items**; the [Setup matrix](#prod.setupmatrix) gives the changeover time from one family to another.

### Code {#prod.setup.setupfamilies.cCode}

Short code of the family. Required. Saved in capitals. It cannot be changed later.

### Active {#prod.setup.setupfamilies.lActive}

Marks a family no longer used.

### Description (French) {#prod.setup.setupfamilies.cDescFR}

Name of the family in French. Required.

### Description (English) {#prod.setup.setupfamilies.cDescEN}

Name of the family in English.

## Downtime reasons {#prod.setup.downtimereasons}

Columns: Code, Description, Group, Counts in OEE and Active. Filter: Group. Why a machine stopped. Used by the planned downtime of the resources now, and by the stops reported on the shop floor later.

### Code {#prod.setup.downtimereasons.cCode}

Short code of the reason (for example `BREAK`, `PM`). Required. Saved in capitals. It cannot be changed later.

### Group {#prod.setup.downtimereasons.cGroup}

*Breakdown*, *Setup / changeover*, *Minor stop*, *Reduced speed*, *No material*, *No operator*, *Quality*, *Planned stop* or *Other*. Groups the reasons in the reports of lost time.

### Counts in OEE {#prod.setup.downtimereasons.lAffectsOEE}

Checked: the stop is lost time and lowers the OEE (overall equipment effectiveness). Unchecked for the planned stops (breaks, preventive maintenance).

### Active {#prod.setup.downtimereasons.lActive}

Marks a reason no longer used.

### Description (French) {#prod.setup.downtimereasons.cDescFR}

Name of the reason in French. Required.

### Description (English) {#prod.setup.downtimereasons.cDescEN}

Name of the reason in English.

## Scrap reasons {#prod.setup.scrapreasons}

Columns: Code, Description, Group and Active. Filter: Group. Why a part or a quantity was scrapped, for the scrap reported on the shop floor.

### Code {#prod.setup.scrapreasons.cCode}

Short code of the reason. Required. Saved in capitals. It cannot be changed later.

### Group {#prod.setup.scrapreasons.cGroup}

*Material*, *Process*, *Machine*, *Operator*, *Start-up* or *Other*. Groups the reasons in the scrap reports.

### Active {#prod.setup.scrapreasons.lActive}

Marks a reason no longer used.

### Description (French) {#prod.setup.scrapreasons.cDescFR}

Name of the reason in French. Required.

### Description (English) {#prod.setup.scrapreasons.cDescEN}

Name of the reason in English.
