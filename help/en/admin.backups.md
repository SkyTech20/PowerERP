# Backups {#admin.backups}

Automatic copies of the whole database, made on the ERP server with PostgreSQL's `pg_dump`. For the administrator only.

**Where:** **Administration > Backups**.

## Status {#admin.backups.status}

The last backup (date and file), the next one, and the error of the last attempt when it failed. **Back up now** makes a backup at once, whatever the schedule. Only one backup runs at a time, even with several ERP servers on the same database.

## Schedule {#admin.backups.settings}

**Save** checks and saves the four settings.

### Automatic backups {#admin.backups.enabled}

Checked: a backup is made every *Every (hours)*. The first one is made right away when no backup was made yet. Unchecked: only **Back up now** makes backups.

### Every (hours) {#admin.backups.intervalHours}

Hours between two backups, from 1 to 720 (24 = once a day). The next backup is counted from the last successful one.

### Backups kept {#admin.backups.keep}

How many backup files are kept, from 1 to 365. Beyond that, the oldest backup files of the folder are deleted.

### Backup folder {#admin.backups.path}

The folder of the backup files, on the ERP server (with Docker: a mounted folder, for example `/app/backups`). Created when missing. Required.

## Backup files {#admin.backups.files}

The backups of the folder, newest first, with their date and size. **Download** saves a copy on your computer. Each file is named `powererp-YYYYMMDD-HHMMSS.dump`.

To restore a backup, on the server: `pg_restore --clean --if-exists --no-owner -d <database> <file>`. This replaces everything in that database: stop the ERP first, and ask for help if in doubt.
