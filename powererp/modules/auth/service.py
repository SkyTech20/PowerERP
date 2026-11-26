"""Users and login: UserService (Administration > Users) and AuthService (login, own password and language)."""

from __future__ import annotations

import os
import secrets
from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func, select
from werkzeug.security import check_password_hash, generate_password_hash

from powererp import database, settings
from powererp.core.errors import AppError, NotFound
from powererp.core.values import text
from powererp.models import Role, RolePermission, User
from powererp.models.core import ADMIN_ROLE, USER_ROLE

LANGS = ("en", "fr")
MIN_PASSWORD = 6
# Lockout: after this many failed logins in a row the account is refused for this many minutes (the
# administrator can unlock it before: Administration > Users > Unlock). ERP_LOCKOUT_ATTEMPTS=0 turns it off.
LOCKOUT_ATTEMPTS = 5
LOCKOUT_MINUTES = 15
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
        "failed_logins": u.failed_logins or 0,
        "locked_until": _iso(u.locked_until),
    }


def public(row: Row) -> Row:
    """A user as returned by the API (never the password hash)."""
    return {
        "id": row["id"],
        "username": row["username"],
        "name": row["name"],
        "email": row["email"],
        "role": row["role"],
        "isAdmin": bool(row.get("is_admin")),
        "lang": row["lang"],
        "active": bool(row["active"]),
        "created_at": row["created_at"],
        "last_login": row["last_login"],
        "failed_logins": row.get("failed_logins", 0),
        "locked_until": row.get("locked_until") if _locked(row.get("locked_until")) else None,
        "locked": _locked(row.get("locked_until")),
    }


def _locked(until: str | None) -> bool:
    return bool(until) and datetime.fromisoformat(str(until)) > _now()


def lockout() -> tuple[int, int]:
    """(attempts, minutes) of the lockout: ERP_LOCKOUT_ATTEMPTS / ERP_LOCKOUT_MINUTES, else 5 and 15."""

    def env(name: str, default: int) -> int:
        try:
            return max(0, int(os.environ.get(name, default)))
        except ValueError:
            return default

    return env("ERP_LOCKOUT_ATTEMPTS", LOCKOUT_ATTEMPTS), max(1, env("ERP_LOCKOUT_MINUTES", LOCKOUT_MINUTES))


def check_password(pw: str, field: str = "password") -> None:
    if len(pw) < MIN_PASSWORD:
        raise AuthError("password_short", field)


class UserRepository:
    """The users table (own transaction per call: a login must be saved even if the request fails later)."""

    def get(self, user_id: int) -> Row | None:
        """The user with the access of their role: is_admin and permissions (a set)."""
        with database.session_scope() as s:
            row = as_row(s.get(User, user_id))
            if row is None:
                return None
            role = s.get(Role, row["role"])
            # an inactive role gives no access (the administrator role cannot be deactivated)
            row["is_admin"] = bool(role and role.active and role.is_admin)
            row["permissions"] = (
                set(s.scalars(select(RolePermission.permission).where(RolePermission.role_code == role.code)))
                if role is not None and role.active
                else set()
            )
            return row

    def by_username(self, s, username: str) -> User | None:
        return s.scalar(select(User).where(func.lower(User.username) == username.lower()))

    def all(self) -> list[Row]:
        with database.session_scope() as s:
            admins = set(s.scalars(select(Role.code).where(Role.is_admin, Role.active)))
            rows = [r for u in s.scalars(select(User).order_by(User.username)) if (r := as_row(u)) is not None]
            for r in rows:
                r["is_admin"] = r["role"] in admins
            return rows

    @staticmethod
    def role_code(s, code: str) -> str | None:
        """The code of an active role, written as stored ("user" finds USER); None when there is none."""
        return s.scalar(select(Role.code).where(func.upper(Role.code) == code.upper(), Role.active.is_(True)))

    @staticmethod
    def is_admin_role(s, code: str) -> bool:
        return bool(s.scalar(select(Role.is_admin).where(Role.code == code)))

    @staticmethod
    def count_admins(s, exclude_id: int | None = None) -> int:
        return s.scalar(
            select(func.count())
            .select_from(User)
            .join(Role, Role.code == User.role)
            .where(Role.is_admin, Role.active, User.active.is_(True), User.id != (exclude_id or 0))
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
            "role": text(p.get("role")) or USER_ROLE,
            "lang": text(p.get("lang")) or "en",
            "active": p.get("active", True) in (True, 1, "1", "true", "on"),
        }
        if not row["username"]:
            raise AuthError("required", "username")
        if not row["name"]:
            raise AuthError("required", "name")
        if row["lang"] not in LANGS:
            row["lang"] = "en"
        return row

    def _role(self, s, row: Row) -> None:
        """Checks the role (an active role of the roles table) and writes its code as stored."""
        code = self.repo.role_code(s, row["role"])
        if code is None:
            raise AuthError("invalid_body", "role")
        row["role"] = code

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
            self._role(s, row)
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
            self._role(s, row)
            last_admin = existing["is_admin"] and existing["active"]
            stays_admin = self.repo.is_admin_role(s, row["role"]) and row["active"]
            if last_admin and not stays_admin and not self.repo.count_admins(s, user_id):
                raise AuthError("last_admin", "role", 409)
            u = s.get(User, user_id)
            for k in ("name", "email", "role", "lang", "active"):
                setattr(u, k, row[k])
            if password:
                u.password_hash = generate_password_hash(password)
        return public(self.get(user_id))

    def unlock(self, user_id: int) -> Row:
        """Lets a locked user log in again at once (and forgets the failed logins)."""
        self.get(user_id)
        with database.session_scope() as s:
            u = s.get(User, user_id)
            u.failed_logins, u.locked_until = 0, None
        return public(self.get(user_id))

    def delete(self, user_id: int, me_id: int | None) -> None:
        existing = self.get(user_id)
        if user_id == me_id:
            raise AuthError("self_delete", status=409)
        with database.session_scope() as s:
            if existing["is_admin"] and not self.repo.count_admins(s, user_id):
                raise AuthError("last_admin", status=409)
            s.delete(s.get(User, user_id))


class AuthService:
    def __init__(self, repo: UserRepository, audit: Callable[..., None] | None = None):
        """audit(event, username, **details): keeps a security event (the audit trail)."""
        self.repo = repo
        self.audit = audit or (lambda *a, **k: None)

    def login(self, username: str, password: str) -> int:
        """The user id after checking the password (401 bad_login otherwise); records the login time.
        Failed logins in a row are counted: at the limit the account is locked for a while (423 locked, with the
        minutes left in detail); a locked account is refused even with the right password."""
        attempts, minutes = lockout()
        now = _now()
        with database.session_scope() as s:
            u = self.repo.by_username(s, username)
            if u is None:
                outcome, detail = "unknown_user", None
            elif u.locked_until and u.locked_until > now:
                outcome, detail = "locked", max(1, -(-int((u.locked_until - now).total_seconds()) // 60))
            elif not u.active:
                outcome, detail = "inactive", None
            elif not check_password_hash(u.password_hash, password):
                u.failed_logins = (u.failed_logins or 0) + 1
                outcome, detail = "bad_password", u.failed_logins
                if attempts and u.failed_logins >= attempts:
                    u.locked_until, u.failed_logins = now + timedelta(minutes=minutes), 0
                    outcome, detail = "now_locked", minutes
            else:
                u.last_login, u.failed_logins, u.locked_until = now, 0, None
                self.audit("login_ok", u.username)
                return u.id
            name = u.username if u is not None else username
        # outside the transaction: the failed login counted above is saved
        if outcome == "locked":
            self.audit("login_locked", name, minutes=detail)
            raise AuthError("locked", status=423, detail=str(detail))
        if outcome == "now_locked":
            self.audit("login_failed", name, reason="bad_password")
            self.audit("locked", name, minutes=detail, attempts=attempts)
            raise AuthError("locked", status=423, detail=str(detail))
        self.audit("login_failed", name, reason=outcome, **({"attempt": detail} if detail else {}))
        raise AuthError("bad_login", status=401)

    def signer(self, username: str, password: str) -> Row:
        """A second signature (shop floor records): the other user, checked with their own password.
        Returns {username, role, is_admin}; 400 bad_signature (field cSecondPassword) when the user is unknown,
        inactive, locked or the password is wrong (not 401: the operator stays logged in)."""
        if not text(username):
            raise AuthError("required", "cSecondUser")
        if not password:
            raise AuthError("required", "cSecondPassword")
        row: Row | None = None
        name = username
        with database.session_scope() as s:
            u = self.repo.by_username(s, username)
            if u is not None:
                name = u.username
                locked = bool(u.locked_until and u.locked_until > _now())
                if u.active and not locked and check_password_hash(u.password_hash, password):
                    role = s.get(Role, u.role)
                    row = {
                        "username": u.username,
                        "role": u.role,
                        "is_admin": bool(role and role.active and role.is_admin),
                    }
        if row is None:
            self.audit("signature_failed", name)
            raise AuthError("bad_signature", "cSecondPassword")
        self.audit("signature_ok", name)
        return row

    def change_password(self, user: Row, current: str, new: str) -> None:
        if not check_password_hash(user["password_hash"], current or ""):
            self.audit("password_failed", user["username"], reason="bad_password")
            raise AuthError("bad_password", "current")
        check_password(new)
        with database.session_scope() as s:
            s.get(User, user["id"]).password_hash = generate_password_hash(new)
        self.audit("password_changed", user["username"])

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
                    role=ADMIN_ROLE,
                    lang="en",
                    active=True,
                    password_hash=generate_password_hash(password),
                )
            )
        msg = f"PowerERP: created administrator '{username}'"
        extra = f" with password: {password}  (set ERP_ADMIN_PASSWORD to choose it)" if generated else ""
        print(msg + extra, flush=True)


__all__ = ["AuthError", "AuthService", "NotFound", "UserRepository", "UserService", "lockout", "public"]
