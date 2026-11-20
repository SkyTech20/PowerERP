"""Stock balances: read, update with each movement, rebuild from the ledger.

Concurrency: lock_product() takes a transaction-level advisory lock on the product before a movement is checked
against the stock, so two requests moving the same product run one after the other and the second sees the
stock left by the first (no negative stock from two simultaneous issues). The lock is released at commit.
"""

from datetime import date

from sqlalchemy import delete, func, insert, select, text

from . import database
from .models.stock import stock_balances as t
from .store import company_id

_UPSERT = text(
    """
INSERT INTO stock_balances (company_id, product, warehouse, location, lot, serial, qty, reserved, expiry)
VALUES (:cid, :product, :warehouse, :location, :lot, :serial, :dq, :dr, :expiry)
ON CONFLICT (company_id, lower(product), lower(warehouse), lower(location), lower(lot), lower(serial))
DO UPDATE SET qty = stock_balances.qty + EXCLUDED.qty,
              reserved = stock_balances.reserved + EXCLUDED.reserved,
              expiry = COALESCE(EXCLUDED.expiry, stock_balances.expiry)
"""
)


def lock_product(code):
    """Serialize the movements of one product until the end of the transaction."""
    database.current().execute(
        text("SELECT pg_advisory_xact_lock(hashtext(:k))"), {"k": f"stock:{company_id()}:{str(code).upper()}"}
    )


def read():
    """{(PRODUCT, WAREHOUSE, LOCATION, LOT, SERIAL): {"cProduct", ..., "qty", "reserved", "dExpiry"}}."""
    rows = database.current().execute(select(t).where(t.c.company_id == company_id()).order_by(t.c.id)).mappings()
    out = {}
    for r in rows:
        key = (
            r["product"].upper(),
            r["warehouse"].upper(),
            r["location"].upper(),
            r["lot"].upper(),
            r["serial"].upper(),
        )
        out[key] = {
            "cProduct": r["product"],
            "cWarehouse": r["warehouse"],
            "cLocation": r["location"],
            "cLot": r["lot"],
            "cSerial": r["serial"],
            "qty": round(float(r["qty"]), 6),
            "reserved": round(float(r["reserved"]), 6),
            "dExpiry": r["expiry"].isoformat() if r["expiry"] else "",
        }
    return out


def _expiry(v):
    v = str(v or "").strip()[:10]
    return date.fromisoformat(v) if v else None


def apply(m, effects):
    """Add the effects [(warehouse, location, on-hand change, reserved change)] of movement m to the balances."""
    s = database.current()
    cid = company_id()
    for wh, loc, dq, dr in effects:
        s.execute(
            _UPSERT,
            {
                "cid": cid,
                "product": m["cProduct"],
                "warehouse": wh,
                "location": loc or "",
                "lot": m.get("cLot") or "",
                "serial": m.get("cSerial") or "",
                "dq": round(dq, 6),
                "dr": round(dr, 6),
                "expiry": _expiry(m.get("dExpiry")) if m.get("dExpiry") and dq > 0 else None,
            },
        )


def rebuild(movements, effects_of):
    """Recalculate every balance from the movements (after a reset or a load of older data)."""
    clear()
    out = {}
    for m in movements:
        for wh, loc, dq, dr in effects_of(m):
            key = (
                m["cProduct"].upper(),
                wh.upper(),
                (loc or "").upper(),
                (m.get("cLot") or "").upper(),
                (m.get("cSerial") or "").upper(),
            )
            b = out.setdefault(
                key,
                {
                    "product": m["cProduct"],
                    "warehouse": wh,
                    "location": loc or "",
                    "lot": m.get("cLot") or "",
                    "serial": m.get("cSerial") or "",
                    "qty": 0.0,
                    "reserved": 0.0,
                    "expiry": None,
                },
            )
            b["qty"] = round(b["qty"] + dq, 6)
            b["reserved"] = round(b["reserved"] + dr, 6)
            if m.get("dExpiry") and dq > 0:
                b["expiry"] = _expiry(m["dExpiry"])
    rows = [{"company_id": company_id(), **b} for b in out.values()]
    s = database.current()
    for i in range(0, len(rows), 500):
        s.execute(insert(t).values(rows[i : i + 500]))


def clear():
    database.current().execute(delete(t).where(t.c.company_id == company_id()))


def count():
    return database.current().scalar(select(func.count()).select_from(t).where(t.c.company_id == company_id()))
