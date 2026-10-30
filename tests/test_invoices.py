"""ERP invoices: totals, duplicates, and how an invoice bills receptions and POs."""


def _inv(**over):
    body = {"cNoFourn": "TECBUR", "cNoFacture": "T-1", "dDateFacture": "2026-10-05",
            "dTransport": "0", "dTotalTPS": "0", "dTotalTVP": "0",
            "lines": [{"cCodeProduit": "A", "dQuantite": "2", "dCoutUnitaire": "10"}]}
    body.update(over)
    return body


def _unbilled_recs(client):
    return {r["NoReception"] for r in client.get("/api/receptions?f_lUnbilled=true&size=500").get_json()["items"]}


def _unbilled_pos(client):
    return {p["cPO"] for p in client.get("/api/purchase-orders?f_lUnbilled=true&size=500").get_json()["items"]}


def test_invoice_totals(client):
    inv = client.post("/api/invoices", json=_inv(dTransport="1", dTotalTPS="$1.05", dTotalTVP="2,10")).get_json()
    assert inv["dSousTotal"] == "20.00" and inv["dTotalFacture"] == "24.15"
    assert inv["cStatut"] == "Draft" and inv["cDevise"] == "CAD" and inv["cSource"] == "ERP"
    assert inv["cNomFourn"]


def test_invoice_line_with_amount_only(client):
    inv = client.post("/api/invoices", json=_inv(lines=[{"cDescription": "Service", "dMontant": "$50"}])).get_json()
    assert inv["lines"][0]["dMontant"] == "50.00" and inv["lines"][0]["cCodeProduit"] == "LINE"


def test_invoice_duplicate_is_case_insensitive(client):
    assert client.post("/api/invoices", json=_inv()).status_code == 201
    assert client.post("/api/invoices", json=_inv(cNoFourn="tecbur", cNoFacture="t-1")).status_code == 409


def test_invoice_with_reception_bills_only_that_reception(client):
    assert {"700101", "700102"} <= _unbilled_recs(client)
    client.post("/api/invoices", json=_inv(cNoCommAch="500101", lines=[{"cCodeProduit": "A", "dQuantite": "1", "dCoutUnitaire": "1", "iNoReception": "700101"}]))
    recs = _unbilled_recs(client)
    assert "700101" not in recs and "700102" in recs
    assert "500101" in _unbilled_pos(client)  # 700102 is still open


def test_invoice_with_po_and_no_reception_bills_all_po_receptions(client):
    client.post("/api/invoices", json=_inv(cNoCommAch="500101"))
    recs = _unbilled_recs(client)
    assert "700101" not in recs and "700102" not in recs
    assert "500101" not in _unbilled_pos(client)


def test_update_and_delete_invoice(client):
    inv = client.post("/api/invoices", json=_inv()).get_json()
    upd = client.put(f"/api/invoices/{inv['id']}", json=_inv(cStatut="Posted", lines=[{"cCodeProduit": "A", "dQuantite": "1", "dCoutUnitaire": "5"}])).get_json()
    assert upd["cStatut"] == "Posted" and upd["dTotalFacture"] == "5.00"
    assert client.delete(f"/api/invoices/{inv['id']}").status_code == 200
    assert client.get(f"/api/invoices/{inv['id']}").status_code == 404
