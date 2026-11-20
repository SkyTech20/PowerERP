"""Products, taxes and inventory management (powererp/modules/inventory), on the seed in data/inventory.json."""


def mv(client, **over):
    body = {"cType": "IN", "cProduct": "CLAV-SF", "dQty": "1", "cWarehouse": "ENT-01", "cLocation": "A-01-02-A"}
    body.update(over)
    return client.post("/api/stock-movements", json=body)


def stock(client, product, wh=None):
    p = client.get(f"/api/products/{product}").get_json()
    if wh is None:
        return float(p["dQtyOnHand"])
    return float(next((s["dQtyOnHand"] for s in p["stock"] if s["cWarehouse"] == wh), 0))


# ------------------------------------------------------------------ taxes


def test_tax_code_rate_history(client):
    tvq = client.get("/api/tax-codes/TVQ").get_json()
    assert tvq["dCurrentRate"] == "9.975" and len(tvq["lines"]) == 2
    old = client.get("/api/tax-groups/QC/calc?amount=100&date=2012-06-01").get_json()
    assert [t["dTax"] for t in old["taxes"]] == ["5.00", "9.50"]
    now = client.get("/api/tax-groups/QC/calc?amount=100").get_json()
    assert now["dTotalTax"] == "14.98" and now["dTotal"] == "114.98"
    assert client.get("/api/tax-groups/EXO/calc?amount=100").get_json()["dTotalTax"] == "0.00"
    ns = client.get("/api/tax-groups/NS/calc?amount=100&date=2025-01-15").get_json()
    assert ns["dTotalTax"] == "15.00"


def test_compound_tax(client):
    client.post(
        "/api/tax-codes", json={"cCode": "T1", "cDescFR": "t1", "lines": [{"dStartDate": "2020-01-01", "dRate": "10"}]}
    )
    client.post(
        "/api/tax-codes", json={"cCode": "T2", "cDescFR": "t2", "lines": [{"dStartDate": "2020-01-01", "dRate": "10"}]}
    )
    r = client.post(
        "/api/tax-groups",
        json={
            "cCode": "CMP",
            "cDescFR": "c",
            "lines": [{"iSeq": 1, "cTaxCode": "t1"}, {"iSeq": 2, "cTaxCode": "T2", "lCompound": True}],
        },
    )
    assert r.status_code == 201 and r.get_json()["lines"][0]["cTaxCode"] == "T1"
    calc = client.get("/api/tax-groups/CMP/calc?amount=100").get_json()
    assert [t["dTax"] for t in calc["taxes"]] == ["10.00", "11.00"]


def test_tax_references_are_checked(client):
    r = client.post("/api/tax-groups", json={"cCode": "BAD", "cDescFR": "x", "lines": [{"cTaxCode": "NOPE"}]})
    assert r.status_code == 400 and r.get_json()["error"] == "unknown_ref"
    assert client.delete("/api/tax-codes/TPS").status_code == 409  # used by groups
    assert client.delete("/api/tax-groups/QC").status_code == 409  # used by products
    r = client.post(
        "/api/tax-codes",
        json={
            "cCode": "X",
            "cDescFR": "x",
            "lines": [{"dStartDate": "2026-02-01", "dEndDate": "2026-01-01", "dRate": "1"}],
        },
    )
    assert r.get_json()["error"] == "invalid_dates"


# ------------------------------------------------------------------ products


def test_product_crud_and_validation(client):
    body = {
        "cCode": "NEW-1",
        "cDescFR": "Nouveau",
        "cDescEN": "New",
        "cStockUOM": "UN",
        "cCategory": "PAP",
        "cSalesTaxGroup": "QC",
        "dPrice1": "$10,00",
        "lines": [{"cSupplierCode": "papcen", "dPurchasePrice": "6"}],
    }
    r = client.post("/api/products", json=body)
    assert r.status_code == 201, r.get_json()
    p = r.get_json()
    assert p["dPrice1"] == "10.00" and p["lines"][0]["cSupplierCode"] == "PAPCEN" and p["cType"] == "stock"
    assert client.post("/api/products", json=body).status_code == 409
    assert client.post("/api/products", json={**body, "cCode": "N2", "cCategory": "ZZZ"}).get_json() == {
        "error": "unknown_ref",
        "field": "cCategory",
    }
    assert (
        client.post("/api/products", json={**body, "cCode": "N3", "cType": "bogus"}).get_json()["error"]
        == "invalid_choice"
    )
    assert client.post("/api/products", json={"cCode": "N4", "cStockUOM": "UN"}).get_json() == {
        "error": "required",
        "field": "cDescFR",
    }
    r = client.put("/api/products/NEW-1", json={"cDescFR": "Renommé", "cType": "service"})
    assert r.get_json()["cDescFR"] == "Renommé" and r.get_json()["lStocked"] is False
    assert client.delete("/api/products/NEW-1").status_code == 200
    assert client.delete("/api/products/CLAV-SF").status_code == 409  # has movements


def test_product_shows_stock_cost_and_margin(client):
    p = client.get("/api/products/TUBE-T8").get_json()
    # 60 @ 12.50 then 40 @ 13.10: moving average 12.74
    assert p["dQtyOnHand"] == "100" and p["dAvgCost"] == "12.74" and p["dLastCost"] == "13.10"
    assert p["dStockValue"] == "1274.00" and p["dMarginPct"] == "27.2"
    clav = client.get("/api/products/CLAV-SF").get_json()
    assert clav["dQtyOnHand"] == "12" and clav["dQtyReserved"] == "2" and clav["dQtyAvailable"] == "10"
    listed = client.get("/api/products?q=clav").get_json()["items"][0]
    assert listed["dQtyOnHand"] == "12" and "lines" not in listed


# ------------------------------------------------------------------ warehouses and locations


def test_location_code_is_built_and_rules_apply(client):
    r = client.post(
        "/api/locations", json={"cWarehouse": "ent-01", "cZone": "C", "cAisle": "01", "cRack": "02", "cLevel": "A"}
    )
    assert r.status_code == 201 and r.get_json()["cCode"] == "C-01-02-A" and r.get_json()["cWarehouse"] == "ENT-01"
    assert client.get("/api/locations/ENT-01/C-01-02-A").status_code == 200
    assert client.post("/api/locations", json={"cWarehouse": "NOPE", "cCode": "X"}).get_json()["error"] == "unknown_ref"
    assert client.delete("/api/locations/ENT-01/A-01-02-A").status_code == 409  # has stock
    assert client.delete("/api/warehouses/ENT-01").status_code == 409


# ------------------------------------------------------------------ movements


def test_movements_update_balances_and_average_cost(client):
    assert mv(client, dQty="8", dUnitCost="65").status_code == 201
    p = client.get("/api/products/CLAV-SF").get_json()
    # 12 @ 59 + 8 @ 65 = 20 @ 61.40
    assert p["dQtyOnHand"] == "20" and p["dAvgCost"] == "61.40"
    out = mv(client, cType="OUT", dQty="5").get_json()
    assert out["dValue"] == "-307.00" and out["cUser"] == "api"
    assert stock(client, "CLAV-SF") == 15


def test_movement_rules(client):
    assert mv(client, cType="OUT", dQty="11").get_json() == {
        "error": "insufficient_stock",
        "field": "dQty",
        "detail": "10",
    }
    assert mv(client, cLocation="").get_json() == {"error": "required", "field": "cLocation"}
    assert mv(client, cLocation="A-02-02-A").get_json()["error"] == "blocked_location"
    assert mv(client, cProduct="INSP-EXT").get_json()["error"] == "not_stocked"
    assert mv(client, cProduct="EXT-5LB", dExpiry="2030-01-01").get_json()["error"] == "lot_required"
    assert mv(client, cProduct="EXT-5LB", cLot="L1").get_json() == {"error": "required", "field": "dExpiry"}
    assert mv(client, cProduct="LAP-14I7").get_json()["error"] == "serial_required"
    assert mv(client, cProduct="LAP-14I7", cSerial="X", dQty="2").get_json()["error"] == "serial_qty"
    assert mv(client, cProduct="LAP-14I7", cSerial="PF4K2A01").status_code == 409
    # B-01-01-A takes one product only
    assert mv(client, cLocation="B-01-01-A").get_json()["error"] == "location_mixed"
    # Warehouse without locations
    assert mv(client, cProduct="RIV-ALU-316", cWarehouse="ENT-02", cLocation="").status_code == 201
    # Movements cannot be changed
    assert client.put("/api/stock-movements/1", json={}).status_code == 409
    assert client.delete("/api/stock-movements/1").status_code == 409


def test_transfer_and_reservation(client):
    r = mv(client, cType="TRF", dQty="4", cWhTo="QUAR", cLocTo="")
    assert r.status_code == 201, r.get_json()
    assert stock(client, "CLAV-SF", "ENT-01") == 8 and stock(client, "CLAV-SF", "QUAR") == 4
    assert mv(client, cType="TRF", dQty="1", cWhTo="ENT-01", cLocTo="A-01-02-A").get_json()["error"] == "same_location"
    # 8 on hand, 2 reserved: 6 can be reserved, then nothing can leave
    assert mv(client, cType="RSV", dQty="7").get_json()["error"] == "insufficient_stock"
    assert mv(client, cType="RSV", dQty="6").status_code == 201
    assert mv(client, cType="OUT", dQty="1").get_json()["error"] == "insufficient_stock"
    assert mv(client, cType="RSV", dQty="-9").get_json()["error"] == "insufficient_reserved"
    rows = client.get("/api/inventory/stock?q=CLAV-SF&f_cWarehouse=ENT-01").get_json()["items"]
    assert rows[0]["dQtyReserved"] == "8" and rows[0]["dQtyAvailable"] == "0"


# ------------------------------------------------------------------ valuation, replenishment


def test_valuation(client):
    page = client.get("/api/inventory/valuation?f_cWarehouse=ENT-02&size=500").get_json()
    total = sum(float(r["dValue"]) for r in page["items"])
    assert page["total"] == 4 and abs(float(page["totalValue"]) - total) < 0.01
    s = client.get("/api/summary").get_json()
    assert s["products"] >= 16 and s["stockValue"] > 0 and s["reorderItems"] > 0


def test_replenishment_and_purchase_orders(client):
    rows = client.get("/api/inventory/replenishment?size=500").get_json()["items"]
    by = {r["cProduct"]: r for r in rows}
    # MON-27Q: 2 available, reorder at 4, max 10 -> 8 (supplier minimum 2)
    assert by["MON-27Q"]["dSuggestedQty"] == "8" and by["MON-27Q"]["cSupplierCode"] == "TECBUR"
    assert "CLAV-SF" not in by
    # AL6061-F125-48: 4 available, max 30 -> 26
    assert by["AL6061-F125-48"]["dPurchaseQty"] == "26"
    r = client.post(
        "/api/inventory/replenishment/po",
        json={
            "cWarehouse": "ENT-01",
            "lines": [
                {"cProduct": "MON-27Q", "dPurchaseQty": "8"},
                {"cProduct": "DOCK-USBC", "dPurchaseQty": "2"},
                {"cProduct": "TON-26A", "dPurchaseQty": "9"},
            ],
        },
    )
    assert r.status_code == 201, r.get_json()
    pos = r.get_json()["purchaseOrders"]
    assert sorted(p["cSupplierCode"] for p in pos) == ["PAPCEN", "TECBUR"]
    tec = client.get("/api/purchase-orders/" + next(p["cPO"] for p in pos if p["cSupplierCode"] == "TECBUR")).get_json()
    assert tec["lineCount"] == 2 and tec["dSubTotal"] == "3052.00"
    assert tec["dGST"] == "152.60" and tec["dPST"] == "304.44"  # QC purchase tax group, rounded per line
    # The open PO now counts as "on order": MON-27Q is no longer suggested
    rows = client.get("/api/inventory/replenishment?size=500").get_json()["items"]
    assert "MON-27Q" not in {r["cProduct"] for r in rows}


def test_stock_params(client):
    r = client.post(
        "/api/stock-params", json={"cProduct": "CLAV-SF", "cWarehouse": "QUAR", "dMinQty": "5", "dMaxQty": "2"}
    )
    assert r.get_json()["error"] == "max_below_min"
    assert client.post("/api/stock-params", json={"cProduct": "CLAV-SF", "cWarehouse": "ENT-01"}).status_code == 409
    assert client.put("/api/stock-params/CLAV-SF/ENT-01", json={"dReorderPoint": "11"}).status_code == 200
    rows = client.get("/api/inventory/replenishment?size=500").get_json()["items"]
    assert any(r["cProduct"] == "CLAV-SF" for r in rows)


# ------------------------------------------------------------------ physical count


def test_physical_count(client):
    r = client.post(
        "/api/stock-counts",
        json={"cWarehouse": "ENT-01", "cLocationPrefix": "A-02", "cDescription": "Décompte cyclique A-02"},
    )
    assert r.status_code == 201
    c = r.get_json()
    assert {l["cProduct"] for l in c["lines"]} == {"PAP-8511", "TON-26A", "ENV-10", "CRAY-HB"}
    lines = [
        {**l, "dQtyCounted": {"PAP-8511": "7", "TON-26A": "3", "CRAY-HB": "42"}.get(l["cProduct"], "")}
        for l in c["lines"]
    ]
    c = client.put(f"/api/stock-counts/{c['iNo']}", json={"lines": lines}).get_json()
    assert c["countedLines"] == 3 and next(l for l in c["lines"] if l["cProduct"] == "PAP-8511")["dDiff"] == "-1"
    posted = client.post(f"/api/stock-counts/{c['iNo']}/post").get_json()
    assert posted["cStatus"] == "Posted" and len(posted["movements"]) == 2  # TON-26A has no difference
    assert stock(client, "PAP-8511") == 7 and stock(client, "CRAY-HB") == 42 and stock(client, "ENV-10") == 12
    assert client.put(f"/api/stock-counts/{c['iNo']}", json={}).status_code == 409
    assert client.post(f"/api/stock-counts/{c['iNo']}/post").status_code == 409


def test_count_posting_is_all_or_nothing(client):
    c = client.post(
        "/api/stock-counts",
        json={
            "cWarehouse": "ENT-01",
            "lines": [
                {"cProduct": "CRAY-HB", "cLocation": "A-02-01-A", "dQtyCounted": "1"},
                {"cProduct": "CRAY-HB", "cLocation": "A-02-02-A", "dQtyCounted": "1"},
            ],
        },
    ).get_json()  # blocked location
    r = client.post(f"/api/stock-counts/{c['iNo']}/post")
    assert r.status_code == 400 and r.get_json()["error"] == "blocked_location"
    assert stock(client, "CRAY-HB") == 40


# ------------------------------------------------------------------ lookups, persistence, reset


def test_lookups_and_persistence(client):
    assert any(r["code"] == "QC" for r in client.get("/api/lookups/taxgroups").get_json())
    assert all(r["code"] != "INSP-EXT" for r in client.get("/api/lookups/stockproducts?q=insp").get_json())
    locs = client.get("/api/lookups/locations?wh=ENT-01").get_json()
    assert locs and all(r["label"].startswith("ENT-01") for r in locs)
    mv(client, dQty="3")
    from sqlalchemy import text

    from powererp import database

    with database.engine.connect() as con:
        rows = con.execute(text("SELECT product, qty FROM stock_movements ORDER BY no DESC LIMIT 1")).all()
    assert rows[0][0] == "CLAV-SF" and float(rows[0][1]) == 3


def test_reset_and_clear(client):
    mv(client, dQty="3")
    client.post("/api/clear")
    assert client.get("/api/products").get_json()["total"] == 0
    client.post("/api/reset")
    assert stock(client, "CLAV-SF") == 12


def test_replenishment_in_purchase_units(client):
    """TUBE-T8 is bought by the case of 25 at 312.50: the PO line is in tubes at 12.50."""
    client.put("/api/stock-params/TUBE-T8/ENT-01", json={"dReorderPoint": "120"})
    row = next(
        r for r in client.get("/api/inventory/replenishment?size=500").get_json()["items"] if r["cProduct"] == "TUBE-T8"
    )
    assert (
        row["dPurchaseQty"] == "4"
        and row["cPurchaseUOM"] == "CS"
        and row["dSuggestedQty"] == "100"
        and row["dUnitCost"] == "312.50"
    )
    po = client.post(
        "/api/inventory/replenishment/po", json={"lines": [{"cProduct": "TUBE-T8", "dPurchaseQty": "4"}]}
    ).get_json()["purchaseOrders"][0]
    line = client.get("/api/purchase-orders/" + po["cPO"]).get_json()["lines"][0]
    assert line["dQuantity"] == "100" and line["dUnitCost"] == "12.50" and "(4 CS)" in line["cProductDesc"]
