"""Application factory: builds the Flask app of the ERP (create_app), with its database, modules and seed.

    from powererp.factory import create_app
    app = create_app()

Each module registers its services in the container and its routes in the app; the modules talk to each other
through the services they get from the container, never through module-level state.
"""

from __future__ import annotations

from pathlib import Path

from flask import Flask

from . import database
from .container import Container
from .core.errors import register_error_handlers
from .integrations import powerware
from .modules import catalog, inventory, ledger, purchasing, suppliers, system, taxes
from .modules.common.registry import ReferenceRegistry
from .seed.demo import DemoData

ROOT = Path(__file__).resolve().parent.parent


def create_app(database_url: str | None = None, dataset: str | None = None) -> Flask:
    # Still at the project root: login and backups (moved into powererp/modules in O5)
    import db
    from auth import register_auth
    from backup_api import register_backup

    app = Flask("powererp", root_path=str(ROOT))
    c = Container()
    app.extensions["powererp"] = c
    register_error_handlers(app)

    c.register("database_url", db.init(database_url))
    register_auth(app)
    demo = c.register("demo", DemoData.load(dataset))

    system.register(app, c)  # lifecycle (seed / reset / clear), dashboard, lookups, the screens' files
    c.register("references", ReferenceRegistry())
    ledger.register(app, c, demo.lists)
    suppliers.register(app, c, demo.lists)
    taxes.register(app, c, demo.inventory)
    catalog.register(app, c, demo.inventory)
    purchasing.register(app, c, demo.lists)
    powerware.register(app, c)  # the web services SkyAI calls
    inventory.register(app, c, demo.inventory)
    register_backup(app)  # Administration > Backups
    database.init_app(app)  # one transaction per request
    _seed_or_migrate(db, c, demo)
    return app


def _seed_or_migrate(db, c: Container, demo: DemoData) -> None:
    """An empty database (or another dataset) gets the demo data; data of an older database kept as JSON
    (legacy_datasets) is moved into the tables once."""
    lifecycle = c.get("lifecycle")
    stored = db.load_datasets()
    with database.unit_of_work():
        if stored and db.get_setting("dataset") == demo.name:
            lifecycle.load(stored)
            moved = [k for k in lifecycle.keys() if k in stored]
        else:
            lifecycle.seed()
            moved = lifecycle.keys()
    db.drop_datasets(moved)
    db.set_setting("dataset", demo.name)
