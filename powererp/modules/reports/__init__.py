"""Reports module: the supply chain indicators (step 7 of the SCOR / ISO plan, Reports > Supply chain indicators).

GET /api/kpi/scor?from=&to=&horizon=   the indicators of the period (see kpi.py), read only
"""

from __future__ import annotations

from flask import Blueprint, Flask, jsonify, request

from powererp.container import Container

from .kpi import KpiService


def register(app: Flask, c: Container) -> None:
    bp = Blueprint("reports", __name__)

    def optional(name: str, read, default):
        return lambda: read(c.get(name)) if name in c else default

    kpis = c.register(
        "kpi",
        KpiService(
            {
                "invoices": optional("sales_invoices", lambda s: s.list(), []),
                "orders": optional("production_orders", lambda s: s.list(), []),
                "receptions": optional("receptions", lambda s: s.list(), []),
                "ncs": optional("nonconformances", lambda s: s.list(), []),
                "lot_statuses": optional("lot_status", lambda s: s.statuses(), {}),
                "balances": lambda: c.get("stock").balances(),
                "movements": lambda: c.get("stock").ledger.all(),
                "products": lambda: c.get("stock").products_repo.all(lines=False),
                "unit_cost": lambda prod: c.get("stock").unit_cost(prod),
            }
        ),
    )

    @bp.route("/api/kpi/scor")
    def kpi_scor():
        return jsonify(kpis.indicators(request.args))

    app.register_blueprint(bp)
