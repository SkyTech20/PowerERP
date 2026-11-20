"""Users and login: UserService (Administration > Users) and AuthService (login, own password and language)."""

from __future__ import annotations

import os
import secrets
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select
from werkzeug.security import check_password_hash, generate_password_hash

from powererp import database, settings
from powererp.core.errors import AppError, NotFound
from powererp.core.values import text
from powererp.models import User

ROLES = ("admin", "user")
LANGS = ("en", "fr")
MIN_PASSWORD = 6
Row = dict[str, Any]


class AuthError(AppError):
    """Login and user errors (same JSON as every other error)."""


def _iso(value) -> str | None:
    return value.isoformat() if value else None


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def as_row(u: User | None) -> Row | None:
    """A users row as a dict (what the rest of the ERP reads), password hash included."""
    if u is None:
        return None
    return {
        "id": u.id,
        "username": u.username,
        "name": u.name,
        "email": u.email,
        "role": u.role,
        "lang": u.lang,
        "active": u.active,
        "password_hash": u.password_hash,
        "created_at": _iso(u.created_at),
        "last_login": _iso(u.last_login),
    }


def public(row: Row) -> Row:
    """A user as returned by the API (never the password hash)."""
    return {
        "id": row["id"],
        "username": row["username"],
        "name": row["name"],
        "email": row["email"],
        "role": row["role"],
        "lang": row["lang"],
        "active": bool(row["active"]),
        "created_at": row["created_at"],
        "last_login": row["last_login"],
    }


def check_password(pw: str, field: str = "password") -> None:
    if len(pw) < MIN_PASSWORD:
        raise AuthError("password_short", field)


class UserRepository:
    """The users table (own transaction per call: a login must be saved even if the request fails later)."""

    def get(self, user_id: int) -> Row | None:
        with database.session_scope() as s:
            return as_row(s.get(User, user_id))

    def by_username(self, s, username: str) -> User | None:
        return s.scalar(select(User).where(func.lower(User.username) == username.lower()))

    def all(self) -> list[Row]:
        with database.session_scope() as s:
            return [r for u in s.scalars(select(User).order_by(User.username)) if (r := as_row(u)) is not None]

    @staticmethod
    def count_admins(s, exclude_id: int | None = None) -> int:
        return s.scalar(
            select(func.count())
            .select_from(User)
            .where(User.role == "admin", User.active.is_(True), User.id != (exclude_id or 0))
        )


class UserService:
    def __init__(self, repo: UserRepository):
        self.repo = repo

    @staticmethod
    def from_payload(p: Row, existing: Row | None = None) -> Row:
        row = {
            "username": text(p.get("username")) if existing is None else existing["username"],
            "name": text(p.get("name")),
            "email": text(p.get("email")),
            "role": text(p.get("role")) or "user",
            "lang": text(p.get("lang")) or "en",
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

    def list(self) -> list[Row]:
        return [public(r) for r in self.repo.all()]

    def get(self, user_id: int) -> Row:
        row = self.repo.get(user_id)
        if row is None:
            raise AuthError("not_found", status=404)
        return row

    def create(self, p: Row) -> Row:
        row = self.from_payload(p)
        password = p.get("password") or ""
        if not password:
            raise AuthError("required", "password")
        check_password(password)
        with database.session_scope() as s:
            if self.repo.by_username(s, row["username"]) is not None:
                raise AuthError("duplicate", "username", 409)
            u = User(**row, password_hash=generate_password_hash(password))
            s.add(u)
            s.flush()
            new_id = u.id
        return public(self.get(new_id))

    def update(self, user_id: int, p: Row) -> Row:
        existing = self.get(user_id)
        row = self.from_payload(p, existing)
        password = p.get("password") or ""
        if password:
            check_password(password)
        with database.session_scope() as s:
            last_admin = existing["role"] == "admin" and existing["active"]
            if last_admin and (row["role"] != "admin" or not row["active"]) and not self.repo.count_admins(s, user_id):
                raise AuthError("last_admin", "role", 409)
            u = s.get(User, user_id)
            for k in ("name", "email", "role", "lang", "active"):
                setattr(u, k, row[k])
            if password:
                u.password_hash = generate_password_hash(password)
        return public(self.get(user_id))

    def delete(self, user_id: int, me_id: int | None) -> None:
        existing = self.get(user_id)
        if user_id == me_id:
            raise AuthError("self_delete", status=409)
        with database.session_scope() as s:
            if existing["role"] == "admin" and not self.repo.count_admins(s, user_id):
                raise AuthError("last_admin", status=409)
            s.delete(s.get(User, user_id))


class AuthService:
    def __init__(self, repo: UserRepository):
        self.repo = repo

    def login(self, username: str, password: str) -> int:
        """The user id after checking the password (401 bad_login otherwise); records the login time."""
        with database.session_scope() as s:
            u = self.repo.by_username(s, username)
            if u is None or not u.active or not check_password_hash(u.password_hash, password):
                raise AuthError("bad_login", status=401)
            u.last_login = _now()
            return u.id

    def change_password(self, user: Row, current: str, new: str) -> None:
        if not check_password_hash(user["password_hash"], current or ""):
            raise AuthError("bad_password", "current")
        check_password(new)
        with database.session_scope() as s:
            s.get(User, user["id"]).password_hash = generate_password_hash(new)

    def set_lang(self, user: Row, lang: str) -> None:
        if lang in LANGS:
            with database.session_scope() as s:
                s.get(User, user["id"]).lang = lang

    @staticmethod
    def secret_key() -> str:
        """ERP_SECRET_KEY, else a random key kept in the database (sessions survive a restart)."""
        key = os.environ.get("ERP_SECRET_KEY") or settings.get_setting("secret_key")
        if not key:
            key = secrets.token_hex(32)
            settings.set_setting("secret_key", key)
        return key

    @staticmethod
    def ensure_admin() -> None:
        """The first start creates the administrator ERP_ADMIN_USER / ERP_ADMIN_PASSWORD (random if not set)."""
        with database.session_scope() as s:
            if s.scalar(select(func.count()).select_from(User)):
                return
            username = os.environ.get("ERP_ADMIN_USER", "admin").strip() or "admin"
            password = os.environ.get("ERP_ADMIN_PASSWORD", "")
            generated = not password
            if generated:
                password = secrets.token_urlsafe(9)
            s.add(
                User(
                    username=username,
                    name="Administrator",
                    email="",
                    role="admin",
                    lang="en",
                    active=True,
                    password_hash=generate_password_hash(password),
                )
            )
        msg = f"PowerERP: created administrator '{username}'"
        extra = f" with password: {password}  (set ERP_ADMIN_PASSWORD to choose it)" if generated else ""
        print(msg + extra, flush=True)


__all__ = ["AuthError", "AuthService", "NotFound", "UserRepository", "UserService", "public"]
