"""Sales API (V2): price lists, the price list of a customer and the price of a line (/api/pricing)."""

DAY = "2026-11-23"


def price(client, customer, product, qty="1", uom="", day=DAY):
    r = client.get(f"/api/pricing?customer={customer}&product={product}&qty={qty}&uom={uom}&date={day}")
    assert r.status_code == 200, r.get_json()
    return r.get_json()


def test_demo_price_lists(client):
    page = client.get("/api/price-lists?sort=cCode").get_json()
    assert [p["cCode"] for p in page["items"]] == ["DIST", "EPICERIE-QC", "HORECA"]
    horeca = next(p for p in page["items"] if p["cCode"] == "HORECA")
    assert horeca["iCustomers"] == 3 and horeca["iProducts"] == 6 and "lines" not in horeca
    full = client.get("/api/price-lists/HORECA").get_json()
    assert full["customers"] == ["BOUL-ST-DENIS", "CPE-SOLEIL", "HOTEL-LAURIER"]
    assert client.get("/api/customers/MAPLE-FOODS").get_json()["cPriceList"] == "DIST"


def test_quantity_breaks_and_category_discount(client):
    p = price(client, "HOTEL-LAURIER", "TUBE-T8", "10")
    assert (p["cPriceList"], p["cPriceSource"], p["dPrice"], p["dListPrice"]) == (
        "HORECA",
        "price_list",
        "15.75",
        "17.50",
    )
    assert (p["dDiscountPct"], p["cDiscountSource"], p["dNetPrice"]) == ("3", "customer", "15.2775")
    p = price(client, "HOTEL-LAURIER", "TUBE-T8", "50")  # from 50: the second line
    assert (p["dPrice"], p["dMinQty"]) == ("13.95", "50")
    p = price(client, "HOTEL-LAURIER", "PAP-8511", "12")  # PAP: 5 % in the price list, before the customer's 3 %
    assert (p["dPrice"], p["dDiscountPct"], p["cDiscountSource"], p["cDiscountCategory"]) == (
        "64.90",
        "5",
        "category",
        "PAP",
    )
    assert p["dNetPrice"] == "61.655"


def test_parent_category_line_discount_and_list_price(client):
    p = price(client, "MAPLE-FOODS", "DOCK-USBC")  # INFO-ACC: the discount of its parent INFO
    assert (p["dPrice"], p["cDiscountCategory"], p["dDiscountPct"], p["dNetPrice"]) == ("249.00", "INFO", "4", "239.04")
    p = price(client, "MAPLE-FOODS", "TON-26A")  # a discount of 0 on the line: a net price
    assert (p["dPrice"], p["cDiscountSource"], p["dDiscountPct"], p["dNetPrice"]) == ("155.00", "line", "0", "155.00")
    p = price(client, "MAPLE-FOODS", "EXT-5LB")  # not in its list, no discount for SEC
    assert (p["cPriceSource"], p["dPrice"], p["cDiscountSource"], p["dNetPrice"]) == ("product", "99.00", "", "99.00")
    p = price(client, "", "EXT-5LB")  # no customer: the list price
    assert (p["cCustomer"], p["cPriceList"], p["dNetPrice"]) == ("", "", "99.00")


def test_validity_and_inactive_list(client):
    assert price(client, "MAPLE-FOODS", "MON-27Q", day="2028-01-05")["cPriceSource"] == "product"  # DIST ended
    assert price(client, "MAPLE-FOODS", "MON-27Q", day="2025-12-31")["cPriceList"] == ""
    client.put("/api/price-lists/DIST", json={"lActive": False})
    assert price(client, "MAPLE-FOODS", "MON-27Q")["dPrice"] == "429.00"


def test_units_and_minimum_price(client):
    client.put("/api/products/CLAV-SF", json={"dMinPrice": "60", "conversions": [{"cUOM": "CS", "dFactor": "10"}]})
    p = price(client, "MAPLE-FOODS", "CLAV-SF", "2", "cs")  # a case of 10 at the unit price of the list
    assert (p["cUOM"], p["dPrice"], p["dListPrice"], p["dMinPrice"]) == ("CS", "690.00", "790.00", "600.00")
    client.put("/api/customers/MAPLE-FOODS", json={"dDiscountPct": "20"})
    client.put("/api/price-lists/DIST", json={"discounts": []})
    p = price(client, "MAPLE-FOODS", "CLAV-SF")
    assert (p["dNetPrice"], p["lBelowMinPrice"]) == ("55.20", True)
    r = client.get("/api/pricing?customer=MAPLE-FOODS&product=CLAV-SF&uom=KG")
    assert r.status_code == 400 and r.get_json()["error"] == "no_conversion"


def test_pricing_errors(client):
    def err(query):
        r = client.get("/api/pricing?" + query)
        assert r.status_code == 400, r.get_json()
        return r.get_json()["error"], r.get_json()["field"]

    assert err("product=") == ("required", "product")
    assert err("product=NOPE") == ("unknown_ref", "product")
    assert err("customer=NOPE&product=CLAV-SF") == ("unknown_ref", "customer")
    assert err("product=CLAV-SF&qty=0") == ("positive", "qty")
    assert err("product=CLAV-SF&date=2026-13-45") == ("invalid_date", "date")


def test_price_list_rules(client):
    def err(**body):
        r = client.post("/api/price-lists", json={"cCode": "new", "cDescFR": "Nouvelle", **body})
        assert r.status_code == 400, r.get_json()
        return r.get_json()["error"], r.get_json()["field"]

    assert err(cDescFR="") == ("required", "cDescFR")
    assert err(dStartDate="2026-12-01", dEndDate="2026-11-01") == ("invalid_range", "dEndDate")
    assert err(lines=[{"cProduct": "NOPE", "dPrice": "1"}]) == ("unknown_ref", "lines")
    assert err(lines=[{"cProduct": "CLAV-SF"}]) == ("required", "lines")
    assert err(lines=[{"cProduct": "CLAV-SF", "dPrice": "-1"}]) == ("negative", "lines")
    assert err(lines=[{"cProduct": "CLAV-SF", "dPrice": "1", "dDiscountPct": "101"}]) == ("out_of_range", "lines")
    assert err(lines=[{"cProduct": "CLAV-SF", "dPrice": "1", "cUOM": "KG"}]) == ("no_conversion", "lines")
    two = [{"cProduct": "CLAV-SF", "dPrice": "1"}, {"cProduct": "clav-sf", "dPrice": "2", "dMinQty": "0"}]
    assert err(lines=two) == ("duplicate", "lines")
    client.put("/api/products/CLAV-SF", json={"lSellable": False})
    assert err(lines=[{"cProduct": "CLAV-SF", "dPrice": "1"}]) == ("not_sellable", "lines")
    assert err(discounts=[{"cCategory": "NOPE", "dDiscountPct": "1"}]) == ("unknown_ref", "discounts")
    assert err(discounts=[{"cCategory": "PAP"}]) == ("required", "discounts")
    assert err(discounts=[{"cCategory": "PAP", "dDiscountPct": "1"}, {"cCategory": "pap", "dDiscountPct": "2"}]) == (
        "duplicate",
        "discounts",
    )


def test_crud_and_references(client):
    body = {
        "cCode": "promo",
        "cDescFR": "Promo",
        "lines": [
            {"cProduct": "tube-t8", "dPrice": "12", "dMinQty": "100"},
            {"cProduct": "tube-t8", "dPrice": "13"},
            {},
        ],
        "discounts": [{"cCategory": "ecl", "dDiscountPct": "2"}, {"cCategory": ""}],
    }
    r = client.post("/api/price-lists", json=body)
    assert r.status_code == 201, r.get_json()
    row = r.get_json()
    assert row["cCode"] == "PROMO" and [(ln["cProduct"], ln["cUOM"], ln["dMinQty"]) for ln in row["lines"]] == [
        ("TUBE-T8", "UN", "0"),
        ("TUBE-T8", "UN", "100"),
    ]
    assert row["discounts"] == [{"cCategory": "ECL", "dDiscountPct": "2"}]
    saved = client.get("/api/price-lists/PROMO").get_json()
    assert client.put("/api/price-lists/PROMO", json=saved).status_code == 200  # what the screen sends back
    assert "PROMO" in {x["code"] for x in client.get("/api/lookups/price_lists").get_json()}
    assert client.put("/api/customers/CPE-SOLEIL", json={"cPriceList": "promo"}).get_json()["cPriceList"] == "PROMO"
    assert client.put("/api/customers/CPE-SOLEIL", json={"cPriceList": "NOPE"}).get_json()["field"] == "cPriceList"
    assert client.delete("/api/price-lists/PROMO").status_code == 409  # a customer uses it
    assert client.delete("/api/products/TUBE-T8").status_code == 409  # in a price list
    assert client.delete("/api/categories/ECL").status_code == 409  # discount of a price list
    client.put("/api/customers/CPE-SOLEIL", json={"cPriceList": ""})
    assert client.delete("/api/price-lists/PROMO").status_code == 200


def test_pastry_shop_prices(admin):
    try:
        admin.post("/api/reset", json={"scenario": "pastry"})
        p = price(admin, "TRAITEUR-ROYAL", "PASTEL-BEEF", "250")
        assert (p["cPriceList"], p["dPrice"], p["cDiscountSource"], p["dNetPrice"]) == (
            "CATERERS",
            "4.85",
            "customer",
            "4.6075",
        )
        p = price(admin, "OTTAWA-DELI", "PASTEL-CHICKEN", "24")
        assert (p["cPriceSource"], p["dNetPrice"]) == ("product", "6.00")
    finally:
        admin.post("/api/reset", json={"scenario": "manufacturing"})
