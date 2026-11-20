"""Work centers (P3): a group of machines, a line, a team or a subcontractor doing the same kind of work.

The resources (P4) belong to a work center; the operations of the recipes (P8) say on which work center they run.
What a work center gives the rest of Production:
- its calendar (P2) and whether its capacity is finite (the scheduler never loads it beyond the calendar);
- its efficiency and utilization: capacity = calendar minutes x utilization %, standard times / efficiency %;
- its hourly rates (setup, run, burden) for the estimated and actual cost of the orders;
- where its materials are staged and where its output goes (warehouse and locations);
- default queue and move times for the operations.
"""

from __future__ import annotations

from typing import Any

from powererp import schemas as S
from powererp.core.errors import AppError
from powererp.core.http import require
from powererp.core.values import number, text
from powererp.modules.common.crud import CrudService
from powererp.modules.common.forms import Row
from powererp.modules.common.registry import ReferenceRegistry
from powererp.store import Store


def _exists(finder, row: Row, field: str) -> Row | None:
    """An optional reference: empty is fine, otherwise it must exist (the stored code takes its spelling)."""
    v = text(row.get(field))
    if not v:
        return None
    found = finder(v)
    if found is None:
        raise AppError("unknown_ref", field)
    return found


class WorkCenterService(CrudService):
    kind = "work_center"

    def __init__(self, repo: Store, refs: dict[str, Any], references: ReferenceRegistry):
        """refs: finders of the other modules, given by the container: calendars, warehouses, locations
        (warehouse, code), suppliers, cost_centers (a function listing the cost center codes)."""
        super().__init__(repo, S.WORK_CENTER, S.DEFAULTS["work_centers"])
        self.refs = refs
        self.references = references
        references.register("calendar", self.uses_calendar)

    def uses_calendar(self, code: str) -> bool:
        return any(w["cCalendar"].upper() == code.upper() for w in self.repo.all(lines=False))

    def validate(self, row: Row, is_new: bool) -> None:
        require(row, "cDescFR")
        row["cCode"] = row["cCode"].upper()
        subcontract = row["cType"] == "subcontract"
        if not subcontract:
            require(row, "cCalendar")
        cal = _exists(self.refs["calendars"], row, "cCalendar")
        if cal is not None:
            row["cCalendar"] = cal["cCode"]
        for field, low, high in (("dEfficiencyPct", 1, 500), ("dUtilizationPct", 1, 100)):
            if not text(row[field]):
                row[field] = "100"
            if not low <= number(row[field]) <= high:
                raise AppError("out_of_range", field, detail=f"{low}-{high}")
        for field in ("dSetupRateHr", "dRunRateHr", "dBurdenRateHr"):
            if text(row[field]) and number(row[field]) < 0:
                raise AppError("negative", field)
        for field in ("iQueueMin", "iMoveMin"):
            if row[field] < 0:
                raise AppError("negative", field)
        if row["cCostCenter"] and row["cCostCenter"] not in self.refs["cost_centers"]():
            raise AppError("unknown_ref", "cCostCenter")
        wh = _exists(self.refs["warehouses"], row, "cWarehouse")
        if wh is not None:
            row["cWarehouse"] = wh["cCode"]
        for field in ("cInLocation", "cOutLocation"):
            if not row[field]:
                continue
            if wh is None:
                raise AppError("required", "cWarehouse")
            loc = self.refs["locations"](wh["cCode"], row[field])
            if loc is None:
                raise AppError("unknown_ref", field)
            row[field] = loc["cCode"]
        sup = _exists(self.refs["suppliers"], row, "cSupplier")
        if sup is not None:
            row["cSupplier"] = sup["cCode"]
        if subcontract:
            require(row, "cSupplier")
            row["lFinite"] = False  # a subcontractor's capacity is not ours to plan
        elif row["cSupplier"]:
            raise AppError("subcontract_only", "cSupplier")

    def before_delete(self, row: Row) -> None:
        self.references.check(self.kind, row["cCode"])  # resources and recipe operations (P4, P8)

    def capacity_minutes(self, row: Row, calendar_minutes: int) -> int:
        """Minutes the scheduler can load: the calendar time x the utilization."""
        return round(calendar_minutes * number(row["dUtilizationPct"] or 100) / 100)
