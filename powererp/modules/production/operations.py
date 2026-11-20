"""Standard operations (P5): the catalog of operations the recipes reuse (Epicor OpMaster).

A recipe operation (P8) starts from a standard operation and copies its defaults: where it runs (a work center,
or a capability that any able resource has), the standard setup and run time, the crew, the instruction, and,
for a subcontracted operation, the supplier, cost and lead time.

The run time is given in one of three formats, the way people measure it on the floor:
- min_per_unit: 6.5 minutes per part (machining);
- units_per_hour: 1,200 units per hour (a packing line);
- min_per_lot: 25 minutes per batch, whatever the quantity (an oven, a mixer).
`minutes()` turns it into minutes for a quantity, on a resource with its speed factor (P4) and the work
center's efficiency (P3): the formula the recipes and the scheduler use.
"""

from __future__ import annotations

import math
from typing import Any

from powererp import schemas as S
from powererp.core.errors import AppError
from powererp.core.http import require
from powererp.core.values import number, text
from powererp.modules.common.crud import CrudService
from powererp.modules.common.forms import Row
from powererp.modules.common.registry import ReferenceRegistry
from powererp.store import Store


def run_minutes(run_format: str, run_value: float, qty: float, lot_size: float = 0) -> float:
    """Standard run minutes of `qty` units; min_per_lot counts the lots of `lot_size` (one lot when 0)."""
    if qty <= 0 or run_value <= 0:
        return 0.0
    if run_format == "min_per_unit":
        return qty * run_value
    if run_format == "units_per_hour":
        return qty / run_value * 60
    lots = math.ceil(qty / lot_size - 1e-9) if lot_size > 0 else 1
    return lots * run_value


class OperationService(CrudService):
    kind = "operation"

    def __init__(self, repo: Store, refs: dict[str, Any], references: ReferenceRegistry):
        """refs: finders given by the container: work_centers, capabilities, suppliers."""
        super().__init__(repo, S.OPERATION, S.DEFAULTS["operations"])
        self.refs = refs
        self.references = references
        references.register("work_center", lambda code: self._uses("cWorkCenter", code))
        references.register("capability", lambda code: self._uses("cCapability", code))

    def _uses(self, field: str, code: str) -> bool:
        return any(o[field].upper() == code.upper() for o in self.repo.all(lines=False))

    def validate(self, row: Row, is_new: bool) -> None:
        require(row, "cDescFR")
        row["cCode"] = row["cCode"].upper()
        wc = None
        if row["cWorkCenter"]:
            wc = self.refs["work_centers"](row["cWorkCenter"])
            if wc is None:
                raise AppError("unknown_ref", "cWorkCenter")
            row["cWorkCenter"] = wc["cCode"]
            if wc["cType"] == "subcontract":
                row["lSubcontract"] = True
        if row["cCapability"]:
            cap = self.refs["capabilities"](row["cCapability"])
            if cap is None:
                raise AppError("unknown_ref", "cCapability")
            row["cCapability"] = cap["cCode"]
        if row["lSubcontract"]:
            require(row, "cSupplier")
            sup = self.refs["suppliers"](row["cSupplier"])
            if sup is None:
                raise AppError("unknown_ref", "cSupplier")
            row["cSupplier"] = sup["cCode"]
            row["cCapability"] = ""  # the subcontractor does it: no resource of ours
        else:
            if not row["cWorkCenter"] and not row["cCapability"]:
                raise AppError("work_center_or_capability", "cWorkCenter")
            if row["cWorkCenter"] and row["cCapability"]:
                raise AppError("work_center_or_capability", "cCapability")
            row["cSupplier"] = ""
            row["dSubcontractCost"] = ""
            row["iSubcontractDays"] = 0
        for field in ("dSetupMin", "dRunValue", "dSubcontractCost"):
            if text(row[field]) and number(row[field]) < 0:
                raise AppError("negative", field)
        for field in ("iCrew", "iSubcontractDays"):
            if row[field] < 0:
                raise AppError("negative", field)
        if row["cRunFormat"] == "units_per_hour" and text(row["dRunValue"]) and number(row["dRunValue"]) == 0:
            raise AppError("positive", "dRunValue")

    def before_delete(self, row: Row) -> None:
        self.references.check(self.kind, row["cCode"])  # recipe operations (P8)

    def minutes(self, code: str, qty: float, lot_size: float = 0, speed: float = 1, efficiency: float = 100) -> Row:
        """Setup + run minutes of a quantity: the standard time / resource speed / work center efficiency."""
        op = self.get(code)
        if qty < 0:
            raise AppError("negative", "qty")
        factor = (speed or 1) * (efficiency or 100) / 100
        setup = number(op["dSetupMin"])
        run = run_minutes(op["cRunFormat"], number(op["dRunValue"]), qty, lot_size) / factor
        return {
            "cOperation": op["cCode"],
            "dQty": qty,
            "dSetupMin": round(setup, 2),
            "dRunMin": round(run, 2),
            "dTotalMin": round(setup + run, 2),
            "dLaborMin": round((setup + run) * max(op["iCrew"], 0), 2),
        }
