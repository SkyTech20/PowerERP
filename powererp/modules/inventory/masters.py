"""Inventory master files: products, warehouses, locations, replenishment parameters (CrudService subclasses)."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from powererp import schemas as S
from powererp.core.errors import AppError
from powererp.core.http import require
from powererp.core.values import number, quantity, text
from powererp.modules.common.crud import CrudService
from powererp.modules.common.forms import Row

STOCKED_TYPES = S.STOCKED_TYPES


def must_exist(finder, row: Row, field: str, required: bool = False) -> Row | None:
    """A reference to another master file must exist (empty is fine unless required)."""
    v = text(row.get(field))
    if not v:
        if required:
            raise AppError("required", field)
        return None
    found = finder(v)
    if found is None:
        raise AppError("unknown_ref", field)
    return found


def in_use(used: bool) -> None:
    if used:
        raise AppError("in_use", status=409)


class LocationService(CrudService):
    """Locations of a warehouse: zone > aisle > rack > level > bin; the code is built from them when empty."""

    keys = ("cWarehouse", "cCode")
    full_view_on_create = False

    def __init__(self, repo, warehouses_repo, stock=None):
        super().__init__(repo, S.LOCATION, S.DEFAULTS["locations"])
        self.warehouses_repo = warehouses_repo
        self.stock = stock  # StockService (quantities on the location's screen), set by the module

    def find_in(self, warehouse: str, code: str) -> Row | None:
        return self.repo.get(text(warehouse), text(code)) if text(code) else None

    def has_locations(self, warehouse: str) -> bool:
        return any(loc["cWarehouse"].upper() == warehouse.upper() for loc in self.repo.all(lines=False))

    def validate(self, row: Row, is_new: bool) -> None:
        if is_new:
            wh = must_exist(self.warehouses_repo.get, row, "cWarehouse", required=True)
            assert wh is not None
            row["cWarehouse"] = wh["cCode"]
            if not row["cCode"]:
                row["cCode"] = "-".join(
                    x for x in (row["cZone"], row["cAisle"], row["cRack"], row["cLevel"], row["cBin"]) if x
                )
            if not row["cCode"]:
                raise AppError("required", "cCode")
            row["cCode"] = row["cCode"].upper()

    def view(self, row: Row, full: bool = True) -> Row:
        if not full or self.stock is None:
            return row
        return {**row, "dQtyOnHand": quantity(self.stock.quantity_at(row["cWarehouse"], row["cCode"]))}

    def before_delete(self, row: Row) -> None:
        in_use(self.stock is not None and self.stock.location_used(row["cWarehouse"], row["cCode"]))


class WarehouseService(CrudService):
    def __init__(self, repo, locations: LocationService, params_repo, stock=None):
        super().__init__(repo, S.WAREHOUSE, S.DEFAULTS["warehouses"])
        self.locations = locations
        self.params_repo = params_repo
        self.stock = stock

    def validate(self, row: Row, is_new: bool) -> None:
        require(row, "cNameFR")
        for f in ("cReceivingLoc", "cShippingLoc"):
            if row[f] and not self.locations.find_in(row["cCode"], row[f]):
                raise AppError("unknown_ref", f)

    def before_delete(self, row: Row) -> None:
        in_use(self.stock is not None and self.stock.warehouse_used(row["cCode"]))
        code = row["cCode"].upper()
        for loc in self.locations.repo.all(lines=False):
            if loc["cWarehouse"].upper() == code:
                self.locations.repo.delete(loc)
        for par in self.params_repo.all(lines=False):
            if par["cWarehouse"].upper() == code:
                self.params_repo.delete(par)


class ProductService(CrudService):
    """The item master. The full view (one product) adds its stock by warehouse, value, quantity on order, margin."""

    line_schema = S.PRODUCT_SUPPLIER
    children = {"conversions": S.PRODUCT_UOM}  # its own units: 1 BAG = 25 KG (the stock unit)
    readonly = ("dAvgCost", "dLastCost")

    def __init__(self, repo, refs: dict[str, Any], stock=None):
        super().__init__(repo, S.PRODUCT, S.DEFAULTS["products"])
        self.refs = refs  # finders of the other master files: categories, uom, tax_groups, warehouses, suppliers
        self.stock = stock
        # set by the module: other modules say whether a product is used (ReferenceRegistry, kind "product")
        # and what goes with it when it is deleted (e.g. its manufacturing data)
        self.references = None
        self.on_delete: list[Callable[[str], None]] = []

    def keep_line(self, line: Row) -> bool:
        return bool(line["cSupplierCode"])

    def keep_child(self, key: str, line: Row) -> bool:
        return bool(text(line["cUOM"]))

    def validate(self, row: Row, is_new: bool) -> None:
        require(row, "cDescFR")
        must_exist(self.refs["categories"], row, "cCategory")
        for f in ("cStockUOM", "cPurchaseUOM", "cSalesUOM"):
            must_exist(self.refs["uom"], row, f, required=(f == "cStockUOM"))
        for f in ("cSalesTaxGroup", "cPurchaseTaxGroup"):
            must_exist(self.refs["tax_groups"], row, f)
        must_exist(self.refs["warehouses"], row, "cDefaultWarehouse")
        for f in ("dPurchaseFactor", "dSalesFactor"):
            if text(row.get(f)) and number(row[f]) <= 0:
                raise AppError("positive", f)
            row[f] = row[f] or "1"
        if row["cType"] not in STOCKED_TYPES:
            row["lStocked"] = False
        if not is_new and not row["lStocked"] and self.stock is not None:
            in_use(abs(self.stock.product_totals(row["cCode"])[0]) > 1e-9)  # still has stock
        codes = {s["cCode"].upper(): s["cCode"] for s in self.refs["suppliers"]()}
        for i, ln in enumerate(row.get("lines", []), 1):
            if ln["cSupplierCode"].upper() not in codes:
                raise AppError("unknown_ref", "lines", detail=f"line {i}: {ln['cSupplierCode']}")
            ln["cSupplierCode"] = codes[ln["cSupplierCode"].upper()]
            ln["cCurrency"] = ln["cCurrency"] or row.get("cCurrency") or "CAD"
        seen = set()
        for i, cv in enumerate(row.get("conversions", []), 1):
            unit = self.refs["uom"](cv["cUOM"])
            if unit is None:
                raise AppError("unknown_ref", "conversions", detail=f"line {i}: {cv['cUOM']}")
            cv["cUOM"] = unit["cCode"]
            if cv["cUOM"].upper() == text(row["cStockUOM"]).upper():
                raise AppError("same_unit", "conversions", detail=f"line {i}")
            if cv["cUOM"].upper() in seen:
                raise AppError("duplicate", "conversions", detail=f"line {i}: {cv['cUOM']}")
            seen.add(cv["cUOM"].upper())
            if number(cv["dFactor"]) <= 0:
                raise AppError("positive", "conversions", detail=f"line {i}")
        for f in ("dAvgCost", "dLastCost"):
            row.setdefault(f, "")

    def view(self, row: Row, full: bool = True) -> Row:
        if self.stock is None:
            return row
        return self.stock.product_view(row, full)

    def before_delete(self, row: Row) -> None:
        in_use(self.stock is not None and self.stock.product_used(row["cCode"]))
        if self.references is not None:
            self.references.check("product", row["cCode"])
        for fn in self.on_delete:
            fn(row["cCode"])
        code = row["cCode"].upper()
        for par in self.stock.params_repo.all(lines=False) if self.stock else []:
            if par["cProduct"].upper() == code:
                self.stock.params_repo.delete(par)

    def uses(self, fields: tuple[str, ...], code: str) -> bool:
        """Is `code` in one of these fields of a product (tax group, unit, category)?"""
        cu = code.upper()
        return any(text(p.get(f)).upper() == cu for p in self.repo.all(lines=False) for f in fields)

    def uses_unit(self, code: str) -> bool:
        """Is the unit a stock, purchase or sales unit, or a conversion, of a product?"""
        cu = code.upper()
        fields = ("cStockUOM", "cPurchaseUOM", "cSalesUOM")
        return self.uses(fields, code) or any(
            c["cUOM"].upper() == cu for p in self.repo.all() for c in p.get("conversions", [])
        )


class StockParamService(CrudService):
    """Replenishment parameters per product and warehouse: reorder point, min / max, order quantity."""

    keys = ("cProduct", "cWarehouse")

    def __init__(self, repo, products_repo, warehouses_repo, locations: LocationService, stock=None):
        super().__init__(repo, S.STOCK_PARAM, S.DEFAULTS["stock_params"])
        self.products_repo = products_repo
        self.warehouses_repo = warehouses_repo
        self.locations = locations
        self.stock = stock

    def validate(self, row: Row, is_new: bool) -> None:
        if is_new:
            prod = must_exist(self.products_repo.get, row, "cProduct", required=True)
            wh = must_exist(self.warehouses_repo.get, row, "cWarehouse", required=True)
            assert prod is not None and wh is not None
            row["cProduct"], row["cWarehouse"] = prod["cCode"], wh["cCode"]
        if row["cDefaultLocation"] and not self.locations.find_in(row["cWarehouse"], row["cDefaultLocation"]):
            raise AppError("unknown_ref", "cDefaultLocation")
        if text(row["dMaxQty"]) and text(row["dMinQty"]) and number(row["dMaxQty"]) < number(row["dMinQty"]):
            raise AppError("max_below_min", "dMaxQty")

    def view(self, row: Row, full: bool = True) -> Row:
        prod = self.products_repo.get(row["cProduct"]) or {}
        qty, res = self.stock.product_totals(row["cProduct"], row["cWarehouse"]) if self.stock else (0.0, 0.0)
        return {
            **row,
            "cDescFR": prod.get("cDescFR", ""),
            "cDescEN": prod.get("cDescEN", ""),
            "dQtyAvailable": quantity(qty - res),
        }
