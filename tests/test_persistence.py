"""Changes are saved in PostgreSQL: relational tables for the master files, JSON (legacy_datasets) for the rest."""

from sqlalchemy import text

import db
from powererp import database


def _sql(query, **params):
    with database.engine.connect() as con:
        return con.execute(text(query), params).all()


def test_schema_is_migrated(app):
    assert _sql("SELECT version_num FROM alembic_version")[0][0] == "0004"
    assert _sql("SELECT code FROM companies")[0][0] == "MAIN"


def test_settings_round_trip(app):
    db.set_setting("test_key", "a")
    db.set_setting("test_key", "b")
    assert db.get_setting("test_key") == "b"
    assert db.get_setting("missing", "dflt") == "dflt"


def test_master_data_is_in_tables(client):
    client.post("/api/gl-accounts", json={"cCode": "8888", "cDesc": "Saved"})
    assert _sql("SELECT description FROM gl_accounts WHERE code = '8888'") == [("Saved",)]
    stored = db.load_datasets()
    assert "gl" not in stored and "suppliers" not in stored and "inv_products" not in stored
    assert "po_details" not in stored and "invoices" not in stored
    assert stored == {}  # every table is relational since R3


def test_purchasing_is_in_tables(client):
    assert _sql("SELECT count(*) FROM purchase_orders")[0][0] > 0
    po = client.get("/api/purchase-orders").get_json()["items"][0]["cPO"]
    detail = _sql("SELECT has_detail, unbilled FROM purchase_orders WHERE po_no = :no", no=po)
    assert detail and detail[0][0] is True
    assert _sql("SELECT count(*) FROM receptions")[0][0] > 0


def test_invoice_numbers_come_from_the_sequence(client):
    body = {
        "cNoFourn": "LUMPRO",
        "cNoFacture": "SEQ-1",
        "dDateFacture": "2026-11-01",
        "lines": [{"cCodeProduit": "X", "dQuantite": "1", "dCoutUnitaire": "10"}],
    }
    first = client.post("/api/invoices", json=body).get_json()["id"]
    second = client.post("/api/invoices", json={**body, "cNoFacture": "SEQ-2"}).get_json()["id"]
    assert second == first + 1
    assert client.get(f"/api/invoices/{second}").get_json()["dTotalFacture"] == "10.00"


def test_unparseable_date_is_kept_as_sent(client):
    """A date in another format (sent by an external system) is not refused nor lost."""
    from powererp import purchasing as purch

    with database.unit_of_work():
        purch.inv_put({"id": 999, "cNoFourn": "LUMPRO", "cNoFacture": "OLD", "dDateFacture": "10/01/2026", "lines": []})
    assert client.get("/api/invoices/999").get_json()["dDateFacture"] == "10/01/2026"


def test_failed_change_is_not_saved(client):
    before = _sql("SELECT count(*) FROM suppliers")[0][0]
    assert client.post("/api/suppliers", json={"cCode": "LUMPRO", "cName": "dup"}).status_code == 409
    assert _sql("SELECT count(*) FROM suppliers")[0][0] == before


def test_failed_request_rolls_back_everything(client):
    """A product saved with a bad supplier line is refused: nothing of it is written."""
    r = client.post("/api/products", json={"cCode": "ROLLBK", "cDescFR": "x", "lines": [{"cSupplierCode": "NOPE"}]})
    assert r.status_code == 400
    assert _sql("SELECT count(*) FROM products WHERE code = 'ROLLBK'")[0][0] == 0


def test_numbers_keep_their_scale(client):
    r = client.post("/api/products", json={"cCode": "SCALE", "cDescFR": "x", "dPrice1": "12.50", "dWeight": "1"})
    assert r.status_code == 201
    p = client.get("/api/products/SCALE").get_json()
    assert p["dPrice1"] == "12.50" and p["dWeight"] == "1" and p["dPrice2"] == ""


def test_case_insensitive_codes_are_unique(client):
    assert client.post("/api/uom", json={"cCode": "BX", "cDescFR": "Boîte"}).status_code == 201
    assert client.post("/api/uom", json={"cCode": "bx", "cDescFR": "Boîte"}).status_code == 409


def test_reload_from_old_json_dataset(app, client):
    """An older database kept the master files as JSON: loading it fills the tables."""
    import app as erp_app

    with database.unit_of_work():
        erp_app.hooks["load"]({"gl": [{"cCode": "7777", "cDesc": "Kept"}]})
    assert client.get("/api/gl-accounts/7777").get_json()["cDesc"] == "Kept"
    assert client.get("/api/summary").get_json()["glAccounts"] == 1
