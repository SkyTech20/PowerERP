"""General ledger: GL accounts (type, FR / EN, active, requires a cost center), cost centers as departments and
sub-departments, and the account + cost center of the purchase lines (supplier invoices, receptions)."""

import pytest

from powererp.modules.ledger import guess_type, normalize_accounts
from tests.conftest import new_reception


@pytest.mark.parametrize(
    "code,kind",
    [
        ("1310", "asset"),
        ("2100", "liability"),
        ("3000", "equity"),
        ("4010", "revenue"),
        ("5100", "expense"),
        ("9", "expense"),
    ],
)
def test_type_from_the_code(code, kind):
    assert guess_type(code) == kind


def test_rows_of_an_older_seed_get_a_type_and_stay_active():
    assert normalize_accounts([{"cCode": "2100", "cDesc": "Fournisseurs"}]) == [
        {"cCode": "2100", "cDesc": "Fournisseurs", "cType": "liability", "lActive": True}
    ]
    assert (
        normalize_accounts([{"cCode": "1", "cDesc": "x", "cType": "equity", "lActive": False}])[0]["cType"] == "equity"
    )


def test_account_fields(client):
    seeded = client.get("/api/gl-accounts/2100").get_json()
    assert (seeded["cType"], seeded["lActive"], seeded["lRequiresCC"]) == ("liability", True, False)
    r = client.post("/api/gl-accounts", json={"cCode": "4100", "cDesc": "Ventes", "cDescEN": "Sales", "cType": ""})
    assert r.status_code == 201 and r.get_json()["cType"] == "revenue"  # from the code
    r = client.post(
        "/api/gl-accounts", json={"cCode": "1310", "cDesc": "Stock MP", "cType": "asset", "lRequiresCC": False}
    )
    assert r.get_json()["cType"] == "asset"
    assert client.post("/api/gl-accounts", json={"cCode": "X1", "cDesc": "x", "cType": "nope"}).get_json() == {
        "error": "invalid_choice",
        "field": "cType",
    }
    upd = client.put("/api/gl-accounts/4100", json={"cDescEN": "Product sales", "lActive": False}).get_json()
    assert (upd["cDesc"], upd["cDescEN"], upd["lActive"], upd["cType"]) == ("Ventes", "Product sales", False, "revenue")
    codes = {r["code"] for r in client.get("/api/lookups/gl?all=1").get_json()}
    assert "4100" not in codes and "1310" in codes  # an inactive account is not proposed
    en = {r["code"]: r["label"] for r in client.get("/api/lookups/gl?all=1&lang=en").get_json()}
    assert en["1310"] == "Stock MP"  # no English description: the French one
    assert client.get("/api/gl-accounts?f_cType=revenue").get_json()["total"] == 1


def test_departments_and_sub_departments(client):
    assert client.post("/api/cost-centers", json={"cCC1": "700", "cCC2": "710", "cDesc": "Orphan"}).get_json() == {
        "error": "no_department",
        "field": "cCC1",
    }
    assert (
        client.post(
            "/api/cost-centers", json={"cCC1": "700", "cDesc": "Production", "cDescEN": "Production"}
        ).status_code
        == 201
    )
    assert (
        client.post("/api/cost-centers", json={"cCC1": "700", "cCC2": "710", "cDesc": "Ligne sirop"}).status_code == 201
    )
    client.post("/api/cost-centers", json={"cCC1": "700", "cCC2": "720", "cDesc": "Emballage", "lActive": False})
    assert client.get("/api/cost-centers/700").get_json()["lActive"] is True
    assert [r["code"] for r in client.get("/api/lookups/cc2?cc1=700").get_json()] == ["710"]  # active only
    assert "700" in [r["code"] for r in client.get("/api/lookups/cc1?all=1").get_json()]
    assert "710" not in [r["code"] for r in client.get("/api/lookups/cc1?all=1").get_json()]
    assert client.delete("/api/cost-centers/700").status_code == 409  # still has sub-departments
    assert client.delete("/api/cost-centers/700/710").status_code == 200
    assert client.delete("/api/cost-centers/700/720").status_code == 200
    assert client.delete("/api/cost-centers/700").status_code == 200


def _inv(lines):
    body = {"cNoFourn": "TECBUR", "cNoFacture": "GL-1", "dDateFacture": "2026-10-05", "lines": lines}
    return body | {"dTransport": "0", "dTotalTPS": "0", "dTotalTVP": "0"}


def test_purchase_lines_check_account_and_cost_center(client):
    client.post("/api/gl-accounts", json={"cCode": "5900", "cDesc": "Entretien", "lRequiresCC": True})
    line = {"cCodeProduit": "A", "dQuantite": "1", "dCoutUnitaire": "10", "cGL": "5900"}
    r = client.post("/api/invoices", json=_inv([line]))
    assert r.status_code == 400 and r.get_json() == {"error": "cc_required", "field": "lines", "detail": "1: 5900"}
    r = client.post("/api/invoices", json=_inv([{**line, "cCC1": "100", "cCC2": "999"}]))
    assert r.get_json()["error"] == "unknown_cc" and r.get_json()["detail"] == "1: 100-999"
    r = client.post("/api/invoices", json=_inv([{**line, "cGL": "0000"}]))
    assert r.get_json()["error"] == "unknown_gl"
    r = client.post("/api/invoices", json=_inv([{**line, "cCC2": "210"}]))
    assert r.get_json()["error"] == "no_department"
    ok = client.post(
        "/api/invoices", json=_inv([{**line, "cCC1": "100", "cCC2": "210"}, {"cCodeProduit": "B", "dQuantite": "1"}])
    )
    assert ok.status_code == 201  # a line without account nor cost center is still allowed

    rec = {"CodeArticle": "PAP-01", "QuantiteCommandee": "1", "QuantiteRecue": "1", "PrixUnitaire": "1", "cGL": "5900"}
    r = new_reception(client, no="990777", lines=[rec])
    assert r.status_code == 400 and r.get_json()["error"] == "cc_required"
    assert new_reception(client, no="990777", lines=[{**rec, "cCC1": "200"}]).status_code == 201
    r = client.put(
        "/api/receptions/990777",
        json={"NoBonCommande": "500301", "DateReception": "2026-10-02", "lines": [{**rec, "cCC1": "ZZ"}]},
    )
    assert r.get_json()["error"] == "unknown_cc"
