"""Manufacturing data of the products (P7): the "Manufacturing" tab of the item master.

Kept by Production in its own table (1 to 1 with the product), so the inventory module does not change:
- make or buy (or both): only made products get recipes and production orders;
- setup family (P1): which line of the setup matrix (P6) applies when the product is scheduled;
- manufacturing lot: minimum and multiple (the order quantities MRP will suggest), lead time in days;
- phantom: a sub-assembly never stocked, its materials go up to the order of the parent;
- traceability: none, by lot or by serial number; the inventory controls of the product must allow it;
- attributes (width, basis weight, colour...), compared with the limits of the resources (P4) in the recipes.
"""

from __future__ import annotations

from typing import Any

from powererp import schemas as S
from powererp.core.errors import AppError
from powererp.core.values import number, text
from powererp.modules.common.crud import CrudService
from powererp.modules.common.forms import Row
from powererp.modules.common.registry import ReferenceRegistry
from powererp.store import Store

MADE = ("make", "both")


class ProductMfgService(CrudService):
    keys = ("cProduct",)
    children = {"attributes": S.PRODUCT_ATTRIBUTE}

    def __init__(self, repo: Store, refs: dict[str, Any], references: ReferenceRegistry):
        """refs: finders given by the container: products, setup_families."""
        super().__init__(repo, S.PRODUCT_MFG, S.DEFAULTS["product_mfg"])
        self.refs = refs
        references.register("setup_family", self._uses_family)

    def _uses_family(self, code: str) -> bool:
        return any(p["cSetupFamily"].upper() == code.upper() for p in self.repo.all(lines=False))

    def keep_child(self, key: str, line: Row) -> bool:
        return bool(text(line["cAttribute"]))

    def validate(self, row: Row, is_new: bool) -> None:
        prod = self.refs["products"](row["cProduct"]) if text(row["cProduct"]) else None
        if prod is None:
            raise AppError("unknown_ref" if text(row["cProduct"]) else "required", "cProduct")
        row["cProduct"] = prod["cCode"]
        if row["cSetupFamily"]:
            fam = self.refs["setup_families"](row["cSetupFamily"])
            if fam is None:
                raise AppError("unknown_ref", "cSetupFamily")
            row["cSetupFamily"] = fam["cCode"]
        for field in ("dMfgLotMin", "dMfgLotMultiple"):
            if text(row[field]) and number(row[field]) < 0:
                raise AppError("negative", field)
        if row["iMfgLeadDays"] < 0:
            raise AppError("negative", "iMfgLeadDays")
        if row["lPhantom"] and row["cMakeBuy"] == "buy":
            raise AppError("phantom_is_made", "lPhantom")
        # the inventory controls of the product must allow the traceability asked
        if row["cTraceLevel"] == "lot" and not prod.get("lLotControl"):
            raise AppError("lot_control_required", "cTraceLevel")
        if row["cTraceLevel"] == "serial" and not prod.get("lSerialControl"):
            raise AppError("serial_control_required", "cTraceLevel")
        seen = set()
        for i, a in enumerate(row.get("attributes", []), 1):
            a["cAttribute"] = a["cAttribute"].strip()
            if a["cAttribute"].lower() in seen:
                raise AppError("duplicate", "attributes", detail=f"line {i}: {a['cAttribute']}")
            seen.add(a["cAttribute"].lower())

    def view(self, row: Row, full: bool = True) -> Row:
        prod = self.refs["products"](row["cProduct"]) or {}
        out = {
            **row,
            "cDescFR": prod.get("cDescFR", ""),
            "cDescEN": prod.get("cDescEN", ""),
            "cStockUOM": prod.get("cStockUOM", ""),
        }
        return out if full else {**out, "iAttributes": len(row.get("attributes", []))}

    def delete_for(self, product: str) -> None:
        """The product is deleted: its manufacturing data go with it (ProductService.on_delete)."""
        row = self.find(product)
        if row is not None:
            self.repo.delete(row)

    def is_made(self, product: str) -> bool:
        row = self.find(product)
        return row is not None and row["cMakeBuy"] in MADE

    def lot_quantity(self, product: str, needed: float) -> float:
        """The quantity to make for a need: at least the minimum lot, rounded up to the multiple."""
        row = self.find(product)
        if row is None or needed <= 0:
            return max(needed, 0.0)
        qty = max(needed, number(row["dMfgLotMin"]))
        multiple = number(row["dMfgLotMultiple"])
        if multiple > 0:
            steps = -(-qty // multiple)  # ceiling
            qty = steps * multiple
        return qty
