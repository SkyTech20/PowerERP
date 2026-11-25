# Suppliers {#ap.suppliers}

The supplier master file: who the company buys from, their address, payment term, tax numbers and buyer. The purchase orders, receptions, supplier invoices and the suppliers of the products use them.

**Where:** **Accounts Payable > Suppliers**.

## List {#ap.suppliers.list}

Columns: Supplier code, Name, City, Province / State, Payment term, Buyer name and Purchasing status. Filter: Purchasing status. **New** creates a supplier.

## General {#ap.suppliers.general}

### Supplier code {#ap.suppliers.cCode}

Short code of the supplier (for example `ISECO`). Required, unique. It cannot be changed later.

### Name {#ap.suppliers.cName}

Name of the supplier. Required. It is copied into the purchase orders, receptions and invoices.

## Address {#ap.suppliers.address}

### Address line 1 {#ap.suppliers.cAddress1}

Street address of the supplier.

### Address line 2 {#ap.suppliers.cAddress2}

Suite, building, second line.

### City {#ap.suppliers.cCity}

City of the supplier.

### Province / State {#ap.suppliers.cProvince}

Province or state. `QC` by default.

### Country {#ap.suppliers.cCountry}

Country. `CA` by default.

### Postal code {#ap.suppliers.cZipCode}

Postal code or ZIP code.

## Terms & taxes {#ap.suppliers.terms}

### Payment term {#ap.suppliers.cTermCode}

When the supplier is paid (for example `n30`). Choose a term already used by another supplier, or type a new code; choosing fills the description. `n30` by default.

### Term description {#ap.suppliers.cTermDesc}

The term in words (for example *net 30 jours*).

### TPS number {#ap.suppliers.cNoTPS}

The supplier's GST registration number. Filled: the purchase orders and receptions of this supplier calculate the TPS (5 %). Empty: no TPS.

### TVQ number {#ap.suppliers.cNoTVQ}

The supplier's QST registration number. Filled: the purchase orders and receptions calculate the TVQ (9.975 %). Empty: no TVQ.

## Purchasing {#ap.suppliers.purchasing}

### Buyer code {#ap.suppliers.cCodeAch}

The usual buyer of this supplier. Choose a buyer already used, or type a new code; choosing fills the name.

### Buyer name {#ap.suppliers.cDescAch}

Name of the buyer.

### Department {#ap.suppliers.cDeptSauv}

Department that deals with the supplier. Free text.

### Purchasing status {#ap.suppliers.iStatutAch}

*Active* or *Inactive*. For information: an inactive supplier is still offered in the lists.

### PO type {#ap.suppliers.iTypePO}

*1 - With PO*, *2 - Without PO* or *3 - Open PO*: how the supplier is usually bought from. For information.
