"""Production orders (M3a): what to make, how much, where and when, from an approved recipe.

An order is created as a draft: product, quantity (in the unit of the recipe), warehouse, start and due dates. Its
recipe is the version given (cRevision), else the one new orders use on the start date (the default approved
recipe valid that day, RecipeFlow.current). The materials (in stock units), the operations (time on their resource)
and the estimated cost are the recipe exploded for the quantity (RecipeService.explode), and are calculated again
on every change while the order is a draft.

Life of an order:
    draft --release--> released --(first issue or report, floor.py)--> in_progress --complete--> completed --close--> closed
    draft / released --cancel--> cancelled     released --unrelease--> draft     completed --reopen--> in_progress
Only a draft is changed or deleted. Releasing checks the recipe again (still approved) and freezes the order; the
availability of each material in the warehouse is shown on the order (shortages warn, they do not block). Once the
stock has moved for the order it can no longer go back to draft or be cancelled. Completing needs a quantity made.
Every change of status is written to the order's history (who, when, comment).

The stock moves on the shop floor (M3b, floor.py): the materials issued and the product made are stock movements
(document PROD, the order number). The actual cost (materials issued + the estimated operations for the quantity
made) is shown against the estimate, and kept on the order when it is closed.
"""

from __future__ import annotations

import copy
from collections.abc import Callable
from datetime import date, datetime
from typing import Any

from powererp import schemas as S
from powererp.core.errors import AppError, NotFound
from powererp.core.values import amount, number, quantity, text, unit_cost
from powererp.modules.common.forms import RecordForm
from powererp.modules.common.registry import ReferenceRegistry

Row = dict[str, Any]
SEQUENCE = "PROD_ORDER"
EPS = 1e-9

# action -> (statuses it starts from, status it leads to)
MOVES = {
    "release": (("draft",), "released"),
    "unrelease": (("released",), "draft"),
    "cancel": (("draft", "released"), "cancelled"),
    "complete": (("in_progress",), "completed"),
    "reopen": (("completed",), "in_progress"),
    "close": (("completed",), "closed"),
}
UNMOVED = ("release", "unrelease", "cancel")  # only while the stock has not moved for the order


def actuals(order: Row) -> Row:
    """The actual cost of an order so far: the materials issued (net of returns) and the estimated operation cost
    for the quantity made; the variance against the estimated unit cost x the quantity made."""
    done = number(order.get("dQtyDone"))
    qty = number(order.get("dQty"))
    material = sum(number(i["dValue"]) for i in order.get("issues", []))
    operation = number(order.get("dEstOperationCost")) * done / qty if qty > EPS else 0.0
    total = material + operation
    return {
        "dActMaterialCost": amount(material),
        "dActOperationCost": amount(operation),
        "dActCost": amount(total),
        "dActUnitCost": unit_cost(total / done) if done > EPS else "",
        "dVariance": amount(total - number(order.get("dEstUnitCost")) * done) if done > EPS else "",
    }


class ProductionOrderService:
    def __init__(
        self,
        repo: Any,
        refs: dict[str, Any],
        numbering: Any,
        username: Callable[[], str],
        references: ReferenceRegistry,
    ):
        """refs: products (find), product_mfg (find), warehouses (find), recipes (RecipeService),
        current_recipe (RecipeFlow.current), stock (StockService, for the availability)."""
        self.repo = repo
        self.refs = refs
        self.numbering = numbering
        self.username = username
        self.form = RecordForm(S.PRODUCTION_ORDER)
        references.register("product", self._uses_product)
        references.register("warehouse", lambda code: self._uses("cWarehouse", code))

    # ---------------------------------------------------------- references
    def _uses(self, field: str, code: str) -> bool:
        return any(text(r.get(field)).upper() == code.upper() for r in self.repo.all(lines=False))

    def _uses_product(self, code: str) -> bool:
        cu = code.upper()
        return any(
            r["cProduct"].upper() == cu or any(m["cComponent"].upper() == cu for m in r.get("materials", []))
            for r in self.repo.all()
        )

    # ---------------------------------------------------------- read
    def list(self) -> list[Row]:
        return self.repo.all()

    def get(self, no: int) -> Row:
        order = self.repo.get(no)
        if order is None:
            raise NotFound()
        return order

    @staticmethod
    def summary(order: Row) -> Row:
        out = {k: v for k, v in order.items() if k not in ("materials", "operations", "history", "issues", "outputs")}
        out["iMaterials"] = len(order.get("materials", []))
        out["iOperations"] = len(order.get("operations", []))
        return out

    def view(self, order: Row) -> Row:
        """The order with the stock available for each material in its warehouse (dAvailable, dShort)."""
        out = copy.deepcopy(order)
        if out["cStatus"] in ("draft", "released", "in_progress"):
            avail = self._available()
            for m in out.get("materials", []):
                wh = (m["cWarehouse"] or out["cWarehouse"]).upper()
                have = avail.get((m["cComponent"].upper(), wh), 0.0)
                left = max(number(m["dQtyRequired"]) - number(m["dQtyIssued"]), 0.0)
                m["dAvailable"] = quantity(have)
                m["dShort"] = quantity(max(left - have, 0.0))
        out["lShort"] = any(number(m.get("dShort")) > EPS for m in out.get("materials", []))
        if out["cStatus"] != "closed":
            out.update(actuals(out))
        return out

    def _available(self) -> dict[tuple[str, str], float]:
        """Available stock (on hand - reserved) by product and warehouse; expired lots do not count."""
        today = date.today().isoformat()
        out: dict[tuple[str, str], float] = {}
        for (p, w, *_rest), b in self.refs["stock"]().balances().items():
            if b.get("dExpiry") and str(b["dExpiry"])[:10] < today:
                continue
            out[(p, w)] = out.get((p, w), 0.0) + b["qty"] - b["reserved"]
        return out

    # ---------------------------------------------------------- calculation
    def blank(self) -> Row:
        order = self.form.blank()
        order.update(
            {
                "iNo": 0,
                "cStatus": "draft",
                "cDescFR": "",
                "cDescEN": "",
                "cUOM": "",
                "dQtyDone": "0",
                "cLot": "",
                "dEstMaterialCost": "0.00",
                "dEstOperationCost": "0.00",
                "dEstCost": "0.00",
                "dEstUnitCost": "",
                "dTotalMin": "0",
                "cUser": "",
                "dCreated": "",
                "dReleased": "",
                "cReleasedBy": "",
                "materials": [],
                "operations": [],
                "history": [],
                "issues": [],
                "outputs": [],
                "dCompleted": "",
                "cCompletedBy": "",
                "dClosed": "",
                "cClosedBy": "",
                "dActMaterialCost": "",
                "dActOperationCost": "",
                "dActCost": "",
                "dActUnitCost": "",
                "dVariance": "",
            }
        )
        return order

    def calc(self, order: Row, base_qty: bool = False) -> Row:
        """Check the header and fill the recipe, materials, operations and costs (see the module's docstring).
        base_qty: an empty quantity takes the base quantity of the recipe (the screen, as soon as a product is picked).
        """
        code = text(order["cProduct"])
        prod = self.refs["products"](code) if code else None
        if prod is None:
            raise AppError("required" if not code else "unknown_ref", "cProduct")
        order["cProduct"] = prod["cCode"]
        order["cDescFR"], order["cDescEN"] = text(prod.get("cDescFR")), text(prod.get("cDescEN"))
        mfg = self.refs["product_mfg"](prod["cCode"]) or {}
        if mfg.get("cMakeBuy", "make") == "buy":
            raise AppError("not_made", "cProduct")
        if not order["dStart"]:
            order["dStart"] = date.today().isoformat()
        if order["dDue"] and order["dDue"] < order["dStart"]:
            raise AppError("end_before_start", "dDue")
        recipe = self._recipe(order)
        if base_qty and not text(order["dQty"]):
            order["dQty"] = text(recipe.get("dBaseQty")) or "1"
        qty = number(order["dQty"])
        if qty <= 0:
            raise AppError("positive" if text(order["dQty"]) else "required", "dQty")
        order["dQty"] = quantity(qty)
        wh_code = text(order["cWarehouse"]) or text(prod.get("cDefaultWarehouse"))
        wh = self.refs["warehouses"](wh_code) if wh_code else None
        if wh is None:
            raise AppError("required" if not wh_code else "unknown_ref", "cWarehouse")
        order["cWarehouse"] = wh["cCode"]
        e = self.refs["recipes"].explode(recipe["cProduct"], recipe["cRevision"], qty)
        mats = {m["iSeq"]: m for m in recipe.get("materials", [])}
        issued = {m["iSeq"]: m["dQtyIssued"] for m in order.get("materials", [])}
        order["materials"] = [
            {
                "iSeq": m["iSeq"],
                "cComponent": m["cComponent"],
                "cDescFR": m["cDescFR"],
                "cDescEN": m["cDescEN"],
                "iOpSeq": m["iOpSeq"],
                "cIssueMethod": text(mats.get(m["iSeq"], {}).get("cIssueMethod")) or "manual",
                "cWarehouse": text(mats.get(m["iSeq"], {}).get("cWarehouse")),
                "dQtyRequired": quantity(m["dStockQty"]),
                "cUOM": m["cStockUOM"] or m["cUOM"],
                "dQtyIssued": issued.get(m["iSeq"]) or "0",
                "dUnitCost": unit_cost(m["dStockUnitCost"]),
                "dCost": amount(m["dCost"]),
            }
            for m in e["materials"]
        ]
        order["operations"] = [
            {
                "iOpSeq": op["iOpSeq"],
                "cOperation": op["cOperation"],
                "cDescFR": op["cDescFR"],
                "cDescEN": op["cDescEN"],
                "cWhere": op["cWhere"],
                "dSetupMin": quantity(op["dSetupMin"]),
                "dRunMin": quantity(op["dRunMin"]),
                "dWaitMin": quantity(op["dWaitMin"]),
                "dCost": amount(op["dCost"]),
            }
            for op in e["operations"]
        ]
        order["cUOM"] = e["cUOM"]
        order["dEstMaterialCost"] = amount(e["dMaterialCost"])
        order["dEstOperationCost"] = amount(e["dOperationCost"])
        order["dEstCost"] = amount(e["dTotalCost"])
        order["dEstUnitCost"] = unit_cost(e["dUnitCost"])
        order["dTotalMin"] = quantity(e["dTotalMin"])
        return order

    def _recipe(self, order: Row) -> Row:
        """The recipe of the order: the revision given (approved), else the current one on the start date."""
        rev = text(order["cRevision"]).upper()
        if rev:
            recipe = self.refs["recipes"].repo.get(order["cProduct"], rev)
            if recipe is None:
                raise AppError("unknown_ref", "cRevision")
            if recipe["cStatus"] != "approved":
                raise AppError("no_approved_recipe", "cRevision", detail=f"{recipe['cRevision']}: {recipe['cStatus']}")
        else:
            recipe = self.refs["current_recipe"](order["cProduct"], date.fromisoformat(order["dStart"]))
            if recipe is None:
                raise AppError("no_approved_recipe", "cProduct")
        order["cRevision"] = recipe["cRevision"]
        return recipe

    def preview(self, payload: Row, no: int | None = None) -> Row:
        """The draft calculated from a payload, without saving it (the screen shows materials and operations)."""
        order = copy.deepcopy(self.draft(no)) if no else self.blank()
        self.form.apply(order, payload)
        if not text(order["cProduct"]):
            return self.view(order)
        return self.view(self.calc(order, base_qty=True))

    # ---------------------------------------------------------- write
    def draft(self, no: int) -> Row:
        order = self.get(no)
        if order["cStatus"] != "draft":
            raise AppError("invalid_status", status=409, detail=order["cStatus"])
        return order

    def create(self, payload: Row) -> Row:
        order = self.calc(self.form.apply(self.blank(), payload))
        order["iNo"] = self.numbering.next(SEQUENCE)
        order["cUser"] = self.username()
        order["dCreated"] = self._now()
        order["history"] = [self._event("created", "", "draft", "")]
        self.repo.insert(order)
        return self.view(order)

    def update(self, no: int, payload: Row) -> Row:
        current = self.draft(no)
        order = self.calc(self.form.apply(copy.deepcopy(current), payload, skip=("iNo",)))
        self.repo.update(order, [current["iNo"]])
        return self.view(order)

    def delete(self, no: int) -> None:
        self.repo.delete(self.draft(no))

    def move(self, no: int, action: str, comment: str = "") -> Row:
        """release / unrelease / cancel / complete / reopen / close (see the module's docstring)."""
        if action not in MOVES:
            raise AppError("not_found", status=404)
        order = copy.deepcopy(self.get(no))
        sources, target = MOVES[action]
        if order["cStatus"] not in sources:
            raise AppError("invalid_status", status=409, detail=f"{order['cStatus']} -> {target}")
        moved = bool(order.get("issues") or order.get("outputs")) or number(order["dQtyDone"]) > EPS
        if action in UNMOVED and (moved or any(number(m["dQtyIssued"]) > EPS for m in order.get("materials", []))):
            raise AppError("invalid_status", status=409, detail="stock already moved")
        if action == "complete" and number(order["dQtyDone"]) <= EPS:
            raise AppError("nothing_made", status=409)
        if action == "release":
            self.calc(order)  # the recipe is checked again (still approved) and the quantities recalculated
            order["dReleased"] = self._now()
            order["cReleasedBy"] = self.username()
        elif action == "unrelease":
            order["dReleased"] = ""
            order["cReleasedBy"] = ""
        elif action == "complete":
            order["dCompleted"], order["cCompletedBy"] = self._now(), self.username()
        elif action == "reopen":
            order["dCompleted"], order["cCompletedBy"] = "", ""
        elif action == "close":
            order.update(actuals(order))  # the actual cost is kept as it is on closing
            order["dClosed"], order["cClosedBy"] = self._now(), self.username()
        order["history"] = order.get("history", []) + [self._event(action, order["cStatus"], target, comment)]
        order["cStatus"] = target
        self.repo.update(order, [order["iNo"]])
        return self.view(order)

    # ---------------------------------------------------------- helpers
    def _event(self, action: str, src: str, dst: str, comment: str) -> Row:
        return {
            "dAt": self._now(),
            "cUser": self.username(),
            "cAction": action,
            "cFrom": src,
            "cTo": dst,
            "cComment": text(comment),
        }

    @staticmethod
    def _now() -> str:
        return datetime.now().isoformat(timespec="seconds")
