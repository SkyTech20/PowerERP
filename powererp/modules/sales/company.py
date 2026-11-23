"""Company profile (V1): the name, address and numbers printed at the top of the invoices.

One row (code MAIN). The GST / HST and QST registration numbers are not typed twice: they are the registration
numbers of the active tax codes (Administration > Taxes), returned with the profile.
"""

from __future__ import annotations

from collections.abc import Callable

from powererp import schemas as S
from powererp.core.http import require
from powererp.modules.common.forms import RecordForm, Row
from powererp.store import Store

from .customers import check_email

CODE = "MAIN"


class CompanyProfileService:
    def __init__(self, repo: Store, tax_codes: Callable[[], list[Row]]):
        self.repo = repo
        self.tax_codes = tax_codes
        self.form = RecordForm(S.COMPANY_PROFILE, S.DEFAULTS["company_profile"])

    def get(self) -> Row:
        """The profile (the defaults while it was never saved)."""
        return self.repo.get(CODE) or self.form.blank()

    def save(self, payload: Row) -> Row:
        current = self.repo.get(CODE)
        row = self.form.apply(dict(current) if current else self.form.blank(), payload, skip=("cCode",))
        row["cCode"] = CODE
        require(row, "cName")
        row["cEmail"] = check_email(row["cEmail"], "cEmail")
        row["cProvince"] = row["cProvince"].strip().upper()
        row["cCountry"] = row["cCountry"].strip().upper()
        if current:
            self.repo.update(row, [CODE])
        else:
            self.repo.insert(row)
        return row

    def tax_numbers(self) -> list[Row]:
        """The registration numbers to print: one per number (GST and HST share theirs), from the active codes."""
        out: list[Row] = []
        seen: set[str] = set()
        for t in sorted(self.tax_codes(), key=lambda t: t["cCode"]):
            number = t.get("cRegistrationNo", "").strip()
            if not t.get("lActive") or not number or number.upper() in seen:
                continue
            seen.add(number.upper())
            out.append({"cTaxCode": t["cCode"], "cKind": t.get("cKind", ""), "cRegistrationNo": number})
        return out

    def view(self) -> Row:
        return {**self.get(), "taxNumbers": self.tax_numbers()}
