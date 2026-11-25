# GL accounts and cost centers {#gl.accounts}

The chart of accounts and the cost centers. The products (tab **Taxes and accounting**), the lines of the receptions and of the supplier invoices, and the work centers pick their accounts and cost centers from these lists. There are no journal entries yet: the lists prepare the accounting to come.

**Where:** **General Ledger > GL Accounts / Cost Centers**, tabs **GL accounts** and **Cost centers**.

## GL accounts {#gl.accounts.list}

Columns: Code and Description. **New** creates an account.

### Code {#gl.accounts.cCode}

Number of the account (for example `5700`). Required, unique. It cannot be changed later.

### Description {#gl.accounts.cDesc}

Name of the account (for example *Office supplies*). Required.

## Cost centers {#gl.accounts.cc}

Columns: Cost center (CC1), Sub cost center (CC2) and Description. A cost center can be split into sub cost centers: `170` alone, or `170` with `751`. The lists show them as `170-751`.

### Cost center (CC1) {#gl.accounts.cc.cCC1}

Code of the cost center (for example a department). Required. It cannot be changed later.

### Sub cost center (CC2) {#gl.accounts.cc.cCC2}

Code of the sub cost center inside CC1. Empty = the cost center itself. The pair CC1 + CC2 is unique, and it cannot be changed later.

### Description {#gl.accounts.cc.cDesc}

Name of the cost center. Required.
