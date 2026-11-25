# Users & security {#admin.users}

The people who can sign in to PowerERP, and the role of each one. The role decides which screens and buttons the user has: see [Roles](#admin.roles). Only the administrator role sees this screen.

**Where:** **Administration > Users & security**.

## List {#admin.users.list}

Columns: Username, Full name, Email, Role, Language, Status, Last sign-in and Locked (a user locked after too many failed sign-ins).

Filters: Role and Status. **New** creates a user.

## General {#admin.users.general}

### Username {#admin.users.username}

The name typed to sign in. Required, and unique (capital letters do not matter: `Marie` and `marie` are the same user). It cannot be changed later.

### Full name {#admin.users.name}

The name of the person. Required.

### Email {#admin.users.email}

E-mail of the person. For information only.

### Role {#admin.users.role}

The role of the user: what the user can open and do. Required. The list shows only the active roles. A user has one role; to give someone different access, create another role for that person in **Administration > Roles**.

There must always be at least one active user with the administrator role: the system refuses to change the role of the last one (*There must be at least one active administrator*).

### Language {#admin.users.lang}

English or Français: the language of the screens when this user signs in. The user can still switch with the **EN** / **FR** button.

### Active {#admin.users.active}

Unchecked: the user can no longer sign in. The last active administrator cannot be made inactive.

## Password {#admin.users.passwordSection}

### New password {#admin.users.password}

At least 6 characters. Required for a new user. When changing a user, leave it empty to keep the current password. Each user can also change their own password in **My account**.

## When a change counts {#admin.users.when}

The server applies the new role at once, on every operation. The menu and the buttons of the user change when the user reloads the page or signs in again.

## Unlock {#admin.users.unlock}

After 5 failed sign-ins in a row, an account is locked for 15 minutes: the user sees *Too many failed sign-ins* and cannot sign in, even with the right password. The list shows *Locked*, and the user's form a yellow notice with the time it ends. **Unlock** lets the user sign in at once (for instance after you gave a new password). Every lockout and unlock is in the [Audit log](#admin.audit).

## Delete {#admin.users.delete}

Deletes the user. You cannot delete your own user, nor the last administrator. For someone who leaves, unchecking *Active* is enough and keeps the user on record.
