"""Production module, built step by step (Docs/PowerERP-Cadastros-Plano.md).

P1: the reference lists /api/capabilities, /api/setup-families, /api/downtime-reasons, /api/scrap-reasons.
P2: working calendars /api/calendars (+ /<code>/availability?from=&to=) and /api/calendar-exceptions.
P3: work centers /api/work-centers (+ /<code>/availability?from=&to=: the calendar time and the capacity).
P4: resources /api/resources (+ /<code>/availability: calendar - planned downtime, capacity), and
    /api/capabilities/<code>/resources: the resources able to do it, preferred first.
P5: standard operations /api/operations (+ /<code>/time?qty=&lot=&resource=: setup and run minutes).
P6: setup matrices /api/setup-matrices/<scope>/<code> (+ /grid), and /api/setup-changeover?from=&to=&resource=
    (or &workCenter=) &default=: the changeover a sequence costs, and which rule gave it.
P7: manufacturing data of the products /api/product-mfg/<product> (make / buy, setup family, lots, traceability,
    attributes); deleted with the product.
P8: recipes /api/recipes/<product>/<revision> (materials, outputs, operations), and
    /api/recipes/<product>/<revision>/explode?qty=: materials, times and cost for a quantity.
P9: the steps of the recipe operations; POST /api/recipes/<product>/<revision>/steps/check
    {iOpSeq, iStep, value}: the value against the limits of the step (what the shop floor will call).
P10: POST /api/recipes/<product>/<revision>/submit | approve | reject | obsolete | default | copy,
    GET /api/recipes/<product>/compare?a=&b=, GET /api/products/<code>/recipe?date= (the current version).
M3a: production orders /api/production-orders (+ /calc: a draft calculated without saving it, and
    POST /<no>/release | unrelease | cancel {cComment}).

Production never changes the stock directly: it posts movements through the stock service of the container
(c.get("stock").add(...) with cDocType "PROD"), so every stock rule applies to it.
"""

from __future__ import annotations

from datetime import date, timedelta

from flask import Blueprint, Flask, jsonify, request

from powererp.container import Container
from powererp.core.errors import AppError
from powererp.core.http import json_payload
from powererp.core.pagination import paginate_request
from powererp.core.security import current_can, current_username
from powererp.core.values import text
from powererp.modules.common.crud import register_crud_routes
from powererp.modules.common.registry import label_lookup
from powererp.store import store

from .calendar import CalendarExceptionService, CalendarService
from .operations import OperationService
from .orders import SEQUENCE, ProductionOrderService
from .products import ProductMfgService
from .recipe_flow import RecipeFlow
from .recipes import RecipeService, prepare_demo
from .resources import ResourceService
from .service import (
    CapabilityService,
    DowntimeReasonService,
    ReferenceListService,
    ScrapReasonService,
    SetupFamilyService,
)
from .setup_matrix import SetupMatrixService
from .steps import check_value
from .work_centers import WorkCenterService

DESC_FR, DESC_EN = ("cDescFR",), ("cDescEN", "cDescFR")
SEARCH = ("cCode", "cDescFR", "cDescEN")

# key (container, lookups, table and seed), URL, service class
LISTS = (
    ("capabilities", "capabilities", CapabilityService),
    ("setup_families", "setup-families", SetupFamilyService),
    ("downtime_reasons", "downtime-reasons", DowntimeReasonService),
    ("scrap_reasons", "scrap-reasons", ScrapReasonService),
)


def register(app: Flask, c: Container, seed: dict) -> None:
    bp = Blueprint("production", __name__)
    for key, url, cls in LISTS:
        service: ReferenceListService = c.register(key, cls(store(key), c.get("references")))
        search = SEARCH + (("cGroup",) if "cGroup" in service.form.schema else ())
        register_crud_routes(bp, url, key, service, search)
        c.get("lookups").register(key, label_lookup(service, DESC_FR, DESC_EN, keep=lambda r: r.get("lActive")))
        c.get("lifecycle").add(service.repo, "prod_" + key, seed.get(key, []))
    calendars = _register_calendars(bp, c, seed)
    centers = _register_work_centers(bp, c, seed, calendars)
    resources = _register_resources(bp, c, seed, calendars, centers)
    _register_operations(bp, c, seed, centers, resources)
    _register_setup_matrix(bp, c, seed, centers, resources)
    _register_product_mfg(bp, c, seed)
    _register_recipes(bp, c, seed)
    _register_orders(bp, c)
    app.register_blueprint(bp)


def _day(name: str, default: date) -> date:
    value = request.args.get(name)
    if not value:
        return default
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        raise AppError("invalid_date", name) from None


def _week() -> tuple[date, date]:
    """?from=&to= of an availability request; the current week (Monday to Sunday) by default."""
    today = date.today()
    start = _day("from", today - timedelta(days=today.weekday()))
    return start, _day("to", start + timedelta(days=6))


def _register_calendars(bp: Blueprint, c: Container, seed: dict) -> CalendarService:
    calendars = c.register(
        "calendars", CalendarService(store("calendars"), store("calendar_exceptions"), c.get("references"))
    )
    exceptions = c.register("calendar_exceptions", CalendarExceptionService(store("calendar_exceptions"), calendars))
    register_crud_routes(bp, "calendars", "calendars", calendars, SEARCH)
    register_crud_routes(
        bp, "calendar-exceptions", "calendar_exceptions", exceptions, ("cCalendar", "dDate", "cDescFR", "cDescEN")
    )

    @bp.route("/api/calendars/<code>/availability")
    def calendar_availability(code):
        """Minutes available per day; the current week (Monday to Sunday) by default."""
        return jsonify(calendars.availability(code, *_week()))

    c.get("lookups").register("calendars", label_lookup(calendars, DESC_FR, DESC_EN, keep=lambda r: r.get("lActive")))
    lifecycle = c.get("lifecycle")
    lifecycle.add(calendars.repo, "prod_calendars", seed.get("calendars", []))
    lifecycle.add(exceptions.repo, "prod_calendar_exceptions", seed.get("calendar_exceptions", []))
    return calendars


def _register_work_centers(bp: Blueprint, c: Container, seed: dict, calendars: CalendarService) -> WorkCenterService:
    locations = c.get("locations")
    refs = {
        "calendars": calendars.find,
        "warehouses": c.get("warehouses").find,
        "locations": locations.find_in,
        "suppliers": c.get("suppliers").find,
        "cost_centers": lambda: {r["code"] for r in c.get("cost_centers").lookup()[0]},
    }
    centers = c.register("work_centers", WorkCenterService(store("work_centers"), refs, c.get("references")))
    register_crud_routes(bp, "work-centers", "work_centers", centers, SEARCH + ("cType", "cCalendar"))

    @bp.route("/api/work-centers/<code>/availability")
    def work_center_availability(code):
        """The minutes of its calendar per day, and the capacity (x utilization) the scheduler can load."""
        wc = centers.get(code)
        if not wc["cCalendar"]:
            raise AppError("no_calendar", "cCalendar")
        out = calendars.availability(wc["cCalendar"], *_week())
        return jsonify(
            {**out, "cWorkCenter": wc["cCode"], "iCapacityMinutes": centers.capacity_minutes(wc, out["iMinutes"])}
        )

    c.get("lookups").register("work_centers", label_lookup(centers, DESC_FR, DESC_EN, keep=lambda r: r.get("lActive")))
    c.get("lifecycle").add(centers.repo, "prod_work_centers", seed.get("work_centers", []))
    return centers


def _register_resources(
    bp: Blueprint, c: Container, seed: dict, calendars: CalendarService, centers: WorkCenterService
) -> ResourceService:
    refs = {
        "work_centers": centers.find,
        "capabilities": c.get("capabilities").find,
        "downtime_reasons": c.get("downtime_reasons").find,
    }
    resources = c.register("resources", ResourceService(store("resources"), refs, calendars, c.get("references")))
    register_crud_routes(bp, "resources", "resources", resources, SEARCH + ("cWorkCenter", "cManufacturer", "cModel"))

    @bp.route("/api/resources/<code>/availability")
    def resource_availability(code):
        return jsonify(resources.availability(code, *_week()))

    @bp.route("/api/capabilities/<code>/resources")
    def capability_resources(code):
        c.get("capabilities").get(code)  # 404 when unknown
        rows = resources.with_capability(code)
        return jsonify(
            [
                {"cCode": r["cCode"], "cDescFR": r["cDescFR"], "cDescEN": r["cDescEN"], "cWorkCenter": r["cWorkCenter"]}
                for r in rows
            ]
        )

    c.get("lookups").register("resources", label_lookup(resources, DESC_FR, DESC_EN, keep=lambda r: r.get("lActive")))
    c.get("lifecycle").add(resources.repo, "prod_resources", seed.get("resources", []))
    return resources


def _number_arg(name: str, default: float) -> float:
    value = request.args.get(name)
    if value in (None, ""):
        return default
    try:
        return float(str(value).replace(",", "."))
    except ValueError:
        raise AppError("numeric", name) from None


def _register_operations(
    bp: Blueprint, c: Container, seed: dict, centers: WorkCenterService, resources: ResourceService
) -> None:
    refs = {
        "work_centers": centers.find,
        "capabilities": c.get("capabilities").find,
        "suppliers": c.get("suppliers").find,
    }
    operations = c.register("operations", OperationService(store("operations"), refs, c.get("references")))
    register_crud_routes(bp, "operations", "operations", operations, SEARCH + ("cWorkCenter", "cCapability"))

    @bp.route("/api/operations/<code>/time")
    def operation_time(code):
        """Minutes of ?qty= units (?lot= lot size for min_per_lot), on ?resource= (its speed and the
        efficiency of its work center), else at the standard."""
        speed, efficiency = 1.0, 100.0
        if request.args.get("resource"):
            res = resources.get(request.args["resource"])
            wc = centers.find(res["cWorkCenter"]) or {}
            speed, efficiency = float(res["dSpeedFactor"] or 1), float(wc.get("dEfficiencyPct") or 100)
        return jsonify(operations.minutes(code, _number_arg("qty", 1), _number_arg("lot", 0), speed, efficiency))

    c.get("lookups").register("operations", label_lookup(operations, DESC_FR, DESC_EN, keep=lambda r: r.get("lActive")))
    c.get("lifecycle").add(operations.repo, "prod_operations", seed.get("operations", []))


def _register_setup_matrix(
    bp: Blueprint, c: Container, seed: dict, centers: WorkCenterService, resources: ResourceService
) -> None:
    families = c.get("setup_families")
    refs = {
        "work_centers": centers.find,
        "resources": resources.find,
        "setup_families": families.find,
        "families": families.active,
    }
    matrices = c.register("setup_matrices", SetupMatrixService(store("setup_matrices"), refs, c.get("references")))
    register_crud_routes(bp, "setup-matrices", "setup_matrices", matrices, ("cScope", "cScopeCode", "cNotes"))

    @bp.route("/api/setup-matrices/<scope>/<code>/grid")
    def setup_matrix_grid(scope, code):
        matrices.get(scope, code)  # 404 when unknown
        return jsonify(matrices.grid(scope, code, _number_arg("default", 0)))

    @bp.route("/api/setup-changeover")
    def setup_changeover():
        a = request.args
        return jsonify(
            matrices.changeover(
                a.get("from", ""),
                a.get("to", ""),
                a.get("resource", ""),
                a.get("workCenter", ""),
                _number_arg("default", 0),
            )
        )

    c.get("lifecycle").add(matrices.repo, "prod_setup_matrices", seed.get("setup_matrices", []))


def _register_product_mfg(bp: Blueprint, c: Container, seed: dict) -> None:
    products = c.get("products")
    refs = {"products": products.find, "setup_families": c.get("setup_families").find}
    mfg = c.register("product_mfg", ProductMfgService(store("product_mfg"), refs, c.get("references")))
    products.on_delete.append(mfg.delete_for)
    register_crud_routes(bp, "product-mfg", "product_mfg", mfg, ("cProduct", "cSetupFamily", "cMakeBuy", "cNotes"))
    c.get("lifecycle").add(mfg.repo, "prod_product_mfg", seed.get("product_mfg", []))


def _register_recipes(bp: Blueprint, c: Container, seed: dict) -> None:
    refs = {
        "products": c.get("products").find,
        "product_mfg": c.get("product_mfg").find,
        "operations": c.get("operations").find,
        "work_centers": c.get("work_centers").find,
        "resources": c.get("resources").find,
        "capabilities": c.get("capabilities").find,
        "suppliers": c.get("suppliers").find,
        "with_capability": c.get("resources").with_capability,
        "unit_factor": c.get("unit_converter").factor,
    }
    recipes = c.register("recipes", RecipeService(store("recipes"), refs, c.get("references")))
    register_crud_routes(bp, "recipes", "recipes", recipes, ("cProduct", "cRevision", "cDescFR", "cDescEN", "cStatus"))

    @bp.route("/api/recipes/<product>/<revision>/explode")
    def recipe_explode(product, revision):
        recipes.get(product, revision)  # 404 when unknown
        return jsonify(
            recipes.explode(product, revision, _number_arg("qty", 0) or _base_qty(recipes, product, revision))
        )

    demo_lists = {**seed, "products": c.get("demo").inventory.get("products", [])}

    @bp.route("/api/recipes/<product>/<revision>/steps/check", methods=["POST"])
    def recipe_step_check(product, revision):
        body = json_payload()
        recipe = recipes.get(product, revision)
        step = next(
            (
                s
                for s in recipe.get("steps", [])
                if str(s["iOpSeq"]) == str(body.get("iOpSeq")) and str(s["iStep"]) == str(body.get("iStep"))
            ),
            None,
        )
        if step is None:
            raise AppError("unknown_ref", "iStep")
        return jsonify(check_value(step, body.get("value")))

    flow = c.register("recipe_flow", RecipeFlow(recipes, current_username, lambda: current_can("prod.recipes:approve")))

    @bp.route("/api/recipes/<product>/<revision>/<action>", methods=["POST"])
    def recipe_action(product, revision, action):
        body = request.get_json(silent=True) or {}
        comment = text(body.get("cComment"))
        if action == "copy":
            row = flow.new_version(product, revision, text(body.get("cRevision")), comment)
            return jsonify(recipes.view(row)), 201
        moves = {
            "submit": flow.submit,
            "approve": flow.approve,
            "reject": flow.reject,
            "obsolete": flow.obsolete,
        }
        if action == "default":
            return jsonify(recipes.view(flow.make_default(product, revision)))
        if action not in moves:
            raise AppError("not_found", status=404)
        return jsonify(recipes.view(moves[action](product, revision, comment)))

    @bp.route("/api/recipes/<product>/compare")
    def recipe_compare(product):
        return jsonify(flow.compare(product, request.args.get("a", ""), request.args.get("b", "")))

    @bp.route("/api/products/<code>/recipe")
    def product_current_recipe(code):
        c.get("products").get(code)  # 404 when unknown
        row = flow.current(code, _day("date", date.today()))
        if row is None:
            raise AppError("no_approved_recipe", status=404)
        return jsonify(recipes.view(row))

    c.get("lifecycle").add(recipes.repo, "prod_recipes", prepare_demo(seed.get("recipes", []), demo_lists))


def _register_orders(bp: Blueprint, c: Container) -> None:
    refs = {
        "products": c.get("products").find,
        "product_mfg": c.get("product_mfg").find,
        "warehouses": c.get("warehouses").find,
        "recipes": c.get("recipes"),
        "current_recipe": c.get("recipe_flow").current,
        "stock": lambda: c.get("stock"),
    }
    numbering = c.get("numbering")
    orders = c.register(
        "production_orders",
        ProductionOrderService(store("production_orders"), refs, numbering, current_username, c.get("references")),
    )

    @bp.route("/api/production-orders", methods=["GET", "POST"])
    def production_orders():
        if request.method == "GET":
            rows = [orders.summary(o) for o in orders.list()]
            return jsonify(paginate_request(rows, ("cProduct", "cDescFR", "cDescEN", "cLot", "cNotes")))
        return jsonify(orders.create(json_payload())), 201

    @bp.route("/api/production-orders/<int:no>", methods=["GET", "PUT", "DELETE"])
    def production_order(no):
        order = orders.get(no)
        if request.method == "GET":
            return jsonify(orders.view(order))
        if request.method == "DELETE":
            orders.delete(no)
            return jsonify({"ok": True})
        return jsonify(orders.update(no, json_payload()))

    @bp.route("/api/production-orders/calc", methods=["POST"])
    @bp.route("/api/production-orders/<int:no>/calc", methods=["POST"])
    def production_order_calc(no=None):
        return jsonify(orders.preview(json_payload(), no))

    @bp.route("/api/production-orders/<int:no>/<action>", methods=["POST"])
    def production_order_action(no, action):
        body = request.get_json(silent=True) or {}
        return jsonify(orders.move(no, action, text(body.get("cComment"))))

    recipes = c.get("recipes")

    def made_products():
        """The products that have an approved recipe (what an order can make)."""
        fields = ("cDescEN", "cDescFR") if request.args.get("lang") == "en" else ("cDescFR",)
        codes = sorted({r["cProduct"].upper() for r in recipes.repo.all(lines=False) if r["cStatus"] == "approved"})
        rows = []
        for code in codes:
            p = c.get("products").find(code)
            if p:
                rows.append({"code": p["cCode"], "label": next((p[f] for f in fields if p.get(f)), "")})
        return rows, 200

    def approved_revisions():
        """The approved revisions of a product (?product=): the recipe an order can be made from."""
        code = text(request.args.get("product")).upper()
        fields = ("cDescEN", "cDescFR") if request.args.get("lang") == "en" else ("cDescFR",)
        rows = [
            {
                "code": r["cRevision"],
                "label": " ".join(
                    x for x in (next((r[f] for f in fields if r.get(f)), ""), "★" if r.get("lDefault") else "") if x
                ),
            }
            for r in recipes.repo.all(lines=False)
            if r["cProduct"].upper() == code and r["cStatus"] == "approved"
        ]
        return sorted(rows, key=lambda r: r["code"]), 200

    c.get("lookups").register("made_products", made_products)
    c.get("lookups").register("approved_revisions", approved_revisions)
    c.get("lifecycle").add(orders.repo, "prod_orders", [])

    def renumber(data: dict) -> None:
        if "prod_orders" in data:
            numbering.set_next(SEQUENCE, max((int(o.get("iNo") or 0) for o in data["prod_orders"]), default=0) + 1)

    c.get("lifecycle").after_load(renumber)


def _base_qty(recipes: RecipeService, product: str, revision: str) -> float:
    return float(recipes.get(product, revision)["dBaseQty"] or 1)
