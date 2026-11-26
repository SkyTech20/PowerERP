"""Administration > Personal data (Quebec Law 25, item 9): find a person, the file and its export, anonymize a user,
a former user and a contact, the retention rule, the policy, and the administrator only."""

import io
import json
import uuid

import pytest

URL = "/api/privacy"


def _user(admin, **extra):
    name = "p" + uuid.uuid4().hex[:8]
    body = {"username": name, "name": f"Jo {name}", "email": f"{name}@mail.example", "password": "secret1", **extra}
    r = admin.post("/api/users", json=body)
    assert r.status_code == 201, r.get_json()
    return r.get_json()


def _deactivate(admin, u):
    r = admin.put(f"/api/users/{u['id']}", json={**u, "active": False})
    assert r.status_code == 200, r.get_json()


def _find(admin, q, kind=None):
    items = admin.get(f"{URL}/search?q={q}").get_json()["items"]
    return [p for p in items if kind is None or p["kind"] == kind]


def test_find_a_user_open_the_file_and_export(app, admin):
    u = _user(admin)
    c = app.test_client()
    assert c.post("/api/auth/login", json={"username": u["username"], "password": "secret1"}).status_code == 200
    c.post("/api/auth/logout")
    assert _find(admin, "x") == []  # 2 characters at least
    [p] = _find(admin, u["username"], "user")
    assert (p["ref"], p["email"], p["active"]) == (str(u["id"]), u["email"], True)
    f = admin.get(f"{URL}/user/{u['id']}").get_json()
    assert f["identity"]["email"] == u["email"] and f["identity"]["username"] == u["username"]
    assert f["events"] >= 3 and {"login_ok", "logout"} <= {e["event"] for e in f["recentEvents"]}
    assert (f["canAnonymize"], f["refusal"]) == (False, "user_active")
    j = admin.get(f"{URL}/user/{u['id']}/export")
    assert j.status_code == 200 and "attachment" in j.headers["Content-Disposition"]
    data = json.loads(j.data)
    assert data["person"]["name"] == u["name"] and len(data["auditLog"]) == f["events"]
    x = admin.get(f"{URL}/user/{u['id']}/export?format=xlsx&lang=fr")
    from openpyxl import load_workbook

    wb = load_workbook(io.BytesIO(x.data))
    assert wb.sheetnames == ["Personne", "Documents", "Journal d'audit"]
    assert admin.get(f"{URL}/user/999999").status_code == 404
    assert admin.get(f"{URL}/nobody/1").status_code == 404


def test_anonymize_a_user_everywhere(app, admin):
    u = _user(admin)
    # the user signs a document: a nonconformance created with their session
    c = app.test_client()
    c.post("/api/auth/login", json={"username": u["username"], "password": "secret1"})
    r = admin.post(f"{URL}/user/{u['id']}/anonymize")
    assert (r.status_code, r.get_json()["error"]) == (409, "user_active")
    me = admin.get("/api/auth/me").get_json()
    assert admin.post(f"{URL}/user/{me['id']}/anonymize").get_json()["error"] in (
        "cannot_anonymize_self",
        "user_active",
    )
    _deactivate(admin, u)
    assert admin.get(f"{URL}/user/{u['id']}").get_json()["canAnonymize"] is True
    r = admin.post(f"{URL}/user/{u['id']}/anonymize")
    assert r.status_code == 200, r.get_json()
    new = f"anon-{u['id']}"
    assert r.get_json()["name"] == new and r.get_json()["changed"] > 0
    row = admin.get(f"/api/users/{u['id']}").get_json()
    assert (row["username"], row["name"], row["email"], row["active"]) == (new, "Anonymized", "", False)
    # nothing names the person any more: not the audit log, not what it kept of the changes
    log = admin.get("/api/audit?size=500").get_json()["items"]
    text = json.dumps(log)
    assert u["username"] not in text and u["email"] not in text and u["name"] not in text
    assert all(e["ip"] == "" for e in log if e["username"] == new)
    assert _find(admin, u["username"]) == []
    # the anonymization is kept, without the name
    [done] = [e for e in log if e["event"] == "anonymize"][:1]
    assert (done["screen"], done["record"]) == ("admin.privacy", f"user/{u['id']}")
    # cannot sign in, cannot be anonymized twice
    assert (
        app.test_client().post("/api/auth/login", json={"username": u["username"], "password": "secret1"}).status_code
        == 401
    )
    r = admin.post(f"{URL}/user/{u['id']}/anonymize")
    assert r.get_json()["error"] == "already_anonymized"


def test_a_former_user_still_named_in_the_documents(app, admin):
    u = _user(admin)
    c = app.test_client()
    c.post("/api/auth/login", json={"username": u["username"], "password": "secret1"})
    assert admin.delete(f"/api/users/{u['id']}").status_code == 200
    [p] = _find(admin, u["username"], "former")
    assert p["ref"] == u["username"]
    f = admin.get(f"{URL}/former/{u['username']}").get_json()
    assert f["canAnonymize"] and f["events"] >= 1
    r = admin.post(f"{URL}/former/{u['username']}/anonymize")
    assert r.status_code == 200 and r.get_json()["name"].startswith("anon-")
    assert _find(admin, u["username"]) == []
    log = json.dumps(admin.get("/api/audit?size=500").get_json()["items"])
    assert u["username"] not in log  # not even in the path of the anonymization
    assert admin.get(f"{URL}/former/{u['username']}").status_code == 404


def test_anonymize_a_contact_and_a_ship_to_contact(client, admin):
    body = {
        "cCode": "PRIV-1",
        "cName": "Privacy test",
        "cTaxGroup": "QC",
        "addresses": [
            {
                "cCode": "MAIN",
                "cAddress1": "1 rue A",
                "cCity": "Laval",
                "cContact": "Marie Tremblay",
                "cPhone": "514-555-0101",
            }
        ],
        "contacts": [
            {"cName": "Luc Gagnon", "cTitle": "Buyer", "cEmail": "luc.gagnon@resto.example", "cPhone": "514-555-0199"}
        ],
    }
    assert client.post("/api/customers", json=body).status_code == 201
    [k] = _find(admin, "gagnon", "contact")
    assert (k["email"], k["where"]) == ("luc.gagnon@resto.example", "PRIV-1 Privacy test")
    f = admin.get(f"{URL}/contact/{k['ref']}").get_json()
    assert f["identity"]["customer"] == "PRIV-1" and f["events"] >= 1  # the creation of the customer names him
    assert admin.post(f"{URL}/contact/{k['ref']}/anonymize").status_code == 200
    assert client.get("/api/customers/PRIV-1").get_json()["contacts"] == []
    [a] = _find(admin, "marie tremblay", "shipto")
    assert admin.post(f"{URL}/shipto/{a['ref']}/anonymize").status_code == 200
    addr = client.get("/api/customers/PRIV-1").get_json()["addresses"][0]
    assert (addr["cContact"], addr["cPhone"], addr["cCity"]) == ("", "", "Laval")
    log = json.dumps(admin.get("/api/audit?size=500&q=PRIV-1").get_json()["items"])
    assert "Gagnon" not in log and "luc.gagnon" not in log and "514-555-0199" not in log and "Tremblay" not in log


def test_retention_lists_and_anonymizes_who_is_kept_too_long(client, admin, app):
    from datetime import date

    old = _user(admin)
    _deactivate(admin, old)
    body = {
        "cCode": "PRIV-OLD",
        "cName": "Closed",
        "cTaxGroup": "QC",
        "lActive": False,
        "contacts": [{"cName": "Ann Old"}],
    }
    assert client.post("/api/customers", json=body).status_code == 201
    # nobody is older than 24 months: the users were just created
    due = admin.get(f"{URL}/retention").get_json()
    assert due["months"] == 24 and str(old["id"]) not in {p["ref"] for p in due["items"] if p["kind"] == "user"}
    # the contact of an inactive customer without an invoice is due at once
    assert "Ann Old" in {p["name"] for p in due["items"]}
    # one year later with a retention of 1 month: the inactive user is due too
    svc = _service(app)
    svc._today = lambda: date.today().replace(year=date.today().year + 1)
    try:
        assert admin.put(f"{URL}/policy", json={"iRetentionMonths": "1"}).status_code == 200
        due = admin.get(f"{URL}/retention").get_json()
        assert str(old["id"]) in {p["ref"] for p in due["items"] if p["kind"] == "user"}
        r = admin.post(f"{URL}/retention/apply")
        assert r.status_code == 200 and r.get_json()["anonymized"] == len(due["items"])
        assert admin.get(f"{URL}/retention").get_json()["items"] == []
        assert admin.get(f"/api/users/{old['id']}").get_json()["username"] == f"anon-{old['id']}"
    finally:
        svc._today = date.today
        admin.put(f"{URL}/policy", json={"iRetentionMonths": "24"})


def _service(app):
    for fn in app.view_functions.values():
        for cell in getattr(fn, "__closure__", None) or ():
            if type(cell.cell_contents).__name__ == "PrivacyService":
                return cell.cell_contents
    raise AssertionError("no PrivacyService")


def test_the_policy_is_checked_and_kept(admin):
    p = {
        "cOfficerName": "Mohamed",
        "cOfficerTitle": "President",
        "cOfficerEmail": "privacy@shop.example",
        "cHosting": "Amazon Web Services",
        "cRegion": "ca-central-1 (Montreal)",
        "iRetentionMonths": "36",
    }
    r = admin.put(f"{URL}/policy", json=p)
    assert r.status_code == 200 and r.get_json()["iRetentionMonths"] == 36
    assert admin.get(f"{URL}/policy").get_json()["cRegion"] == "ca-central-1 (Montreal)"
    for bad, code in (
        ({"cOfficerEmail": "nope"}, "invalid_email"),
        ({"iRetentionMonths": "x"}, "numeric"),
        ({"iRetentionMonths": "0"}, "out_of_range"),
    ):
        r = admin.put(f"{URL}/policy", json={**p, **bad})
        assert (r.status_code, r.get_json()["error"]) == (400, code)
    admin.put(f"{URL}/policy", json={"iRetentionMonths": "24"})


@pytest.mark.parametrize(
    "method, path", [("get", "/search?q=jo"), ("get", "/policy"), ("get", "/retention"), ("post", "/retention/apply")]
)
def test_only_the_administrator(app, admin, method, path):
    u = _user(admin)
    other = app.test_client()
    other.post("/api/auth/login", json={"username": u["username"], "password": "secret1"})
    assert getattr(other, method)(URL + path).status_code == 403


def test_every_column_with_a_user_name_is_known(app, admin):
    """A new table that keeps who did something must be added to USER_COLUMNS (or the person stays named)."""
    from sqlalchemy import text

    from powererp import database
    from powererp.modules.privacy.service import USER_COLUMNS

    with database.session_scope() as s:
        found = {
            (t, c)
            for t, c in s.execute(
                text(
                    "SELECT table_name, column_name FROM information_schema.columns WHERE table_schema = current_schema() "
                    "AND (column_name IN ('user', 'username', 'second_user') OR column_name LIKE '%\\_by')"
                )
            ).all()
        }
    assert found - {("users", "username")} == set(USER_COLUMNS)
