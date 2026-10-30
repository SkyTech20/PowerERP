"""GL accounts, cost centers, suppliers, lookups and list behaviour (search, filter, sort, pages)."""


def test_gl_crud(client):
    r = client.post("/api/gl-accounts", json={"cCode": "9999", "cDesc": "Test"})
    assert r.status_code == 201
    assert client.post("/api/gl-accounts", json={"cCode": "9999", "cDesc": "Dup"}).status_code == 409
    assert client.post("/api/gl-accounts", json={"cCode": "9998"}).get_json() == {"error": "required", "field": "cDesc"}
    assert client.put("/api/gl-accounts/9999", json={"cDesc": "Changed"}).get_json()["cDesc"] == "Changed"
    assert client.delete("/api/gl-accounts/9999").status_code == 200
    assert client.get("/api/gl-accounts/9999").status_code == 404


def test_cost_center_with_and_without_cc2(client):
    assert client.post("/api/cost-centers", json={"cCC1": "T1", "cDesc": "Top"}).status_code == 201
    assert client.post("/api/cost-centers", json={"cCC1": "T1", "cCC2": "A", "cDesc": "Sub"}).status_code == 201
    assert client.post("/api/cost-centers", json={"cCC1": "T1", "cCC2": "A", "cDesc": "Dup"}).status_code == 409
    assert client.get("/api/cost-centers/T1").get_json()["cDesc"] == "Top"
    assert client.get("/api/cost-centers/T1/A").get_json()["cDesc"] == "Sub"
    assert client.delete("/api/cost-centers/T1/A").status_code == 200
    assert client.get("/api/cost-centers/T1/A").status_code == 404


def test_supplier_crud(client):
    r = client.post("/api/suppliers", json={"cCode": "NEWSUP", "cName": "New supplier", "cNoTPS": "123", "iStatutAch": "0"})
    assert r.status_code == 201
    row = r.get_json()
    assert row["iStatutAch"] == 0 and row["iTypePO"] == 1 and row["cNoTVQ"] == ""
    assert client.post("/api/suppliers", json={"cCode": "newsup", "cName": "x"}).status_code == 409
    assert client.put("/api/suppliers/NEWSUP", json={"cName": "Renamed"}).get_json()["cName"] == "Renamed"
    assert client.put("/api/suppliers/NEWSUP", json={}).status_code == 400
    assert client.delete("/api/suppliers/NEWSUP").status_code == 200


def test_invalid_body(client):
    r = client.post("/api/suppliers", data="not json", content_type="application/json")
    assert r.status_code == 400 and r.get_json()["error"] == "invalid_body"


def test_list_search_filter_sort_and_pages(client):
    page = client.get("/api/suppliers?q=lumpro").get_json()
    assert [s["cCode"] for s in page["items"]] == ["LUMPRO"]

    allp = client.get("/api/suppliers?size=2&page=1&sort=cCode").get_json()
    assert allp["size"] == 2 and len(allp["items"]) == 2 and allp["total"] > 2
    codes = [s["cCode"] for s in client.get("/api/suppliers?size=500&sort=cCode").get_json()["items"]]
    assert codes == sorted(codes, key=str.lower)
    desc = [s["cCode"] for s in client.get("/api/suppliers?size=500&sort=cCode&dir=desc").get_json()["items"]]
    assert desc == codes[::-1]

    unb = client.get("/api/purchase-orders?f_lUnbilled=true&size=500").get_json()["items"]
    assert unb and all(p["lUnbilled"] for p in unb)


def test_numeric_sort_on_amounts(client):
    rows = client.get("/api/purchase-orders?sort=dTotalAmount&size=500").get_json()["items"]
    amounts = [float(r["dTotalAmount"]) for r in rows]
    assert amounts == sorted(amounts)


def test_bad_page_values_fall_back(client):
    r = client.get("/api/suppliers?size=abc&page=x").get_json()
    assert r["size"] == 25 and r["page"] == 1


def test_lookups(client):
    assert {"code": "LUMPRO", "label": client.get("/api/suppliers/LUMPRO").get_json()["cName"]} in client.get("/api/lookups/suppliers?q=lum").get_json()
    assert any(p["code"] == "500101" for p in client.get("/api/lookups/po?q=500101").get_json())
    assert client.get("/api/lookups/unknown").status_code == 404


def test_summary(client):
    s = client.get("/api/summary").get_json()
    assert s["suppliers"] > 0 and s["purchaseOrders"] > 0 and s["receptions"] > 0


def test_reset_and_clear(client):
    client.delete("/api/suppliers/LUMPRO")
    assert client.get("/api/suppliers/LUMPRO").status_code == 404
    client.post("/api/reset")
    assert client.get("/api/suppliers/LUMPRO").status_code == 200

    client.post("/api/clear")
    s = client.get("/api/summary").get_json()
    assert s["suppliers"] == 0 and s["purchaseOrders"] == 0 and s["invoices"] == 0
