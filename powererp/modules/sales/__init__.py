"""Sales module (B2B, Quebec first), built step by step: V1 customers and company profile, V2 price lists and
discounts, V3 invoices (draft), V4 posting (the stock goes out), V5 printing FR / EN, V6 credit notes.

V1: /api/customers (ship-to addresses and contacts as child lists), lookups customers and customer_terms;
    GET /api/company (the header of the invoices, with the GST / QST numbers of the tax codes),
    PUT /api/admin/company (administrators).
    GET /api/company/logo (the logo as a PNG, 404 without one), PUT /api/admin/company/logo ({"cLogo": data URL};
    the image is made a PNG fitting in 600 x 240), DELETE /api/admin/company/logo (administrators).
V2: /api/price-lists (prices by product, unit and quantity as lines; discounts by category), lookup price_lists;
    lookup sellable_products; GET /api/pricing?customer=&product=&qty=&uom=&date=: the price, the discount and the rule that gave them.
V3: /api/sales-invoices (drafts: GET/POST, GET/PUT/DELETE /<no>; a posted one is 409),
    POST /api/sales-invoices/calc (and /<no>/calc): the draft calculated without saving it (prices, taxes, totals).
V4: POST /api/sales-invoices/<no>/check (what posting would do: problems, stock taken), POST /<no>/post.
V5: GET /api/sales-invoices/<no>/print?lang=fr|en: the invoice to print (HTML), in its language by default.
V6: credit notes: sales invoices of cType "credit"; POST /api/sales-invoices/<no>/credit makes one from a posted
    invoice (every line still creditable); then saved, checked, posted and printed like an invoice.

Sales never changes the stock directly: the invoices will post movements through the stock service of the
container (c.get("stock").add(...) with cDocType "SO"), so every stock rule applies to them.
"""

from __future__ import annotations

from datetime import date

from flask import Blueprint, Flask, Response, jsonify, render_template, request

from powererp.container import Container
from powererp.core.errors import AppError, NotFound
from powererp.core.http import json_payload
from powererp.core.pagination import paginate_request
from powererp.core.security import current_username
from powererp.modules.common.crud import register_crud_routes
from powererp.modules.common.registry import label_lookup
from powererp.store import store

from . import printing
from .company import CompanyProfileService
from .customers import CustomerService
from .invoices import CREDIT_PREFIX, CREDIT_SEQUENCE, DRAFT_SEQUENCE, INVOICE_SEQUENCE, SalesInvoiceService
from .pricing import PriceListService, PriceResolver

SEARCH = ("cCode", "cName", "cLegalName", "cCity", "cEmail")
DESC_FR, DESC_EN = ("cDescFR",), ("cDescEN", "cDescFR")


def register(app: Flask, c: Container, seed: dict) -> None:
    bp = Blueprint("sales", __name__, template_folder="templates")
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

    @bp.route("/api/company/logo")
    def company_logo():
        png = company.logo_png()
        if png is None:
            raise NotFound()
        return Response(png, mimetype="image/png", headers={"Cache-Control": "no-cache"})

    @bp.route("/api/admin/company/logo", methods=["PUT", "DELETE"])
    def company_logo_save():
        if request.method == "DELETE":
            company.remove_logo()
        else:
            company.set_logo(str(json_payload().get("cLogo") or ""))
        return jsonify(company.view())

    _register_invoices(bp, c, customers, pricing, seed.get("sales_invoices", []))

    lookups = c.get("lookups")
    lookups.register("customers", label_lookup(customers, ("cName",), keep=lambda r: r.get("lActive")))
    lookups.register("customer_terms", customers.terms_lookup)
    lookups.register("customer_addresses", lambda: customers.addresses_lookup(request.args.get("customer", "")))
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


INVOICE_SEARCH = ("iNo", "cInvoiceNo", "cOrigInvoice", "cCustomer", "cCustomerName", "cCustomerPO", "dDate")


def _register_invoices(
    bp: Blueprint, c: Container, customers: CustomerService, pricing: PriceResolver, demo: list[dict]
) -> None:
    refs = {
        "customers": customers,
        "products": c.get("products"),
        "warehouses": c.get("warehouses"),
        "tax_groups": c.get("tax_groups"),
        "pricing": pricing,
        "tax_calculator": c.get("tax_calculator"),
        "stock": c.get("stock"),
        "unit_factor": c.get("unit_converter").factor,
        "held_lots": lambda: c.get("lot_status").held() if "lot_status" in c else set(),  # quality: lots not released
        "invoice_start": lambda: c.get("company_profile").get().get("iInvoiceStart") or 0,
    }
    numbering = c.get("numbering")
    invoices = c.register(
        "sales_invoices",
        SalesInvoiceService(store("sales_invoices"), refs, numbering, current_username, c.get("references")),
    )

    # The stock card links a sales movement (its document number is the invoice / credit note number) to its invoice
    c.get("stock").document_ids["SO"] = lambda: {
        i["cInvoiceNo"]: i["iNo"] for i in invoices.repo.all(lines=False) if i.get("cInvoiceNo")
    }

    @bp.route("/api/sales-invoices", methods=["GET", "POST"])
    def sales_invoices():
        if request.method == "GET":
            return jsonify(paginate_request([invoices.view(i, full=False) for i in invoices.list()], INVOICE_SEARCH))
        return jsonify(invoices.create(json_payload())), 201

    @bp.route("/api/sales-invoices/<int:no>", methods=["GET", "PUT", "DELETE"])
    def sales_invoice(no):
        inv = invoices.get(no)
        if request.method == "GET":
            return jsonify(inv)
        if request.method == "DELETE":
            invoices.delete(no)
            return jsonify({"ok": True})
        return jsonify(invoices.update(no, json_payload()))

    @bp.route("/api/sales-invoices/calc", methods=["POST"])
    @bp.route("/api/sales-invoices/<int:no>/calc", methods=["POST"])
    def sales_invoice_calc(no=None):
        return jsonify(invoices.preview(json_payload(), no))

    @bp.route("/api/sales-invoices/<int:no>/credit", methods=["POST"])
    def sales_invoice_credit(no):
        return jsonify(invoices.credit_from(no)), 201

    @bp.route("/api/sales-invoices/<int:no>/print")
    def sales_invoice_print(no):
        inv = invoices.get(no)
        customer = customers.find(inv["cCustomer"])
        ship_to = customers.ship_to(customer, inv["cShipTo"]) if customer and inv["cShipTo"] else None
        codes = {t["cCode"].upper(): t for t in c.get("tax_codes").list()}
        lang = (request.args.get("lang") or inv.get("cLang") or "fr").lower()
        profile = c.get("company_profile")
        ctx = printing.context(inv, profile.view(), customer, ship_to, codes, lang)
        ctx["logo"] = profile.logo_url()
        return render_template("sales_invoice.html", **ctx)

    @bp.route("/api/sales-invoices/<int:no>/check", methods=["POST"])
    def sales_invoice_check(no):
        return jsonify(invoices.check(no))

    @bp.route("/api/sales-invoices/<int:no>/post", methods=["POST"])
    def sales_invoice_post(no):
        return jsonify(invoices.post(no))

    lifecycle = c.get("lifecycle")
    lifecycle.add(invoices.repo, "sales_invoices", demo)

    def renumber(data: dict) -> None:
        """The drafts go on from the last number loaded."""
        if "sales_invoices" in data:
            last = max((int(i.get("iNo") or 0) for i in data["sales_invoices"]), default=0)
            numbering.set_next(DRAFT_SEQUENCE, last + 1)
            posted = [int(i["cInvoiceNo"]) for i in data["sales_invoices"] if str(i.get("cInvoiceNo", "")).isdigit()]
            numbering.set_next(INVOICE_SEQUENCE, max(posted, default=0) + 1)
            credits = [
                int(n[len(CREDIT_PREFIX) :])
                for n in (str(i.get("cInvoiceNo", "")) for i in data["sales_invoices"])
                if n.startswith(CREDIT_PREFIX) and n[len(CREDIT_PREFIX) :].isdigit()
            ]
            numbering.set_next(CREDIT_SEQUENCE, max(credits, default=0) + 1)

    lifecycle.after_load(renumber)
