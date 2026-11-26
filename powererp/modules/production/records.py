"""The records of the recipe steps on the shop floor (M4, step 6 of the SCOR / ISO plan: ISO 9001 8.5.1, HACCP and
ISO 22000 8.5.4 monitoring of the critical control points, SFCR preventive control records).

While an order is released or in progress, the operator follows the steps of its recipe (P9) and records each one:
a value for the steps that measure or set something (parameter, measure, check), "done" for the others. Each
record keeps who, when, the value, the limits of the step at that time, and whether it is within them.

A value out of the limits is a deviation: the corrective action (comment) is required. For a critical step, the
action of the step applies:
- block: the order cannot report production or be completed until the step is recorded again within its limits;
- hold_lot: the lot made (the lot of the record, else every lot the order made, and the lots it makes later) is put
  on hold (quality, lot status) until someone decides;
- warn: recorded and shown, nothing is stopped (a deviation of a step that is not critical is a warning too).

A step with a second signature (and a signature step) needs another user, with their password; a step with a
required role is signed by a user of that role (the second signer when there is one, else the operator; an
administrator may always). A step with a condition ("TEMP_PATE < 24") applies only when the last value of that
parameter matches. Frequency: once; per lot (one record within limits for each lot made); every N units (one per N
units made); every N minutes (as often as needed, at least once).
"""

from __future__ import annotations

import copy
import math
from collections.abc import Callable
from datetime import datetime
from typing import Any

from powererp.core.errors import AppError
from powererp.core.values import number, text

from .steps import VALUED, check_value, condition_met

Row = dict[str, Any]
Rows = list[Row]
FLOOR = ("released", "in_progress")
SIGNED = "signature"


def _key(r: Row) -> tuple[int, int]:
    return int(r["iOpSeq"]), int(r["iStep"])


class StepRecordService:
    def __init__(self, orders: Any, deps: dict[str, Callable[..., Any]]):
        """deps: operator() -> {username, role, is_admin}; signer(username, password) -> the same (AppError when the
        password is wrong); lots() -> the LotStatusService (quality), or None."""
        self.orders = orders
        self.deps = deps

    # ---------------------------------------------------------- the steps of an order
    def recipe_steps(self, order: Row) -> Rows:
        recipe = (
            self.orders.refs["recipes"].find(order["cProduct"], order["cRevision"]) if order.get("cRevision") else None
        )
        return sorted((recipe or {}).get("steps", []), key=_key)

    @staticmethod
    def _values(records: Rows) -> dict[str, object]:
        """The last value of each parameter (for the conditions of the next steps)."""
        out: dict[str, object] = {}
        for r in records:
            if r.get("cParam"):
                out[r["cParam"].upper()] = r["cValue"]
        return out

    @staticmethod
    def _needed(step: Row, order: Row) -> int:
        freq = step.get("cFrequency") or "once"
        if freq == "per_lot":
            return max(1, len({text(o.get("cLot")).upper() for o in order.get("outputs", []) if text(o.get("cLot"))}))
        if freq == "every_n_units" and number(step.get("dFrequencyValue")) > 0:
            return max(1, math.ceil(number(order.get("dQtyDone")) / number(step["dFrequencyValue"]) - 1e-9))
        return 1

    def board(self, order: Row) -> Row:
        """Every step of the recipe with its state: todo, done, deviation (the last record is out of its limits),
        skipped (its condition does not apply), and the records; the summary for the screen."""
        records = order.get("records", [])
        values = self._values(records)
        steps = []
        for s in self.recipe_steps(order):
            mine = [r for r in records if _key(r) == _key(s)]
            applies = condition_met(s.get("cCondition", ""), values)
            needed = self._needed(s, order)
            if s.get("cFrequency") == "per_lot":
                good = len({text(r.get("cLot")).upper() for r in mine if r["lOk"]})
            else:
                good = sum(1 for r in mine if r["lOk"])
            last = mine[-1] if mine else None
            if not applies and not mine:
                state = "skipped"
            elif last is not None and not last["lOk"]:
                state = "deviation"
            elif good >= needed:
                state = "done"
            else:
                state = "todo"
            steps.append(
                {
                    **{k: s.get(k) for k in s if k != "id"},
                    "cState": state,
                    "iNeeded": needed,
                    "iGood": good,
                    "lBlocking": state == "deviation" and bool(s.get("lCritical")) and s.get("cOnFail") == "block",
                    "records": mine,
                }
            )
        live = [s for s in steps if s["cState"] != "skipped"]
        return {
            "steps": steps,
            "iRequired": sum(1 for s in live if s.get("lRequired")),
            "iRequiredDone": sum(1 for s in live if s.get("lRequired") and s["cState"] == "done"),
            "iDeviations": sum(1 for r in records if not r["lOk"]),
            "blocking": [self._label(s) for s in steps if s["lBlocking"]],
        }

    @staticmethod
    def _label(s: Row) -> str:
        return f"{s['iOpSeq']}/{s['iStep']} {text(s.get('cTitleEN')) or text(s.get('cTitleFR'))}"

    def check_not_blocked(self, order: Row) -> None:
        """Refuse reporting or completing while a critical "block" step is out of its limits."""
        blocking = self.board(order)["blocking"]
        if blocking:
            raise AppError("step_blocked", status=409, detail=", ".join(blocking))

    # ---------------------------------------------------------- record
    def record(self, no: int, payload: Row) -> Row:
        """{iOpSeq, iStep, cValue, cComment, cLot, cSecondUser, cSecondPassword}: the step done."""
        order = copy.deepcopy(self.orders.get(no))
        if order["cStatus"] not in FLOOR:
            raise AppError("invalid_status", status=409, detail=order["cStatus"])
        key = (int(number(payload.get("iOpSeq"))), int(number(payload.get("iStep"))))
        step = next((s for s in self.recipe_steps(order) if _key(s) == key), None)
        if step is None:
            raise AppError("unknown_ref", "iStep", 404)
        records = order.setdefault("records", [])
        if not condition_met(step.get("cCondition", ""), self._values(records)):
            raise AppError("step_not_applicable", "iStep", detail=step["cCondition"])
        valued = step["cKind"] in VALUED
        value = text(payload.get("cValue"))
        if valued:
            if not value:
                raise AppError("required", "cValue")
            result = check_value(step, value)
            if result["reason"] == "numeric":
                raise AppError("numeric", "cValue")
        else:
            value, result = "done", {"ok": True, "reason": "", "action": ""}
        comment = text(payload.get("cComment"))
        if not result["ok"] and not comment:
            raise AppError("corrective_action", "cComment", detail=result["reason"])
        operator = self.deps["operator"]()
        second = ""
        if step.get("lSecondSignature") or step["cKind"] == SIGNED:
            signer = self.deps["signer"](text(payload.get("cSecondUser")), text(payload.get("cSecondPassword")))
            if signer["username"].lower() == operator["username"].lower():
                raise AppError("same_signer", "cSecondUser")
            second = signer["username"]
            who = signer
        else:
            who = operator
        role = text(step.get("cRequiredRole"))
        if role and not who.get("is_admin") and text(who.get("role")).upper() != role.upper():
            raise AppError("role_required", "cSecondUser" if second else "iStep", detail=role)
        lot = text(payload.get("cLot")) or (order.get("cLot") or "")
        rec = {
            "iSeq": max((int(r.get("iSeq") or 0) for r in records), default=0) + 1,
            "dAt": datetime.now().isoformat(timespec="seconds"),
            "cUser": operator["username"],
            "iOpSeq": key[0],
            "iStep": key[1],
            "cKind": step["cKind"],
            "cTitleFR": text(step.get("cTitleFR")),
            "cTitleEN": text(step.get("cTitleEN")),
            "cParam": text(step.get("cParam")),
            "cValue": value,
            "cUOM": text(step.get("cUOM")),
            "dMin": step.get("dMin") if valued else "",
            "dMax": step.get("dMax") if valued else "",
            "lOk": result["ok"],
            "cReason": result["reason"],
            "cAction": result["action"],
            "cComment": comment,
            "cSecondUser": second,
            "cLot": lot if step.get("cFrequency") == "per_lot" else "",
        }
        records.append(rec)
        if not result["ok"]:
            title = text(step.get("cTitleEN")) or text(step.get("cTitleFR"))
            order["history"] = order.get("history", []) + [
                {
                    "dAt": rec["dAt"],
                    "cUser": operator["username"],
                    "cAction": "deviation",
                    "cFrom": "",
                    "cTo": order["cStatus"],
                    "cComment": f"{key[0]}/{key[1]} {title}: {value} {rec['cUOM']} ({result['reason']}) — {comment}".strip(),
                }
            ]
            if result["action"] == "hold_lot":
                lots = [rec["cLot"]] if rec["cLot"] else [o["cLot"] for o in order.get("outputs", []) if o.get("cLot")]
                for lt in dict.fromkeys(lots):
                    self._hold(order, lt, rec)
        self.orders.repo.update(order, [order["iNo"]])
        return self.orders.view(order)

    # ---------------------------------------------------------- holding the lots
    def _hold(self, order: Row, lot: str, rec: Row) -> None:
        get = self.deps.get("lots")
        lots = get() if get else None
        if lots is None or not lot or lots.status_of(order["cProduct"], lot) != "released":
            return
        title = rec["cTitleEN"] or rec["cTitleFR"]
        reason = (
            f"Order {order['iNo']}, step {rec['iOpSeq']}/{rec['iStep']} {title}: {rec['cValue']} {rec['cUOM']}".strip()
        )
        lots.change(order["cProduct"], lot, "on_hold", reason[:300])

    def hold_new_lot(self, order: Row, lot: str) -> None:
        """A lot reported after a "hold the lot" deviation of the order (recorded before the lot existed) is held."""
        for rec in order.get("records", []):
            if (
                not rec["lOk"]
                and rec["cAction"] == "hold_lot"
                and (not rec["cLot"] or rec["cLot"].upper() == lot.upper())
            ):
                self._hold(order, lot, rec)
                return
