"""Steps of the recipe operations (P9): "the recipe step by step" the operator follows on the shop floor.

Each operation of a recipe has its steps, in order. A step is one of:
- instruction: read and confirm;
- material_add: add a material of the recipe (weigh it, scan its lot);
- parameter: set a process value (oven at 230 degrees);
- measure: measure and record a value (dough temperature 24 to 26 degrees);
- check: a yes / no checklist item (bowl clean);
- timer: wait or process for N minutes;
- output: declare the production (lot, serial number, label);
- signature: a second person confirms.
A step records at most one value (its parameter, with a code used by the conditions of the next steps), with a
target and limits. A critical step (critical control point) out of its limits blocks, warns or holds the lot.
Frequency: once, every N units, every N minutes, per lot. Condition: the step is done only when an earlier value
matches ("TEMP_PATE < 24" -> a correction step).

check_value() and condition_met() are what the shop floor screen (M4) will call.
"""

from __future__ import annotations

import re

from powererp.core.errors import AppError
from powererp.core.values import number, text
from powererp.modules.common.forms import Row

VALUED = ("parameter", "measure", "check")  # the kinds that record a value
CONDITION = re.compile(r"^\s*([A-Za-z_][\w]*)\s*(<=|>=|!=|=|<|>)\s*(.+?)\s*$")
PARAM = re.compile(r"^[A-Za-z_][\w]*$")


def parse_condition(cond: str) -> tuple[str, str, str] | None:
    """'TEMP_PATE < 24' -> ('TEMP_PATE', '<', '24'); None when empty; AppError when it cannot be read."""
    if not text(cond):
        return None
    m = CONDITION.match(cond)
    if not m:
        raise AppError("invalid_condition", "steps", detail=cond)
    return m.group(1).upper(), m.group(2), m.group(3).strip().strip("\"'")


def condition_met(cond: str, values: dict[str, object]) -> bool:
    """Is the condition true for the values recorded so far (param code -> value)? No condition = always."""
    parsed = parse_condition(cond)
    if parsed is None:
        return True
    param, op, expected = parsed
    if param not in values:
        return False
    got = values[param]
    try:
        a, b = float(str(got).replace(",", ".")), float(expected.replace(",", "."))
    except ValueError:
        a, b = str(got).strip().lower(), expected.lower()  # type: ignore[assignment]
        if op not in ("=", "!="):
            return False
    return {
        "<": lambda: a < b,
        "<=": lambda: a <= b,
        ">": lambda: a > b,
        ">=": lambda: a >= b,
        "=": lambda: a == b,
        "!=": lambda: a != b,
    }[op]()


def check_value(step: Row, value: object) -> Row:
    """A value recorded at a step against its limits: {ok, reason, action}; action is cOnFail when not ok and
    the step is critical, "warn" when not ok and not critical, "" when ok."""
    kind, dtype = step["cKind"], step["cDataType"]
    raw = text(value)
    if not raw:
        ok, reason = not step["lRequired"], "required"
    elif kind == "check" or dtype == "yes_no":
        ok, reason = raw.lower() in ("1", "true", "yes", "oui", "on", "ok"), "not_confirmed"
    elif dtype == "number":
        try:
            v = float(raw.replace(",", "."))
        except ValueError:
            return {"ok": False, "reason": "numeric", "action": "block"}
        low = text(step["dMin"]) and v < number(step["dMin"])
        high = text(step["dMax"]) and v > number(step["dMax"])
        ok, reason = not (low or high), "below_min" if low else "above_max"
    elif dtype == "list":
        options = [o.strip().lower() for o in text(step["cOptions"]).split(",") if o.strip()]
        ok, reason = raw.lower() in options, "not_in_list"
    else:
        ok, reason = True, ""
    if ok:
        return {"ok": True, "reason": "", "action": ""}
    return {"ok": False, "reason": reason, "action": step["cOnFail"] if step["lCritical"] else "warn"}


def validate_steps(recipe: Row) -> None:
    """Rules of the steps of a recipe (called by RecipeService.validate)."""
    ops = {op["iOpSeq"] for op in recipe.get("operations", [])}
    first_op = min(ops) if ops else 0
    materials = {m["iSeq"]: m for m in recipe.get("materials", [])}
    steps = recipe.get("steps", [])
    seen: set[tuple[int, int]] = set()
    for s in steps:
        if not s["iStep"]:
            s["iStep"] = 10 * (1 + sum(1 for x in steps if x is not s and x["iOpSeq"] == s["iOpSeq"] and x["iStep"]))
    steps.sort(key=lambda x: (x["iOpSeq"], x["iStep"]))
    params: dict[str, tuple[int, int]] = {}  # code -> (op, step) where it is recorded
    for s in steps:
        where = f"op {s['iOpSeq']} step {s['iStep']}"
        if s["iOpSeq"] not in ops:
            raise AppError("unknown_ref", "steps", detail=f"{where}: op {s['iOpSeq']}")
        key = (s["iOpSeq"], s["iStep"])
        if key in seen:
            raise AppError("duplicate", "steps", detail=where)
        seen.add(key)
        if not text(s["cTitleFR"]):
            raise AppError("required", "steps", detail=f"{where}: cTitleFR")
        _check_kind(s, where, materials, first_op)
        if s["cParam"]:
            s["cParam"] = s["cParam"].strip().upper()
            if not PARAM.match(s["cParam"]):
                raise AppError("invalid_param", "steps", detail=f"{where}: {s['cParam']}")
            if s["cParam"] in params:
                raise AppError("duplicate", "steps", detail=f"{where}: {s['cParam']}")
        cond = parse_condition(s["cCondition"])
        if cond is not None:
            if cond[0] not in params:  # only an earlier step's value can be tested
                raise AppError("invalid_condition", "steps", detail=f"{where}: {cond[0]}")
            s["cCondition"] = f"{cond[0]} {cond[1]} {cond[2]}"
        if s["cParam"]:
            params[s["cParam"]] = key
        if s["cFrequency"] in ("every_n_units", "every_n_min") and number(s["dFrequencyValue"]) <= 0:
            raise AppError("positive", "steps", detail=f"{where}: dFrequencyValue")
        if text(s["dDurationMin"]) and number(s["dDurationMin"]) < 0:
            raise AppError("negative", "steps", detail=f"{where}: dDurationMin")


def _check_kind(s: Row, where: str, materials: dict[int, Row], first_op: int) -> None:
    kind = s["cKind"]
    if kind in ("parameter", "measure"):
        if not s["cParam"]:
            raise AppError("required", "steps", detail=f"{where}: cParam")
        if s["cDataType"] == "number":
            lo, hi, tgt = (number(s[f]) if text(s[f]) else None for f in ("dMin", "dMax", "dTarget"))
            if lo is not None and hi is not None and hi < lo:
                raise AppError("max_below_min", "steps", detail=where)
            if tgt is not None and ((lo is not None and tgt < lo) or (hi is not None and tgt > hi)):
                raise AppError("target_out_of_limits", "steps", detail=where)
        if s["cDataType"] == "list" and not text(s["cOptions"]):
            raise AppError("required", "steps", detail=f"{where}: cOptions")
    elif kind == "check":
        s["cDataType"] = "yes_no"
    if kind not in VALUED:
        s["lCritical"] = False  # nothing to compare
    if kind == "material_add":
        mat = materials.get(s["iMaterialSeq"])
        if mat is None:
            raise AppError("unknown_ref", "steps", detail=f"{where}: material {s['iMaterialSeq']}")
        if (mat["iOpSeq"] or first_op) != s["iOpSeq"]:
            raise AppError("material_other_operation", "steps", detail=where)
    else:
        s["iMaterialSeq"] = 0
    if kind == "timer" and number(s["dDurationMin"]) <= 0:
        raise AppError("positive", "steps", detail=f"{where}: dDurationMin")
    if kind == "signature":
        s["lSecondSignature"] = True
