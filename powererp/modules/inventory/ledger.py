"""The stock ledger: movements (insert only) and the balances they add up to.

Two implementations of the same interface:
    DatabaseLedger  stock_movements + stock_balances tables, a lock per product, balances cached per request
    MemoryLedger    a list (the demo data is prepared with it at start-up, before the database is used)
"""

from __future__ import annotations

import copy
from typing import Any, Protocol

from flask import g

from powererp import stock as balances_table
from powererp.core.values import number

Row = dict[str, Any]
Key = tuple[str, str, str, str, str]  # product, warehouse, location, lot, serial (upper case)
Balances = dict[Key, Row]
Effect = tuple[str, str, float, float]  # warehouse, location, on-hand change, reserved change


def effects(m: Row) -> list[Effect]:
    """(warehouse, location, on-hand change, reserved change) of a movement."""
    q = number(m["dQty"])
    wh, loc = m["cWarehouse"], m.get("cLocation", "")
    t = m["cType"]
    if t == "IN":
        return [(wh, loc, q, 0.0)]
    if t == "OUT":
        return [(wh, loc, -q, 0.0)]
    if t == "TRF":
        return [(wh, loc, -q, 0.0), (m["cWhTo"], m.get("cLocTo", ""), q, 0.0)]
    if t in ("ADJ", "CNT"):
        return [(wh, loc, q, 0.0)]
    if t == "RSV":
        return [(wh, loc, 0.0, q)]
    return []


def replay(movements, into: Balances | None = None) -> Balances:
    """Balances obtained by adding the effects of `movements` to `into` (a new dict by default)."""
    out: Balances = {} if into is None else into
    for m in movements:
        for wh, loc, dq, dr in effects(m):
            key = (
                m["cProduct"].upper(),
                wh.upper(),
                loc.upper(),
                m.get("cLot", "").upper(),
                m.get("cSerial", "").upper(),
            )
            b = out.setdefault(
                key,
                {
                    "cProduct": m["cProduct"],
                    "cWarehouse": wh,
                    "cLocation": loc,
                    "cLot": m.get("cLot", ""),
                    "cSerial": m.get("cSerial", ""),
                    "qty": 0.0,
                    "reserved": 0.0,
                    "dExpiry": "",
                },
            )
            b["qty"] = round(b["qty"] + dq, 6)
            b["reserved"] = round(b["reserved"] + dr, 6)
            if m.get("dExpiry") and dq > 0:
                b["dExpiry"] = m["dExpiry"]
    return out


class StockLedger(Protocol):
    def balances(self) -> Balances: ...
    def lock(self, product: str) -> None: ...
    def append(self, m: Row) -> Row: ...
    def all(self) -> list[Row]: ...
    def get(self, no: int) -> Row | None: ...


class MemoryLedger:
    def __init__(self) -> None:
        self.movements: list[Row] = []

    def balances(self) -> Balances:
        return replay(self.movements)

    def lock(self, product: str) -> None:
        """Nothing to lock: one thread prepares the data."""

    def append(self, m: Row) -> Row:
        m["iNo"] = len(self.movements) + 1
        self.movements.append(m)
        return m

    def all(self) -> list[Row]:
        return list(self.movements)

    def get(self, no: int) -> Row | None:
        return next((m for m in self.movements if m["iNo"] == no), None)


class DatabaseLedger:
    """stock_movements (Store) + stock_balances (powererp.stock), numbered by doc_sequences ("STOCK_MOVE")."""

    def __init__(self, movements, numbering):
        self.repo = movements
        self.numbering = numbering

    def balances(self) -> Balances:
        """Cached for the request (the lists ask once per row) until the next movement."""
        try:
            cached = g.get("inv_bal")
        except RuntimeError:
            cached = None
        if cached is None:
            cached = balances_table.read()
            try:
                g.inv_bal = cached
            except RuntimeError:
                pass
        return cached

    @staticmethod
    def forget() -> None:
        try:
            g.pop("inv_bal", None)
        except RuntimeError:
            pass

    def lock(self, product: str) -> None:
        """One movement of this product at a time (until the end of the transaction); the cache is dropped so the
        stock is read again after the wait (another request may have changed it)."""
        balances_table.lock_product(product)
        self.forget()

    def append(self, m: Row) -> Row:
        m["iNo"] = self.numbering.next("STOCK_MOVE")
        self.repo.insert(m)
        balances_table.apply(m, effects(m))
        self.forget()
        return m

    def all(self) -> list[Row]:
        return self.repo.all()

    def get(self, no: int) -> Row | None:
        return self.repo.get(no)

    def rebuild(self) -> None:
        balances_table.rebuild(self.repo.all(), effects)
        self.forget()

    @staticmethod
    def clear_balances() -> None:
        balances_table.clear()


def with_staged(balances: Balances, staged) -> Balances:
    """The balances plus the effects of movements not posted yet (a copy)."""
    return replay(staged, copy.deepcopy(balances)) if staged else balances
