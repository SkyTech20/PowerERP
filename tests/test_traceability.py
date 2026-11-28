"""Traceability of a lot (step 3): one step back to the supplier, one step forward to the orders, the lots made and
the customers; the recall (lots reached, customers, stock on hand, open orders) and the spreadsheet export."""

import io

import pytest
from conftest import new_reception

URL = "/api/production-orders"
DAY = "2026-12-01"


def _move(client, prod, loc, lot, exp, qty, cost):
    body = {"cType": "IN", "cProduct": prod, "dQty": qty, "cWarehouse": "ENT-01", "cLocation": loc}
    body.update({"cLot": lot, "dExpiry": exp, "dUnitCost": cost, "dDate": "2026-11-20"})
    r = client.post("/api/stock-movements", json=body)
    assert r.status_code == 201, r.get_json()


@pytest.fixture
def made(client):
    """Flour received from a supplier (lot F-REC, supplier lot SUP-1), bread made with it (MO1), 50 sold, 5 back."""
    line = {"CodeArticle": "FARINE-T55", "Description": "Farine", "QuantiteCommandee": "200", "QuantiteRecue": "200"}
    line.update({"PrixUnitaire": "0.85", "cLot": "F-REC", "cSupplierLot": "SUP-1", "dExpiry": "2027-02-01"})
    r = new_reception(client, no="990301", Entrepot="ENT-01", lines=[line])
    assert r.status_code == 201, r.get_json()
    assert client.post("/api/receptions/990301/post").status_code == 200
    _move(client, "LEVURE", "A-01-01-B", "LV1", "2027-01-31", "10", "6.00")
    _move(client, "SEL-FIN", "A-01-02-A", "S1", "", "10", "1.00")
    _move(client, "SAC-PAIN", "A-01-01-A", "", "", "1000", "0.05")
    o = client.post(URL, json={"cProduct": "PAIN-BL-675", "dQty": "400", "dStart": DAY}).get_json()
    no = o["iNo"]
    assert client.post(f"{URL}/{no}/release", json={}).status_code == 200
    r = client.post(f"{URL}/{no}/issue", json={"dDate": DAY})
    assert r.status_code == 200, r.get_json()
    r = client.post(f"{URL}/{no}/report", json={"dQty": "200", "dDate": DAY})
    assert r.status_code == 200, r.get_json()
    inv = client.post(
        "/api/sales-invoices",
        json={
            "cCustomer": "HOTEL-LAURIER",
            "dDate": "2026-12-02",
            "lines": [{"cProduct": "PAIN-BL-675", "dQty": "50"}],
        },
    ).get_json()
    r = client.post(f"/api/sales-invoices/{inv['iNo']}/post")
    assert r.status_code == 200, r.get_json()
    cn = client.post(f"/api/sales-invoices/{inv['iNo']}/credit").get_json()
    lines = [{"iOrigLine": 1, "cProduct": "PAIN-BL-675", "dQty": "5", "lReturn": True}]
    client.put(f"/api/sales-invoices/{cn['iNo']}", json={"lines": lines})
    r = client.post(f"/api/sales-invoices/{cn['iNo']}/post")
    assert r.status_code == 200, r.get_json()
    return no


def test_forward_from_the_supplier_lot_reaches_the_customers(client, made):
    r = client.get("/api/traceability?product=farine-t55&lot=f-rec")
    assert r.status_code == 200, r.get_json()
    t = r.get_json()
    assert (t["cProduct"], t["cLot"], t["cUOM"]) == ("FARINE-T55", "F-REC", "KG")
    [src] = t["origin"]["sources"]
    assert src["cKind"] == "reception" and src["cDocNo"] == "990301"
    assert (src["cSupplier"], src["cSupplierLot"], src["cPO"]) == ("PAPCEN", "SUP-1", "500301")
    [use] = t["uses"]["orders"]
    assert use["iOrder"] == made and use["cStatus"] == "in_progress"
    assert [(o["cProduct"], o["cLot"], float(o["dQtyMade"])) for o in use["outputs"]] == [("PAIN-BL-675", "MO1", 200)]
    rc = t["recall"]
    assert [(n["cProduct"], n["cLot"]) for n in rc["lots"]] == [("FARINE-T55", "F-REC"), ("PAIN-BL-675", "MO1")]
    assert [(c["cCustomer"], c["cType"], float(c["dQty"])) for c in rc["customers"]] == [
        ("HOTEL-LAURIER", "invoice", 50),
        ("HOTEL-LAURIER", "credit", -5),
    ]
    assert rc["customers"][0]["cInvoiceNo"] == "1" and rc["iCustomers"] == 1
    bread = [s for s in rc["stock"] if s["cProduct"] == "PAIN-BL-675"]
    assert sum(float(s["dQty"]) for s in bread) == 155
    assert [o["iOrder"] for o in rc["orders"]] == [made]  # still in progress
    kinds = [(m["cType"], m["cDocType"]) for m in t["movements"]]
    assert kinds[0] == ("IN", "REC") and ("OUT", "PROD") in kinds


def test_back_from_the_lot_made_reaches_the_supplier(client, made):
    t = client.get("/api/traceability?product=PAIN-BL-675&lot=MO1").get_json()
    [src] = t["origin"]["sources"]
    assert (src["cKind"], src["iOrder"], float(src["dQty"])) == ("production", made, 200)
    inputs = {(i["cProduct"], i["cLot"]): i for i in t["origin"]["inputs"]}
    assert set(inputs) >= {("FARINE-T55", "F-REC"), ("LEVURE", "LV1"), ("SEL-FIN", "S1")}
    flour = inputs[("FARINE-T55", "F-REC")]
    assert flour["iOrder"] == made and float(flour["dQtyUsed"]) > 0
    assert flour["sources"][0]["cSupplierLot"] == "SUP-1"
    assert [s["cKind"] for s in inputs[("LEVURE", "LV1")]["sources"]] == ["other"]  # a manual entry
    assert t["uses"]["orders"] == []
    assert [c["cType"] for c in t["recall"]["customers"]] == ["invoice", "credit"]
    # the movements of the lot: in from production, out to the invoice, back from the credit note
    assert [(m["cType"], m["cDocType"]) for m in t["movements"]] == [("IN", "PROD"), ("OUT", "SO"), ("ADJ", "SO")]


def test_lookups_and_unknown_lot(client, made):
    products = {r["code"] for r in client.get("/api/lookups/traced_products?all=1").get_json()}
    assert {"FARINE-T55", "PAIN-BL-675", "LEVURE"} <= products and "SAC-PAIN" not in products
    lots = client.get("/api/lookups/trace_lots?product=PAIN-BL-675").get_json()
    assert [(r["code"], r["label"]) for r in lots] == [("MO1", "2026-12-08 · 155")]
    r = client.get("/api/traceability?product=PAIN-BL-675&lot=NOPE")
    assert r.status_code == 404 and r.get_json()["error"] == "unknown_lot"
    assert client.get("/api/traceability?product=PAIN-BL-675").status_code == 404


def test_export_is_a_spreadsheet(client, made):
    from openpyxl import load_workbook

    r = client.get("/api/traceability/export?product=FARINE-T55&lot=F-REC&lang=fr")
    assert r.status_code == 200
    assert r.mimetype == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    assert 'filename="trace-FARINE-T55-F-REC.xlsx"' in r.headers["Content-Disposition"]
    wb = load_workbook(io.BytesIO(r.data))
    assert wb.sheetnames == ["Résumé", "Origine", "Utilisations", "Clients", "Stock", "Mouvements"]
    summary = {row[0]: row[1] for row in wb["Résumé"].iter_rows(min_row=2, values_only=True)}
    assert summary["Lot"] == "F-REC" and summary["Clients touchés"] == 1
    origin = list(wb["Origine"].iter_rows(min_row=2, values_only=True))
    assert origin[0][5:10] == ("Réception", "990301", "2026-10-02", "PAPCEN Papeterie Centrale inc.", "SUP-1")
    [use] = list(wb["Utilisations"].iter_rows(min_row=2, values_only=True))
    assert (use[4], use[7], use[8]) == ("En cours", "MO1", 200)
    moves = list(wb["Mouvements"].iter_rows(min_row=2, values_only=True))
    assert moves[0][2:5] == ("Entrée", "Réception", "990301")
    customers = list(wb["Clients"].iter_rows(min_row=2, values_only=True))
    assert [(c[2], c[8]) for c in customers] == [("Facture", 50), ("Note de crédit", -5)]
    en = client.get("/api/traceability/export?product=FARINE-T55&lot=F-REC")
    assert load_workbook(io.BytesIO(en.data)).sheetnames[0] == "Summary"
    assert client.get("/api/traceability/export?product=FARINE-T55&lot=X").status_code == 404


def test_export_has_the_company_logo_above_the_summary(client, made):
    from openpyxl import load_workbook

    from tests.test_company_logo import data_url

    assert client.put("/api/admin/company/logo", json={"cLogo": data_url(size=(600, 150))}).status_code == 200
    r = client.get("/api/traceability/export?product=FARINE-T55&lot=F-REC&lang=en")
    wb = load_workbook(io.BytesIO(r.data))
    ws = wb["Summary"]
    assert len(ws._images) == 1 and len(wb["Origin"]._images) == 0
    rows = list(ws.iter_rows(values_only=True))
    top = next(i for i, row in enumerate(rows) if row[0] == "Field")  # the table starts under the logo
    assert top >= 2 and all(v is None for row in rows[:top] for v in row)
    assert {row[0]: row[1] for row in rows[top + 1 :]}["Lot"] == "F-REC"
    assert ws.freeze_panes == f"A{top + 2}"
