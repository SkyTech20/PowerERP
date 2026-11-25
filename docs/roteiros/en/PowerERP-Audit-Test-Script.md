# PowerERP — Audit trail and security log: test script

Script to test step 4 of the SCOR / ISO plan: the **lockout** after wrong passwords, the **unlock** by the administrator and the **Administration > Audit log** screen (who did what and when: sign-ins, lockouts, refusals and every change). The screen labels are in English, as the ERP shows them with the **EN** button. Any demo scenario will do.

**Before you start:** log in as the administrator (admin).

---

## 1. Create a test user

| Step | Expected |
|---|---|
| **Administration > Users & security**, **New**: *Username* marie, *Full name* Marie Tremblay, *Role* SALES, *New password* secret1, **Save** | User created. The list has the new *Locked* column (empty). |
| **Production > Production orders**, **New**: DOUGH (or PAIN-BL-675 in the other demo), **Save**, **Release** | Order released. It will show in the log. |
| **Sign out** | Back to the sign-in screen. |

## 2. Lockout after 5 wrong passwords

| Step | Expected |
|---|---|
| Sign in as marie with a wrong password, 4 times | "Wrong username or password, or the user is inactive." each time. |
| 5th wrong password | "Too many failed sign-ins: this account is locked for 15 min. Try again later, or ask the administrator to unlock it." |
| Now the right password (secret1) | The same message: locked, even with the right password. |
| A wrong password for a user that does not exist (e.g. ghost) | "Wrong username or password..." (it does not say whether the user exists). |

## 3. Unlock

| Step | Expected |
|---|---|
| Sign in as admin; **Administration > Users & security** | marie with the red *Locked* badge (hover: until when). |
| Open marie | Yellow notice "Locked after too many failed sign-ins (until ...): Unlock lets the user sign in now." and the **Unlock** button. |
| **Unlock** | Message "The user can sign in again."; the notice and the button are gone; in the list, *Locked* is empty. |
| Sign out and sign in as marie / secret1 | Signs in. |
| The count starts again: as marie, 1 wrong password then the right one; sign out and 1 wrong again | Not locked (the lockout is for 5 wrong **in a row**). |

## 4. Access refused

| Step | Expected |
|---|---|
| As marie (role SALES), type `#/admin/audit` in the address | Back to the dashboard: the screen is not hers. |
| Through the API, as marie: `/api/audit` | 403. It goes into the log as *Access refused*. |

## 5. The Audit log screen

Sign in as admin. **Administration > Audit log**.

| What to look at | Expected |
|---|---|
| Open the screen | *From* = today − 6 days, *To* empty. Newest on top. 50 per page. |
| marie's lines | *Sign-in failed* (red, pink line) with "wrong password" under it, 5 times; *Account locked*; *Refused: locked*; *Unlocked*; *Signed in*; *Access refused*. |
| ghost's *Sign-in failed* line | User ghost, reason "unknown user". |
| **Details** of *Account locked* | `attempts: 5`, `minutes: 15`. **Hide** closes it. |
| **Details** of *Unlocked* | `by: admin`. |
| admin's lines | *Create* in *Users & security* (record marie): **Details** shows what was sent, with `password: "***"`. *Create* and *Release* in *Production orders* (the order number): **Details** of *Create* shows the product and quantity sent. |
| Under each user | The IP address. |
| No password | No line or detail shows secret1 or the wrong passwords typed. |

## 6. Filters

| Step | Expected |
|---|---|
| *User* marie | Only marie's events. |
| *Kind* Security | Only sign-ins, lockouts, unlocks, passwords and refusals. The *Event* list shows only security events. |
| *Kind* Change, *Event* Release | Only the release of the order. |
| Search: the order number | The creation and the release of that order. |
| *From* 2000-01-01, *To* 2000-01-02 | "No event for these filters." |
| Calculations are not kept | Open a draft order and change the quantity (the ERP recalculates): no new line. Only **Save** makes an *Edit*. |

## 7. Export and language

| Step | Expected |
|---|---|
| **Export to Excel** | Downloads `audit-log.xlsx` with the events of the filters, first row bold and frozen, dates in UTC. |
| **FR** button | The screen in French ("Journal d'audit", "Connexion refusée", "mauvais mot de passe"); the Excel file has French headings. |

## 8. Own password

| Step | Expected |
|---|---|
| As marie, **My account**: wrong current password | Error on the screen; in the log, *Password change refused*. |
| Right current password and a new one | In the log, *Password changed*. |

## 9. Help

| Step | Expected |
|---|---|
| **?** on the Audit log screen, and **Help > Administration > Audit log** (EN and FR) | Sections From, To, User, Kind, Event, Search, Columns, Export to Excel, The lockout. |
| **Help > Users & security** | New section *Unlock*. |
