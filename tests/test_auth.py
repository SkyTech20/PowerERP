"""Login, access control and user administration."""
import uuid

from conftest import ADMIN_PASSWORD, PW


def _name():
    return "u" + uuid.uuid4().hex[:8]


def test_health_is_open(anon):
    assert anon.get("/api/health").get_json() == {"ok": True}


def test_api_needs_login(anon):
    assert anon.get("/api/suppliers").status_code == 401
    assert anon.get("/api/auth/me").status_code == 401


def test_api_key_opens_the_api(client):
    assert client.get("/api/suppliers").status_code == 200


def test_wrong_api_key_is_refused(app):
    c = app.test_client()
    assert c.get("/api/suppliers", headers={"X-API-Key": "wrong"}).status_code == 401


def test_powerware_services_need_the_key_when_set(anon, client):
    url = PW + "/getSupplierTerm.p?COMPANY=MA2"
    assert anon.get(url).status_code == 401
    assert client.get(url).status_code == 200


def test_login_ok_and_me(admin):
    me = admin.get("/api/auth/me").get_json()
    assert me["username"] == "admin" and me["role"] == "admin"
    assert "password_hash" not in me


def test_login_bad_password(anon):
    r = anon.post("/api/auth/login", json={"username": "admin", "password": "nope"})
    assert r.status_code == 401 and r.get_json()["error"] == "bad_login"


def test_logout(admin):
    admin.post("/api/auth/logout")
    assert admin.get("/api/auth/me").status_code == 401


def test_admin_creates_user_and_user_cannot_manage_users(admin, app):
    name = _name()
    r = admin.post("/api/users", json={"username": name, "name": "Test", "role": "user", "password": "secret1"})
    assert r.status_code == 201
    assert "password_hash" not in r.get_json()

    u = app.test_client()
    assert u.post("/api/auth/login", json={"username": name, "password": "secret1"}).status_code == 200
    assert u.get("/api/suppliers").status_code == 200
    assert u.get("/api/users").status_code == 403


def test_user_rules(admin):
    name = _name()
    assert admin.post("/api/users", json={"username": name, "name": "T", "password": "123"}).get_json()["error"] == "password_short"
    assert admin.post("/api/users", json={"username": name, "name": "T"}).get_json() == {"error": "required", "field": "password"}
    assert admin.post("/api/users", json={"username": name, "name": "T", "role": "boss", "password": "secret1"}).status_code == 400
    assert admin.post("/api/users", json={"username": name, "name": "T", "password": "secret1"}).status_code == 201
    dup = admin.post("/api/users", json={"username": name.upper(), "name": "T", "password": "secret1"})
    assert dup.status_code == 409


def test_inactive_user_cannot_login(admin, app):
    name = _name()
    uid = admin.post("/api/users", json={"username": name, "name": "T", "password": "secret1"}).get_json()["id"]
    assert admin.put(f"/api/users/{uid}", json={"name": "T", "active": False}).status_code == 200
    r = app.test_client().post("/api/auth/login", json={"username": name, "password": "secret1"})
    assert r.status_code == 401


def test_cannot_delete_self_or_last_admin(admin):
    me = admin.get("/api/auth/me").get_json()
    assert admin.delete(f"/api/users/{me['id']}").get_json()["error"] == "self_delete"
    r = admin.put(f"/api/users/{me['id']}", json={"name": "Administrator", "role": "user"})
    assert r.status_code == 409 and r.get_json()["error"] == "last_admin"


def test_change_own_password(admin, app):
    name = _name()
    admin.post("/api/users", json={"username": name, "name": "T", "password": "secret1"})
    u = app.test_client()
    u.post("/api/auth/login", json={"username": name, "password": "secret1"})
    assert u.post("/api/auth/password", json={"current": "bad", "password": "secret2"}).get_json()["error"] == "bad_password"
    assert u.post("/api/auth/password", json={"current": "secret1", "password": "secret2"}).status_code == 200
    u.post("/api/auth/logout")
    assert u.post("/api/auth/login", json={"username": name, "password": "secret2"}).status_code == 200


def test_admin_password_from_env_works(anon):
    assert anon.post("/api/auth/login", json={"username": "admin", "password": ADMIN_PASSWORD}).status_code == 200
