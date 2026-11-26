# PowerERP — Personal data (Quebec Law 25): test script

Test script of the screen **Administration > Personal data** (item 9 of the SCOR / ISO comparison: Law 25 package). The screen finds what the ERP keeps on a person, exports the file to give them, anonymizes the person and keeps the privacy policy (person in charge, hosting, retention). Only the administrator role sees the screen.

**Before you start:** sign in as the administrator, go to **Administration > System settings**, choose the **Pastry shop** scenario and restore the demo data.

---

## 1. Prepare a person

| Step | Expected |
|---|---|
| **Administration > Users**, **New**: *User name* `jtest`, *Name* `Julie Test`, *E-mail* `julie.test@patisserie.example`, *Role* PRODUCTION, a password; **Save** | User created. |
| In another private window, sign in as `jtest`; **Production > Production orders**, **New**: DOUGH, 10 KG, *Start* today, *Due* tomorrow, **Save**, **Release**; sign out | An order created and released by `jtest`. |

## 2. Find the person and open the file

**Administration > Personal data** (new item of the **Administration** menu, between *Audit log* and *Taxes*)

| Step | Expected |
|---|---|
| Open the screen | Three cards: *Find a person*, *Retention*, *Privacy policy*. |
| Type `t` | Nothing: 2 characters are needed. |
| Type `test` | The row *Julie Test*, type *User*, *Where* `jtest`, the e-mail, status *Active*. |
| Type `tremblay` | Julie Tremblay shows as *Customer contact* and as *Ship-to contact* of CAFE-PLATEAU, with e-mail and phone. |
| Back to `test`, **Open the file** of Julie Test | Card *File of Julie Test*: *What the ERP keeps* (name, user name, e-mail, role, language, active, created, last sign-in); *Where the user name is written*: *Production orders: created by* 1 and *released by* 1 with the order number; *Audit log*: the events (creation by admin, sign-in, create, release) with the IP. |
| **Anonymize…** button | Disabled, with "This user is active. Deactivate the user in Administration > Users first." |

## 3. Export (right of access and portability)

| Step | Expected |
|---|---|
| **Export to Excel** | Downloads `personal-data-user-<id>.xlsx` with 3 sheets: *Person*, *Documents*, *Audit log* (every event). In FR the sheets are in French. |
| **Export (JSON)** | Downloads `personal-data-user-<id>.json`: `person`, `documents`, `auditLog`, `policy` (the person in charge and the hosting). |

## 4. Anonymize a user

| Step | Expected |
|---|---|
| **Administration > Users**, open `jtest`, clear *Active*, **Save** | User inactive. |
| Back to **Personal data**, find `test`, **Open the file** | **Anonymize…** enabled. |
| **Anonymize…**, confirm | "Anonymized (N records changed)". Searching `test` finds nobody. |
| **Administration > Users** | The user is now `anon-<id>`, name *Anonymized*, no e-mail, inactive. |
| **Production > Production orders**, the order of step 1 | *Released by* shows `anon-<id>`; the order is unchanged. |
| **Administration > Audit log**, text filter `jtest` | No event. The events of `anon-<id>` have no IP. A new *Anonymize* event by admin, screen *Personal data*, record `user/<id>`. |
| Try to sign in as `jtest` | Refused. |
| Try to anonymize admin itself | Button disabled (active user); through the API the error is `cannot_anonymize_self` or `user_active`. |

## 5. Anonymize a contact

| Step | Expected |
|---|---|
| Search `tremblay`, **Open the file** of the *Customer contact* | *What the ERP keeps*: name, title, phone, e-mail, customer CAFE-PLATEAU. Text "A contact is kept only on the customer…". |
| **Anonymize…**, confirm | The contact is gone from **Sales > Customers > CAFE-PLATEAU**, contacts tab. |
| *Ship-to contact* of Julie Tremblay, **Anonymize…** | On the CAFE ship-to address of the customer, *Contact* and *Phone* are empty; the address stays. |
| **Administration > Audit log**, text `cafeduplateau` | No event with the e-mail of the contact. |

## 6. Former user

| Step | Expected |
|---|---|
| Create the user `jold` and sign in with it once; as admin, **Administration > Users**, delete `jold` | User deleted. |
| **Personal data**, search `jold` | A *Former user* row: the name is still in the audit log. |
| **Open the file**, **Anonymize…** | `jold` is gone from the audit log (even from the anonymization itself). |

## 7. Privacy policy and retention

| Step | Expected |
|---|---|
| *Privacy policy*: *Person in charge* `Mohamed`, *Title* `President`, *E-mail* `privacy@patisserie.example`, *Hosted by* `Amazon Web Services`, *Hosting region* `ca-central-1 (Montreal)`, *Retention (months)* 24; **Save** | "Privacy policy saved." Open the screen again: the values stayed. |
| *E-mail* `nope`, **Save** | Invalid e-mail error; the field gets the focus. |
| *Retention (months)* 0, **Save** | "Value out of range". |
| Card *Retention* | "Kept longer than the retention rule (24 months, before <date>)". With the demo: "Nobody is kept longer than the retention rule." |
| **Sales > Customers**, deactivate UNI-CAFE (no posted invoice) | Back on the screen, the contact of UNI-CAFE shows in *Retention* with "No recent invoice". |
| **Anonymize the 1 persons…**, confirm | "1 persons anonymized."; the list is empty and the contact is gone from the customer. |

## 8. Access

| Step | Expected |
|---|---|
| Sign in with a SALES or PRODUCTION user | No **Personal data** item; `#/admin/privacy` goes back to the dashboard; the API answers 403. |
| **?** on the screen | Opens the *Personal data* help; each field of the policy has its ⓘ. |
