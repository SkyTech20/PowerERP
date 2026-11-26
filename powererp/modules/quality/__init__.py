"""Quality module (step 5 of the SCOR / ISO plan): the status of the lots and the nonconformances.

GET /api/lot-status?status=&product=&q=       the lots in stock (and the lots not released) with their status
GET /api/lot-status/<product>/<lot>           one lot, with the history of its status
POST /api/lot-status/<product>/<lot>          {cStatus, cReason}: a new status
POST /api/lot-status/hold                     {lots: [{cProduct, cLot}], cReason}: hold several lots (a recall)
/api/nonconformances (+ /<no>), POST /<no>/close {cDisposition, cAction...} and /<no>/reopen {cComment}
Lookups: lot_products (the products with lots), lot_choices (?product=: its lots and their status).

A lot that is not released is left out of the sales invoices and of the production orders (inventory/picking.py:
the services ask c.get("lot_status").held()).
"""

from __future__ import annotations

from flask import Blueprint, Flask, jsonify, request

from powererp.container import Container
from powererp.core.http import json_payload
from powererp.core.pagination import paginate_request
from powererp.core.security import current_username
from powererp.core.values import text
from powererp.store import store

from .lots import LotStatusService
from .nonconformances import SEQUENCE, NonconformanceService


def register(app: Flask, c: Container) -> None:
    bp = Blueprint("quality", __name__)
    products = c.get("products")
    lots = c.register(
        "lot_status",
        LotStatusService(
            store("lot_status"), {"stock": lambda: c.get("stock"), "products": lambda: products.find}, current_username
        ),
    )
    numbering = c.get("numbering")
    ncs = c.register(
        "nonconformances",
        NonconformanceService(store("nonconformances"), lots, {"products": products.find}, numbering, current_username),
    )

    @bp.route("/api/lot-status")
    def lot_status_list():
        return jsonify(lots.lots(request.args))

    @bp.route("/api/lot-status/<product>/<lot>")
    def lot_status_item(product, lot):
        return jsonify(lots.get(product, lot))

    @bp.route("/api/lot-status/<product>/<lot>", methods=["POST"])
    def lot_status_change(product, lot):
        body = json_payload()
        return jsonify(lots.change(product, lot, text(body.get("cStatus")), text(body.get("cReason"))))

    @bp.route("/api/lot-status/hold", methods=["POST"])
    def lot_status_hold():
        body = json_payload()
        return jsonify(lots.hold_many(body.get("lots") or [], text(body.get("cReason"))))

    @bp.route("/api/nonconformances", methods=["GET", "POST"])
    def nonconformances():
        if request.method == "GET":
            rows = [ncs.summary(r) for r in ncs.list()]
            return jsonify(paginate_request(rows, ("cProduct", "cLot", "cRef", "cDescription", "cCause", "cAction")))
        return jsonify(ncs.create(json_payload())), 201

    @bp.route("/api/nonconformances/<int:no>", methods=["GET", "PUT", "DELETE"])
    def nonconformance(no):
        if request.method == "GET":
            return jsonify(ncs.view(ncs.get(no)))
        if request.method == "DELETE":
            ncs.delete(no)
            return jsonify({"ok": True})
        return jsonify(ncs.update(no, json_payload()))

    @bp.route("/api/nonconformances/<int:no>/close", methods=["POST"], defaults={"action": "close"})
    @bp.route("/api/nonconformances/<int:no>/reopen", methods=["POST"], defaults={"action": "reopen"})
    def nonconformance_action(no, action):
        body = json_payload()
        if action == "reopen":
            return jsonify(ncs.reopen(no, text(body.get("cComment"))))
        return jsonify(ncs.close(no, body))

    def lot_products():
        fields = ("cDescEN", "cDescFR") if request.args.get("lang") == "en" else ("cDescFR",)
        return lots.products(fields), 1000

    def lot_choices():
        return lots.lot_choices(text(request.args.get("product")), text(request.args.get("lang"))), 1000

    lookups = c.get("lookups")
    lookups.register("lot_products", lot_products)
    lookups.register("lot_choices", lot_choices)
    lifecycle = c.get("lifecycle")
    lifecycle.add(lots.repo, "qa_lot_status", [])
    lifecycle.add(ncs.repo, "qa_nonconformances", [])

    def renumber(data: dict) -> None:
        if "qa_nonconformances" in data:
            top = max((int(r.get("iNo") or 0) for r in data["qa_nonconformances"]), default=0)
            numbering.set_next(SEQUENCE, top + 1)

    lifecycle.after_load(renumber)
    app.register_blueprint(bp)
