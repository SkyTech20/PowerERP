"""The shop floor of the production orders (M3b): issue by lot (FEFO), return, report with a new lot, backflush,
complete / close with the actual cost, the stock movements PROD."""

import pytest

URL = "/api/production-orders"
STOCK = [  # product, location, lot, expiry, qty, cost
    ("FARINE-T55", "A-02-01-A", "F-LATE", "2027-03-01", "100", "0.90"),
    ("FARINE-T55", "B-01-02-A", "F-SOON", "2026-12-20", "100", "0.80"),
    ("LEVURE", "A-01-01-B", "LV1", "2027-01-31", "10", "6.00"),
    ("SEL-FIN", "A-01-02-A", "S1", "", "10", "1.00"),
    ("SAC-PAIN", "A-01-01-A", "", "", "1000", "0.05"),
]


def _stock(client):
    for prod, loc, lot, exp, qty, cost in STOCK:
        body = {"cType": "IN", "cProduct": prod, "dQty": qty, "cWarehouse": "ENT-01", "cLocation": loc}
        body.update({"cLot": lot, "dExpiry": exp, "dUnitCost": cost, "dDate": "2026-11-20"})
        r = client.post("/api/stock-movements", json=body)
        assert r.status_code in (200, 201), r.get_json()


@pytest.fixture
def order(client):
    _stock(client)
    o = client.post(URL, json={"cProduct": "PAIN-BL-675", "dQty": "400", "dStart": "2026-12-01"}).get_json()
    assert client.post(f"{URL}/{o['iNo']}/release", json={}).status_code == 200
    return o["iNo"]


def _moves(client, no):
    rows = client.get("/api/stock-movements?size=500").get_json()["items"]
    return [m for m in rows if m["cDocType"] == "PROD" and m["cDocNo"] == str(no)]


def test_issue_check_takes_the_lots_expiring_first_and_moves_nothing(client, order):
    r = client.post(f"{URL}/{order}/issue/check", json={"dDate": "2026-12-01"}).get_json()
    assert r["ok"], r
    flour = [(a["cLot"], float(a["dQty"])) for a in r["allocations"] if a["cComponent"] == "FARINE-T55"]
    assert flour == [("F-SOON", 100.0), ("F-LATE", pytest.approx(73.4694))]
    assert {a["cComponent"] for a in r["allocations"]} == {"FARINE-T55", "LEVURE", "SEL-FIN"}  # SAC-PAIN: backflush
    assert _moves(client, order) == []
    assert client.get(f"{URL}/{order}").get_json()["cStatus"] == "released"


def test_issue_report_complete_close(client, order):
    r = client.post(f"{URL}/{order}/issue", json={"dDate": "2026-12-01"})
    assert r.status_code == 200, r.get_json()
    o = r.get_json()
    assert o["cStatus"] == "in_progress"
    assert [h["cAction"] for h in o["history"]][-1] == "start"
    mats = {m["cComponent"]: m for m in o["materials"]}
    assert float(mats["FARINE-T55"]["dQtyIssued"]) == pytest.approx(173.4694)
    assert float(mats["SAC-PAIN"]["dQtyIssued"]) == 0
    assert {i["cLot"] for i in o["issues"]} == {"F-SOON", "F-LATE", "LV1", "S1"}
    assert all(i["iMovement"] and float(i["dValue"]) > 0 for i in o["issues"])
    assert float(o["dActMaterialCost"]) == pytest.approx(sum(float(i["dValue"]) for i in o["issues"]), abs=0.01)
    # nothing left to issue
    assert client.post(f"{URL}/{order}/issue", json={}).get_json()["error"] == "nothing_to_issue"
    # report 200 of the 400: the bags are backflushed for 200, the bread goes in with its lot and expiry
    r = client.post(f"{URL}/{order}/report", json={"dQty": "200", "dDate": "2026-12-01"})
    assert r.status_code == 200, r.get_json()
    o = r.get_json()
    out = o["outputs"][0]
    assert (out["cLot"], out["dExpiry"], out["cWarehouse"], float(out["dQty"])) == ("MO1", "2026-12-08", "ENT-01", 200)
    assert out["cLocation"] and out["iMovement"]
    assert o["cLot"] == "MO1" and float(o["dQtyDone"]) == 200
    bags = [i for i in o["issues"] if i["cKind"] == "backflush"]
    assert len(bags) == 1 and float(bags[0]["dQty"]) == pytest.approx(204.0816, abs=1e-3)
    stock = client.get("/api/inventory/stock?f_cProduct=PAIN-BL-675&size=100").get_json()["items"]
    assert any(s["cLot"] == "MO1" and float(s["dQtyOnHand"]) == 200 for s in stock)
    kinds = sorted((m["cType"], m["cProduct"]) for m in _moves(client, order))
    assert ("IN", "PAIN-BL-675") in kinds and kinds.count(("OUT", "FARINE-T55")) == 2
    # a cancelled or draft order can no longer be reached once the stock moved
    assert client.post(f"{URL}/{order}/cancel", json={}).status_code == 409
    # complete, reopen, complete, close: the actual cost is kept
    assert client.post(f"{URL}/{order}/complete", json={}).get_json()["cStatus"] == "completed"
    assert client.post(f"{URL}/{order}/report", json={"dQty": "1"}).status_code == 409  # no report once completed
    assert client.post(f"{URL}/{order}/reopen", json={}).get_json()["cStatus"] == "in_progress"
    client.post(f"{URL}/{order}/complete", json={})
    o = client.post(f"{URL}/{order}/close", json={"cComment": "ok"}).get_json()
    assert o["cStatus"] == "closed" and o["dClosed"] and o["cClosedBy"]
    est = float(o["dEstUnitCost"]) * 200
    assert float(o["dVariance"]) == pytest.approx(float(o["dActCost"]) - est, abs=0.02)
    assert float(o["dActUnitCost"]) == pytest.approx(float(o["dActCost"]) / 200, abs=1e-3)
    assert [h["cAction"] for h in o["history"]] == [
        "created",
        "release",
        "start",
        "complete",
        "reopen",
        "complete",
        "close",
    ]


def test_issue_lines_and_return(client, order):
    r = client.post(f"{URL}/{order}/issue", json={"lines": [{"iSeq": 10, "dQty": "120"}], "dDate": "2026-12-01"})
    o = r.get_json()
    flour = [(i["cLot"], float(i["dQty"])) for i in o["issues"]]
    assert flour == [("F-SOON", 100), ("F-LATE", 20)]
    # give back 5 of F-LATE: into its lot and location, at its cost
    r = client.post(f"{URL}/{order}/return", json={"iSeq": 10, "cLot": "F-LATE", "cLocation": "A-02-01-A", "dQty": "5"})
    assert r.status_code == 200, r.get_json()
    o = r.get_json()
    back = o["issues"][-1]
    assert back["cKind"] == "return" and float(back["dQty"]) == -5 and float(back["dValue"]) < 0
    assert float(o["materials"][0]["dQtyIssued"]) == 115
    over = client.post(
        f"{URL}/{order}/return", json={"iSeq": 10, "cLot": "F-LATE", "cLocation": "A-02-01-A", "dQty": "50"}
    )
    assert over.status_code == 409 and over.get_json()["error"] == "over_return"
    none = client.post(f"{URL}/{order}/return", json={"iSeq": 20, "cLot": "LV1", "cLocation": "A-01-01-B", "dQty": "1"})
    assert none.get_json()["error"] == "not_issued"


@pytest.mark.parametrize(
    "path, body, status, error",
    [
        ("issue", {"lines": [{"iSeq": 10, "dQty": "500"}]}, 409, "insufficient_stock"),
        ("issue", {"lines": [{"iSeq": 99, "dQty": "1"}]}, 400, "unknown_ref"),
        ("issue", {"lines": [{"iSeq": 10, "dQty": "-1"}]}, 400, "positive"),
        ("report", {"dQty": "0"}, 400, "positive"),
        ("report", {}, 400, "required"),
        ("issue", {"dDate": "2026-13-45"}, 400, "invalid_date"),
    ],
)
def test_refused_and_nothing_moves(client, order, path, body, status, error):
    r = client.post(f"{URL}/{order}/{path}", json=body)
    assert (r.status_code, r.get_json()["error"]) == (status, error)
    assert _moves(client, order) == []


def test_an_expired_lot_is_never_used(client, order):
    r = client.post(f"{URL}/{order}/issue/check", json={"dDate": "2026-12-21"}).get_json()
    assert [a["cLot"] for a in r["allocations"] if a["cComponent"] == "FARINE-T55"] == ["F-LATE"]
    assert r["problems"][0]["cComponent"] == "FARINE-T55"  # 100 left only


def test_a_draft_has_no_shop_floor(client):
    o = client.post(URL, json={"cProduct": "PAIN-BL-675", "dQty": "10"}).get_json()
    assert client.post(f"{URL}/{o['iNo']}/issue", json={}).status_code == 409
    assert client.post(f"{URL}/{o['iNo']}/complete", json={}).status_code == 409


def test_complete_needs_a_quantity_made(client, order):
    client.post(f"{URL}/{order}/issue", json={"lines": [{"iSeq": 30, "dQty": "1"}]})
    r = client.post(f"{URL}/{order}/complete", json={})
    assert (r.status_code, r.get_json()["error"]) == (409, "nothing_made")
