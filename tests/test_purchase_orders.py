"""Purchase orders: creation, totals, unbilled flag, and amounts typed with "$"."""
from conftest import new_po


def test_create_po_computes_totals(client):
    r = new_po(client, dFreight="5", dGST="1.25", dPST="2.49")
    assert r.status_code == 201
    po = r.get_json()
    assert po["cSupplierName"]  # filled from the supplier code
    assert po["lines"][0]["dTotalAmount"] == "20.00"
    assert po["dSubTotal"] == "20.00"
    assert po["dTotalAmount"] == "28.74"
    assert po["lUnbilled"] is True
    assert client.get("/api/purchase-orders/990001").get_json()["dTotalAmount"] == "28.74"


def test_po_required_and_duplicate(client):
    assert client.post("/api/purchase-orders", json={"cPO": "990002"}).get_json() == {"error": "required", "field": "cSupplierCode"}
    assert new_po(client, "500101").status_code == 409


def test_empty_lines_are_dropped(client):
    po = new_po(client, lines=[{"cUnique": "1", "dQuantity": "1"}, {"cProductcode": "A", "dQuantity": "1", "dUnitCost": "3"}]).get_json()
    assert po["lineCount"] == 1 and po["dSubTotal"] == "3.00"


def test_unbilled_flag_moves_po_in_and_out_of_unbilled_list(client):
    new_po(client)
    assert client.put("/api/purchase-orders/990001", json={"cSupplierCode": "TECBUR", "lUnbilled": False, "lines": []}).get_json()["lUnbilled"] is False
    assert client.put("/api/purchase-orders/990001", json={"cSupplierCode": "TECBUR", "lUnbilled": True, "lines": []}).get_json()["lUnbilled"] is True


def test_update_and_delete_po(client):
    new_po(client)
    upd = client.put("/api/purchase-orders/990001", json={
        "cSupplierCode": "TECBUR", "lines": [{"cProductcode": "X", "dQuantity": "3", "dUnitCost": "2.5"}]}).get_json()
    assert upd["dTotalAmount"] == "7.50"
    assert client.delete("/api/purchase-orders/990001").status_code == 200
    assert client.get("/api/purchase-orders/990001").status_code == 404


def test_po_amounts_typed_with_dollar_sign(client):
    """Regression: "$" in the unit cost was saved as typed and the line total became 0."""
    po = new_po(client, dFreight="$5.00", dGST="1,25 $", dPST="$2.49", lines=[
        {"cUnique": "1", "cProductcode": "A", "dQuantity": "2", "dUnitCost": "$10.00"},
        {"cUnique": "2", "cProductcode": "B", "dQuantity": "1", "dUnitCost": "1 234,50 $"},
    ]).get_json()
    assert [l["dUnitCost"] for l in po["lines"]] == ["10.00", "1234.50"]
    assert [l["dTotalAmount"] for l in po["lines"]] == ["20.00", "1234.50"]
    assert po["dSubTotal"] == "1254.50"
    assert po["dFreight"] == "5.00" and po["dGST"] == "1.25" and po["dPST"] == "2.49"
    assert po["dTotalAmount"] == "1263.24"


def test_existing_demo_po_is_unchanged(client):
    po = client.get("/api/purchase-orders/500101").get_json()
    assert po["cSupplierCode"] == "TECBUR"
    assert po["dTotalAmount"] == "6714.54"
    assert [l["dUnitCost"] for l in po["lines"]] == ["1250.00", "210.00"]
