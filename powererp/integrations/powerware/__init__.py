"""PowerWARE / SkyAI-compatible web services served by PowerERP.

Same paths, parameters and XML formats as the real PowerWARE web services (and the SkyAI mock API), backed by
the ERP's services. Point the SkyAI "APIs" configuration at this server (e.g. http://erp-sample:5050): SkyAI reads
suppliers, GL accounts, POs and receptions, creates its invoices (apInvoiceNoPO.p / apInvoiceWithPO.p) and the POs
of its requisitions (apCreatePO.p).

The routes are thin: the data comes from the services in the container, the XML from xml.py.
"""

from __future__ import annotations

import logging
import xml.etree.ElementTree as ET
from datetime import datetime

from flask import Blueprint, Flask, Response, jsonify, request

from powererp.container import Container

from .requisitions import RequisitionService, create_po_route
from .xml import (
    build_dspo_xml,
    build_dspodetail_xml,
    create_dsreceiving_xml_response,
    create_gl_xml_response,
    create_receiving_details_xml_response,
    create_supplier_xml_response,
    create_xml_response,
    invoice_error_response,
    invoice_success_response,
    parse_dsinput,
)

logger = logging.getLogger(__name__)

PW_PREFIX = "/cgi-bin/cgiip.exe/WService=wsbroker1/wm/custom/vol100/SkyAI"
XML = "application/xml; charset=utf-8"


def create_blueprint(c: Container) -> Blueprint:
    bp = Blueprint("powerware", __name__)
    suppliers = c.get("suppliers")
    accounts, centers = c.get("gl_accounts"), c.get("cost_centers")
    pos, recs, invoices = c.get("purchase_orders"), c.get("receptions"), c.get("invoices")

    @bp.route(PW_PREFIX + "/getReceivingDetails.p", methods=["GET"])
    def get_receiving_details():
        """Les détails d'une réception (XML dsReceiving)."""
        try:
            company = request.args.get("COMPANY", "")
            no_reception = request.args.get("NoReception", "")
            if not company:
                return jsonify({"error": "Paramètre COMPANY requis"}), 400
            if not no_reception:
                return jsonify({"error": "Paramètre NoReception requis"}), 400
            reception = recs.detail(no_reception)
            if reception is not None and reception.get("COMPANY") != company:
                reception = None
            if not reception:
                return jsonify({"error": f"Réception {no_reception} non trouvée pour la compagnie {company}"}), 404
            return create_receiving_details_xml_response(reception)
        except Exception:
            return jsonify({"error": "Erreur lors de la récupération des détails de réception"}), 500

    @bp.route(PW_PREFIX + "/getUnbilledPO.p", methods=["GET"])
    def get_unbilled_po():
        """Unbilled POs (XML dsPO / ttPO). Optional Supplier filters by cSupplierCode. Empty list = empty dsPO."""
        try:
            company = request.args.get("COMPANY", "")
            if not company:
                return jsonify({"error": "Paramètre COMPANY requis"}), 400
            rows = [po for po in pos.unbilled() if po.get("COMPANY") == company]
            supplier = (request.args.get("Supplier") or "").strip().upper()
            if supplier:
                rows = [po for po in rows if (po.get("cSupplierCode") or "").strip().upper() == supplier]
            return Response(build_dspo_xml(rows), mimetype=XML)
        except Exception:
            return jsonify({"error": "Erreur lors de la récupération des bons de commande non facturés"}), 500

    @bp.route(PW_PREFIX + "/getUnbilledReceiving.p", methods=["GET"])
    def get_unbilled_receiving():
        """Les réceptions non facturées (XML dsReceiving)."""
        try:
            company = request.args.get("COMPANY", "")
            if not company:
                return jsonify({"error": "Paramètre COMPANY requis"}), 400
            rows = [r for r in recs.unbilled() if r.get("COMPANY") == company]
            if not rows:
                return jsonify({"error": f"Aucune réception non facturée trouvée pour la compagnie {company}"}), 404
            return create_dsreceiving_xml_response(rows)
        except Exception:
            return jsonify({"error": "Erreur lors de la récupération des réceptions non facturées"}), 500

    @bp.route(PW_PREFIX + "/getGLaccounts.p", methods=["GET"])
    def get_gl_accounts():
        """GL accounts and cost centers: JSON (Accept: application/json or format=json) or XML dsGLCC."""
        try:
            company = request.args.get("COMPANY", "")
            cc1 = request.args.get("CC1", "")
            wants_json = request.args.get("format", "").lower() == "json" or "application/json" in (
                request.headers.get("Accept") or ""
            )
            if not company:
                return jsonify({"error": "Paramètre COMPANY requis"}), 400
            gl = accounts.list()
            cc = [a for a in centers.list() if not cc1 or a.get("cCC1") == cc1]
            if not gl and not cc:
                return jsonify({"error": "Aucun compte GL trouvé"}), 404
            if wants_json:
                return jsonify({"gl_accounts": gl, "cost_centers": cc})
            return create_gl_xml_response(gl, cc)
        except Exception:
            return jsonify({"error": "Erreur lors de la récupération des comptes GL"}), 500

    @bp.route(PW_PREFIX + "/getPODetails.p", methods=["GET"])
    def get_po_details():
        """Les détails d'un bon de commande (XML dsPOdetail: ttPOheader + ttPOdetail)."""
        try:
            company = request.args.get("COMPANY", "")
            po_number = request.args.get("PO", "")
            if not company:
                return jsonify({"error": "Paramètre COMPANY requis"}), 400
            if not po_number:
                return jsonify({"error": "Paramètre PO requis"}), 400
            po = pos.detail(po_number)
            if po is not None and po.get("COMPANY") != company:
                po = None
            if not po:
                return jsonify({"error": f"Bon de commande {po_number} non trouvé pour la compagnie {company}"}), 404
            return Response(build_dspodetail_xml(po.get("ttPOheader", {}), po.get("ttPOdetail", [])), mimetype=XML)
        except Exception:
            return jsonify({"error": "Erreur lors de la récupération des détails du bon de commande"}), 500

    @bp.route(PW_PREFIX + "/getSupplierTerm.p", methods=["GET"])
    def get_supplier_term():
        """Les fournisseurs et leurs termes de paiement (filtres SupplierCode, TermCode)."""
        try:
            company = request.args.get("COMPANY", "")
            supplier_code = request.args.get("SupplierCode", "")
            term_filter = request.args.get("TermCode", "")
            if not company:
                return jsonify({"error": "Paramètre COMPANY requis"}), 400
            rows = suppliers.list()
            if supplier_code:
                rows = [s for s in rows if s["cCode"].upper() == supplier_code.upper()]
            if term_filter:
                rows = [s for s in rows if s["cTermCode"].upper() == term_filter.upper()]
            if not rows:
                error_msg = "Aucun fournisseur trouvé"
                if supplier_code:
                    error_msg += f" avec le code {supplier_code}"
                if term_filter:
                    error_msg += f" avec le terme {term_filter}"
                return jsonify({"error": error_msg}), 404
            return create_supplier_xml_response(rows)
        except Exception:
            return jsonify({"error": "Erreur lors de la récupération des termes fournisseurs"}), 500

    @bp.route(PW_PREFIX + "/getStats.p", methods=["GET"])
    def get_skyai_stats():
        """Statistiques pour SkyAI."""
        try:
            company = request.args.get("COMPANY", "MA2")
            stats = {
                "COMPANY": company,
                "DateGenerationStats": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "TotalBonesCommandeNonFactures": len([p for p in pos.unbilled() if p.get("COMPANY") == company]),
                "TotalReceptionsNonFacturees": len([r for r in recs.unbilled() if r.get("COMPANY") == company]),
                "MontantTotalEnAttente": f"{0.0:.2f}",
                "TotalFournisseurs": suppliers.count(),
                "Devise": "CAD",
                "StatusSysteme": "Opérationnel",
                "DerniereMAJ": "2025-09-19 10:30:00",
            }
            return create_xml_response(stats)
        except Exception:
            return jsonify({"error": "Erreur lors du calcul des statistiques"}), 500

    def create_invoice():
        today = datetime.now().strftime("%Y-%m-%d")
        body = request.get_data(as_text=True) or ""
        if not body.strip():
            return invoice_error_response("", "", today, "Corps de la requête vide")
        try:
            header, lines = parse_dsinput(body)
        except ET.ParseError as e:
            return invoice_error_response("", "", today, f"XML invalide: {e}")
        except ValueError as e:
            return invoice_error_response("", "", today, str(e))
        supplier = header.get("cNoFourn", "")
        number = header.get("cNoFacture", "")
        date = header.get("dDateFacture", "") or today
        if not supplier or not number:
            return invoice_error_response(supplier, number, date, "Fournisseur et numéro de facture requis")
        # Same error simulation as the SkyAI mock API
        simulate = request.args.get("simulate_error", "").strip() in ("1", "true", "yes")
        if simulate or "FAIL" in number.upper() or "ERROR" in number.upper():
            return invoice_error_response(supplier, number, date, "Facture existante")
        if invoices.exists(supplier, number):
            return invoice_error_response(supplier, number, date, "Facture existante")
        try:
            invoices.from_powerware(header, lines)
        except Exception as e:  # keep the PowerWARE contract: errors come back as ttError
            logger.exception("PowerERP: could not create invoice")
            return invoice_error_response(supplier, number, date, str(e))
        return invoice_success_response(supplier, number, date)

    @bp.route(PW_PREFIX + "/apInvoiceNoPO.p", methods=["POST"])
    def ap_invoice_no_po():
        """Invoice without PO (dsInput: ttInputHD + ttInputDT with cGL / cCC1 / cCC2)."""
        return create_invoice()

    @bp.route(PW_PREFIX + "/apInvoiceWithPO.p", methods=["POST"])
    def ap_invoice_with_po():
        """Invoice with PO (dsInput: ttInputHD with cNoCommAch + ttInputDT with iNoReception)."""
        return create_invoice()

    create_po_route(bp, PW_PREFIX, RequisitionService(suppliers, pos))
    return bp


def register(app: Flask, c: Container) -> None:
    app.register_blueprint(create_blueprint(c))
