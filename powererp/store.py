"""Access to the master data tables in the API's format.

A Store reads and writes one table of powererp.models.master as the dicts the API has always returned
(cCode, dPrice1 "1649.00", lActive True, "lines": [...]), so the routes keep their contract while the data
lives in relational tables. Every call uses the session of the current request (powererp.database.current()).
"""

from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from sqlalchemy import delete, func, insert, select, update

from . import database
from .models.master import SPECS, column_name

_company_cache = {}


def company_id(code="MAIN"):
    """Id of the company the ERP works on (one company for now: MAIN)."""
    if code not in _company_cache:
        from .models import Company

        cid = database.current().scalar(select(Company.id).where(Company.code == code))
        if cid is None:
            raise RuntimeError(f"company {code} missing (migration 0001 creates MAIN)")
        _company_cache[code] = cid
    return _company_cache[code]


def _to_db(kind, value):
    if kind == "d":
        if value is None or str(value).strip() == "":
            return None
        try:
            return Decimal(str(value).strip())
        except InvalidOperation:
            raise ValueError(value) from None
    if kind == "date":
        v = str(value or "").strip()[:10]
        return date.fromisoformat(v) if v else None
    if kind == "ts":
        v = str(value or "").strip()
        return datetime.fromisoformat(v) if v else None
    if kind == "json":
        return value
    if kind == "b":
        return bool(value)
    if kind == "i":
        return int(value or 0)
    return "" if value is None else str(value)


def _from_db(kind, value):
    if kind == "d":
        return "" if value is None else format(value, "f")
    if kind == "date":
        return value.isoformat() if value else ""
    if kind == "ts":
        return value.isoformat(timespec="seconds") if value else ""
    if kind == "json":
        return value
    if kind == "b":
        return bool(value)
    if kind == "i":
        return int(value or 0)
    return value if value is not None else ""


class Store:
    def __init__(self, name):
        self.spec = SPECS[name]
        self.t = self.spec.table
        self.lt = self.spec.lines
        self.fields = self.spec.fields
        self.cols = {f: self.t.c[column_name(f)] for f in self.fields}
        self.lcols = {f: self.lt.c[column_name(f)] for f in self.spec.line_schema} if self.lt is not None else {}

    # ------------------------------------------------------------ conversion

    def _row_out(self, r):
        m = r._mapping
        return {
            f: _from_db(k, m[self.cols[f]])
            for f, k in self.fields.items()
            if not (f in self.spec.sparse and m[self.cols[f]] is None)
        }

    @staticmethod
    def _default(kind):
        return kind[0] if isinstance(kind, tuple) else None

    def _values(self, row, full=False):
        """Column values of the fields present in `row`; full=True gives every column (missing = default),
        as multi-row INSERTs need the same columns in every row."""
        return {
            self.cols[f].name: _to_db(k, row.get(f, self._default(k)))
            for f, k in self.fields.items()
            if full or f in row
        }

    def _line_values(self, ln):
        return {self.lcols[f].name: _to_db(k, ln.get(f, self._default(k))) for f, k in self.spec.line_schema.items()}

    # ------------------------------------------------------------ queries

    def _where_key(self, key_values, ci):
        conds = [self.t.c.company_id == company_id()]
        for f, v in zip(self.spec.keys, key_values, strict=False):
            c = self.cols[f]
            if self.fields[f] != "s":
                conds.append(c == _to_db(self.fields[f], v))
            else:
                conds.append(func.lower(c) == str(v or "").lower() if ci else c == str(v or ""))
        return conds

    def _order(self):
        return [self.cols[f] for f in self.spec.order] + [self.t.c.id] if self.spec.order else [self.t.c.id]

    def _attach_lines(self, rows_by_id, s):
        if self.lt is None:
            return
        for r in rows_by_id.values():
            r["lines"] = []
        if not rows_by_id:
            return
        q = (
            select(self.lt)
            .where(self.lt.c.parent_id.in_(list(rows_by_id)))
            .order_by(self.lt.c.parent_id, self.lt.c.line_no)
        )
        for ln in s.execute(q):
            m = ln._mapping
            rows_by_id[m["parent_id"]]["lines"].append(
                {f: _from_db(k, m[self.lcols[f]]) for f, k in self.spec.line_schema.items()}
            )

    def all(self, lines=True, where=None):
        """Every row of the company, in the table's default order."""
        s = database.current()
        q = select(self.t).where(self.t.c.company_id == company_id()).order_by(*self._order())
        if where is not None:
            q = q.where(*where(self.cols))
        result = s.execute(q).all()
        out = {r._mapping["id"]: self._row_out(r) for r in result}
        if lines:
            self._attach_lines(out, s)
        return list(out.values())

    def get(self, *key_values, ci=True):
        """The row with this business key (case-insensitive by default), or None."""
        s = database.current()
        r = s.execute(select(self.t).where(*self._where_key(key_values, ci))).first()
        if r is None:
            return None
        out = {r._mapping["id"]: self._row_out(r)}
        self._attach_lines(out, s)
        return out[r._mapping["id"]]

    def exists(self, where):
        """True when a row matches where(cols) -> list of conditions."""
        s = database.current()
        q = select(self.t.c.id).where(self.t.c.company_id == company_id(), *where(self.cols)).limit(1)
        return s.execute(q).first() is not None

    def count(self, where=None):
        s = database.current()
        q = select(func.count()).select_from(self.t).where(self.t.c.company_id == company_id())
        if where is not None:
            q = q.where(*where(self.cols))
        return s.scalar(q)

    # ------------------------------------------------------------ writes

    def _id(self, row, ci=True):
        s = database.current()
        return s.scalar(select(self.t.c.id).where(*self._where_key([row.get(k) for k in self.spec.keys], ci)))

    def _write_lines(self, s, parent_id, lines):
        s.execute(delete(self.lt).where(self.lt.c.parent_id == parent_id))
        rows = [{"parent_id": parent_id, "line_no": i, **self._line_values(ln)} for i, ln in enumerate(lines, 1)]
        if rows:
            s.execute(insert(self.lt).values(rows))

    def insert(self, row):
        s = database.current()
        new_id = s.execute(
            insert(self.t).values(company_id=company_id(), **self._values(row, full=True)).returning(self.t.c.id)
        ).scalar()
        if self.lt is not None:
            self._write_lines(s, new_id, row.get("lines") or [])
        return row

    def update(self, row, key_values=None):
        """Replace the row found by its business key (or key_values, when the key itself changed)."""
        s = database.current()
        keys = key_values if key_values is not None else [row.get(k) for k in self.spec.keys]
        rid = s.scalar(select(self.t.c.id).where(*self._where_key(keys, True)))
        if rid is None:
            raise KeyError(keys)
        s.execute(update(self.t).where(self.t.c.id == rid).values(**self._values(row)))
        if self.lt is not None and "lines" in row:
            self._write_lines(s, rid, row["lines"])
        return row

    def delete(self, row):
        s = database.current()
        s.execute(delete(self.t).where(*self._where_key([row.get(k) for k in self.spec.keys], True)))

    def delete_where(self, where):
        s = database.current()
        s.execute(delete(self.t).where(self.t.c.company_id == company_id(), *where(self.cols)))

    def clear(self):
        s = database.current()
        s.execute(delete(self.t).where(self.t.c.company_id == company_id()))

    def replace_all(self, rows):
        """Empty the table and load these rows (seed, reset, migration from the JSON datasets)."""
        self.clear()
        if not rows:
            return
        s = database.current()
        cid = company_id()
        # Multi-row INSERT ... VALUES statements (one round trip each; executemany is slow with psycopg's
        # pipeline mode on some networks), in chunks to keep the statements a reasonable size.
        params = [{"company_id": cid, **self._values(r, full=True)} for r in rows]
        key_cols = [self.cols[k] for k in self.spec.keys]
        ids = {}
        for chunk in range(0, len(params), 500):
            part = params[chunk : chunk + 500]
            if self.lt is None:
                s.execute(insert(self.t).values(part))
                continue
            for r in s.execute(insert(self.t).values(part).returning(self.t.c.id, *key_cols)):
                ids[tuple(str(v).lower() for v in r[1:])] = r[0]
        if self.lt is None:
            return
        lines = [
            {
                "parent_id": ids[tuple(str(r.get(k) or "").lower() for k in self.spec.keys)],
                "line_no": i,
                **self._line_values(ln),
            }
            for r in rows
            for i, ln in enumerate(r.get("lines") or [], 1)
        ]
        for chunk in range(0, len(lines), 500):
            s.execute(insert(self.lt).values(lines[chunk : chunk + 500]))


_stores = {}


def store(name):
    if name not in _stores:
        _stores[name] = Store(name)
    return _stores[name]
