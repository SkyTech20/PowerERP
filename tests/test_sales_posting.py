"""Sales API (V4): posting an invoice: checked first, the stock goes out (pick policy per product), the number."""

DAY = "2026-11-23"


def draft(client, lines, **over):
    body = {"cCustomer": "HOTEL-LAURIER", "dDate": DAY, "lines": lines, **over}
    r = client.post("/api/sales-invoices", json=body)
    assert r.status_code == 201, r.get_json()
    return r.get_json()["iNo"]


def on_hand(client, product):
    rows = client.get(f"/api/inventory/stock?q={product}&size=100").get_json()["items"]
    return {(r["cLocation"], r["cLot"], r["cSerial"]): float(r["dQtyOnHand"]) for r in rows if r["cProduct"] == product}


def receive(client, product, qty, lot, expiry, date=DAY, location="B-01-02-A"):
    m = {"cType": "IN", "cProduct": product, "dQty": qty, "cWarehouse": "ENT-01", "cLocation": location}
    m.update({"cLot": lot, "dExpiry": expiry, "dDate": date, "dUnitCost": "40"})
    r = client.post("/api/stock-movements", json=m)
    assert r.status_code == 201, r.get_json()


def taken(client, no):
    r = client.post(f"/api/sales-invoices/{no}/check")
    assert r.status_code == 200, r.get_json()
    return [(a["cLot"] or a["cSerial"], a["dQty"]) for a in r.get_json()["allocations"]]


def test_post_takes_the_stock_out_and_numbers_the_invoice(client):
    before = on_hand(client, "TUBE-T8")[("B-01-02-A", "", "")]
    no = draft(client, [{"cProduct": "TUBE-T8", "dQty": "10"}])
    check = client.post(f"/api/sales-invoices/{no}/check").get_json()
    assert check["ok"] and check["problems"] == [] and len(check["allocations"]) == 1
    assert client.get(f"/api/sales-invoices/{no}").get_json()["cStatus"] == "draft"  # a check changes nothing

    r = client.post(f"/api/sales-invoices/{no}/post")
    assert r.status_code == 200, r.get_json()
    inv = r.get_json()
    assert (inv["cStatus"], inv["cInvoiceNo"], inv["cPostedBy"]) == ("posted", "1", "api")
    [a] = inv["allocations"]
    assert (a["iLine"], a["cLocation"], a["dQty"], a["cUOM"]) == (1, "B-01-02-A", "10", "UN")
    assert float(inv["dCost"]) > 0 and inv["dCost"] == a["dValue"]
    assert on_hand(client, "TUBE-T8")[("B-01-02-A", "", "")] == before - 10
    m = client.get(f"/api/stock-movements/{a['iMovement']}").get_json()
    assert (m["cType"], m["cDocType"], m["cDocNo"], m["dQty"]) == ("OUT", "SO", "1", "10")

    # posted: no more changes
    assert client.put(f"/api/sales-invoices/{no}", json={"cNotes": "x"}).status_code == 409
    assert client.delete(f"/api/sales-invoices/{no}").status_code == 409
    assert client.post(f"/api/sales-invoices/{no}/post").status_code == 409
    assert client.get(f"/api/sales-invoices/{no}").get_json() == inv
    no2 = draft(client, [{"cProduct": "TUBE-T8", "dQty": "1"}])
    assert client.post(f"/api/sales-invoices/{no2}/post").get_json()["cInvoiceNo"] == "2"


def test_invoice_numbers_start_at_the_company_setting(client, admin):
    admin.put("/api/admin/company", json={"iInvoiceStart": 1001})
    no = draft(client, [{"cProduct": "TUBE-T8", "dQty": "1"}])
    assert client.post(f"/api/sales-invoices/{no}/post").get_json()["cInvoiceNo"] == "1001"
    no = draft(client, [{"cProduct": "TUBE-T8", "dQty": "1"}])
    assert client.post(f"/api/sales-invoices/{no}/post").get_json()["cInvoiceNo"] == "1002"
    client.post("/api/reset")
    no = draft(client, [{"cProduct": "TUBE-T8", "dQty": "1"}])
    assert client.post(f"/api/sales-invoices/{no}/post").get_json()["cInvoiceNo"] == "1"


def test_nothing_moves_while_a_problem_is_left(client):
    before = on_hand(client, "TUBE-T8")
    no = draft(client, [{"cProduct": "TUBE-T8", "dQty": "1"}, {"cProduct": "TUBE-T8", "dQty": "500"}])
    check = client.post(f"/api/sales-invoices/{no}/check").get_json()
    assert not check["ok"]
    [p] = check["problems"]
    assert (p["iLine"], p["cProduct"], p["code"]) == (2, "TUBE-T8", "insufficient_stock")
    r = client.post(f"/api/sales-invoices/{no}/post")
    assert r.status_code == 400 and r.get_json()["error"] == "insufficient_stock"
    assert "line 2" in r.get_json()["detail"]
    assert on_hand(client, "TUBE-T8") == before
    assert client.get(f"/api/sales-invoices/{no}").get_json()["cStatus"] == "draft"
    # the checks of the draft come back too (here: the customer was deactivated since)
    client.put("/api/customers/HOTEL-LAURIER", json={"lActive": False})
    p = client.post(f"/api/sales-invoices/{no}/check").get_json()["problems"][0]
    assert (p["code"], p["field"]) == ("inactive", "cCustomer")


def test_serial_numbers_go_out_one_by_one(client):
    no = draft(client, [{"cProduct": "LAP-14I7", "dQty": "2"}])
    assert taken(client, no) == [("PF4K2A01", "1"), ("PF4K2A02", "1")]
    inv = client.post(f"/api/sales-invoices/{no}/post").get_json()
    assert [a["cSerial"] for a in inv["allocations"]] == ["PF4K2A01", "PF4K2A02"]
    assert set(on_hand(client, "LAP-14I7")) == {("A-01-01-A", "", "PF4K2A03")}


def test_pick_policy_of_the_product(client):
    # in stock: L2026-09 (5, expires 2032-09-30, received first); received now: L2027-03, expiring earlier
    # (one lot of a product per location: each lot in its own location)
    receive(client, "EXT-5LB", "2", "L2027-03", "2031-03-31", location="A-01-01-B")
    receive(client, "EXT-5LB", "4", "L-OLD", "2026-01-31", location="A-01-02-A")  # expired: never sold
    no = draft(client, [{"cProduct": "EXT-5LB", "dQty": "3"}])
    # empty policy + expiry date = FEFO
    assert taken(client, no) == [("L2027-03", "2"), ("L2026-09", "1")]
    client.put("/api/products/EXT-5LB", json={"cPickPolicy": "FIFO"})
    assert taken(client, no) == [("L2026-09", "3")]
    client.put("/api/products/EXT-5LB", json={"cPickPolicy": "LIFO"})
    assert taken(client, no) == [("L2027-03", "2"), ("L2026-09", "1")]
    no = draft(client, [{"cProduct": "EXT-5LB", "dQty": "8"}])  # 7 sellable, 4 more expired
    p = client.post(f"/api/sales-invoices/{no}/check").get_json()["problems"][0]
    assert p["code"] == "insufficient_stock" and "> 7 UN" in p["detail"]
