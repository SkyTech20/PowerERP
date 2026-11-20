"""Taxes: tax codes with their rate history, tax groups (the codes charged together) and the tax calculation."""

from __future__ import annotations

from powererp import schemas as S
from powererp.core.errors import AppError
from powererp.core.http import require
from powererp.core.values import amount, number, quantity, today
from powererp.modules.common.crud import CrudService
from powererp.modules.common.forms import Row
from powererp.modules.common.registry import ReferenceRegistry
from powererp.store import Store


def rate_on(tax: Row, on: str | None = None) -> float | None:
    """The rate (percent) valid at a date: the rate line with the latest start date that applies."""
    on = on or today()
    valid = [
        r
        for r in tax.get("lines", [])
        if (r.get("dStartDate") or "0000") <= on and (not r.get("dEndDate") or r["dEndDate"] >= on)
    ]
    if not valid:
        return None
    return number(max(valid, key=lambda r: r.get("dStartDate") or "")["dRate"])


class TaxCodeService(CrudService):
    line_schema = S.TAX_RATE

    def __init__(self, repo: Store, references: ReferenceRegistry):
        super().__init__(repo, S.TAX_CODE, S.DEFAULTS["tax_codes"])
        self.references = references

    def keep_line(self, line: Row) -> bool:
        return bool(line["dRate"] != "" or line["dStartDate"])

    def validate(self, row: Row, is_new: bool) -> None:
        require(row, "cDescFR")
        for i, ln in enumerate(row.get("lines", []), 1):
            if ln["dRate"] == "":
                raise AppError("required", "lines", detail=f"line {i}: rate")
            if ln["dEndDate"] and ln["dStartDate"] and ln["dEndDate"] < ln["dStartDate"]:
                raise AppError("invalid_dates", "lines", detail=f"line {i}")
        row.setdefault("lines", []).sort(key=lambda r: r.get("dStartDate") or "")

    def view(self, row: Row, full: bool = True) -> Row:
        rate = rate_on(row)
        return {**row, "dCurrentRate": "" if rate is None else quantity(rate)}

    def before_delete(self, row: Row) -> None:
        self.references.check("tax_code", row["cCode"])


class TaxGroupService(CrudService):
    line_schema = S.TAX_GROUP_LINE

    def __init__(self, repo: Store, codes: TaxCodeService, references: ReferenceRegistry):
        super().__init__(repo, S.TAX_GROUP, S.DEFAULTS["tax_groups"])
        self.codes = codes
        self.references = references
        references.register("tax_code", self.uses_tax_code)

    def uses_tax_code(self, code: str) -> bool:
        return any(
            str(ln.get("cTaxCode") or "").upper() == code.upper() for g in self.list() for ln in g.get("lines", [])
        )

    def keep_line(self, line: Row) -> bool:
        return bool(line["cTaxCode"])

    def validate(self, row: Row, is_new: bool) -> None:
        require(row, "cDescFR")
        for i, ln in enumerate(row.get("lines", []), 1):
            tax = self.codes.find(ln["cTaxCode"])
            if tax is None:
                raise AppError("unknown_ref", "lines", detail=f"line {i}: {ln['cTaxCode']}")
            ln["cTaxCode"] = tax["cCode"]
            ln["iSeq"] = ln["iSeq"] or i
        row["lines"] = sorted(row.get("lines", []), key=lambda ln: ln["iSeq"])

    def view(self, row: Row, full: bool = True) -> Row:
        names = [ln["cTaxCode"] for ln in sorted(row.get("lines", []), key=lambda ln: ln["iSeq"])]
        return {**row, "cTaxList": " + ".join(names) if names and row.get("cTreatment") == "taxable" else ""}

    def before_delete(self, row: Row) -> None:
        self.references.check("tax_group", row["cCode"])


class TaxCalculator:
    """Taxes of an amount for a tax group at a date. A compound tax is calculated on the amount plus the taxes
    before it (tax on tax); groups that are not "taxable" (exempt, zero-rated) charge nothing."""

    def __init__(self, codes: TaxCodeService, groups: TaxGroupService):
        self.codes = codes
        self.groups = groups

    def calc(self, group_code: str, base_amount: float, on: str | None = None) -> Row | None:
        group = self.groups.find(group_code)
        if group is None:
            return None
        on = on or today()
        out, total = [], 0.0
        if group.get("cTreatment") == "taxable":
            for ln in sorted(group.get("lines", []), key=lambda ln: ln["iSeq"]):
                tax = self.codes.find(ln["cTaxCode"])
                rate = rate_on(tax, on) if tax else None
                if tax is None or rate is None:
                    continue
                base = base_amount + (total if ln.get("lCompound") else 0.0)
                value = round(base * rate / 100 + 1e-9, 2)
                total += value
                out.append(
                    {
                        "cTaxCode": tax["cCode"],
                        "cKind": tax.get("cKind", ""),
                        "dRate": quantity(rate),
                        "dBase": amount(base),
                        "dTax": amount(value),
                        "cGLCollected": tax.get("cGLCollected", ""),
                        "cGLRecoverable": tax.get("cGLRecoverable", ""),
                        "dRecoverable": amount(value * number(tax.get("dRecoverablePct") or 100) / 100),
                    }
                )
        return {
            "cTaxGroup": group["cCode"],
            "cTreatment": group.get("cTreatment"),
            "dDate": on,
            "dAmount": amount(base_amount),
            "taxes": out,
            "dTotalTax": amount(total),
            "dTotal": amount(base_amount + total),
        }
