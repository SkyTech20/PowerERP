"""Purchasing module: purchase orders (/api/purchase-orders), receptions (/api/receptions) and supplier invoices
(/api/invoices). SkyAI reads and writes the same records through the PowerWARE services
(powererp.integrations.powerware)."""

from __future__ import annotations

from flask import Blueprint, Flask, jsonify, request

from powererp.container import Container
from powererp.core.http import json_payload
from powererp.core.pagination import paginate_request

from . import repository
from .services import (
    BillingService,
    DocumentNumbering,
    InvoiceService,
    PurchaseOrderService,
    ReceptionService,
    compute_invoice,
)

__all__ = [
    "BillingService",
    "DocumentNumbering",
    "InvoiceService",
    "PurchaseOrderService",
    "ReceptionService",
    "compute_invoice",
    "register",
    "repository",
]

# The full dataset starts with these invoices; the demo dataset with none (or its history)
SAMPLE_INVOICES = [
    {
        "cNoFourn": "ZEPMAN",
        "cNoFacture": "ZM-48812",
        "dDateFacture": "2026-09-02",
        "cNoCommAch": "",
        "cDevise": "CAD",
        "cStatut": "Posted",
        "cSource": "ERP",
        "dTransport": "0.00",
        "dTotalTPS": "12.50",
        "dTotalTVP": "24.94",
        "lines": [
            {
                "cCodeProduit": "CLEAN-01",
                "cDescription": "Industrial degreaser 20L",
                "dQuantite": "2",
                "dCoutUnitaire": "125.00",
                "cGL": "5960",
                "cCC1": "100",
                "cCC2": "215",
                "iNoReception": "",
            },
        ],
    },
    {
        "cNoFourn": "MANSCO",
        "cNoFacture": "SC-2024-0311",
        "dDateFacture": "2024-03-15",
        "cNoCommAch": "266009",
        "cDevise": "CAD",
        "cStatut": "Approved",
        "cSource": "ERP",
        "dTransport": "15.00",
        "dTotalTPS": "0.00",
        "dTotalTVP": "0.00",
        "lines": [
            {
                "cCodeProduit": "AIR00276",
                "cDescription": "MRFCP.08.1/8 Flow regulator",
                "dQuantite": "10",
                "dCoutUnitaire": "8.82",
                "cGL": "",
                "cCC1": "",
                "cCC2": "",
                "iNoReception": "335871",
            },
            {
                "cCodeProduit": "AIR00273",
                "cDescription": "MRFCP.1/4.1/4 Flow regulator",
                "dQuantite": "10",
                "dCoutUnitaire": "8.82",
                "cGL": "",
                "cCC1": "",
                "cCC2": "",
                "iNoReception": "335871",
            },
        ],
    },
    {
        "cNoFourn": "RE3DIS",
        "cNoFacture": "INV-77120",
        "dDateFacture": "2026-09-20",
        "cNoCommAch": "",
        "cDevise": "CAD",
        "cStatut": "Draft",
        "cSource": "ERP",
        "dTransport": "0.00",
        "dTotalTPS": "22.50",
        "dTotalTVP": "44.89",
        "lines": [
            {
                "cCodeProduit": "SIGN",
                "cDescription": "Trade show banners",
                "dQuantite": "3",
                "dCoutUnitaire": "150.00",
                "cGL": "5960",
                "cCC1": "100",
                "cCC2": "400",
                "iNoReception": "",
            },
        ],
    },
]


def _blueprint(pos: PurchaseOrderService, recs: ReceptionService, invs: InvoiceService) -> Blueprint:
    bp = Blueprint("purchasing", __name__)

    @bp.route("/api/purchase-orders", methods=["GET", "POST"])
    def po_collection():
        if request.method == "GET":
            rows = [{k: v for k, v in r.items() if k != "lines"} for r in pos.list()]
            return jsonify(paginate_request(rows, ("cPO", "cSupplierCode", "cSupplierName", "cBuyerName")))
        return jsonify(pos.create(json_payload())), 201

    @bp.route("/api/purchase-orders/<cpo>", methods=["GET", "PUT", "DELETE"])
    def po_item(cpo):
        view = pos.get(cpo)
        if request.method == "GET":
            return jsonify(view)
        if request.method == "DELETE":
            pos.delete(cpo)
            return jsonify({"ok": True})
        return jsonify(pos.update(cpo, json_payload()))

    @bp.route("/api/receptions", methods=["GET", "POST"])
    def rec_collection():
        if request.method == "GET":
            rows = [{k: v for k, v in r.items() if k != "lines"} for r in recs.list()]
            return jsonify(paginate_request(rows, ("NoReception", "NoBonCommande", "CodeFournisseur", "Fournisseur")))
        return jsonify(recs.create(json_payload())), 201

    @bp.route("/api/receptions/<no>", methods=["GET", "PUT", "DELETE"])
    def rec_item(no):
        view = recs.get(no)
        if request.method == "GET":
            return jsonify(view)
        if request.method == "DELETE":
            recs.delete(no)
            return jsonify({"ok": True})
        return jsonify(recs.update(no, json_payload()))

    @bp.route("/api/invoices", methods=["GET", "POST"])
    def inv_collection():
        if request.method == "GET":
            rows = [{k: v for k, v in invs.with_count(i).items() if k != "lines"} for i in invs.list()]
            return jsonify(paginate_request(rows, ("cNoFacture", "cNoFourn", "cNomFourn", "cNoCommAch")))
        return jsonify(invs.create(json_payload())), 201

    @bp.route("/api/invoices/<int:inv_id>", methods=["GET", "PUT", "DELETE"])
    def inv_item(inv_id):
        inv = invs.get(inv_id)
        if request.method == "GET":
            return jsonify(invs.with_count(inv))
        if request.method == "DELETE":
            invs.delete(inv_id)
            return jsonify({"ok": True})
        return jsonify(invs.update(inv_id, json_payload()))

    return bp


def register(app: Flask, c: Container, seed: dict) -> None:
    supplier_name = c.get("suppliers").name_of
    numbering = c.register("numbering", DocumentNumbering())
    pos = c.register("purchase_orders", PurchaseOrderService(supplier_name, numbering))
    recs = c.register("receptions", ReceptionService(supplier_name))
    billing = c.register("billing", BillingService())
    invs = c.register("invoices", InvoiceService(supplier_name, billing, numbering, recs))
    app.register_blueprint(_blueprint(pos, recs, invs))

    c.get("lookups").register("po", pos.lookup)
    dashboard = c.get("dashboard")
    dashboard.register(pos.counts)
    dashboard.register(recs.counts)
    dashboard.register(invs.dashboard)

    # Seed: the PowerWARE lists of the dataset; the invoices are computed now with the seed suppliers' names
    names = {s["cCode"].upper(): s["cName"] for s in seed["supplier_terms_data"]}
    seed_invoices = InvoiceService.prepare_seed(
        seed.get("seed_invoices", SAMPLE_INVOICES), lambda code: names.get(str(code).strip().upper(), "")
    )
    lifecycle = c.get("lifecycle")
    lifecycle.add_dataset(
        {"po_details": seed["po_details"], "unbilled_po": seed["unbilled_po"]},
        lambda d: repository.po_replace_all(d.get("po_details", []), d.get("unbilled_po", [])),
        repository.po_clear,
    )
    lifecycle.add_dataset(
        {"receiving_details": seed["receiving_details"], "unbilled_receiving": seed["unbilled_receiving"]},
        lambda d: repository.rec_replace_all(d.get("receiving_details", []), d.get("unbilled_receiving", [])),
        repository.rec_clear,
    )
    lifecycle.add_dataset(
        {"invoices": seed_invoices}, lambda d: repository.inv_replace_all(d["invoices"]), repository.inv_clear
    )
