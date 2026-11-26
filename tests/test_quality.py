"""Quality (step 5): the status of the lots (a lot not released is left out of the sales and the production orders)
and the nonconformances (hold the lot, close with a disposition and a corrective action)."""

import pytest

DAY = "2026-12-01"
BREAD = "PAIN-BL-675"


def _move(client, prod, loc, lot, exp, qty, cost="1.00"):
    body = {"cType": "IN", "cProduct": prod, "dQty": qty, "cWarehouse": "ENT-01", "cLocation": loc}
    body.update({"cLot": lot, "dExpiry": exp, "dUnitCost": cost, "dDate": "2026-11-20"})
    r = client.post("/api/stock-movements", json=body)
    assert r.status_code == 201, r.get_json()


@pytest.fixture
def bread(client):
    """Two lots of bread: B1 expires first (FEFO takes it first), B2 later."""
    _move(client, BREAD, "A-01-01-B", "B1", "2027-01-10", "20")
    _move(client, BREAD, "A-01-02-A", "B2", "2027-02-10", "20")


def _invoice(client, qty):
    body = {"cCustomer": "HOTEL-LAURIER", "dDate": "2026-12-02", "cWarehouse": "ENT-01"}
    body["lines"] = [{"cProduct": BREAD, "dQty": qty}]
    r = client.post("/api/sales-invoices", json=body)
    assert r.status_code == 201, r.get_json()
    return r.get_json()["iNo"]


def _status(client, lot, status, reason="lab result awaited"):
    return client.post(f"/api/lot-status/{BREAD}/{lot}", json={"cStatus": status, "cReason": reason})


def _lot(client, lot, product=BREAD):
    return client.get(f"/api/lot-status/{product}/{lot}").get_json()


def test_a_lot_without_a_status_is_released_and_listed_with_its_stock(client, bread):
    data = client.get(f"/api/lot-status?product={BREAD}").get_json()
    rows = {r["cLot"]: r for r in data["items"]}
    assert {"B1", "B2"} <= set(rows)
    b1 = rows["B1"]
    assert (b1["cStatus"], float(b1["dOnHand"]), b1["dExpiry"], b1["cWhere"]) == (
        "released",
        20,
        "2027-01-10",
        "ENT-01/A-01-01-B",
    )
    assert data["counts"]["released"] >= 2 and data["counts"]["on_hold"] == 0
    assert _lot(client, "B1")["history"] == []


def test_change_needs_a_reason_and_a_new_status_and_is_kept_in_the_history(client, bread):
    assert _status(client, "B1", "on_hold", "").get_json()["field"] == "cReason"
    assert _status(client, "B1", "frozen").get_json()["error"] == "invalid_choice"
    assert _status(client, "B1", "released").get_json()["error"] == "same_status"
    assert _status(client, "ZZZ", "on_hold").status_code == 404
    r = _status(client, "b1", "quarantine", "supplier recall")
    assert r.status_code == 200, r.get_json()
    lot = r.get_json()
    assert (lot["cLot"], lot["cStatus"], lot["cReason"], lot["cUser"]) == ("B1", "quarantine", "supplier recall", "api")
    assert _status(client, "B1", "released", "checked: conform").status_code == 200
    h = _lot(client, "B1")["history"]
    assert [(e["cFrom"], e["cTo"], e["cReason"]) for e in h] == [
        ("quarantine", "released", "checked: conform"),
        ("released", "quarantine", "supplier recall"),
    ]
    blocked = client.get("/api/lot-status?status=blocked").get_json()["items"]
    assert "B1" not in [r["cLot"] for r in blocked]


def test_a_held_lot_is_not_sold_the_next_released_lot_is(client, bread):
    assert _status(client, "B1", "on_hold").status_code == 200
    no = _invoice(client, "5")
    r = client.post(f"/api/sales-invoices/{no}/post")
    assert r.status_code == 200, r.get_json()
    lots = {a["cLot"] for a in r.get_json()["allocations"]}
    assert lots == {"B2"}


def test_when_only_held_lots_are_left_the_sale_says_so(client, bread):
    for lot in ("B1", "B2"):
        assert _status(client, lot, "rejected").status_code == 200
    others = [
        r for r in client.get(f"/api/lot-status?product={BREAD}").get_json()["items"] if r["cStatus"] == "released"
    ]
    for r in others:  # the demo's own bread lots
        assert _status(client, r["cLot"], "on_hold").status_code == 200
    no = _invoice(client, "5")
    r = client.post(f"/api/sales-invoices/{no}/post")
    assert r.status_code == 400
    assert r.get_json()["error"] == "insufficient_released"


def test_a_held_material_is_not_issued_to_a_production_order(client):
    _move(client, "FARINE-T55", "A-01-01-B", "F1", "2027-01-31", "500", "0.85")
    _move(client, "LEVURE", "A-01-01-B", "LV1", "2027-01-31", "10", "6.00")
    _move(client, "SEL-FIN", "A-01-02-A", "S1", "", "10", "1.00")
    _move(client, "SAC-PAIN", "A-01-01-A", "", "", "1000", "0.05")
    held = client.post(
        "/api/lot-status/hold", json={"lots": [{"cProduct": "FARINE-T55", "cLot": "F1"}], "cReason": "recall"}
    )
    assert held.get_json()["changed"] == [{"cProduct": "FARINE-T55", "cLot": "F1"}]
    o = client.post("/api/production-orders", json={"cProduct": BREAD, "dQty": "400", "dStart": DAY}).get_json()
    flour = next(m for m in o["materials"] if m["cComponent"] == "FARINE-T55")
    assert float(flour["dAvailable"]) == 0  # the held flour is not available
    assert client.post(f"/api/production-orders/{o['iNo']}/release", json={}).status_code == 200
    r = client.post(f"/api/production-orders/{o['iNo']}/issue/check", json={"dDate": DAY})
    problems = {p["cComponent"]: p["code"] for p in r.get_json()["problems"]}
    assert problems["FARINE-T55"] == "insufficient_released"


def test_hold_many_keeps_the_lots_already_held(client, bread):
    assert _status(client, "B1", "quarantine").status_code == 200
    lots = [{"cProduct": BREAD, "cLot": "B1"}, {"cProduct": BREAD, "cLot": "B2"}, {"cProduct": BREAD, "cLot": "b2"}]
    assert client.post("/api/lot-status/hold", json={"lots": lots, "cReason": ""}).get_json()["field"] == "cReason"
    r = client.post("/api/lot-status/hold", json={"lots": lots, "cReason": "recall 12"}).get_json()
    assert r == {"changed": [{"cProduct": BREAD, "cLot": "B2"}], "kept": [{"cProduct": BREAD, "cLot": "B1"}]}
    assert _lot(client, "B1")["cStatus"] == "quarantine" and _lot(client, "B2")["cStatus"] == "on_hold"


def test_the_trace_shows_the_status_of_the_lots(client, bread):
    assert _status(client, "B2", "on_hold").status_code == 200
    t = client.get(f"/api/traceability?product={BREAD}&lot=B2").get_json()
    assert t["cStatus"] == "on_hold"
    assert [n["cStatus"] for n in t["recall"]["lots"]] == ["on_hold"]
    assert {s["cStatus"] for s in t["recall"]["stock"]} == {"on_hold"}


# ------------------------------------------------------------------ nonconformances
NC = "/api/nonconformances"


def _nc(client, **over):
    body = {"cSource": "customer", "cRef": "complaint 7", "cProduct": BREAD, "cLot": "B1", "dQty": "3"}
    body.update({"cSeverity": "major", "cDescription": "mould on the crust", **over})
    return client.post(NC, json=body)


def test_a_nonconformance_needs_a_description_and_a_known_lot(client, bread):
    assert _nc(client, cDescription="").get_json()["field"] == "cDescription"
    assert _nc(client, cLot="NOPE").get_json()["error"] == "unknown_lot"
    assert _nc(client, cProduct="", cLot="B1").get_json()["field"] == "cProduct"
    assert _nc(client, cProduct="NOPE").get_json()["error"] == "unknown_ref"


def test_opening_holds_the_lot_and_use_as_is_releases_it(client, bread):
    r = _nc(client, cLot="b1")
    assert r.status_code == 201, r.get_json()
    nc = r.get_json()
    no = nc["iNo"]
    assert (nc["cStatus"], nc["cLot"], nc["cUOM"], nc["cLotStatus"], nc["cDisposition"]) == (
        "open",
        "B1",
        "UN",
        "on_hold",
        "pending",
    )
    lot = _lot(client, "B1")
    assert lot["iNC"] == no and lot["cReason"].startswith(f"NC {no}: mould")
    assert [h["cAction"] for h in nc["history"]] == ["created", "lot_held"]
    # closing needs the decision
    assert client.post(f"{NC}/{no}/close", json={}).get_json()["field"] == "cDisposition"
    r = client.post(f"{NC}/{no}/close", json={"cDisposition": "use_as_is"})
    assert r.get_json()["field"] == "cAction"
    r = client.post(f"{NC}/{no}/close", json={"cDisposition": "use_as_is", "cAction": "dry storage", "cCause": "humid"})
    assert r.status_code == 200, r.get_json()
    done = r.get_json()
    assert (done["cStatus"], done["cClosedBy"], done["cLotStatus"], done["cCause"]) == (
        "closed",
        "api",
        "released",
        "humid",
    )
    assert [h["cAction"] for h in done["history"]][-2:] == ["lot_released", "closed"]
    # a closed nonconformance is read only, until it is reopened (with a reason)
    assert client.put(f"{NC}/{no}", json={"cCause": "x"}).status_code == 409
    assert client.delete(f"{NC}/{no}").status_code == 409
    assert client.post(f"{NC}/{no}/reopen", json={"cComment": ""}).get_json()["field"] == "cComment"
    r = client.post(f"{NC}/{no}/reopen", json={"cComment": "more mould found"})
    assert r.get_json()["cStatus"] == "open" and not r.get_json().get("dClosed")
    assert "dClosed" not in client.get(f"{NC}/{no}").get_json()


def test_scrap_rejects_the_lot_and_rework_keeps_it_on_hold(client, bread):
    a = _nc(client).get_json()["iNo"]
    r = client.post(f"{NC}/{a}/close", json={"cDisposition": "rework", "cAction": "re-bake"})
    assert r.get_json()["cLotStatus"] == "on_hold"
    b = _nc(client, cLot="B2").get_json()["iNo"]
    r = client.post(f"{NC}/{b}/close", json={"cDisposition": "scrap", "cAction": "supplier audit"})
    assert r.get_json()["cLotStatus"] == "rejected"
    assert _lot(client, "B2")["iNC"] == b


def test_use_as_is_does_not_release_a_lot_held_by_something_else(client, bread):
    assert _status(client, "B1", "quarantine", "lab").status_code == 200
    no = _nc(client).get_json()["iNo"]  # already held: the nonconformance does not change it
    assert _lot(client, "B1")["cReason"] == "lab"
    r = client.post(f"{NC}/{no}/close", json={"cDisposition": "use_as_is", "cAction": "none needed"})
    assert r.get_json()["cLotStatus"] == "quarantine"


def test_a_nonconformance_without_hold_or_lot_and_the_list(client, bread):
    r = _nc(client, lHoldLot=False)
    assert r.get_json()["cLotStatus"] == "released"
    assert _nc(client, cProduct="", cLot="", cDescription="wrong label printed").status_code == 201
    rows = client.get(NC + "?cStatus=open").get_json()["items"]
    assert len(rows) == 2 and "history" not in rows[0]
    first = rows[-1]["iNo"]
    assert client.delete(f"{NC}/{first}").status_code == 200  # holds no lot: a mistake can be deleted
    held = _nc(client).get_json()["iNo"]
    assert client.delete(f"{NC}/{held}").get_json()["error"] == "nc_holds_lot"


def test_the_quality_routes_follow_the_role(client, admin, bread):
    r = admin.post(
        "/api/roles",
        json={
            "cCode": "QA-VIEW",
            "cDescFR": "Qualité",
            "cDescEN": "Quality",
            "permissions": ["qa.lots:view", "qa.nc:view"],
        },
    )
    assert r.status_code == 201, r.get_json()
    r = admin.post("/api/users", json={"username": "qa1", "name": "QA", "role": "QA-VIEW", "password": "Secret-123"})
    assert r.status_code == 201, r.get_json()
    other = client.application.test_client()
    assert other.post("/api/auth/login", json={"username": "qa1", "password": "Secret-123"}).status_code == 200
    assert other.get("/api/lot-status").status_code == 200
    assert other.get(NC).status_code == 200
    assert _status(other, "B1", "on_hold").status_code == 403
    assert other.post("/api/lot-status/hold", json={"lots": [], "cReason": "x"}).status_code == 403
    assert _nc(other).status_code == 403
