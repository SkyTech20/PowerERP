"""Inventory > Stock on hand > stock card (GET /api/inventory/stock/card): the movements of one stock line, with the
documents behind them, on the maple demo (receptions, production orders, sales invoices)."""

from tests.test_demo_maple import maple  # noqa: F401  (fixture)


def card(client, line, **extra):
    q = {
        "product": line["cProduct"],
        "warehouse": line["cWarehouse"],
        "location": line["cLocation"],
        "lot": line["cLot"],
        **extra,
    }
    return client.get("/api/inventory/stock/card", query_string=q)


def test_every_stock_line_adds_up_to_its_card(maple):  # noqa: F811
    lines = maple.get("/api/inventory/stock?size=1000").get_json()["items"]
    assert len(lines) > 10
    for line in lines:
        c = card(maple, line).get_json()
        assert c["items"], line
        assert c["dClosing"] == c["dQtyOnHand"] == line["dQtyOnHand"], line


def test_card_links_the_documents(maple):  # noqa: F811
    lines = maple.get("/api/inventory/stock?q=MAPLE-SYRUP-540&size=50").get_json()["items"]
    c = card(maple, lines[0]).get_json()
    made = c["items"][0]
    assert (made["cType"], made["cDocType"]) == ("IN", "PROD")  # made by a production order
    assert maple.get(f"/api/production-orders/{made['cDocNo']}").status_code == 200
    sales = [m for m in c["items"] if m["cDocType"] == "SO"]
    assert sales and all(m["dQtyOut"] for m in sales)
    for m in sales:  # the invoice number of the movement leads to the invoice
        inv = maple.get(f"/api/sales-invoices/{m['iDocId']}").get_json()
        assert inv["cInvoiceNo"] == m["cDocNo"] and inv["cCustomer"] == m["cReason"]

    barrel = maple.get("/api/inventory/stock?q=SYRUP-BULK-AMB&size=50").get_json()["items"][0]
    rec = card(maple, barrel).get_json()["items"][0]
    assert (rec["cType"], rec["cDocType"]) == ("IN", "REC")
    assert maple.get(f"/api/receptions/{rec['cDocNo']}").status_code == 200


def test_card_period_and_errors(maple):  # noqa: F811
    line = maple.get("/api/inventory/stock?q=MAPLE-SYRUP-540&size=50").get_json()["items"][0]
    full = card(maple, line).get_json()["items"]
    cut = full[1]["dDate"]
    part = card(maple, line, **{"from": cut}).get_json()
    assert part["dOpening"] == full[0]["dBalance"] and part["items"][0]["iNo"] == full[1]["iNo"]
    assert card(maple, {**line, "cProduct": "NOPE"}).status_code == 404


def test_card_needs_the_stock_screen(anon):
    assert anon.get("/api/inventory/stock/card?product=X&warehouse=Y").status_code == 401
