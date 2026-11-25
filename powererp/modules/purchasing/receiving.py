"""Entry of a reception into the stock: check what it would put in, then post it once.

check(no) lists, without changing anything, what each line will put into the stock and what must be fixed first:
- a line with a product of the item master goes in, in stock units (the quantities of a reception are in stock
  units, like the PO lines), at its unit cost, in the reception's warehouse;
- a line without an item (freight, a service) or with a product that is not stocked (a fixed asset) is skipped;
- the location: the line's, else the default location of the product in that warehouse (Inventory > Replenishment
  parameters), else the receiving location of the warehouse; when the default location holds another lot of the
  product (one lot per location) or another product (no mixing), the receiving location is taken instead;
- the lot of a lot-controlled product: the line's, else <reception>-<line> (e.g. 900107-2); the supplier's lot
  (cSupplierLot) is kept with it, for the traceability "one step back";
- the expiry of an expiry-controlled product: the line's, else the reception date + the shelf life of the product;
- every movement is then checked by the stock service (blocked locations, one lot per location, serial numbers...).
post(no) checks again and, when nothing is left to fix, posts one IN movement per line (document REC <number>),
writes the location / lot / expiry used on the lines and marks the reception as in stock: it can no longer be
changed or deleted (a mistake is corrected with a stock movement).
"""

from __future__ import annotations

import copy
from collections.abc import Callable
from datetime import date, datetime, timedelta
from typing import Any

from powererp.core.errors import AppError
from powererp.core.values import amount, number, quantity, text, unit_cost

from . import repository as repo
from .services import ReceptionService

Row = dict[str, Any]
Rows = list[Row]

DOC_TYPE = "REC"
MIXED = ("location_mixed", "location_mixed_lots")  # the rules of a location that another location may not have


class ReceptionStockService:
    def __init__(self, receptions: ReceptionService, stock: Callable[[], Any], username: Callable[[], str]):
        self.receptions = receptions
        self._stock = stock  # the StockService (registered after Purchasing)
        self.username = username

    @property
    def stock(self) -> Any:
        return self._stock()

    # ---------------------------------------------------------- view
    def with_stock(self, view: Row) -> Row:
        """The reception, with the movements it posted (`movements`) once it is in the stock."""
        if not view.get("lStockPosted"):
            return view
        return {**view, "movements": self.movements(view["NoReception"])}

    def movements(self, no: str) -> Rows:
        stock = self.stock
        return [
            stock.view(m)
            for m in stock.ledger.all()
            if m.get("cDocType") == DOC_TYPE and text(m.get("cDocNo")) == text(no)
        ]

    # ---------------------------------------------------------- check
    def check(self, no: str) -> Row:
        """What posting would put into the stock: {ok, problems: [{iLine, cProduct, code, field, detail}],
        entries: [...], warnings: [...]}. Nothing is saved."""
        rec = self.receptions.not_posted(no)
        problems: Rows = []
        entries: Rows = []
        warnings: Rows = []
        wh = self._warehouse(rec, problems)
        if text(rec.get("Devise")) not in ("", "CAD"):
            warnings.append({"iLine": 0, "code": "currency_not_cad", "detail": text(rec.get("Devise"))})
        staged: Rows = []
        for i, ln in enumerate(rec["lines"], 1):
            entry = self._entry(rec, wh, i, ln, problems)
            if entry is None:
                continue
            auto = entry.pop("_auto", False)
            entries.append(entry)
            if entry["cSkip"] or wh is None:
                continue
            m = self._checked(rec, wh, entry, auto, ln, staged, problems)
            if m is not None:
                staged.append(m)
        if not any(not e["cSkip"] for e in entries) and not problems:
            problems.append({"iLine": 0, "cProduct": "", "code": "no_lines", "field": "lines", "detail": ""})
        return {"ok": not problems, "problems": problems, "entries": entries, "warnings": warnings}

    def _checked(self, rec: Row, wh: Row, entry: Row, auto: bool, ln: Row, staged: Rows, problems: Rows) -> Row | None:
        """The movement of a line, checked by the stock service. A location chosen by the ERP that already holds
        another lot (or another product) of the location's rules gives way to the receiving location."""
        while True:
            m = self.stock.movement_from(self._payload(rec, entry))
            try:
                self.stock.check(m, staged)
                return m
            except AppError as e:
                receiving = text(wh.get("cReceivingLoc"))
                if auto and e.code in MIXED and receiving and entry["cLocation"].upper() != receiving.upper():
                    entry["cLocation"], auto = receiving, False
                    continue
                problems.append(self._problem(entry["iLine"], ln, e))
                return None

    def _warehouse(self, rec: Row, problems: Rows) -> Row | None:
        code = text(rec.get("Entrepot"))
        wh = self.stock.warehouses_repo.get(code) if code else None
        if wh is None:
            code_ = "unknown_ref" if code else "required"
            problems.append({"iLine": 0, "cProduct": "", "code": code_, "field": "Entrepot", "detail": code})
        return wh

    def _entry(self, rec: Row, wh: Row | None, i: int, ln: Row, problems: Rows) -> Row | None:
        code = text(ln.get("CodeArticle"))
        qty = number(ln.get("QuantiteRecue"))
        base = {
            "iLine": i,
            "cProduct": code,
            "cDescription": text(ln.get("Description")),
            "dQty": quantity(qty),
            "cUOM": "",
            "dUnitCost": text(ln.get("PrixUnitaire")),
            "cLocation": "",
            "cLot": "",
            "cSupplierLot": text(ln.get("cSupplierLot")),
            "cSerial": text(ln.get("cSerial")),
            "dExpiry": "",
            "cSkip": "",
        }
        if not code:
            return {**base, "cSkip": "no_item"}
        prod = self.stock.products_repo.get(code)
        if prod is None:
            problems.append({"iLine": i, "cProduct": code, "code": "unknown_ref", "field": "CodeArticle", "detail": ""})
            return None
        base.update(cProduct=prod["cCode"], cUOM=text(prod.get("cStockUOM")))
        if not prod.get("lStocked"):
            return {**base, "cSkip": "not_stocked"}
        if qty == 0:
            return {**base, "cSkip": "nothing_received"}
        if qty < 0:
            problems.append({"iLine": i, "cProduct": code, "code": "positive", "field": "QuantiteRecue", "detail": ""})
            return None
        lot = text(ln.get("cLot"))
        if prod.get("lLotControl") and not lot:
            lot = f"{rec['NoReception']}-{i}"
        expiry = text(ln.get("dExpiry"))
        if prod.get("lExpiryControl") and not expiry:
            expiry = self._expiry(rec, prod)
            if not expiry:
                problems.append({"iLine": i, "cProduct": code, "code": "required", "field": "dExpiry", "detail": ""})
                return None
        base.update(
            cDescription=base["cDescription"] or text(prod.get("cDescFR")),
            cLocation=text(ln.get("cLocation")) or (self._location(prod, wh) if wh else ""),
            _auto=not text(ln.get("cLocation")),
            cLot=lot if prod.get("lLotControl") else text(ln.get("cLot")),
            dExpiry=expiry,
        )
        return base

    @staticmethod
    def _expiry(rec: Row, prod: Row) -> str:
        days = int(number(prod.get("iShelfLifeDays")))
        received = text(rec.get("DateReception"))[:10]
        if days <= 0 or not received:
            return ""
        try:
            return (date.fromisoformat(received) + timedelta(days=days)).isoformat()
        except ValueError:
            return ""

    def _location(self, prod: Row, wh: Row) -> str:
        """The default location of the product in the warehouse, else the warehouse's receiving location."""
        for p in self.stock.params_repo.all():
            if (
                text(p.get("cProduct")).upper() == prod["cCode"].upper()
                and text(p.get("cWarehouse")).upper() == wh["cCode"].upper()
                and text(p.get("cDefaultLocation"))
            ):
                return text(p["cDefaultLocation"])
        return text(wh.get("cReceivingLoc"))

    @staticmethod
    def _payload(rec: Row, e: Row) -> Row:
        comment = " · ".join(x for x in (f"PO {text(rec.get('NoBonCommande'))}", e["cSupplierLot"]) if x.strip())
        return {
            "cType": "IN",
            "cProduct": e["cProduct"],
            "dQty": e["dQty"],
            "dUnitCost": e["dUnitCost"],
            "cWarehouse": text(rec.get("Entrepot")),
            "cLocation": e["cLocation"],
            "cLot": e["cLot"],
            "cSerial": e["cSerial"],
            "dExpiry": e["dExpiry"],
            "cDocType": DOC_TYPE,
            "cDocNo": rec["NoReception"],
            "cReason": text(rec.get("CodeFournisseur")),
            "cComment": comment,
            "dDate": text(rec.get("DateReception"))[:10],
        }

    @staticmethod
    def _problem(i: int, ln: Row, e: AppError) -> Row:
        field = {"cWarehouse": "Entrepot", "cProduct": "CodeArticle", "dQty": "QuantiteRecue"}.get(
            e.field or "", e.field or ""
        )
        return {
            "iLine": i,
            "cProduct": text(ln.get("CodeArticle")),
            "code": e.code,
            "field": field,
            "detail": e.detail or "",
        }

    # ---------------------------------------------------------- post
    def post(self, no: str) -> Row:
        """Check, then put the reception into the stock (see the module's docstring). The first problem is the error
        (400 / 409), and then nothing has moved."""
        result = self.check(no)
        if result["problems"]:
            p = result["problems"][0]
            detail = f"line {p['iLine']}: {p['cProduct']} {p['detail']}".strip() if p["iLine"] else p["detail"]
            raise AppError(p["code"], p["field"] or None, detail=detail or None)
        stock = self.stock
        rec = self.receptions.get(no)
        det, unb = repo.rec_get(no)
        assert det is not None
        staged: list[tuple[Row, Row]] = []
        for e in result["entries"]:
            if e["cSkip"]:
                continue
            m = stock.movement_from(self._payload(rec, e))
            staged.append((m, stock.check(m, [s for s, _p in staged])))
        for e, (m, prod) in zip([e for e in result["entries"] if not e["cSkip"]], staged, strict=True):
            done = stock.post(m, prod)
            e["iMovement"] = done["iNo"]
            e["dValue"] = amount(number(done["dValue"]))
            e["dUnitCost"] = unit_cost(number(done["dUnitCost"]))
        articles = copy.deepcopy(det.get("Articles") or [])  # the lines of the view, in the same order
        for e in result["entries"]:
            if not e["cSkip"] and e["iLine"] <= len(articles):
                articles[e["iLine"] - 1].update(
                    {"cLocation": e["cLocation"], "cLot": e["cLot"], "dExpiry": e["dExpiry"]}
                )
        det.update(
            {
                "Articles": articles,
                "lStockPosted": True,
                "dStockPosted": datetime.now().isoformat(timespec="seconds"),
                "cStockPostedBy": self.username(),
            }
        )
        repo.rec_put(no, det, unb)
        view = self.with_stock(self.receptions.get(no))
        view["entries"] = result["entries"]
        return view
