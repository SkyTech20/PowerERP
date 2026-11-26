"""The shop floor of a production order (M3b): issue the materials by lot, give them back, report the product made.

An order released (or in progress) moves the stock, one stock movement per lot, document PROD with the order number:
- issue: the materials go out of their warehouse (the material's, else the order's), lot by lot in the order of the
  product's pick policy (FEFO for a product with an expiry date, inventory/picking.py); an expired lot or a blocked
  location is never used; by default each material not backflushed takes what is left to issue
  (required - issued). issue_check() shows the lots it would take, without moving anything;
- return: a quantity issued comes back into the lot and location it went out of, at the cost it went out at;
- report: the quantity made goes into the order's warehouse: lot = the one typed, else the order's, else MO<order>
  for a lot-controlled product; expiry = the one typed, else the day + the shelf life of the product; location = the
  one typed, else the default location of the product in the warehouse (Inventory > Replenishment parameters), else
  the warehouse's receiving location (also when the default location holds another lot: one lot per location).
  The product goes in at the estimated unit cost of the order. Before it, the backflushed materials go out for the
  quantity reported (required x reported / quantity of the order).
Every movement is checked by the stock service first; nothing moves while one problem is left. The first movement
puts a released order in progress. The order keeps what went out (issues: the lots used) and what came in (outputs:
the lots made): its genealogy.
"""

from __future__ import annotations

import copy
from collections.abc import Callable
from datetime import date, timedelta
from typing import Any

from powererp.core.errors import AppError
from powererp.core.values import amount, number, quantity, text, today, unit_cost
from powererp.modules.inventory.picking import location_usable, pick_order, received_dates, shortage_code

from .orders import EPS, ProductionOrderService

Row = dict[str, Any]
Rows = list[Row]
DOC_TYPE = "PROD"
FLOOR = ("released", "in_progress")
MIXED = ("location_mixed", "location_mixed_lots")


class ShopFloorService:
    def __init__(self, orders: ProductionOrderService, username: Callable[[], str]):
        self.orders = orders
        self.refs = orders.refs
        self.username = username

    @property
    def stock(self) -> Any:
        return self.refs["stock"]()

    # ---------------------------------------------------------- issue
    def issue_check(self, no: int, payload: Row) -> Row:
        """The lots an issue would take: {ok, problems, allocations}. Nothing moves."""
        order = self._floor(no)
        wanted, problems = self._wanted(order, payload)
        rows, more = self._allocate(order, wanted, self._day(payload), "issue")
        problems += more
        if not wanted and not problems:
            problems.append(self._problem(None, "nothing_to_issue", ""))
        return {"ok": not problems, "problems": problems, "allocations": rows}

    def issue(self, no: int, payload: Row) -> Row:
        check = self.issue_check(no, payload)
        self._raise(check["problems"])
        order = self._floor(no)
        self._post(order, check["allocations"])
        return self._save(order)

    def _wanted(self, order: Row, payload: Row) -> tuple[list[tuple[Row, float]], Rows]:
        """(material, quantity to issue): the lines given ({iSeq, dQty}), else what is left of each material that is
        not backflushed."""
        lines = payload.get("lines")
        if lines is None:
            out = [(m, self._left(m)) for m in order["materials"] if m["cIssueMethod"] != "backflush"]
            return [(m, q) for m, q in out if q > EPS], []
        mats = {int(m["iSeq"]): m for m in order["materials"]}
        wanted: list[tuple[Row, float]] = []
        problems: Rows = []
        for ln in lines:
            m = mats.get(int(number(ln.get("iSeq"))))
            if m is None:
                problems.append(self._problem(None, "unknown_ref", text(ln.get("iSeq"))))
                continue
            q = round(number(ln.get("dQty")), 6)
            if q < 0:
                problems.append(self._problem(m, "positive", ""))
            elif q > EPS:
                wanted.append((m, q))
        return wanted, problems

    @staticmethod
    def _left(m: Row) -> float:
        return round(max(number(m["dQtyRequired"]) - number(m["dQtyIssued"]), 0.0), 6)

    def _allocate(self, order: Row, wanted: list[tuple[Row, float]], day: str, kind: str) -> tuple[Rows, Rows]:
        """The lots each material takes, in the order of its pick policy, against the stock and what the previous
        materials already took."""
        stock = self.stock
        bal = {k: dict(v) for k, v in stock.balances().items()}
        received = received_dates(stock, {m["cComponent"].upper() for m, _q in wanted})
        held = self.refs.get("held_lots", set)()
        rows: Rows = []
        problems: Rows = []
        for m, need in wanted:
            prod = self.refs["products"](m["cComponent"]) or {}
            if not prod.get("lStocked"):
                continue  # not followed in the stock: nothing goes out
            wh_code = text(m.get("cWarehouse")) or order["cWarehouse"]
            wh = self.refs["warehouses"](wh_code) or {"cCode": wh_code}

            def usable(location: str, w: str = wh["cCode"]) -> bool:
                return location_usable(stock, w, location)

            left = need
            for b, free in pick_order(prod, wh["cCode"], bal, day, received, usable, held):
                if left <= EPS:
                    break
                take = round(min(free, left), 6)
                b["qty"] = round(b["qty"] - take, 6)
                left = round(left - take, 6)
                rows.append(self._row(m, wh["cCode"], b, take, kind, day))
            if left > EPS:
                lots = prod.get("lLotControl") or prod.get("lSerialControl")
                if wh.get("lAllowNegative") and not lots:
                    rows.append(self._row(m, wh["cCode"], {}, left, kind, day))
                    continue
                problems.append(
                    self._problem(
                        m,
                        shortage_code(prod, wh["cCode"], bal, held),
                        f"{quantity(need)} > {quantity(need - left)} {m['cUOM']}",
                    )
                )
        return rows, problems

    def _row(self, m: Row, wh: str, b: Row, qty: float, kind: str, day: str) -> Row:
        return {
            "iMovement": 0,
            "dDate": day,
            "cUser": self.username(),
            "cKind": kind,
            "iSeq": m["iSeq"],
            "cComponent": m["cComponent"],
            "cWarehouse": wh,
            "cLocation": b.get("cLocation", ""),
            "cLot": b.get("cLot", ""),
            "cSerial": b.get("cSerial", ""),
            "dExpiry": text(b.get("dExpiry"))[:10],
            "dQty": quantity(qty),
            "cUOM": m["cUOM"],
            "dValue": "",
        }

    # ---------------------------------------------------------- return
    def give_back(self, no: int, payload: Row) -> Row:
        """A quantity issued comes back into its lot and location: {iSeq, cLot, cLocation, cSerial, dQty}."""
        order = self._floor(no)
        q = round(number(payload.get("dQty")), 6)
        if q <= 0:
            raise AppError("positive" if text(payload.get("dQty")) else "required", "dQty")
        same = [
            i
            for i in order["issues"]
            if int(i["iSeq"]) == int(number(payload.get("iSeq")))
            and all(text(i[f]).upper() == text(payload.get(f)).upper() for f in ("cLot", "cLocation", "cSerial"))
        ]
        net = sum(number(i["dQty"]) for i in same)
        if not same or net <= EPS:
            raise AppError("not_issued", "iSeq", status=409)
        if q > net + EPS:
            raise AppError("over_return", "dQty", status=409, detail=quantity(net))
        value = sum(number(i["dValue"]) for i in same)
        first = next(i for i in same if i["cKind"] != "return")
        row = {**first, "iMovement": 0, "dDate": self._day(payload), "cUser": self.username(), "cKind": "return"}
        row["dQty"] = quantity(-q)
        row["_unit"] = value / net if net else 0.0
        self._post(order, [row])
        return self._save(order)

    # ---------------------------------------------------------- report
    def report(self, no: int, payload: Row) -> Row:
        """The quantity made goes into the stock (see the module's docstring): {dQty, cLot, dExpiry, cLocation, dDate}."""
        order = self._floor(no)
        records = self.orders.records
        if records is not None:
            records.check_not_blocked(order)  # a critical "block" step out of its limits
        qty = round(number(payload.get("dQty")), 6)
        if qty <= 0:
            raise AppError("positive" if text(payload.get("dQty")) else "required", "dQty")
        day = self._day(payload)
        share = qty / number(order["dQty"]) if number(order["dQty"]) > EPS else 0.0
        flush = [
            (m, round(number(m["dQtyRequired"]) * share, 6))
            for m in order["materials"]
            if m["cIssueMethod"] == "backflush"
        ]
        rows, problems = self._allocate(order, [(m, q) for m, q in flush if q > EPS], day, "backflush")
        self._raise(problems)
        output = self._output(order, payload, qty, day)
        made = {text(o.get("cLot")).upper() for o in order["outputs"]}
        self._post(order, rows, output)
        order["dQtyDone"] = quantity(number(order["dQtyDone"]) + qty)
        if output["cLot"] and not order["cLot"]:
            order["cLot"] = output["cLot"]
        saved = self._save(order)
        if records is not None and output["cLot"] and output["cLot"].upper() not in made:
            records.hold_new_lot(order, output["cLot"])  # after a "hold the lot" deviation of the order
        return saved

    def _output(self, order: Row, payload: Row, qty: float, day: str) -> Row:
        prod = self.refs["products"](order["cProduct"]) or {}
        wh = self.refs["warehouses"](order["cWarehouse"]) or {"cCode": order["cWarehouse"]}
        lot = text(payload.get("cLot")) or order["cLot"]
        if prod.get("lLotControl") and not lot:
            lot = f"MO{order['iNo']}"
        expiry = text(payload.get("dExpiry"))
        if prod.get("lExpiryControl") and not expiry:
            expiry = self._expiry(day, prod)
            if not expiry:
                raise AppError("required", "dExpiry")
        to_stock = self.refs["recipes"]._factor(order["cUOM"], prod) or 1.0  # recipe unit -> stock unit
        location = text(payload.get("cLocation"))
        return {
            "iMovement": 0,
            "dDate": day,
            "cUser": self.username(),
            "dQty": quantity(qty * to_stock),
            "cUOM": text(prod.get("cStockUOM")) or order["cUOM"],
            "cWarehouse": wh["cCode"],
            "cLocation": location or self._location(prod, wh),
            "_auto": not location,
            "_receiving": text(wh.get("cReceivingLoc")),
            "cLot": lot if prod.get("lLotControl") else text(payload.get("cLot")),
            "dExpiry": expiry,
            "dUnitCost": unit_cost(number(order["dEstUnitCost"]) / to_stock),
            "dValue": "",
        }

    @staticmethod
    def _expiry(day: str, prod: Row) -> str:
        days = int(number(prod.get("iShelfLifeDays")))
        if days <= 0:
            return ""
        return (date.fromisoformat(day) + timedelta(days=days)).isoformat()

    def _location(self, prod: Row, wh: Row) -> str:
        """The default location of the product in the warehouse, else the warehouse's receiving location."""
        for p in self.stock.params_repo.all():
            if (
                text(p.get("cProduct")).upper() == prod.get("cCode", "").upper()
                and text(p.get("cWarehouse")).upper() == wh["cCode"].upper()
                and text(p.get("cDefaultLocation"))
            ):
                return text(p["cDefaultLocation"])
        return text(wh.get("cReceivingLoc"))

    # ---------------------------------------------------------- posting
    def _post(self, order: Row, rows: Rows, output: Row | None = None) -> None:
        """Check every movement (with the ones before it), then post them all and keep them on the order."""
        stock = self.stock
        staged: list[tuple[Row, Row]] = []
        for r in rows:
            m = stock.movement_from(self._payload(order, r))
            try:
                staged.append((m, stock.check(m, [s for s, _p in staged])))
            except AppError as e:
                raise AppError(
                    e.code, e.field, e.status, detail=f"{r['cComponent']} {e.detail or ''}".strip()
                ) from None
        if output is not None:
            while True:
                m = stock.movement_from(self._out_payload(order, output))
                try:
                    staged.append((m, stock.check(m, [s for s, _p in staged])))
                    break
                except AppError as e:
                    receiving = output["_receiving"]
                    if (
                        output["_auto"]
                        and e.code in MIXED
                        and receiving
                        and output["cLocation"].upper() != receiving.upper()
                    ):
                        output["cLocation"], output["_auto"] = receiving, False
                        continue
                    raise
        done = [stock.post(m, prod) for m, prod in staged]
        for r, d in zip(rows, done, strict=False):
            r.pop("_unit", None)
            r["iMovement"] = d["iNo"]
            r["dValue"] = amount(-number(d["dValue"]))  # the cost taken by the order (negative for a return)
            order["issues"].append(r)
            for mat in order["materials"]:
                if int(mat["iSeq"]) == int(r["iSeq"]):
                    mat["dQtyIssued"] = quantity(number(mat["dQtyIssued"]) + number(r["dQty"]))
        if output is not None:
            d = done[-1]
            output.pop("_auto", None)
            output.pop("_receiving", None)
            output["iMovement"] = d["iNo"]
            output["dValue"] = amount(number(d["dValue"]))
            order["outputs"].append(output)
        if order["cStatus"] == "released":
            order["history"].append(self.orders._event("start", "released", "in_progress", ""))
            order["cStatus"] = "in_progress"

    @staticmethod
    def _payload(order: Row, r: Row) -> Row:
        q = number(r["dQty"])
        back = q < 0
        p = {
            "cType": "ADJ" if back else "OUT",  # a return comes back at the cost it went out at, into its lot
            "cProduct": r["cComponent"],
            "dQty": quantity(abs(q)),
            "cWarehouse": r["cWarehouse"],
            "cLocation": r["cLocation"],
            "cLot": r["cLot"],
            "cSerial": r["cSerial"],
            "cDocType": DOC_TYPE,
            "cDocNo": str(order["iNo"]),
            "cReason": order["cProduct"],
            "dDate": r["dDate"],
        }
        if back:
            p["dUnitCost"] = unit_cost(r.get("_unit", 0.0))
            p["dExpiry"] = r["dExpiry"]
        return p

    @staticmethod
    def _out_payload(order: Row, o: Row) -> Row:
        return {
            "cType": "IN",
            "cProduct": order["cProduct"],
            "dQty": o["dQty"],
            "dUnitCost": o["dUnitCost"],
            "cWarehouse": o["cWarehouse"],
            "cLocation": o["cLocation"],
            "cLot": o["cLot"],
            "dExpiry": o["dExpiry"],
            "cDocType": DOC_TYPE,
            "cDocNo": str(order["iNo"]),
            "cReason": order["cProduct"],
            "dDate": o["dDate"],
        }

    # ---------------------------------------------------------- helpers
    def _floor(self, no: int) -> Row:
        order = copy.deepcopy(self.orders.get(no))
        if order["cStatus"] not in FLOOR:
            raise AppError("invalid_status", status=409, detail=order["cStatus"])
        order.setdefault("issues", [])
        order.setdefault("outputs", [])
        return order

    def _save(self, order: Row) -> Row:
        self.orders.repo.update(order, [order["iNo"]])
        return self.orders.view(order)

    @staticmethod
    def _day(payload: Row) -> str:
        day = text(payload.get("dDate"))[:10] or today()
        try:
            date.fromisoformat(day)
        except ValueError:
            raise AppError("invalid_date", "dDate") from None
        return day

    @staticmethod
    def _problem(m: Row | None, code: str, detail: str) -> Row:
        return {
            "iSeq": m["iSeq"] if m else 0,
            "cComponent": m["cComponent"] if m else "",
            "code": code,
            "detail": detail,
        }

    @staticmethod
    def _raise(problems: Rows) -> None:
        if problems:
            p = problems[0]
            detail = f"{p['cComponent']} {p['detail']}".strip()
            status = 409 if p["code"] in ("insufficient_stock", "nothing_to_issue") else 400
            raise AppError(p["code"], "materials", status, detail=detail or None)
