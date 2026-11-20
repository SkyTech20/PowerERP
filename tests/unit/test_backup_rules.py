"""Unit tests of the backup rules (settings, schedule, file rotation), without the database nor pg_dump."""

from datetime import datetime, timezone

import pytest

from powererp.modules.admin import backup
from powererp.modules.admin.backup import BackupError


@pytest.fixture
def folder(tmp_path, monkeypatch):
    settings = {"enabled": True, "intervalHours": 24, "path": str(tmp_path), "keep": 2}
    monkeypatch.setattr(backup, "get_settings", lambda: dict(settings))
    return tmp_path


def code_of(p):
    with pytest.raises(BackupError) as e:
        backup.validate(p)
    return e.value.code, e.value.field, e.value.status


def test_settings_validation(folder):
    assert backup.validate({"intervalHours": "1,5", "keep": "30", "enabled": "on"})["intervalHours"] == 1.5
    assert backup.validate({"intervalHours": "12"})["intervalHours"] == 12
    assert code_of({"intervalHours": "0"}) == ("out_of_range", "intervalHours", 400)
    assert code_of({"keep": "366"}) == ("out_of_range", "keep", 400)
    assert code_of({"keep": "many"}) == ("numeric", "keep", 400)
    assert code_of({"path": " "}) == ("required", "path", 400)
    new = folder / "sub" / "dir"
    assert backup.validate({"path": str(new)})["path"] == str(new) and new.is_dir()  # created


def test_errors_status():
    assert BackupError("backup_running").status == 409
    assert BackupError("pg_dump_missing").status == 500


def test_next_run():
    on = {"enabled": True, "intervalHours": 6}
    assert backup.next_run({**on, "enabled": False}, {}) is None
    assert backup.next_run(on, {"lastSuccess": "2026-11-20T08:00:00+00:00"}) == "2026-11-20T14:00:00+00:00"
    assert datetime.fromisoformat(backup.next_run(on, {})) <= datetime.now(timezone.utc)  # never ran: due now


def test_rotation_keeps_the_newest_backups_only(folder):
    names = [f"powererp-2026112{d}-030000.dump" for d in range(4)]
    for n in names + ["notes.txt"]:
        (folder / n).write_text("x", encoding="utf-8")
    settings = backup.get_settings()
    assert [f["name"] for f in backup.list_files(settings)] == names[::-1]
    assert backup.rotate(settings) == [names[1], names[0]]
    assert sorted(p.name for p in folder.iterdir()) == sorted([names[2], names[3], "notes.txt"])  # others untouched


def test_only_backup_files_can_be_downloaded(folder):
    (folder / "powererp-20261120-030000.dump").write_text("x", encoding="utf-8")
    settings = backup.get_settings()
    assert backup.file_path("powererp-20261120-030000.dump", settings) is not None
    assert backup.file_path("../secret.dump", settings) is None
    assert backup.file_path("powererp-20261121-030000.dump", settings) is None  # not there
