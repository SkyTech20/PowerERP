"""Production module, built step by step (Docs/PowerERP-Cadastros-Plano.md).

P1: the reference lists /api/capabilities, /api/setup-families, /api/downtime-reasons, /api/scrap-reasons.
P2: working calendars /api/calendars (+ /<code>/availability?from=&to=) and /api/calendar-exceptions.
P3: work centers /api/work-centers (+ /<code>/availability?from=&to=: the calendar time and the capacity).

Production never changes the stock directly: it posts movements through the stock service of the container
(c.get("stock").add(...) with cDocType "PROD"), so every stock rule applies to it.
"""

from __future__ import annotations

from datetime import date, timedelta

from flask import Blueprint, Flask, jsonify, request

from powererp.container import Container
from powererp.core.errors import AppError
from powererp.modules.common.crud import register_crud_routes
from powererp.modules.common.registry import label_lookup
from powererp.store import store

from .calendar import CalendarExceptionService, CalendarService
from .service import (
    CapabilityService,
    DowntimeReasonService,
    ReferenceListService,
    ScrapReasonService,
    SetupFamilyService,
)
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
    _register_work_centers(bp, c, seed, calendars)
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


def _register_work_centers(bp: Blueprint, c: Container, seed: dict, calendars: CalendarService) -> None:
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
