"""Unit tests of the resources (P4): child lists, references, planned downtime and available time."""

from datetime import date

import pytest

from powererp.core.errors import AppError
from powererp.modules.common.registry import ReferenceRegistry
from powererp.modules.production.calendar import CalendarService
from powererp.modules.production.resources import ResourceService, downtime_window
from tests.unit.helpers import memory

MON, SUN = date(2026, 11, 23), date(2026, 11, 29)


@pytest.fixture
def world():
    registry = ReferenceRegistry()
    calendars = CalendarService(memory([]), memory([], keys=("cCalendar", "dDate")), registry)
    week = [{"iWeekday": d, "cShift": "J", "cStart": "07:00", "cEnd": "15:30", "iBreakMin": 30} for d in range(1, 6)]
    calendars.create({"cCode": "MET", "cDescFR": "Métal", "lines": week})
    calendars.create(
        {"cCode": "NIGHT", "cDescFR": "Nuit", "lines": [{"iWeekday": 1, "cStart": "22:00", "cEnd": "06:00"}]}
    )
    centers = memory(
        [
            {"cCode": "CNC", "cType": "machine", "cCalendar": "MET", "dUtilizationPct": "85"},
            {"cCode": "SUB", "cType": "subcontract", "cCalendar": "", "dUtilizationPct": "100"},
        ]
    )
    refs = {
        "work_centers": centers.get,
        "capabilities": memory([{"cCode": "CNC"}, {"cCode": "WELD"}]).get,
        "downtime_reasons": memory([{"cCode": "PM"}]).get,
    }
    return ResourceService(memory([]), refs, calendars, registry), registry


BASE = {"cCode": "cnc1", "cDescFR": "Haas", "cWorkCenter": "cnc"}


def code_of(fn, *args):
    with pytest.raises(AppError) as e:
        fn(*args)
    return e.value.code, e.value.field


def test_create_with_child_lists(world):
    svc, _r = world
    row = svc.create(
        {
            **BASE,
            "capabilities": [{"cCapability": "cnc", "iPreference": "0"}, {"cCapability": ""}],
            "attributes": [{"cAttribute": " Course X ", "cUOM": "mm", "dMax": "1270"}],
            "subresources": [{"cCode": "broche", "cDescFR": "Broche"}],
            "downtime": [{"dStart": "2026-11-25", "cStartTime": "7:00", "cEndTime": "11:00", "cReason": "pm"}],
        }
    )
    assert (row["cCode"], row["cWorkCenter"], row["dSpeedFactor"], row["iParallel"]) == ("CNC1", "CNC", "1", 1)
    assert row["capabilities"] == [{"cCapability": "CNC", "iPreference": 1}]  # empty line dropped, preference >= 1
    assert row["attributes"][0]["cAttribute"] == "Course X" and row["subresources"][0]["cCode"] == "BROCHE"
    assert row["downtime"][0] | {} == {
        **row["downtime"][0],
        "dEnd": "2026-11-25",
        "cStartTime": "07:00",
        "cReason": "PM",
    }


@pytest.mark.parametrize(
    "change, error",
    [
        ({"cWorkCenter": ""}, ("required", "cWorkCenter")),
        ({"cWorkCenter": "NOPE"}, ("unknown_ref", "cWorkCenter")),
        ({"cWorkCenter": "SUB"}, ("subcontract_no_resources", "cWorkCenter")),
        ({"cCalendar": "NOPE"}, ("unknown_ref", "cCalendar")),
        ({"dSpeedFactor": "20"}, ("out_of_range", "dSpeedFactor")),
        ({"iParallel": "0"}, ("out_of_range", "iParallel")),
        ({"capabilities": [{"cCapability": "PAINT"}]}, ("unknown_ref", "capabilities")),
        ({"capabilities": [{"cCapability": "CNC"}, {"cCapability": "cnc"}]}, ("duplicate", "capabilities")),
        ({"attributes": [{"cAttribute": "W", "dMin": "5", "dMax": "2"}]}, ("max_below_min", "attributes")),
        ({"attributes": [{"cAttribute": "W"}, {"cAttribute": "w"}]}, ("duplicate", "attributes")),
        ({"subresources": [{"cCode": "A"}]}, ("required", "subresources")),
        (
            {"downtime": [{"dStart": "2026-11-25", "cStartTime": "11:00", "cEndTime": "07:00"}]},
            ("end_before_start", "downtime"),
        ),
        ({"downtime": [{"dStart": "2026-11-25", "cStartTime": "25:00"}]}, ("invalid_time", "downtime")),
        ({"downtime": [{"dStart": "2026-11-25", "cReason": "ZZ"}]}, ("unknown_ref", "downtime")),
    ],
)
def test_rules(world, change, error):
    svc, _r = world
    assert code_of(svc.create, {**BASE, **change}) == error


def test_available_time_minus_planned_downtime(world):
    svc, _r = world
    svc.create(
        {**BASE, "iParallel": 2, "downtime": [{"dStart": "2026-11-25", "cStartTime": "07:00", "cEndTime": "11:00"}]}
    )
    r = svc.availability("CNC1", MON, SUN)
    assert (r["cCalendar"], r["iCalendarMinutes"], r["iDowntimeMinutes"], r["iMinutes"]) == ("MET", 2400, 240, 2160)
    assert r["days"][2]["iMinutes"] == 240  # Wednesday: 480 - 240
    assert r["iCapacityMinutes"] == round(2160 * 0.85 * 2)  # x utilization of the work center x parallel


def test_whole_day_downtime_and_own_calendar(world):
    svc, _r = world
    svc.create({**BASE, "cCalendar": "night", "downtime": [{"dStart": "2026-11-23"}]})  # no times: the whole day
    r = svc.availability("CNC1", MON, MON)
    # the night shift of Monday runs 22:00-06:00: 2 hours fall on Monday (the downtime day), 6 on Tuesday
    assert (r["cCalendar"], r["iCalendarMinutes"], r["iDowntimeMinutes"], r["iMinutes"]) == ("NIGHT", 480, 120, 360)


def test_downtime_window():
    a, b = downtime_window({"dStart": "2026-11-25", "cStartTime": "22:00", "dEnd": "2026-11-26", "cEndTime": "02:00"})
    assert (b - a).total_seconds() == 4 * 3600


def test_references_and_alternatives(world):
    svc, registry = world
    svc.create(
        {
            **BASE,
            "capabilities": [{"cCapability": "CNC", "iPreference": 2}],
            "downtime": [{"dStart": "2026-11-25", "cReason": "PM"}],
        }
    )
    svc.create(
        {
            "cCode": "CNC2",
            "cDescFR": "B",
            "cWorkCenter": "CNC",
            "capabilities": [{"cCapability": "CNC", "iPreference": 1}],
        }
    )
    svc.create(
        {
            "cCode": "OFF",
            "cDescFR": "C",
            "cWorkCenter": "CNC",
            "lActive": False,
            "capabilities": [{"cCapability": "CNC"}],
        }
    )
    assert [r["cCode"] for r in svc.with_capability("cnc")] == ["CNC2", "CNC1"]  # preferred first, inactive left out
    assert (
        registry.is_used("work_center", "CNC")
        and registry.is_used("capability", "CNC")
        and not registry.is_used("capability", "WELD")
    )
    assert registry.is_used("downtime_reason", "pm") and not registry.is_used("calendar", "MET")
    assert svc.view(svc.get("CNC1"), full=False)["cCapabilities"] == "CNC"
