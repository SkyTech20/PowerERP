"""The status of the lots (step 5 of the SCOR / ISO plan: ISO 9001 8.7, ISO 22000 / HACCP and SFCR: a lot that may be
unsafe is held until a decision is taken).

A lot of a product is released (it may be sold and used in production), on hold (waiting for a decision),
in quarantine (kept apart until it is checked) or rejected (it never goes out: scrap or return to the supplier). A
lot without a row in lot_status is released. A lot that is not released is left out of the sales invoices and of
the materials of the production orders (picking.pick_order), and is not counted as available; it can still be
moved, adjusted or counted in Inventory (to a quarantine location, to scrap).

Every change needs a reason and is kept in the history of the lot (who, when, from, to, why, nonconformance).
"""

from __future__ import annotations

import copy
from collections import defaultdict
from collections.abc import Callable, Iterable
from datetime import datetime
from typing import Any

from powererp import schemas as S
from powererp.core.errors import AppError
from powererp.core.values import quantity, text

Row = dict[str, Any]
Key = tuple[str, str]
RELEASED = "released"
# the statuses in the labels of the lot lists (lookups)
STATUS_LABELS = {
    "en": {"on_hold": "On hold", "quarantine": "Quarantine", "rejected": "Rejected"},
    "fr": {"on_hold": "En attente", "quarantine": "Quarantaine", "rejected": "Rejeté"},
}
EPS = 1e-9


def key(product: Any, lot: Any) -> Key:
    return text(product).upper(), text(lot).upper()


class LotStatusService:
    def __init__(self, repo: Any, refs: dict[str, Callable[[], Any]], username: Callable[[], str]):
        """refs: stock (the StockService), products (find)."""
        self.repo = repo
        self.refs = refs
        self.username = username

    # ---------------------------------------------------------- read
    def held(self) -> set[Key]:
        """The lots that may not go out: every lot whose status is not released, as (PRODUCT, LOT)."""
        return {key(r["cProduct"], r["cLot"]) for r in self.repo.all(lines=False) if r["cStatus"] != RELEASED}

    def statuses(self) -> dict[Key, str]:
        """(PRODUCT, LOT) -> status, for the lots that have one."""
        return {key(r["cProduct"], r["cLot"]): r["cStatus"] for r in self.repo.all(lines=False)}

    def status_of(self, product: str, lot: str) -> str:
        row = self.repo.get(product, lot) if text(lot) else None
        return row["cStatus"] if row else RELEASED

    def _known(self) -> dict[Key, Row]:
        """The lots the stock knows (a movement with a lot): name, expiry, product."""
        out: dict[Key, Row] = {}
        for m in self.refs["stock"]().ledger.all():
            if text(m.get("cLot")):
                k = key(m["cProduct"], m["cLot"])
                r = out.setdefault(k, {"cProduct": m["cProduct"], "cLot": m["cLot"], "dExpiry": ""})
                if m.get("dExpiry"):
                    r["dExpiry"] = text(m["dExpiry"])[:10]
        return out

    def _on_hand(self) -> tuple[dict[Key, float], dict[Key, list[str]]]:
        qty: dict[Key, float] = defaultdict(float)
        where: dict[Key, list[str]] = defaultdict(list)
        for (p, w, loc, lot, _serial), b in self.refs["stock"]().balances().items():
            if not lot or abs(b["qty"]) <= EPS:
                continue
            qty[(p, lot)] += b["qty"]
            place = f"{w}/{loc}" if loc else w
            if place not in where[(p, lot)]:
                where[(p, lot)].append(place)
        return qty, where

    def _row(self, k: Key, known: Row, status: Row | None, qty: float, where: list[str]) -> Row:
        prod = self.refs["products"]()(k[0]) or {}
        return {
            "cProduct": prod.get("cCode") or known.get("cProduct") or k[0],
            "cLot": known.get("cLot") or (status or {}).get("cLot") or k[1],
            "cDescFR": text(prod.get("cDescFR")),
            "cDescEN": text(prod.get("cDescEN")),
            "cUOM": text(prod.get("cStockUOM")),
            "dExpiry": known.get("dExpiry", ""),
            "dOnHand": quantity(qty),
            "cWhere": ", ".join(where),
            "cStatus": status["cStatus"] if status else RELEASED,
            "cReason": text((status or {}).get("cReason")),
            "dChanged": text((status or {}).get("dChanged")),
            "cUser": text((status or {}).get("cUser")),
            "iNC": int((status or {}).get("iNC") or 0),
        }

    def lots(self, f: Row) -> Row:
        """The lots in stock (and every lot that is not released, even when used up), with their status.
        Filters: status (one status, or "blocked": every status but released), product, q (text)."""
        known = self._known()
        qty, where = self._on_hand()
        statuses = {key(r["cProduct"], r["cLot"]): r for r in self.repo.all(lines=False)}
        keys = {k for k in known if qty.get(k, 0.0) > EPS} | {
            k for k, r in statuses.items() if r["cStatus"] != RELEASED
        }
        rows = [self._row(k, known.get(k, {}), statuses.get(k), qty.get(k, 0.0), where.get(k, [])) for k in keys]
        counts = {s: sum(1 for r in rows if r["cStatus"] == s) for s in S.LOT_STATUSES}
        status, product, q = text(f.get("status")), text(f.get("product")).upper(), text(f.get("q")).lower()
        if status == "blocked":
            rows = [r for r in rows if r["cStatus"] != RELEASED]
        elif status:
            rows = [r for r in rows if r["cStatus"] == status]
        if product:
            rows = [r for r in rows if r["cProduct"].upper() == product]
        if q:
            fields = ("cProduct", "cLot", "cDescFR", "cDescEN", "cReason", "cWhere")
            rows = [r for r in rows if any(q in text(r[x]).lower() for x in fields)]
        # what needs a decision first, then by product and lot
        order = {s: i for i, s in enumerate(("on_hold", "quarantine", "rejected", RELEASED))}
        rows.sort(key=lambda r: (order[r["cStatus"]], r["cProduct"].upper(), r["cLot"].upper()))
        return {"items": rows, "counts": counts, "total": len(rows)}

    def get(self, product: str, lot: str) -> Row:
        """One lot: its status, its stock and the history of its status."""
        k = key(product, lot)
        known = self._known()
        status = self.repo.get(product, lot)
        if k not in known and status is None:
            raise AppError("unknown_lot", "cLot", 404)
        qty, where = self._on_hand()
        out = self._row(k, known.get(k, {}), status, qty.get(k, 0.0), where.get(k, []))
        out["history"] = list(reversed((status or {}).get("history", [])))
        return out

    # ---------------------------------------------------------- change
    def change(self, product: str, lot: str, status: str, reason: str, nc: int = 0) -> Row:
        """Give a lot a new status (the reason is required); kept in its history."""
        status, reason = text(status), text(reason)
        if status not in S.LOT_STATUSES:
            raise AppError("invalid_choice", "cStatus")
        if not reason:
            raise AppError("required", "cReason")
        k = key(product, lot)
        known = self._known()
        current = self.repo.get(product, lot)
        if k not in known and current is None:
            raise AppError("unknown_lot", "cLot", 404)
        before = current["cStatus"] if current else RELEASED
        if before == status:
            raise AppError("same_status", "cStatus")
        now = datetime.now().isoformat(timespec="seconds")
        event = {"dAt": now, "cUser": self.username(), "cFrom": before, "cTo": status, "cReason": reason, "iNC": nc}
        if current is None:
            prod = self.refs["products"]()(k[0]) or {}
            row = {
                "cProduct": prod.get("cCode") or known[k]["cProduct"],
                "cLot": known[k]["cLot"],
                "history": [],
            }
        else:
            row = copy.deepcopy(current)
        row.update({"cStatus": status, "cReason": reason, "dChanged": now, "cUser": self.username(), "iNC": nc})
        row["history"] = row.get("history", []) + [event]
        if current is None:
            self.repo.insert(row)
        else:
            self.repo.update(row, [current["cProduct"], current["cLot"]])
        return self.get(row["cProduct"], row["cLot"])

    def hold_many(self, lots: Iterable[Row], reason: str, status: str = "on_hold") -> Row:
        """Put several lots on hold at once (the lots a recall reaches): the released ones change, the others stay."""
        if not text(reason):
            raise AppError("required", "cReason")
        if status not in S.LOT_STATUSES or status == RELEASED:
            raise AppError("invalid_choice", "cStatus")
        changed, kept = [], []
        seen: set[Key] = set()
        for ln in lots:
            k = key(ln.get("cProduct"), ln.get("cLot"))
            if not k[1] or k in seen:
                continue
            seen.add(k)
            if self.status_of(*k) != RELEASED:
                kept.append({"cProduct": ln.get("cProduct"), "cLot": ln.get("cLot")})
                continue
            row = self.change(text(ln.get("cProduct")), text(ln.get("cLot")), status, reason)
            changed.append({"cProduct": row["cProduct"], "cLot": row["cLot"]})
        return {"changed": changed, "kept": kept}

    def products(self, fields: tuple[str, ...] = ("cDescFR",)) -> list[Row]:
        """The products with lots (the filter of the screen and the product of a nonconformance's lot)."""
        codes = sorted({k[0] for k in self._known()})
        rows = []
        for code in codes:
            p = self.refs["products"]()(code) or {"cCode": code}
            rows.append({"code": p["cCode"], "label": next((p[f] for f in fields if p.get(f)), "")})
        return rows

    def lot_choices(self, product: str, lang: str = "en") -> list[Row]:
        """The lots of a product (code = lot; label = status when not released, expiry, on hand)."""
        p = text(product).upper()
        qty, _where = self._on_hand()
        statuses = self.statuses()
        rows = []
        for k, r in sorted(self._known().items()):
            if k[0] != p:
                continue
            st = statuses.get(k, RELEASED)
            words = STATUS_LABELS["fr" if lang == "fr" else "en"]
            parts = [words.get(st, ""), r["dExpiry"], quantity(qty.get(k, 0.0))]
            rows.append({"code": r["cLot"], "label": " · ".join(x for x in parts if x), "cStatus": st})
        return rows
