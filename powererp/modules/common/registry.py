"""Registries that let modules work together without importing each other (dependency inversion).

ReferenceRegistry: before a record is deleted, the modules that point to it say whether it is still used.
    references.register("tax_group", lambda code: products.uses_tax_group(code))
    references.check("tax_group", "QC")     # 409 in_use when a checker says yes
LookupRegistry: the short code / label lists of the screens' select fields (/api/lookups/<kind>).
DashboardRegistry: the figures each module adds to the dashboard (/api/summary).
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable

from powererp.core.errors import AppError

Lookup = Callable[[], tuple[list[dict], int]]


class ReferenceRegistry:
    def __init__(self) -> None:
        self._checkers: dict[str, list[Callable[[str], bool]]] = defaultdict(list)

    def register(self, kind: str, is_used: Callable[[str], bool]) -> None:
        self._checkers[kind].append(is_used)

    def is_used(self, kind: str, code: str) -> bool:
        return any(check(code) for check in self._checkers[kind])

    def check(self, kind: str, code: str) -> None:
        if self.is_used(kind, code):
            raise AppError("in_use", status=409)


class LookupRegistry(dict):
    """kind -> function returning (rows [{"code", "label"}], default limit)."""

    def register(self, kind: str, fn: Lookup) -> None:
        self[kind] = fn


def label_lookup(service, fr_fields: tuple[str, ...], en_fields: tuple[str, ...] | None = None, keep=None, limit=200):
    """A lookup of a master file: code + label in the language of the screen (?lang=fr|en, French by default)."""
    from flask import request

    from powererp.core.values import text

    en_fields = en_fields or fr_fields

    def fn():
        fields = fr_fields if (request.args.get("lang") or "fr") != "en" else en_fields
        rows = []
        for r in service.repo.all(lines=False):
            if keep and not keep(r):
                continue
            rows.append({"code": r["cCode"], "label": " · ".join(text(r.get(f)) for f in fields if text(r.get(f)))})
        return rows, limit

    return fn


class SeedRegistry:
    """The tables seeded with the demo data, reset by /api/reset and emptied by /api/clear."""

    def __init__(self, add_stores) -> None:
        self._add = add_stores

    def add(self, repo, key: str, rows: list) -> None:
        self._add([(repo, key, rows)])
