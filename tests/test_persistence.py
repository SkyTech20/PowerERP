"""Changes are saved in PostgreSQL after every successful write, and come back after a restart."""
from sqlalchemy import text

import db
from powererp import database


def test_schema_is_migrated(app):
    with database.engine.connect() as con:
        assert con.execute(text("SELECT version_num FROM alembic_version")).scalar() == "0001"
        assert con.execute(text("SELECT code FROM companies")).scalar() == "MAIN"


def test_settings_round_trip(app):
    db.set_setting("test_key", "a")
    db.set_setting("test_key", "b")
    assert db.get_setting("test_key") == "b"
    assert db.get_setting("missing", "dflt") == "dflt"


def test_changes_are_saved_in_the_database(client):
    client.post("/api/gl-accounts", json={"cCode": "8888", "cDesc": "Saved"})
    stored = db.load_datasets()
    assert any(g["cCode"] == "8888" for g in stored["gl"])


def test_failed_change_is_not_saved(client):
    before = db.load_datasets()["suppliers"]
    assert client.post("/api/suppliers", json={"cCode": "LUMPRO", "cName": "dup"}).status_code == 409
    assert db.load_datasets()["suppliers"] == before


def test_reload_from_database_restores_tables(app, client):
    import app as erp_app
    client.post("/api/gl-accounts", json={"cCode": "7777", "cDesc": "Kept"})
    stored = db.load_datasets()
    client.post("/api/clear")
    erp_app.hooks["load"](stored)
    assert client.get("/api/gl-accounts/7777").status_code == 200
