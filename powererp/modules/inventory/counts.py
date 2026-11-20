"""Physical / cycle counts: the sheet built from the stock, the counted quantities, the posting (all or nothing)."""

from __future__ import annotations

import copy
from datetime import datetime
from typing import Any

from powererp import schemas as S
from powererp.core.errors import AppError, NotFound
from powererp.core.values import amount, number, quantity, text, today
from powererp.modules.common.forms import RecordForm

from .masters import must_exist

Row = dict[str, Any]


class CountService:
    def __init__(self, repo, stock, warehouses_repo, numbering, username):
        self.repo = repo
        self.stock = stock  # StockService
        self.warehouses_repo = warehouses_repo
        self.numbering = numbering
        self.username = username
        self.form = RecordForm(S.COUNT)
        self.line_form = RecordForm(S.COUNT_LINE)

    @staticmethod
    def view(c: Row) -> Row:
        out = dict(c)
        lines = []
        for ln in c.get("lines", []):
            ln = dict(ln)
            if ln.get("dQtyCounted", "") != "" and c["cStatus"] == "Draft":
                ln["dDiff"] = quantity(number(ln["dQtyCounted"]) - number(ln.get("dQtyExpected")))
            lines.append(ln)
        out["lines"] = lines
        out["lineCount"] = len(lines)
        out["countedLines"] = sum(1 for ln in lines if ln.get("dQtyCounted", "") != "")
        return out

    def list(self) -> list[Row]:
        return self.repo.all()

    def get(self, no: int) -> Row:
        c = self.repo.get(no)
        if c is None:
            raise NotFound()
        return c

    def draft(self, no: int) -> Row:
        c = self.get(no)
        if c["cStatus"] != "Draft":
            raise AppError("posted", status=409)
        return c

    def generate(self, c: Row) -> None:
        """Fill the sheet with the current balances of the warehouse (optionally only some locations / products).
        Counted quantities already typed are kept."""
        lp, pp = text(c.get("cLocationPrefix")).upper(), text(c.get("cProductPrefix")).upper()
        keep = {
            (ln["cProduct"], ln["cLocation"], ln["cLot"], ln["cSerial"]): ln["dQtyCounted"] for ln in c.get("lines", [])
        }
        lines = []
        for r in self.stock.stock_rows():
            if r["cWarehouse"].upper() != c["cWarehouse"].upper():
                continue
            if lp and not r["cLocation"].upper().startswith(lp):
                continue
            if pp and not r["cProduct"].upper().startswith(pp):
                continue
            k = (r["cProduct"], r["cLocation"], r["cLot"], r["cSerial"])
            lines.append(
                {
                    "cProduct": r["cProduct"],
                    "cDescFR": r["cDescFR"],
                    "cLocation": r["cLocation"],
                    "cLot": r["cLot"],
                    "cSerial": r["cSerial"],
                    "dQtyExpected": r["dQtyOnHand"],
                    "dQtyCounted": keep.get(k, ""),
                    "dDiff": "",
                }
            )
        c["lines"] = lines

    def _fill(self, c: Row, p: Row, is_new: bool) -> None:
        if c["cStatus"] != "Draft":
            raise AppError("posted", status=409)
        self.form.apply(c, p, skip=() if is_new else ("cWarehouse",))
        wh = must_exist(self.warehouses_repo.get, c, "cWarehouse", required=True)
        assert wh is not None
        c["cWarehouse"] = wh["cCode"]
        c["dDate"] = c["dDate"] or today()
        if "lines" not in p:
            return
        lines = []
        for i, ln in enumerate(p.get("lines") or [], 1):
            if not isinstance(ln, dict):
                continue
            row = self.line_form.apply(self.line_form.blank(), ln)
            if not row["cProduct"]:
                continue
            prod = self.stock.products_repo.get(row["cProduct"])
            if prod is None:
                raise AppError("unknown_ref", "lines", detail=f"line {i}: {row['cProduct']}")
            row["cProduct"] = prod["cCode"]
            row["cDescFR"] = prod.get("cDescFR", "")
            row["cLocation"] = row["cLocation"].upper()
            if not row["dQtyExpected"]:
                k = (
                    prod["cCode"].upper(),
                    wh["cCode"].upper(),
                    row["cLocation"],
                    row["cLot"].upper(),
                    row["cSerial"].upper(),
                )
                row["dQtyExpected"] = quantity(self.stock.balances().get(k, {"qty": 0.0})["qty"])
            row["dDiff"] = ""
            lines.append(row)
        c["lines"] = lines

    def create(self, p: Row) -> Row:
        c = {**self.form.blank(), "cStatus": "Draft", "lines": []}
        self._fill(c, p, True)
        if not c["lines"]:
            self.generate(c)
        c["iNo"] = self.numbering.next("STOCK_COUNT")
        c["cUser"] = self.username()
        self.repo.insert(c)
        return c

    def update(self, no: int, p: Row) -> Row:
        work = copy.deepcopy(self.draft(no))
        self._fill(work, p, False)
        self.repo.update(work)
        return work

    def delete(self, no: int) -> None:
        self.repo.delete(self.draft(no))

    def regenerate(self, no: int) -> Row:
        c = self.draft(no)
        self.generate(c)
        self.repo.update(c)
        return c

    def post(self, no: int) -> Row:
        """One CNT movement per counted line whose quantity differs from the stock now. Lines without a counted
        quantity are ignored. All or nothing: every movement is checked before the first one is posted."""
        c = self.draft(no)
        counted = [ln for ln in c.get("lines", []) if ln.get("dQtyCounted", "") != ""]
        if not counted:
            raise AppError("nothing_counted", "lines")
        bal = self.stock.balances()
        staged: list[tuple[Row, Row]] = []
        for i, ln in enumerate(counted, 1):
            k = (
                ln["cProduct"].upper(),
                c["cWarehouse"].upper(),
                ln["cLocation"].upper(),
                ln["cLot"].upper(),
                ln["cSerial"].upper(),
            )
            now = bal.get(k, {"qty": 0.0})["qty"]
            diff = round(number(ln["dQtyCounted"]) - now, 6)
            ln["dQtyExpected"] = quantity(now)
            ln["dDiff"] = quantity(diff)
            if abs(diff) < 1e-9:
                continue
            m = self.stock.movement_from(
                {
                    "cType": "CNT",
                    "cProduct": ln["cProduct"],
                    "dQty": diff,
                    "cWarehouse": c["cWarehouse"],
                    "cLocation": ln["cLocation"],
                    "cLot": ln["cLot"],
                    "cSerial": ln["cSerial"],
                    "cDocType": "CNT",
                    "cDocNo": str(no),
                    "cReason": c.get("cDescription", ""),
                    "dDate": c.get("dDate") or today(),
                }
            )
            try:
                prod = self.stock.check(m, [s for s, _p in staged])
            except AppError as e:
                raise AppError(
                    e.code, "lines", e.status, detail=f"line {i}: {ln['cProduct']} {ln['cLocation']}".strip()
                ) from None
            staged.append((m, prod))
        posted, value = [], 0.0
        for m, prod in staged:
            done = self.stock.post(m, prod)
            posted.append(done["iNo"])
            value += number(done["dValue"])
        c.update(
            {
                "cStatus": "Posted",
                "dPosted": datetime.now().isoformat(timespec="seconds"),
                "movements": posted,
                "dValueDiff": amount(value),
            }
        )
        self.repo.update(c)
        return c
