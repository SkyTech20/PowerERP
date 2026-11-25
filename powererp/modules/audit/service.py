"""The audit trail (step 4 of the SCOR / ISO plan: ISO 27001 8.15 logging, 8.5 secure authentication; Quebec Law 25).

Two kinds of events, kept in the table audit_log, each in its own transaction (an event is kept even when the
request fails, and is never changed afterwards):
- security: login_ok, login_failed, locked (the account is locked after too many failed logins), login_locked
  (a login refused while locked), unlocked (by the administrator), logout, password_changed, password_failed,
  access_denied (a call refused by the role);
- change: every call that changes data (POST / PUT / PATCH / DELETE answered with a success), with the screen of the
  permission it needs, the action (create, edit, delete, post, release...), the record and what was sent
  (passwords and secrets masked, long values cut). The calls that only read or calculate (their permission is the
  view of the screen: calc, check, preview) are not changes and are not kept.
The administrator reads it in Administration > Audit log (filters by date, user, kind, event, screen, text) and
exports it to a spreadsheet.
"""

from __future__ import annotations

import io
import json
from datetime import date, datetime, timedelta, timezone
from typing import Any

from sqlalchemy import Select, Text, cast, func, or_, select

from powererp import database
from powererp.core import permissions
from powererp.core.values import text
from powererp.models import AuditEvent

Row = dict[str, Any]
KINDS = ("security", "change")
SECURITY_EVENTS = (
    "login_ok",
    "login_failed",
    "locked",
    "login_locked",
    "unlocked",
    "logout",
    "password_changed",
    "password_failed",
    "access_denied",
)
SECRET_KEYS = ("password", "current", "secret", "token", "apikey", "api_key")
MAX_VALUE = 300  # characters kept of one value sent
MAX_ITEMS = 50  # lines kept of a list sent
RECORD_KEYS = ("iNo", "cInvoiceNo", "cPO", "NoReception", "cCode", "cProduct", "username", "id")
# The administrator's routes: the screen they belong to (their permission is the administrator role)
ADMIN_SCREENS = {
    "auth.users_collection": "admin.users",
    "auth.users_item": "admin.users",
    "auth.user_unlock": "admin.users",
    "auth.roles_collection": "admin.roles",
    "auth.roles_item": "admin.roles",
    "backup.backup_settings": "admin.backups",
    "backup.backup_run": "admin.backups",
    "sales.company_save": "admin.settings",
    "system.reset": "admin.settings",
    "system.clear": "admin.settings",
}
# Writes that are not changes of data (the language of the screens) or have their own security event
NOT_CHANGES = {"auth.login", "auth.logout", "auth.set_lang", "auth.change_password", "auth.user_unlock"}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def mask(value: Any, depth: int = 0) -> Any:
    """What was sent, fit to keep: secrets masked, long texts and lists cut."""
    if isinstance(value, dict):
        return {
            k: ("***" if any(s in str(k).lower() for s in SECRET_KEYS) and v else mask(v, depth + 1))
            for k, v in list(value.items())[:MAX_ITEMS]
        }
    if isinstance(value, list):
        out = [mask(v, depth + 1) for v in value[:MAX_ITEMS]]
        return out + ([f"... {len(value) - MAX_ITEMS} more"] if len(value) > MAX_ITEMS else [])
    if isinstance(value, str) and len(value) > MAX_VALUE:
        return value[:MAX_VALUE] + "..."
    return value


def screen_action(endpoint: str | None, method: str, args: dict) -> tuple[str, str] | None:
    """The screen and the action of a call (None: not a change to keep)."""
    if not endpoint or endpoint in NOT_CHANGES:
        return None
    action = text(args.get("action") or args.get("step"))
    if endpoint in ADMIN_SCREENS:
        verb = endpoint.split(".")[-1] if endpoint.startswith("system.") or endpoint == "backup.backup_run" else ""
        return ADMIN_SCREENS[endpoint], action or verb or permissions.METHOD_ACTION.get(method, "edit")
    needed = permissions.required(endpoint, method, args)
    if needed:
        screen, _, perm = needed[0].partition(":")
        if perm == "view":
            return None  # calc, check, preview: nothing changes
        return screen, action or perm
    if endpoint in permissions.OPEN_ENDPOINTS:
        return None
    return endpoint.split(".")[0], action or permissions.METHOD_ACTION.get(method, "edit")  # e.g. PowerWARE


def record_of(args: dict, answer: Any) -> str:
    """The record a change is about: the keys of its address, else the key of the record the call answered."""
    keys = [text(v) for k, v in args.items() if k not in ("action", "step")]
    if keys:
        return "/".join(keys)
    if isinstance(answer, dict):
        for k in RECORD_KEYS:
            if text(answer.get(k)):
                return text(answer[k])
    return ""


class AuditService:
    def record(
        self,
        kind: str,
        event: str,
        username: str = "",
        *,
        screen: str = "",
        method: str = "",
        path: str = "",
        record: str = "",
        status: int = 0,
        ip: str = "",
        details: dict | None = None,
    ) -> None:
        """Keep one event (own transaction)."""
        with database.session_scope() as s:
            s.add(
                AuditEvent(
                    username=username[:80],
                    kind=kind,
                    event=event[:40],
                    screen=screen[:60],
                    method=method,
                    path=path[:500],
                    record=record[:200],
                    status=status,
                    ip=ip[:64],
                    details=json.loads(json.dumps(mask(details or {}), default=str)),
                )
            )

    # ---------------------------------------------------------------- reading
    @staticmethod
    def _query(f: dict) -> Select:
        q = select(AuditEvent)
        start, end = _day(f.get("from")), _day(f.get("to"))
        if start:
            q = q.where(AuditEvent.at >= datetime.combine(start, datetime.min.time(), timezone.utc))
        if end:
            q = q.where(AuditEvent.at < datetime.combine(end + timedelta(days=1), datetime.min.time(), timezone.utc))
        if text(f.get("user")):
            q = q.where(func.lower(AuditEvent.username) == text(f["user"]).lower())
        if text(f.get("kind")) in KINDS:
            q = q.where(AuditEvent.kind == f["kind"])
        if text(f.get("event")):
            q = q.where(AuditEvent.event == text(f["event"]))
        if text(f.get("screen")):
            q = q.where(AuditEvent.screen == text(f["screen"]))
        if text(f.get("q")):
            like = f"%{text(f['q']).lower()}%"
            q = q.where(
                or_(
                    func.lower(AuditEvent.record).like(like),
                    func.lower(AuditEvent.path).like(like),
                    func.lower(AuditEvent.username).like(like),
                    func.lower(cast(AuditEvent.details, Text)).like(like),
                )
            )
        return q

    def page(self, f: dict) -> Row:
        """The events (newest first) matching the filters, one page (size 50 by default, 500 at most)."""
        try:
            size = max(1, min(int(f.get("size") or 50), 500))
            page = max(1, int(f.get("page") or 1))
        except ValueError:
            size, page = 50, 1
        q = self._query(f)
        with database.session_scope() as s:
            total = s.scalar(select(func.count()).select_from(q.subquery())) or 0
            rows = s.scalars(
                q.order_by(AuditEvent.at.desc(), AuditEvent.id.desc()).limit(size).offset((page - 1) * size)
            )
            items = [view(e) for e in rows]
        return {"total": total, "page": page, "size": size, "items": items}

    def filters(self) -> Row:
        """The user names and the events found in the log, by kind (the lists of the screen's filters)."""
        with database.session_scope() as s:
            users = sorted(s.scalars(select(AuditEvent.username).distinct()), key=str.lower)
            found = s.execute(select(AuditEvent.kind, AuditEvent.event).distinct()).all()
        events = {k: sorted({e for kind, e in found if kind == k}) for k in KINDS}
        events["security"] = [e for e in SECURITY_EVENTS if e in events["security"]]
        return {"users": users, "events": events}

    def export(self, f: dict, lang: str = "en") -> bytes:
        """The events matching the filters as a spreadsheet (.xlsx), newest first, 50 000 at most."""
        from openpyxl import Workbook
        from openpyxl.styles import Font

        fr = lang == "fr"
        head = (
            [
                "Date (UTC)",
                "Utilisateur",
                "Type",
                "Événement",
                "Écran",
                "Méthode",
                "Adresse",
                "Fiche",
                "Résultat",
                "IP",
                "Détails",
            ]
            if fr
            else [
                "Date (UTC)",
                "User",
                "Kind",
                "Event",
                "Screen",
                "Method",
                "Path",
                "Record",
                "Status",
                "IP",
                "Details",
            ]
        )
        wb = Workbook()
        ws = wb.active
        ws.title = "Journal d'audit" if fr else "Audit log"
        ws.append(head)
        for cell in ws[1]:
            cell.font = Font(bold=True)
        q = self._query(f).order_by(AuditEvent.at.desc(), AuditEvent.id.desc()).limit(50000)
        with database.session_scope() as s:
            for e in s.scalars(q):
                ws.append(
                    [
                        e.at.astimezone(timezone.utc).replace(tzinfo=None),
                        e.username,
                        e.kind,
                        e.event,
                        e.screen,
                        e.method,
                        e.path,
                        e.record,
                        e.status,
                        e.ip,
                        json.dumps(e.details, ensure_ascii=False) if e.details else "",
                    ]
                )
        for col, width in zip("ABCDEFGHIJK", (20, 16, 10, 16, 20, 8, 40, 20, 8, 16, 80), strict=True):
            ws.column_dimensions[col].width = width
        ws.freeze_panes = "A2"
        buf = io.BytesIO()
        wb.save(buf)
        return buf.getvalue()


def view(e: AuditEvent) -> Row:
    return {
        "id": e.id,
        "at": e.at.astimezone(timezone.utc).isoformat(timespec="seconds"),
        "username": e.username,
        "kind": e.kind,
        "event": e.event,
        "screen": e.screen,
        "method": e.method,
        "path": e.path,
        "record": e.record,
        "status": e.status,
        "ip": e.ip,
        "details": e.details or {},
    }


def _day(value: Any) -> date | None:
    try:
        return date.fromisoformat(text(value)[:10]) if text(value) else None
    except ValueError:
        return None
