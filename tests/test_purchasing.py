"""apCreatePO.p: the PO SkyAI creates for each supplier of an approved requisition."""
from conftest import PW


def _create(client, **over):
    body = {"requisitionNumber": "DA-1", "supplierCode": "TECBUR", "requester": "Cassiano", "requiredDate": "2026-11-01",
            "lines": [{"productCode": "NEW-1", "description": "Item", "quantity": 2, "unitCost": "10"}]}
    body.update(over)
    return client.post(f"{PW}/apCreatePO.p", json=body)


def test_creates_po_with_taxes(client):
    r = _create(client)
    assert r.status_code == 201
    out = r.get_json()
    assert out["status"] == "ok" and out["alreadyExisted"] is False
    assert int(out["cPO"]) >= 500501
    po = client.get(f"/api/purchase-orders/{out['cPO']}").get_json()
    # TECBUR has TPS and TVQ numbers: 20.00 + 1.00 + 2.00 (9.975 % rounded)
    assert po["dSubTotal"] == "20.00" and po["dGST"] == "1.00" and po["dPST"] == "2.00"
    assert out["dTotalAmount"] == po["dTotalAmount"] == "23.00"
    assert po["cSource"] == "SkyAI" and po["cReference"] == "DA-1" and po["dDueDate"] == "2026-11-01"


def test_same_requisition_and_supplier_returns_existing_po(client):
    first = _create(client).get_json()
    again = _create(client)
    assert again.status_code == 200
    assert again.get_json()["cPO"] == first["cPO"] and again.get_json()["alreadyExisted"] is True


def test_numbers_follow_each_other(client):
    a = int(_create(client, requisitionNumber="DA-A").get_json()["cPO"])
    b = int(_create(client, requisitionNumber="DA-B").get_json()["cPO"])
    assert b == a + 1


def test_unit_cost_with_dollar_sign(client):
    out = _create(client, lines=[{"productCode": "X", "quantity": 1, "unitCost": "$12.50"}]).get_json()
    po = client.get(f"/api/purchase-orders/{out['cPO']}").get_json()
    assert po["lines"][0]["dUnitCost"] == "12.50"


def test_missing_unit_cost_uses_last_price(client):
    out = _create(client, lines=[{"productCode": "LAP-14I7", "quantity": 1}]).get_json()
    po = client.get(f"/api/purchase-orders/{out['cPO']}").get_json()
    assert po["lines"][0]["dUnitCost"] == "1250.00"


def test_errors(client):
    assert client.post(f"{PW}/apCreatePO.p", data="x", content_type="application/json").status_code == 400
    assert _create(client, supplierCode="NOPE").status_code == 400
    assert _create(client, lines=[]).status_code == 400
