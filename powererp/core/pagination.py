"""Search, filters, sort and pages of a list, the same way for every list screen.

Query string: q (search in `search_fields`), f_<field>=value (exact, ignoring case), sort, dir (asc / desc),
page, size (1 to 500).
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from .values import text


def _sort_key(sort: str):
    def key(r: Mapping[str, Any]):
        v = r.get(sort)
        if isinstance(v, int | float) and not isinstance(v, bool):
            return (0, v, "")
        sv = text(v)
        try:
            return (0, float(sv), "")
        except ValueError:
            return (1, 0, sv.lower())

    return key


def paginate(rows: Iterable[Mapping[str, Any]], search_fields: Iterable[str], args: Mapping[str, str]) -> dict:
    """{"total", "page", "size", "items"} of `rows` filtered, sorted and paged by the query `args`."""
    rows = list(rows)
    q = (args.get("q") or "").strip().lower()
    if q:
        rows = [r for r in rows if any(q in text(r.get(f)).lower() for f in search_fields)]
    for key, val in args.items():
        if key.startswith("f_") and val != "":
            field = key[2:]
            rows = [r for r in rows if text(r.get(field)).lower() == val.lower()]
    sort = args.get("sort")
    if sort:
        rows = sorted(rows, key=_sort_key(sort), reverse=args.get("dir") == "desc")
    try:
        size = max(1, min(int(args.get("size", 25)), 500))
        page = max(1, int(args.get("page", 1)))
    except ValueError:
        size, page = 25, 1
    start = (page - 1) * size
    return {"total": len(rows), "page": page, "size": size, "items": rows[start : start + size]}


def paginate_request(rows: Iterable[Mapping[str, Any]], search_fields: Iterable[str]) -> dict:
    """paginate() with the query string of the current request."""
    from flask import request

    return paginate(rows, search_fields, request.args)
