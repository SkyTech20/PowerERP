"""Application factory: builds the Flask app of the ERP (create_app), with its database, modules and seed.

    from powererp.factory import create_app
    app = create_app()
"""

from __future__ import annotations

from pathlib import Path

from flask import Flask

from . import database
from .container import Container
from .core.errors import register_error_handlers
from .seed.demo import DemoData

ROOT = Path(__file__).resolve().parent.parent


def create_app(database_url: str | None = None, dataset: str | None = None) -> Flask:
    # The route modules are still at the project root (moved into powererp/modules in phases O2 to O5)
    import db
    from auth import register_auth
    from backup_api import register_backup
    from erp_api import register_erp
    from inventory_api import register_inventory
    from powerware_api import register_powerware
    from purchasing_api import register_purchasing

    app = Flask("powererp", root_path=str(ROOT))
    container = Container()
    app.extensions["powererp"] = container
    register_error_handlers(app)

    container.register("database_url", db.init(database_url))
    register_auth(app)
    demo = container.register("demo", DemoData.load(dataset))
    hooks = container.register("hooks", register_erp(app, demo.lists))
    # PowerWARE-compatible web services, so SkyAI can read from and write to this ERP
    register_powerware(app, demo.lists, hooks["invoice_exists"], hooks["record_invoice"])
    # Best supplier per item and PO creation for SkyAI requisitions (Offer workflow)
    register_purchasing(app, demo.lists, hooks)
    # Products, taxes and inventory (warehouses, locations, movements, replenishment, counts)
    register_inventory(app, demo.lists, hooks)
    # Administration > Backups: pg_dump on a schedule (settings in the database), with rotation
    register_backup(app)
    database.init_app(app)  # one transaction per request
    _seed_or_migrate(db, hooks, demo)
    return app


def _seed_or_migrate(db, hooks, demo: DemoData) -> None:
    """An empty database (or another dataset) gets the demo data; data of an older database kept as JSON
    (legacy_datasets) is moved into the tables once."""
    stored = db.load_datasets()
    with database.unit_of_work():
        if stored and db.get_setting("dataset") == demo.name:
            hooks["load"](stored)
            moved = [k for k in hooks["store_keys"]() if k in stored]
        else:
            hooks["seed"]()
            moved = hooks["store_keys"]()
    db.drop_datasets(moved)
    db.set_setting("dataset", demo.name)
