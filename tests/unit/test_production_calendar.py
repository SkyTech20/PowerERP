"""Unit tests of the working calendars (P2): shift rules, exceptions and available minutes."""

from datetime import date, datetime

import pytest

from powererp.core.errors import AppError
from powererp.modules.common.registry import ReferenceRegistry
from powererp.modules.production.calendar import CalendarExceptionService, CalendarService, minutes_of, span
from tests.unit.helpers import memory

MON = date(2026, 11, 23)  # a Monday
SUN = date(2026, 11, 29)


def shift(day, start, end, brk=0, name=""):
    return {"iWeekday": day, "cShift": name, "cStart": start, "cEnd": end, "iBreakMin": brk}


@pytest.fixture
def svc():
    refs = ReferenceRegistry()
    calendars = CalendarService(memory([]), memory([], keys=("cCalendar", "dDate")), refs)
    exceptions = CalendarExceptionService(calendars.exceptions_repo, calendars)
    return calendars, exceptions, refs


def error(fn, *args):
    with pytest.raises(AppError) as e:
        fn(*args)
    return e.value.code, e.value.field, e.value.detail


def test_times():
    assert minutes_of("07:30", "x") == 450 and minutes_of("7:30", "x") == 450
    assert span("22:00", "06:00") == (1320, 480)  # ends the next day
    assert span("07:00", "07:00") == (420, 1440)  # a 24 h shift
    for bad in ("24:00", "7h30", "", "12:60"):
        with pytest.raises(AppError):
            minutes_of(bad, "cStart")


def test_shift_rules(svc):
    calendars, _e, _r = svc
    row = calendars.create(
        {"cCode": "c1", "cDescFR": "Un", "lines": [shift(2, "7:00", "15:00", 30), shift(1, "07:00", "15:00")]}
    )
    assert (
        row["cCode"] == "C1"
        and [ln["iWeekday"] for ln in row["lines"]] == [1, 2]
        and row["lines"][1]["cStart"] == "07:00"
    )
    assert (
        error(calendars.create, {"cCode": "X", "cDescFR": "x", "lines": [shift(8, "07:00", "15:00")]})[0]
        == "invalid_weekday"
    )
    assert (
        error(calendars.create, {"cCode": "X", "cDescFR": "x", "lines": [shift(1, "07:00", "15:00", 480)]})[0]
        == "break_too_long"
    )
    assert error(calendars.create, {"cCode": "X", "cDescFR": "x", "lines": [shift(1, "07:00", "25:00")]})[:2] == (
        "invalid_time",
        "lines",
    )
    assert error(calendars.create, {"cCode": "*", "cDescFR": "x"})[:2] == ("invalid_code", "cCode")


@pytest.mark.parametrize(
    "a, b",
    [
        (shift(1, "07:00", "15:00"), shift(1, "14:00", "22:00")),  # same day
        (shift(1, "22:00", "06:00"), shift(2, "05:00", "13:00")),  # the night shift runs into Tuesday
        (shift(7, "22:00", "06:00"), shift(1, "05:00", "13:00")),  # Sunday night runs into Monday
    ],
)
def test_overlapping_shifts_are_refused(svc, a, b):
    calendars, _e, _r = svc
    assert error(calendars.create, {"cCode": "X", "cDescFR": "x", "lines": [a, b]})[0] == "shift_overlap"


def test_back_to_back_shifts_are_fine(svc):
    calendars, _e, _r = svc
    lines = [
        shift(d, s, e) for d in range(1, 8) for s, e in (("07:00", "15:00"), ("15:00", "23:00"), ("23:00", "07:00"))
    ]
    assert len(calendars.create({"cCode": "X", "cDescFR": "x", "lines": lines})["lines"]) == 21


def test_available_minutes_with_exceptions(svc):
    calendars, exceptions, _r = svc
    week = [shift(d, "07:00", "15:30", 30, "JOUR") for d in range(1, 6)]
    calendars.create({"cCode": "MET", "cDescFR": "Métal", "lines": week})
    assert calendars.availability("MET", MON, SUN)["iMinutes"] == 5 * 480
    exceptions.create(
        {
            "cCalendar": "met",
            "dDate": "2026-11-28",
            "cDescFR": "Samedi",
            "lClosed": False,
            "cStart": "07:00",
            "cEnd": "12:00",
        }
    )
    exceptions.create({"cCalendar": "*", "dDate": "2026-11-23", "cDescFR": "Fermé", "lClosed": True})
    days = calendars.availability("MET", MON, SUN)["days"]
    assert [d["iMinutes"] for d in days] == [0, 480, 480, 480, 480, 300, 0]
    assert days[0]["lClosed"] and days[0]["cException"] == "Fermé"
    # an exception of the calendar wins over the one for every calendar
    exceptions.create(
        {
            "cCalendar": "MET",
            "dDate": "2026-11-23",
            "cDescFR": "Ouvert",
            "lClosed": False,
            "cStart": "08:00",
            "cEnd": "10:00",
        }
    )
    assert calendars.availability("MET", MON, MON)["iMinutes"] == 120


def test_night_shift_belongs_to_its_start_day(svc):
    calendars, _e, _r = svc
    calendars.create({"cCode": "N", "cDescFR": "Nuit", "lines": [shift(5, "22:00", "06:00", 30, "NUIT")]})
    [iv] = calendars.intervals("N", date(2026, 11, 27), date(2026, 11, 27))  # Friday
    assert (iv.start, iv.end, iv.minutes) == (datetime(2026, 11, 27, 22), datetime(2026, 11, 28, 6), 450)


def test_exception_rules(svc):
    calendars, exceptions, _r = svc
    assert error(exceptions.create, {"cCalendar": "NOPE", "dDate": "2026-12-25", "cDescFR": "x"})[:2] == (
        "unknown_ref",
        "cCalendar",
    )
    assert error(exceptions.create, {"cCalendar": "*", "cDescFR": "x"})[:2] == ("required", "dDate")
    assert (
        error(
            exceptions.create, {"dDate": "2026-12-25", "cDescFR": "x", "lClosed": False, "cStart": "8:00", "cEnd": ""}
        )[0]
        == "invalid_time"
    )
    row = exceptions.create({"dDate": "2026-12-25", "cDescFR": "Noël", "cStart": "08:00"})
    assert (row["cCalendar"], row["lClosed"], row["cStart"]) == ("*", True, "")  # closed by default


def test_deleting_a_calendar(svc):
    calendars, exceptions, refs = svc
    calendars.create({"cCode": "A", "cDescFR": "a"})
    exceptions.create({"cCalendar": "A", "dDate": "2026-12-24", "cDescFR": "x"})
    exceptions.create({"cCalendar": "*", "dDate": "2026-12-25", "cDescFR": "y"})
    refs.register("calendar", lambda code: code == "B")  # e.g. a work center uses B
    calendars.create({"cCode": "B", "cDescFR": "b"})
    assert error(calendars.delete, ["B"])[0] == "in_use"
    calendars.delete(["A"])
    assert [e["cCalendar"] for e in exceptions.list()] == ["*"]  # its own exceptions went with it


def test_range_limits(svc):
    calendars, _e, _r = svc
    calendars.create({"cCode": "A", "cDescFR": "a"})
    assert error(calendars.intervals, "A", SUN, MON)[0] == "invalid_range"
    assert error(calendars.intervals, "A", date(2026, 1, 1), date(2027, 1, 2))[0] == "range_too_long"
