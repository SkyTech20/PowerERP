"""Sales module (B2B, Quebec first), built step by step: V1 customers and company profile, V2 price lists and
discounts, V3 invoices (draft), V4 posting (the stock goes out), V5 printing FR / EN, V6 credit notes.

V1: /api/customers (ship-to addresses and contacts as child lists), lookups customers and customer_terms;
    GET /api/company (the header of the invoices, with the GST / QST numbers of the tax codes),
    PUT /api/admin/company (administrators).
V2: /api/price-lists (prices by product, unit and quantity as lines; discounts by category), lookup price_lists;
    lookup sellable_products; GET /api/pricing?customer=&product=&qty=&uom=&date=: the price, the discount and the rule that gave them.

Sales never changes the stock directly: the invoices will post movements through the stock service of the
container (c.get("stock").add(...) with cDocType "SO"), so every stock rule applies to them.
"""

from __future__ import annotations

from datetime import date

from flask import Blueprint, Flask, jsonify, request

from powererp.container import Container
from powererp.core.errors import AppError
from powererp.core.http import json_payload
from powererp.modules.common.crud import register_crud_routes
from powererp.modules.common.registry import label_lookup
from powererp.store import store

from .company import CompanyProfileService
from .customers import CustomerService
from .pricing import PriceListService, PriceResolver

SEARCH = ("cCode", "cName", "cLegalName", "cCity", "cEmail")
DESC_FR, DESC_EN = ("cDescFR",), ("cDescEN", "cDescFR")


def register(app: Flask, c: Container, seed: dict) -> None:
    bp = Blueprint("sales", __name__)
    products, categories, converter = c.get("products"), c.get("categories"), c.get("unit_converter")
    plist_refs = {"products": products.find, "categories": categories.find, "converter": converter}
    price_lists = c.register("price_lists", PriceListService(store("price_lists"), plist_refs, c.get("references")))
    refs = {
        "tax_groups": c.get("tax_groups").find,
        "warehouses": c.get("warehouses").find,
        "price_lists": price_lists.find,
    }
    customers = c.register("customers", CustomerService(store("customers"), refs, c.get("references")))
    price_lists.customers_of = customers.using_price_list
    pricing = c.register("pricing", PriceResolver(price_lists, customers, products, categories, converter))
    register_crud_routes(bp, "customers", "customers", customers, SEARCH)
    register_crud_routes(bp, "price-lists", "price_lists", price_lists, ("cCode", "cDescFR", "cDescEN"))

    @bp.route("/api/pricing")
    def price_of():
        a = request.args
        if a.get("date"):
            try:
                date.fromisoformat(a["date"][:10])
            except ValueError:
                raise AppError("invalid_date", "date") from None
        return jsonify(
            pricing.price(
                a.get("customer", ""), a.get("product", ""), a.get("qty", ""), a.get("uom", ""), a.get("date") or None
            )
        )

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
    lookups.register(
        "sellable_products",
        label_lookup(products, DESC_FR, DESC_EN, keep=lambda r: r.get("lSellable") and r.get("cStatus") == "active"),
    )
    lookups.register("price_lists", label_lookup(price_lists, DESC_FR, DESC_EN, keep=lambda r: r.get("lActive")))
    lifecycle = c.get("lifecycle")
    lifecycle.add(company.repo, "company_profile", seed.get("company_profile", []))
    lifecycle.add(price_lists.repo, "price_lists", seed.get("price_lists", []))
    lifecycle.add(customers.repo, "customers", seed.get("customers", []))
    app.register_blueprint(bp)
