"""Production module, built step by step (Docs/PowerERP-Cadastros-Plano.md).

P1: the reference lists /api/capabilities, /api/setup-families, /api/downtime-reasons, /api/scrap-reasons.
P2: working calendars /api/calendars (+ /<code>/availability?from=&to=) and /api/calendar-exceptions.

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
    _register_calendars(bp, c, seed)
    app.register_blueprint(bp)


def _day(name: str, default: date) -> date:
    value = request.args.get(name)
    if not value:
        return default
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        raise AppError("invalid_date", name) from None


def _register_calendars(bp: Blueprint, c: Container, seed: dict) -> None:
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
        today = date.today()
        start = _day("from", today - timedelta(days=today.weekday()))
        end = _day("to", start + timedelta(days=6))
        return jsonify(calendars.availability(code, start, end))

    c.get("lookups").register("calendars", label_lookup(calendars, DESC_FR, DESC_EN, keep=lambda r: r.get("lActive")))
    lifecycle = c.get("lifecycle")
    lifecycle.add(calendars.repo, "prod_calendars", seed.get("calendars", []))
    lifecycle.add(exceptions.repo, "prod_calendar_exceptions", seed.get("calendar_exceptions", []))
