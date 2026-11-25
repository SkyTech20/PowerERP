"""The audit trail and the login lockout (step 4): security events, every change kept with its screen and record,
the reads and calculations left out, secrets masked, the lockout and the unlock, the screen's API and export."""

import io
import uuid

import pytest
from conftest import ADMIN_PASSWORD


def _user(admin, password="secret1", role="USER"):
    name = "u" + uuid.uuid4().hex[:8]
    r = admin.post("/api/users", json={"username": name, "name": name, "role": role, "password": password})
    assert r.status_code == 201, r.get_json()
    return r.get_json()


def _events(admin, **f):
    query = "&".join(f"{k}={v}" for k, v in f.items())
    return admin.get(f"/api/audit?size=500&{query}").get_json()["items"]


def test_logins_good_and_bad_are_kept(app, admin):
    u = _user(admin)
    c = app.test_client()
    assert c.post("/api/auth/login", json={"username": u["username"], "password": "nope"}).status_code == 401
    assert c.post("/api/auth/login", json={"username": "ghost", "password": "x"}).status_code == 401
    assert c.post("/api/auth/login", json={"username": u["username"], "password": "secret1"}).status_code == 200
    assert c.post("/api/auth/logout").status_code == 200
    mine = [(e["event"], e["details"].get("reason")) for e in _events(admin, kind="security", user=u["username"])]
    assert mine == [("logout", None), ("login_ok", None), ("login_failed", "bad_password")]  # newest first
    ghost = _events(admin, user="ghost")[0]
    assert (ghost["event"], ghost["details"]["reason"], ghost["ip"]) == ("login_failed", "unknown_user", "127.0.0.1")
    assert all("nope" not in str(e) and "secret1" not in str(e) for e in _events(admin))  # never a password


def test_lockout_after_failed_logins_and_unlock(app, admin, monkeypatch):
    monkeypatch.setenv("ERP_LOCKOUT_ATTEMPTS", "3")
    monkeypatch.setenv("ERP_LOCKOUT_MINUTES", "10")
    u = _user(admin)
    c = app.test_client()
    bad = {"username": u["username"], "password": "wrong1"}
    assert [c.post("/api/auth/login", json=bad).status_code for _ in range(2)] == [401, 401]
    r = c.post("/api/auth/login", json=bad)
    assert (r.status_code, r.get_json()["error"], r.get_json()["detail"]) == (423, "locked", "10")
    # locked: even the right password is refused
    good = {"username": u["username"], "password": "secret1"}
    assert c.post("/api/auth/login", json=good).status_code == 423
    row = admin.get(f"/api/users/{u['id']}").get_json()
    assert row["locked"] is True and row["locked_until"]
    listed = [x for x in admin.get("/api/users?size=500").get_json()["items"] if x["id"] == u["id"]][0]
    assert listed["locked"] is True
    events = [e["event"] for e in _events(admin, user=u["username"])]
    assert events[:3] == ["login_locked", "locked", "login_failed"]
    # the administrator unlocks: the user logs in again at once
    r = admin.post(f"/api/users/{u['id']}/unlock")
    assert r.status_code == 200 and r.get_json()["locked"] is False and r.get_json()["failed_logins"] == 0
    assert c.post("/api/auth/login", json=good).status_code == 200
    unlocked = _events(admin, event="unlocked", user=u["username"])[0]
    assert unlocked["details"]["by"] == "admin"


def test_a_good_login_forgets_the_failed_ones(app, admin, monkeypatch):
    monkeypatch.setenv("ERP_LOCKOUT_ATTEMPTS", "2")
    u = _user(admin)
    c = app.test_client()
    bad = {"username": u["username"], "password": "wrong1"}
    good = {"username": u["username"], "password": "secret1"}
    assert c.post("/api/auth/login", json=bad).status_code == 401
    assert c.post("/api/auth/login", json=good).status_code == 200
    assert c.post("/api/auth/login", json=bad).status_code == 401  # 1 in a row again: not locked
    assert c.post("/api/auth/login", json=good).status_code == 200


def test_lockout_off(app, admin, monkeypatch):
    monkeypatch.setenv("ERP_LOCKOUT_ATTEMPTS", "0")
    u = _user(admin)
    c = app.test_client()
    for _ in range(8):
        assert c.post("/api/auth/login", json={"username": u["username"], "password": "x"}).status_code == 401


def test_changes_are_kept_reads_and_calculations_are_not(client, admin):
    r = client.post("/api/customers", json={"cCode": "AUDIT-1", "cName": "Audit test", "cTaxGroup": "QC"})
    assert r.status_code == 201, r.get_json()
    client.put("/api/customers/AUDIT-1", json={**r.get_json(), "cName": "Audit test 2"})
    client.get("/api/customers/AUDIT-1")
    client.post("/api/production-orders/calc", json={"cProduct": "PAIN-BL-675", "dQty": "10"})  # a view: not kept
    client.post("/api/customers", json={"cCode": ""})  # refused (400): nothing changed, not kept
    rows = _events(admin, kind="change", q="audit-1")
    assert [(e["event"], e["screen"], e["record"], e["username"], e["method"]) for e in rows] == [
        ("edit", "sales.customers", "AUDIT-1", "api", "PUT"),
        ("create", "sales.customers", "AUDIT-1", "api", "POST"),
    ]
    assert rows[1]["details"]["sent"]["cName"] == "Audit test"
    assert not _events(admin, q="production-orders/calc")


def test_actions_and_secrets(app, admin):
    u = _user(admin, password="secret1")
    events = _events(admin, kind="change", screen="admin.users")
    created = [e for e in events if e["record"] == u["username"]][0]
    assert created["event"] == "create" and created["details"]["sent"]["password"] == "***"
    c = app.test_client()
    c.post("/api/auth/login", json={"username": u["username"], "password": "secret1"})
    assert c.post("/api/auth/password", json={"current": "bad", "password": "secret2"}).status_code == 400
    assert c.post("/api/auth/password", json={"current": "secret1", "password": "secret2"}).status_code == 200
    mine = [e["event"] for e in _events(admin, user=u["username"])]
    assert mine[:2] == ["password_changed", "password_failed"]
    # an action of a document: its name is the event
    o = admin.post("/api/production-orders", json={"cProduct": "PAIN-BL-675", "dQty": "10"}).get_json()
    admin.post(f"/api/production-orders/{o['iNo']}/release", json={"cComment": "go"})
    rel = _events(admin, screen="prod.orders", event="release")[0]
    assert (rel["record"], rel["username"], rel["details"]["sent"]) == (str(o["iNo"]), "admin", {"cComment": "go"})


def test_access_denied_is_a_security_event(app, admin):
    u = _user(admin)
    admin.put(f"/api/users/{u['id']}", json={**u, "role": "SALES"})
    c = app.test_client()
    c.post("/api/auth/login", json={"username": u["username"], "password": "secret1"})
    assert c.get("/api/audit").status_code == 403
    assert c.delete("/api/suppliers/TECBUR").status_code == 403
    denied = _events(admin, event="access_denied", user=u["username"])
    assert {e["path"] for e in denied} == {"/api/audit", "/api/suppliers/TECBUR"}


def test_filters_and_export(admin):
    from openpyxl import load_workbook

    admin.post("/api/auth/logout")
    admin.post("/api/auth/login", json={"username": "admin", "password": ADMIN_PASSWORD})
    page = admin.get("/api/audit?kind=security&size=1").get_json()
    assert page["size"] == 1 and page["total"] >= 2 and len(page["items"]) == 1
    assert page["items"][0]["event"] == "login_ok"
    assert admin.get("/api/audit?from=2000-01-01&to=2000-01-02").get_json()["total"] == 0
    f = admin.get("/api/audit/filters").get_json()
    assert "admin" in f["users"] and f["events"]["security"][0] == "login_ok"
    r = admin.get("/api/audit/export?kind=security&lang=fr")
    assert r.status_code == 200 and "audit-log.xlsx" in r.headers["Content-Disposition"]
    ws = load_workbook(io.BytesIO(r.data)).active
    assert ws.title == "Journal d'audit" and ws["B1"].value == "Utilisateur"
    assert ws["D2"].value == "login_ok" and ws["B2"].value == "admin"


@pytest.mark.parametrize("value, kept", [("x" * 400, "x" * 300 + "..."), (list(range(60))[:3], [0, 1, 2])])
def test_mask_cuts_long_values(value, kept):
    from powererp.modules.audit.service import mask

    assert mask({"v": value, "apiKey": "k", "cPassword": "p", "empty_password": ""})["v"] == kept
    assert mask({"apiKey": "k", "cPassword": "p", "empty_password": ""}) == {
        "apiKey": "***",
        "cPassword": "***",
        "empty_password": "",
    }
