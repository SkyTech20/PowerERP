"""Sales module (B2B, Quebec first), built step by step: V1 customers and company profile, V2 price lists and
discounts, V3 invoices (draft), V4 posting (the stock goes out), V5 printing FR / EN, V6 credit notes.

V1: /api/customers (ship-to addresses and contacts as child lists), lookups customers and customer_terms;
    GET /api/company (the header of the invoices, with the GST / QST numbers of the tax codes),
    PUT /api/admin/company (administrators).

Sales never changes the stock directly: the invoices will post movements through the stock service of the
container (c.get("stock").add(...) with cDocType "SO"), so every stock rule applies to them.
"""

from __future__ import annotations

from flask import Blueprint, Flask, jsonify

from powererp.container import Container
from powererp.core.http import json_payload
from powererp.modules.common.crud import register_crud_routes
from powererp.modules.common.registry import label_lookup
from powererp.store import store

from .company import CompanyProfileService
from .customers import CustomerService

SEARCH = ("cCode", "cName", "cLegalName", "cCity", "cEmail")


def register(app: Flask, c: Container, seed: dict) -> None:
    bp = Blueprint("sales", __name__)
    refs = {"tax_groups": c.get("tax_groups").find, "warehouses": c.get("warehouses").find}
    customers = c.register("customers", CustomerService(store("customers"), refs, c.get("references")))
    register_crud_routes(bp, "customers", "customers", customers, SEARCH)
    company = c.register("company_profile", CompanyProfileService(store("company_profile"), c.get("tax_codes").list))

    @bp.route("/api/company")
    def company_profile():
        return jsonify(company.view())

    @bp.route("/api/admin/company", methods=["PUT"])
    def company_save():
        company.save(json_payload())
        return jsonify(company.view())

    lookups = c.get("lookups")
    lookups.register("customers", label_lookup(customers, ("cName",), keep=lambda r: r.get("lActive")))
    lookups.register("customer_terms", customers.terms_lookup)
    lifecycle = c.get("lifecycle")
    lifecycle.add(company.repo, "company_profile", seed.get("company_profile", []))
    lifecycle.add(customers.repo, "customers", seed.get("customers", []))
    app.register_blueprint(bp)
