# PowerERP — Access control: test script (A1 to A3)

Script to test the roles (*Roles*) in the demo. Screen labels are in English, as the ERP shows them with the **EN** button. The screen manual is in the ERP help (Help > Administration > Roles).

**Before you start:**

1. Log in as the administrator and go to **Administration > System settings**.
2. Restore the demo data. This puts back the sample roles SALES, PRODUCTION and WAREHOUSE.
3. Users and roles you create are not deleted by the demo, so the script can be repeated.

Use two windows: a normal one with the administrator, and a private one (or another browser) to log in as the other users.

---

## 1. Role list

**Administration > Roles**

| Step | Expected |
|---|---|
| Open the screen | ADMIN, PRODUCTION, SALES, USER and WAREHOUSE appear. ADMIN shows *All* under Screens. SALES opens 6 screens, WAREHOUSE 8 and PRODUCTION 11. |
| Open ADMIN | Opens read-only, with the notice *The administrator role has every permission and cannot be changed*. There is no Save or Delete. |

## 2. Levels per screen (Access tab)

Open **SALES**.

| Step | Expected |
|---|---|
| Look at the modules on the left | Sales shows *3 of 3*. Inventory shows *2 of 9* (Products and Stock on hand). Administration shows *View* (Taxes only). The other modules show *No access*. |
| Click **Sales** | Customers = **Edit**, Price lists = **View**, Invoices = **Custom** (everything except Credit note). |
| On Invoices, click **Customize** | The actions View, Create, Edit, Delete, Post, Credit note and Print appear. Only Credit note is unchecked. |
| Check **Credit note** | The Invoices level becomes **Full**. |
| Uncheck **View** | Every Invoices action is unchecked and the level becomes **No access**. |
| Click **Full** again on Invoices, then **Cancel** | Nothing is saved. When SALES is reopened, Invoices is still **Custom**. |
| Open Inventory and click **Set all screens: View** | Every Inventory screen becomes **View**. *Stock on hand* and *Inventory valuation* only offer No access and View. Click **Cancel**. |

## 3. Preview menu

Still on SALES:

| Step | Expected |
|---|---|
| Click **👁 Preview menu** | Shows Sales (Customers, Price lists, Invoices), Inventory (Products, Stock on hand) and Administration (Taxes). |
| Close it, set Production > Recipes to View and open the Preview again | Production > Recipes appears in the menu, even without saving. Click **Cancel**. |

## 4. Create a role by copying another

**Administration > Roles > New**

| Step | Expected |
|---|---|
| Code `buyer`, Description (French) `Acheteur`, Description (English) `Buyer` | The code becomes BUYER (capital letters). |
| Code `with space` and Save | The system refuses: *Use capital letters, digits, - or _*. Set it back to BUYER. |
| *Copy from role* = WAREHOUSE | The WAREHOUSE permissions appear on the Access tab. |
| Purchasing > **Set all screens: Full** and Save | The role is saved and opens. Purchase orders and Receptions are **Full**. |
| Create again with Code BUYER | The system refuses because the code already exists. |
| **History** tab of BUYER | One *Created* line with *Copied from WAREHOUSE*. |

## 5. Change history

Open **SALES**.

| Step | Expected |
|---|---|
| Sales > Invoices: check **Credit note** and Save | Saved. |
| Change Description (English) to `Sales counter` and Save | Saved. |
| **History** tab | At the top, *Description / status* with the old and new value, and *Permissions* with *+ Sales › Invoices: Credit note*. Each line shows the date, the time and the admin user. |
| Uncheck Credit note, set the description back to `Sales desk` and Save | New history lines with the permission removed (−). |

## 6. Users and role

**Administration > Users & security**

| Step | Expected |
|---|---|
| Create `marie` (Name Marie Lefebvre, Role **SALES**, password `secret1`) | Saved. The Role field lists only active roles. |
| Create `paul` (Name Paul Roy, Role **WAREHOUSE**, password `secret1`) | Saved. |
| Create `luc` (Name Luc Gagnon, Role **PRODUCTION**, password `secret1`) | Saved. |
| **Roles > SALES**, **Users** tab | Shows marie. |
| Try to delete SALES | The system refuses because the role has users. |
| Delete BUYER (no users) | Deleted. It no longer appears in the list. |

## 7. Sales user (marie)

Log in as **marie / secret1** in the private window.

| Step | Expected |
|---|---|
| Look at the menu | Only Dashboard, Sales (Customers, Price lists, Invoices), Inventory (Products, Stock on hand) and Administration (Taxes). No General Ledger, Accounts Payable, Purchasing or Production. |
| Look at the Dashboard | Shows no figures (suppliers, purchases and stock value belong to screens outside the role). *Your role shows no figures here: open your screens from the menu* appears. |
| **Sales > Invoices** | The **New** button appears. |
| Open draft #3 | Has **Save**, **Delete**, **Check**, **Post** and **Print**. |
| Click **Post** on draft #3 | The invoice is posted and gets a number. It has **Print**, but no **Credit note**. |
| **Sales > Price lists** and open a list | No **New** on the list. The form opens read-only, with only *Back to list*. |
| **Sales > Customers** and open a customer | Has **Save**, but no **Delete**. |
| In the address bar, change the end to `#/po` | Goes back to the Dashboard (Purchase orders is not in the role). |
| **Inventory > Products** | No **New**. The product opens read-only. |

## 8. Warehouse user (paul)

Log in as **paul / secret1**.

| Step | Expected |
|---|---|
| Look at the menu | Inventory (Products, Stock on hand, Stock movements, Replenishment, Physical count, Warehouses / locations, Reorder parameters) and Purchasing (Receptions). No Sales. |
| **Inventory > Replenishment** | Shows the suggestions, but without the **Create purchase orders** button (the admin sees that button). |
| **Inventory > Physical count > New**, choose ENT-01 and Save | The count is created and has **Refresh from stock**, **Post the count** and **Save**. It has no **Delete** (the admin sees Delete on the same count). |
| **Inventory > Reorder parameters** | Can change and save. No **New**. |

## 9. Production user (luc)

Log in as **luc / secret1**.

| Step | Expected |
|---|---|
| Look at the menu | All of Production, plus Inventory (Products, Stock on hand, Categories / units). |
| **Production > Recipes** | Has **New**. |
| Open PAIN-BL-675 version B (*In review*) | Has only *Back to list* and *New version from this one*. No **Approve** or **Send back**. |
| As admin: **Roles > PRODUCTION**, Production > Recipes to **Full**, Save | Saved. |
| As luc: reload the page and open the same recipe | **Approve** and **Send back** now appear. Do not approve: go back to the admin. |
| As admin: set Recipes back to **Edit** and Save | The history shows both changes. |

## 10. Inactive role

| Step | Expected |
|---|---|
| As admin: **Roles > WAREHOUSE**, uncheck **Active** and Save | The notice *Inactive: its users open no screen* appears. |
| As paul: reload the page | The menu shows only the Dashboard, with *Your role shows no figures here*. |
| As admin: check **Active** again and Save | Paul sees the screens again after reloading. |

## 11. Blocking on the server

This test checks that the blocking does not rely only on hiding the button.

| Step | Expected |
|---|---|
| As marie, open `http://<server>:5051/api/purchase-orders` in the browser | Answer 403 (*forbidden*). |
| As marie, open `.../api/roles` | Answer 403: only the administrator manages roles. |
| As admin, the same addresses | They answer with the data. |

## 12. Demo back

| Step | Expected |
|---|---|
| Before restoring: in **Roles > SALES**, check Credit note on Invoices and save | Saved. |
| As admin: **System settings**, restore the demo | SALES, PRODUCTION and WAREHOUSE go back to the sample permissions. |
| Open **Roles > SALES > History** | One *Demo data restored* line with *− Sales › Invoices: Credit note*. The description also goes back to the sample one. |
