"""Nonconformances (step 5 of the SCOR / ISO plan: ISO 9001 8.7 control of nonconforming outputs, 10.2
nonconformity and corrective action; ISO 22000 8.9).

A nonconformance records what was found wrong: where (reception, production, customer, internal), the document it
comes from, the product, the lot and the quantity, how serious it is and what is wrong. With "Hold the lot" the lot
is put on hold when the nonconformance is saved (if it is released), so that it is no longer sold or used.

It is closed when the decision is taken: the disposition (what is done with the product) and the corrective action
(what is done so that it does not happen again) are required. Closing changes the lot it held:
    use as is -> released        scrap, return to the supplier -> rejected        rework -> stays on hold
(a lot put on hold by something else keeps its status when the disposition is "use as is"). A closed
nonconformance is read only; it is kept (never deleted), with its history (who, when, what).
"""

from __future__ import annotations

import copy
from collections.abc import Callable
from datetime import date, datetime
from typing import Any

from powererp import schemas as S
from powererp.core.errors import AppError, NotFound
from powererp.core.values import text
from powererp.modules.common.forms import RecordForm

from .lots import RELEASED, LotStatusService

Row = dict[str, Any]
SEQUENCE = "NONCONFORMANCE"
LOT_AFTER = {"use_as_is": RELEASED, "scrap": "rejected", "return_supplier": "rejected"}


class NonconformanceService:
    def __init__(
        self,
        repo: Any,
        lots: LotStatusService,
        refs: dict[str, Callable[..., Any]],
        numbering: Any,
        username: Callable[[], str],
    ):
        """refs: products (find)."""
        self.repo = repo
        self.lots = lots
        self.refs = refs
        self.numbering = numbering
        self.username = username
        self.form = RecordForm(S.NONCONFORMANCE)

    # ---------------------------------------------------------- read
    def list(self) -> list[Row]:
        return self.repo.all(lines=False)

    def get(self, no: int) -> Row:
        row = self.repo.get(no)
        if row is None:
            raise NotFound()
        return row

    def view(self, row: Row) -> Row:
        out = copy.deepcopy(row)
        prod = (self.refs["products"](row["cProduct"]) if row.get("cProduct") else None) or {}
        out["cDescFR"], out["cDescEN"] = text(prod.get("cDescFR")), text(prod.get("cDescEN"))
        out["cLotStatus"] = self.lots.status_of(row["cProduct"], row["cLot"]) if row.get("cLot") else ""
        return out

    def summary(self, row: Row) -> Row:
        return self.view({k: v for k, v in row.items() if k != "history"})

    def blank(self) -> Row:
        row = self.form.blank()
        row.update({"iNo": 0, "cStatus": "open", "dDate": date.today().isoformat(), "lHoldLot": True})
        return row

    # ---------------------------------------------------------- checks
    def _check(self, row: Row) -> None:
        if not row.get("dDate"):
            raise AppError("required", "dDate")
        if not text(row.get("cDescription")):
            raise AppError("required", "cDescription")
        if row.get("cProduct"):
            prod = self.refs["products"](row["cProduct"])
            if prod is None:
                raise AppError("unknown_ref", "cProduct")
            row["cProduct"] = prod["cCode"]
            row["cUOM"] = row.get("cUOM") or text(prod.get("cStockUOM"))
        elif row.get("cLot"):
            raise AppError("required", "cProduct")
        if row.get("cLot"):
            known = {c["code"].upper(): c["code"] for c in self.lots.lot_choices(row["cProduct"])}
            if row["cLot"].upper() not in known:
                raise AppError("unknown_lot", "cLot")
            row["cLot"] = known[row["cLot"].upper()]
        if row.get("dQty") not in ("", None) and float(row["dQty"]) < 0:
            raise AppError("negative", "dQty")

    def _event(self, action: str, comment: str = "") -> Row:
        return {"dAt": self._now(), "cUser": self.username(), "cAction": action, "cComment": comment}

    @staticmethod
    def _now() -> str:
        return datetime.now().isoformat(timespec="seconds")

    def _hold(self, row: Row) -> None:
        """Put the lot on hold (when asked and the lot is released)."""
        if row.get("lHoldLot") and row.get("cLot") and self.lots.status_of(row["cProduct"], row["cLot"]) == RELEASED:
            reason = f"NC {row['iNo']}: {text(row['cDescription'])[:200]}"
            self.lots.change(row["cProduct"], row["cLot"], "on_hold", reason, row["iNo"])
            row["history"].append(self._event("lot_held", row["cLot"]))

    def _open(self, no: int) -> Row:
        row = self.get(no)
        if row["cStatus"] != "open":
            raise AppError("nc_closed", status=409)
        return row

    # ---------------------------------------------------------- write
    def create(self, payload: Row) -> Row:
        row = self.form.apply(self.blank(), payload)
        self._check(row)
        row["iNo"] = self.numbering.next(SEQUENCE)
        row["cStatus"] = "open"
        row["cUser"] = self.username()
        row["dCreated"] = self._now()
        row["history"] = [self._event("created")]
        self._hold(row)
        self.repo.insert(row)
        return self.view(row)

    def update(self, no: int, payload: Row) -> Row:
        current = self._open(no)
        row = self.form.apply(copy.deepcopy(current), payload)
        self._check(row)
        row["history"] = current.get("history", []) + [self._event("edited")]
        self._hold(row)
        self.repo.update(row, [no])
        return self.view(row)

    def delete(self, no: int) -> None:
        """Only an open nonconformance that holds no lot is deleted (a mistake); the others are kept."""
        row = self._open(no)
        if row.get("cLot") and self.lots.status_of(row["cProduct"], row["cLot"]) != RELEASED:
            raise AppError("nc_holds_lot", "cLot", 409)
        self.repo.delete(row)

    def close(self, no: int, payload: Row) -> Row:
        """Close with the decision: the disposition and the corrective action (saved from the payload first)."""
        current = self._open(no)
        row = self.form.apply(copy.deepcopy(current), payload)
        self._check(row)
        if row["cDisposition"] == "pending":
            raise AppError("required", "cDisposition")
        if not text(row.get("cAction")):
            raise AppError("required", "cAction")
        history = current.get("history", [])
        target = LOT_AFTER.get(row["cDisposition"])
        if row.get("cLot") and target:
            now = self.lots.repo.get(row["cProduct"], row["cLot"])
            status = now["cStatus"] if now else RELEASED
            mine = bool(now) and int(now.get("iNC") or 0) == no
            # "use as is" releases only the hold of this nonconformance; scrap and return always reject
            if status != target and (target != RELEASED or mine):
                words = row["cDisposition"].replace("_", " ").replace("supplier", "to supplier")
                self.lots.change(row["cProduct"], row["cLot"], target, f"NC {no} closed: {words}", no)
                history = history + [self._event("lot_" + target, row["cLot"])]
        row["cStatus"] = "closed"
        row["dClosed"] = self._now()
        row["cClosedBy"] = self.username()
        row["history"] = history + [self._event("closed", row["cDisposition"])]
        self.repo.update(row, [no])
        return self.view(row)

    def reopen(self, no: int, comment: str) -> Row:
        """Open a closed nonconformance again (the reason is required); the lot keeps its status."""
        row = self.get(no)
        if row["cStatus"] != "closed":
            raise AppError("invalid_status", status=409)
        if not text(comment):
            raise AppError("required", "cComment")
        row["cStatus"] = "open"
        row["dClosed"], row["cClosedBy"] = "", ""
        row["history"] = row.get("history", []) + [self._event("reopened", text(comment))]
        self.repo.update(row, [no])
        return self.view(row)
