"""Quebec Law 25 (item 9 of the SCOR / ISO plan): the personal information the ERP keeps, a person's file,
its export and its anonymization, the retention rule and the privacy policy.

The persons the ERP knows (kind:ref):
- user:<id>        a user of the ERP (Administration > Users): name, e-mail, user name, and where the user name was
                   written (documents released / posted / signed, history, audit log with the IP address);
- former:<name>    a user name still written in the documents or the audit log, whose user was deleted;
- contact:<id>     a contact of a customer (name, title, phone, e-mail);
- shipto:<id>      the contact of a ship-to address of a customer (name, phone);
- warehouse:<id>   the manager of a warehouse (name, phone, e-mail).
The companies (customers, suppliers) are businesses, not persons: they are not in this list.

Anonymize (Law 25 s. 23: destroy or anonymize once the purpose is over) cannot be undone:
- a user (inactive first, never oneself): the user name becomes anon-<id> everywhere it is written, the name
  "Anonymized", the e-mail and the IP addresses of the audit log are emptied, the password can no longer be used;
- a contact is removed from the customer; a ship-to contact and a warehouse manager are emptied;
- in what the audit log kept of the changes, the values equal to the person's name, e-mail or phone are replaced.
The documents (invoices, orders, lots) stay: only who did them is no longer a person.
"""

from __future__ import annotations

import io
import json
import secrets
from collections.abc import Callable
from datetime import date, datetime, timedelta, timezone
from typing import Any

from sqlalchemy import text as sql

from powererp import database
from powererp.core.errors import AppError, NotFound
from powererp.core.values import text

Row = dict[str, Any]
KINDS = ("user", "former", "contact", "shipto", "warehouse")
ANON_NAME = "Anonymized"
ANON_PREFIX = "anon-"
POLICY_KEY = "privacy.policy"
POLICY_FIELDS = ("cOfficerName", "cOfficerTitle", "cOfficerEmail", "cHosting", "cRegion", "iRetentionMonths")
DEFAULT_RETENTION = 24  # months
MAX_EVENTS = 50000  # audit events in an export

# Every column where the ERP writes the user name of who did something (tests/test_privacy.py checks that a new
# table with such a column is added here).
USER_COLUMNS: tuple[tuple[str, str], ...] = (
    ("audit_log", "username"),
    ("role_history", "username"),
    ("lot_status", "user"),
    ("lot_status_history", "user"),
    ("nonconformances", "user"),
    ("nonconformances", "closed_by"),
    ("nonconformances_history", "user"),
    ("production_orders", "user"),
    ("production_orders", "released_by"),
    ("production_orders", "completed_by"),
    ("production_orders", "closed_by"),
    ("production_orders_history", "user"),
    ("production_orders_issues", "user"),
    ("production_orders_outputs", "user"),
    ("production_orders_records", "user"),
    ("production_orders_records", "second_user"),
    ("receptions", "received_by"),
    ("receptions", "stock_posted_by"),
    ("recipes", "submitted_by"),
    ("recipes", "approved_by"),
    ("recipes_history", "user"),
    ("sales_invoices", "user"),
    ("sales_invoices", "posted_by"),
    ("stock_counts", "user"),
    ("stock_movements", "user"),
)
# The record each document table shows in the person's file (its number / code)
DOC_KEYS = {
    "lot_status": "product || ' / ' || lot",
    "nonconformances": "no::text",
    "production_orders": "no::text",
    "receptions": "reception_no::text",
    "recipes": "product || ' ' || revision::text",
    "sales_invoices": "COALESCE(NULLIF(invoice_no, ''), no::text)",
    "stock_counts": "no::text",
    "stock_movements": "no::text",
}


def _q(name: str) -> str:
    return f'"{name}"'


def _iso(v: Any) -> str | None:
    if v is None:
        return None
    if isinstance(v, datetime):
        return v.astimezone(timezone.utc).isoformat(timespec="seconds")
    return v.isoformat() if isinstance(v, date) else text(v)


def _like(q: str) -> str:
    return "%" + q.lower().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"


def _re(value: str) -> str:
    """The value as a literal in a PostgreSQL regular expression."""
    return "".join("\\" + ch if not ch.isalnum() else ch for ch in value)


def _scrub(value: Any, find: set[str], new: str) -> tuple[Any, bool]:
    """The JSON value with every string equal (any case) to one of `find` replaced by `new`."""
    if isinstance(value, dict):
        out, hit = {}, False
        for k, v in value.items():
            out[k], h = _scrub(v, find, new)
            hit = hit or h
        return out, hit
    if isinstance(value, list):
        pairs = [_scrub(v, find, new) for v in value]
        return [p[0] for p in pairs], any(p[1] for p in pairs)
    if isinstance(value, str) and value.strip().lower() in find:
        return new, True
    return value, False


class PrivacyService:
    def __init__(
        self,
        get_setting: Callable[[str, Any], Any],
        set_setting: Callable[[str, str], None],
        today: Callable[[], date] = date.today,
    ):
        self._get, self._set, self._today = get_setting, set_setting, today

    @staticmethod
    def _s():
        return database.current()

    # ---------------------------------------------------------------- policy
    def policy(self) -> Row:
        try:
            saved = json.loads(self._get(POLICY_KEY, "") or "{}")
        except ValueError:
            saved = {}
        out: Row = {f: text(saved.get(f)) for f in POLICY_FIELDS if f != "iRetentionMonths"}
        months = saved.get("iRetentionMonths", DEFAULT_RETENTION)
        out["iRetentionMonths"] = months if isinstance(months, int) else DEFAULT_RETENTION
        return out

    def save_policy(self, p: Row) -> Row:
        if not isinstance(p, dict):
            raise AppError("invalid_body")
        out: Row = {f: text(p.get(f))[:200] for f in POLICY_FIELDS if f != "iRetentionMonths"}
        email = out["cOfficerEmail"]
        if email and ("@" not in email or " " in email):
            raise AppError("invalid_email", "cOfficerEmail")
        try:
            months = int(text(p.get("iRetentionMonths")) or DEFAULT_RETENTION)
        except ValueError:
            raise AppError("numeric", "iRetentionMonths") from None
        if not 1 <= months <= 600:
            raise AppError("out_of_range", "iRetentionMonths")
        out["iRetentionMonths"] = months
        self._set(POLICY_KEY, json.dumps(out, ensure_ascii=False))
        return out

    # ---------------------------------------------------------------- search
    def search(self, q: str) -> list[Row]:
        """The persons whose name, user name, e-mail or phone contains q (2 characters at least)."""
        q = text(q)
        if len(q) < 2:
            return []
        like = {"q": _like(q)}
        s = self._s()
        out: list[Row] = []
        for r in s.execute(
            sql(
                "SELECT id, username, name, email, active, last_login FROM users WHERE lower(username) LIKE :q "
                "OR lower(name) LIKE :q OR lower(email) LIKE :q ORDER BY lower(name), id"
            ),
            like,
        ).mappings():
            out.append(
                self._person(
                    "user",
                    r["id"],
                    r["name"] or r["username"],
                    email=r["email"],
                    where=r["username"],
                    active=r["active"],
                    last=_iso(r["last_login"]),
                    anonymized=r["username"].startswith(ANON_PREFIX),
                )
            )
        known = {u.lower() for u in s.execute(sql("SELECT username FROM users")).scalars()}
        former: set[str] = set()
        for table, col in USER_COLUMNS:
            former.update(
                v
                for v in s.execute(
                    sql(f"SELECT DISTINCT {_q(col)} FROM {table} WHERE lower({_q(col)}) LIKE :q"), like
                ).scalars()
                if v and v.lower() not in known and not v.startswith(ANON_PREFIX)
            )
        out += [self._person("former", name, name, where=name, active=False) for name in sorted(former, key=str.lower)]
        for r in s.execute(
            sql(
                "SELECT k.id, k.name, k.title, k.phone, k.email, c.code, c.name AS cname, c.active FROM customers_contacts k "
                "JOIN customers c ON c.id = k.parent_id WHERE lower(k.name) LIKE :q OR lower(k.email) LIKE :q "
                "OR lower(k.phone) LIKE :q ORDER BY lower(k.name), k.id"
            ),
            like,
        ).mappings():
            out.append(
                self._person(
                    "contact",
                    r["id"],
                    r["name"],
                    email=r["email"],
                    phone=r["phone"],
                    where=f"{r['code']} {r['cname']}".strip(),
                    active=r["active"],
                )
            )
        for r in s.execute(
            sql(
                "SELECT a.id, a.contact, a.phone, a.code AS acode, c.code, c.name AS cname, c.active FROM customers_addresses a "
                "JOIN customers c ON c.id = a.parent_id WHERE a.contact <> '' AND (lower(a.contact) LIKE :q "
                "OR lower(a.phone) LIKE :q) ORDER BY lower(a.contact), a.id"
            ),
            like,
        ).mappings():
            out.append(
                self._person(
                    "shipto",
                    r["id"],
                    r["contact"],
                    phone=r["phone"],
                    where=f"{r['code']} {r['cname']} / {r['acode']}".strip(),
                    active=r["active"],
                )
            )
        for r in s.execute(
            sql(
                "SELECT id, code, manager, phone, email, active FROM warehouses WHERE manager <> '' AND "
                "(lower(manager) LIKE :q OR lower(email) LIKE :q OR lower(phone) LIKE :q) ORDER BY lower(manager)"
            ),
            like,
        ).mappings():
            out.append(
                self._person(
                    "warehouse",
                    r["id"],
                    r["manager"],
                    email=r["email"],
                    phone=r["phone"],
                    where=r["code"],
                    active=r["active"],
                )
            )
        return out[:200]

    @staticmethod
    def _person(kind: str, ref: Any, name: str, **kw: Any) -> Row:
        return {
            "kind": kind,
            "ref": str(ref),
            "name": name,
            "email": kw.get("email") or "",
            "phone": kw.get("phone") or "",
            "where": kw.get("where") or "",
            "active": bool(kw.get("active")),
            "lastLogin": kw.get("last"),
            "anonymized": bool(kw.get("anonymized")),
        }

    # ---------------------------------------------------------------- one person
    def _user(self, ref: str) -> Row:
        try:
            uid = int(ref)
        except ValueError:
            raise NotFound() from None
        r = (
            self._s()
            .execute(
                sql(
                    "SELECT id, username, name, email, role, lang, active, created_at, last_login FROM users "
                    "WHERE id = :id"
                ),
                {"id": uid},
            )
            .mappings()
            .first()
        )
        if r is None:
            raise NotFound()
        return dict(r)

    def _one(self, kind: str, query: str, ref: str) -> Row:
        try:
            rid = int(ref)
        except ValueError:
            raise NotFound() from None
        r = self._s().execute(sql(query), {"id": rid}).mappings().first()
        if r is None:
            raise NotFound()
        return dict(r)

    def _identity(self, kind: str, ref: str) -> tuple[Row, str]:
        """What the ERP keeps on the person itself, and the user name written in the documents ("" for a contact)."""
        if kind == "user":
            u = self._user(ref)
            profile = {
                "username": u["username"],
                "name": u["name"],
                "email": u["email"],
                "role": u["role"],
                "lang": u["lang"],
                "active": u["active"],
                "created": _iso(u["created_at"]),
                "lastLogin": _iso(u["last_login"]),
            }
            return profile, u["username"]
        if kind == "former":
            name = text(ref)
            if not name or not any(self._count(t, c, name) for t, c in USER_COLUMNS):
                raise NotFound()
            # the name and e-mail it had: from what the audit log kept of the user's creation and changes
            found: Row = {"username": name}
            for (details,) in self._s().execute(
                sql(
                    "SELECT details FROM audit_log WHERE screen = 'admin.users' "
                    "AND lower(details->'sent'->>'username') = :u ORDER BY at"
                ),
                {"u": name.lower()},
            ):
                sent = (details or {}).get("sent") or {}
                found.update({k: text(sent.get(k)) for k in ("name", "email") if text(sent.get(k))})
            return found, name
        if kind == "contact":
            r = self._one(
                kind,
                "SELECT k.name, k.title, k.phone, k.email, k.invoices, c.code AS customer, c.name AS customer_name "
                "FROM customers_contacts k JOIN customers c ON c.id = k.parent_id WHERE k.id = :id",
                ref,
            )
            return r, ""
        if kind == "shipto":
            r = self._one(
                kind,
                "SELECT a.contact AS name, a.phone, a.code AS address, a.name AS address_name, a.address1, a.city, "
                "c.code AS customer, c.name AS customer_name FROM customers_addresses a "
                "JOIN customers c ON c.id = a.parent_id WHERE a.id = :id",
                ref,
            )
            return r, ""
        if kind == "warehouse":
            r = self._one(
                kind, "SELECT manager AS name, phone, email, code AS warehouse FROM warehouses WHERE id = :id", ref
            )
            return r, ""
        raise NotFound()

    def _count(self, table: str, col: str, username: str) -> int:
        return int(
            self._s()
            .execute(sql(f"SELECT count(*) FROM {table} WHERE lower({_q(col)}) = :u"), {"u": username.lower()})
            .scalar()
            or 0
        )

    def _values(self, identity: Row, username: str) -> set[str]:
        """The values that name the person (to find and replace in what the audit log kept)."""
        found = {text(identity.get(k)).lower() for k in ("name", "email", "phone")} | {username.lower()}
        return {v for v in found if len(v) >= 3}

    def file(self, kind: str, ref: str) -> Row:
        """The person's file: what is kept on the person, where the user name is written, and the audit events."""
        if kind not in KINDS:
            raise NotFound()
        identity, username = self._identity(kind, ref)
        s = self._s()
        documents = []
        if username:
            for table, col in USER_COLUMNS:
                if table == "audit_log":
                    continue
                n = self._count(table, col, username)
                if n:
                    key = DOC_KEYS.get(table)
                    sample = (
                        list(
                            s.execute(
                                sql(
                                    f"SELECT DISTINCT {key} FROM {table} WHERE lower({_q(col)}) = :u ORDER BY 1 LIMIT 20"
                                ),
                                {"u": username.lower()},
                            ).scalars()
                        )
                        if key
                        else []
                    )
                    documents.append({"table": table, "column": col, "count": n, "records": sample})
        events = self._events(username, self._values(identity, username), MAX_EVENTS)
        return {
            "kind": kind,
            "ref": str(ref),
            "identity": {k: (_iso(v) if isinstance(v, date) else v) for k, v in identity.items()},
            "documents": documents,
            "events": len(events),
            "recentEvents": events[:20],
            "canAnonymize": self._refusal(kind, identity) is None,
            "refusal": self._refusal(kind, identity),
        }

    def _events(self, username: str, values: set[str], limit: int) -> list[Row]:
        """The audit events of the user, and the ones whose details name the person."""
        where, params = [], {}
        if username:
            where.append("lower(username) = :u")
            params["u"] = username.lower()
        for i, v in enumerate(sorted(values)):
            where.append(f"lower(details::text) LIKE :v{i} OR lower(record) = :r{i}")
            params[f"v{i}"], params[f"r{i}"] = _like(v), v
        if not where:
            return []
        rows = self._s().execute(
            sql(
                "SELECT id, at, username, kind, event, screen, method, path, record, status, ip, details FROM audit_log "
                f"WHERE {' OR '.join(where)} ORDER BY at DESC, id DESC LIMIT {int(limit)}"
            ),
            params,
        )
        return [{**dict(r), "at": _iso(r["at"])} for r in rows.mappings()]

    def _refusal(self, kind: str, identity: Row) -> str | None:
        if kind == "user":
            if text(identity.get("username")).startswith(ANON_PREFIX):
                return "already_anonymized"
            if identity.get("active"):
                return "user_active"
        return None

    # ---------------------------------------------------------------- export
    def export(self, kind: str, ref: str, fmt: str = "json", lang: str = "en") -> tuple[bytes, str, str]:
        """The person's file (Law 25 s. 27: a structured, commonly used format): JSON or a spreadsheet."""
        f = self.file(kind, ref)
        identity, username = self._identity(kind, ref)
        events = self._events(username, self._values(identity, username), MAX_EVENTS)
        data = {
            "exported": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "person": f["identity"],
            "kind": kind,
            "documents": f["documents"],
            "auditLog": events,
            "policy": self.policy(),
        }
        name = f"personal-data-{kind}-{ref}"
        if fmt != "xlsx":
            body = json.dumps(data, ensure_ascii=False, indent=2, default=str).encode()
            return body, "application/json", name + ".json"
        return (
            self._xlsx(data, lang == "fr"),
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            (name + ".xlsx"),
        )

    @staticmethod
    def _xlsx(data: Row, fr: bool) -> bytes:
        from openpyxl import Workbook
        from openpyxl.styles import Font

        wb = Workbook()
        ws = wb.active
        ws.title = "Personne" if fr else "Person"
        for k, v in data["person"].items():
            ws.append([k, "" if v is None else str(v)])
        ws.append([])
        ws.append(["Exporté le (UTC)" if fr else "Exported (UTC)", data["exported"]])
        ws.column_dimensions["A"].width, ws.column_dimensions["B"].width = 22, 50
        docs = wb.create_sheet("Documents")
        docs.append(
            ["Table", "Colonne" if fr else "Column", "Nombre" if fr else "Count", "Fiches" if fr else "Records"]
        )
        for d in data["documents"]:
            docs.append([d["table"], d["column"], d["count"], ", ".join(map(str, d["records"]))])
        log = wb.create_sheet("Journal d'audit" if fr else "Audit log")
        head = ["at", "username", "kind", "event", "screen", "method", "path", "record", "status", "ip", "details"]
        log.append(head)
        for e in data["auditLog"]:
            log.append(
                [json.dumps(e[h], ensure_ascii=False) if h == "details" else e[h] for h in head]  # type: ignore[index]
            )
        for sheet in (docs, log):
            for cell in sheet[1]:
                cell.font = Font(bold=True)
            sheet.freeze_panes = "A2"
        buf = io.BytesIO()
        wb.save(buf)
        return buf.getvalue()

    # ---------------------------------------------------------------- anonymize
    def anonymize(self, kind: str, ref: str, me: str = "") -> Row:
        if kind not in KINDS:
            raise NotFound()
        identity, username = self._identity(kind, ref)
        refusal = self._refusal(kind, identity)
        if kind == "user" and me and username.lower() == me.lower():
            refusal = "cannot_anonymize_self"
        if refusal:
            raise AppError(refusal, status=409)
        s = self._s()
        values = self._values(identity, username)
        new_name = f"{ANON_PREFIX}{ref}" if kind == "user" else ANON_NAME
        if kind == "former":
            new_name = f"{ANON_PREFIX}{secrets.token_hex(4)}"
        changed = 0
        if username:
            for table, col in USER_COLUMNS:
                params = {"u": username.lower(), "n": new_name}
                extra = ", ip = ''" if table == "audit_log" else ""
                changed += (
                    s.execute(
                        sql(f"UPDATE {table} SET {_q(col)} = :n{extra} WHERE lower({_q(col)}) = :u"), params
                    ).rowcount
                    or 0
                )
        if kind == "user":
            s.execute(
                sql(
                    "UPDATE users SET username = :n, name = :name, email = '', active = false, password_hash = :pw, "
                    "failed_logins = 0, locked_until = NULL WHERE id = :id"
                ),
                {"n": new_name, "name": ANON_NAME, "pw": "!" + secrets.token_hex(16), "id": int(ref)},
            )
        elif kind == "contact":
            s.execute(sql("DELETE FROM customers_contacts WHERE id = :id"), {"id": int(ref)})
        elif kind == "shipto":
            s.execute(sql("UPDATE customers_addresses SET contact = '', phone = '' WHERE id = :id"), {"id": int(ref)})
        elif kind == "warehouse":
            s.execute(
                sql("UPDATE warehouses SET manager = '', phone = '', email = '' WHERE id = :id"), {"id": int(ref)}
            )
        changed += self._scrub_log(values, new_name)
        return {"ok": True, "kind": kind, "ref": str(ref), "name": new_name, "changed": changed}

    def _scrub_log(self, values: set[str], new: str) -> int:
        """Replace the person's name, e-mail and phone in what the audit log kept of the changes."""
        if not values:
            return 0
        s = self._s()
        n = 0
        for v in values:  # the record of the change (e.g. the user created), the address called
            n += (
                s.execute(sql("UPDATE audit_log SET record = :n WHERE lower(record) = :v"), {"n": new, "v": v}).rowcount
                or 0
            )
            n += (
                s.execute(
                    sql("UPDATE audit_log SET path = regexp_replace(path, :re, :n, 'gi') WHERE lower(path) LIKE :like"),
                    {"re": "(?<![a-z0-9])" + _re(v) + "(?![a-z0-9])", "n": new, "like": _like(v)},
                ).rowcount
                or 0
            )
        where = " OR ".join(f"lower(details::text) LIKE :v{i}" for i in range(len(values)))
        params = {f"v{i}": _like(v) for i, v in enumerate(sorted(values))}
        for rid, details in s.execute(sql(f"SELECT id, details FROM audit_log WHERE {where}"), params).all():
            fixed, hit = _scrub(details, values, new)
            if hit:
                s.execute(
                    sql("UPDATE audit_log SET details = CAST(:d AS jsonb) WHERE id = :id"),
                    {"d": json.dumps(fixed, ensure_ascii=False), "id": rid},
                )
                n += 1
        return n

    # ---------------------------------------------------------------- retention
    def due(self) -> Row:
        """The persons kept longer than the retention rule: inactive users without activity for N months, and the
        contacts of inactive customers without an invoice for N months."""
        months = self.policy()["iRetentionMonths"]
        limit = self._today() - timedelta(days=round(months * 30.44))
        cut = datetime.combine(limit, datetime.min.time(), timezone.utc)
        s = self._s()
        out: list[Row] = []
        for r in s.execute(
            sql(
                "SELECT u.id, u.username, u.name, u.email, GREATEST(u.last_login, u.created_at, "
                "(SELECT max(at) FROM audit_log a WHERE lower(a.username) = lower(u.username))) AS last "
                "FROM users u WHERE NOT u.active AND u.username NOT LIKE 'anon-%' ORDER BY lower(u.name)"
            )
        ).mappings():
            if r["last"] is None or r["last"] < cut:
                out.append(
                    self._person(
                        "user",
                        r["id"],
                        r["name"] or r["username"],
                        email=r["email"],
                        where=r["username"],
                        last=_iso(r["last"]),
                    )
                )
        stale = (
            "SELECT c.id FROM customers c WHERE NOT c.active AND NOT EXISTS (SELECT 1 FROM sales_invoices i "
            "WHERE i.customer = c.code AND i.date >= :d)"
        )
        for r in s.execute(
            sql(
                "SELECT k.id, k.name, k.email, k.phone, c.code, c.name AS cname FROM customers_contacts k "
                f"JOIN customers c ON c.id = k.parent_id WHERE c.id IN ({stale}) ORDER BY c.code, k.line_no"
            ),
            {"d": limit},
        ).mappings():
            out.append(
                self._person(
                    "contact",
                    r["id"],
                    r["name"],
                    email=r["email"],
                    phone=r["phone"],
                    where=f"{r['code']} {r['cname']}",
                )
            )
        for r in s.execute(
            sql(
                "SELECT a.id, a.contact, a.phone, a.code AS acode, c.code, c.name AS cname FROM customers_addresses a "
                f"JOIN customers c ON c.id = a.parent_id WHERE a.contact <> '' AND c.id IN ({stale}) "
                "ORDER BY c.code, a.line_no"
            ),
            {"d": limit},
        ).mappings():
            out.append(
                self._person(
                    "shipto",
                    r["id"],
                    r["contact"],
                    phone=r["phone"],
                    where=f"{r['code']} {r['cname']} / {r['acode']}",
                )
            )
        return {"months": months, "before": limit.isoformat(), "items": out}

    def apply_retention(self, me: str = "") -> Row:
        """Anonymize every person the retention rule lists."""
        items = self.due()["items"]
        for p in items:
            self.anonymize(p["kind"], p["ref"], me)
        return {"ok": True, "anonymized": len(items)}
