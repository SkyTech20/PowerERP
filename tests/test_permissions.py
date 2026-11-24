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
        assert c.post("/api/auth/login", json={"username": name, "password": "secret1"}).status_code == 200
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
