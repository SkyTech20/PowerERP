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

Credit notes (V6: cType "credit"): they credit a posted invoice (cOrigInvoice, its number), usually made from it
(credit_from(): every line still creditable). The header is the invoice's (customer, places, language, tax group);
each line credits a line of the invoice (iOrigLine), at its price and discount unless typed, at most the quantity
invoiced minus what posted credit notes already credited; the taxes are those of the invoice's date. Posting it:
the lines marked lReturn bring the goods back to the stock, into the lots / locations / serial numbers they went out
of, at their cost (ADJ movements, document "SO"); the others only credit the price. Numbered NC-1, NC-2... (sequence
SALES_CREDIT).
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
from powererp.modules.inventory.picking import location_usable, pick_order, received_dates, shortage_code
from powererp.store import Store

DRAFT_SEQUENCE = "SALES_INVOICE_DRAFT"
INVOICE_SEQUENCE = "SALES_INVOICE"
CREDIT_SEQUENCE = "SALES_CREDIT"
CREDIT_PREFIX = "NC-"
EPS = 1e-9
Rows = list[Row]


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
        self.form.apply(inv, payload, skip=("cType", "cOrigInvoice") if inv.get("iNo") else ())
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
        if inv.get("cType") == "credit":
            orig = self._credit_header(inv)
            for i, ln in enumerate(inv.get("lines", []), 1):
                self._credit_line(inv, orig, ln, i)
            return self._totals(inv, orig["dDate"])
        customer = self._header(inv)
        group = self.refs["tax_groups"].find(inv["cTaxGroup"]) if inv["cTaxGroup"] else None
        invoice_taxable = group is None or group.get("cTreatment") == "taxable"
        for i, ln in enumerate(inv.get("lines", []), 1):
            self._line(inv, customer, ln, i, invoice_taxable)
        return self._totals(inv, inv["dDate"])

    def _totals(self, inv: Row, tax_date: str) -> Row:
        """The taxes on the total of the lines of each tax group (at tax_date), the totals."""
        bases: dict[str, float] = {}
        gross = 0.0
        for ln in inv.get("lines", []):
            gross += number(ln["dQty"]) * number(ln["dPrice"])
            if ln["cTaxGroup"]:
                bases[ln["cTaxGroup"]] = bases.get(ln["cTaxGroup"], 0.0) + number(ln["dAmount"])
        sub = sum(number(ln["dAmount"]) for ln in inv.get("lines", []))
        taxes: list[Row] = []
        for code in sorted(bases):
            result = self.refs["tax_calculator"].calc(code, round(bases[code], 2), tax_date)
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

    # ---------------------------------------------------------- credit notes (V6)
    def posted_invoice(self, number_: str) -> Row | None:
        """The posted invoice of that number (not a credit note)."""
        n = text(number_).strip()
        return next(
            (
                i
                for i in self.repo.all()
                if i.get("cType", "invoice") == "invoice" and i["cStatus"] == "posted" and i["cInvoiceNo"] == n
            ),
            None,
        )

    def credited(self, invoice_no: str, but: int = 0) -> dict[int, float]:
        """Quantity credited per line of the invoice by its posted credit notes (other than the draft `but`)."""
        out: dict[int, float] = {}
        for c in self.repo.all():
            if c.get("cType") != "credit" or c["cOrigInvoice"] != invoice_no or c["cStatus"] != "posted":
                continue
            if c["iNo"] == but:
                continue
            for ln in c.get("lines", []):
                out[ln["iOrigLine"]] = out.get(ln["iOrigLine"], 0.0) + number(ln["dQty"])
        return out

    def _credit_header(self, inv: Row) -> Row:
        if not text(inv["cOrigInvoice"]):
            raise AppError("required", "cOrigInvoice")
        orig = self.posted_invoice(inv["cOrigInvoice"])
        if orig is None:
            raise AppError("unknown_ref", "cOrigInvoice")
        for f in ("cCustomer", "cCustomerName", "cShipTo", "cWarehouse", "cLang", "cTaxGroup", "cCustomerPO"):
            inv[f] = orig[f]
        inv["cTermCode"], inv["cTermDesc"] = "", ""
        inv["dDate"] = inv["dDate"] or today()
        return orig

    def _credit_line(self, inv: Row, orig: Row, ln: Row, i: int) -> None:
        where = f"line {i}"
        lines = orig.get("lines", [])
        n = int(ln.get("iOrigLine") or 0)
        if not n:  # the first line of the invoice with that product
            n = next((k for k, ol in enumerate(lines, 1) if ol["cProduct"].upper() == text(ln["cProduct"]).upper()), 0)
        if not 1 <= n <= len(lines):
            raise AppError("not_invoiced", "lines", detail=f"{where}: {ln['cProduct']}")
        ol = lines[n - 1]
        ln["iOrigLine"] = n
        ln["cProduct"], ln["cUOM"], ln["cTaxGroup"] = ol["cProduct"], ol["cUOM"], ol["cTaxGroup"]
        ln["cDescription"] = ln["cDescription"] or ol["cDescription"]
        if not text(ln["dQty"]) or number(ln["dQty"]) <= 0:
            raise AppError("positive", "lines", detail=f"{where}: dQty")
        left = number(ol["dQty"]) - self.credited(orig["cInvoiceNo"], inv.get("iNo") or 0).get(n, 0.0)
        left -= sum(number(x["dQty"]) for x in inv["lines"][: i - 1] if x.get("iOrigLine") == n)
        if number(ln["dQty"]) > left + EPS:
            raise AppError(
                "over_credit", "lines", detail=f"{where}: {ol['cProduct']} {number(ln['dQty']):g} > {left:g}"
            )
        ln["dQty"] = quantity(number(ln["dQty"]))
        ln["dPrice"] = unit_cost(number(ln["dPrice"] if text(ln["dPrice"]) else ol["dPrice"]))
        ln["cPriceSource"] = "invoice" if abs(number(ln["dPrice"]) - number(ol["dPrice"])) < EPS else "manual"
        disc = number(ln["dDiscountPct"] if text(ln["dDiscountPct"]) else ol["dDiscountPct"])
        if not 0 <= disc <= 100:
            raise AppError("out_of_range", "lines", detail=f"{where}: dDiscountPct 0-100")
        ln["dDiscountPct"] = quantity(disc)
        net = number(ln["dPrice"]) * (1 - disc / 100)
        ln["dNetPrice"] = unit_cost(net)
        ln["dAmount"] = amount(number(ln["dQty"]) * net)
        prod = self.refs["products"].find(ln["cProduct"]) or {}
        ln["lReturn"] = bool(ln.get("lReturn")) and bool(prod.get("lStocked"))

    def credit_from(self, no: int) -> Row:
        """A draft credit note of a posted invoice: every line still creditable, the goods coming back."""
        orig = self.get(no)
        if orig.get("cType") == "credit" or orig["cStatus"] != "posted":
            raise AppError("not_posted", status=409)
        done = self.credited(orig["cInvoiceNo"])
        lines = []
        for n, ol in enumerate(orig.get("lines", []), 1):
            left = number(ol["dQty"]) - done.get(n, 0.0)
            if left > EPS:
                lines.append({"iOrigLine": n, "cProduct": ol["cProduct"], "dQty": quantity(left), "lReturn": True})
        if not lines:
            raise AppError("fully_credited", status=409)
        return self.create({"cType": "credit", "cOrigInvoice": orig["cInvoiceNo"], "lines": lines})

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
            elif inv["cType"] == "credit":
                allocations, problems = self._returns(inv)
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
        received = received_dates(stock, {text(ln["cProduct"]).upper() for ln in inv["lines"]})
        held = self.refs.get("held_lots", set)()
        allocations: Rows = []
        problems: Rows = []

        def usable(location: str) -> bool:
            return location_usable(stock, wh.get("cCode", ""), location)

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
            candidates = pick_order(prod, wh.get("cCode", ""), bal, inv["dDate"], received, usable, held)
            left = need
            for b, free in candidates:
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
                        i,
                        prod,
                        shortage_code(prod, wh.get("cCode", ""), bal, held),
                        f"{quantity(need)} {stock_uom} > {available} {stock_uom}",
                    )
                )
        return allocations, problems

    def _returns(self, inv: Row) -> tuple[Rows, Rows]:
        """A credit note: the lines marked lReturn come back to the stock, into what their invoice line took out
        (its allocations), less what posted credit notes already brought back."""
        orig = self.posted_invoice(inv["cOrigInvoice"]) or {}
        back: dict[tuple, float] = {}  # (invoice line, location, lot, serial) -> quantity already returned
        for c in self.repo.all():
            if c.get("cType") == "credit" and c["cOrigInvoice"] == orig.get("cInvoiceNo") and c["cStatus"] == "posted":
                for a in c.get("allocations", []):
                    ol = c["lines"][a["iLine"] - 1]["iOrigLine"]
                    k = (ol, a["cLocation"], a["cLot"], a["cSerial"])
                    back[k] = back.get(k, 0.0) + number(a["dQty"])
        allocations: Rows = []
        problems: Rows = []
        for i, ln in enumerate(inv["lines"], 1):
            if not ln.get("lReturn"):
                continue
            prod = self.refs["products"].find(ln["cProduct"]) or {}
            stock_uom = prod.get("cStockUOM") or ln["cUOM"]
            factor = self.refs["unit_factor"](ln["cUOM"], stock_uom, prod) or 1.0
            left = round(number(ln["dQty"]) * factor, 6)
            for a in orig.get("allocations", []):
                if a["iLine"] != ln["iOrigLine"] or left <= EPS:
                    continue
                k = (a["iLine"], a["cLocation"], a["cLot"], a["cSerial"])
                free = number(a["dQty"]) - back.get(k, 0.0)
                if free <= EPS:
                    continue
                take = round(min(free, left), 6)
                back[k] = back.get(k, 0.0) + take
                left = round(left - take, 6)
                row = self._allocation(i, prod, {"cCode": a["cWarehouse"]}, a, take, stock_uom)
                row["dValue"] = amount(number(a["dValue"]) / number(a["dQty"]) * take) if number(a["dQty"]) else "0.00"
                allocations.append(row)
            if left > EPS:
                problems.append(self._line_problem(i, prod, "over_return", f"{quantity(left)} {stock_uom}"))
        return allocations, problems

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
        credit = inv["cType"] == "credit"
        number_ = self._next_credit_no() if credit else self._next_invoice_no()
        staged: list[tuple[Row, Row]] = []
        for a in result["allocations"]:
            payload = {
                "cType": "ADJ" if credit else "OUT",
                "cProduct": a["cProduct"],
                "dQty": a["dQty"],
                "cWarehouse": a["cWarehouse"],
                "cLocation": a["cLocation"],
                "cLot": a["cLot"],
                "cSerial": a["cSerial"],
                "cDocType": "SO",
                "cDocNo": number_,
                "cReason": f"{inv['cCustomer']} {inv['cOrigInvoice']}".strip() if credit else inv["cCustomer"],
                "dDate": inv["dDate"],
            }
            if credit:  # back at the cost it went out at, into its lot
                payload["dUnitCost"] = unit_cost(number(a["dValue"]) / number(a["dQty"])) if number(a["dQty"]) else ""
                payload["dExpiry"] = a["dExpiry"]
            m = stock.movement_from(payload)
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
            a["dValue"] = amount(abs(number(done["dValue"])))
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

    def _next_credit_no(self) -> str:
        used = [
            int(i["cInvoiceNo"][len(CREDIT_PREFIX) :])
            for i in self.repo.all(lines=False)
            if i.get("cType") == "credit" and i["cInvoiceNo"][len(CREDIT_PREFIX) :].isdigit()
        ]
        return CREDIT_PREFIX + str(self.numbering.next(CREDIT_SEQUENCE, minimum=max(used, default=0) + 1))

    def _next_invoice_no(self) -> str:
        start = max(1, int(self.refs["invoice_start"]() or 0))
        used = [
            int(i["cInvoiceNo"])
            for i in self.repo.all(lines=False)
            if i.get("cType") != "credit" and str(i.get("cInvoiceNo", "")).isdigit()
        ]
        return str(self.numbering.next(INVOICE_SEQUENCE, start=start, minimum=max([start - 1, *used]) + 1))
