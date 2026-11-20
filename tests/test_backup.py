"""Administration > Backups: settings, manual and scheduled backups, rotation, access."""
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from powererp import backup

FAKE = Path(__file__).resolve().parent / "tools" / "fake_pg_dump.py"


@pytest.fixture
def folder(tmp_path, monkeypatch, admin):
    monkeypatch.setenv("PG_DUMP", f"{sys.executable} {FAKE}")
    r = admin.put("/api/admin/backup", json={"enabled": False, "intervalHours": 24, "path": str(tmp_path), "keep": 3})
    assert r.status_code == 200, r.get_json()
    import db
    db.set_setting("backup_status", "{}")
    return tmp_path


def test_settings_are_validated_and_saved(admin, folder):
    assert admin.put("/api/admin/backup", json={"intervalHours": 0}).get_json()["field"] == "intervalHours"
    assert admin.put("/api/admin/backup", json={"keep": "x"}).get_json() == {"error": "numeric", "field": "keep"}
    assert admin.put("/api/admin/backup", json={"path": ""}).get_json()["field"] == "path"
    r = admin.put("/api/admin/backup", json={"enabled": True, "intervalHours": "6", "keep": 10}).get_json()
    assert r["settings"] == {"enabled": True, "intervalHours": 6, "path": str(folder), "keep": 10}
    assert r["nextRun"]  # never backed up: due now


def test_manual_backup_writes_a_file_without_the_password_on_the_command_line(admin, folder):
    r = admin.post("/api/admin/backup/run")
    assert r.status_code == 200, r.get_json()
    st = r.get_json()
    name = st["status"]["lastFile"]
    assert st["files"][0]["name"] == name and not st["status"]["lastError"]
    content = (folder / name).read_text(encoding="utf-8")
    assert "--format=custom" in content and "powererp_test" in content
    args, pw = content.split("\nPGPASSWORD=")
    assert pw == "powererp" and "powererp:powererp@" not in args
    assert admin.get(f"/api/admin/backup/files/{name}").status_code == 200
    assert admin.get("/api/admin/backup/files/..%2Fsecrets.txt").status_code == 404


def test_only_the_last_backups_are_kept(admin, folder):
    for i in range(5):
        (folder / f"powererp-2026010{i + 1}-120000.dump").write_text("old")
    (folder / "notes.txt").write_text("not a backup")
    admin.post("/api/admin/backup/run")
    names = sorted(f.name for f in folder.iterdir())
    assert "notes.txt" in names
    dumps = [n for n in names if n.endswith(".dump")]
    assert len(dumps) == 3 and "powererp-20260105-120000.dump" in dumps and "powererp-20260101-120000.dump" not in dumps


def test_failed_backup_is_reported_and_leaves_no_file(admin, folder, monkeypatch):
    monkeypatch.setenv("FAKE_PG_DUMP_FAIL", "1")
    r = admin.post("/api/admin/backup/run")
    assert r.status_code == 500 and r.get_json()["error"] == "backup_failed"
    assert "connection refused" in admin.get("/api/admin/backup").get_json()["status"]["lastError"]
    assert not list(folder.iterdir())


def test_schedule_runs_when_due(admin, folder):
    admin.put("/api/admin/backup", json={"enabled": True, "intervalHours": 2})
    assert backup.due()
    backup.run_backup("schedule")
    assert not backup.due()  # next one in 2 hours
    later = datetime.now(timezone.utc) + timedelta(hours=2, minutes=1)
    assert backup.due(later)
    admin.put("/api/admin/backup", json={"enabled": False})
    assert not backup.due(later)


def test_scheduler_thread_makes_the_backup(admin, folder, monkeypatch):
    admin.put("/api/admin/backup", json={"enabled": True, "intervalHours": 1})
    monkeypatch.setenv("BACKUP_SCHEDULER", "1")
    stop = backup.start_scheduler(every=0.2)
    try:
        for _ in range(50):
            if any(f.suffix == ".dump" for f in folder.iterdir()):
                break
            time.sleep(0.1)
    finally:
        stop.set()
    assert any(f.suffix == ".dump" for f in folder.iterdir())
    assert backup.get_status()["lastTrigger"] == "schedule"


def test_only_administrators(app, admin):
    c = app.test_client()
    admin.post("/api/users", json={"username": "bob", "name": "Bob", "password": "secret1", "role": "user"})
    assert c.post("/api/auth/login", json={"username": "bob", "password": "secret1"}).status_code == 200
    assert c.get("/api/admin/backup").status_code == 403
    assert app.test_client().get("/api/admin/backup").status_code == 401
