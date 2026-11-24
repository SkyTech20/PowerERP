"""Sales API (V3): draft invoices priced for the customer, with the taxes of the place of delivery."""

DAY = "2026-11-23"
DEMO = 3  # draft invoices of the demo data (data/sales.json)


def new(client, **over):
    body = {
        "cCustomer": "hotel-laurier",
        "dDate": DAY,
        "lines": [{"cProduct": "tube-t8", "dQty": "10"}, {"cProduct": ""}],
        **over,
    }
    r = client.post("/api/sales-invoices", json=body)
    assert r.status_code == 201, r.get_json()
    return r.get_json()


def test_create_with_the_customer_defaults_and_prices(client):
    inv = new(client)
    assert inv["iNo"] == DEMO + 1 and inv["cStatus"] == "draft" and inv["cInvoiceNo"] == ""
    assert (inv["cCustomer"], inv["cCustomerName"], inv["cShipTo"]) == (
        "HOTEL-LAURIER",
        "Hôtel Laurier Gatineau",
        "HOTEL",
    )
    assert (inv["cWarehouse"], inv["cLang"], inv["cTermCode"], inv["cTaxGroup"]) == ("ENT-01", "fr", "n30", "QC")
    [ln] = inv["lines"]  # the empty line is dropped
    assert (ln["cUOM"], ln["dPrice"], ln["cPriceSource"], ln["dDiscountPct"]) == ("UN", "15.75", "price_list", "3")
    assert (ln["dNetPrice"], ln["dAmount"], ln["cTaxGroup"]) == ("15.2775", "152.78", "QC")
    assert ln["cDescription"].startswith("Tube DEL")  # in the customer's language
    # 152.78 x 5 % = 7.64 (TPS); x 9.975 % = 15.24 (TVQ)
    assert [(t["cTaxCode"], t["dBase"], t["dTax"]) for t in inv["taxes"]] == [
        ("TPS", "152.78", "7.64"),
        ("TVQ", "152.78", "15.24"),
    ]
    assert (inv["dSubTotal"], inv["dDiscountTotal"], inv["dTaxTotal"], inv["dTotal"]) == (
        "152.78",
        "4.72",
        "22.88",
        "175.66",
    )
    assert client.get(f"/api/sales-invoices/{DEMO + 1}").get_json() == inv
    assert new(client)["iNo"] == DEMO + 2


def test_taxes_follow_the_place_of_delivery_and_the_product(client):
    inv = new(client, cShipTo="ottawa", lines=[{"cProduct": "TUBE-T8", "dQty": "1"}])
    assert inv["cTaxGroup"] == "ON" and [t["cTaxCode"] for t in inv["taxes"]] == ["TVH-ON"]
    bread = [{"cProduct": "PAIN-BL-675", "dQty": "20"}, {"cProduct": "TUBE-T8", "dQty": "1"}]
    inv = new(client, lines=bread)
    assert [ln["cTaxGroup"] for ln in inv["lines"]] == ["ZERO", "QC"]  # bread: zero-rated
    assert {t["cTaxGroup"] for t in inv["taxes"]} == {"QC"} and inv["taxes"][0]["dBase"] == "15.28"
    inv = new(client, cCustomer="CPE-SOLEIL", lines=[{"cProduct": "TUBE-T8", "dQty": "1"}])
    assert inv["cTaxGroup"] == "EXO" and inv["taxes"] == [] and inv["dTotal"] == inv["dSubTotal"]


def test_typed_price_and_discount_are_kept(client):
    inv = new(client, lines=[{"cProduct": "TUBE-T8", "dQty": "2", "dPrice": "16", "dDiscountPct": "0"}])
    ln = inv["lines"][0]
    assert (ln["dPrice"], ln["cPriceSource"], ln["dDiscountPct"], ln["dAmount"]) == ("16.00", "manual", "0", "32.00")
    r = client.put(f"/api/sales-invoices/{inv['iNo']}", json={"lines": [{"cProduct": "TUBE-T8", "dQty": "60"}]})
    ln = r.get_json()["lines"][0]
    assert (ln["dPrice"], ln["cPriceSource"]) == ("13.95", "price_list")  # quantity break from 50


def test_rules(client):
    def err(**over):
        body = {"cCustomer": "HOTEL-LAURIER", "lines": [{"cProduct": "TUBE-T8", "dQty": "1"}], **over}
        r = client.post("/api/sales-invoices", json=body)
        assert r.status_code == 400, r.get_json()
        return r.get_json()["error"], r.get_json()["field"]

    assert err(cCustomer="") == ("required", "cCustomer")
    assert err(cCustomer="NOPE") == ("unknown_ref", "cCustomer")
    assert err(cShipTo="NOPE") == ("unknown_ref", "cShipTo")
    assert err(cWarehouse="NOPE") == ("unknown_ref", "cWarehouse")
    assert err(cLang="pt") == ("invalid_choice", "cLang")
    assert err(lines=[{"cProduct": "NOPE", "dQty": "1"}]) == ("unknown_ref", "lines")
    assert err(lines=[{"cProduct": "TUBE-T8"}]) == ("positive", "lines")
    assert err(lines=[{"cProduct": "TUBE-T8", "dQty": "1", "cUOM": "KG"}]) == ("no_conversion", "lines")
    assert err(lines=[{"cProduct": "TUBE-T8", "dQty": "1", "dDiscountPct": "150"}]) == ("out_of_range", "lines")
    client.put("/api/products/TUBE-T8", json={"dMinPrice": "15.50"})
    r = client.post(
        "/api/sales-invoices", json={"cCustomer": "HOTEL-LAURIER", "lines": [{"cProduct": "TUBE-T8", "dQty": "1"}]}
    )
    assert r.get_json()["error"] == "below_min_price" and "line 1" in r.get_json()["detail"]
    client.put("/api/products/TUBE-T8", json={"lSellable": False})
    assert err() == ("not_sellable", "lines")
    client.put("/api/customers/HOTEL-LAURIER", json={"lActive": False})
    assert err() == ("inactive", "cCustomer")


def test_calc_without_saving(client):
    r = client.post(
        "/api/sales-invoices/calc", json={"cCustomer": "MAPLE-FOODS", "lines": [{"cProduct": "DOCK-USBC", "dQty": "1"}]}
    )
    inv = r.get_json()
    assert inv["iNo"] == 0 and inv["cLang"] == "en" and inv["lines"][0]["dNetPrice"] == "239.04"
    assert inv["lines"][0]["cDescription"] == client.get("/api/products/DOCK-USBC").get_json()["cDescEN"]
    assert client.get("/api/sales-invoices").get_json()["total"] == DEMO
    saved = new(client)
    r = client.post(f"/api/sales-invoices/{saved['iNo']}/calc", json={"lines": [{"cProduct": "TUBE-T8", "dQty": "50"}]})
    assert r.get_json()["lines"][0]["dPrice"] == "13.95"
    assert client.get(f"/api/sales-invoices/{saved['iNo']}").get_json()["lines"][0]["dQty"] == "10"


def test_list_delete_and_references(client):
    inv = new(client)
    page = client.get("/api/sales-invoices?q=laurier&sort=iNo&dir=desc").get_json()
    assert page["total"] == 2 and page["items"][0]["iLines"] == 1 and "lines" not in page["items"][0]
    assert client.delete("/api/customers/HOTEL-LAURIER").status_code == 409  # used by an invoice
    assert client.delete(f"/api/sales-invoices/{inv['iNo']}").status_code == 200
    assert client.get(f"/api/sales-invoices/{inv['iNo']}").status_code == 404
    assert client.delete("/api/sales-invoices/1").status_code == 200  # the demo's draft for the same customer
    assert client.delete("/api/customers/HOTEL-LAURIER").status_code == 200


def test_reset_restarts_the_numbering(client):
    new(client)
    new(client)
    client.post("/api/reset")
    assert client.get("/api/sales-invoices").get_json()["total"] == DEMO
    assert new(client)["iNo"] == DEMO + 1


def test_the_demo_drafts_can_be_posted(client):
    for no in range(1, DEMO + 1):
        assert client.post(f"/api/sales-invoices/{no}/check").get_json()["ok"], no
    assert client.post("/api/sales-invoices/1/post").get_json()["cInvoiceNo"] == "1"


def test_a_line_offers_only_the_units_of_its_product(client):
    def units(product):
        return [r["code"] for r in client.get(f"/api/lookups/product_uoms?product={product}").get_json()]

    assert units("TUBE-T8") == ["UN"]  # sold by the unit: no litre, no kilogram
    assert units("") == []
    prod = client.get("/api/products/TUBE-T8").get_json()
    prod["conversions"] = [{"cUOM": "CS", "dFactor": "12", "cNotes": ""}]
    assert client.put("/api/products/TUBE-T8", json=prod).status_code == 200
    assert units("TUBE-T8") == ["UN", "CS"]  # its own packaging too
    flour = units(
        next(p["cCode"] for p in client.get("/api/products?size=500").get_json()["items"] if p["cStockUOM"] == "KG")
    )
    assert (
        flour[0] == "KG" and {"G", "LB"} <= set(flour) and "L" not in flour
    )  # the general conversions of the kilogram
