"""Customers (V1): who the company sells to (B2B), where the goods go and who receives the invoices.

What a customer gives the rest of Sales:
- the language of its invoices (FR / EN) and its billing address;
- its tax group (QC = GST + QST), unless the ship-to address of the invoice has its own: the taxes follow the
  place of delivery; a tax exemption number is printed on the invoice;
- its payment terms (printed; no receivables in this phase), its default discount and the warehouse its orders
  are shipped from;
- its ship-to addresses (one is the default) and its contacts (those flagged "invoices" receive them).
"""

from __future__ import annotations

import re
from typing import Any

from powererp import schemas as S
from powererp.core.errors import AppError
from powererp.core.http import require
from powererp.core.values import number, text
from powererp.modules.common.crud import CrudService
from powererp.modules.common.forms import Row
from powererp.modules.common.registry import ReferenceRegistry
from powererp.store import Store

EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def check_email(value: str, field: str, detail: str | None = None) -> str:
    """An optional e-mail address: empty, or something@domain.tld (trimmed)."""
    value = text(value).strip()
    if value and not EMAIL.match(value):
        raise AppError("invalid_email", field, detail=detail)
    return value


class CustomerService(CrudService):
    kind = "customer"
    children = {"addresses": S.CUSTOMER_ADDRESS, "contacts": S.CUSTOMER_CONTACT}

    def __init__(self, repo: Store, refs: dict[str, Any], references: ReferenceRegistry):
        """refs: finders given by the container: tax_groups, warehouses."""
        super().__init__(repo, S.CUSTOMER, S.DEFAULTS["customers"])
        self.refs = refs
        self.references = references
        references.register("tax_group", self.uses_tax_group)

    # ---------------------------------------------------------- references
    def _uses(self, field: str, code: str) -> bool:
        return any(r[field].upper() == code.upper() for r in self.repo.all(lines=False))

    def uses_tax_group(self, code: str) -> bool:
        return self._uses("cTaxGroup", code) or any(
            a["cTaxGroup"].upper() == code.upper() for r in self.repo.all() for a in r.get("addresses", [])
        )

    def keep_child(self, key: str, line: Row) -> bool:
        if key == "addresses":
            return any(text(line.get(f)) for f in ("cCode", "cName", "cAddress1", "cCity"))
        return any(text(line.get(f)) for f in ("cName", "cEmail", "cPhone"))

    def _tax_group(self, value: str, field: str, detail: str | None = None) -> str:
        group = self.refs["tax_groups"](value)
        if group is None:
            raise AppError("unknown_ref", field, detail=f"{detail}: {value}" if detail else None)
        return str(group["cCode"])

    # ---------------------------------------------------------- rules
    def validate(self, row: Row, is_new: bool) -> None:
        require(row, "cName", "cTaxGroup")
        row["cCode"] = row["cCode"].strip().upper()
        row["cTaxGroup"] = self._tax_group(row["cTaxGroup"], "cTaxGroup")
        if row["cWarehouse"]:
            wh = self.refs["warehouses"](row["cWarehouse"])
            if wh is None:
                raise AppError("unknown_ref", "cWarehouse")
            row["cWarehouse"] = wh["cCode"]
        if text(row["dDiscountPct"]) and not 0 <= number(row["dDiscountPct"]) <= 100:
            raise AppError("out_of_range", "dDiscountPct", detail="0-100")
        row["cEmail"] = check_email(row["cEmail"], "cEmail")
        row["cProvince"] = row["cProvince"].strip().upper()
        row["cCountry"] = row["cCountry"].strip().upper()
        self._check_addresses(row)
        self._check_contacts(row)

    def _check_addresses(self, row: Row) -> None:
        seen = set()
        addresses = row.get("addresses", [])
        for i, a in enumerate(addresses, 1):
            a["cCode"] = a["cCode"].strip().upper()
            if not a["cCode"]:
                raise AppError("required", "addresses", detail=f"line {i}: cCode")
            if a["cCode"] in seen:
                raise AppError("duplicate", "addresses", detail=f"line {i}: {a['cCode']}")
            seen.add(a["cCode"])
            if not a["cAddress1"]:
                raise AppError("required", "addresses", detail=f"line {i}: cAddress1")
            a["cName"] = a["cName"] or row["cName"]
            a["cProvince"] = a["cProvince"].strip().upper()
            a["cCountry"] = (a["cCountry"].strip() or row["cCountry"]).upper()
            if a["cTaxGroup"]:
                a["cTaxGroup"] = self._tax_group(a["cTaxGroup"], "addresses", f"line {i}")
        defaults = [a for a in addresses if a["lDefault"]]
        if len(defaults) > 1:
            raise AppError("one_default", "addresses")
        if addresses and not defaults:
            addresses[0]["lDefault"] = True

    @staticmethod
    def _check_contacts(row: Row) -> None:
        for i, c in enumerate(row.get("contacts", []), 1):
            if not c["cName"]:
                raise AppError("required", "contacts", detail=f"line {i}: cName")
            c["cEmail"] = check_email(c["cEmail"], "contacts", f"line {i}")
            if c["lInvoices"] and not c["cEmail"]:
                raise AppError("required", "contacts", detail=f"line {i}: cEmail")

    def before_delete(self, row: Row) -> None:
        self.references.check(self.kind, row["cCode"])  # the invoices (V3)

    def view(self, row: Row, full: bool = True) -> Row:
        if full:
            return row
        return {**row, "iAddresses": len(row.get("addresses", []))}

    # ---------------------------------------------------------- what the invoices use
    def ship_to(self, customer: Row, code: str = "") -> Row | None:
        """A ship-to address of the customer (its default one when no code is given); None if it has none."""
        addresses = customer.get("addresses", [])
        if code:
            return next((a for a in addresses if a["cCode"].upper() == code.upper()), None)
        return next((a for a in addresses if a["lDefault"]), addresses[0] if addresses else None)

    def tax_group_for(self, customer: Row, ship_to: str = "") -> str:
        """The taxes follow the place of delivery: the ship-to address's tax group, else the customer's."""
        address = self.ship_to(customer, ship_to)
        return (address or {}).get("cTaxGroup") or customer["cTaxGroup"]

    def invoice_emails(self, customer: Row) -> list[str]:
        """Where the invoices go: the contacts flagged "invoices", else the customer's e-mail."""
        emails = [c["cEmail"] for c in customer.get("contacts", []) if c["lInvoices"] and c["cEmail"]]
        return emails or ([customer["cEmail"]] if customer["cEmail"] else [])

    def terms_lookup(self) -> tuple[list[dict], int]:
        """The payment terms already typed on customers (code + description)."""
        seen: dict[str, str] = {}
        for c in self.repo.all(lines=False):
            if c["cTermCode"] and c["cTermCode"] not in seen:
                seen[c["cTermCode"]] = c["cTermDesc"]
        return [{"code": k, "label": v} for k, v in sorted(seen.items())], 200
