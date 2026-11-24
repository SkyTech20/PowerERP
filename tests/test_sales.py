"""Sales API (V1): customers with their ship-to addresses and contacts, and the company profile."""

NEW = {
    "cCode": "resto-1",
    "cName": "Resto Un",
    "cTaxGroup": "qc",
    "addresses": [
        {"cCode": "main", "cAddress1": "1, rue A", "cCity": "Montréal", "cProvince": "qc"},
        {"cCode": "ott", "cAddress1": "2 B St", "cCity": "Ottawa", "cProvince": "on", "cTaxGroup": "on"},
        {"cCode": ""},
    ],
    "contacts": [{"cName": "Paie", "cEmail": "ap@resto.example", "lInvoices": True}, {"cName": ""}],
}


def test_demo_customers(client):
    page = client.get("/api/customers?sort=cCode").get_json()
    assert page["total"] == 5
    c = client.get("/api/customers/HOTEL-LAURIER").get_json()
    assert c["cLang"] == "fr" and c["cTaxGroup"] == "QC" and c["dDiscountPct"] == "3"
    assert [a["cCode"] for a in c["addresses"]] == ["HOTEL", "OTTAWA"] and c["addresses"][0]["lDefault"] is True
    assert c["addresses"][1]["cTaxGroup"] == "ON"  # delivered in Ontario: HST
    assert "addresses" not in page["items"][0] and page["items"][0]["iAddresses"] >= 0


def test_crud(client):
    r = client.post("/api/customers", json=NEW)
    assert r.status_code == 201, r.get_json()
    row = r.get_json()
    assert (row["cCode"], row["cTaxGroup"], row["cLang"], row["lActive"]) == ("RESTO-1", "QC", "fr", True)
    assert [a["cCode"] for a in row["addresses"]] == ["MAIN", "OTT"]  # the empty line is dropped
    assert row["addresses"][0]["lDefault"] and row["addresses"][0]["cName"] == "Resto Un"
    assert row["addresses"][1]["cTaxGroup"] == "ON" and row["addresses"][1]["cProvince"] == "ON"
    assert len(row["contacts"]) == 1
    assert client.post("/api/customers", json=NEW).status_code == 409
    r = client.put("/api/customers/RESTO-1", json={"cLang": "en", "dDiscountPct": "7.5", "lActive": False})
    assert (r.get_json()["cLang"], r.get_json()["dDiscountPct"], r.get_json()["lActive"]) == ("en", "7.5", False)
    assert "RESTO-1" not in {x["code"] for x in client.get("/api/lookups/customers").get_json()}
    assert client.delete("/api/customers/RESTO-1").status_code == 200
    assert client.get("/api/customers/RESTO-1").status_code == 404


def test_rules(client):
    def err(**over):
        r = client.post("/api/customers", json={**NEW, **over})
        assert r.status_code == 400, r.get_json()
        return r.get_json()["error"], r.get_json()["field"]

    assert err(cName="") == ("required", "cName")
    assert err(cTaxGroup="XX") == ("unknown_ref", "cTaxGroup")
    assert err(cWarehouse="NOPE") == ("unknown_ref", "cWarehouse")
    assert err(cLang="pt") == ("invalid_choice", "cLang")
    assert err(dDiscountPct="120") == ("out_of_range", "dDiscountPct")
    assert err(cEmail="not-an-email") == ("invalid_email", "cEmail")
    assert err(addresses=[{"cCode": "A", "cAddress1": "x"}, {"cCode": "a", "cAddress1": "y"}]) == (
        "duplicate",
        "addresses",
    )
    assert err(addresses=[{"cCode": "A", "cCity": "x"}]) == ("required", "addresses")
    assert err(addresses=[{"cCode": "A", "cAddress1": "x", "cTaxGroup": "XX"}]) == ("unknown_ref", "addresses")
    two = [{"cCode": c, "cAddress1": "x", "lDefault": True} for c in ("A", "B")]
    assert err(addresses=two) == ("one_default", "addresses")
    assert err(contacts=[{"cName": "X", "lInvoices": True}]) == ("required", "contacts")
    assert err(contacts=[{"cName": "X", "cEmail": "x@"}]) == ("invalid_email", "contacts")


def test_a_tax_group_used_by_a_customer_cannot_be_deleted(client):
    client.post("/api/tax-groups", json={"cCode": "NB", "cDescFR": "Nouveau-Brunswick", "lines": []})
    assert client.post("/api/customers", json={**NEW, "cTaxGroup": "NB", "addresses": []}).status_code == 201
    assert client.delete("/api/tax-groups/NB").status_code == 409
    client.delete("/api/customers/RESTO-1")
    body = {**NEW, "addresses": [{"cCode": "A", "cAddress1": "x", "cTaxGroup": "NB"}]}
    assert client.post("/api/customers", json=body).status_code == 201  # used by a ship-to address
    assert client.delete("/api/tax-groups/NB").status_code == 409


def test_lookups(client):
    names = {x["code"]: x["label"] for x in client.get("/api/lookups/customers").get_json()}
    assert names["MAPLE-FOODS"] == "Maple Foods Distribution Ltd."
    terms = {x["code"]: x["label"] for x in client.get("/api/lookups/customer_terms").get_json()}
    assert terms["n15"] == "net 15 jours" and "n45" in terms


def test_company_profile(app, admin):
    me = admin.get("/api/company").get_json()
    assert me["cName"] == "Industries Démo PowerERP" and me["cNEQ"]
    # the GST / HST and QST numbers come from the tax codes, once per number
    assert [(t["cTaxCode"], t["cRegistrationNo"]) for t in me["taxNumbers"]] == [
        ("TPS", "123456789 RT0001"),
        ("TVQ", "1234567890 TQ0001"),
    ]
    r = admin.put("/api/admin/company", json={"cName": "Nouvelle", "cProvince": "qc", "cCode": "X"})
    assert r.status_code == 200 and r.get_json()["cName"] == "Nouvelle" and r.get_json()["cCode"] == "MAIN"
    assert r.get_json()["cProvince"] == "QC" and r.get_json()["cCity"] == "Montréal"  # the rest is kept
    assert admin.put("/api/admin/company", json={"cName": ""}).get_json()["field"] == "cName"
    assert admin.put("/api/admin/company", json={"cEmail": "x"}).get_json()["error"] == "invalid_email"

    admin.post("/api/users", json={"username": "sam", "name": "Sam", "password": "secret1", "role": "user"})
    c = app.test_client()
    assert c.post("/api/auth/login", json={"username": "sam", "password": "secret1"}).status_code == 200
    assert c.get("/api/company").status_code == 200  # every user reads it (the invoices print it)
    assert c.put("/api/admin/company", json={"cName": "Hack"}).status_code == 403


def test_company_profile_after_clear(admin):
    admin.post("/api/clear")
    me = admin.get("/api/company").get_json()
    assert me["cName"] == "" and me["cProvince"] == "QC" and me["taxNumbers"] == []
    assert admin.put("/api/admin/company", json={"cName": "Neuve"}).get_json()["cName"] == "Neuve"


def test_pastry_shop_customers(admin):
    try:
        admin.post("/api/reset", json={"scenario": "pastry"})
        codes = {c["cCode"] for c in admin.get("/api/customers").get_json()["items"]}
        assert codes == {"CAFE-PLATEAU", "TRAITEUR-ROYAL", "UNI-CAFE", "OTTAWA-DELI"}
        assert admin.get("/api/company").get_json()["cName"] == "Pâtisserie Démo"
    finally:
        admin.post("/api/reset", json={"scenario": "manufacturing"})
