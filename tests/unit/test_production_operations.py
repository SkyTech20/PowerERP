"""Unit tests of the standard operations (P5): where they run, subcontracting, and the time of a quantity."""

import pytest

from powererp.core.errors import AppError
from powererp.modules.common.registry import ReferenceRegistry
from powererp.modules.production.operations import OperationService, run_minutes
from tests.unit.helpers import memory


@pytest.fixture
def ops():
    refs = {
        "work_centers": memory([{"cCode": "PEINT", "cType": "line"}, {"cCode": "SUB", "cType": "subcontract"}]).get,
        "capabilities": memory([{"cCode": "CNC"}]).get,
        "suppliers": memory([{"cCode": "USINEX"}]).get,
    }
    registry = ReferenceRegistry()
    return OperationService(memory([]), refs, registry), registry


def code_of(fn, *args):
    with pytest.raises(AppError) as e:
        fn(*args)
    return e.value.code, e.value.field


BASE = {"cCode": "usin", "cDescFR": "Usinage", "cCapability": "cnc", "dSetupMin": "45", "dRunValue": "6.5"}


@pytest.mark.parametrize(
    "fmt, value, qty, lot, minutes",
    [
        ("min_per_unit", 6.5, 100, 0, 650),
        ("units_per_hour", 1200, 600, 0, 30),
        ("min_per_lot", 25, 500, 0, 25),  # one lot whatever the quantity
        ("min_per_lot", 25, 500, 200, 75),  # 3 lots of 200
        ("min_per_unit", 6.5, 0, 0, 0),
    ],
)
def test_run_minutes(fmt, value, qty, lot, minutes):
    assert run_minutes(fmt, value, qty, lot) == pytest.approx(minutes)


def test_create_and_time_of_a_quantity(ops):
    svc, _r = ops
    row = svc.create(BASE)
    assert (row["cCode"], row["cCapability"], row["cRunFormat"], row["iCrew"], row["lReportingPoint"]) == (
        "USIN",
        "CNC",
        "min_per_unit",
        1,
        True,
    )
    t = svc.minutes("USIN", 100)
    assert (t["dSetupMin"], t["dRunMin"], t["dTotalMin"]) == (45, 650, 695)
    # a resource 30 % faster in a work center at 100 % efficiency; then a 90 % efficient work center
    assert svc.minutes("USIN", 100, speed=1.3)["dRunMin"] == 500
    assert svc.minutes("USIN", 90, efficiency=90)["dRunMin"] == 650
    svc.update(["USIN"], {"iCrew": "2"})
    assert svc.minutes("USIN", 10)["dLaborMin"] == (45 + 65) * 2


@pytest.mark.parametrize(
    "change, error",
    [
        ({"cCapability": ""}, ("work_center_or_capability", "cWorkCenter")),
        ({"cWorkCenter": "PEINT"}, ("work_center_or_capability", "cCapability")),
        ({"cCapability": "WELD"}, ("unknown_ref", "cCapability")),
        ({"cCapability": "", "cWorkCenter": "NOPE"}, ("unknown_ref", "cWorkCenter")),
        ({"dSetupMin": "-1"}, ("negative", "dSetupMin")),
        ({"iCrew": "-1"}, ("negative", "iCrew")),
        ({"cRunFormat": "units_per_hour", "dRunValue": "0"}, ("positive", "dRunValue")),
        ({"cRunFormat": "per_day"}, ("invalid_choice", "cRunFormat")),
        ({"lSubcontract": True}, ("required", "cSupplier")),
        ({"lSubcontract": True, "cSupplier": "NOPE"}, ("unknown_ref", "cSupplier")),
    ],
)
def test_rules(ops, change, error):
    svc, _r = ops
    assert code_of(svc.create, {**BASE, **change}) == error


def test_subcontracted_operations(ops):
    svc, _r = ops
    row = svc.create(
        {**BASE, "lSubcontract": True, "cSupplier": "usinex", "dSubcontractCost": "4.25", "iSubcontractDays": 5}
    )
    assert (row["cSupplier"], row["cCapability"], row["iSubcontractDays"]) == ("USINEX", "", 5)
    # a subcontract work center makes the operation subcontracted
    row = svc.create({"cCode": "TRT", "cDescFR": "Traitement", "cWorkCenter": "sub", "cSupplier": "USINEX"})
    assert (row["cWorkCenter"], row["lSubcontract"]) == ("SUB", True)
    # back in house: the subcontract fields are cleared
    row = svc.update(["USIN"], {"lSubcontract": False, "cCapability": "CNC"})
    assert (row["cSupplier"], row["dSubcontractCost"], row["iSubcontractDays"]) == ("", "", 0)


def test_references(ops):
    svc, registry = ops
    svc.create(BASE)
    svc.create(
        {"cCode": "P", "cDescFR": "Peinture", "cWorkCenter": "PEINT", "cRunFormat": "min_per_lot", "dRunValue": "60"}
    )
    assert registry.is_used("capability", "CNC") and registry.is_used("work_center", "peint")
    registry.register("operation", lambda code: code == "USIN")  # a recipe uses it (P8)
    assert code_of(svc.delete, ["USIN"]) == ("in_use", None)
