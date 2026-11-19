"""
PowerERP — users, login and access control.

Who needs what:
  /  and  /assets/*            open (the page shows the login screen itself)
  /api/health, /api/auth/*     open
  /api/*                       a logged-in user (session cookie) or the API key
  /api/users*                  an administrator
  PowerWARE web services       open, unless ERP_API_KEY is set: then the
  (/cgi-bin/..., used by SkyAI) caller sends it in the X-API-Key header

ERP_API_KEY lets SkyAI and scripts call the ERP without a session (in SkyAI:
APIs > Authentication "API Key", header X-API-Key).

The first start creates the administrator ERP_ADMIN_USER (default "admin") with
ERP_ADMIN_PASSWORD; without it a random password is generated and printed in the log.
"""
import hmac
import logging
import os
import secrets
from datetime import timedelta

from flask import Blueprint, jsonify, request, session
from sqlalchemy import func, select
from werkzeug.security import check_password_hash, generate_password_hash

import db
from powererp.models import User

logger = logging.getLogger(__name__)

ROLES = ("admin", "user")
LANGS = ("en", "fr")
PW_PREFIX = "/cgi-bin/"
OPEN_PATHS = {"/", "/api/health", "/api/auth/login", "/api/auth/logout", "/api/auth/me"}
MIN_PASSWORD = 6

bp = Blueprint("auth", __name__)


class AuthError(Exception):
    def __init__(self, code, field=None, status=400):
        super().__init__(code)
        self.code, self.field, self.status = code, field, status


@bp.errorhandler(AuthError)
def _auth_error(err):
    body = {"error": err.code}
    if err.field:
        body["field"] = err.field
    return jsonify(body), err.status


def _s(value):
    return "" if value is None else str(value).strip()


def _iso(value):
    return value.isoformat() if value else None


def _row(u):
    """A users row as a dict (what the rest of the ERP reads)."""
    if u is None:
        return None
    return {"id": u.id, "username": u.username, "name": u.name, "email": u.email, "role": u.role,
            "lang": u.lang, "active": u.active, "password_hash": u.password_hash,
            "created_at": _iso(u.created_at), "last_login": _iso(u.last_login)}


def _public(row):
    """A user as returned by the API (never the password hash)."""
    return {"id": row["id"], "username": row["username"], "name": row["name"], "email": row["email"],
            "role": row["role"], "lang": row["lang"], "active": bool(row["active"]),
            "created_at": row["created_at"], "last_login": row["last_login"]}


def _get_user(user_id):
    with db.session() as s:
        return _row(s.get(User, user_id))


def _by_username(s, username):
    return s.scalar(select(User).where(func.lower(User.username) == username.lower()))


def current_user():
    uid = session.get("uid")
    if not uid:
        return None
    row = _get_user(uid)
    if row is None or not row["active"]:
        session.clear()
        return None
    return row


def _api_key_ok():
    key = os.environ.get("ERP_API_KEY", "")
    sent = request.headers.get("X-API-Key", "")
    return bool(key) and hmac.compare_digest(sent.encode(), key.encode())


def _payload():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise AuthError("invalid_body")
    return data


def _check_password(pw, field="password"):
    if len(pw) < MIN_PASSWORD:
        raise AuthError("password_short", field)


def _count_admins(s, exclude_id=None):
    return s.scalar(select(func.count()).select_from(User).where(
        User.role == "admin", User.active.is_(True), User.id != (exclude_id or 0)))


# ---------------------------------------------------------------- guard

def _guard():
    path = request.path
    if request.method == "OPTIONS" or path in OPEN_PATHS or path.startswith("/assets/"):
        return None
    if path.startswith(PW_PREFIX):
        # SkyAI calls these without a session; protected only when ERP_API_KEY is set.
        if os.environ.get("ERP_API_KEY") and not _api_key_ok():
            return jsonify({"error": "unauthorized"}), 401
        return None
    if _api_key_ok():
        return None
    user = current_user()
    if user is None:
        return jsonify({"error": "unauthorized"}), 401
    if path.startswith("/api/users") and user["role"] != "admin":
        return jsonify({"error": "forbidden"}), 403
    return None


# ---------------------------------------------------------------- login

@bp.route("/api/health")
def health():
    return jsonify({"ok": True})


@bp.route("/api/auth/login", methods=["POST"])
def login():
    p = _payload()
    username, password = _s(p.get("username")), p.get("password") or ""
    with db.session() as s:
        u = _by_username(s, username)
        if u is None or not u.active or not check_password_hash(u.password_hash, password):
            raise AuthError("bad_login", status=401)
        u.last_login = db.now()
        uid = u.id
    session.clear()
    session.permanent = True
    session["uid"] = uid
    return jsonify(_public(_get_user(uid)))


@bp.route("/api/auth/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"ok": True})


@bp.route("/api/auth/me")
def me():
    user = current_user()
    if user is None:
        return jsonify({"error": "unauthorized"}), 401
    return jsonify(_public(user))


@bp.route("/api/auth/password", methods=["POST"])
def change_password():
    """The logged-in user changes their own password."""
    user = current_user()
    if user is None:
        raise AuthError("unauthorized", status=401)
    p = _payload()
    if not check_password_hash(user["password_hash"], p.get("current") or ""):
        raise AuthError("bad_password", "current")
    new = p.get("password") or ""
    _check_password(new)
    with db.session() as s:
        s.get(User, user["id"]).password_hash = generate_password_hash(new)
    return jsonify({"ok": True})


@bp.route("/api/auth/lang", methods=["POST"])
def set_lang():
    """Remember the language the logged-in user picked."""
    user = current_user()
    if user is None:
        raise AuthError("unauthorized", status=401)
    lang = _s(_payload().get("lang"))
    if lang in LANGS:
        with db.session() as s:
            s.get(User, user["id"]).lang = lang
    return jsonify({"ok": True})


# ---------------------------------------------------------------- users (admin)

def _user_from_payload(p, existing=None):
    row = {
        "username": _s(p.get("username")) if existing is None else existing["username"],
        "name": _s(p.get("name")),
        "email": _s(p.get("email")),
        "role": _s(p.get("role")) or "user",
        "lang": _s(p.get("lang")) or "en",
        "active": p.get("active", True) in (True, 1, "1", "true", "on"),
    }
    if not row["username"]:
        raise AuthError("required", "username")
    if not row["name"]:
        raise AuthError("required", "name")
    if row["role"] not in ROLES:
        raise AuthError("invalid_body", "role")
    if row["lang"] not in LANGS:
        row["lang"] = "en"
    return row


@bp.route("/api/users", methods=["GET", "POST"])
def users_collection():
    if request.method == "GET":
        q = _s(request.args.get("q")).lower()
        with db.session() as s:
            rows = [_public(_row(u)) for u in s.scalars(select(User).order_by(User.username))]
        if q:
            rows = [r for r in rows if any(q in _s(r[f]).lower() for f in ("username", "name", "email"))]
        for key, val in request.args.items():
            if key.startswith("f_") and val != "":
                rows = [r for r in rows if _s(r.get(key[2:])).lower() == val.lower()]
        sort = request.args.get("sort") or "username"
        rows.sort(key=lambda r: _s(r.get(sort)).lower(), reverse=request.args.get("dir") == "desc")
        try:
            size = max(1, min(int(request.args.get("size", 25)), 500))
            page = max(1, int(request.args.get("page", 1)))
        except ValueError:
            size, page = 25, 1
        start = (page - 1) * size
        return jsonify({"total": len(rows), "page": page, "size": size, "items": rows[start:start + size]})
    p = _payload()
    row = _user_from_payload(p)
    password = p.get("password") or ""
    if not password:
        raise AuthError("required", "password")
    _check_password(password)
    with db.session() as s:
        if _by_username(s, row["username"]) is not None:
            raise AuthError("duplicate", "username", 409)
        u = User(**row, password_hash=generate_password_hash(password))
        s.add(u)
        s.flush()
        new_id = u.id
    return jsonify(_public(_get_user(new_id))), 201


@bp.route("/api/users/<int:user_id>", methods=["GET", "PUT", "DELETE"])
def users_item(user_id):
    existing = _get_user(user_id)
    if existing is None:
        raise AuthError("not_found", status=404)
    if request.method == "GET":
        return jsonify(_public(existing))
    me_id = session.get("uid")
    if request.method == "DELETE":
        if user_id == me_id:
            raise AuthError("self_delete", status=409)
        with db.session() as s:
            if existing["role"] == "admin" and not _count_admins(s, user_id):
                raise AuthError("last_admin", status=409)
            s.delete(s.get(User, user_id))
        return jsonify({"ok": True})
    p = _payload()
    row = _user_from_payload(p, existing)
    password = p.get("password") or ""
    if password:
        _check_password(password)
    with db.session() as s:
        if (existing["role"] == "admin" and existing["active"] and (row["role"] != "admin" or not row["active"])
                and not _count_admins(s, user_id)):
            raise AuthError("last_admin", "role", 409)
        u = s.get(User, user_id)
        for k in ("name", "email", "role", "lang", "active"):
            setattr(u, k, row[k])
        if password:
            u.password_hash = generate_password_hash(password)
    return jsonify(_public(_get_user(user_id)))


# ---------------------------------------------------------------- setup

def _secret_key():
    key = os.environ.get("ERP_SECRET_KEY") or db.get_setting("secret_key")
    if not key:
        key = secrets.token_hex(32)
        db.set_setting("secret_key", key)  # kept in the database so sessions survive a restart
    return key


def _ensure_admin():
    with db.session() as s:
        if s.scalar(select(func.count()).select_from(User)):
            return
        username = os.environ.get("ERP_ADMIN_USER", "admin").strip() or "admin"
        password = os.environ.get("ERP_ADMIN_PASSWORD", "")
        generated = not password
        if generated:
            password = secrets.token_urlsafe(9)
        s.add(User(username=username, name="Administrator", email="", role="admin", lang="en", active=True,
                   password_hash=generate_password_hash(password)))
    msg = f"PowerERP: created administrator '{username}'"
    print(msg + (f" with password: {password}  (set ERP_ADMIN_PASSWORD to choose it)" if generated else ""), flush=True)


def register_auth(app):
    app.config.update(
        SECRET_KEY=_secret_key(),
        # Own cookie name: SkyAI is served from the same host.
        SESSION_COOKIE_NAME="powererp_session",
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.environ.get("ERP_COOKIE_SECURE") == "1",
        PERMANENT_SESSION_LIFETIME=timedelta(hours=12),
    )
    _ensure_admin()
    app.before_request(_guard)
    app.register_blueprint(bp)
