"""Replenishment: what to order (reorder point, min / max, order quantity) and the purchase orders that follow."""

from __future__ import annotations

import math
from typing import Any

from powererp.core.errors import AppError
from powererp.core.values import number, quantity, text, today, unit_cost

Row = dict[str, Any]
FIRST_PO = 500501
GST_RATE, QST_RATE = 0.05, 0.09975  # when the product has no purchase tax group: the supplier's TPS / TVQ numbers


def preferred_supplier(prod: Row) -> Row | None:
    lines = prod.get("lines") or []
    return next((ln for ln in lines if ln.get("lPreferred")), lines[0] if lines else None)


class ReplenishmentService:
    def __init__(self, stock, params_repo, suppliers, purchase_orders, tax_calculator, username, unit_factor=None):
        self.stock = stock  # StockService
        self.params_repo = params_repo
        self.suppliers = suppliers
        self.pos = purchase_orders
        self.taxes = tax_calculator
        self.username = username
        self.unit_factor = unit_factor  # the unit converter: stock units in one purchase unit (1 CS = 25 UN)

    def rows(self) -> list[Row]:
        """Available + on order at or below the trigger (reorder point, else minimum) -> suggested quantity up to the
        maximum (or the order quantity), rounded to the supplier minimum and to purchase units."""
        rows = []
        supplier_names = {s["cCode"]: s["cName"] for s in self.suppliers.list()}
        bal = self.stock.balances()
        params = self.params_repo.all()
        for par in params:
            if not par.get("lActive", True):
                continue
            prod = self.stock.products_repo.get(par["cProduct"]) if text(par["cProduct"]) else None
            if not prod or prod.get("cStatus") != "active" or not prod.get("lPurchasable", True):
                continue
            qty, res = self.stock.product_totals(prod["cCode"], par["cWarehouse"], bal)
            avail = qty - res
            # Open POs are not by warehouse: they count for the product's default warehouse (or its only one)
            params_of_prod = [x for x in params if x["cProduct"].upper() == prod["cCode"].upper()]
            home = prod.get("cDefaultWarehouse") or (
                params_of_prod[0]["cWarehouse"] if len(params_of_prod) == 1 else ""
            )
            ordered = self.pos.quantity_on_order(prod["cCode"]) if home.upper() == par["cWarehouse"].upper() else 0.0
            projected = avail + ordered
            rop, mn, mx, oq = (
                number(par.get(f)) if text(par.get(f)) else None
                for f in ("dReorderPoint", "dMinQty", "dMaxQty", "dOrderQty")
            )
            trigger = rop if rop is not None else mn
            if trigger is None or projected > trigger + 1e-9:
                continue
            if mx is not None and mx > projected:
                need = mx - projected
            elif oq:
                need = oq
            else:
                need = max((mn or 0) - projected, trigger - projected, 0) or 1
            if oq and need < oq:
                need = oq
            sup = preferred_supplier(prod)
            moq = number((sup or {}).get("dMinOrderQty"))
            if moq and need < moq:
                need = moq
            factor = self.purchase_factor(prod)
            purchase_qty = math.ceil(need / factor - 1e-9)
            # Price per purchase unit (e.g. a case): the supplier's, else the last / average cost x the factor
            price = (
                number((sup or {}).get("dPurchasePrice"))
                or (number(prod.get("dLastCost")) or number(prod.get("dAvgCost"))) * factor
            )
            rows.append(
                {
                    "cProduct": prod["cCode"],
                    "cDescFR": prod.get("cDescFR", ""),
                    "cDescEN": prod.get("cDescEN", ""),
                    "cWarehouse": par["cWarehouse"],
                    "dQtyAvailable": quantity(avail),
                    "dQtyOnOrder": quantity(ordered),
                    "dReorderPoint": par.get("dReorderPoint", ""),
                    "dMinQty": par.get("dMinQty", ""),
                    "dMaxQty": par.get("dMaxQty", ""),
                    "dSuggestedQty": quantity(purchase_qty * factor),
                    "cStockUOM": prod.get("cStockUOM", ""),
                    "dPurchaseQty": quantity(purchase_qty),
                    "cPurchaseUOM": prod.get("cPurchaseUOM", ""),
                    "dPurchaseFactor": quantity(factor),
                    "cSupplierCode": (sup or {}).get("cSupplierCode", ""),
                    "cSupplierName": supplier_names.get((sup or {}).get("cSupplierCode"), ""),
                    "cSupplierItem": (sup or {}).get("cSupplierItem", ""),
                    "dUnitCost": unit_cost(price),
                    "iLeadTimeDays": (sup or {}).get("iLeadTimeDays") or par.get("iLeadTimeDays") or 0,
                }
            )
        rows.sort(key=lambda r: (r["cSupplierCode"] or "~", r["cProduct"]))
        return rows

    def purchase_factor(self, prod: Row) -> float:
        """Stock units in one purchase unit of the product, from the unit conversions (1 when there is none)."""
        if self.unit_factor is None or not text(prod.get("cPurchaseUOM")):
            return 1.0
        return self.unit_factor(prod["cPurchaseUOM"], prod.get("cStockUOM", ""), prod) or 1.0

    def po_taxes(self, prod: Row, supplier: Row, amount_: float, on: str) -> tuple[float, float]:
        """TPS / TVQ of a PO line: the product's purchase tax group, else the supplier's TPS / TVQ numbers."""
        res = self.taxes.calc(prod.get("cPurchaseTaxGroup"), amount_, on) if prod.get("cPurchaseTaxGroup") else None
        if res is None:
            return (
                round(amount_ * GST_RATE + 1e-9, 2) if supplier.get("cNoTPS") else 0.0,
                round(amount_ * QST_RATE + 1e-9, 2) if supplier.get("cNoTVQ") else 0.0,
            )
        gst = sum(number(t["dTax"]) for t in res["taxes"] if t["cKind"] in ("gst", "hst"))
        pst = sum(number(t["dTax"]) for t in res["taxes"] if t["cKind"] not in ("gst", "hst"))
        return gst, pst

    def create_pos(self, p: Row) -> list[Row]:
        """One PO per supplier: {"lines": [{"cProduct", "dPurchaseQty", "cSupplierCode"?, "dUnitCost"?}]}.
        Quantities and prices come in purchase units; the PO lines are in stock units (like the receptions)."""
        lines = [ln for ln in (p.get("lines") or []) if isinstance(ln, dict) and number(ln.get("dPurchaseQty")) > 0]
        if not lines:
            raise AppError("required", "lines")
        groups: dict[str, tuple[Row, list]] = {}
        for i, ln in enumerate(lines, 1):
            prod = self.stock.products_repo.get(text(ln.get("cProduct"))) if text(ln.get("cProduct")) else None
            if prod is None:
                raise AppError("unknown_ref", "lines", detail=f"line {i}: {ln.get('cProduct')}")
            sup_line = preferred_supplier(prod) or {}
            code = text(ln.get("cSupplierCode")) or sup_line.get("cSupplierCode", "")
            supplier = self.suppliers.find(code)
            if supplier is None:
                raise AppError("no_supplier", "lines", detail=f"line {i}: {prod['cCode']}")
            item = next((x for x in prod.get("lines", []) if x["cSupplierCode"] == supplier["cCode"]), sup_line)
            factor = self.purchase_factor(prod)
            price = (
                number(ln.get("dUnitCost"))
                if text(ln.get("dUnitCost"))
                else (
                    number(item.get("dPurchasePrice"))
                    or (number(prod.get("dLastCost")) or number(prod.get("dAvgCost"))) * factor
                )
            )
            groups.setdefault(supplier["cCode"], (supplier, []))[1].append(
                (prod, number(ln["dPurchaseQty"]) * factor, price / factor, number(ln["dPurchaseQty"]))
            )
        on = today()
        created = []
        for code, (supplier, items) in groups.items():
            po_lines, gst, pst = [], 0.0, 0.0
            for n, (prod, qty, price, pqty) in enumerate(items, 1):
                desc = prod.get("cDescFR", "")
                if prod.get("cPurchaseUOM") and prod.get("cPurchaseUOM") != prod.get("cStockUOM"):
                    desc += f" ({quantity(pqty)} {prod['cPurchaseUOM']})"
                po_lines.append(
                    {
                        "cUnique": str(n),
                        "cProductcode": prod["cCode"],
                        "cProductDesc": desc,
                        "dQuantity": quantity(qty),
                        "dUnitCost": unit_cost(price),
                    }
                )
                g, s_ = self.po_taxes(prod, supplier, qty * price, on)
                gst, pst = gst + g, pst + s_
            cpo = self.pos.next_number(FIRST_PO)
            view = self.pos.save(
                cpo,
                {
                    "cSupplierCode": code,
                    "cSupplierName": supplier.get("cName", ""),
                    "cBuyerCode": supplier.get("cCodeAch", ""),
                    "cBuyerName": supplier.get("cDescAch", ""),
                    "cApplicantCode": self.username(),
                    "dOrderDate": on,
                    "dCreationDate": on,
                    "dFreight": 0,
                    "dGST": gst,
                    "dPST": pst,
                    "lines": po_lines,
                    "lUnbilled": True,
                },
            )
            self.pos.update_header(cpo, {"cReference": "REAPPRO " + text(p.get("cWarehouse")), "cSource": "ERP"})
            created.append(
                {
                    "cPO": cpo,
                    "cSupplierCode": code,
                    "cSupplierName": supplier.get("cName", ""),
                    "lineCount": len(po_lines),
                    "dTotalAmount": view["dTotalAmount"],
                }
            )
        return created
