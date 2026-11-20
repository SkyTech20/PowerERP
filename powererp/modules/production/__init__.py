"""Production module (Docs/PowerERP-Producao-Plano.md). M0: the module, its tables and the reference lists:
/api/capabilities, /api/setup-families, /api/downtime-reasons, /api/scrap-reasons.

Production never changes the stock directly: it posts movements through the stock service of the container
(c.get("stock").add(...) with cDocType "PROD"), so every stock rule applies to it.
"""

from __future__ import annotations

from flask import Blueprint, Flask

from powererp.container import Container
from powererp.modules.common.crud import register_crud_routes
from powererp.modules.common.registry import label_lookup
from powererp.store import store

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
    app.register_blueprint(bp)
