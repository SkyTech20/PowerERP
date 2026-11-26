"""Roles (Administration > Roles): what each role may open and do, and the history of every change.

A role has a code, a description (FR/EN), an active flag and its permissions ("<screen>:<action>", see
powererp/core/permissions.py). The administrator role (is_admin) has every permission and cannot be changed or
deleted. A role given to a user cannot be deleted; an inactive role gives its users no access.
Every change is written to role_history: created (copied from), updated (fields: old -> new), permissions
(added / removed), demo (put back by the demo data) and deleted.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from datetime import datetime
from typing import Any

from sqlalchemy import delete, func, select

from powererp import database
from powererp.core import permissions as P
from powererp.core.errors import AppError
from powererp.core.values import text
from powererp.models import Role, RoleHistory, RolePermission, User

Row = dict[str, Any]
CODE = re.compile(r"^[A-Z0-9][A-Z0-9_-]{0,29}$")

# Example roles of the demo data (put back by Administration > System settings > reset).
DEMO_ROLES: tuple[Row, ...] = (
    {
        "cCode": "SALES",
        "cDescFR": "Comptoir des ventes",
        "cDescEN": "Sales desk",
        "permissions": [
            "sales.customers:view",
            "sales.customers:create",
            "sales.customers:edit",
            "sales.priceLists:view",
            "sales.invoices:view",
            "sales.invoices:create",
            "sales.invoices:edit",
            "sales.invoices:delete",
            "sales.invoices:post",
            "sales.invoices:print",
            "inv.items:view",
            "inv.stock:view",
            "admin.taxes:view",
        ],
    },
    {
        "cCode": "PRODUCTION",
        "cDescFR": "Planification de la production",
        "cDescEN": "Production planning",
        "permissions": [
            f"{s.key}:{a}"
            for s in P.SCREENS
            if s.module == "prod"
            for a in s.actions
            if a != "approve" and not (s.key == "prod.recipes" and a == "delete")
        ]
        + ["inv.items:view", "inv.stock:view", "inv.setup:view"]
        + [f"{s.key}:{a}" for s in P.SCREENS if s.module == "qa" for a in s.actions if a != "delete"],
    },
    {
        "cCode": "WAREHOUSE",
        "cDescFR": "Entrepôt et inventaires",
        "cDescEN": "Warehouse and counts",
        "permissions": [
            "inv.items:view",
            "inv.stock:view",
            "inv.movements:view",
            "inv.movements:create",
            "inv.movements:edit",
            "inv.replenishment:view",
            "inv.count:view",
            "inv.count:create",
            "inv.count:edit",
            "inv.count:post",
            "qa.lots:view",
            "qa.nc:view",
            "qa.nc:create",
            "inv.warehouses:view",
            "inv.params:view",
            "inv.params:edit",
            "pur.receptions:view",
            "pur.receptions:create",
            "pur.receptions:edit",
            "pur.receptions:post",
        ],
    },
)


def _view(r: Role, perms: list[str], users: int) -> Row:
    return {
        "cCode": r.code,
        "cDescFR": r.desc_fr,
        "cDescEN": r.desc_en,
        "lAdmin": bool(r.is_admin),
        "lActive": bool(r.active),
        "iUsers": users,
        "iScreens": len(P.SCREENS) if r.is_admin else len({p.split(":")[0] for p in perms if p.endswith(":view")}),
        "permissions": P.all_permissions() if r.is_admin else P.clean(perms),
    }


class RoleService:
    def __init__(self, username: Callable[[], str]):
        self.username = username

    # ---------------------------------------------------------------- reading
    @staticmethod
    def _perms(s) -> dict[str, list[str]]:
        out: dict[str, list[str]] = {}
        for code, perm in s.execute(select(RolePermission.role_code, RolePermission.permission)):
            out.setdefault(code, []).append(perm)
        return out

    @staticmethod
    def _users(s) -> dict[str, int]:
        return dict(s.execute(select(User.role, func.count()).group_by(User.role)).all())  # type: ignore[arg-type]

    def rows(self) -> list[Row]:
        with database.session_scope() as s:
            perms, users = self._perms(s), self._users(s)
            return [
                _view(r, perms.get(r.code, []), users.get(r.code, 0))
                for r in s.scalars(select(Role).order_by(Role.code))
            ]

    def _find(self, s, code: str) -> Role:
        role = s.scalar(select(Role).where(func.upper(Role.code) == text(code).upper()))
        if role is None:
            raise AppError("not_found", status=404)
        return role

    def get(self, code: str) -> Row:
        with database.session_scope() as s:
            role = self._find(s, code)
            perms = list(s.scalars(select(RolePermission.permission).where(RolePermission.role_code == role.code)))
            users = [
                {"id": u.id, "username": u.username, "name": u.name, "active": u.active}
                for u in s.scalars(select(User).where(User.role == role.code).order_by(User.username))
            ]
            row = _view(role, perms, len(users))
            row["users"] = users
            return row

    def history(self, code: str) -> list[Row]:
        with database.session_scope() as s:
            rows = s.scalars(
                select(RoleHistory)
                .where(func.upper(RoleHistory.role_code) == text(code).upper())
                .order_by(RoleHistory.at.desc(), RoleHistory.id.desc())
            )
            return [
                {
                    "dAt": h.at.isoformat() if h.at else None,
                    "cUser": h.username,
                    "cChange": h.change,
                    "details": h.details or {},
                }
                for h in rows
            ]

    def catalog(self) -> list[Row]:
        """The screens a role can be given, in menu order, with their actions."""
        return [{"cScreen": s.key, "cModule": s.module, "actions": list(s.actions)} for s in P.SCREENS]

    # ---------------------------------------------------------------- changes
    def _log(self, s, code: str, change: str, details: Row) -> None:
        s.add(
            RoleHistory(
                at=datetime.now().astimezone(), role_code=code, username=self.username(), change=change, details=details
            )
        )

    @staticmethod
    def _fields(p: Row, existing: Role | None = None) -> Row:
        row = {
            "desc_fr": text(p.get("cDescFR")) if "cDescFR" in p or existing is None else existing.desc_fr,
            "desc_en": text(p.get("cDescEN")) if "cDescEN" in p or existing is None else existing.desc_en,
            "active": (
                p.get("lActive", True) in (True, 1, "1", "true", "on")
                if "lActive" in p or existing is None
                else existing.active
            ),
        }
        if not row["desc_fr"]:
            raise AppError("required", "cDescFR")
        return row

    @staticmethod
    def _wanted(p: Row) -> list[str]:
        perms = p.get("permissions") or []
        if not isinstance(perms, list):
            raise AppError("invalid_body", "permissions")
        unknown = sorted({str(x) for x in perms} - set(P.all_permissions()))
        if unknown:
            raise AppError("invalid_body", "permissions", detail=", ".join(unknown))
        wanted = P.clean(str(x) for x in perms)
        # an action without the view of its screen would show nothing: the view comes with it
        views = {p.split(":")[0] + ":view" for p in wanted}
        return P.clean([*wanted, *views])

    def create(self, p: Row) -> Row:
        code = text(p.get("cCode")).upper()
        if not code:
            raise AppError("required", "cCode")
        if not CODE.match(code):
            raise AppError("bad_code", "cCode")
        fields = self._fields(p)
        copy_from = text(p.get("cCopyFrom"))
        with database.session_scope() as s:
            if s.scalar(select(Role.code).where(func.upper(Role.code) == code)):
                raise AppError("duplicate", "cCode", status=409)
            src = self._find(s, copy_from) if copy_from else None
            if src is not None and "permissions" not in p:  # copied as is (the screen sends what was adjusted)
                perms = (
                    P.all_permissions()
                    if src.is_admin
                    else P.clean(
                        s.scalars(select(RolePermission.permission).where(RolePermission.role_code == src.code))
                    )
                )
            else:
                perms = self._wanted(p)
            s.add(Role(code=code, is_admin=False, **fields))
            s.flush()
            s.add_all(RolePermission(role_code=code, permission=x) for x in perms)
            details: Row = {"permissions": len(perms)}
            if src is not None:
                details["copiedFrom"] = src.code
            self._log(s, code, "created", details)
        return self.get(code)

    def update(self, code: str, p: Row) -> Row:
        with database.session_scope() as s:
            role = self._find(s, code)
            if role.is_admin:
                raise AppError("admin_role", status=409)
            fields = self._fields(p, role)
            names = {"desc_fr": "cDescFR", "desc_en": "cDescEN", "active": "lActive"}
            changed = {names[k]: [getattr(role, k), v] for k, v in fields.items() if getattr(role, k) != v}
            for k, v in fields.items():
                setattr(role, k, v)
            if changed:
                self._log(s, role.code, "updated", changed)
            if "permissions" in p:
                before = set(s.scalars(select(RolePermission.permission).where(RolePermission.role_code == role.code)))
                after = set(self._wanted(p))
                added, removed = P.clean(after - before), P.clean(before - after)
                if added or removed:
                    s.execute(delete(RolePermission).where(RolePermission.role_code == role.code))
                    s.add_all(RolePermission(role_code=role.code, permission=x) for x in P.clean(after))
                    self._log(s, role.code, "permissions", {"added": added, "removed": removed})
            code = role.code
        return self.get(code)

    def delete(self, code: str) -> None:
        with database.session_scope() as s:
            role = self._find(s, code)
            if role.is_admin:
                raise AppError("admin_role", status=409)
            if s.scalar(select(func.count()).select_from(User).where(User.role == role.code)):
                raise AppError("in_use", status=409)
            self._log(s, role.code, "deleted", {"cDescFR": role.desc_fr})
            s.delete(role)

    # ---------------------------------------------------------------- demo data
    def load_demo(self, _data: Row | None = None) -> None:
        """Puts the example roles back as in the demo (other roles are left alone)."""
        with database.session_scope() as s:
            for d in DEMO_ROLES:
                role = s.get(Role, d["cCode"])
                if role is None:
                    role = Role(code=d["cCode"], is_admin=False)
                    s.add(role)
                role.desc_fr, role.desc_en, role.active = d["cDescFR"], d["cDescEN"], True
                s.flush()
                before = set(s.scalars(select(RolePermission.permission).where(RolePermission.role_code == role.code)))
                after = set(P.clean(d["permissions"]))
                if before == after:
                    continue
                s.execute(delete(RolePermission).where(RolePermission.role_code == role.code))
                s.add_all(RolePermission(role_code=role.code, permission=x) for x in P.clean(after))
                self._log(s, role.code, "demo", {"added": P.clean(after - before), "removed": P.clean(before - after)})
