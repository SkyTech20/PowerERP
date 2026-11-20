"""Resources (P4): the machine, line, station or team that really does the work, inside a work center.

What a resource gives the rest of Production:
- its calendar (its own, else the work center's) minus its planned downtime = the time it is available;
- its speed factor (1.2 = 20 % faster than the standard times) and how many orders it runs at once (parallel);
- its capabilities: an operation asking for a capability (P1) can run on any resource that has it, the
  preference ranks the alternatives for the scheduler;
- its attributes with limits (width 2.5 to 5.4 m, 6 knives, oven up to 280 degrees): a product / operation is
  checked against them later (P7, P8);
- its subresources (the parts of the machine) to say where a stop was on the shop floor (M4).
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

from powererp import schemas as S
from powererp.core.errors import AppError
from powererp.core.http import require
from powererp.core.values import number, text
from powererp.modules.common.crud import CrudService
from powererp.modules.common.forms import Row
from powererp.modules.common.registry import ReferenceRegistry
from powererp.store import Store

from .calendar import CalendarService, normalize_time


def _at(day: str, time: str, field: str) -> datetime:
    """'2026-11-24' + '13:30' -> datetime; an empty time is midnight."""
    try:
        d = date.fromisoformat(day)
    except ValueError:
        raise AppError("invalid_date", field) from None
    hhmm = normalize_time(time, field) if text(time) else "00:00"
    return datetime(d.year, d.month, d.day, int(hhmm[:2]), int(hhmm[3:]))


def downtime_window(dt: Row, line: int | None = None) -> tuple[datetime, datetime]:
    where = f"line {line}" if line else None
    try:
        start = _at(dt["dStart"], dt["cStartTime"], "dStart")
        # no end time: the whole end day
        end = _at(dt["dEnd"] or dt["dStart"], dt["cEndTime"], "dEnd")
        if not text(dt["cEndTime"]):
            end += timedelta(days=1)
    except AppError as e:
        raise AppError(e.code, "downtime", detail=f"{where}: {e.field}" if where else e.field) from None
    if end <= start:
        raise AppError("end_before_start", "downtime", detail=where)
    return start, end


def _overlap(a: datetime, b: datetime, c: datetime, d: datetime) -> int:
    """Minutes shared by [a, b) and [c, d)."""
    return max(0, int((min(b, d) - max(a, c)).total_seconds() // 60))


class ResourceService(CrudService):
    kind = "resource"
    children = {
        "capabilities": S.RESOURCE_CAPABILITY,
        "attributes": S.RESOURCE_ATTRIBUTE,
        "subresources": S.RESOURCE_SUBRESOURCE,
        "downtime": S.RESOURCE_DOWNTIME,
    }

    def __init__(self, repo: Store, refs: dict[str, Any], calendars: CalendarService, references: ReferenceRegistry):
        """refs: finders given by the container: work_centers, capabilities, downtime_reasons."""
        super().__init__(repo, S.RESOURCE, S.DEFAULTS["resources"])
        self.refs = refs
        self.calendars = calendars
        self.references = references
        references.register("work_center", lambda code: self._uses("cWorkCenter", code))
        references.register("calendar", lambda code: self._uses("cCalendar", code))
        references.register("capability", lambda code: self._uses_child("capabilities", "cCapability", code))
        references.register("downtime_reason", lambda code: self._uses_child("downtime", "cReason", code))

    # ---------------------------------------------------------- references
    def _uses(self, field: str, code: str) -> bool:
        return any(r[field].upper() == code.upper() for r in self.repo.all(lines=False))

    def _uses_child(self, key: str, field: str, code: str) -> bool:
        return any(c[field].upper() == code.upper() for r in self.repo.all() for c in r.get(key, []))

    def keep_child(self, key: str, line: Row) -> bool:
        first = {
            "capabilities": "cCapability",
            "attributes": "cAttribute",
            "subresources": "cCode",
            "downtime": "dStart",
        }
        return bool(text(line.get(first[key])))

    # ---------------------------------------------------------- rules
    def validate(self, row: Row, is_new: bool) -> None:
        require(row, "cDescFR", "cWorkCenter")
        row["cCode"] = row["cCode"].upper()
        wc = self.refs["work_centers"](row["cWorkCenter"])
        if wc is None:
            raise AppError("unknown_ref", "cWorkCenter")
        if wc["cType"] == "subcontract":
            raise AppError("subcontract_no_resources", "cWorkCenter")
        row["cWorkCenter"] = wc["cCode"]
        if row["cCalendar"]:
            cal = self.calendars.find(row["cCalendar"])
            if cal is None:
                raise AppError("unknown_ref", "cCalendar")
            row["cCalendar"] = cal["cCode"]
        if not text(row["dSpeedFactor"]):
            row["dSpeedFactor"] = "1"
        if not 0.1 <= number(row["dSpeedFactor"]) <= 10:
            raise AppError("out_of_range", "dSpeedFactor", detail="0.1-10")
        if not 1 <= row["iParallel"] <= 100:
            raise AppError("out_of_range", "iParallel", detail="1-100")
        self._check_capabilities(row)
        self._check_attributes(row)
        self._check_subresources(row)
        self._check_downtime(row)

    def _check_capabilities(self, row: Row) -> None:
        seen = set()
        for i, c in enumerate(row.get("capabilities", []), 1):
            cap = self.refs["capabilities"](c["cCapability"])
            if cap is None:
                raise AppError("unknown_ref", "capabilities", detail=f"line {i}: {c['cCapability']}")
            c["cCapability"] = cap["cCode"]
            if cap["cCode"] in seen:
                raise AppError("duplicate", "capabilities", detail=f"line {i}: {cap['cCode']}")
            seen.add(cap["cCode"])
            c["iPreference"] = c["iPreference"] if c["iPreference"] > 0 else 1

    @staticmethod
    def _check_attributes(row: Row) -> None:
        seen = set()
        for i, a in enumerate(row.get("attributes", []), 1):
            name = a["cAttribute"].strip()
            if name.lower() in seen:
                raise AppError("duplicate", "attributes", detail=f"line {i}: {name}")
            seen.add(name.lower())
            a["cAttribute"] = name
            if text(a["dMin"]) and text(a["dMax"]) and number(a["dMax"]) < number(a["dMin"]):
                raise AppError("max_below_min", "attributes", detail=f"line {i}: {name}")

    @staticmethod
    def _check_subresources(row: Row) -> None:
        seen = set()
        for i, sub in enumerate(row.get("subresources", []), 1):
            sub["cCode"] = sub["cCode"].strip().upper()
            if sub["cCode"] in seen:
                raise AppError("duplicate", "subresources", detail=f"line {i}: {sub['cCode']}")
            seen.add(sub["cCode"])
            if not sub["cDescFR"]:
                raise AppError("required", "subresources", detail=f"line {i}: cDescFR")

    def _check_downtime(self, row: Row) -> None:
        for i, dt in enumerate(row.get("downtime", []), 1):
            dt["cStartTime"] = normalize_time(dt["cStartTime"], "downtime") if text(dt["cStartTime"]) else ""
            dt["cEndTime"] = normalize_time(dt["cEndTime"], "downtime") if text(dt["cEndTime"]) else ""
            dt["dEnd"] = dt["dEnd"] or dt["dStart"]
            downtime_window(dt, i)
            if dt["cReason"]:
                reason = self.refs["downtime_reasons"](dt["cReason"])
                if reason is None:
                    raise AppError("unknown_ref", "downtime", detail=f"line {i}: {dt['cReason']}")
                dt["cReason"] = reason["cCode"]
        row["downtime"] = sorted(row.get("downtime", []), key=lambda d: (d["dStart"], d["cStartTime"]))

    def before_delete(self, row: Row) -> None:
        self.references.check(self.kind, row["cCode"])  # recipe operations (P8)

    def view(self, row: Row, full: bool = True) -> Row:
        if full:
            return row
        caps = ", ".join(c["cCapability"] for c in row.get("capabilities", []))
        return {**row, "cCapabilities": caps}

    def with_capability(self, capability: str) -> list[Row]:
        """The active resources able to do it, preferred first (the alternatives of an operation)."""
        found = []
        for r in self.repo.all():
            if not r.get("lActive"):
                continue
            for c in r.get("capabilities", []):
                if c["cCapability"].upper() == capability.upper():
                    found.append((c["iPreference"], r["cCode"], r))
        return [r for _p, _c, r in sorted(found, key=lambda x: (x[0], x[1]))]

    # ---------------------------------------------------------- available time
    def calendar_of(self, row: Row) -> str:
        if row["cCalendar"]:
            return row["cCalendar"]
        wc = self.refs["work_centers"](row["cWorkCenter"]) or {}
        if not wc.get("cCalendar"):
            raise AppError("no_calendar", "cCalendar")
        return wc["cCalendar"]

    def availability(self, code: str, start: date, end: date) -> Row:
        """The calendar time per day minus the planned downtime, and the capacity the scheduler can load
        (available x utilization of the work center x parallel orders)."""
        res = self.get(code)
        cal = self.calendar_of(res)
        base = self.calendars.availability(cal, start, end)
        windows = [downtime_window(dt) for dt in res.get("downtime", [])]
        lost: dict[str, int] = {}
        for iv in self.calendars.intervals(cal, start, end):
            taken = sum(_overlap(iv.start, iv.end, a, b) for a, b in windows)
            lost[iv.day.isoformat()] = lost.get(iv.day.isoformat(), 0) + min(taken, iv.minutes)
        for d in base["days"]:
            d["iCalendarMinutes"] = d["iMinutes"]
            d["iDowntimeMinutes"] = lost.get(d["dDate"], 0)
            d["iMinutes"] = d["iCalendarMinutes"] - d["iDowntimeMinutes"]
        wc = self.refs["work_centers"](res["cWorkCenter"]) or {}
        available = sum(d["iMinutes"] for d in base["days"])
        utilization = number(wc.get("dUtilizationPct") or 100) / 100
        return {
            **base,
            "cResource": res["cCode"],
            "cCalendar": cal,
            "iCalendarMinutes": base["iMinutes"],
            "iDowntimeMinutes": sum(d["iDowntimeMinutes"] for d in base["days"]),
            "iMinutes": available,
            "iCapacityMinutes": round(available * utilization * res["iParallel"]),
        }
