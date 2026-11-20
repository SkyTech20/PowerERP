"""Cleaning of the fields a screen sends, from the record's field schema (powererp.schemas).

kind: s = text, d = number (kept as text "12.50"), i = integer, b = yes / no, date = YYYY-MM-DD, (choices) = one of.
"""

from __future__ import annotations

import copy
from collections.abc import Callable, Iterable
from datetime import datetime
from typing import Any

from powererp.core.errors import AppError
from powererp.core.values import boolean, decimal_text, number, text

Row = dict[str, Any]


def clean(kind: Any, value: Any) -> Any:
    """The value of a field, cleaned for its kind; ValueError when it does not fit."""
    if isinstance(kind, tuple):
        v = text(value)
        if v not in kind:
            raise ValueError(v)
        return v
    if kind == "b":
        return boolean(value)
    if kind == "i":
        return int(number(value)) if text(value) else 0
    if kind == "d":
        v = text(value)
        if v == "":
            return ""
        out = decimal_text(v, None)
        if out is None:
            raise ValueError(v)
        float(out)
        return out
    if kind == "date":
        v = text(value)[:10]
        if v:
            datetime.strptime(v, "%Y-%m-%d")
        return v
    return text(value)


def _error_code(kind: Any) -> str:
    if isinstance(kind, tuple):
        return "invalid_choice"
    return "numeric" if kind in ("d", "i") else "invalid_date"


class RecordForm:
    """Blank records and payload cleaning for one field schema."""

    def __init__(self, schema: dict[str, Any], defaults: Row | None = None):
        self.schema = schema
        self.defaults = defaults or {}

    def blank(self) -> Row:
        row: Row = {
            f: (False if k == "b" else 0 if k == "i" else (k[0] if isinstance(k, tuple) else ""))
            for f, k in self.schema.items()
        }
        row.update(copy.deepcopy(self.defaults))
        return row

    def apply(self, row: Row, payload: Row, skip: Iterable[str] = ()) -> Row:
        """Copy the fields present in the payload, cleaned. A bad value raises AppError on its field."""
        skipped = set(skip)
        for f, kind in self.schema.items():
            if f in payload and f not in skipped:
                try:
                    row[f] = clean(kind, payload[f])
                except (ValueError, TypeError):
                    raise AppError(_error_code(kind), f) from None
        return row

    def lines(self, payload: Row, keep: Callable[[Row], Any]) -> list[Row]:
        """The cleaned "lines" of a payload; keep(line) says whether an (almost) empty line is kept."""
        out = []
        for ln in payload.get("lines") or []:
            if not isinstance(ln, dict):
                continue
            row = self.apply(self.blank(), ln)
            if keep(row):
                out.append(row)
        return out
