"""Production orders (M3a): drafts from the approved recipe, release / unrelease / cancel, history, permissions."""

import pytest

URL = "/api/production-orders"


def _new(client, **over):
    body = {"cProduct": "PAIN-BL-675", "dQty": "400", "dStart": "2026-12-01", "dDue": "2026-12-02", **over}
    return client.post(URL, json=body)


def test_create_takes_the_default_recipe_and_explodes_it(client):
    r = _new(client)
    assert r.status_code == 201, r.get_json()
    o = r.get_json()
    assert (o["iNo"], o["cStatus"], o["cRevision"], o["cUOM"]) == (1, "draft", "A", "UN")
    assert o["cWarehouse"] == "ENT-01"  # the product's default warehouse
    mats = {m["cComponent"]: m for m in o["materials"]}
    assert set(mats) == {"FARINE-T55", "LEVURE", "SEL-FIN", "SAC-PAIN"}
    # explode of the recipe for 400 = the materials of the order, in stock units
    e = client.get("/api/recipes/PAIN-BL-675/A/explode?qty=400").get_json()
    want = {m["cComponent"]: m["dStockQty"] for m in e["materials"]}
    assert {k: float(v["dQtyRequired"]) for k, v in mats.items()} == pytest.approx(want, abs=1e-3)
    assert float(o["dEstCost"]) == pytest.approx(e["dTotalCost"])
    assert [op["iOpSeq"] for op in o["operations"]] == [op["iOpSeq"] for op in e["operations"]]
    assert all("dAvailable" in m and "dShort" in m for m in o["materials"])
    assert [h["cAction"] for h in o["history"]] == ["created"]
    assert o["cUser"] and o["dCreated"]


def test_list_and_calc(client):
    _new(client)
    rows = client.get(URL).get_json()["items"]
    assert rows[0]["iMaterials"] == 4 and "materials" not in rows[0]
    calc = client.post(URL + "/calc", json={"cProduct": "PAIN-BL-675", "dQty": "200"}).get_json()
    assert calc["iNo"] == 0 and calc["materials"] and calc["dStart"]
    assert client.post(URL + "/calc", json={}).get_json()["materials"] == []
    assert len(client.get(URL).get_json()["items"]) == 1  # calc saves nothing


@pytest.mark.parametrize(
    "over,error,field",
    [
        ({"cProduct": ""}, "required", "cProduct"),
        ({"cProduct": "NOPE"}, "unknown_ref", "cProduct"),
        ({"cProduct": "FARINE-T55"}, "not_made", "cProduct"),
        ({"cProduct": "JUMBO-CO17"}, "no_approved_recipe", "cProduct"),
        ({"cRevision": "B"}, "no_approved_recipe", "cRevision"),
        ({"cRevision": "Z"}, "unknown_ref", "cRevision"),
        ({"dQty": "0"}, "positive", "dQty"),
        ({"dQty": ""}, "required", "dQty"),
        ({"dDue": "2026-11-01"}, "end_before_start", "dDue"),
        ({"cWarehouse": "NOWH"}, "unknown_ref", "cWarehouse"),
    ],
)
def test_create_refused(client, over, error, field):
    r = _new(client, **over)
    assert r.status_code == 400 and (r.get_json()["error"], r.get_json()["field"]) == (error, field)


def test_update_recalculates_and_only_a_draft_changes(client):
    _new(client)
    o = client.put(URL + "/1", json={"dQty": "200", "cNotes": "rush"}).get_json()
    sac = next(m for m in o["materials"] if m["cComponent"] == "SAC-PAIN")
    assert float(o["dQty"]) == 200 and float(sac["dQtyRequired"]) == pytest.approx(200, rel=0.2)
    rel = client.post(URL + "/1/release", json={"cComment": "go"}).get_json()
    assert rel["cStatus"] == "released" and rel["cReleasedBy"] and rel["dReleased"]
    assert client.put(URL + "/1", json={"dQty": "300"}).status_code == 409
    assert client.delete(URL + "/1").status_code == 409
    assert client.post(URL + "/1/release").status_code == 409
    back = client.post(URL + "/1/unrelease").get_json()
    assert back["cStatus"] == "draft" and back["dReleased"] == ""
    cancelled = client.post(URL + "/1/cancel", json={"cComment": "no flour"}).get_json()
    assert cancelled["cStatus"] == "cancelled"
    assert [(h["cAction"], h["cTo"]) for h in cancelled["history"]] == [
        ("created", "draft"),
        ("release", "released"),
        ("unrelease", "draft"),
        ("cancel", "cancelled"),
    ]
    assert cancelled["history"][-1]["cComment"] == "no flour"
    assert client.post(URL + "/1/release").status_code == 409
    assert client.post(URL + "/1/explode").status_code == 404


def test_delete_a_draft_and_numbers_go_on(client):
    _new(client)
    assert client.delete(URL + "/1").status_code == 200
    assert _new(client).get_json()["iNo"] == 2


def test_shortage_is_shown(client):
    o = _new(client, dQty="1000000").get_json()
    assert o["lShort"] is True
    assert any(float(m["dShort"]) > 0 for m in o["materials"])


def test_product_used_by_an_order_cannot_be_deleted(client):
    _new(client)
    r = client.delete("/api/products/SAC-PAIN")
    assert r.status_code == 409


def test_made_products_lookup(client):
    codes = [r["code"] for r in client.get("/api/lookups/made_products").get_json()]
    assert "PAIN-BL-675" in codes and "FARINE-T55" not in codes and "JUMBO-CO17" not in codes


def test_reset_empties_the_orders(admin):
    assert _new(admin).status_code == 201
    assert admin.post("/api/reset").status_code == 200
    assert admin.get(URL).get_json()["items"] == []
    assert _new(admin).get_json()["iNo"] == 1


def test_approved_revisions_lookup_and_base_quantity(client):
    revs = client.get("/api/lookups/approved_revisions?product=pain-bl-675").get_json()
    assert [r["code"] for r in revs] == ["A"] and "★" in revs[0]["label"]  # B is in review
    assert client.get("/api/lookups/approved_revisions?product=").get_json() == []
    calc = client.post(URL + "/calc", json={"cProduct": "PAIN-BL-675"}).get_json()  # a product just picked
    base = client.get("/api/recipes/PAIN-BL-675/A").get_json()["dBaseQty"]
    assert float(calc["dQty"]) == float(base) and calc["materials"]
