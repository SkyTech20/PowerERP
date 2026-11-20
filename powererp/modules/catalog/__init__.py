"""Catalog module: units of measure (/api/uom) and product categories (/api/categories)."""

from __future__ import annotations

from flask import Blueprint, Flask

from powererp import schemas as S
from powererp.container import Container
from powererp.core.errors import AppError
from powererp.core.http import require
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
    categories = c.register("categories", CategoryService(store("product_categories"), c.get("references")))
    bp = Blueprint("catalog", __name__)
    register_crud_routes(bp, "uom", "uom", units, ("cCode", "cDescFR", "cDescEN"))
    register_crud_routes(bp, "categories", "categories", categories, ("cCode", "cDescFR", "cDescEN", "cParent"))
    app.register_blueprint(bp)
    c.get("lookups").register("uom", label_lookup(units, DESC_FR, DESC_EN))
    c.get("lookups").register("categories", label_lookup(categories, DESC_FR, DESC_EN))
    c.get("seeds").add(units.repo, "inv_uom", seed.get("uom", []))
    c.get("seeds").add(categories.repo, "inv_categories", seed.get("categories", []))
