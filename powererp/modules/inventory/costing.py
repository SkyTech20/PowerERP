"""How stock is valued (Strategy): the unit cost of a product and what a receipt does to it.

Every product keeps a moving average cost (dAvgCost), updated by each receipt, and the cost of its last purchase
(dLastCost). Its cost method (cCostMethod) chooses which cost values the stock:
    avg   the moving average
    std   the standard cost (dStdCost) when there is one, else the moving average
A new method (e.g. FIFO) is a new class registered in COSTING, without touching the stock service.
"""

from __future__ import annotations

from typing import Any

from powererp.core.values import number, text, unit_cost

Row = dict[str, Any]


class Costing:
    def unit_cost(self, product: Row) -> float:
        return number(product.get("dAvgCost"))

    def receipt_cost(self, product: Row, movement: Row) -> float:
        """Cost of a receipt: the one given, else the average, last or standard cost of the product."""
        if text(movement.get("dUnitCost")):
            return number(movement["dUnitCost"])
        return number(product.get("dAvgCost")) or number(product.get("dLastCost")) or number(product.get("dStdCost"))

    def receive(self, product: Row, qty_before: float, qty: float, cost: float, is_purchase: bool) -> None:
        """Moving average after `qty` received at `cost` when `qty_before` was in stock (updates the product)."""
        avg = number(product.get("dAvgCost"))
        new_qty = qty_before + qty
        new_avg = cost if qty_before <= 0 or new_qty <= 0 else (qty_before * avg + qty * cost) / new_qty
        product["dAvgCost"] = unit_cost(new_avg)
        if is_purchase:
            product["dLastCost"] = unit_cost(cost)


class AverageCosting(Costing):
    pass


class StandardCosting(Costing):
    def unit_cost(self, product: Row) -> float:
        if text(product.get("dStdCost")):
            return number(product["dStdCost"])
        return super().unit_cost(product)


COSTING: dict[str, Costing] = {"avg": AverageCosting(), "std": StandardCosting()}


def costing_of(product: Row) -> Costing:
    return COSTING.get(product.get("cCostMethod") or "avg", COSTING["avg"])
