# Audit log {#admin.audit}

Who did what in PowerERP, and when: every sign-in (good or failed), every account locked or unlocked, every password change, every call refused by a role, and every change of data, with the screen, the record and what was sent. This is the audit trail asked by ISO 27001 (8.15 logging), ISO 9001 (records) and Quebec's Law 25. Only the administrator role sees this screen.

**Where:** **Administration > Audit log**.

The log is kept for good: no screen and no call can change or delete an event. Passwords are never written (they show as `***`).

## From {#admin.audit.from}

The first day shown. The screen opens on the last 7 days. Empty: since the first event.

## To {#admin.audit.to}

The last day shown (included). Empty: up to now.

## User {#admin.audit.user}

The events of one user. *api* is a call made with the API key (SkyAI, scripts); *system* is the ERP itself. For a failed sign-in, the user is the name that was typed, even when no such user exists.

## Kind {#admin.audit.kind}

- **Security:** sign-ins, sign-outs, lockouts, unlocks, password changes and refusals.
- **Change:** what was created, changed, deleted, posted, released...

## Event {#admin.audit.event}

What happened. The list shows only the events found in the log.

Security events:

- **Signed in** / **Signed out.**
- **Sign-in failed:** wrong password, unknown user or inactive user (*Details* says which). The details never hold the password typed.
- **Account locked:** too many failed sign-ins in a row (5 by default): the account is refused for 15 minutes, even with the right password.
- **Refused: locked:** a sign-in tried while the account was locked.
- **Unlocked:** the administrator unlocked the account ([Users](#admin.users.unlock)); *Details* says who.
- **Password changed** / **Password change refused** (in *My account*, the current password was wrong).
- **Second signature** / **Second signature refused** (a step of a production order signed by a second user with their password; refused: unknown user or wrong password).
- **Access refused:** the user called something the role does not allow (a screen or a button they do not have).

Change events are the actions of the screens: **Create**, **Edit**, **Delete**, **Post**, **Release**, **Issue**, **Complete**, **Close**... Calculations and checks that change nothing (the preview of an order, the check of a posting) are not kept.

## Search {#admin.audit.search}

Finds the events whose record, address or details hold the text: an invoice number, a product code, a customer, a lot...

## Columns {#admin.audit.columns}

- **When:** date and time, in the time zone of this computer.
- **User**, with the **IP address** of the computer the call came from under it.
- **Event:** violet for a security event, blue for a change, green for a sign-in, red for a refusal (on a pink line). Under a refused sign-in, the reason: wrong password, unknown user or inactive user.
- **Screen:** the screen the change belongs to.
- **Record:** the record changed (order number, product code, user name...).
- **Call:** the method and the address of the call, for the technical support.
- **Details:** what was sent with the change (the values of the form), or the reason of a refused sign-in. Click to see it, again to hide it.

## Export to Excel {#admin.audit.export}

Downloads the events of the filters as a spreadsheet (.xlsx), newest first (50 000 lines at most), in the language of the screen. The dates of the file are in UTC.

## The lockout {#admin.audit.lockout}

After 5 failed sign-ins in a row an account is locked for 15 minutes; a good sign-in starts the count again. The server settings `ERP_LOCKOUT_ATTEMPTS` (0 turns the lockout off) and `ERP_LOCKOUT_MINUTES` change these numbers.
