"""Access control (A1): roles, permissions per screen and action, and the check of every API route."""

import re
from pathlib import Path

import pytest

from powererp.core import permissions as P

ROOT = Path(__file__).resolve().parent.parent


def _role(code, perms, active=True, is_admin=False):
    """A role straight in the database (the Roles screen and its API come in A2)."""
    from powererp import database
    from powererp.models import Role, RolePermission

    with database.session_scope() as s:
        s.add(Role(code=code, desc_fr=code, desc_en=code, active=active, is_admin=is_admin))
        s.flush()
        s.add_all(RolePermission(role_code=code, permission=p) for p in perms)


@pytest.fixture
def login(app, admin):
    """login(perms) -> a client logged in as a new user whose role has exactly these permissions."""
    count = {"n": 0}

    def make(perms, active=True):
        count["n"] += 1
        code = f"R{count['n']}"
        _role(code, perms)
        name = f"u{count['n']}"
        r = admin.post("/api/users", json={"username": name, "name": name, "role": code, "password": "secret1"})
        assert r.status_code == 201, r.get_json()
        if not active:  # a role switched off after its users were given it
            from powererp import database
            from powererp.models import Role

            with database.session_scope() as s:
                s.get(Role, code).active = False
        c = app.test_client()
        r = c.post("/api/auth/login", json={"username": name, "password": "secret1"})
        assert r.status_code == 200 and r.get_json()["permissions"] == P.clean(perms) or not active
        return c

    return make


# ------------------------------------------------------------------ catalog
def test_every_api_route_has_an_access_rule(app):
    missing = sorted(
        {r.endpoint for r in app.url_map.iter_rules() if r.rule.startswith("/api/") and not P.classified(r.endpoint)}
    )
    assert missing == [], "add these endpoints to powererp/core/permissions.py"


def test_rules_name_existing_routes(app):
    endpoints = {r.endpoint for r in app.url_map.iter_rules()}
    named = set(P._RULES) | set(P._READS) | P.ADMIN_ENDPOINTS | (P.OPEN_ENDPOINTS - {"static"})
    assert sorted(named - endpoints) == []


def test_screens_are_menu_entries():
    menu = (ROOT / "static/js/menu.js").read_text(encoding="utf-8")
    keys = set(re.findall(r'k: "([\w.]+)", route:', menu))
    assert sorted(s.key for s in P.SCREENS if s.key not in keys) == []


def test_crud_action_follows_the_method():
    assert P.required("sales.customers_item", "PUT", {}) == ["sales.customers:edit"]
    assert P.required("sales.sales_invoice_post", "POST", {}) == ["sales.invoices:post"]
    assert P.required("production.recipe_action", "POST", {"action": "copy"}) == ["prod.recipes:create"]
    assert P.required("production.recipe_action", "POST", {"action": "reject"}) == ["prod.recipes:approve"]
    # a read another screen needs: its own view or the view of the screens that read it
    assert set(P.required("suppliers.supplier_item", "GET", {})) == {
        "ap.suppliers:view",
        "ap.invoices:view",
        "pur.po:view",
        "pur.receptions:view",
    }
    assert P.required("suppliers.supplier_item", "PUT", {}) == ["ap.suppliers:edit"]
    assert P.required("nobody.knows", "GET", {}) is None


# ------------------------------------------------------------------ migration
def test_migration_roles(admin):
    from sqlalchemy import select

    from powererp import database
    from powererp.models import Role, RolePermission

    with database.session_scope() as s:
        roles = {r.code: (r.is_admin, r.active) for r in s.scalars(select(Role))}
        user = set(s.scalars(select(RolePermission.permission).where(RolePermission.role_code == "USER")))
    assert roles["ADMIN"] == (True, True) and roles["USER"] == (False, True)
    # USER: everything a plain user could do before roles; approving recipes stayed with the administrator
    assert user == set(P.all_permissions()) - {"prod.recipes:approve"}
    users = admin.get("/api/users").get_json()["items"]
    assert {u["username"]: u["role"] for u in users}["admin"] == "ADMIN"


# ------------------------------------------------------------------ the check of each call
def test_role_sees_only_its_screens(login):
    c = login(["sales.invoices:view", "sales.customers:view", "sales.customers:edit"])
    me = c.get("/api/auth/me").get_json()
    assert me["permissions"] == ["sales.customers:view", "sales.customers:edit", "sales.invoices:view"]
    assert me["isAdmin"] is False
    assert c.get("/api/sales-invoices").status_code == 200
    assert c.get("/api/customers").status_code == 200
    assert c.get("/api/purchase-orders").status_code == 403
    assert c.get("/api/products").status_code == 403
    assert c.post("/api/customers", json={"cCode": "X"}).status_code == 403  # view + edit, no create
    assert c.delete("/api/customers/HOTEL-LAURIER").status_code == 403
    assert c.post("/api/sales-invoices/1/post").status_code == 403  # no post
    # for everyone: own account, lookups, dashboard, company header
    assert c.get("/api/lookups/products").status_code == 200
    assert c.get("/api/summary").status_code == 200
    assert c.get("/api/company").status_code == 200
    # administrator only
    for url in ("/api/users", "/api/admin/backup", "/api/demo"):
        assert c.get(url).status_code == 403, url
    assert c.post("/api/reset").status_code == 403


def test_read_needed_by_another_screen(login):
    c = login(["pur.po:view"])
    sup = c.get("/api/purchase-orders").get_json()["items"][0]["cSupplierCode"]
    assert c.get(f"/api/suppliers/{sup}").status_code == 200  # the PO form shows the supplier
    assert c.get("/api/suppliers").status_code == 403  # not the Suppliers screen
    assert c.put(f"/api/suppliers/{sup}", json={}).status_code == 403


def test_special_actions(login):
    c = login(["inv.count:view", "inv.count:create", "inv.count:edit"])
    assert c.post("/api/stock-counts/1/post").status_code == 403
    c2 = login(["inv.count:view", "inv.count:post"])
    assert c2.post("/api/stock-counts/999999/post").status_code == 404  # allowed; the count does not exist


def test_reception_post_is_a_permission(login):
    from conftest import new_reception

    c = login(["pur.receptions:view", "pur.receptions:create", "pur.receptions:edit"])
    lines = [{"CodeArticle": "MON-27Q", "QuantiteRecue": "1", "PrixUnitaire": "250"}]
    assert new_reception(c, no="990301", Entrepot="ENT-01", lines=lines).status_code == 201
    assert c.post("/api/receptions/990301/check").status_code == 200  # a check needs only the view
    assert c.post("/api/receptions/990301/post").status_code == 403
    assert login(["pur.receptions:view", "pur.receptions:post"]).post("/api/receptions/990301/post").status_code == 200


def test_approve_is_a_permission(login):
    url = "/api/recipes/PAIN-BL-675/B"
    assert login(["prod.recipes:view", "prod.recipes:edit"]).post(f"{url}/approve", json={}).status_code == 403
    r = login(["prod.recipes:view", "prod.recipes:approve"]).post(f"{url}/approve", json={})
    assert r.status_code == 200 and r.get_json()["cStatus"] == "approved"


def test_inactive_role_gives_no_access(login):
    c = login(["sales.invoices:view"], active=False)
    assert c.get("/api/sales-invoices").status_code == 403
    assert c.get("/api/auth/me").get_json()["permissions"] == []


def test_api_key_keeps_full_access(client):
    assert client.get("/api/users").status_code == 200
    assert client.get("/api/purchase-orders").status_code == 200


# ------------------------------------------------------------------ users and roles
def test_user_role_must_exist(admin):
    r = admin.post("/api/users", json={"username": "rx", "name": "R", "role": "user", "password": "secret1"})
    assert r.status_code == 201 and r.get_json()["role"] == "USER"  # written as stored
    r = admin.post("/api/users", json={"username": "ry", "name": "R", "role": "BOSS", "password": "secret1"})
    assert r.status_code == 400 and r.get_json()["field"] == "role"
    _role("OFF", [], active=False)
    r = admin.post("/api/users", json={"username": "rz", "name": "R", "role": "OFF", "password": "secret1"})
    assert r.status_code == 400


def test_another_admin_role_keeps_the_last_admin_rule(admin):
    _role("BOSS", [], is_admin=True)
    me = admin.get("/api/auth/me").get_json()
    r = admin.post("/api/users", json={"username": "boss", "name": "B", "role": "BOSS", "password": "secret1"})
    assert r.status_code == 201
    # another active administrator exists: the first one may become a plain user
    assert admin.put(f"/api/users/{me['id']}", json={"name": "Administrator", "role": "USER"}).status_code == 200


# ------------------------------------------------------------------ Administration > Roles (A2)
def test_demo_roles(admin):
    rows = {r["cCode"]: r for r in admin.get("/api/roles").get_json()["items"]}
    assert {"ADMIN", "USER", "SALES", "PRODUCTION", "WAREHOUSE"} <= set(rows)
    assert rows["ADMIN"]["lAdmin"] and rows["ADMIN"]["permissions"] == P.all_permissions()
    assert rows["ADMIN"]["iUsers"] == 1
    assert "sales.invoices:post" in rows["SALES"]["permissions"]
    assert "sales.invoices:credit" not in rows["SALES"]["permissions"]
    assert all(p in P.all_permissions() for r in rows.values() for p in r["permissions"])
    catalog = admin.get("/api/permissions").get_json()
    assert [c["cScreen"] for c in catalog] == [s.key for s in P.SCREENS]
    lookup = admin.get("/api/lookups/roles?lang=en").get_json()
    assert {"code": "SALES", "label": "Sales desk"} in lookup


def test_role_create_edit_delete_with_history(admin, app):
    r = admin.post("/api/roles", json={"cCode": "buyer", "cDescFR": "Acheteur", "permissions": ["pur.po:edit"]})
    assert r.status_code == 201
    role = r.get_json()
    # the code is upper case; an action brings the view of its screen
    assert role["cCode"] == "BUYER" and role["permissions"] == ["pur.po:view", "pur.po:edit"]
    assert admin.post("/api/roles", json={"cCode": "Buyer", "cDescFR": "x"}).status_code == 409
    assert admin.post("/api/roles", json={"cCode": "A B", "cDescFR": "x"}).get_json()["error"] == "bad_code"
    assert admin.post("/api/roles", json={"cCode": "X1", "cDescFR": ""}).get_json()["field"] == "cDescFR"
    bad = admin.post("/api/roles", json={"cCode": "X2", "cDescFR": "x", "permissions": ["pur.po:fly"]})
    assert bad.status_code == 400 and bad.get_json()["detail"] == "pur.po:fly"

    r = admin.put(
        "/api/roles/buyer",
        json={"cDescFR": "Acheteuse", "permissions": ["pur.po:view", "pur.po:create", "ap.suppliers:view"]},
    )
    assert r.status_code == 200
    assert r.get_json()["permissions"] == ["ap.suppliers:view", "pur.po:view", "pur.po:create"]

    admin.post("/api/users", json={"username": "bea", "name": "Bea", "role": "BUYER", "password": "secret1"})
    u = app.test_client()
    u.post("/api/auth/login", json={"username": "bea", "password": "secret1"})
    assert u.get("/api/suppliers").status_code == 200
    assert u.get("/api/roles").status_code == 403  # roles: administrator only
    assert admin.get("/api/roles/BUYER").get_json()["users"][0]["username"] == "bea"
    assert admin.delete("/api/roles/BUYER").status_code == 409  # given to a user

    history = admin.get("/api/roles/buyer/history").get_json()
    assert [h["cChange"] for h in history] == ["permissions", "updated", "created"]
    assert history[0]["details"] == {"added": ["ap.suppliers:view", "pur.po:create"], "removed": ["pur.po:edit"]}
    assert history[1]["details"] == {"cDescFR": ["Acheteur", "Acheteuse"]} and history[0]["cUser"] == "admin"

    me = admin.get("/api/auth/me").get_json()
    admin.put(f"/api/users/{u.get('/api/auth/me').get_json()['id']}", json={"name": "Bea", "role": "USER"})
    assert admin.delete("/api/roles/BUYER").status_code == 200
    assert admin.get("/api/roles/BUYER").status_code == 404
    assert admin.get("/api/roles/BUYER/history").status_code == 404
    assert me["role"] == "ADMIN"


def test_copy_role_and_admin_role_is_fixed(admin):
    r = admin.post("/api/roles", json={"cCode": "SALES2", "cDescFR": "Ventes 2", "cCopyFrom": "sales"})
    assert r.status_code == 201
    sales = admin.get("/api/roles/SALES").get_json()
    assert r.get_json()["permissions"] == sales["permissions"]
    assert admin.get("/api/roles/SALES2/history").get_json()[0]["details"]["copiedFrom"] == "SALES"
    assert admin.put("/api/roles/ADMIN", json={"cDescFR": "x"}).get_json()["error"] == "admin_role"
    assert admin.delete("/api/roles/ADMIN").status_code == 409


def test_demo_reset_puts_the_example_roles_back(admin):
    admin.put("/api/roles/SALES", json={"permissions": []})
    assert admin.get("/api/roles/SALES").get_json()["permissions"] == []
    assert admin.post("/api/reset").status_code == 200
    assert "sales.invoices:view" in admin.get("/api/roles/SALES").get_json()["permissions"]
    last = admin.get("/api/roles/SALES/history").get_json()[0]
    assert last["cChange"] == "demo" and "sales.invoices:view" in last["details"]["added"]


# ------------------------------------------------------------------ dashboard (A3)
def test_dashboard_shows_the_figures_of_the_role(admin, client, login):
    everything = admin.get("/api/summary").get_json()
    assert set(everything) == set(P.DASHBOARD_KEYS)  # every figure belongs to a screen
    assert client.get("/api/summary").get_json() == everything  # API key: all
    assert login(["sales.invoices:view"]).get("/api/summary").get_json() == {}
    ap = login(["ap.invoices:view"]).get("/api/summary").get_json()
    assert set(ap) == {"invoices", "openInvoices", "openInvoicesAmount", "recentInvoices"}
