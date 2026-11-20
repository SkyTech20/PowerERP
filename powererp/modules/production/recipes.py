"""Recipes (P8): the full method to make a product, for a base quantity (Epicor method of manufacturing).

A recipe = product + revision, with:
- materials: what is consumed, for the base quantity, at which operation, how it is issued;
- outputs: the co-products and by-products made with the product (e.g. trimmings), with their share of the cost;
- operations: in which order, where (a work center, a resource or a capability; or subcontracted), how long.
  An operation starts from a standard operation (P5): its empty fields take the standard's values.
  Predecessors ("10, 20") allow operations in parallel; empty = the previous operation.
The steps of each operation ("the recipe step by step", P9) are in steps.py; the approval flow and versions
come in P10.

explode(): the recipe for a quantity: materials scaled (with scrap and yield), the time of each operation
(on its resource, with the speed and the efficiency), the estimated cost, and warnings when a product attribute
is outside the limits of the resource (width, weight...).
"""

from __future__ import annotations

import math
from typing import Any, cast

from powererp import schemas as S
from powererp.core.errors import AppError
from powererp.core.http import require
from powererp.core.values import number, text
from powererp.modules.common.crud import CrudService
from powererp.modules.common.forms import Row
from powererp.modules.common.registry import ReferenceRegistry
from powererp.store import Store

from .operations import run_minutes
from .steps import validate_steps

# fields an operation takes from its standard operation when they are left empty
FROM_STANDARD = (
    "cDescFR",
    "cDescEN",
    "dSetupMin",
    "dRunValue",
    "cInstructionFR",
    "cInstructionEN",
    "cSupplier",
    "dSubcontractCost",
)


def parse_predecessors(value: str) -> list[int]:
    """'10, 20' -> [10, 20]; AppError when it is not a list of numbers."""
    out = []
    for part in text(value).replace(";", ",").split(","):
        if part.strip():
            try:
                out.append(int(part.strip()))
            except ValueError:
                raise AppError("invalid_predecessors", "operations", detail=value) from None
    return out


def product_cost(prod: Row) -> float:
    """Unit cost used for the estimate: standard, else average, else last cost."""
    return number(prod.get("dStdCost")) or number(prod.get("dAvgCost")) or number(prod.get("dLastCost"))


class RecipeService(CrudService):
    keys = ("cProduct", "cRevision")
    readonly = ("cStatus",)
    children = {
        "materials": S.RECIPE_MATERIAL,
        "outputs": S.RECIPE_OUTPUT,
        "operations": S.RECIPE_OPERATION,
        "steps": S.RECIPE_STEP,
    }

    def __init__(self, repo: Store, refs: dict[str, Any], references: ReferenceRegistry):
        """refs: finders given by the container: products, product_mfg, operations, work_centers, resources,
        capabilities, suppliers; with_capability(code) lists the able resources, preferred first."""
        super().__init__(repo, S.RECIPE, S.DEFAULTS["recipes"])
        self.refs = refs
        self.references = references
        references.register("product", self._uses_product)
        references.register("operation", lambda code: self._uses_in("operations", "cOperation", code))
        references.register("work_center", lambda code: self._uses_in("operations", "cWorkCenter", code))
        references.register("resource", lambda code: self._uses_in("operations", "cResource", code))
        references.register("capability", lambda code: self._uses_in("operations", "cCapability", code))

    # ---------------------------------------------------------- references
    def _uses_in(self, key: str, field: str, code: str) -> bool:
        c = code.upper()
        return any(ln[field].upper() == c for r in self.repo.all() for ln in r.get(key, []))

    def _uses_product(self, code: str) -> bool:
        c = code.upper()
        for r in self.repo.all():
            if r["cProduct"].upper() == c:
                return True
            if any(m["cComponent"].upper() == c for m in r.get("materials", [])):
                return True
            if any(o["cProduct"].upper() == c for o in r.get("outputs", [])):
                return True
        return False

    def keep_child(self, key: str, line: Row) -> bool:
        if key == "steps":
            return bool(text(line["cTitleFR"]) or text(line["cInstructionFR"]))
        first = {"materials": "cComponent", "outputs": "cProduct", "operations": "iOpSeq"}[key]
        return bool(text(line[first])) and line[first] != 0

    # ---------------------------------------------------------- rules
    def validate(self, row: Row, is_new: bool) -> None:
        prod = self.refs["products"](row["cProduct"]) if text(row["cProduct"]) else None
        if prod is None:
            raise AppError("unknown_ref" if text(row["cProduct"]) else "required", "cProduct")
        row["cProduct"] = prod["cCode"]
        if not self.refs["product_mfg"](prod["cCode"]):
            raise AppError("not_made", "cProduct")  # Production > Manufactured items: make or both
        require(row, "cRevision")
        row["cRevision"] = row["cRevision"].strip().upper()
        if row.get("cStatus") in ("approved", "obsolete") and not is_new:
            raise AppError("recipe_locked", "cStatus")  # an approved version is frozen (P10: new version)
        row["cDescFR"] = row["cDescFR"] or prod.get("cDescFR", "")
        row["cDescEN"] = row["cDescEN"] or prod.get("cDescEN", "")
        row["cUOM"] = row["cUOM"] or prod.get("cStockUOM", "")
        if number(row["dBaseQty"]) <= 0:
            raise AppError("positive", "dBaseQty")
        lo, hi = number(row["dMinBatch"]), number(row["dMaxBatch"])
        if lo < 0 or hi < 0:
            raise AppError("negative", "dMinBatch" if lo < 0 else "dMaxBatch")
        if text(row["dMaxBatch"]) and hi and lo > hi:
            raise AppError("max_below_min", "dMaxBatch")
        if not text(row["dYieldPct"]):
            row["dYieldPct"] = "100"
        if not 1 <= number(row["dYieldPct"]) <= 100:
            raise AppError("out_of_range", "dYieldPct", detail="1-100")
        self._check_operations(row)
        self._check_materials(row)
        self._check_outputs(row)
        validate_steps(row)

    def _check_operations(self, row: Row) -> None:
        ops = row.get("operations", [])
        seqs = [op["iOpSeq"] for op in ops]
        for i, op in enumerate(ops, 1):
            where = f"op {op['iOpSeq']}"
            if op["iOpSeq"] <= 0:
                raise AppError("positive", "operations", detail=f"line {i}: iOpSeq")
            if seqs.count(op["iOpSeq"]) > 1:
                raise AppError("duplicate", "operations", detail=where)
            if op["cOperation"]:
                std = self.refs["operations"](op["cOperation"])
                if std is None:
                    raise AppError("unknown_ref", "operations", detail=f"{where}: {op['cOperation']}")
                op["cOperation"] = std["cCode"]
                self._copy_standard(op, std)
            self._check_where(op, where)
            for field in ("dSetupMin", "dRunValue", "dMinWaitMin", "dMaxWaitMin", "dSubcontractCost"):
                if text(op[field]) and number(op[field]) < 0:
                    raise AppError("negative", "operations", detail=f"{where}: {field}")
            for field in ("iCrew", "iQueueMin", "iMoveMin", "iSubcontractDays"):
                if op[field] < 0:
                    raise AppError("negative", "operations", detail=f"{where}: {field}")
            if (
                text(op["dMaxWaitMin"])
                and number(op["dMaxWaitMin"])
                and number(op["dMaxWaitMin"]) < number(op["dMinWaitMin"])
            ):
                raise AppError("max_below_min", "operations", detail=f"{where}: dMaxWaitMin")
            if not text(op["dYieldPct"]):
                op["dYieldPct"] = "100"
            if not 1 <= number(op["dYieldPct"]) <= 100:
                raise AppError("out_of_range", "operations", detail=f"{where}: dYieldPct")
            preds = parse_predecessors(op["cPredecessors"])
            for p in preds:
                if p not in seqs or p == op["iOpSeq"]:
                    raise AppError("invalid_predecessors", "operations", detail=f"{where}: {p}")
            op["cPredecessors"] = ", ".join(str(p) for p in preds)
        row["operations"] = sorted(ops, key=lambda o: o["iOpSeq"])
        self._check_cycles(row["operations"])

    @staticmethod
    def _copy_standard(op: Row, std: Row) -> None:
        if not text(op["dRunValue"]):
            op["cRunFormat"] = std["cRunFormat"]  # the time comes with its format
        for field in FROM_STANDARD:
            if not text(op[field]):
                op[field] = std[field]
        if not (op["cWorkCenter"] or op["cResource"] or op["cCapability"] or op["lSubcontract"]):
            op["cWorkCenter"], op["cCapability"] = std["cWorkCenter"], std["cCapability"]
            op["lSubcontract"] = std["lSubcontract"]
        if op["iCrew"] == 0:
            op["iCrew"] = std["iCrew"]
        if not op["iSubcontractDays"]:
            op["iSubcontractDays"] = std["iSubcontractDays"]

    def _check_where(self, op: Row, where: str) -> None:
        if op["lSubcontract"]:
            if not text(op["cSupplier"]):
                raise AppError("required", "operations", detail=f"{where}: cSupplier")
            sup = self.refs["suppliers"](op["cSupplier"])
            if sup is None:
                raise AppError("unknown_ref", "operations", detail=f"{where}: {op['cSupplier']}")
            op["cSupplier"] = sup["cCode"]
            op["cResource"] = op["cCapability"] = ""
            return
        op["cSupplier"], op["dSubcontractCost"], op["iSubcontractDays"] = "", "", 0
        if op["cResource"]:
            res = self.refs["resources"](op["cResource"])
            if res is None:
                raise AppError("unknown_ref", "operations", detail=f"{where}: {op['cResource']}")
            op["cResource"] = res["cCode"]
            op["cWorkCenter"] = res["cWorkCenter"]  # the resource says where
            op["cCapability"] = ""
        elif op["cCapability"]:
            cap = self.refs["capabilities"](op["cCapability"])
            if cap is None:
                raise AppError("unknown_ref", "operations", detail=f"{where}: {op['cCapability']}")
            op["cCapability"] = cap["cCode"]
            op["cWorkCenter"] = ""
        elif op["cWorkCenter"]:
            wc = self.refs["work_centers"](op["cWorkCenter"])
            if wc is None:
                raise AppError("unknown_ref", "operations", detail=f"{where}: {op['cWorkCenter']}")
            op["cWorkCenter"] = wc["cCode"]
        else:
            raise AppError("work_center_or_capability", "operations", detail=where)

    @staticmethod
    def _check_cycles(ops: list[Row]) -> None:
        preds = {}
        for i, op in enumerate(ops):
            given = parse_predecessors(op["cPredecessors"])
            preds[op["iOpSeq"]] = given if given else ([ops[i - 1]["iOpSeq"]] if i else [])
        state: dict[int, int] = {}  # 1 = visiting, 2 = done

        def visit(n: int) -> None:
            if state.get(n) == 1:
                raise AppError("predecessor_cycle", "operations", detail=f"op {n}")
            if state.get(n) == 2:
                return
            state[n] = 1
            for p in preds.get(n, []):
                visit(p)
            state[n] = 2

        for n in preds:
            visit(n)

    def _check_materials(self, row: Row) -> None:
        seqs = {op["iOpSeq"] for op in row.get("operations", [])}
        for i, m in enumerate(row.get("materials", []), 1):
            where = f"line {i}"
            comp = self.refs["products"](m["cComponent"])
            if comp is None:
                raise AppError("unknown_ref", "materials", detail=f"{where}: {m['cComponent']}")
            if comp["cCode"] == row["cProduct"]:
                raise AppError("component_is_product", "materials", detail=where)
            m["cComponent"] = comp["cCode"]
            m["cUOM"] = m["cUOM"] or comp.get("cStockUOM", "")
            if number(m["dQtyPer"]) <= 0:
                raise AppError("positive", "materials", detail=f"{where}: dQtyPer")
            if text(m["dScrapPct"]) and not 0 <= number(m["dScrapPct"]) < 100:
                raise AppError("out_of_range", "materials", detail=f"{where}: dScrapPct")
            if m["iOpSeq"] and m["iOpSeq"] not in seqs:
                raise AppError("unknown_ref", "materials", detail=f"{where}: op {m['iOpSeq']}")
            m["iSeq"] = m["iSeq"] or i * 10
        row["materials"] = sorted(row.get("materials", []), key=lambda x: x["iSeq"])

    def _check_outputs(self, row: Row) -> None:
        total = 0.0
        for i, o in enumerate(row.get("outputs", []), 1):
            prod = self.refs["products"](o["cProduct"])
            if prod is None:
                raise AppError("unknown_ref", "outputs", detail=f"line {i}: {o['cProduct']}")
            if prod["cCode"] == row["cProduct"]:
                raise AppError("component_is_product", "outputs", detail=f"line {i}")
            o["cProduct"] = prod["cCode"]
            o["cUOM"] = o["cUOM"] or prod.get("cStockUOM", "")
            if number(o["dQtyPer"]) <= 0:
                raise AppError("positive", "outputs", detail=f"line {i}: dQtyPer")
            total += number(o["dCostPct"])
        if total >= 100:
            raise AppError("cost_share_too_high", "outputs")

    def before_delete(self, row: Row) -> None:
        if row.get("cStatus") == "approved":
            raise AppError("recipe_locked", "cStatus", status=409)

    def view(self, row: Row, full: bool = True) -> Row:
        if full:
            return row
        return {
            **row,
            "iMaterials": len(row.get("materials", [])),
            "iOperations": len(row.get("operations", [])),
            "iSteps": len(row.get("steps", [])),
        }

    # ---------------------------------------------------------- explosion
    @staticmethod
    def _attribute_warnings(op_seq: int, res: Row | None, attrs: dict[str, Row]) -> list[Row]:
        """The product's numeric attributes outside the limits of the resource with the same name."""
        out: list[Row] = []
        for a in (res or {}).get("attributes", []):
            pa = attrs.get(a["cAttribute"].lower())
            if not pa or not text(pa["dNumber"]):
                continue
            v = number(pa["dNumber"])
            if (text(a["dMin"]) and v < number(a["dMin"])) or (text(a["dMax"]) and v > number(a["dMax"])):
                out.append(
                    {
                        "iOpSeq": op_seq,
                        "cResource": res["cCode"] if res else "",
                        "cAttribute": a["cAttribute"],
                        "dValue": v,
                        "dMin": a["dMin"],
                        "dMax": a["dMax"],
                    }
                )
        return out

    def explode(self, product: str, revision: str, qty: float) -> Row:
        """The recipe for `qty` of the product: materials, operations (time on their resource), cost, warnings."""
        r = self.get(product, revision)
        if qty <= 0:
            raise AppError("positive", "qty")
        base = number(r["dBaseQty"]) or 1
        yield_factor = (number(r["dYieldPct"]) or 100) / 100
        factor = qty / base / yield_factor  # what to start with for qty good units
        max_batch = number(r["dMaxBatch"])
        batches = math.ceil(qty / max_batch - 1e-9) if max_batch > 0 else 1
        warnings: list[Row] = []
        materials, mat_cost = [], 0.0
        for m in r.get("materials", []):
            comp = self.refs["products"](m["cComponent"]) or {}
            per = number(m["dQtyPer"])
            need = (per * batches if m["lFixedQty"] else per * factor) * (1 + number(m["dScrapPct"]) / 100)
            cost = need * product_cost(comp)
            mat_cost += cost
            materials.append(
                {
                    "iSeq": m["iSeq"],
                    "cComponent": m["cComponent"],
                    "cDescFR": comp.get("cDescFR", ""),
                    "cDescEN": comp.get("cDescEN", ""),
                    "cUOM": m["cUOM"],
                    "iOpSeq": m["iOpSeq"],
                    "dQty": round(need, 4),
                    "dUnitCost": product_cost(comp),
                    "dCost": round(cost, 2),
                }
            )
        attrs = {
            a["cAttribute"].lower(): a for a in (self.refs["product_mfg"](r["cProduct"]) or {}).get("attributes", [])
        }
        operations, op_cost, total_min = [], 0.0, 0.0
        for op in r.get("operations", []):
            res = self.refs["resources"](op["cResource"]) if op["cResource"] else None
            where = op["cResource"] or op["cWorkCenter"] or op["cSupplier"]
            if res is None and op["cCapability"]:
                # a capability: estimated on the preferred resource having it
                able = self.refs.get("with_capability", lambda _c: [])(op["cCapability"])
                res = able[0] if able else None
                where = f"{op['cCapability']} ({res['cCode']})" if res else op["cCapability"]
            wc_code = op["cWorkCenter"] or (res or {}).get("cWorkCenter", "")
            wc = self.refs["work_centers"](wc_code) if wc_code else None
            speed = number(res["dSpeedFactor"]) if res else 1.0
            eff = number((wc or {}).get("dEfficiencyPct")) or 100
            setup = number(op["dSetupMin"])
            run = (
                0.0
                if op["lSubcontract"]
                else run_minutes(op["cRunFormat"], number(op["dRunValue"]), qty, max_batch) / ((speed or 1) * eff / 100)
            )
            cost = 0.0
            if wc:
                # a labour work center costs per person: its rates x the crew (0 = unattended, e.g. proofing)
                people = op["iCrew"] if wc.get("cType") == "labor" else 1
                rates = setup / 60 * number(wc["dSetupRateHr"])
                rates += run / 60 * (number(wc["dRunRateHr"]) + number(wc["dBurdenRateHr"]))
                cost = rates * people
            if op["lSubcontract"]:
                cost += qty * number(op["dSubcontractCost"])
            op_cost += cost
            total_min += setup + run
            operations.append(
                {
                    "iOpSeq": op["iOpSeq"],
                    "cOperation": op["cOperation"],
                    "cDescFR": op["cDescFR"],
                    "cDescEN": op["cDescEN"],
                    "cWhere": where,
                    "dSetupMin": round(setup, 2),
                    "dRunMin": round(run, 2),
                    "dWaitMin": number(op["dMinWaitMin"]),
                    "dCost": round(cost, 2),
                }
            )
            warnings += self._attribute_warnings(op["iOpSeq"], res, attrs)
        total = mat_cost + op_cost
        outputs = [{**o, "dQty": round(number(o["dQtyPer"]) * qty / base, 4)} for o in r.get("outputs", [])]
        main_share = 1 - sum(number(o["dCostPct"]) for o in r.get("outputs", [])) / 100
        return {
            "cProduct": r["cProduct"],
            "cRevision": r["cRevision"],
            "dQty": qty,
            "cUOM": r["cUOM"],
            "iBatches": batches,
            "materials": materials,
            "operations": operations,
            "outputs": outputs,
            "dMaterialCost": round(mat_cost, 2),
            "dOperationCost": round(op_cost, 2),
            "dTotalCost": round(total, 2),
            "dUnitCost": round(total * main_share / qty, 4),
            "dTotalMin": round(total_min, 2),
            "warnings": warnings,
        }


def prepare_demo(recipes: list[Row], seed: dict[str, list[Row]]) -> list[Row]:
    """The demo recipes completed like an edit would (standard operation values, units, order), on memory
    copies of the demo lists: products, product_mfg, operations, work_centers, resources, capabilities."""
    from powererp.modules.common.memory import MemoryRepository

    def finder(key: str, keys: tuple[str, ...] = ("cCode",)):
        return MemoryRepository([dict(r) for r in seed.get(key, [])], keys=keys).get

    refs = {
        "products": finder("products"),
        "product_mfg": finder("product_mfg", ("cProduct",)),
        "operations": finder("operations"),
        "work_centers": finder("work_centers"),
        "resources": finder("resources"),
        "capabilities": finder("capabilities"),
        "suppliers": finder("suppliers"),
    }
    repo = cast(Store, MemoryRepository([], keys=("cProduct", "cRevision")))  # the same methods as a Store
    service = RecipeService(repo, refs, ReferenceRegistry())
    out = []
    for raw in recipes:
        row = service.create({k: v for k, v in raw.items() if k != "cStatus"})
        row["cStatus"] = raw.get("cStatus", "draft")
        out.append(row)
    return out
