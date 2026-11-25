"""Receptions into the stock: check (what goes in, what to fix), post (IN movements REC <no>), then locked."""

from conftest import new_reception

LINES = [
    # lot + expiry (shelf life 2190 days); its default location B-01-02-A holds another lot: the receiving location
    {"CodeArticle": "EXT-5LB", "QuantiteRecue": "4", "PrixUnitaire": "60.00", "cSupplierLot": "SUP-778"},
    # default location of the product in ENT-01 (replenishment parameters)
    {"CodeArticle": "MON-27Q", "QuantiteRecue": "2", "PrixUnitaire": "250.00"},
    {"CodeArticle": "INSP-EXT", "QuantiteRecue": "1", "PrixUnitaire": "40.00"},  # a service: not stocked
    {"Description": "Freight", "QuantiteRecue": "1", "PrixUnitaire": "15.00"},  # no item: skipped
]


def _rec(client, no="990201", **over):
    body = {"Entrepot": "ENT-01", "lines": LINES, **over}
    r = new_reception(client, no=no, **body)
    assert r.status_code == 201, r.get_json()
    return r.get_json()


def _stock(client, product):
    return client.get(f"/api/inventory/stock?q={product}&size=500").get_json()["items"]


def test_check_shows_what_goes_in_and_changes_nothing(client):
    _rec(client)
    before = len(client.get("/api/stock-movements?size=1").get_json()["items"])
    res = client.post("/api/receptions/990201/check").get_json()
    assert res["ok"] is True and res["problems"] == []
    by = {e["iLine"]: e for e in res["entries"]}
    assert (by[1]["cLot"], by[1]["cSupplierLot"], by[1]["cLocation"]) == ("990201-1", "SUP-778", "REC-01")
    assert by[1]["dExpiry"] == "2032-09-30"  # 2026-10-02 + 2190 days
    assert by[2]["cLocation"] == "A-01-02-A" and by[2]["cLot"] == ""
    assert by[3]["cSkip"] == "not_stocked" and by[4]["cSkip"] == "no_item"
    assert len(client.get("/api/stock-movements?size=1").get_json()["items"]) == before
    assert client.get("/api/receptions/990201").get_json()["lStockPosted"] is False


def test_post_puts_the_stock_in_and_locks_the_reception(client):
    _rec(client)
    on_hand = sum(float(x["dQtyOnHand"]) for x in _stock(client, "EXT-5LB"))
    r = client.post("/api/receptions/990201/post")
    assert r.status_code == 200, r.get_json()
    rec = r.get_json()
    assert rec["lStockPosted"] is True and rec["cStockPostedBy"] and rec["dStockPosted"]
    assert [ln["cLot"] for ln in rec["lines"]][:2] == ["990201-1", ""]
    assert rec["lines"][0]["dExpiry"] == "2032-09-30" and rec["lines"][0]["cLocation"] == "REC-01"
    moves = rec["movements"]
    assert [(m["cProduct"], m["cType"], m["cDocType"], m["cDocNo"]) for m in moves] == [
        ("EXT-5LB", "IN", "REC", "990201"),
        ("MON-27Q", "IN", "REC", "990201"),
    ]
    assert moves[0]["cLot"] == "990201-1" and float(moves[0]["dUnitCost"]) == 60
    assert "SUP-778" in moves[0]["cComment"] and moves[0]["cReason"] == "PAPCEN"
    assert sum(float(x["dQtyOnHand"]) for x in _stock(client, "EXT-5LB")) == on_hand + 4
    # the GET shows the movements too; then no more change, delete or second posting
    assert len(client.get("/api/receptions/990201").get_json()["movements"]) == 2
    upd = client.put("/api/receptions/990201", json={"NoBonCommande": "500301", "DateReception": "2026-10-02"})
    assert upd.status_code == 409 and upd.get_json()["error"] == "posted"
    assert client.delete("/api/receptions/990201").status_code == 409
    assert client.post("/api/receptions/990201/post").status_code == 409
    assert client.post("/api/receptions/990201/check").status_code == 409


def test_lot_and_expiry_typed_are_kept(client):
    lines = [
        {
            "CodeArticle": "EXT-5LB",
            "QuantiteRecue": "1",
            "PrixUnitaire": "60",
            "cLot": "L-OWN",
            "dExpiry": "2030-01-31",
            "cLocation": "EXP-01",
        }
    ]
    _rec(client, lines=lines)
    mv = client.post("/api/receptions/990201/post").get_json()["movements"][0]
    assert (mv["cLot"], mv["dExpiry"], mv["cLocation"]) == ("L-OWN", "2030-01-31", "EXP-01")


def test_problems_block_the_posting(client):
    lines = [
        {"CodeArticle": "NOPE-1", "QuantiteRecue": "1", "PrixUnitaire": "1"},
        {"CodeArticle": "LAP-14I7", "QuantiteRecue": "2", "PrixUnitaire": "900"},  # serial number required
        {"CodeArticle": "MON-27Q", "QuantiteRecue": "1", "PrixUnitaire": "1", "cLocation": "A-02-02-A"},  # blocked
    ]
    _rec(client, lines=lines)
    res = client.post("/api/receptions/990201/check").get_json()
    assert res["ok"] is False
    assert [(p["iLine"], p["code"], p["field"]) for p in res["problems"]] == [
        (1, "unknown_ref", "CodeArticle"),
        (2, "serial_required", "cSerial"),
        (3, "blocked_location", "cLocation"),
    ]
    r = client.post("/api/receptions/990201/post")
    assert r.status_code == 400 and r.get_json()["error"] == "unknown_ref"
    assert client.get("/api/receptions/990201").get_json()["lStockPosted"] is False


def test_warehouse_required_and_nothing_to_post(client):
    _rec(client, Entrepot="")
    assert [p["code"] for p in client.post("/api/receptions/990201/check").get_json()["problems"]][0] == "required"
    _rec(client, no="990202", lines=[{"Description": "Freight", "QuantiteRecue": "1", "PrixUnitaire": "5"}])
    probs = client.post("/api/receptions/990202/check").get_json()["problems"]
    assert [p["code"] for p in probs] == ["no_lines"]


def test_serial_numbers_one_line_each(client):
    lines = [
        {"CodeArticle": "LAP-14I7", "QuantiteRecue": "1", "PrixUnitaire": "900", "cSerial": "SN-A1"},
        {"CodeArticle": "LAP-14I7", "QuantiteRecue": "1", "PrixUnitaire": "900", "cSerial": "SN-A2"},
    ]
    _rec(client, lines=lines)
    moves = client.post("/api/receptions/990201/post").get_json()["movements"]
    assert [m["cSerial"] for m in moves] == ["SN-A1", "SN-A2"]


def test_currency_other_than_cad_is_a_warning(client):
    _rec(client, Devise="USD")
    res = client.post("/api/receptions/990201/check").get_json()
    assert res["ok"] is True and [w["code"] for w in res["warnings"]] == ["currency_not_cad"]
