"""Which stock goes out first: the pick policy of a product and the order of its balances (lots, locations).

FEFO: the lots expiring first; FIFO: the stock received first; LIFO: the stock received last; a product without a
policy is FEFO when it has an expiry date, else FIFO. An expired lot never goes out (sold or used in production),
and neither does a lot that is not released (on hold, quarantine, rejected: quality/lots.py) or the stock of a
blocked or inactive location. Used by the sales invoices and the production orders.
"""

from __future__ import annotations

from collections.abc import Callable, Collection
from typing import Any

from powererp.core.values import text

from .ledger import effects

Row = dict[str, Any]
Received = dict[tuple[str, ...], tuple[str, int, str, int]]
EPS = 1e-9


def _day(d: str) -> int:
    """2026-11-23 -> 20261123 (0 when empty)."""
    digits = d.replace("-", "")[:8]
    return int(digits) if digits.isdigit() else 0


def pick_policy(prod: Row) -> str:
    """FEFO / FIFO / LIFO: the product's, else FEFO when it has an expiry date, else FIFO."""
    return str(prod.get("cPickPolicy") or ("FEFO" if prod.get("lExpiryControl") else "FIFO"))


def received_dates(stock: Any, products: set[str]) -> Received:
    """Per balance key: (first received date, its movement no, last received date, its movement no)."""
    out: Received = {}
    for m in stock.ledger.all():
        if m["cProduct"].upper() not in products:
            continue
        for wh, loc, dq, _dr in effects(m):
            if dq <= 0:
                continue
            key = (
                m["cProduct"].upper(),
                wh.upper(),
                loc.upper(),
                text(m.get("cLot")).upper(),
                text(m.get("cSerial")).upper(),
            )
            d, n = str(m.get("dDate") or ""), int(m.get("iNo") or 0)
            first = out.get(key)
            if first is None:
                out[key] = (d, n, d, n)
            else:
                out[key] = min(first[:2], (d, n)) + max(first[2:], (d, n))
    return out


def pick_key(policy: str, b: Row, received: tuple[str, int, str, int] | None) -> tuple:
    """Sort key of a balance: the stock that goes out first comes first."""
    first, last = (received[:2], received[2:]) if received else (("", 0), ("", 0))
    place = (b["cLot"].upper(), b["cLocation"].upper(), b["cSerial"].upper())
    if policy == "FEFO":
        return (b.get("dExpiry") or "9999-12-31", *first, *place)
    if policy == "LIFO":
        return (-_day(last[0]), -last[1], *place)
    return (*first, *place)


def location_usable(stock: Any, warehouse: str, location: str) -> bool:
    """Stock may be taken from this location (none, or an active location that is not blocked)."""
    if not location:
        return True
    loc = stock.locations.find_in(warehouse, location)
    return loc is not None and not loc.get("lBlocked") and loc.get("lActive", True)


def pick_order(
    prod: Row,
    warehouse: str,
    bal: dict,
    day: str,
    received: Received,
    usable: Callable[[str], bool],
    held: Collection[tuple[str, str]] = (),
) -> list[tuple[Row, float]]:
    """The balances of a product in a warehouse that can go out on `day`, first to go out first: (balance, free qty).
    held: the lots that may not go out, as (PRODUCT, LOT) in capitals."""
    policy = pick_policy(prod)
    candidates = []
    for key, b in bal.items():
        if key[0] != prod["cCode"].upper() or key[1] != warehouse.upper():
            continue
        free = b["qty"] - b["reserved"]
        if free <= EPS or not usable(b["cLocation"]):
            continue
        if prod.get("lExpiryControl") and b.get("dExpiry") and str(b["dExpiry"])[:10] < day:
            continue  # expired: never goes out
        if b["cLot"] and (key[0], b["cLot"].upper()) in held:
            continue  # on hold, in quarantine or rejected
        candidates.append((pick_key(policy, b, received.get(key)), b, free))
    candidates.sort(key=lambda c: c[0])
    return [(b, free) for _k, b, free in candidates]


def held_quantity(prod: Row, warehouse: str, bal: dict, held: Collection[tuple[str, str]]) -> float:
    """The free stock of a product in a warehouse that is in lots not released (to explain a shortage)."""
    code, wh = prod["cCode"].upper(), warehouse.upper()
    return sum(
        b["qty"] - b["reserved"]
        for key, b in bal.items()
        if key[0] == code and key[1] == wh and b["cLot"] and (code, b["cLot"].upper()) in held
    )


def shortage_code(prod: Row, warehouse: str, bal: dict, held: Collection[tuple[str, str]]) -> str:
    """insufficient_stock, or insufficient_released when lots on hold (quarantine, rejected) hold stock back."""
    return "insufficient_released" if held and held_quantity(prod, warehouse, bal, held) > EPS else "insufficient_stock"
