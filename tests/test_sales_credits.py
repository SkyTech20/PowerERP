"""Sales API (V6): credit notes: made from a posted invoice, at its prices, the goods back into their lots."""

DAY = "2026-11-23"


def posted(client, lines):
    r = client.post("/api/sales-invoices", json={"cCustomer": "HOTEL-LAURIER", "dDate": DAY, "lines": lines})
    no = r.get_json()["iNo"]
    r = client.post(f"/api/sales-invoices/{no}/post")
    assert r.status_code == 200, r.get_json()
    return r.get_json()


def on_hand(client, product):
    rows = client.get(f"/api/inventory/stock?q={product}&size=100").get_json()["items"]
    return {(r["cLot"] or r["cSerial"]): float(r["dQtyOnHand"]) for r in rows if r["cProduct"] == product}


def test_credit_note_from_an_invoice_brings_the_goods_back(client):
    inv = posted(client, [{"cProduct": "TUBE-T8", "dQty": "10"}, {"cProduct": "LAP-14I7", "dQty": "2"}])
    tubes, laptops = on_hand(client, "TUBE-T8")[""], on_hand(client, "LAP-14I7")
    r = client.post(f"/api/sales-invoices/{inv['iNo']}/credit")
    assert r.status_code == 201, r.get_json()
    cn = r.get_json()
    assert (cn["cType"], cn["cOrigInvoice"], cn["cStatus"], cn["cInvoiceNo"]) == ("credit", "1", "draft", "")
    assert (cn["cCustomer"], cn["cShipTo"], cn["cTaxGroup"]) == (inv["cCustomer"], inv["cShipTo"], inv["cTaxGroup"])
    assert [(ln["iOrigLine"], ln["dQty"], ln["dPrice"], ln["lReturn"]) for ln in cn["lines"]] == [
        (1, "10", "15.75", True),
        (2, "2", inv["lines"][1]["dPrice"], True),
    ]
    assert cn["dTotal"] == inv["dTotal"] and cn["taxes"] == inv["taxes"]

    # credit 3 tubes back to the stock, one laptop as a price adjustment only
    lines = [
        {"iOrigLine": 1, "cProduct": "TUBE-T8", "dQty": "3", "lReturn": True},
        {"iOrigLine": 2, "cProduct": "LAP-14I7", "dQty": "1", "dPrice": "100", "dDiscountPct": "0", "lReturn": False},
    ]
    cn = client.put(f"/api/sales-invoices/{cn['iNo']}", json={"lines": lines, "cOrigInvoice": "999"}).get_json()
    assert cn["cOrigInvoice"] == "1"  # never changed
    assert [ln["dAmount"] for ln in cn["lines"]] == ["45.83", "100.00"]
    check = client.post(f"/api/sales-invoices/{cn['iNo']}/check").get_json()
    assert check["ok"] and [(a["iLine"], a["dQty"]) for a in check["allocations"]] == [(1, "3")]

    r = client.post(f"/api/sales-invoices/{cn['iNo']}/post")
    assert r.status_code == 200, r.get_json()
    cn = r.get_json()
    assert (cn["cStatus"], cn["cInvoiceNo"]) == ("posted", "NC-1")
    [a] = cn["allocations"]
    unit = float(inv["allocations"][0]["dValue"]) / 10
    assert abs(float(a["dValue"]) - 3 * unit) < 0.01 and cn["dCost"] == a["dValue"]
    assert on_hand(client, "TUBE-T8")[""] == tubes + 3 and on_hand(client, "LAP-14I7") == laptops
    m = client.get(f"/api/stock-movements/{a['iMovement']}").get_json()
    assert (m["cType"], m["cDocType"], m["cDocNo"], m["dQty"]) == ("ADJ", "SO", "NC-1", "3")

    # the next one: only what is left; the invoice stays posted and numbered
    cn2 = client.post(f"/api/sales-invoices/{inv['iNo']}/credit").get_json()
    assert [(ln["iOrigLine"], ln["dQty"]) for ln in cn2["lines"]] == [(1, "7"), (2, "1")]
    assert client.post(f"/api/sales-invoices/{cn2['iNo']}/post").get_json()["cInvoiceNo"] == "NC-2"
    assert client.post(f"/api/sales-invoices/{inv['iNo']}/credit").get_json()["error"] == "fully_credited"
    assert client.get(f"/api/sales-invoices/{inv['iNo']}").get_json()["cInvoiceNo"] == "1"
    # one laptop credited as a price only (NC-1), the other one came back: its serial number is in stock again
    assert set(on_hand(client, "LAP-14I7")) == {"PF4K2A01", "PF4K2A03"}


def test_lots_come_back_into_their_lot(client):
    inv = posted(client, [{"cProduct": "EXT-5LB", "dQty": "2"}])
    assert on_hand(client, "EXT-5LB")["L2026-09"] == 3
    cn = client.post(f"/api/sales-invoices/{inv['iNo']}/credit").get_json()
    cn = client.post(f"/api/sales-invoices/{cn['iNo']}/post").get_json()
    assert [(a["cLot"], a["dExpiry"], a["dQty"]) for a in cn["allocations"]] == [("L2026-09", "2032-09-30", "2")]
    assert on_hand(client, "EXT-5LB")["L2026-09"] == 5


def test_credit_rules(client):
    inv = posted(client, [{"cProduct": "TUBE-T8", "dQty": "10"}])

    def err(body):
        r = client.post("/api/sales-invoices", json={"cType": "credit", "dDate": DAY, **body})
        assert r.status_code == 400, r.get_json()
        return r.get_json()["error"], r.get_json()["field"]

    assert err({"lines": []}) == ("required", "cOrigInvoice")
    assert err({"cOrigInvoice": "77"}) == ("unknown_ref", "cOrigInvoice")
    one = {"cOrigInvoice": "1"}
    assert err({**one, "lines": [{"cProduct": "DOCK-USBC", "dQty": "1"}]}) == ("not_invoiced", "lines")
    assert err({**one, "lines": [{"cProduct": "TUBE-T8", "dQty": "11"}]}) == ("over_credit", "lines")
    two = [{"cProduct": "TUBE-T8", "dQty": "6"}, {"cProduct": "TUBE-T8", "dQty": "5"}]
    assert err({**one, "lines": two}) == ("over_credit", "lines")
    # a draft invoice cannot be credited
    draft = client.post(
        "/api/sales-invoices", json={"cCustomer": "HOTEL-LAURIER", "lines": [{"cProduct": "TUBE-T8", "dQty": "1"}]}
    )
    assert client.post(f"/api/sales-invoices/{draft.get_json()['iNo']}/credit").status_code == 409
    # printed as a credit note
    cn = client.post(f"/api/sales-invoices/{inv['iNo']}/credit").get_json()
    html = client.get(f"/api/sales-invoices/{cn['iNo']}/print").get_data(as_text=True)
    assert "Note de crédit" in html and "Facture créditée</td><td><b>1</b>" in html
