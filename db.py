"""
PowerERP — SQLite storage.

One file (ERP_DB_PATH, default db/powererp.db next to app.py) holds:
  users     ERP users (login screen, Administration > Users)
  settings  key/value (session secret, dataset the data was seeded from)
  datasets  the ERP data (GL accounts, cost centers, suppliers, POs, receptions,
            invoices), one JSON document per table, rewritten after each change

The ERP keeps working on its in-memory lists; this module only loads them at
startup and saves them after every successful change, so the data survives a
restart. In Docker, mount the folder of ERP_DB_PATH as a volume.
"""
import json
import os
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_PATH = Path(__file__).resolve().parent / "db" / "powererp.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT NOT NULL UNIQUE COLLATE NOCASE,
    name          TEXT NOT NULL DEFAULT '',
    email         TEXT NOT NULL DEFAULT '',
    role          TEXT NOT NULL DEFAULT 'user',
    lang          TEXT NOT NULL DEFAULT 'en',
    active        INTEGER NOT NULL DEFAULT 1,
    password_hash TEXT NOT NULL,
    created_at    TEXT NOT NULL,
    last_login    TEXT
);
CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS datasets (
    name       TEXT PRIMARY KEY,
    data       TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""

_lock = threading.RLock()
_path = None


def now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def init(path=None):
    """Open (and create if needed) the database file. Returns its path."""
    global _path
    _path = Path(path or os.environ.get("ERP_DB_PATH") or DEFAULT_PATH)
    _path.parent.mkdir(parents=True, exist_ok=True)
    with connect() as con:
        con.executescript(_SCHEMA)
    return _path


@contextmanager
def connect():
    """One short-lived connection per operation, serialized by a lock (Flask runs threaded)."""
    with _lock:
        con = sqlite3.connect(_path, timeout=30)
        con.row_factory = sqlite3.Row
        try:
            yield con
            con.commit()
        except Exception:
            con.rollback()
            raise
        finally:
            con.close()


# ---------------------------------------------------------------- settings

def get_setting(key, default=None):
    with connect() as con:
        row = con.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else default


def set_setting(key, value):
    with connect() as con:
        con.execute("INSERT INTO settings (key, value) VALUES (?, ?) "
                    "ON CONFLICT(key) DO UPDATE SET value = excluded.value", (key, value))


# ---------------------------------------------------------------- datasets

def load_datasets():
    """{name: data} of every stored table, or {} when the ERP was never saved."""
    with connect() as con:
        rows = con.execute("SELECT name, data FROM datasets").fetchall()
    return {r["name"]: json.loads(r["data"]) for r in rows}


def save_datasets(datasets):
    stamp = now()
    with connect() as con:
        con.executemany(
            "INSERT INTO datasets (name, data, updated_at) VALUES (?, ?, ?) "
            "ON CONFLICT(name) DO UPDATE SET data = excluded.data, updated_at = excluded.updated_at",
            [(name, json.dumps(data, ensure_ascii=False), stamp) for name, data in datasets.items()])


def clear_datasets():
    with connect() as con:
        con.execute("DELETE FROM datasets")
