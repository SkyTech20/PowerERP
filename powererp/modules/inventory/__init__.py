"""Inventory module: products, warehouses / locations, replenishment parameters, stock movements and balances,
stock and valuation lists, replenishment (POs) and physical counts.

    masters.py        ProductService, WarehouseService, LocationService, StockParamService (CrudService)
    stock.py          StockService: movements checked, costed and posted; balances; stock, valuation, product figures
    costing.py        Costing strategies (moving average, standard)
    ledger.py         StockLedger: DatabaseLedger (tables, lock per product) and MemoryLedger (demo data)
    replenishment.py  ReplenishmentService
    counts.py         CountService

The demo data's opening stock is posted at start-up by the same services, on memory repositories and a memory
ledger: the products get their average cost the same way as in use, and the result seeds the tables.
"""

from __future__ import annotations

import copy

from flask import Blueprint, Flask, jsonify, request

from powererp.container import Container
from powererp.core.errors import AppError
from powererp.core.http import json_payload
from powererp.core.pagination import paginate_request
from powererp.core.security import current_username
from powererp.core.values import amount, boolean, number, text
from powererp.modules.common.crud import register_crud_routes
from powererp.modules.common.memory import MemoryRepository
from powererp.modules.common.registry import label_lookup
from powererp.store import store

from .counts import CountService
from .ledger import DatabaseLedger, MemoryLedger
from .masters import LocationService, ProductService, StockParamService, WarehouseService
from .replenishment import ReplenishmentService
from .stock import StockService

__all__ = [
    "CountService",
    "LocationService",
    "ProductService",
    "ReplenishmentService",
    "StockParamService",
    "StockService",
    "WarehouseService",
    "register",
]

DESC_FR, DESC_EN = ("cDescFR",), ("cDescEN", "cDescFR")
MOVEMENT_SEARCH = ("cProduct", "cDescFR", "cDescEN", "cDocNo", "cLot", "cSerial", "cReason", "cWarehouse")
VALUATION_SEARCH = ("cProduct", "cDescFR", "cDescEN", "cCategory", "cGLInventory")


def build_services(repos: dict, ledger, refs: dict, on_order=lambda code: 0.0, username=current_username):
    """The inventory services on a set of repositories (tables, or memory for the demo data)."""
    locations = LocationService(repos["locations"], repos["warehouses"])
    stock = StockService(
        ledger, repos["products"], repos["warehouses"], locations, repos["stock_params"], on_order, username
    )
    locations.stock = stock
    products = ProductService(repos["products"], {**refs, "warehouses": repos["warehouses"].get}, stock)
    warehouses = WarehouseService(repos["warehouses"], locations, repos["stock_params"], stock)
    params = StockParamService(repos["stock_params"], repos["products"], repos["warehouses"], locations, stock)
    return {"locations": locations, "stock": stock, "products": products, "warehouses": warehouses, "params": params}


def prepare_demo(seed: dict, refs: dict) -> dict:
    """The demo inventory with its opening stock posted (memory): products with their costs, and the movements."""
    repos = {
        "warehouses": MemoryRepository(copy.deepcopy(seed.get("warehouses", []))),
        "locations": MemoryRepository(copy.deepcopy(seed.get("locations", [])), keys=("cWarehouse", "cCode")),
        "products": MemoryRepository(copy.deepcopy(seed.get("products", []))),
        "stock_params": MemoryRepository(copy.deepcopy(seed.get("stock_params", [])), keys=("cProduct", "cWarehouse")),
    }
    for p in repos["products"].rows:
        p.setdefault("lines", [])
        p.setdefault("dAvgCost", "")
        p.setdefault("dLastCost", "")
    ledger = MemoryLedger()
    services = build_services(repos, ledger, refs, username=lambda: "system")
    for raw in seed.get("movements", []):
        services["stock"].add(raw, user="system")
    return {**{k: r.rows for k, r in repos.items()}, "movements": ledger.movements}


def _blueprint(s: dict, counts: CountService, replenishment: ReplenishmentService) -> Blueprint:
    bp = Blueprint("inventory", __name__)
    stock: StockService = s["stock"]
    register_crud_routes(
        bp,
        "products",
        "products",
        s["products"],
        ("cCode", "cDescFR", "cDescEN", "cCategory", "cBrand", "cUPC", "cMfrPartNo", "cManufacturer"),
    )
    register_crud_routes(
        bp, "warehouses", "warehouses", s["warehouses"], ("cCode", "cNameFR", "cNameEN", "cCity", "cManager")
    )
    register_crud_routes(
        bp, "locations", "locations", s["locations"], ("cWarehouse", "cCode", "cZone", "cDescription", "cType")
    )
    register_crud_routes(
        bp, "stock-params", "stock_params", s["params"], ("cProduct", "cWarehouse", "cDescFR", "cDescEN")
    )

    @bp.route("/api/products/unit-check", methods=["POST"])
    def products_unit_check():
        """The purchase / sales units of the product being edited that have no conversion to its stock unit
        (the screen warns while the user picks them; saving refuses them)."""
        p = json_payload()
        row = {
            "cStockUOM": text(p.get("cStockUOM")),
            "cPurchaseUOM": text(p.get("cPurchaseUOM")),
            "cSalesUOM": text(p.get("cSalesUOM")),
            "conversions": [c for c in (p.get("conversions") or []) if isinstance(c, dict) and text(c.get("cUOM"))],
        }
        return jsonify({"missing": s["products"].missing_conversions(row)})

    @bp.route("/api/stock-movements", methods=["GET", "POST"])
    def movements_collection():
        if request.method == "GET":
            return jsonify(paginate_request(stock.movements_view(), MOVEMENT_SEARCH))
        return jsonify(stock.view(stock.add(json_payload()))), 201

    @bp.route("/api/stock-movements/<int:no>", methods=["GET", "PUT", "DELETE"])
    def movements_item(no):
        m = stock.get_movement(no)
        if request.method != "GET":
            raise AppError("posted", status=409)  # correct a movement with another movement
        return jsonify(m)

    @bp.route("/api/inventory/stock")
    def inventory_stock():
        rows = stock.stock_rows(boolean(request.args.get("zero")))
        return jsonify(paginate_request(rows, ("cProduct", "cDescFR", "cDescEN", "cLocation", "cLot", "cSerial")))

    @bp.route("/api/inventory/valuation")
    def inventory_valuation():
        rows = stock.valuation_rows()
        page = paginate_request(rows, VALUATION_SEARCH)
        # The total follows the search and the filters, not only the page shown
        total = 0.0
        q = (request.args.get("q") or "").strip().lower()
        for r in rows:
            if q and not any(q in text(r.get(f)).lower() for f in VALUATION_SEARCH):
                continue
            if any(
                k.startswith("f_") and v and text(r.get(k[2:])).lower() != v.lower() for k, v in request.args.items()
            ):
                continue
            total += number(r["dValue"])
        page["totalValue"] = amount(total)
        return jsonify(page)

    @bp.route("/api/inventory/replenishment")
    def inventory_replenishment():
        rows = replenishment.rows()
        return jsonify(paginate_request(rows, ("cProduct", "cDescFR", "cDescEN", "cSupplierCode", "cSupplierName")))

    @bp.route("/api/inventory/replenishment/po", methods=["POST"])
    def replenishment_po():
        return jsonify({"purchaseOrders": replenishment.create_pos(json_payload())}), 201

    @bp.route("/api/stock-counts", methods=["GET", "POST"])
    def counts_collection():
        if request.method == "GET":
            rows = [{k: v for k, v in counts.view(c).items() if k != "lines"} for c in counts.list()]
            return jsonify(paginate_request(rows, ("cWarehouse", "cDescription", "cStatus")))
        return jsonify(counts.view(counts.create(json_payload()))), 201

    @bp.route("/api/stock-counts/<int:no>", methods=["GET", "PUT", "DELETE"])
    def counts_item(no):
        c = counts.get(no)
        if request.method == "GET":
            return jsonify(counts.view(c))
        counts.draft(no)  # 409 posted before reading the body
        if request.method == "DELETE":
            counts.delete(no)
            return jsonify({"ok": True})
        return jsonify(counts.view(counts.update(no, json_payload())))

    @bp.route("/api/stock-counts/<int:no>/generate", methods=["POST"])
    def counts_generate(no):
        return jsonify(counts.view(counts.regenerate(no)))

    @bp.route("/api/stock-counts/<int:no>/post", methods=["POST"])
    def counts_post(no):
        return jsonify(counts.view(counts.post(no)))

    return bp


def register(app: Flask, c: Container, seed: dict) -> None:
    repos = {name: store(name) for name in ("warehouses", "locations", "products", "stock_params")}
    numbering = c.get("numbering")
    movements_repo, counts_repo = store("stock_movements"), store("stock_counts")
    ledger = DatabaseLedger(movements_repo, numbering)
    suppliers, pos = c.get("suppliers"), c.get("purchase_orders")
    refs = {
        "categories": c.get("categories").find,
        "uom": c.get("units").find,
        "tax_groups": c.get("tax_groups").find,
        "suppliers": suppliers.list,
        "unit_factor": c.get("unit_converter").factor,
    }
    s = build_services(repos, ledger, refs, on_order=pos.quantity_on_order)
    stock = c.register("stock", s["stock"])
    products = c.register("products", s["products"])
    products.references = c.get("references")
    c.register("warehouses", s["warehouses"])
    c.register("locations", s["locations"])
    c.register("stock_params", s["params"])
    counts = c.register("counts", CountService(counts_repo, stock, repos["warehouses"], numbering, current_username))
    replenishment = c.register(
        "replenishment",
        ReplenishmentService(
            stock,
            repos["stock_params"],
            suppliers,
            pos,
            c.get("tax_calculator"),
            current_username,
            c.get("unit_converter").factor,
        ),
    )
    app.register_blueprint(_blueprint(s, counts, replenishment))

    # The products tell taxes, units and categories when a code is still used
    references = c.get("references")
    references.register("tax_group", lambda code: products.uses(("cSalesTaxGroup", "cPurchaseTaxGroup"), code))
    references.register("uom", products.uses_unit)
    references.register("category", lambda code: products.uses(("cCategory",), code))

    lookups = c.get("lookups")
    lookups.register("products", label_lookup(products, DESC_FR, DESC_EN, limit=30))
    lookups.register(
        "stockproducts", label_lookup(products, DESC_FR, DESC_EN, keep=lambda r: r.get("lStocked"), limit=30)
    )
    lookups.register("warehouses", label_lookup(s["warehouses"], ("cNameFR",), ("cNameEN", "cNameFR")))

    def locations_lookup():
        wh = text(request.args.get("wh")).upper()
        rows = [
            {
                "code": loc["cCode"],
                "label": " · ".join(
                    x for x in (loc["cWarehouse"], loc.get("cDescription") or loc.get("cType", "")) if x
                ),
            }
            for loc in repos["locations"].all()
            if not wh or loc["cWarehouse"].upper() == wh
        ]
        return rows, 200

    lookups.register("locations", locations_lookup)

    def dashboard():
        return {
            "products": repos["products"].count(),
            "warehouses": repos["warehouses"].count(),
            "stockValue": round(sum(number(r["dValue"]) for r in stock.valuation_rows()), 2),
            "reorderItems": len(replenishment.rows()),
        }

    c.get("dashboard").register(dashboard)

    # Demo data: prepared now (memory), loaded into the tables on an empty database and on /api/reset
    demo = prepare_demo(seed, {**refs, "suppliers": lambda: seed.get("_suppliers", [])})
    lifecycle = c.get("lifecycle")
    for name in ("warehouses", "locations", "products", "stock_params"):
        lifecycle.add(repos[name], "inv_" + name, demo[name])
    lifecycle.add(movements_repo, "inv_movements", demo["movements"])
    lifecycle.add(counts_repo, "inv_counts", [])

    def after_load(data):
        """Balances and numbering follow the movements and counts that were loaded."""
        if "inv_movements" in data:
            ledger.rebuild()
            numbering.set_next("STOCK_MOVE", max((int(x["iNo"]) for x in data["inv_movements"]), default=0) + 1)
        if "inv_counts" in data:
            numbering.set_next("STOCK_COUNT", max((int(x["iNo"]) for x in data["inv_counts"]), default=0) + 1)

    lifecycle.after_load(after_load)
    lifecycle.on_clear(DatabaseLedger.clear_balances)
