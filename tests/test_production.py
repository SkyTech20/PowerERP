"""Production API (M0): the reference lists of the shop floor, their lookups and the demo data life cycle."""

import pytest

LISTS = [
    ("capabilities", "CNC", 10),
    ("setup-families", "FOOD-ALLERG", 6),
    ("downtime-reasons", "BRK-MECH", 11),
    ("scrap-reasons", "WEB-BREAK", 7),
]


@pytest.mark.parametrize("url, code, count", LISTS)
def test_demo_lists(client, url, code, count):
    page = client.get(f"/api/{url}?sort=cCode").get_json()
    assert page["total"] == count
    assert client.get(f"/api/{url}/{code}").get_json()["cCode"] == code


@pytest.mark.parametrize("url, code, count", LISTS)
def test_crud(client, url, code, count):
    r = client.post(f"/api/{url}", json={"cCode": "new-1", "cDescFR": "Nouveau", "cDescEN": "New"})
    assert r.status_code == 201 and r.get_json()["cCode"] == "NEW-1"  # codes in capitals
    assert client.post(f"/api/{url}", json={"cCode": "new-1", "cDescFR": "x"}).status_code == 409
    r = client.post(f"/api/{url}", json={"cCode": "X"})
    assert r.status_code == 400 and r.get_json()["field"] == "cDescFR"
    r = client.put(f"/api/{url}/NEW-1", json={"cDescFR": "Renommé", "lActive": False})
    assert r.get_json()["cDescFR"] == "Renommé" and r.get_json()["lActive"] is False
    assert client.delete(f"/api/{url}/NEW-1").status_code == 200
    assert client.get(f"/api/{url}/NEW-1").status_code == 404


def test_downtime_reason_groups(client):
    r = client.post("/api/downtime-reasons", json={"cCode": "LUNCH", "cDescFR": "Dîner", "cGroup": "planned"})
    assert r.get_json()["lAffectsOEE"] is False  # a planned stop is not lost time
    r = client.post("/api/downtime-reasons", json={"cCode": "Z", "cDescFR": "z", "cGroup": "coffee"})
    assert r.status_code == 400 and r.get_json() == {"error": "invalid_choice", "field": "cGroup"}
    planned = client.get("/api/downtime-reasons?f_cGroup=planned").get_json()["items"]
    assert {r["cCode"] for r in planned} == {"BREAK", "LUNCH", "PM"}


def test_lookups_follow_the_language_and_skip_inactive(client):
    client.put("/api/capabilities/PAINT", json={"lActive": False})
    fr = {r["code"]: r["label"] for r in client.get("/api/lookups/capabilities").get_json()}
    en = {r["code"]: r["label"] for r in client.get("/api/lookups/capabilities?lang=en").get_json()}
    assert fr["BAKE"] == "Cuisson" and en["BAKE"].startswith("Baking") and "PAINT" not in fr


def test_reset_and_clear(client):
    client.delete("/api/scrap-reasons/DIM")
    client.post("/api/clear")
    assert client.get("/api/capabilities").get_json()["total"] == 0
    client.post("/api/reset")
    assert client.get("/api/scrap-reasons/DIM").status_code == 200


def test_production_uses_the_stock_service(app):
    """The plan's rule: production posts stock movements (cDocType PROD) through the stock service."""
    from powererp import database

    stock = app.extensions["powererp"].get("stock")
    with app.test_request_context(), database.unit_of_work():
        m = stock.add(
            {
                "cType": "IN",
                "cProduct": "CLAV-SF",
                "dQty": "2",
                "cWarehouse": "ENT-01",
                "cLocation": "A-01-02-A",
                "cDocType": "PROD",
                "cDocNo": "1",
            },
            user="test",
        )
    assert m["cDocType"] == "PROD"
