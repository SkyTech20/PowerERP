"""
PowerERP — purchasing services used by the SkyAI requisition ("Offer") workflow.

  POST <PW_PREFIX>/apCreatePO.p        one purchase order for one supplier (SkyAI calls it once
                                       per supplier after the approval). Calling it again for the
                                       same requisition and supplier returns the existing PO.

SkyAI chooses the supplier of each item itself, from its own purchase history: the ERP is not asked.

JSON in and out. Same protection as the other PowerWARE services (X-API-Key when ERP_API_KEY is set).
"""
import logging
from datetime import datetime

from flask import Blueprint, jsonify, request

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


def register_purchasing(app, ns, hooks):
    _ns.update(ns)
    _hooks.update(hooks)
    app.register_blueprint(bp)
