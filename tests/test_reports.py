"""Reports > Supply chain indicators (step 7 of the SCOR / ISO plan): the API on the demo data and after a production
order, the period checked, the access of the roles."""

import pytest
from test_production_floor import _stock

URL = "/api/kpi/scor"
ORDERS = "/api/production-orders"


def _k(out, group, key):
    return next(k for k in out[group] if k["key"] == key)


def test_the_indicators_of_the_demo(client):
    r = client.get(URL)
    assert r.status_code == 200, r.get_json()
    out = r.get_json()
    assert out["period"]["days"] == 90 and out["period"]["horizon"] == 30
    assert {k["key"] for k in out["reliability"]} == {
        "perfect_order",
        "prod_on_time",
        "prod_yield",
        "supplier_fill",
        "supplier_quality",
        "steps_first_time",
    }
    assert [len(out[g]) for g in ("responsiveness", "cost", "assets")] == [2, 2, 5]
    # the stock value is the one of Inventory > Inventory valuation
    rows = client.get("/api/inventory/valuation?size=1000").get_json()["items"]
    assert _k(out, "assets", "inventory_value")["value"] == pytest.approx(
        sum(float(v["dValue"]) for v in rows), abs=0.05
    )
    assert set(out["products"]) == {"rows", "total", "slow"} and set(out["lots"]) == {"expiring", "held"}


@pytest.mark.parametrize(
    "query, code",
    [
        ("from=2026-12-01&to=2026-11-01", "invalid_period"),
        ("from=yesterday", "invalid_date"),
        ("horizon=999", "invalid_choice"),
    ],
)
def test_a_wrong_period_is_refused(client, query, code):
    r = client.get(f"{URL}?{query}")
    assert r.status_code == 400 and r.get_json()["error"] == code


def test_a_production_order_feeds_the_indicators(client):
    _stock(client)
    o = client.post(
        ORDERS, json={"cProduct": "PAIN-BL-675", "dQty": "400", "dStart": "2026-12-01", "dDue": "2026-12-02"}
    )
    no = o.get_json()["iNo"]
    client.post(f"{ORDERS}/{no}/release", json={})
    rec = {"iOpSeq": 20, "iStep": 40, "cValue": "22", "cComment": "warm water added"}  # TEMP_PATE below 24: a warning
    assert client.post(f"{ORDERS}/{no}/steps/record", json=rec).status_code == 200
    assert client.post(f"{ORDERS}/{no}/report", json={"dQty": "380", "dDate": "2026-12-01"}).status_code == 200
    assert client.post(f"{ORDERS}/{no}/complete", json={}).status_code == 200
    out = client.get(f"{URL}?from=2026-01-01&to=2030-12-31").get_json()
    assert _k(out, "reliability", "prod_yield")["value"] == pytest.approx(0.95)
    assert _k(out, "reliability", "steps_first_time")["den"] == 1
    assert [(d["iOrder"], d["cStep"], d["cAction"], d["cComment"]) for d in out["deviations"]] == [
        (no, "20/40", "warn", "warm water added")
    ]
    # the materials went out for the order: stock used in the period
    assert _k(out, "assets", "inventory_turns")["num"] > 0


def test_the_screen_follows_the_role(client, admin):
    r = admin.post(
        "/api/roles", json={"cCode": "NO-REP", "cDescFR": "Sans", "cDescEN": "None", "permissions": ["inv.items:view"]}
    )
    assert r.status_code == 201, r.get_json()
    assert (
        admin.post(
            "/api/users", json={"username": "norep", "name": "N", "role": "NO-REP", "password": "Secret-123"}
        ).status_code
        == 201
    )
    other = client.application.test_client()
    other.post("/api/auth/login", json={"username": "norep", "password": "Secret-123"})
    assert other.get(URL).status_code == 403
    admin.put(
        "/api/roles/NO-REP",
        json={"cCode": "NO-REP", "cDescFR": "Sans", "cDescEN": "None", "permissions": ["rep.scor:view"]},
    )
    assert other.get(URL).status_code == 200
