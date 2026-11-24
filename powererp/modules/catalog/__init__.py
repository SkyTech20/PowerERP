"""Catalog module: units of measure (/api/uom), their conversions (/api/uom-conversions) and product categories."""

from __future__ import annotations

from collections import deque

from flask import Blueprint, Flask, jsonify, request

from powererp import schemas as S
from powererp.container import Container
from powererp.core.errors import AppError
from powererp.core.http import require
from powererp.core.values import number, text
from powererp.modules.common.crud import CrudService, register_crud_routes
from powererp.modules.common.forms import Row
from powererp.modules.common.registry import ReferenceRegistry, label_lookup
from powererp.store import Store, store

DESC_FR, DESC_EN = ("cDescFR",), ("cDescEN", "cDescFR")


class UnitService(CrudService):
    """Units of measure (count, weight, length, time...). Used by the products (stock, purchase, sales units)."""

    def __init__(self, repo: Store, references: ReferenceRegistry):
        super().__init__(repo, S.UOM, S.DEFAULTS["uom"])
        self.references = references

    def validate(self, row: Row, is_new: bool) -> None:
        require(row, "cDescFR")

    def before_delete(self, row: Row) -> None:
        self.references.check("uom", row["cCode"])


# The units and conversions every company needs, added on request (Units > Conversions > "Standard conversions")
STANDARD_UNITS = (
    ("KG", "weight", "Kilogramme", "Kilogram"),
    ("G", "weight", "Gramme", "Gram"),
    ("MG", "weight", "Milligramme", "Milligram"),
    ("LB", "weight", "Livre", "Pound"),
    ("L", "volume", "Litre", "Litre"),
    ("ML", "volume", "Millilitre", "Millilitre"),
    ("KM", "length", "Kilomètre", "Kilometre"),
    ("M", "length", "Mètre", "Metre"),
    ("CM", "length", "Centimètre", "Centimetre"),
    ("MM", "length", "Millimètre", "Millimetre"),
    ("UN", "count", "Unité", "Unit"),
    ("DZ", "count", "Douzaine", "Dozen"),
    ("H", "time", "Heure", "Hour"),
    ("MIN", "time", "Minute", "Minute"),
)
STANDARD_CONVERSIONS = (
    ("KG", "G", "1000"),
    ("G", "MG", "1000"),
    ("LB", "G", "453.59237"),
    ("L", "ML", "1000"),
    ("KM", "M", "1000"),
    ("M", "CM", "100"),
    ("CM", "MM", "10"),
    ("DZ", "UN", "12"),
    ("H", "MIN", "60"),
)


class UnitConversionService(CrudService):
    """General conversions between two units, for every product: 1 cFromUOM = dFactor cToUOM.
    One pair is entered once: the reverse (1 G = 0.001 KG) is deduced."""

    keys = ("cFromUOM", "cToUOM")

    def __init__(self, repo: Store, units: UnitService):
        super().__init__(repo, S.UOM_CONVERSION, S.DEFAULTS["uom_conversions"])
        self.units = units
        units.references.register("uom", self.uses)

    def uses(self, code: str) -> bool:
        c = code.upper()
        return any(c in (r["cFromUOM"].upper(), r["cToUOM"].upper()) for r in self.repo.all(lines=False))

    def validate(self, row: Row, is_new: bool) -> None:
        for f in ("cFromUOM", "cToUOM"):
            require(row, f)
            unit = self.units.find(row[f])
            if unit is None:
                raise AppError("unknown_ref", f)
            row[f] = unit["cCode"]
        if row["cFromUOM"] == row["cToUOM"]:
            raise AppError("same_unit", "cToUOM")
        if number(row["dFactor"]) <= 0:
            raise AppError("positive", "dFactor")
        if is_new and self.find(row["cToUOM"], row["cFromUOM"]):
            raise AppError("conversion_exists", "cToUOM")  # the reverse is already there

    def add_standard(self) -> dict[str, int]:
        """Adds the standard units and conversions that are missing (an empty database starts with none)."""
        units = conversions = 0
        for code, kind, fr, en in STANDARD_UNITS:
            if self.units.find(code) is None:
                self.units.create({"cCode": code, "cType": kind, "cDescFR": fr, "cDescEN": en})
                units += 1
        for a, b, factor in STANDARD_CONVERSIONS:
            if self.find(a, b) is None and self.find(b, a) is None:
                self.create({"cFromUOM": a, "cToUOM": b, "dFactor": factor})
                conversions += 1
        return {"iUnits": units, "iConversions": conversions}


class UnitConverter:
    """How many units of `to` make one unit of `from`, for a product or in general. The conversions of the
    product (its packaging: 1 BAG = 25 KG) come first, then the general ones; a chain is followed
    (1 BAG = 25 KG and 1 KG = 1000 G: 1 BAG = 25000 G)."""

    def __init__(self, conversions: UnitConversionService):
        self.conversions = conversions

    def factor(self, from_uom: str, to_uom: str, product: Row | None = None) -> float | None:
        a, b = text(from_uom).upper(), text(to_uom).upper()
        if not a or not b:
            return None
        if a == b:
            return 1.0
        graph: dict[str, dict[str, float]] = {}

        def edge(x: str, y: str, f: float) -> None:
            if f > 0 and x != y:
                graph.setdefault(x, {})[y] = f
                graph.setdefault(y, {})[x] = 1 / f

        for r in self.conversions.repo.all(lines=False):
            if r["lActive"]:
                edge(r["cFromUOM"].upper(), r["cToUOM"].upper(), number(r["dFactor"]))
        stock = text((product or {}).get("cStockUOM")).upper()
        for c in (product or {}).get("conversions", []) if stock else []:
            edge(text(c["cUOM"]).upper(), stock, number(c["dFactor"]))  # the product's own win (set last)
        seen, todo = {a: 1.0}, deque([a])
        while todo:
            x = todo.popleft()
            for y, f in graph.get(x, {}).items():
                if y not in seen:
                    seen[y] = seen[x] * f
                    if y == b:
                        return seen[y]
                    todo.append(y)
        return None

    def units_of(self, product: Row) -> list[str]:
        """The units a product can be counted in: its stock unit and every unit that converts to it (its own
        packaging and the general conversions). The sales unit first, then the stock unit, then the others."""
        stock = text(product.get("cStockUOM")).upper()
        if not stock:
            return []
        graph: dict[str, set[str]] = {}
        for r in self.conversions.repo.all(lines=False):
            if r["lActive"] and number(r["dFactor"]) > 0:
                a, b = r["cFromUOM"].upper(), r["cToUOM"].upper()
                graph.setdefault(a, set()).add(b)
                graph.setdefault(b, set()).add(a)
        for c in product.get("conversions", []):
            u = text(c["cUOM"]).upper()
            if u and number(c["dFactor"]) > 0:
                graph.setdefault(u, set()).add(stock)
                graph.setdefault(stock, set()).add(u)
        seen, todo = {stock}, deque([stock])
        while todo:
            for y in graph.get(todo.popleft(), ()):
                if y not in seen:
                    seen.add(y)
                    todo.append(y)
        first = [u for u in (text(product.get("cSalesUOM")).upper(), stock) if u in seen]
        return list(dict.fromkeys(first + sorted(seen)))

    def to_stock(self, qty: float, uom: str, product: Row) -> float | None:
        """A quantity in `uom` expressed in the stock unit of the product."""
        f = self.factor(uom, product.get("cStockUOM", ""), product)
        return None if f is None else qty * f


class CategoryService(CrudService):
    """Product categories, in a tree (cParent)."""

    def __init__(self, repo: Store, references: ReferenceRegistry):
        super().__init__(repo, S.CATEGORY, S.DEFAULTS["categories"])
        self.references = references
        references.register("category", self.has_children)

    def has_children(self, code: str) -> bool:
        return any(str(r.get("cParent") or "").upper() == code.upper() for r in self.repo.all(lines=False))

    def validate(self, row: Row, is_new: bool) -> None:
        require(row, "cDescFR")
        parent = row.get("cParent")
        if parent:
            if parent.upper() == row["cCode"].upper():
                raise AppError("invalid_ref", "cParent")
            if self.find(parent) is None:
                raise AppError("unknown_ref", "cParent")

    def before_delete(self, row: Row) -> None:
        self.references.check("category", row["cCode"])


def register(app: Flask, c: Container, seed: dict) -> None:
    units = c.register("units", UnitService(store("uoms"), c.get("references")))
    conversions = c.register("unit_conversions", UnitConversionService(store("uom_conversions"), units))
    c.register("unit_converter", UnitConverter(conversions))
    categories = c.register("categories", CategoryService(store("product_categories"), c.get("references")))
    bp = Blueprint("catalog", __name__)
    register_crud_routes(bp, "uom", "uom", units, ("cCode", "cDescFR", "cDescEN"))
    register_crud_routes(bp, "uom-conversions", "uom_conversions", conversions, ("cFromUOM", "cToUOM", "cNotes"))

    @bp.route("/api/uom-conversions/standard", methods=["POST"])
    def add_standard_conversions():
        return jsonify(conversions.add_standard())

    @bp.route("/api/uom-conversions/factor")
    def conversion_factor():
        prod = c.get("products").find(request.args.get("product", "")) if request.args.get("product") else None
        f = c.get("unit_converter").factor(request.args.get("from", ""), request.args.get("to", ""), prod)
        if f is None:
            raise AppError("no_conversion", "to")
        return jsonify({"dFactor": f})

    register_crud_routes(bp, "categories", "categories", categories, ("cCode", "cDescFR", "cDescEN", "cParent"))
    app.register_blueprint(bp)
    c.get("lookups").register("uom", label_lookup(units, DESC_FR, DESC_EN))

    def product_units():
        """The units of one product (?product=): those that convert to its stock unit, the sales unit first."""
        prod = c.get("products").find(request.args.get("product", ""))
        if prod is None:
            return [], 200
        en = (request.args.get("lang") or "fr") == "en"
        rows = []
        for code in c.get("unit_converter").units_of(prod):
            u = units.find(code) or {"cCode": code}
            label = text(u.get("cDescEN") if en else u.get("cDescFR")) or text(u.get("cDescFR"))
            rows.append({"code": u["cCode"], "label": label})
        return rows, 200

    c.get("lookups").register("product_uoms", product_units)
    c.get("lookups").register("categories", label_lookup(categories, DESC_FR, DESC_EN))
    c.get("lifecycle").add(units.repo, "inv_uom", seed.get("uom", []))
    c.get("lifecycle").add(conversions.repo, "inv_uom_conversions", seed.get("uom_conversions", []))
    c.get("lifecycle").add(categories.repo, "inv_categories", seed.get("categories", []))
