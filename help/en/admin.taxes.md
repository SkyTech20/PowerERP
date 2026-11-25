# Taxes {#admin.taxes}

The tax codes (TPS, TVQ, HST...) with their rates over time, and the tax groups that say which taxes apply. A product, a customer or a sales invoice only keeps a group code (for example `QC`); the group gives the taxes, in order.

**Where:** **Administration > Taxes**, tabs **Tax codes** and **Tax groups**.

## Tax codes {#admin.taxes.list}

Columns: Code, Description, Kind, Jurisdiction, Current rate, Registration number and Active. **New** creates a tax code. A tax code used by a tax group cannot be deleted.

### Code {#admin.taxes.cCode}

Short code of the tax (for example `TPS`, `TVQ`). Required. It cannot be changed later.

### Kind {#admin.taxes.cKind}

*Federal (GST / TPS)*, *Provincial (QST / PST)*, *Harmonized (HST)* or *Other*.

### Jurisdiction {#admin.taxes.cJurisdiction}

Who levies the tax (for example *Canada*, *Québec*). For information.

### Active {#admin.taxes.lActive}

Marks a tax no longer used.

### Description (French) {#admin.taxes.cDescFR}

Name of the tax in French. Required.

### Description (English) {#admin.taxes.cDescEN}

Name of the tax in English.

### Registration number {#admin.taxes.cRegistrationNo}

The company's own registration number for this tax (for example `123456789 RT0001` for the TPS, `1234567890 TQ0001` for the TVQ). It is printed on the sales invoices and shown in **Administration > System settings**.

## Accounting {#admin.taxes.accounting}

The accounts of the tax, for the accounting to come.

### GL - tax collected (sales) {#admin.taxes.cGLCollected}

Where the tax charged on sales goes.

### GL - tax recoverable (ITC / ITR) {#admin.taxes.cGLRecoverable}

Where the tax paid on purchases and claimed back goes.

### % recoverable {#admin.taxes.dRecoverablePct}

Share of the tax paid that can be claimed back. 100 unless the input tax credits are restricted.

## Rates {#admin.taxes.lines}

The rates of the tax over time. Keep the old rates with their dates: a document uses the rate valid at its date (the line with the latest start date that applies). A line needs a rate.

### From {#admin.taxes.lines.dStartDate}

First day of the rate. Empty = always.

### To {#admin.taxes.lines.dEndDate}

Last day of the rate. Empty = no end. It cannot be before *From*.

### Rate % {#admin.taxes.lines.dRate}

The rate in percent (for example `5` for the TPS, `9.975` for the TVQ). Required.

## Tax groups {#admin.taxes.taxgroups}

Columns: Code, Description, Province / State, Treatment, Taxes and Active. A group says which taxes apply, in which order. A group used by a product, a customer or a document cannot be deleted.

### Code {#admin.taxes.taxgroups.cCode}

Short code of the group (for example `QC`, `ON`, `EXEMPT`). Required. It cannot be changed later.

### Treatment {#admin.taxes.taxgroups.cTreatment}

*Taxable*: the taxes of the group are charged. *Zero-rated* or *Exempt*: no tax is charged.

### Province / State {#admin.taxes.taxgroups.cProvince}

The province of the group. For information.

### Active {#admin.taxes.taxgroups.lActive}

Marks a group no longer used.

### Description (French) {#admin.taxes.taxgroups.cDescFR}

Name of the group in French. Required.

### Description (English) {#admin.taxes.taxgroups.cDescEN}

Name of the group in English.

## Taxes of the group {#admin.taxes.taxgroups.lines}

The tax codes of the group, in order.

### Order {#admin.taxes.taxgroups.lines.iSeq}

Order of calculation. Empty = 1, 2, 3...

### Tax code {#admin.taxes.taxgroups.lines.cTaxCode}

A tax code of the first tab.

### Tax on tax {#admin.taxes.taxgroups.lines.lCompound}

Checked: the tax is calculated on the amount plus the taxes above it. Unchecked: on the amount only (the usual case for the TPS and the TVQ since 2013).

## Try the group {#admin.taxes.taxgroups.sim}

Below a saved group: the taxes of an amount at a date, with each tax, its rate, base and accounts, and the total. It is what the other screens get from the group.

### Amount {#admin.taxes.taxgroups.sim.amount}

The amount before taxes. 100.00 by default.

### Date {#admin.taxes.taxgroups.sim.date}

The date of the rates. Today by default.
