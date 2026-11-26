# Personal data {#admin.privacy}

What PowerERP keeps on a person, the copy to give them, and how to anonymize it. This screen covers what Quebec's Law 25 (Act respecting the protection of personal information in the private sector) asks of the software. Only the administrator role sees this screen.

**Where:** **Administration > Personal data**.

The ERP keeps personal information on these persons:

- **User:** a user of the ERP (Administration > Users): name, e-mail, user name, language, role, the last sign-in. The user name is also written in the documents the user created, released, posted or signed, and in the audit log with the IP address.
- **Former user:** a user name that is still written in the documents or in the audit log, but whose user was deleted.
- **Customer contact:** a contact of a customer (name, title, phone, e-mail).
- **Ship-to contact:** the contact of a ship-to address of a customer (name, phone).
- **Warehouse manager:** the manager of a warehouse (name, phone, e-mail).

The customers and the suppliers are businesses: they are not listed. The free texts (comments, notes) are not searched: read them if a person asks.

## Find a person {#admin.privacy.search}

Type 2 characters at least of a name, a user name, an e-mail or a phone. The list shows each person found, the type, where the ERP keeps them (the user name, the customer, the warehouse) and the status. Click **Open the file** to see everything about the person.

## File of the person {#admin.privacy.file}

- **What the ERP keeps:** the fields kept on the person.
- **Where the user name is written:** for a user, the documents that name them (production orders released, invoices posted, steps signed...), with the number of records and their numbers.
- **Audit log:** the events of the user, and the events whose details name the person (for example the change that created a contact). The last 20 are shown.

## Export to Excel {#admin.privacy.export}

A spreadsheet with the whole file: a sheet for the person, one for the documents and one with every audit event. This is the copy to give a person who asks for their information (Law 25, section 27). The export is in the language of the screen.

## Export (JSON) {#admin.privacy.exportJson}

The same file in JSON, a structured and commonly used format: give it when the person asks for their information to be sent to another organization (portability, in force since September 2024).

## Anonymize {#admin.privacy.anonymize}

Removes the person from the ERP once their information is no longer needed (Law 25, section 23). **This cannot be undone:** export the file first if the person asked for it.

- **User:** must be deactivated first (Administration > Users), and you cannot anonymize yourself. The user name becomes *anon-* and a number everywhere it is written (documents, history, audit log), the name becomes *Anonymized*, the e-mail is emptied, the IP addresses of the user's events are emptied and the password can no longer be used. The user stays in the list of users, inactive.
- **Former user:** the user name is replaced in the documents and the audit log.
- **Customer contact:** the contact is removed from the customer.
- **Ship-to contact** and **warehouse manager:** the name, phone and e-mail are emptied.

In every case the name, e-mail and phone of the person are also replaced in what the audit log kept of the changes. The documents themselves (invoices, orders, lots, receptions) stay: they are needed by the tax and food safety rules; only who did them is no longer a person. The anonymization itself is kept in the audit log (event *Anonymize*), without the person's name.

The backups made before keep the old data until they are replaced ([Backups](#admin.backups)).

## Retention {#admin.privacy.apply}

The persons kept longer than the retention rule (see **Retention (months)** below):

- the inactive users whose last activity (sign-in or audit event) is older;
- the contacts and ship-to contacts of the inactive customers with no invoice since.

Review the list (deactivate a customer or a user only when you no longer need them), then click **Anonymize the persons** to anonymize all of them at once. The ERP does not do it by itself: come to this screen at least once a year.

## Privacy policy {#admin.privacy.policy}

What Law 25 asks the company to decide and to publish. Save the fields with **Save**.

### Person in charge {#admin.privacy.cOfficerName}

The person in charge of the protection of personal information. By default it is the person with the highest authority in the company (the president); the job can be delegated in writing.

### Title {#admin.privacy.cOfficerTitle}

The title of the person in charge. Law 25 asks the company to publish the title and the contact details on its website.

### E-mail of the person in charge {#admin.privacy.cOfficerEmail}

Where a person writes to ask for their information, to correct it or to complain.

### Hosted by {#admin.privacy.cHosting}

Who hosts the ERP and its database (for example *Amazon Web Services* or *own server*).

### Hosting region {#admin.privacy.cRegion}

Where the data is (for example *ca-central-1, Montreal*). When it is outside Quebec, Law 25 (section 17) asks for a privacy impact assessment before sending the information there.

### Retention (months) {#admin.privacy.iRetentionMonths}

How long a person is kept after their last activity: 24 months by default (from 1 to 600). The **Retention** list uses it. Do not go below what other rules ask: the food traceability records (SFCR) are kept 2 years, and the tax records 6 years (the documents stay, only the persons are anonymized).
