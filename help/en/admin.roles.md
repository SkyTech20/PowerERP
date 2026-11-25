# Roles {#admin.roles}

A role says what its users can open and do in PowerERP, screen by screen. Only the administrator role sees this screen.

- Each user has **one role** (**Administration > Users & security**, field *Role*).
- The role gives, for each screen, the **actions** allowed: view, create, edit, delete, post, and so on.
- There is no exception by user. To give one person different access, create another role for that person.
- A screen with no access **is not in the menu**. A button with no permission **is not on the screen**.
- The server checks the permission on every operation: typing the address of a screen or calling the API directly is refused too.

**Where:** **Administration > Roles**.

## List {#admin.roles.list}

| Column | What it shows |
|---|---|
| Code | Code of the role (for example `SALES`). |
| Description | Description in the language of the screen. |
| Users | How many users have this role. |
| Screens | How many screens the role can open. The administrator shows *All*. |
| Active | An inactive role opens no screen for its users. |

**＋ New** creates a role. Click a line to open the role.

## Roles that come with the system {#admin.roles.builtin}

- **ADMIN** (Administrator): every permission, including Users & security, Roles, Backups and System settings. It cannot be changed or deleted, and opens read-only with the notice *The administrator role has every permission and cannot be changed*.
- **USER** (User): kept the access the ordinary users already had before roles existed: every screen except approving recipes and the administration screens.

**Example roles of the demo:** restoring the demo data (**Administration > System settings**) puts these three roles back as in the example. The roles you created are not touched.

- **SALES** (Sales desk): Customers: view, create and edit. Price lists: view only. Invoices: everything (create, edit, delete a draft, Post, Print) except Credit note. Products, Stock on hand and Taxes: view only.
- **PRODUCTION** (Production planning): every Production screen, except approving and deleting recipes. Products, Stock on hand and Categories / units: view only.
- **WAREHOUSE** (Warehouse and counts): Stock movements: view, create and edit. Physical count: view, create, edit and Post. Reorder parameters: view and edit. Receptions: view, create, edit and Post (put in stock). Products, Stock on hand, Replenishment and Warehouses: view only (no Create PO).

## The role {#admin.roles.general}

At the top: **👁 Preview menu**, **Cancel**, **Delete** and **Save**.

### Code {#admin.roles.cCode}

Short code in capitals, with digits, `-` or `_` (up to 30 characters, for example `BUYER`). Required. It cannot be changed later.

### Copy from role {#admin.roles.cCopyFrom}

New role only. The role starts with the permissions of the role chosen, and you change what differs before saving. *— start empty —* starts with no permission.

### Description (French) {#admin.roles.cDescFR}

Description in French. Required.

### Description (English) {#admin.roles.cDescEN}

Description in English.

### Active {#admin.roles.lActive}

Unchecked: the role stays, but its users see only the Dashboard and their own account. The notice *Inactive: its users open no screen* is shown.

## Access {#admin.roles.access}

On the left, the **modules** (General Ledger, Accounts Payable, Purchasing, Sales, Inventory, Production, Administration), each with a summary: **No access**, **View**, **Edit** or **Full** when every screen of the module is at that level, or **k of n** when the role opens k of the n screens of the module, at different levels.

Click a module to see its screens on the right. Each screen has **one level**:

| Level | What the user can do |
|---|---|
| No access | The screen is not in the menu. |
| View | Open the screen and look. Where the screen prints, print too. |
| Edit | View, plus create and change records. |
| Full | Every action of the screen: also delete and the special actions (Post, Credit note, Approve, Create PO). |
| Custom | A set of actions chosen one by one (see *Customize*). |

A screen that only shows data, such as *Stock on hand* or *Inventory valuation*, offers only **No access** and **View**. *Replenishment* offers **No access**, **View** and **Full**, because its only action besides viewing is *Create PO*.

The screens Users & security, Roles, Backups and System settings are always for the administrator role only, and are not in this tab.

### Set all screens {#admin.roles.setAll}

Puts every screen of the open module at the same level at once. You can then change screen by screen.

### Customize {#admin.roles.customize}

Opens the actions of the screen one by one (*Actions on …*). The level shows **Custom** when the actions checked are not exactly a level.

- Checking any action also checks **View**: without seeing the screen, nothing can be done there.
- Unchecking **View** unchecks every action of the screen.

### The actions of the screens {#admin.roles.actions}

| Action | Where | What it allows |
|---|---|---|
| View | Every screen | See the screen in the menu and open its records. |
| Create | Records and documents | The **New** button and the buttons that create a record (for example *Copy* of a recipe). |
| Edit | Records and documents | Change and save. Without Edit, the form opens read-only, with no **Save**. |
| Delete | Records and documents | The **Delete** button. |
| Post | Sales > Invoices, Inventory > Physical count | Post the invoice (the stock goes out) or the count (the stock is adjusted). |
| Credit note | Sales > Invoices | Make the credit note of a posted invoice. |
| Print | Sales > Invoices | Print the invoice and the credit note. |
| Approve | Production > Recipes | Approve, reject, make default and make obsolete a recipe. |
| Create PO | Inventory > Replenishment | Make purchase orders from the replenishment suggestions. |

## Users {#admin.roles.users}

The users that have the role: Username, Name and Active. To change someone's role, use **Administration > Users & security**.

## History {#admin.roles.history}

Every change of the role, newest first.

| Column | What it shows |
|---|---|
| Date | Date and time of the change. |
| User | Who made the change. |
| Change | *Created*, *Description / status*, *Permissions*, *Demo data restored* or *Deleted*. |
| Details | What changed: the role it was copied from, the old and new description or Active, or the permissions added (+) and removed (−), such as *Sales › Invoices: Credit note*. |

## Preview menu {#admin.roles.preview}

Shows the menu a user of this role will see, with the changes not saved yet. Use it to check before saving. Every user always sees the Dashboard and their own account.

## Delete {#admin.roles.delete}

Deletes the role. The system refuses when the role is ADMIN, or when a user has the role: change the role of those users first, or uncheck *Active*. The deletion stays in the history.

## What the user sees {#admin.roles.effect}

| Where | What changes with the role |
|---|---|
| Menu | Only the screens with View. A group of the menu with no screen disappears. |
| Address of a screen | Opening a screen with no access by its address (or a bookmark) goes back to the Dashboard. Opening *New* without Create goes back to the list. |
| List | **New** only with Create. |
| Form | Without Edit, read-only and no **Save**. **Delete** only with Delete. Post, Credit note, Print, Approve and Create PO only with the action. |
| Links between screens | A link to another screen (for example the product of an invoice line) works only when the role can open that screen. Otherwise it shows as text. |
| Dashboard | Only the figures of the screens the role can open. With none: *Your role shows no figures here: open your screens from the menu*. |
| Help | Only the pages of the screens the role opens, and only the buttons it has. |

**When a change counts:** the server applies the new role at once, on every operation. The menu and the buttons of the user change when the user reloads the page or signs in again.
