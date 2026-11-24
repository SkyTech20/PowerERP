"""Sales invoices (V3: drafts): the customer, where the goods go, the lines priced for the customer, the taxes.

What a draft is calculated from (calc(), on every save and by POST /api/sales-invoices/calc for the screen):
- the customer gives the defaults: ship-to address (its default one), warehouse, language, payment terms;
- the taxes follow the place of delivery: the tax group of the ship-to address, else the customer's (an exempt
  customer, EXO, pays none); a product whose sales tax group is zero-rated or exempt (e.g. basic groceries) keeps
  it on its line; every other line takes the invoice's;
- each line: an empty price or discount takes the customer's (PriceResolver, V2: price list, category, customer
  discount); a price typed by hand is kept (source "manual"); net price = price x (1 - discount %), never below
  the minimum price of the product; amount = quantity x net price, to the cent;
- the taxes are calculated on the total of the lines of each tax group (TaxCalculator: GST, QST, HST...), at the
  date of the invoice.

Posting (V4, post()): everything is checked first (check(): the same calculation, then the stock), and nothing
moves while one problem is left. Then, in one transaction:
- each line of a stocked product goes out of the invoice's warehouse, in stock units (the unit of the line
  converted), in the order of the product's pick policy (cPickPolicy): FEFO, the lots expiring first; FIFO, the
  stock received first; LIFO, the stock received last; empty = FEFO for a product with an expiry date, else FIFO
  (an expired lot is never sold);
  one OUT movement per lot / location / serial (document "SO", the invoice number), kept on the invoice
  (allocations) with its value at the average cost; a product not stocked (a service) does not move;
- the invoice takes its definitive number (sequence SALES_INVOICE, never below the company profile's
  iInvoiceStart, without gaps) and can no longer be changed or deleted.
"""

from __future__ import annotations

import copy
from collections.abc import Callable
from datetime import datetime
from typing import Any

from powererp import schemas as S
from powererp.core.errors import AppError, NotFound
from powererp.core.values import amount, number, quantity, text, today, unit_cost
from powererp.modules.common.forms import RecordForm, Row
from powererp.modules.common.registry import ReferenceRegistry
from powererp.modules.inventory.ledger import effects
from powererp.store import Store

DRAFT_SEQUENCE = "SALES_INVOICE_DRAFT"
INVOICE_SEQUENCE = "SALES_INVOICE"
EPS = 1e-9
Rows = list[Row]
Received = dict[tuple[str, ...], tuple[str, int, str, int]]


def _day(d: str) -> int:
    """2026-11-23 -> 20261123 (0 when empty)."""
    digits = d.replace("-", "")[:8]
    return int(digits) if digits.isdigit() else 0


def pick_policy(prod: Row) -> str:
    """FEFO / FIFO / LIFO: the product's, else FEFO when it has an expiry date, else FIFO."""
    return str(prod.get("cPickPolicy") or ("FEFO" if prod.get("lExpiryControl") else "FIFO"))


class SalesInvoiceService:
    def __init__(
        self,
        repo: Store,
        refs: dict[str, Any],
        numbering: Any,
        username: Callable[[], str],
        references: ReferenceRegistry,
    ):
        """refs: given by the container: customers, products, warehouses, tax_groups (services with find),
        pricing (PriceResolver), tax_calculator (TaxCalculator); for the posting: stock (StockService),
        unit_factor (UnitConverter.factor) and invoice_start (the first invoice number)."""
        self.repo = repo
        self.refs = refs
        self.numbering = numbering
        self.username = username
        self.form = RecordForm(S.SALES_INVOICE)
        self.line_form = RecordForm(S.SALES_INVOICE_LINE)
        references.register("customer", lambda code: self._uses("cCustomer", code))
        references.register("product", self._uses_product)

    # ---------------------------------------------------------- references
    def _uses(self, field: str, code: str) -> bool:
        return any(r[field].upper() == code.upper() for r in self.repo.all(lines=False))

    def _uses_product(self, code: str) -> bool:
        return any(ln["cProduct"].upper() == code.upper() for r in self.repo.all() for ln in r.get("lines", []))

    # ---------------------------------------------------------- read
    def list(self) -> list[Row]:
        return self.repo.all()

    def get(self, no: int) -> Row:
        inv = self.repo.get(no)
        if inv is None:
            raise NotFound()
        return inv

    def draft(self, no: int) -> Row:
        inv = self.get(no)
        if inv["cStatus"] != "draft":
            raise AppError("posted", status=409)
        return inv

    @staticmethod
    def view(inv: Row, full: bool = True) -> Row:
        if full:
            return inv
        out = {k: v for k, v in inv.items() if k not in ("lines", "taxes", "allocations")}
        out["iLines"] = len(inv.get("lines", []))
        return out

    # ---------------------------------------------------------- calculation
    def _apply(self, inv: Row, payload: Row) -> Row:
        self.form.apply(inv, payload)
        if "lines" in payload:
            inv["lines"] = self.line_form.lines(payload, lambda ln: bool(text(ln.get("cProduct"))))
        return inv

    def blank(self) -> Row:
        inv = self.form.blank()
        inv.update(
            {
                "iNo": 0,
                "cStatus": "draft",
                "cInvoiceNo": "",
                "cCustomerName": "",
                "cTaxGroup": "",
                "dSubTotal": "0.00",
                "dDiscountTotal": "0.00",
                "dTaxTotal": "0.00",
                "dTotal": "0.00",
                "cUser": "",
                "dCreated": "",
                "dPosted": "",
                "cPostedBy": "",
                "dCost": "0.00",
                "lines": [],
                "taxes": [],
                "allocations": [],
            }
        )
        return inv

    def calc(self, inv: Row) -> Row:
        """Check the draft and fill in everything calculated (see the module's docstring). Changes inv in place."""
        customer = self._header(inv)
        group = self.refs["tax_groups"].find(inv["cTaxGroup"]) if inv["cTaxGroup"] else None
        invoice_taxable = group is None or group.get("cTreatment") == "taxable"
        bases: dict[str, float] = {}
        gross = 0.0
        for i, ln in enumerate(inv.get("lines", []), 1):
            self._line(inv, customer, ln, i, invoice_taxable)
            gross += number(ln["dQty"]) * number(ln["dPrice"])
            if ln["cTaxGroup"]:
                bases[ln["cTaxGroup"]] = bases.get(ln["cTaxGroup"], 0.0) + number(ln["dAmount"])
        sub = sum(number(ln["dAmount"]) for ln in inv.get("lines", []))
        taxes: list[Row] = []
        for code in sorted(bases):
            result = self.refs["tax_calculator"].calc(code, round(bases[code], 2), inv["dDate"])
            for tx in (result or {}).get("taxes", []):
                taxes.append(
                    {
                        "cTaxGroup": code,
                        "cTaxCode": tx["cTaxCode"],
                        "cKind": tx["cKind"],
                        "dRate": tx["dRate"],
                        "dBase": tx["dBase"],
                        "dTax": tx["dTax"],
                    }
                )
        tax_total = sum(number(tx["dTax"]) for tx in taxes)
        inv["taxes"] = taxes
        inv["dSubTotal"] = amount(sub)
        inv["dDiscountTotal"] = amount(gross - sub)
        inv["dTaxTotal"] = amount(tax_total)
        inv["dTotal"] = amount(sub + tax_total)
        return inv

    def _header(self, inv: Row) -> Row:
        code = text(inv["cCustomer"])
        customer = self.refs["customers"].find(code) if code else None
        if customer is None:
            raise AppError("required" if not code else "unknown_ref", "cCustomer")
        if not customer.get("lActive"):
            raise AppError("inactive", "cCustomer")
        changed = inv.get("cCustomer") != customer["cCode"] or inv.get("cCustomerName") != customer["cName"]
        inv["cCustomer"], inv["cCustomerName"] = customer["cCode"], customer["cName"]
        customers = self.refs["customers"]
        if inv["cShipTo"]:
            address = customers.ship_to(customer, inv["cShipTo"])
            if address is None:
                raise AppError("unknown_ref", "cShipTo")
            inv["cShipTo"] = address["cCode"]
        else:
            address = customers.ship_to(customer)
            inv["cShipTo"] = address["cCode"] if address else ""
        inv["cTaxGroup"] = customers.tax_group_for(customer, inv["cShipTo"])
        inv["dDate"] = inv["dDate"] or today()
        inv["cWarehouse"] = text(inv["cWarehouse"]) or customer.get("cWarehouse", "")
        if inv["cWarehouse"]:
            wh = self.refs["warehouses"].find(inv["cWarehouse"])
            if wh is None:
                raise AppError("unknown_ref", "cWarehouse")
            inv["cWarehouse"] = wh["cCode"]
        inv["cLang"] = (text(inv["cLang"]) or customer.get("cLang") or "fr").lower()
        if inv["cLang"] not in S.LANGS:
            raise AppError("invalid_choice", "cLang")
        if changed or not inv["cTermCode"]:
            inv["cTermCode"], inv["cTermDesc"] = customer.get("cTermCode", ""), customer.get("cTermDesc", "")
        return customer

    def _line(self, inv: Row, customer: Row, ln: Row, i: int, invoice_taxable: bool) -> None:
        where = f"line {i}"
        prod = self.refs["products"].find(ln["cProduct"])
        if prod is None:
            raise AppError("unknown_ref", "lines", detail=f"{where}: {ln['cProduct']}")
        if not prod.get("lSellable") or prod.get("cStatus") != "active":
            raise AppError("not_sellable", "lines", detail=f"{where}: {prod['cCode']}")
        ln["cProduct"] = prod["cCode"]
        if not text(ln["dQty"]) or number(ln["dQty"]) <= 0:
            raise AppError("positive", "lines", detail=f"{where}: dQty")
        ln["dQty"] = quantity(number(ln["dQty"]))
        if not ln["cDescription"]:
            en = inv["cLang"] == "en" and prod.get("cDescEN")
            ln["cDescription"] = en or prod.get("cDescFR", "")
        try:
            p = self.refs["pricing"].price(customer["cCode"], prod["cCode"], ln["dQty"], ln["cUOM"], inv["dDate"])
        except AppError as e:
            raise AppError(e.code, "lines", detail=f"{where}: {e.detail or e.field}") from None
        ln["cUOM"] = p["cUOM"]
        if text(ln["dPrice"]):
            if number(ln["dPrice"]) < 0:
                raise AppError("negative", "lines", detail=f"{where}: dPrice")
            manual = abs(number(ln["dPrice"]) - number(p["dPrice"])) > 1e-9
            ln["cPriceSource"] = "manual" if manual else p["cPriceSource"]
            ln["dPrice"] = unit_cost(number(ln["dPrice"]))
        else:
            ln["dPrice"], ln["cPriceSource"] = p["dPrice"], p["cPriceSource"]
        if not text(ln["dDiscountPct"]):
            ln["dDiscountPct"] = p["dDiscountPct"] or "0"
        if not 0 <= number(ln["dDiscountPct"]) <= 100:
            raise AppError("out_of_range", "lines", detail=f"{where}: dDiscountPct 0-100")
        ln["dDiscountPct"] = quantity(number(ln["dDiscountPct"]))
        net = number(ln["dPrice"]) * (1 - number(ln["dDiscountPct"]) / 100)
        if text(p["dMinPrice"]) and net < number(p["dMinPrice"]) - 1e-9:
            raise AppError("below_min_price", "lines", detail=f"{where}: {unit_cost(net)} < {p['dMinPrice']}")
        ln["dNetPrice"] = unit_cost(net)
        ln["dAmount"] = amount(number(ln["dQty"]) * net)
        ln["cTaxGroup"] = self._line_tax_group(inv, prod, invoice_taxable)

    def _line_tax_group(self, inv: Row, prod: Row, invoice_taxable: bool) -> str:
        """The invoice's tax group, unless it is taxable and the product is zero-rated or exempt."""
        if invoice_taxable and prod.get("cSalesTaxGroup"):
            own = self.refs["tax_groups"].find(prod["cSalesTaxGroup"])
            if own is not None and own.get("cTreatment") in ("zero", "exempt"):
                return str(own["cCode"])
        return str(inv["cTaxGroup"])

    def preview(self, payload: Row, no: int | None = None) -> Row:
        """The draft calculated from a payload, without saving it (the screen shows the prices and taxes)."""
        inv = copy.deepcopy(self.draft(no)) if no else self.blank()
        return self.calc(self._apply(inv, payload))

    # ---------------------------------------------------------- write
    def create(self, payload: Row) -> Row:
        inv = self.calc(self._apply(self.blank(), payload))
        inv["iNo"] = self.numbering.next(DRAFT_SEQUENCE)
        inv["cUser"] = self.username()
        inv["dCreated"] = datetime.now().isoformat(timespec="seconds")
        self.repo.insert(inv)
        return inv

    def update(self, no: int, payload: Row) -> Row:
        current = self.draft(no)
        inv = self.calc(self._apply(copy.deepcopy(current), payload))
        self.repo.update(inv, [current["iNo"]])
        return inv

    def delete(self, no: int) -> None:
        self.repo.delete(self.draft(no))

    # ---------------------------------------------------------- posting (V4)
    def check(self, no: int) -> Row:
        """What posting the draft would do, without doing it: {ok, problems: [{iLine, cProduct, code, detail}],
        allocations: [...]} (the invoice is calculated again; nothing is saved)."""
        inv = copy.deepcopy(self.draft(no))
        problems: list[Row] = []
        allocations: list[Row] = []
        try:
            self.calc(inv)
        except AppError as e:
            problems.append(self._problem(e))
        if not problems:
            if not inv.get("lines"):
                problems.append({"iLine": 0, "cProduct": "", "code": "no_lines", "field": "lines", "detail": ""})
            elif not inv["cWarehouse"]:
                problems.append({"iLine": 0, "cProduct": "", "code": "required", "field": "cWarehouse", "detail": ""})
            else:
                allocations, problems = self._allocate(inv)
        return {"ok": not problems, "problems": problems, "allocations": allocations}

    @staticmethod
    def _problem(e: AppError) -> Row:
        line = 0
        if e.detail and e.detail.startswith("line "):
            head = e.detail[5:].split(":", 1)[0]
            line = int(head) if head.isdigit() else 0
        return {"iLine": line, "cProduct": "", "code": e.code, "field": e.field or "", "detail": e.detail or ""}

    def _allocate(self, inv: Row) -> tuple[Rows, Rows]:
        """The stock each line takes (in the order of its pick policy), against the balances and what the previous lines already took."""
        stock = self.refs["stock"]
        wh = self.refs["warehouses"].find(inv["cWarehouse"]) or {}
        allow_negative = bool(wh.get("lAllowNegative"))
        bal = {k: dict(v) for k, v in stock.balances().items()}
        received = self._received(stock, {text(ln["cProduct"]).upper() for ln in inv["lines"]})
        allocations: Rows = []
        problems: Rows = []
        for i, ln in enumerate(inv["lines"], 1):
            prod = self.refs["products"].find(ln["cProduct"]) or {}
            if not prod.get("lStocked"):
                continue  # a service: nothing goes out
            stock_uom = prod.get("cStockUOM") or ln["cUOM"]
            factor = self.refs["unit_factor"](ln["cUOM"], stock_uom, prod)
            if factor is None:
                problems.append(self._line_problem(i, prod, "no_conversion", f"{ln['cUOM']} -> {stock_uom}"))
                continue
            need = round(number(ln["dQty"]) * factor, 6)
            lots = bool(prod.get("lLotControl") or prod.get("lSerialControl"))
            policy = pick_policy(prod)
            candidates = []
            for key, b in bal.items():
                if key[0] != prod["cCode"].upper() or key[1] != wh.get("cCode", "").upper():
                    continue
                free = b["qty"] - b["reserved"]
                if free <= EPS or not self._location_ok(wh, b["cLocation"]):
                    continue
                if prod.get("lExpiryControl") and b.get("dExpiry") and b["dExpiry"] < inv["dDate"]:
                    continue  # expired: not sold
                candidates.append((self._order(policy, b, received.get(key)), b, free))
            candidates.sort(key=lambda c: c[0])
            left = need
            for _order, b, free in candidates:
                if left <= EPS:
                    break
                take = round(min(free, left), 6)
                b["qty"] = round(b["qty"] - take, 6)
                left = round(left - take, 6)
                allocations.append(self._allocation(i, prod, wh, b, take, stock_uom))
            if left > EPS:
                if allow_negative and not lots:
                    allocations.append(
                        self._allocation(i, prod, wh, {"cLocation": "", "cLot": "", "cSerial": ""}, left, stock_uom)
                    )
                    continue
                available = quantity(need - left)
                problems.append(
                    self._line_problem(
                        i, prod, "insufficient_stock", f"{quantity(need)} {stock_uom} > {available} {stock_uom}"
                    )
                )
        return allocations, problems

    @staticmethod
    def _received(stock: Any, products: set[str]) -> Received:
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

    @staticmethod
    def _order(policy: str, b: Row, received: tuple[str, int, str, int] | None) -> tuple:
        """Sort key of a balance: the stock that goes out first comes first."""
        first, last = (received[:2], received[2:]) if received else (("", 0), ("", 0))
        place = (b["cLot"].upper(), b["cLocation"].upper(), b["cSerial"].upper())
        if policy == "FEFO":
            return (b.get("dExpiry") or "9999-12-31", *first, *place)
        if policy == "LIFO":
            return (-_day(last[0]), -last[1], *place)
        return (*first, *place)

    def _location_ok(self, wh: Row, location: str) -> bool:
        if not location:
            return True
        loc = self.refs["stock"].locations.find_in(wh["cCode"], location)
        return loc is not None and not loc.get("lBlocked") and loc.get("lActive", True)

    @staticmethod
    def _line_problem(i: int, prod: Row, code: str, detail: str) -> Row:
        return {
            "iLine": i,
            "cProduct": prod.get("cCode", ""),
            "code": code,
            "field": "lines",
            "detail": f"line {i}: {prod.get('cCode', '')} {detail}",
        }

    @staticmethod
    def _allocation(i: int, prod: Row, wh: Row, b: Row, qty: float, uom: str) -> Row:
        return {
            "iLine": i,
            "cProduct": prod["cCode"],
            "cWarehouse": wh["cCode"],
            "cLocation": b.get("cLocation", ""),
            "cLot": b.get("cLot", ""),
            "cSerial": b.get("cSerial", ""),
            "dExpiry": b.get("dExpiry", "") or "",
            "dQty": quantity(qty),
            "cUOM": uom,
            "iMovement": 0,
            "dValue": "",
        }

    def post(self, no: int) -> Row:
        """Check everything, then take the stock out and give the invoice its number (see the module's docstring).
        The first problem is the error (400 / 409); nothing has moved then."""
        result = self.check(no)
        if result["problems"]:
            p = result["problems"][0]
            raise AppError(p["code"], p["field"] or None, detail=p["detail"])
        current = self.draft(no)
        inv = self.calc(copy.deepcopy(current))
        stock = self.refs["stock"]
        number_ = self._next_invoice_no()
        staged: list[tuple[Row, Row]] = []
        for a in result["allocations"]:
            m = stock.movement_from(
                {
                    "cType": "OUT",
                    "cProduct": a["cProduct"],
                    "dQty": a["dQty"],
                    "cWarehouse": a["cWarehouse"],
                    "cLocation": a["cLocation"],
                    "cLot": a["cLot"],
                    "cSerial": a["cSerial"],
                    "cDocType": "SO",
                    "cDocNo": number_,
                    "cReason": inv["cCustomer"],
                    "dDate": inv["dDate"],
                }
            )
            try:
                prod = stock.check(m, [s for s, _p in staged])
            except AppError as e:
                raise AppError(
                    e.code, "lines", e.status, detail=f"line {a['iLine']}: {a['cProduct']} {e.detail or ''}".strip()
                ) from None
            staged.append((m, prod))
        cost = 0.0
        for a, (m, prod) in zip(result["allocations"], staged, strict=True):
            done = stock.post(m, prod)
            a["iMovement"] = done["iNo"]
            a["dValue"] = amount(-number(done["dValue"]))
            cost += number(a["dValue"])
        inv.update(
            {
                "cStatus": "posted",
                "cInvoiceNo": number_,
                "dPosted": datetime.now().isoformat(timespec="seconds"),
                "cPostedBy": self.username(),
                "dCost": amount(cost),
                "allocations": result["allocations"],
            }
        )
        self.repo.update(inv, [current["iNo"]])
        return inv

    def _next_invoice_no(self) -> str:
        start = max(1, int(self.refs["invoice_start"]() or 0))
        used = [int(i["cInvoiceNo"]) for i in self.repo.all(lines=False) if str(i.get("cInvoiceNo", "")).isdigit()]
        return str(self.numbering.next(INVOICE_SEQUENCE, start=start, minimum=max([start - 1, *used]) + 1))
