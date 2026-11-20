"""Taxes module: /api/tax-codes, /api/tax-groups, /api/tax-groups/<code>/calc (Administration > Taxes)."""

from __future__ import annotations

from flask import Blueprint, Flask, jsonify, request

from powererp.container import Container
from powererp.core.errors import NotFound
from powererp.core.values import number, text
from powererp.modules.common.crud import register_crud_routes
from powererp.modules.common.registry import label_lookup
from powererp.store import store

from .service import TaxCalculator, TaxCodeService, TaxGroupService, rate_on

__all__ = ["TaxCalculator", "TaxCodeService", "TaxGroupService", "rate_on", "register"]

DESC_FR, DESC_EN = ("cDescFR",), ("cDescEN", "cDescFR")


def register(app: Flask, c: Container, seed: dict) -> None:
    codes = c.register("tax_codes", TaxCodeService(store("tax_codes"), c.get("references")))
    groups = c.register("tax_groups", TaxGroupService(store("tax_groups"), codes, c.get("references")))
    calculator = c.register("tax_calculator", TaxCalculator(codes, groups))

    bp = Blueprint("taxes", __name__)
    register_crud_routes(bp, "tax-codes", "tax_codes", codes, ("cCode", "cDescFR", "cDescEN", "cJurisdiction"))
    register_crud_routes(bp, "tax-groups", "tax_groups", groups, ("cCode", "cDescFR", "cDescEN", "cProvince"))

    @bp.route("/api/tax-groups/<code>/calc")
    def tax_group_calc(code):
        res = calculator.calc(code, number(request.args.get("amount")), text(request.args.get("date"))[:10] or None)
        if res is None:
            raise NotFound()
        return jsonify(res)

    app.register_blueprint(bp)
    c.get("lookups").register("taxcodes", label_lookup(codes, DESC_FR, DESC_EN))
    c.get("lookups").register("taxgroups", label_lookup(groups, DESC_FR, DESC_EN))
    c.get("lifecycle").add(codes.repo, "inv_tax_codes", seed.get("tax_codes", []))
    c.get("lifecycle").add(groups.repo, "inv_tax_groups", seed.get("tax_groups", []))
