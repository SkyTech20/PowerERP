"""MemoryRepository: the read / write methods of a Store, on a list in memory.

Used to run the real services before the database is involved (e.g. the demo data is prepared at start-up by
posting its opening stock movements with the stock service, on memory repositories) and in unit tests.
Keys are compared ignoring case, like the unique indexes of the tables.
"""

from __future__ import annotations

import copy
from typing import Any

Row = dict[str, Any]


class MemoryRepository:
    def __init__(self, rows: list[Row] | None = None, keys: tuple[str, ...] = ("cCode",)):
        self.rows: list[Row] = rows if rows is not None else []
        self.keys = keys

    def _match(self, r: Row, values, ci: bool = True) -> bool:
        def norm(v):
            return str(v or "").lower() if ci else str(v or "")

        return all(norm(r.get(k)) == norm(v) for k, v in zip(self.keys, values, strict=True))

    def all(self, lines: bool = True, where=None) -> list[Row]:
        return [copy.deepcopy(r) for r in self.rows]

    def get(self, *values, ci: bool = True) -> Row | None:
        return next((copy.deepcopy(r) for r in self.rows if self._match(r, values, ci)), None)

    def insert(self, row: Row) -> Row:
        self.rows.append(copy.deepcopy(row))
        return row

    def update(self, row: Row, key_values=None) -> Row:
        keys = key_values if key_values is not None else [row.get(k) for k in self.keys]
        for i, r in enumerate(self.rows):
            if self._match(r, keys):
                self.rows[i] = copy.deepcopy(row)
                return row
        raise KeyError(keys)

    def delete(self, row: Row) -> None:
        self.rows = [r for r in self.rows if not self._match(r, [row.get(k) for k in self.keys])]

    def count(self, where=None) -> int:
        return len(self.rows)

    def replace_all(self, rows: list[Row]) -> None:
        self.rows = [copy.deepcopy(r) for r in rows]

    def clear(self) -> None:
        self.rows = []
