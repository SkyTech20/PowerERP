"""Receptions: creation, totals, unbilled list, and amounts typed with "$"."""
from conftest import new_reception


def test_create_reception(client):
    r = new_reception(client, Transport="1", TPS="1.05", TVQ="2.10")
    assert r.status_code == 201
    rec = r.get_json()
    assert rec["Fournisseur"]  # filled from the supplier code
    assert rec["lines"][0]["QuantiteRecue"] == "5"
    assert rec["MontantTotal"] == "24.15"
    assert rec["lUnbilled"] is True
    unb = [x for x in client.get("/api/receptions?f_lUnbilled=true&size=500").get_json()["items"] if x["NoReception"] == "990101"]
    assert unb


def test_reception_number_must_be_numeric(client):
    r = new_reception(client, no="REC-1")
    assert r.status_code == 400 and r.get_json() == {"error": "numeric", "field": "NoReception"}


def test_reception_required_fields_and_duplicate(client):
    r = client.post("/api/receptions", json={"NoReception": "990102", "DateReception": "2026-10-01"})
    assert r.get_json() == {"error": "required", "field": "NoBonCommande"}
    assert new_reception(client, no="700101").status_code == 409


def test_reception_amounts_typed_with_dollar_sign(client):
    """Regression: "$" in the unit price was saved as typed and the amount became 0."""
    rec = new_reception(client, Transport="$2", TPS="$1.00", TVQ="1,99 $", lines=[
        {"CodeArticle": "A", "QuantiteCommandee": "3", "QuantiteRecue": "3", "PrixUnitaire": "$4.50"},
        {"CodeArticle": "B", "QuantiteCommandee": "1", "QuantiteRecue": "1", "PrixUnitaire": "$1,000.00"},
    ]).get_json()
    assert [l["PrixUnitaire"] for l in rec["lines"]] == ["4.50", "1000.00"]
    assert rec["SousTotal"] == "1013.50"
    assert rec["Transport"] == "2.00" and rec["TPS"] == "1.00" and rec["TVQ"] == "1.99"
    assert rec["MontantTotal"] == "1018.49"


def test_update_and_delete_reception(client):
    new_reception(client)
    upd = client.put("/api/receptions/990101", json={"NoBonCommande": "500301", "DateReception": "2026-10-03", "lUnbilled": False,
                                                    "lines": [{"CodeArticle": "A", "QuantiteRecue": "2", "PrixUnitaire": "3"}]}).get_json()
    assert upd["MontantTotal"] == "6.00" and upd["lUnbilled"] is False
    assert client.delete("/api/receptions/990101").status_code == 200
    assert client.get("/api/receptions/990101").status_code == 404


def test_existing_demo_reception_is_unchanged(client):
    rec = client.get("/api/receptions/700101").get_json()
    assert rec["NoBonCommande"] == "500101" and rec["MontantTotal"] == "5748.75"
