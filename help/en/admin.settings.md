# System settings {#admin.settings}

The company profile printed on the invoices, the demo data and the maintenance of the data. Only the administrator role sees this screen.

**Where:** **Administration > System settings**.

## Company profile {#admin.settings.company}

Everything here is printed at the top of the invoices and credit notes. **Save** keeps the changes; they count for the next printouts, including those of invoices already posted.

### Logo {#admin.settings.cLogo}

The company logo, printed at the top left of the invoices and credit notes and at the top of the *Summary* sheet of the traceability spreadsheet (**Production > Traceability > Export to Excel**).

- **Choose an image…** picks a PNG, JPEG, GIF or WebP file of 5 MB at most. It is saved at once (no need to press **Save**) and shown in the box.
- A big image or a phone photo is made smaller automatically (600 × 240 pixels at most, the proportions are kept), so the invoices stay light.
- A wide logo on a white or transparent background prints best.
- **Change the logo…** replaces it; **Remove the logo** prints the documents without one again.

### Name {#admin.settings.cName}

The usual name of the company. Required.

### Legal name {#admin.settings.cLegalName}

The registered name. When filled in, it is the one printed on the invoice.

### Address line 1 {#admin.settings.cAddress1}

Address of the company on the invoice. The same goes for the fields below.

### Address line 2 {#admin.settings.cAddress2}

Second line of the address.

### City {#admin.settings.cCity}

City of the company.

### Province / State {#admin.settings.cProvince}

Province of the company (for example QC).

### Postal code {#admin.settings.cZipCode}

Postal code of the company.

### Country {#admin.settings.cCountry}

Country of the company.

### Phone {#admin.settings.cPhone}

Printed under the address.

### E-mail {#admin.settings.cEmail}

Printed under the address.

### Website {#admin.settings.cWebsite}

Printed under the address.

### Quebec enterprise number (NEQ) {#admin.settings.cNEQ}

The Quebec enterprise number, printed next to the tax numbers.

### Invoice numbers start at {#admin.settings.iInvoiceStart}

The first invoice number. Empty or 0 starts at 1. With 1001, the next invoice posted gets 1001. It only counts from now on: invoices already posted are not renumbered.

### Invoice note (French) {#admin.settings.cInvoiceNoteFR}

Text at the bottom of the invoice for French-speaking customers (for example payment conditions, bank details, thanks).

### Invoice note (English) {#admin.settings.cInvoiceNoteEN}

The same for English-speaking customers.

### Tax registration numbers {#admin.settings.taxNumbers}

The GST / HST and QST numbers are not typed here. They come from the tax codes in **Administration > Taxes** (the registration number of each tax) and are shown here only to check them.

## Demo data {#admin.settings.demo}

### Data set {#admin.settings.scenario}

The demo data to load:

- *Maple products* (the default): Érablière Démo inc., a plant in Saint-Georges (Beauce) that buys maple syrup in barrels from three sugar bushes and makes syrup in cans and bottles, maple butter, maple candy and maple fudge. It opens with two months of history (October and November 2026): production orders made and closed, the recipe steps recorded (Brix, cooking and filling temperatures), posted invoices and a credit note, lots on hold and nonconformances. Each barrel is a lot whose supplier lot is the producer's barrel number and harvest date, so **Production > Lots and traceability** follows a can sold back to its sugar bush, and **Reports > Supply chain indicators** has a value for every indicator.
- *SkyAI* (purchasing, no production).
- *Manufacturing* (paper, bakery, metal).

**↺ Reset demo data** loads the data set chosen, after a confirmation. Every change made since is lost. The data set chosen is kept when the ERP restarts. The example roles SALES, PRODUCTION and WAREHOUSE are put back as in the demo; the roles you created are not touched.

## Clear all data {#admin.settings.clear}

**🗑 Clear all data** deletes all the data, after a confirmation: GL accounts, cost centers, suppliers, products, stock, purchase orders, receptions, invoices, production, customers and the company profile. The users and the settings are kept. **Reset demo data** brings the demo back.
