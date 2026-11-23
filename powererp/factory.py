"""Application factory: builds the Flask app of the ERP (create_app), with its database, modules and seed.

    from powererp.factory import create_app
    app = create_app()

Each module registers its services in the container and its routes in the app; the modules talk to each other
through the services they get from the container, never through module-level state.
"""

from __future__ import annotations

from pathlib import Path

from flask import Flask

from . import database, settings
from .container import Container
from .core.errors import register_error_handlers
from .integrations import powerware
from .modules import admin, auth, catalog, inventory, ledger, production, purchasing, suppliers, system, taxes
from .modules.common.registry import ReferenceRegistry
from .seed.demo import SCENARIOS, DemoData

ROOT = Path(__file__).resolve().parent.parent


def create_app(database_url: str | None = None, dataset: str | None = None) -> Flask:
    app = Flask("powererp", root_path=str(ROOT))
    c = Container()
    app.extensions["powererp"] = c
    register_error_handlers(app)

    c.register("database_url", settings.init(database_url))
    auth.register(app, c)  # login, users, access control
    # the scenario chosen when the demo data was last reset (dashboard), else ERP_SCENARIO
    demo = DemoData.load(dataset, settings.get_setting("demo_scenario"))
    _register_modules(app, c, demo)
    admin.register(app)  # Administration > Backups
    database.init_app(app)  # one transaction per request
    c.get("lifecycle").scenarios(demo.scenario, SCENARIOS, lambda scenario: _switch(c, dataset, scenario))
    _seed_or_migrate(c, demo)
    return app


def _register_modules(app: Flask, c: Container, demo: DemoData) -> None:
    """The modules that hold the demo data (their services, routes and seed)."""
    c.register("demo", demo)
    system.register(app, c)  # lifecycle (seed / reset / clear), dashboard, lookups, the screens' files
    c.register("references", ReferenceRegistry())
    ledger.register(app, c, demo.lists)
    suppliers.register(app, c, demo.lists)
    taxes.register(app, c, demo.inventory)
    catalog.register(app, c, demo.inventory)
    purchasing.register(app, c, demo.lists)
    powerware.register(app, c)  # the web services SkyAI calls
    inventory.register(app, c, demo.inventory)
    production.register(app, c, demo.production)  # reference lists of the shop floor (M0)


def demo_snapshot(dataset: str | None, scenario: str) -> dict:
    """The seed of every table for another scenario: the modules are registered on a scratch app, which prepares
    the demo data the same way as at start-up (nothing is written to the database)."""
    scratch, c = Flask("powererp-seed", root_path=str(ROOT)), Container()
    _register_modules(scratch, c, DemoData.load(dataset, scenario))
    return c.get("lifecycle").snapshot()


def _switch(c: Container, dataset: str | None, scenario: str) -> None:
    """Reset the demo data with another scenario, and keep it for the next starts."""
    c.get("lifecycle").replace_snapshot(demo_snapshot(dataset, scenario))
    settings.set_setting("demo_scenario", scenario)
    settings.set_setting("dataset", DemoData.load(dataset, scenario).name)


def _seed_or_migrate(c: Container, demo: DemoData) -> None:
    """An empty database (or another dataset) gets the demo data; data of an older database kept as JSON
    (legacy_datasets) is moved into the tables once."""
    lifecycle = c.get("lifecycle")
    stored = settings.load_datasets()
    with database.unit_of_work():
        if stored and settings.get_setting("dataset") == demo.name:
            lifecycle.load(stored)
            moved = [k for k in lifecycle.keys() if k in stored]
        else:
            lifecycle.seed()
            moved = lifecycle.keys()
    settings.drop_datasets(moved)
    settings.set_setting("dataset", demo.name)
