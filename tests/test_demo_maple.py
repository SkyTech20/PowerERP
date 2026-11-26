"""The maple products demo (the default scenario, data/maple built by tools/make_maple_data.py): its master data, and
the story of October and November 2026 (story.json) that replaces the seed of the stock, the production orders, the
lot status, the nonconformances and the sales invoices."""

import pytest

FINISHED = {"MAPLE-SYRUP-540", "MAPLE-SYRUP-250", "MAPLE-BUTTER-200", "MAPLE-CANDY-12", "MAPLE-FUDGE-250"}


@pytest.fixture
def maple(admin):
    r = admin.post("/api/reset", json={"scenario": "maple"})
    assert r.get_json() == {"ok": True, "scenario": "maple"}, r.get_json()
    try:
        yield admin
    finally:
        admin.post("/api/reset", json={"scenario": "manufacturing"})


def _items(client, path):
    return client.get(path + ("&" if "?" in path else "?") + "size=1000").get_json()["items"]


def test_master_data(maple):
    products = {p["cCode"]: p for p in _items(maple, "/api/products")}
    assert {c for c, p in products.items() if p["cClass"] == "finished"} == FINISHED
    assert "LAP-14I7" not in products and "PAIN-BL-675" not in products  # nothing of the other scenarios
    # pure syrup and maple butter are basic groceries (zero-rated), candy and fudge are taxed
    taxes = {c: products[c]["cSalesTaxGroup"] for c in FINISHED}
    assert taxes == {
        "MAPLE-SYRUP-540": "ZERO",
        "MAPLE-SYRUP-250": "ZERO",
        "MAPLE-BUTTER-200": "ZERO",
        "MAPLE-CANDY-12": "QC",
        "MAPLE-FUDGE-250": "QC",
    }
    for bulk in ("SYRUP-BULK-AMB", "SYRUP-BULK-DRK"):
        assert products[bulk]["lLotControl"] and products[bulk]["cClass"] == "raw"
    recipes = {r["cProduct"] for r in _items(maple, "/api/recipes") if r["cStatus"] == "approved" and r["lDefault"]}
    assert recipes == FINISHED | {"SYRUP-STD"}
    # the critical control points of the recipes: Brix, filling and cooking temperatures, the milk allergen
    steps = maple.get("/api/recipes/MAPLE-BUTTER-200/A").get_json()["steps"]
    cooling = next(s for s in steps if s.get("cParam") == "TEMP_REFROID")
    assert (cooling["dMax"], cooling["lCritical"], cooling["cOnFail"]) == ("10", True, "hold_lot")
    fudge = maple.get("/api/recipes/MAPLE-FUDGE-250/A").get_json()
    assert {m["cComponent"] for m in fudge["materials"]} >= {"SYRUP-STD", "CREAM-35", "BUTTER"}
    customers = {c["cCode"]: c for c in _items(maple, "/api/customers")}
    assert set(customers) == {"EPICERIE-STDENIS", "BOUTIQUE-VQ", "LAURENTIAN-HOTELS", "DISTRIB-CHAUDIERE"}
    assert customers["LAURENTIAN-HOTELS"]["cLang"] == "en"
    assert maple.get("/api/company").get_json()["cName"] == "Érablière Démo"
    p = maple.get("/api/pricing?customer=DISTRIB-CHAUDIERE&product=MAPLE-SYRUP-540&qty=300&date=2026-11-26").get_json()
    assert (p["cPriceList"], p["dPrice"], p["dDiscountPct"], p["dNetPrice"]) == ("DISTRIB", "8.80", "3", "8.536")


def test_the_story(maple):
    orders = {o["iNo"]: o for o in _items(maple, "/api/production-orders")}
    assert [o["cStatus"] for o in orders.values()].count("closed") == 10
    assert {o["cStatus"] for o in orders.values()} == {"closed", "completed", "released", "draft"}
    invoices = _items(maple, "/api/sales-invoices")
    posted = [i for i in invoices if i["cStatus"] == "posted"]
    assert len([i for i in posted if i["cType"] == "invoice"]) == 9
    assert [i["cInvoiceNo"] for i in posted if i["cType"] == "credit"] == ["NC-1"]
    assert len([i for i in invoices if i["cStatus"] == "draft"]) == 2
    # a new invoice or order continues the numbering of the story
    no = maple.post("/api/production-orders", json={"cProduct": "SYRUP-STD", "dQty": "100", "cWarehouse": "PLANT"})
    assert no.get_json()["iNo"] == max(orders) + 1
    ncs = {n["cSource"]: n for n in _items(maple, "/api/nonconformances")}
    assert (ncs["reception"]["cStatus"], ncs["reception"]["cDisposition"]) == ("closed", "return_supplier")
    assert (ncs["production"]["cStatus"], ncs["production"]["cLot"]) == ("open", "MO9")


def test_a_can_is_traced_back_to_the_sugar_bush(maple):
    t = maple.get("/api/traceability?product=MAPLE-SYRUP-540&lot=MO8").get_json()

    def sources(node):
        yield from node.get("sources", [])
        for i in node.get("inputs", []):
            yield from sources(i)

    found = {(s["cSupplier"], s["cSupplierLot"]) for s in sources(t["origin"]) if s["cKind"] == "reception"}
    assert ("GAGNON", "B-0412 / récolte 2026-03-24") in found
    assert {s for s, _lot in found} >= {"GAGNON", "CANTONS", "TREMBLAY"}
    assert not any("T-140" in lot for _s, lot in found)  # the barrel that tasted of "bourgeon" was never used


def test_quality_in_the_stock(maple):
    stock = _items(maple, "/api/inventory/stock")
    on_hand = {(s["cProduct"], s["cLot"]): float(s["dQtyOnHand"]) for s in stock}
    assert ("SYRUP-BULK-AMB", "900106-3") not in on_hand  # returned to the supplier
    assert on_hand[("MAPLE-CANDY-12", "MO9")] == 400  # cooked too hot: held
    lot = maple.get("/api/lot-status/MAPLE-CANDY-12/MO9").get_json()
    assert lot["cStatus"] == "on_hold"
    # the draft for 48 boxes of candy cannot be posted: the released candy left is not enough (nothing changes)
    draft = next(
        i
        for i in _items(maple, "/api/sales-invoices")
        if i["cStatus"] == "draft" and i["cCustomer"] == "LAURENTIAN-HOTELS"
    )
    r = maple.post(f"/api/sales-invoices/{draft['iNo']}/post")
    assert (r.status_code, r.get_json()["error"]) == (400, "insufficient_released")
    other = next(
        i
        for i in _items(maple, "/api/sales-invoices")
        if i["cStatus"] == "draft" and i["cCustomer"] == "DISTRIB-CHAUDIERE"
    )
    assert maple.post(f"/api/sales-invoices/{other['iNo']}/check").get_json()["ok"]


def test_every_supply_chain_indicator_has_a_value(maple):
    k = maple.get("/api/kpi/scor?from=2026-09-01&to=2026-11-26").get_json()
    values = {x["key"]: x["value"] for group in ("reliability", "responsiveness", "cost", "assets") for x in k[group]}
    assert all(v is not None for v in values.values()), values
    assert 0 < values["perfect_order"] < 1 and 0 < values["prod_on_time"] < 1 and values["held_value"] > 0
    assert k["deviations"][0]["cValue"] == "118.5"
