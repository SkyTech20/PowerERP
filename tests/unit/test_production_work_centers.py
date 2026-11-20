"""Unit tests of the work centers (P3): references to the other modules, ranges, subcontracting."""

import pytest

from powererp.core.errors import AppError
from powererp.modules.common.registry import ReferenceRegistry
from powererp.modules.production.work_centers import WorkCenterService
from tests.unit.helpers import memory


@pytest.fixture
def centers():
    cals = memory([{"cCode": "MET-1X5"}])
    whs = memory([{"cCode": "ENT-01"}])
    locs = memory([{"cWarehouse": "ENT-01", "cCode": "A-1"}], keys=("cWarehouse", "cCode"))
    sups = memory([{"cCode": "USINEX"}])
    refs = {
        "calendars": cals.get,
        "warehouses": whs.get,
        "locations": locs.get,
        "suppliers": sups.get,
        "cost_centers": lambda: {"200", "200-310"},
    }
    registry = ReferenceRegistry()
    return WorkCenterService(memory([]), refs, registry), registry


def code_of(fn, *args):
    with pytest.raises(AppError) as e:
        fn(*args)
    return e.value.code, e.value.field


BASE = {"cCode": "cnc", "cDescFR": "CNC", "cCalendar": "met-1x5"}


def test_create_with_defaults_and_normalized_references(centers):
    svc, _r = centers
    row = svc.create({**BASE, "cWarehouse": "ent-01", "cInLocation": "a-1", "cCostCenter": "200-310"})
    assert (row["cCode"], row["cCalendar"], row["cWarehouse"], row["cInLocation"]) == (
        "CNC",
        "MET-1X5",
        "ENT-01",
        "A-1",
    )
    assert (row["cType"], row["lFinite"], row["dEfficiencyPct"], row["dUtilizationPct"]) == (
        "machine",
        True,
        "100",
        "100",
    )


@pytest.mark.parametrize(
    "change, error",
    [
        ({"cCalendar": ""}, ("required", "cCalendar")),
        ({"cCalendar": "NOPE"}, ("unknown_ref", "cCalendar")),
        ({"dEfficiencyPct": "0"}, ("out_of_range", "dEfficiencyPct")),
        ({"dUtilizationPct": "120"}, ("out_of_range", "dUtilizationPct")),
        ({"dRunRateHr": "-1"}, ("negative", "dRunRateHr")),
        ({"iQueueMin": "-5"}, ("negative", "iQueueMin")),
        ({"cCostCenter": "999"}, ("unknown_ref", "cCostCenter")),
        ({"cWarehouse": "NOPE"}, ("unknown_ref", "cWarehouse")),
        ({"cInLocation": "A-1"}, ("required", "cWarehouse")),
        ({"cWarehouse": "ENT-01", "cOutLocation": "Z-9"}, ("unknown_ref", "cOutLocation")),
        ({"cSupplier": "USINEX"}, ("subcontract_only", "cSupplier")),
        ({"cType": "robot"}, ("invalid_choice", "cType")),
    ],
)
def test_rules(centers, change, error):
    svc, _r = centers
    assert code_of(svc.create, {**BASE, **change}) == error


def test_subcontract(centers):
    svc, _r = centers
    assert code_of(svc.create, {"cCode": "TRT", "cDescFR": "Traitement", "cType": "subcontract"}) == (
        "required",
        "cSupplier",
    )
    row = svc.create(
        {"cCode": "TRT", "cDescFR": "Traitement", "cType": "subcontract", "cSupplier": "usinex", "lFinite": True}
    )
    assert (row["cSupplier"], row["cCalendar"], row["lFinite"]) == ("USINEX", "", False)  # no calendar needed


def test_calendar_in_use_and_delete_checks(centers):
    svc, registry = centers
    svc.create(BASE)
    assert registry.is_used("calendar", "met-1x5") and not registry.is_used("calendar", "OTHER")
    registry.register("work_center", lambda code: code == "CNC")  # e.g. a resource of the work center (P4)
    assert code_of(svc.delete, ["CNC"]) == ("in_use", None)


def test_capacity_minutes(centers):
    svc, _r = centers
    row = svc.create({**BASE, "dUtilizationPct": "85"})
    assert svc.capacity_minutes(row, 2400) == 2040
