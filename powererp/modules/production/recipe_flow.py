"""Versions and approval of the recipes (P10).

draft --submit--> in_review --approve--> approved --obsolete--> obsolete
                       \\--reject (comment)--> draft
- Only a draft can be edited or deleted; an approved version is frozen: a change is a new version
  ("new version from", any status), which starts as a draft with the next revision letter.
- Approving needs administrator rights and at least one operation. The approved version becomes the product's
  default (the one new production orders take); the previous default stays approved but is no longer the default.
- current(product, day): the default approved version valid that day (effective from / to), else the latest
  approved one valid that day.
- Every change of status is kept in the history: when, who, from, to, comment.
- compare(a, b): what changed between two versions: header fields, materials, outputs, operations and steps.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import date, datetime
from typing import Any

from powererp.core.errors import AppError
from powererp.core.values import text
from powererp.modules.common.forms import Row

from .recipes import RecipeService

HEADER_FIELDS = (
    "cDescFR",
    "cDescEN",
    "cProcessType",
    "dBaseQty",
    "cUOM",
    "dMinBatch",
    "dMaxBatch",
    "dYieldPct",
    "dEffectiveFrom",
    "dEffectiveTo",
)
# how the lines of each list are matched between two versions
LINE_KEYS: dict[str, Callable[[Row], Any]] = {
    "materials": lambda r: r["cComponent"],
    "outputs": lambda r: r["cProduct"],
    "operations": lambda r: r["iOpSeq"],
    "steps": lambda r: (r["iOpSeq"], r["iStep"]),
}


def next_revision(existing: list[str]) -> str:
    """A -> B, Z -> AA, 1 -> 2: the revision after the highest one."""
    if not existing:
        return "A"
    if all(r.isdigit() for r in existing):
        return str(max(int(r) for r in existing) + 1)
    last = max(existing, key=lambda r: (len(r), r))
    chars = list(last)
    i = len(chars) - 1
    while i >= 0:
        if chars[i] == "Z":
            chars[i] = "A"
            i -= 1
        elif chars[i].isalpha():
            chars[i] = chr(ord(chars[i]) + 1)
            return "".join(chars)
        else:
            return last + "A"
    return "A" + "".join(chars)


class RecipeFlow:
    """The approval flow on top of RecipeService (the rules of a recipe stay there)."""

    def __init__(self, recipes: RecipeService, username: Callable[[], str], is_admin: Callable[[], bool]):
        self.recipes = recipes
        self.username = username
        self.is_admin = is_admin

    # ---------------------------------------------------------- status changes
    def _move(
        self, product: str, revision: str, allowed_from: tuple[str, ...], to: str, action: str, comment: str = ""
    ) -> Row:
        row = self.recipes.get(product, revision)
        if row["cStatus"] not in allowed_from:
            raise AppError("invalid_status", "cStatus", status=409, detail=f"{row['cStatus']} -> {to}")
        row.setdefault("history", []).append(
            {
                "dAt": datetime.now().isoformat(timespec="seconds"),
                "cUser": self.username(),
                "cAction": action,
                "cFrom": row["cStatus"],
                "cTo": to,
                "cComment": text(comment),
            }
        )
        row["cStatus"] = to
        return row

    def _need_admin(self) -> None:
        if not self.is_admin():
            raise AppError("forbidden", status=403)

    def submit(self, product: str, revision: str, comment: str = "") -> Row:
        row = self._move(product, revision, ("draft",), "in_review", "submit", comment)
        if not row.get("operations"):
            raise AppError("no_operations", "operations")
        row["cSubmittedBy"] = self.username()
        self.recipes.repo.update(row)
        return row

    def reject(self, product: str, revision: str, comment: str) -> Row:
        self._need_admin()
        if not text(comment):
            raise AppError("required", "cComment")  # say what to fix
        row = self._move(product, revision, ("in_review",), "draft", "reject", comment)
        self.recipes.repo.update(row)
        return row

    def approve(self, product: str, revision: str, comment: str = "") -> Row:
        self._need_admin()
        row = self._move(product, revision, ("in_review",), "approved", "approve", comment)
        row["cApprovedBy"] = self.username()
        row["dApprovedAt"] = datetime.now().isoformat(timespec="seconds")
        row["lDefault"] = True
        for other in self.versions(row["cProduct"]):
            if other["cRevision"] != row["cRevision"] and other.get("lDefault"):
                other["lDefault"] = False
                self.recipes.repo.update(other)
        self.recipes.repo.update(row)
        return row

    def obsolete(self, product: str, revision: str, comment: str = "") -> Row:
        self._need_admin()
        row = self._move(product, revision, ("approved",), "obsolete", "obsolete", comment)
        row["lDefault"] = False
        self.recipes.repo.update(row)
        return row

    def make_default(self, product: str, revision: str) -> Row:
        self._need_admin()
        row = self.recipes.get(product, revision)
        if row["cStatus"] != "approved":
            raise AppError("invalid_status", "cStatus", status=409)
        for other in self.versions(row["cProduct"]):
            if other.get("lDefault") != (other["cRevision"] == row["cRevision"]):
                other["lDefault"] = other["cRevision"] == row["cRevision"]
                self.recipes.repo.update(other)
        return self.recipes.get(product, revision)

    # ---------------------------------------------------------- versions
    def versions(self, product: str) -> list[Row]:
        return [r for r in self.recipes.repo.all() if r["cProduct"].upper() == product.upper()]

    def new_version(self, product: str, revision: str, new_revision: str = "", reason: str = "") -> Row:
        """A draft copy of a version (any status), with the next revision letter unless one is given."""
        src = self.recipes.get(product, revision)
        rev = text(new_revision).upper() or next_revision([r["cRevision"] for r in self.versions(src["cProduct"])])
        payload = {
            k: v
            for k, v in src.items()
            if k not in ("cStatus", "lDefault", "cSubmittedBy", "cApprovedBy", "dApprovedAt", "history")
        }
        payload.update({"cRevision": rev, "cChangeReason": text(reason), "dEffectiveFrom": "", "dEffectiveTo": ""})
        row = self.recipes.create(payload)
        row["history"] = [
            {
                "dAt": datetime.now().isoformat(timespec="seconds"),
                "cUser": self.username(),
                "cAction": "copy",
                "cFrom": f"{src['cRevision']} ({src['cStatus']})",
                "cTo": "draft",
                "cComment": text(reason),
            }
        ]
        self.recipes.repo.update(row)
        return row

    def current(self, product: str, day: date | None = None) -> Row | None:
        """The version new orders use that day: the default approved one valid that day, else the latest approved."""
        day_s = (day or date.today()).isoformat()

        def valid(r: Row) -> bool:
            return (not r.get("dEffectiveFrom") or r["dEffectiveFrom"] <= day_s) and (
                not r.get("dEffectiveTo") or day_s <= r["dEffectiveTo"]
            )

        approved = [r for r in self.versions(product) if r["cStatus"] == "approved" and valid(r)]
        if not approved:
            return None
        defaults = [r for r in approved if r.get("lDefault")]
        return defaults[0] if defaults else max(approved, key=lambda r: r.get("dApprovedAt") or "")

    # ---------------------------------------------------------- comparison
    def compare(self, product: str, a: str, b: str) -> Row:
        """What changed from version a to version b."""
        ra, rb = self.recipes.get(product, a), self.recipes.get(product, b)
        header = [
            {"cField": f, "cFrom": text(ra.get(f)), "cTo": text(rb.get(f))}
            for f in HEADER_FIELDS
            if text(ra.get(f)) != text(rb.get(f))
        ]
        lists = {}
        for key, ident in LINE_KEYS.items():
            old = {ident(x): x for x in ra.get(key, [])}
            new = {ident(x): x for x in rb.get(key, [])}
            changes: list[Row] = []
            for k in sorted(set(old) | set(new), key=str):
                if k not in new:
                    changes.append({"cKey": _key_text(k), "cChange": "removed", "fields": []})
                elif k not in old:
                    changes.append({"cKey": _key_text(k), "cChange": "added", "fields": []})
                else:
                    fields = [
                        {"cField": f, "cFrom": text(old[k].get(f)), "cTo": text(new[k].get(f))}
                        for f in new[k]
                        if text(old[k].get(f)) != text(new[k].get(f))
                    ]
                    if fields:
                        changes.append({"cKey": _key_text(k), "cChange": "changed", "fields": fields})
            lists[key] = changes
        return {"cProduct": ra["cProduct"], "cFrom": ra["cRevision"], "cTo": rb["cRevision"], "header": header, **lists}


def _key_text(k: Any) -> str:
    return "/".join(str(x) for x in k) if isinstance(k, tuple) else str(k)
