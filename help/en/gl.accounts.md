# GL accounts and cost centers {#gl.accounts}

The chart of accounts and the cost centers. **They are two separate lists: neither is inside the other.**

- A **GL account** says *what* an amount is: bank, stock, supplier, sale, expense (for example `5100` Office supplies).
- A **cost center** says *who* spends it: a department (for example `200` Production) or a sub-department under it (`200-210` Syrup line).
- They meet on each **purchase line** (supplier invoice, reception), which names the account **and**, separately, the cost center: `5100` + `200-210` = office supplies of the syrup line. The same account is used by every department, and a department uses many accounts.

The products (tab **Taxes and accounting**) and the work centers also pick their accounts and cost centers from these lists. There are no journal entries yet: the lists prepare the accounting to come.

**Where:** **General Ledger > GL Accounts / Cost Centers**, tabs **GL accounts** and **Cost centers**.

## GL accounts {#gl.accounts.list}

Columns: Code, Description (in the language of the screen), Type, Requires a cost center and Active. Filters: Type and Active. **New** creates an account.

### Code {#gl.accounts.cCode}

Number of the account (for example `5700`). Required, unique. It cannot be changed later.

### Type {#gl.accounts.cType}

- **Asset**, **Liability**, **Equity**: the balance sheet (bank, stock, supplier accounts, capital).
- **Revenue**, **Expense**: the income statement (sales, purchases, salaries, supplies).

Left on **From the code**, the type is taken from the first digit, as in most Canadian charts of accounts: 1 asset, 2 liability, 3 equity, 4 revenue, 5 to 9 expense.

### Active {#gl.accounts.lActive}

Unchecked: the account is kept (its history stays) but is no longer proposed in the lists, and a new purchase line can no longer use it.

### Description (French) {#gl.accounts.cDesc}

Name of the account in French (for example *Fournitures de bureau*). Required. It is the one shown when the English one is empty.

### Description (English) {#gl.accounts.cDescEN}

Name of the account in English (for example *Office supplies*), shown when the screen is in English.

### Requires a cost center {#gl.accounts.lRequiresCC}

Checked: a supplier invoice or reception line on this account cannot be saved without a cost center (CC1). Usual for the expense accounts, so that each expense is known by department.

## Cost centers {#gl.accounts.cc}

The list shows each **department** in bold, with its **sub-departments** under it (`↳ 200-210`). Columns: Cost center, Description, Level (Department or Sub-department) and Active. On a department, **＋ Sub-department** opens a new sub-department already under it.

Example of a factory: `100` Administration, `200` Production with `200-210` Syrup line and `200-220` Packaging, `300` Warehouse, `400` Sales, `500` Quality.

### Department (CC1) {#gl.accounts.cc.cCC1}

Code of the department. Required. It cannot be changed later.

### Sub-department (CC2) {#gl.accounts.cc.cCC2}

Empty: the department itself. Filled: a sub-department of the CC1 department, which must exist first. The pair CC1 + CC2 is unique and cannot be changed later. A department that still has sub-departments cannot be deleted.

### Active {#gl.accounts.cc.lActive}

Unchecked: kept, but no longer proposed on the purchase lines.

### Description (French) {#gl.accounts.cc.cDesc}

Name in French. Required.

### Description (English) {#gl.accounts.cc.cDescEN}

Name in English, shown when the screen is in English.
