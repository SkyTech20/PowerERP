"""apCreatePO.p: the purchase orders of SkyAI requisitions ("Offer" workflow).

SkyAI chooses the supplier of each item itself (from its own purchase history) and calls apCreatePO.p once per
supplier after the approval. Calling it again for the same requisition and supplier returns the existing PO.
JSON in and out; same protection as the other PowerWARE services (X-API-Key when ERP_API_KEY is set).
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from flask import Blueprint, jsonify, request

from powererp.core.values import number

logger = logging.getLogger(__name__)

FIRST_PO = 500501
GST_RATE, QST_RATE = 0.05, 0.09975  # Québec: TPS / TVQ charged when the supplier has the registration number


class RequisitionError(Exception):
    pass


class RequisitionService:
    def __init__(self, suppliers, purchase_orders):
        self.suppliers = suppliers
        self.pos = purchase_orders

    def create_po(self, p: dict[str, Any]) -> tuple[dict, bool]:
        """(response, created) for a requisition payload; RequisitionError for a bad request."""
        supplier_code = str(p.get("supplierCode") or "").strip()
        reference = str(p.get("requisitionNumber") or "").strip()
        supplier = self.suppliers.repo.get(supplier_code, ci=False) if supplier_code else None
        if supplier is None:
            raise RequisitionError(f"unknown supplier {supplier_code}")
        lines_in = [ln for ln in (p.get("lines") or []) if isinstance(ln, dict)]
        if not lines_in:
            raise RequisitionError("lines required")

        if reference:  # idempotent per requisition + supplier (SkyAI may retry after a partial failure)
            po = self.pos.find_by_reference(reference, supplier_code)
            if po is not None:
                return {
                    "status": "ok",
                    "cPO": po["cPO"],
                    "supplierCode": supplier_code,
                    "dTotalAmount": po.get("ttPOheader", {}).get("dTotalAmount", ""),
                    "alreadyExisted": True,
                }, False

        lines = []
        for i, ln in enumerate(lines_in, 1):
            code = str(ln.get("productCode") or "").strip()
            unit = number(ln.get("unitCost")) or (self.pos.last_price(supplier_code, code) if code else 0.0)
            lines.append(
                {
                    "cUnique": str(i),
                    "cProductcode": code or f"REQ-{i}",
                    "cProductDesc": str(ln.get("description") or ""),
                    "dQuantity": ln.get("quantity") or 1,
                    "dUnitCost": f"{unit:.2f}",
                }
            )
        sub = sum(number(ln["dQuantity"]) * number(ln["dUnitCost"]) for ln in lines)
        gst = round(sub * GST_RATE + 1e-9, 2) if supplier.get("cNoTPS") else 0.0
        pst = round(sub * QST_RATE + 1e-9, 2) if supplier.get("cNoTVQ") else 0.0
        today = datetime.now().strftime("%Y-%m-%d")
        buyer = str(p.get("buyerCode") or supplier.get("cCodeAch") or "")
        cpo = self.pos.next_number(FIRST_PO)
        view = self.pos.save(
            cpo,
            {
                "cSupplierCode": supplier_code,
                "cSupplierName": supplier.get("cName", ""),
                "cBuyerCode": buyer,
                "cBuyerName": buyer,
                "cApplicantCode": str(p.get("requester") or ""),
                "dOrderDate": today,
                "dCreationDate": today,
                "dFreight": 0,
                "dGST": gst,
                "dPST": pst,
                "lines": lines,
                "lUnbilled": True,
            },
        )
        self.pos.update_header(
            cpo, {"dDueDate": str(p.get("requiredDate") or ""), "cReference": reference, "cSource": "SkyAI"}
        )
        logger.info("apCreatePO.p: PO %s for %s (requisition %s)", cpo, supplier_code, reference)
        return {
            "status": "ok",
            "cPO": cpo,
            "supplierCode": supplier_code,
            "dTotalAmount": view["dTotalAmount"],
            "alreadyExisted": False,
        }, True


def create_po_route(bp: Blueprint, prefix: str, service: RequisitionService) -> None:
    @bp.route(prefix + "/apCreatePO.p", methods=["POST"])
    def ap_create_po():
        p = request.get_json(silent=True)
        if not isinstance(p, dict):
            return jsonify({"status": "error", "error": "JSON body required"}), 400
        try:
            body, created = service.create_po(p)
        except RequisitionError as e:
            return jsonify({"status": "error", "error": str(e)}), 400
        return jsonify(body), (201 if created else 200)
