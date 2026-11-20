"""Database backups: pg_dump on a schedule, kept in a folder, the oldest removed beyond a number of copies.

Settings (Administration > Backups, stored in the settings table as JSON under "backup"):
  enabled        run the scheduled backups
  intervalHours  hours between two backups (1 to 720)
  path           folder of the backup files (created when missing)
  keep           number of backup files kept; older powererp-*.dump files of that folder are deleted

A backup is `pg_dump --format=custom` of the whole database into powererp-YYYYMMDD-HHMMSS.dump (written to a
.part file, then renamed, so a half-written file is never taken for a backup). Restore it with:
  pg_restore --clean --if-exists --no-owner -d <database> powererp-YYYYMMDD-HHMMSS.dump

The scheduler is a thread of the ERP that wakes up every minute. When several ERP processes share the database,
a PostgreSQL advisory lock makes sure only one of them runs a backup at a time.
The pg_dump command is PG_DUMP (default "pg_dump"); the Docker image has pg_dump 16.
"""

import json
import logging
import os
import re
import shlex
import subprocess
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import unquote, urlsplit, urlunsplit

from sqlalchemy import text

import db

from . import database
from .core.errors import AppError

logger = logging.getLogger(__name__)

PREFIX = "powererp-"
FILE_RE = re.compile(r"^powererp-\d{8}-\d{6}\.dump$")
LOCK_KEY = 784211  # advisory lock id of the backup job
DEFAULTS = {"enabled": False, "intervalHours": 24, "path": os.environ.get("BACKUP_DIR", "backups"), "keep": 7}
_run_lock = threading.Lock()


class BackupError(AppError):
    """409 while another backup runs, 500 when pg_dump fails, 400 for the settings."""

    def __init__(self, code, field=None, detail=None):
        status = 409 if code == "backup_running" else 500 if code in ("backup_failed", "pg_dump_missing") else 400
        super().__init__(code, field=field, status=status, detail=detail)


# ------------------------------------------------------------------ settings and status


def get_settings():
    try:
        saved = json.loads(db.get_setting("backup") or "{}")
    except ValueError:
        saved = {}
    return {**DEFAULTS, **{k: v for k, v in saved.items() if k in DEFAULTS}}


def validate(p):
    """Clean settings from a payload; raises BackupError(code, field)."""
    cur = get_settings()
    out = dict(cur)
    if "enabled" in p:
        out["enabled"] = p["enabled"] in (True, 1, "1", "true", "on")
    for field, lo, hi, cast in (("intervalHours", 1, 720, float), ("keep", 1, 365, int)):
        if field in p:
            try:
                v = cast(str(p[field]).replace(",", ".").strip())
            except ValueError:
                raise BackupError("numeric", field) from None
            if not lo <= v <= hi:
                raise BackupError("out_of_range", field, f"{lo}-{hi}")
            out[field] = int(v) if float(v).is_integer() else v
    if "path" in p:
        path = str(p["path"] or "").strip()
        if not path:
            raise BackupError("required", "path")
        out["path"] = path
    _check_folder(out["path"])
    return out


def save_settings(p):
    settings = validate(p)
    db.set_setting("backup", json.dumps(settings))
    return settings


def get_status():
    try:
        return json.loads(db.get_setting("backup_status") or "{}")
    except ValueError:
        return {}


def _set_status(**kw):
    status = {**get_status(), **kw}
    db.set_setting("backup_status", json.dumps(status))
    return status


def next_run(settings=None, status=None):
    """When the next scheduled backup is due (ISO, UTC), or None when the schedule is off."""
    settings = settings or get_settings()
    if not settings["enabled"]:
        return None
    status = get_status() if status is None else status
    last = status.get("lastSuccess")
    if not last:
        return _now().isoformat(timespec="seconds")
    return (datetime.fromisoformat(last) + timedelta(hours=float(settings["intervalHours"]))).isoformat(
        timespec="seconds"
    )


def _now():
    return datetime.now(timezone.utc).replace(microsecond=0)


# ------------------------------------------------------------------ files


def _check_folder(path):
    folder = Path(path)
    try:
        folder.mkdir(parents=True, exist_ok=True)
        probe = folder / ".powererp-write-test"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
    except OSError as e:
        raise BackupError("folder_not_writable", "path", str(e)) from e
    return folder


def list_files(settings=None):
    """The backup files of the folder, newest first."""
    folder = Path((settings or get_settings())["path"])
    if not folder.is_dir():
        return []
    files = [f for f in folder.iterdir() if f.is_file() and FILE_RE.match(f.name)]
    files.sort(key=lambda f: f.name, reverse=True)  # the name holds the date
    return [
        {
            "name": f.name,
            "size": f.stat().st_size,
            "date": datetime.fromtimestamp(f.stat().st_mtime, timezone.utc).isoformat(timespec="seconds"),
        }
        for f in files
    ]


def file_path(name, settings=None):
    if not FILE_RE.match(name or ""):
        return None
    path = Path((settings or get_settings())["path"]) / name
    return path if path.is_file() else None


def rotate(settings):
    """Delete the oldest backup files beyond `keep` (only files named like a backup)."""
    removed = []
    for f in list_files(settings)[int(settings["keep"]) :]:
        try:
            (Path(settings["path"]) / f["name"]).unlink()
            removed.append(f["name"])
        except OSError as e:
            logger.warning("backup: cannot delete %s: %s", f["name"], e)
    return removed


# ------------------------------------------------------------------ running pg_dump


def _pg_dump_command():
    raw = os.environ.get("PG_DUMP", "pg_dump")
    return [p.strip('"') for p in shlex.split(raw, posix=(os.name != "nt"))]


def _libpq_target():
    """(URL without password, password) of the ERP database, for pg_dump."""
    assert database.engine is not None
    url = database.engine.url
    parts = urlsplit(url.render_as_string(hide_password=False).replace("postgresql+psycopg://", "postgresql://"))
    password = unquote(parts.password or "")
    host = parts.hostname or ""
    netloc = (unquote(parts.username) + "@" if parts.username else "") + host + (f":{parts.port}" if parts.port else "")
    return urlunsplit((parts.scheme, netloc, parts.path, parts.query, "")), password


def run_backup(trigger="manual"):
    """Write one backup now and apply the rotation. Returns the status. Raises BackupError on failure."""
    if not _run_lock.acquire(blocking=False):
        raise BackupError("backup_running")
    try:
        assert database.engine is not None
        with database.engine.connect() as con:
            got = con.execute(text("SELECT pg_try_advisory_lock(:k)"), {"k": LOCK_KEY}).scalar()
            if not got:
                raise BackupError("backup_running")
            try:
                return _run(trigger)
            finally:
                con.execute(text("SELECT pg_advisory_unlock(:k)"), {"k": LOCK_KEY})
                con.commit()
    finally:
        _run_lock.release()


def _run(trigger):
    settings = get_settings()
    folder = _check_folder(settings["path"])
    started = _now()
    name = f"{PREFIX}{started.astimezone().strftime('%Y%m%d-%H%M%S')}.dump"
    target, part = folder / name, folder / (name + ".part")
    url, password = _libpq_target()
    cmd = _pg_dump_command() + ["--format=custom", "--no-owner", f"--file={part}", f"--dbname={url}"]
    env = {**os.environ, "PGPASSWORD": password}
    try:
        res = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=3600)
    except FileNotFoundError:
        _fail(trigger, started, "pg_dump not found (PG_DUMP)")
        raise BackupError("pg_dump_missing") from None
    except subprocess.TimeoutExpired:
        part.unlink(missing_ok=True)
        _fail(trigger, started, "timeout")
        raise BackupError("backup_failed", detail="timeout") from None
    if res.returncode != 0 or not part.is_file():
        part.unlink(missing_ok=True)
        msg = (res.stderr or res.stdout or f"exit {res.returncode}").strip()[-500:]
        _fail(trigger, started, msg)
        raise BackupError("backup_failed", detail=msg)
    part.replace(target)
    removed = rotate(settings)
    logger.info("backup: %s written (%s), %d old file(s) removed", name, trigger, len(removed))
    return _set_status(
        lastRun=started.isoformat(timespec="seconds"),
        lastSuccess=started.isoformat(timespec="seconds"),
        lastFile=name,
        lastSize=target.stat().st_size,
        lastError="",
        lastTrigger=trigger,
        removed=removed,
    )


def _fail(trigger, started, msg):
    logger.error("backup failed (%s): %s", trigger, msg)
    _set_status(lastRun=started.isoformat(timespec="seconds"), lastError=msg, lastTrigger=trigger)


# ------------------------------------------------------------------ scheduler


def due(now=None):
    nxt = next_run()
    return nxt is not None and (now or _now()) >= datetime.fromisoformat(nxt)


def _loop(stop, every):
    while not stop.wait(every):
        try:
            if due():
                run_backup("schedule")
        except BackupError as e:
            if e.code != "backup_running":
                logger.warning("scheduled backup: %s %s", e.code, e.detail or "")
        except Exception:  # never let the thread die
            logger.exception("scheduled backup")


def start_scheduler(every=60):
    """Start the scheduler thread (daemon). BACKUP_SCHEDULER=0 turns it off (tests)."""
    if os.environ.get("BACKUP_SCHEDULER", "1") == "0":
        return None
    stop = threading.Event()
    th = threading.Thread(target=_loop, args=(stop, every), name="powererp-backup", daemon=True)
    th.start()
    return stop
