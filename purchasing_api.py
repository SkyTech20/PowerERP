"""
PowerERP — purchasing services used by the SkyAI requisition ("Offer") workflow.

  POST <PW_PREFIX>/getBestSupplier.p   best supplier (and the other candidates) for each item,
                                       with the reason (supplier_selection.py)
  POST <PW_PREFIX>/apCreatePO.p        one purchase order for one supplier (SkyAI calls it once
                                       per supplier after the approval). Calling it again for the
                                       same requisition and supplier returns the existing PO.

  GET  /api/supplier-selection/settings   criteria (weights, history window, tie margin, ...)
  PUT  /api/supplier-selection/settings   administrators only
  POST /api/supplier-selection/test       run the selection on typed items (settings screen)

JSON in and out. Same protection as the other PowerWARE services (X-API-Key when ERP_API_KEY is set).
"""
import logging
from datetime import datetime

from flask import Blueprint, jsonify, request

import supplier_selection as sel
from auth import current_user, _api_key_ok
from powerware_api import PW_PREFIX

logger = logging.getLogger(__name__)
bp = Blueprint("purchasing", __name__)
_ns = {}
_hooks = {}
FIRST_PO = 500501


def _json():
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else None


def _num(v):
    try:
        return float(str(v).replace(",", "."))
    except (TypeError, ValueError):
        return 0.0


@bp.route(PW_PREFIX + "/getBestSupplier.p", methods=["POST"])
def get_best_supplier():
    p = _json()
    if p is None or not isinstance(p.get("items"), list) or not p["items"]:
        return jsonify({"status": "error", "error": "items required"}), 400
    try:
        return jsonify(sel.best_suppliers(_ns, p))
    except Exception as e:  # never a 500 page for SkyAI: it shows the error on the task
        logger.exception("getBestSupplier.p failed")
        return jsonify({"status": "error", "error": str(e)}), 500


def _last_price(supplier, code):
    best = None
    for po in _ns["po_details"]:
        h = po.get("ttPOheader", {})
        if h.get("cSupplierCode") != supplier:
            continue
        for ln in po.get("ttPOdetail", []):
            if ln.get("cProductcode") == code and (best is None or h.get("dOrderDate", "") > best[0]):
                best = (h.get("dOrderDate", ""), _num(ln.get("dUnitCost")))
    return best[1] if best else 0.0


def _next_po_number():
    nums = [int(p["cPO"]) for p in _hooks["all_pos"]() if str(p["cPO"]).isdigit()]
    return str(max([FIRST_PO - 1] + nums) + 1)


@bp.route(PW_PREFIX + "/apCreatePO.p", methods=["POST"])
def ap_create_po():
    p = _json()
    if p is None:
        return jsonify({"status": "error", "error": "JSON body required"}), 400
    supplier_code = str(p.get("supplierCode") or "").strip()
    reference = str(p.get("requisitionNumber") or "").strip()
    supplier = next((s for s in _ns["supplier_terms_data"] if s.get("cCode") == supplier_code), None)
    if supplier is None:
        return jsonify({"status": "error", "error": f"unknown supplier {supplier_code}"}), 400
    lines_in = [ln for ln in (p.get("lines") or []) if isinstance(ln, dict)]
    if not lines_in:
        return jsonify({"status": "error", "error": "lines required"}), 400

    if reference:  # idempotent per requisition + supplier (SkyAI may retry after a partial failure)
        for po in _ns["po_details"]:
            h = po.get("ttPOheader", {})
            if h.get("cReference") == reference and h.get("cSupplierCode") == supplier_code:
                return jsonify({"status": "ok", "cPO": po["cPO"], "supplierCode": supplier_code,
                                "dTotalAmount": h.get("dTotalAmount", ""), "alreadyExisted": True})

    lines = []
    for i, ln in enumerate(lines_in, 1):
        code = str(ln.get("productCode") or "").strip()
        unit = _num(ln.get("unitCost")) or (_last_price(supplier_code, code) if code else 0.0)
        lines.append({"cUnique": str(i), "cProductcode": code or f"REQ-{i}",
                      "cProductDesc": str(ln.get("description") or ""), "dQuantity": ln.get("quantity") or 1,
                      "dUnitCost": f"{unit:.2f}"})
    sub = sum(_num(l["dQuantity"]) * _num(l["dUnitCost"]) for l in lines)
    gst = round(sub * 0.05 + 1e-9, 2) if supplier.get("cNoTPS") else 0.0
    pst = round(sub * 0.09975 + 1e-9, 2) if supplier.get("cNoTVQ") else 0.0
    today = datetime.now().strftime("%Y-%m-%d")
    buyer = str(p.get("buyerCode") or supplier.get("cCodeAch") or "")
    cpo = _next_po_number()
    view = _hooks["save_po"](cpo, {
        "cSupplierCode": supplier_code, "cSupplierName": supplier.get("cName", ""),
        "cBuyerCode": buyer, "cBuyerName": buyer, "cApplicantCode": str(p.get("requester") or ""),
        "dOrderDate": today, "dCreationDate": today, "dFreight": 0, "dGST": gst, "dPST": pst,
        "lines": lines, "lUnbilled": True,
    }, None)
    det = next(x for x in _ns["po_details"] if x["cPO"] == cpo)
    det["ttPOheader"].update({"dDueDate": str(p.get("requiredDate") or ""), "cReference": reference, "cSource": "SkyAI"})
    logger.info("apCreatePO.p: PO %s for %s (requisition %s)", cpo, supplier_code, reference)
    return jsonify({"status": "ok", "cPO": cpo, "supplierCode": supplier_code,
                    "dTotalAmount": view["dTotalAmount"], "alreadyExisted": False}), 201


# ---------------------------------------------------------------- settings screen

def _is_admin():
    if _api_key_ok():
        return True
    u = current_user()
    return u is not None and u["role"] == "admin"


@bp.route("/api/supplier-selection/settings", methods=["GET", "PUT"])
def selection_settings():
    if request.method == "GET":
        return jsonify({"settings": sel.get_settings(), "ai": sel.ai_status()})
    if not _is_admin():
        return jsonify({"error": "forbidden"}), 403
    p = _json()
    if p is None:
        return jsonify({"error": "invalid_body"}), 400
    return jsonify({"settings": sel.save_settings(p), "ai": sel.ai_status()})


@bp.route("/api/supplier-selection/test", methods=["POST"])
def selection_test():
    p = _json()
    if p is None or not isinstance(p.get("items"), list) or not p["items"]:
        return jsonify({"error": "required", "field": "items"}), 400
    settings = sel.clean_settings(p["settings"]) if isinstance(p.get("settings"), dict) else None
    return jsonify(sel.best_suppliers(_ns, p, settings))


def register_purchasing(app, ns, hooks):
    _ns.update(ns)
    _hooks.update(hooks)
    app.register_blueprint(bp)
