"""Stock rules: movements (checked, costed, posted), balances, stock and valuation lists, product figures."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from typing import Any

from powererp import schemas as S
from powererp.core.errors import AppError
from powererp.core.security import current_username
from powererp.core.values import amount, number, quantity, text, today, unit_cost
from powererp.modules.common.forms import RecordForm, Row

from .costing import costing_of
from .ledger import Balances, StockLedger, effects, with_staged

PURCHASE_TYPES = ("IN",)


def increases_stock(m: Row) -> bool:
    return m["cType"] == "IN" or (m["cType"] in ("ADJ", "CNT") and number(m["dQty"]) > 0)


class StockService:
    """Movements and balances of a ledger (database or memory), against the master files of these repositories."""

    def __init__(
        self,
        ledger: StockLedger,
        products_repo,
        warehouses_repo,
        locations,
        params_repo,
        on_order: Callable[[str], float] = lambda code: 0.0,
        username: Callable[[], str] = current_username,
    ):
        self.ledger = ledger
        self.products_repo = products_repo
        self.warehouses_repo = warehouses_repo
        self.locations = locations  # LocationService
        self.params_repo = params_repo
        self.on_order = on_order
        self.username = username
        self.form = RecordForm(S.MOVEMENT)
        # Other modules tell how to open their documents: doc type -> {document number: record id} (e.g. "SO":
        # the invoice / credit note numbers of the sales invoices)
        self.document_ids: dict[str, Callable[[], dict[str, Any]]] = {}

    # ---------------------------------------------------------- balances
    def balances(self, staged=()) -> Balances:
        return with_staged(self.ledger.balances(), staged)

    def product_totals(self, code: str, warehouse: str | None = None, bal: Balances | None = None):
        bal = self.balances() if bal is None else bal
        qty = res = 0.0
        for (p, w, *_rest), b in bal.items():
            if p == code.upper() and (warehouse is None or w == warehouse.upper()):
                qty += b["qty"]
                res += b["reserved"]
        return qty, res

    def quantity_at(self, warehouse: str, location: str) -> float:
        return sum(
            b["qty"]
            for (_p, w, loc, *_x), b in self.balances().items()
            if w == warehouse.upper() and loc == location.upper()
        )

    # ---------------------------------------------------------- uses (before deleting a master record)
    def _movements(self) -> list[Row]:
        return self.ledger.all()

    def product_used(self, code: str) -> bool:
        return any(m["cProduct"].upper() == code.upper() for m in self._movements())

    def warehouse_used(self, code: str) -> bool:
        cu = code.upper()
        return any(m["cWarehouse"].upper() == cu or text(m.get("cWhTo")).upper() == cu for m in self._movements())

    def location_used(self, warehouse: str, code: str) -> bool:
        wh, loc = warehouse.upper(), code.upper()
        return any(
            (m["cWarehouse"].upper() == wh and text(m.get("cLocation")).upper() == loc)
            or (text(m.get("cWhTo")).upper() == wh and text(m.get("cLocTo")).upper() == loc)
            for m in self._movements()
        )

    # ---------------------------------------------------------- movements
    def movement_from(self, p: Row) -> Row:
        m = self.form.apply(self.form.blank(), p)
        m["cType"] = m["cType"] or "IN"
        m["cDocType"] = m["cDocType"] or "MAN"
        m["dDate"] = m["dDate"] or today()
        if m["dQty"] == "":
            raise AppError("required", "dQty")
        m["dQty"] = quantity(number(m["dQty"]))
        return m

    def _place(self, m: Row, wf: str, lf: str):
        wh = self.warehouses_repo.get(m.get(wf)) if text(m.get(wf)) else None
        if wh is None:
            raise AppError("required" if not m.get(wf) else "unknown_ref", wf)
        m[wf] = wh["cCode"]
        has_locs = wh.get("lUseLocations") and self.locations.has_locations(wh["cCode"])
        if has_locs and not m.get(lf):
            raise AppError("required", lf)
        if m.get(lf):
            loc = self.locations.find_in(wh["cCode"], m[lf])
            if loc is None:
                raise AppError("unknown_ref", lf)
            m[lf] = loc["cCode"]
            if loc.get("lBlocked") or not loc.get("lActive", True):
                raise AppError("blocked_location", lf)
            return wh, loc
        return wh, None

    def check(self, m: Row, staged=()) -> Row:
        """Validate a movement against the master files and the stock (balances + `staged` movements).
        Fills the codes' spelling; returns the product. Locks the product until the end of the transaction."""
        prod = self.products_repo.get(m["cProduct"]) if text(m["cProduct"]) else None
        if prod is None:
            raise AppError("required" if not m["cProduct"] else "unknown_ref", "cProduct")
        m["cProduct"] = prod["cCode"]
        self.ledger.lock(prod["cCode"])
        prod = self.products_repo.get(m["cProduct"])
        if not prod.get("lStocked"):
            raise AppError("not_stocked", "cProduct")
        q = number(m["dQty"])
        if m["cType"] in ("IN", "OUT", "TRF") and q <= 0:
            raise AppError("positive", "dQty")
        if abs(q) < 1e-9:
            raise AppError("required", "dQty")

        wh, loc = self._place(m, "cWarehouse", "cLocation")
        dest = None
        if m["cType"] == "TRF":
            dest = self._place(m, "cWhTo", "cLocTo")
            if dest[0]["cCode"] == wh["cCode"] and (m.get("cLocTo") or "") == (m.get("cLocation") or ""):
                raise AppError("same_location", "cLocTo")
        else:
            m["cWhTo"], m["cLocTo"] = "", ""

        if prod.get("lLotControl") and not m.get("cLot"):
            raise AppError("lot_required", "cLot")
        if prod.get("lSerialControl"):
            if not m.get("cSerial"):
                raise AppError("serial_required", "cSerial")
            if abs(q) != 1 and m["cType"] != "RSV":
                raise AppError("serial_qty", "dQty")
        if prod.get("lExpiryControl") and m["cType"] == "IN" and not m.get("dExpiry"):
            raise AppError("required", "dExpiry")

        bal = self.balances(staged)
        key = (
            prod["cCode"].upper(),
            wh["cCode"].upper(),
            text(m.get("cLocation")).upper(),
            text(m.get("cLot")).upper(),
            text(m.get("cSerial")).upper(),
        )
        b = bal.get(key, {"qty": 0.0, "reserved": 0.0})
        decrease = -q if m["cType"] in ("ADJ", "CNT") and q < 0 else q if m["cType"] in ("OUT", "TRF") else 0
        if decrease and b["qty"] - b["reserved"] - decrease < -1e-9 and not wh.get("lAllowNegative"):
            raise AppError("insufficient_stock", "dQty", detail=quantity(b["qty"] - b["reserved"]))
        if m["cType"] == "RSV":
            if q > 0 and b["qty"] - b["reserved"] - q < -1e-9:
                raise AppError("insufficient_stock", "dQty", detail=quantity(b["qty"] - b["reserved"]))
            if q < 0 and b["reserved"] + q < -1e-9:
                raise AppError("insufficient_reserved", "dQty", detail=quantity(b["reserved"]))
        if (
            prod.get("lSerialControl")
            and increases_stock(m)
            and any(
                k[0] == prod["cCode"].upper() and k[4] == text(m.get("cSerial")).upper() and v["qty"] > 1e-9
                for k, v in bal.items()
            )
        ):
            raise AppError("duplicate", "cSerial", 409)  # a serial number is in stock once only

        # Mixing rules of the location that receives the stock
        incoming = dest if m["cType"] == "TRF" else (wh, loc) if increases_stock(m) or m["cType"] == "IN" else None
        if incoming and incoming[1] is not None:
            iw, il = incoming
            others = [
                k
                for k, v in bal.items()
                if k[1] == iw["cCode"].upper() and k[2] == il["cCode"].upper() and v["qty"] > 1e-9
            ]
            field = "cLocTo" if m["cType"] == "TRF" else "cLocation"
            if not il.get("lMixProducts", True) and any(k[0] != prod["cCode"].upper() for k in others):
                raise AppError("location_mixed", field)
            # One lot of a product per location, always: another lot of the same product must go elsewhere
            other_lot = next(
                (k[3] for k in others if k[0] == prod["cCode"].upper() and k[3] != text(m.get("cLot")).upper()), None
            )
            if other_lot is not None:
                raise AppError("location_mixed_lots", field, detail=other_lot or "-")
        return prod

    def post(self, m: Row, prod: Row) -> Row:
        """Cost the movement (the product's costing) and add it to the ledger.

        The product is read again: a document checks all its lines first, so two lines of the same product would
        otherwise cost the second one with the average before the first."""
        prod = self.products_repo.get(prod["cCode"]) or prod
        q = number(m["dQty"])
        qty_before = self.product_totals(prod["cCode"])[0]
        costing = costing_of(prod)
        avg = number(prod.get("dAvgCost"))
        if increases_stock(m):
            cost = costing.receipt_cost(prod, m)
            costing.receive(prod, qty_before, q, cost, is_purchase=m["cType"] in PURCHASE_TYPES)
            self.products_repo.update(prod)
            m["dUnitCost"] = unit_cost(cost)
            m["dValue"] = amount(q * cost)
        elif m["cType"] in ("OUT", "ADJ", "CNT"):
            m["dUnitCost"] = unit_cost(avg)
            m["dValue"] = amount(-abs(q) * avg)
        else:  # TRF, RSV: no change in value
            m["dUnitCost"] = unit_cost(avg)
            m["dValue"] = "0.00"
        m["dAvgCostAfter"] = prod.get("dAvgCost", "")
        m["cUser"] = m.get("cUser") or self.username()
        m["dCreated"] = datetime.now().isoformat(timespec="seconds")
        return self.ledger.append(m)

    def add(self, payload: Row, user: str | None = None) -> Row:
        """Check, cost and post a movement from a payload (a screen, another module, the seed)."""
        m = self.movement_from(payload)
        prod = self.check(m)
        if user:
            m["cUser"] = user
        return self.post(m, prod)

    def view(self, m: Row, products: dict[str, Row] | None = None) -> Row:
        prod = (products or {}).get(m["cProduct"].upper()) if products is not None else None
        if prod is None:
            prod = self.products_repo.get(m["cProduct"]) or {}
        return {
            **m,
            "cDescFR": prod.get("cDescFR", ""),
            "cDescEN": prod.get("cDescEN", ""),
            "cUOM": prod.get("cStockUOM", ""),
        }

    def movements_view(self) -> list[Row]:
        products = {p["cCode"].upper(): p for p in self.products_repo.all(lines=False)}
        return [self.view(m, products) for m in self.ledger.all()]

    def get_movement(self, no: int) -> Row:
        m = self.ledger.get(no)
        if m is None:
            raise AppError("not_found", status=404)
        return self.view(m)

    # ---------------------------------------------------------- lists
    @staticmethod
    def unit_cost(prod: Row) -> float:
        return costing_of(prod).unit_cost(prod)

    def stock_rows(self, include_zero: bool = False) -> list[Row]:
        rows = []
        products = {p["cCode"].upper(): p for p in self.products_repo.all()}
        for b in self.balances().values():
            if not include_zero and abs(b["qty"]) < 1e-9 and abs(b["reserved"]) < 1e-9:
                continue
            prod = products.get(b["cProduct"].upper(), {})
            loc = self.locations.find_in(b["cWarehouse"], b["cLocation"]) if b["cLocation"] else None
            rows.append(
                {
                    "cProduct": b["cProduct"],
                    "cDescFR": prod.get("cDescFR", ""),
                    "cDescEN": prod.get("cDescEN", ""),
                    "cCategory": prod.get("cCategory", ""),
                    "cWarehouse": b["cWarehouse"],
                    "cLocation": b["cLocation"],
                    "cZone": (loc or {}).get("cZone", ""),
                    "cLocationType": (loc or {}).get("cType", ""),
                    "cLot": b["cLot"],
                    "cSerial": b["cSerial"],
                    "dExpiry": b["dExpiry"],
                    "dQtyOnHand": quantity(b["qty"]),
                    "dQtyReserved": quantity(b["reserved"]),
                    "dQtyAvailable": quantity(b["qty"] - b["reserved"]),
                    "cUOM": prod.get("cStockUOM", ""),
                    "dValue": amount(b["qty"] * self.unit_cost(prod)) if prod else "0.00",
                }
            )
        rows.sort(key=lambda r: (r["cProduct"], r["cWarehouse"], r["cLocation"], r["cLot"], r["cSerial"]))
        return rows

    def statement(
        self,
        product: str,
        warehouse: str,
        location: str = "",
        lot: str = "",
        serial: str = "",
        date_from: str = "",
        date_to: str = "",
    ) -> Row:
        """The stock card of one stock line (product + warehouse + location + lot + serial): every movement that
        changed it, in date order, with what came in, what went out and the balance after each one. Movements
        before `date_from` make the opening balance; reservations change the reserved quantity, not the balance."""
        prod = self.products_repo.get(product) if text(product) else None
        if prod is None:
            raise AppError("not_found", status=404)
        key = (prod["cCode"].upper(), text(warehouse).upper(), text(location).upper())
        lot_u, serial_u = text(lot).upper(), text(serial).upper()
        hits: list[tuple[Row, float, float]] = []
        for m in self.ledger.all():
            if m["cProduct"].upper() != key[0] or text(m.get("cLot")).upper() != lot_u:
                continue
            if text(m.get("cSerial")).upper() != serial_u:
                continue
            for wh, loc, dq, dr in effects(m):
                if (wh.upper(), text(loc).upper()) == key[1:]:
                    hits.append((m, dq, dr))
        hits.sort(key=lambda h: (text(h[0].get("dDate")), int(h[0].get("iNo") or 0)))
        ids = {t: fn() for t, fn in self.document_ids.items() if any(h[0].get("cDocType") == t for h in hits)}
        balance = reserved = opening = opening_res = 0.0
        rows: list[Row] = []
        for m, dq, dr in hits:
            balance = round(balance + dq, 6)
            reserved = round(reserved + dr, 6)
            day = text(m.get("dDate"))
            if date_from and day < date_from:
                opening, opening_res = balance, reserved
                continue
            if date_to and day > date_to:
                continue
            doc_id = ids.get(text(m.get("cDocType")), {}).get(text(m.get("cDocNo")))
            unit = number(m.get("dUnitCost"))
            rows.append(
                {
                    "iNo": m["iNo"],
                    "dDate": day,
                    "cType": m["cType"],
                    "cDocType": text(m.get("cDocType")),
                    "cDocNo": text(m.get("cDocNo")),
                    "iDocId": doc_id if doc_id is not None else "",
                    "cReason": text(m.get("cReason")),
                    "cUser": text(m.get("cUser")),
                    "dQtyIn": quantity(dq) if dq > 0 else "",
                    "dQtyOut": quantity(-dq) if dq < 0 else "",
                    "dQtyReserved": quantity(dr) if dr else "",
                    "dBalance": quantity(balance),
                    "dUnitCost": m.get("dUnitCost", ""),
                    "dValue": amount(dq * unit) if dq else "",
                    "lTransfer": m["cType"] == "TRF",
                    "cFrom": (
                        (m["cWarehouse"] + (" / " + m["cLocation"] if m.get("cLocation") else ""))
                        if m["cType"] == "TRF"
                        else ""
                    ),
                    "cTo": (
                        (m["cWhTo"] + (" / " + m["cLocTo"] if m.get("cLocTo") else "")) if m["cType"] == "TRF" else ""
                    ),
                }
            )
        b = self.balances().get((*key, lot_u, serial_u), {"qty": 0.0, "reserved": 0.0, "dExpiry": ""})
        place: Row = (self.locations.find_in(warehouse, location) if text(location) else None) or {}
        house: Row = (self.warehouses_repo.get(warehouse) if text(warehouse) else None) or {}
        last = next((m for m, dq, _dr in reversed(hits) if dq > 0 and m.get("dExpiry")), None)
        return {
            "cProduct": prod["cCode"],
            "cDescFR": prod.get("cDescFR", ""),
            "cDescEN": prod.get("cDescEN", ""),
            "cUOM": prod.get("cStockUOM", ""),
            "cWarehouse": house.get("cCode", text(warehouse)),
            "cWarehouseName": house.get("cNameFR", ""),
            "cLocation": place.get("cCode", text(location)),
            "cLot": text(lot),
            "cSerial": text(serial),
            "dExpiry": b.get("dExpiry") or (last or {}).get("dExpiry", ""),
            "lLotControl": bool(prod.get("lLotControl")),
            "dFrom": date_from,
            "dTo": date_to,
            "dOpening": quantity(opening),
            "dOpeningReserved": quantity(opening_res),
            "dQtyOnHand": quantity(b["qty"]),
            "dQtyReserved": quantity(b["reserved"]),
            "dQtyAvailable": quantity(b["qty"] - b["reserved"]),
            "dClosing": quantity(rows[-1]["dBalance"]) if rows else quantity(opening),
            "items": rows,
        }

    def valuation_rows(self) -> list[Row]:
        per: dict[tuple[str, str], dict[str, Any]] = {}
        for b in self.balances().values():
            k = (b["cProduct"].upper(), b["cWarehouse"].upper())
            per.setdefault(k, {"cProduct": b["cProduct"], "cWarehouse": b["cWarehouse"], "qty": 0.0})["qty"] += b["qty"]
        rows = []
        for v in per.values():
            prod = self.products_repo.get(v["cProduct"]) or {}
            cost = self.unit_cost(prod)
            if abs(v["qty"]) < 1e-9:
                continue
            rows.append(
                {
                    "cProduct": v["cProduct"],
                    "cDescFR": prod.get("cDescFR", ""),
                    "cDescEN": prod.get("cDescEN", ""),
                    "cCategory": prod.get("cCategory", ""),
                    "cWarehouse": v["cWarehouse"],
                    "cCostMethod": prod.get("cCostMethod", "avg"),
                    "dQtyOnHand": quantity(v["qty"]),
                    "cUOM": prod.get("cStockUOM", ""),
                    "dUnitCost": unit_cost(cost),
                    "dValue": amount(v["qty"] * cost),
                    "cGLInventory": prod.get("cGLInventory", ""),
                }
            )
        rows.sort(key=lambda r: (r["cProduct"], r["cWarehouse"]))
        return rows

    def product_view(self, r: Row, full: bool = True) -> Row:
        """A product with its stock: totals in lists; by warehouse, value, on order and margin for one product."""
        out = dict(r)
        if not full:
            qty, res = self.product_totals(r["cCode"])
            out.update({"dQtyOnHand": quantity(qty), "dQtyAvailable": quantity(qty - res)})
            return out
        rows: dict[str, dict[str, Any]] = {}
        for (p, w, *_rest), b in self.balances().items():
            if p != r["cCode"].upper():
                continue
            s = rows.setdefault(w, {"cWarehouse": b["cWarehouse"], "qty": 0.0, "reserved": 0.0})
            s["qty"] += b["qty"]
            s["reserved"] += b["reserved"]
        cost = self.unit_cost(r)
        stock = []
        for s in rows.values():
            wh = self.warehouses_repo.get(s["cWarehouse"])
            par = self.params_repo.get(r["cCode"], s["cWarehouse"])
            stock.append(
                {
                    "cWarehouse": s["cWarehouse"],
                    "cWarehouseName": (wh or {}).get("cNameFR", ""),
                    "dQtyOnHand": quantity(s["qty"]),
                    "dQtyReserved": quantity(s["reserved"]),
                    "dQtyAvailable": quantity(s["qty"] - s["reserved"]),
                    "dValue": amount(s["qty"] * cost),
                    "dReorderPoint": (par or {}).get("dReorderPoint", ""),
                }
            )
        qty = sum(s["qty"] for s in rows.values())
        res = sum(s["reserved"] for s in rows.values())
        price = number(r.get("dPrice1"))
        out.update(
            {
                "stock": sorted(stock, key=lambda s: s["cWarehouse"]),
                "dQtyOnHand": quantity(qty),
                "dQtyReserved": quantity(res),
                "dQtyAvailable": quantity(qty - res),
                "dQtyOnOrder": quantity(self.on_order(r["cCode"])),
                "dStockValue": amount(qty * cost),
                "dMarginPct": f"{(price - cost) / price * 100:.1f}" if price and cost else "",
            }
        )
        return out
