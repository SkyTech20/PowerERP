"""Login, users and access control.

Who needs what:
  /  and  /assets/*            open (the page shows the login screen itself)
  /api/health, /api/auth/*     open
  /api/*                       a logged-in user (session cookie) or the API key
  /api/users*, /api/admin/*    an administrator (users, backups)
  PowerWARE web services       open, unless ERP_API_KEY is set: then the
  (/cgi-bin/..., used by SkyAI) caller sends it in the X-API-Key header

ERP_API_KEY lets SkyAI and scripts call the ERP without a session (in SkyAI: APIs > Authentication "API Key",
header X-API-Key). The first start creates the administrator ERP_ADMIN_USER (default "admin") with
ERP_ADMIN_PASSWORD; without it a random password is generated and printed in the log.
"""

from __future__ import annotations

import hmac
import os
from datetime import timedelta

from flask import Blueprint, Flask, jsonify, request, session

from powererp.container import Container
from powererp.core.http import json_payload
from powererp.core.values import text

from .service import AuthError, AuthService, UserRepository, UserService, public

__all__ = ["AuthError", "AuthService", "UserRepository", "UserService", "current_user", "register"]

PW_PREFIX = "/cgi-bin/"
OPEN_PATHS = {"/", "/api/health", "/api/auth/login", "/api/auth/logout", "/api/auth/me"}
ADMIN_PREFIXES = ("/api/users", "/api/admin/", "/api/demo", "/api/reset", "/api/clear")

_users = UserRepository()


def current_user():
    """The logged-in user (a dict, with the password hash), or None. Clears the session of an inactive user."""
    uid = session.get("uid")
    if not uid:
        return None
    row = _users.get(uid)
    if row is None or not row["active"]:
        session.clear()
        return None
    return row


def api_key_ok() -> bool:
    key = os.environ.get("ERP_API_KEY", "")
    sent = request.headers.get("X-API-Key", "")
    return bool(key) and hmac.compare_digest(sent.encode(), key.encode())


def guard():
    """Access control of every request (see the table at the top)."""
    path = request.path
    if request.method == "OPTIONS" or path in OPEN_PATHS or path.startswith("/assets/"):
        return None
    if path.startswith(PW_PREFIX):
        # SkyAI calls these without a session; protected only when ERP_API_KEY is set.
        if os.environ.get("ERP_API_KEY") and not api_key_ok():
            return jsonify({"error": "unauthorized"}), 401
        return None
    if api_key_ok():
        return None
    user = current_user()
    if user is None:
        return jsonify({"error": "unauthorized"}), 401
    if path.startswith(ADMIN_PREFIXES) and user["role"] != "admin":
        return jsonify({"error": "forbidden"}), 403
    return None


def _paged_users(rows):
    """Users list: search q, f_<field> filters, sort (username by default, ignoring case), pages."""
    q = text(request.args.get("q")).lower()
    if q:
        rows = [r for r in rows if any(q in text(r[f]).lower() for f in ("username", "name", "email"))]
    for key, val in request.args.items():
        if key.startswith("f_") and val != "":
            rows = [r for r in rows if text(r.get(key[2:])).lower() == val.lower()]
    sort = request.args.get("sort") or "username"
    rows.sort(key=lambda r: text(r.get(sort)).lower(), reverse=request.args.get("dir") == "desc")
    try:
        size = max(1, min(int(request.args.get("size", 25)), 500))
        page = max(1, int(request.args.get("page", 1)))
    except ValueError:
        size, page = 25, 1
    start = (page - 1) * size
    return {"total": len(rows), "page": page, "size": size, "items": rows[start : start + size]}


def _blueprint(auth: AuthService, users: UserService) -> Blueprint:
    bp = Blueprint("auth", __name__)

    @bp.route("/api/health")
    def health():
        return jsonify({"ok": True})

    @bp.route("/api/auth/login", methods=["POST"])
    def login():
        p = json_payload()
        uid = auth.login(text(p.get("username")), p.get("password") or "")
        session.clear()
        session.permanent = True
        session["uid"] = uid
        return jsonify(public(users.get(uid)))

    @bp.route("/api/auth/logout", methods=["POST"])
    def logout():
        session.clear()
        return jsonify({"ok": True})

    @bp.route("/api/auth/me")
    def me():
        user = current_user()
        if user is None:
            return jsonify({"error": "unauthorized"}), 401
        return jsonify(public(user))

    @bp.route("/api/auth/password", methods=["POST"])
    def change_password():
        """The logged-in user changes their own password."""
        user = current_user()
        if user is None:
            raise AuthError("unauthorized", status=401)
        p = json_payload()
        auth.change_password(user, p.get("current") or "", p.get("password") or "")
        return jsonify({"ok": True})

    @bp.route("/api/auth/lang", methods=["POST"])
    def set_lang():
        """Remember the language the logged-in user picked."""
        user = current_user()
        if user is None:
            raise AuthError("unauthorized", status=401)
        auth.set_lang(user, text(json_payload().get("lang")))
        return jsonify({"ok": True})

    @bp.route("/api/users", methods=["GET", "POST"])
    def users_collection():
        if request.method == "GET":
            return jsonify(_paged_users(users.list()))
        return jsonify(users.create(json_payload())), 201

    @bp.route("/api/users/<int:user_id>", methods=["GET", "PUT", "DELETE"])
    def users_item(user_id):
        existing = users.get(user_id)
        if request.method == "GET":
            return jsonify(public(existing))
        if request.method == "DELETE":
            users.delete(user_id, session.get("uid"))
            return jsonify({"ok": True})
        return jsonify(users.update(user_id, json_payload()))

    return bp


def register(app: Flask, c: Container) -> None:
    auth = c.register("auth", AuthService(_users))
    users = c.register("users", UserService(_users))
    app.config.update(
        SECRET_KEY=auth.secret_key(),
        # Own cookie name: SkyAI is served from the same host.
        SESSION_COOKIE_NAME="powererp_session",
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.environ.get("ERP_COOKIE_SECURE") == "1",
        PERMANENT_SESSION_LIFETIME=timedelta(hours=12),
    )
    auth.ensure_admin()
    app.before_request(guard)
    app.register_blueprint(_blueprint(auth, users))
