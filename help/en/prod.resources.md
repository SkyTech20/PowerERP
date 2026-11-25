# Resources (machines) {#prod.resources}

The machine, line, station or team that really does the work, inside a work center. A resource gives the scheduler its available time (its calendar minus its planned downtime), its speed and how many orders it runs at once, and says which capabilities it has.

**Where:** **Production > Resources (machines)**, tabs **General**, **Capabilities and attributes**, **Parts**, **Planned downtime** and **Available time**.

## List {#prod.resources.list}

Columns: Code, Description, Work center, Capabilities, Speed factor, Parallel orders and Active. Filter: Work center. **New** creates a resource. A resource used by a recipe cannot be deleted.

## General {#prod.resources.general}

### Code {#prod.resources.cCode}

Short code of the resource (for example `OVEN-1`). Required. Saved in capitals. It cannot be changed later.

### Work center {#prod.resources.cWorkCenter}

The work center the resource belongs to. Required. A subcontractor work center cannot have resources.

### Active {#prod.resources.lActive}

Marks a resource no longer used.

### Description (French) {#prod.resources.cDescFR}

Name of the resource in French. Required.

### Description (English) {#prod.resources.cDescEN}

Name of the resource in English.

## Capacity {#prod.resources.capacity}

The scheduler plans this resource with its calendar, its speed and its parallel orders.

### Calendar {#prod.resources.cCalendar}

The working time of the resource. Empty = the calendar of the work center.

### Speed factor {#prod.resources.dSpeedFactor}

1 = the standard times; 1.2 = 20 % faster; 0.8 = 20 % slower. From 0.1 to 10. Empty = 1.

### Parallel orders {#prod.resources.iParallel}

How many orders it runs at the same time, 1 to 100 (for example the trays of a tunnel oven).

## Machine {#prod.resources.machine}

### Manufacturer {#prod.resources.cManufacturer}

Maker of the machine. For information.

### Model {#prod.resources.cModel}

Model of the machine. For information.

### Serial number {#prod.resources.cSerialNo}

Serial number of the machine. For information.

### Notes {#prod.resources.cNotes}

Free text.

## Capabilities {#prod.resources.capabilities}

What the resource can do. An operation asking for a capability can run on any resource that has it. A capability is listed once.

### Capability {#prod.resources.capabilities.cCapability}

A capability of **Production > Production setup**.

### Preference {#prod.resources.capabilities.iPreference}

Ranks the resources having the same capability: 1 = the preferred one. Empty = 1.

## Attributes {#prod.resources.attributes}

The limits of the machine (width, number of knives, temperature...). The recipes compare them with the attributes of the product (**Production > Manufactured items**) and warn when the product is outside them. An attribute is listed once.

### Attribute {#prod.resources.attributes.cAttribute}

Name of the attribute, for example `Width`. Use the same name as in the products.

### Unit {#prod.resources.attributes.cUOM}

Unit of the value (for example `M`, `°C`).

### Min {#prod.resources.attributes.dMin}

The lowest value the machine takes. Empty = no minimum.

### Max {#prod.resources.attributes.dMax}

The highest value the machine takes. It cannot be smaller than the minimum. Empty = no maximum.

### Value {#prod.resources.attributes.cValue}

A text value when the attribute is not a number (for example a colour).

## Parts of the machine {#prod.resources.subresources}

To say on the shop floor where a stop was (for example the knives of a rewinder).

### Code {#prod.resources.subresources.cCode}

Short code of the part. Saved in capitals. Listed once.

### Description (French) {#prod.resources.subresources.cDescFR}

Name of the part in French. Required.

### Description (English) {#prod.resources.subresources.cDescEN}

Name of the part in English.

## Planned downtime {#prod.resources.downtime}

Preventive maintenance and planned stops. They are taken off the available time of the resource.

### From {#prod.resources.downtime.dStart}

First day of the stop.

### Start {#prod.resources.downtime.cStartTime}

Time the stop starts, `HH:MM`. Empty = the start of the day.

### To {#prod.resources.downtime.dEnd}

Last day of the stop. Empty = the same day. It cannot be before the start.

### End {#prod.resources.downtime.cEndTime}

Time the stop ends, `HH:MM`. Empty = the whole end day.

### Reason {#prod.resources.downtime.cReason}

A downtime reason of **Production > Production setup**.

### Notes {#prod.resources.downtime.cNotes}

Free text.

## Available time {#prod.resources.preview}

The hours of a week, day by day: the calendar with its holidays and exceptions, minus the planned downtime, then the capacity (× utilization of the work center × parallel orders).

### Week of {#prod.resources.week}

Any day of the week to show; the week starts on Monday.
