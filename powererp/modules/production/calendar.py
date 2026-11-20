"""Working calendars (P2): the shifts of each weekday, the exceptions by date, and the time they make available.

A calendar is used by the work centers and the resources (P3, P4): the scheduler only plans work inside the
intervals given by `intervals()`. Rules:
- a shift is "HH:MM" to "HH:MM"; when the end is at or before the start, it ends the next day (22:00-06:00);
- a shift belongs to the day it starts (the night shift of Friday is Friday's);
- the shifts of a calendar never overlap, also across midnight and from Sunday to Monday;
- an exception replaces the week for its date: closed (holiday) or other hours (overtime, short day);
  an exception of the calendar wins over one for every calendar ("*").
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta

from powererp import schemas as S
from powererp.core.errors import AppError
from powererp.core.http import require
from powererp.core.values import text
from powererp.modules.common.crud import CrudService
from powererp.modules.common.forms import Row
from powererp.modules.common.registry import ReferenceRegistry
from powererp.store import Store

ALL = "*"  # an exception for every calendar
DAY, WEEK = 1440, 7 * 1440
MAX_DAYS = 366
TIME = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")


def minutes_of(value: str, field: str) -> int:
    """'07:30' -> 450; AppError invalid_time on the field otherwise ('7:30' is accepted as 07:30)."""
    v = text(value)
    if re.match(r"^\d:\d\d$", v):
        v = "0" + v
    m = TIME.match(v)
    if not m:
        raise AppError("invalid_time", field)
    return int(m.group(1)) * 60 + int(m.group(2))


def normalize_time(value: str, field: str) -> str:
    m = minutes_of(value, field)
    return f"{m // 60:02d}:{m % 60:02d}"


def span(start: str, end: str, field: str = "cEnd") -> tuple[int, int]:
    """(start, length) in minutes; the end is the next day when it is at or before the start."""
    a, b = minutes_of(start, "cStart"), minutes_of(end, field)
    return a, (b - a) % DAY or DAY


def check_break(length: int, break_min: int, field: str = "iBreakMin") -> None:
    if break_min < 0 or break_min >= length:
        raise AppError("break_too_long", field)


@dataclass(frozen=True)
class Interval:
    """Working time of one shift on one day: [start, end) and the paid minutes (length - break)."""

    day: date
    shift: str
    start: datetime
    end: datetime
    minutes: int


class CalendarService(CrudService):
    line_schema = S.CALENDAR_SHIFT
    kind = "calendar"

    def __init__(self, repo: Store, exceptions_repo: Store, references: ReferenceRegistry):
        super().__init__(repo, S.CALENDAR, S.DEFAULTS["calendars"])
        self.exceptions_repo = exceptions_repo
        self.references = references  # work centers and resources (P3, P4) say when they use a calendar

    def keep_line(self, line: Row) -> bool:
        return bool(line["cStart"] or line["cEnd"] or line["iWeekday"])

    def validate(self, row: Row, is_new: bool) -> None:
        require(row, "cDescFR")
        row["cCode"] = row["cCode"].upper()
        if row["cCode"] == ALL:
            raise AppError("invalid_code", "cCode")
        taken: list[tuple[int, int, int]] = []  # (start in the week, end, line)
        for i, ln in enumerate(row.get("lines", []), 1):
            where = f"line {i}"
            if not 1 <= ln["iWeekday"] <= 7:
                raise AppError("invalid_weekday", "lines", detail=where)
            try:
                ln["cStart"], ln["cEnd"] = normalize_time(ln["cStart"], "cStart"), normalize_time(ln["cEnd"], "cEnd")
                start, length = span(ln["cStart"], ln["cEnd"])
                check_break(length, ln["iBreakMin"])
            except AppError as e:
                raise AppError(e.code, "lines", detail=f"{where}: {e.field}") from None
            ln["cShift"] = ln["cShift"] or str(sum(1 for x in row["lines"][:i] if x["iWeekday"] == ln["iWeekday"]))
            a = (ln["iWeekday"] - 1) * DAY + start
            for b_start, b_end, j in taken:
                # compare on a circular week: shift the other one by -1, 0, +1 week
                if any(a < b_end + k * WEEK and b_start + k * WEEK < a + length for k in (-1, 0, 1)):
                    raise AppError("shift_overlap", "lines", detail=f"{where} / line {j}")
            taken.append((a, a + length, i))
        row["lines"] = sorted(row.get("lines", []), key=lambda x: (x["iWeekday"], x["cStart"]))

    def before_delete(self, row: Row) -> None:
        self.references.check("calendar", row["cCode"])
        for e in self.exceptions_repo.all(lines=False):  # its own exceptions go with it
            if e["cCalendar"].upper() == row["cCode"].upper():
                self.exceptions_repo.delete(e)

    def view(self, row: Row, full: bool = True) -> Row:
        if full:
            return row
        week = sum(span(ln["cStart"], ln["cEnd"])[1] - ln["iBreakMin"] for ln in row.get("lines", []))
        return {**row, "iWeekMinutes": week, "iShifts": len(row.get("lines", []))}

    # ---------------------------------------------------------- available time
    def _exceptions(self, code: str, start: date, end: date) -> dict[date, Row]:
        mine: dict[date, Row] = {}
        everyone: dict[date, Row] = {}
        for e in self.exceptions_repo.all(lines=False):
            d = date.fromisoformat(e["dDate"])
            if not start <= d <= end:
                continue
            if e["cCalendar"].upper() == code.upper():
                mine[d] = e
            elif e["cCalendar"] == ALL:
                everyone[d] = e
        return {**everyone, **mine}

    def intervals(self, code: str, start: date, end: date) -> list[Interval]:
        """The working intervals of the shifts starting from `start` to `end` (inclusive), in order."""
        cal = self.get(code)
        if end < start:
            raise AppError("invalid_range", "to")
        if (end - start).days >= MAX_DAYS:
            raise AppError("range_too_long", "to", detail=f"{MAX_DAYS} days")
        exceptions = self._exceptions(cal["cCode"], start, end)
        out: list[Interval] = []
        d = start
        while d <= end:
            exc = exceptions.get(d)
            if exc is not None:
                shifts = [] if exc["lClosed"] else [{**exc, "cShift": "*"}]
            else:
                shifts = [s for s in cal.get("lines", []) if s["iWeekday"] == d.isoweekday()]
            midnight = datetime(d.year, d.month, d.day)
            for s in shifts:
                a, length = span(s["cStart"], s["cEnd"])
                begin = midnight + timedelta(minutes=a)
                out.append(Interval(d, s["cShift"], begin, begin + timedelta(minutes=length), length - s["iBreakMin"]))
            d += timedelta(days=1)
        return sorted(out, key=lambda x: x.start)

    def availability(self, code: str, start: date, end: date) -> Row:
        """Minutes available per day (the preview of the screen)."""
        exceptions = self._exceptions(self.get(code)["cCode"], start, end)
        by_day: dict[date, list[Interval]] = {}
        for iv in self.intervals(code, start, end):
            by_day.setdefault(iv.day, []).append(iv)
        days = []
        d = start
        while d <= end:
            ivs = by_day.get(d, [])
            exc = exceptions.get(d)
            days.append(
                {
                    "dDate": d.isoformat(),
                    "iWeekday": d.isoweekday(),
                    "shifts": [
                        {
                            "cShift": iv.shift,
                            "cStart": iv.start.strftime("%H:%M"),
                            "cEnd": iv.end.strftime("%H:%M"),
                            "iMinutes": iv.minutes,
                        }
                        for iv in ivs
                    ],
                    "iMinutes": sum(iv.minutes for iv in ivs),
                    "cException": (exc.get("cDescFR") or "") if exc else "",
                    "cExceptionEN": (exc.get("cDescEN") or exc.get("cDescFR") or "") if exc else "",
                    "lClosed": bool(exc and exc["lClosed"]),
                }
            )
            d += timedelta(days=1)
        return {"cCalendar": code.upper(), "days": days, "iMinutes": sum(x["iMinutes"] for x in days)}


class CalendarExceptionService(CrudService):
    keys = ("cCalendar", "dDate")

    def __init__(self, repo: Store, calendars: CalendarService):
        super().__init__(repo, S.CALENDAR_EXCEPTION, S.DEFAULTS["calendar_exceptions"])
        self.calendars = calendars

    def validate(self, row: Row, is_new: bool) -> None:
        require(row, "dDate", "cDescFR")
        code = text(row["cCalendar"]).upper() or ALL
        if code != ALL:
            cal = self.calendars.find(code)
            if cal is None:
                raise AppError("unknown_ref", "cCalendar")
            code = cal["cCode"]
        row["cCalendar"] = code
        if row["lClosed"]:
            row["cStart"] = row["cEnd"] = ""
            row["iBreakMin"] = 0
            return
        row["cStart"], row["cEnd"] = normalize_time(row["cStart"], "cStart"), normalize_time(row["cEnd"], "cEnd")
        check_break(span(row["cStart"], row["cEnd"])[1], row["iBreakMin"])
