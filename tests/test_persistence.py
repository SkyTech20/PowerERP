"""Changes are saved in SQLite after every successful write, and come back after a restart."""
import db


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
