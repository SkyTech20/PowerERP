"""Unit tests of the manufacturing data of the products (P7)."""

import pytest

from powererp.core.errors import AppError
from powererp.modules.common.registry import ReferenceRegistry
from powererp.modules.production.products import ProductMfgService
from tests.unit.helpers import memory


@pytest.fixture
def svc():
    products = memory(
        [
            {"cCode": "PAIN", "cDescFR": "Pain", "cStockUOM": "UN", "lLotControl": True, "lSerialControl": False},
            {"cCode": "CADRE", "cDescFR": "Cadre", "cStockUOM": "UN", "lLotControl": False, "lSerialControl": True},
            {"cCode": "VIS", "cDescFR": "Vis", "cStockUOM": "BTE", "lLotControl": False, "lSerialControl": False},
        ]
    )
    refs = {"products": products.get, "setup_families": memory([{"cCode": "FOOD-PLAIN"}]).get}
    registry = ReferenceRegistry()
    return ProductMfgService(memory([], keys=("cProduct",)), refs, registry), registry


def code_of(fn, *args):
    with pytest.raises(AppError) as e:
        fn(*args)
    return e.value.code, e.value.field


def test_create_and_view(svc):
    s, registry = svc
    row = s.create(
        {
            "cProduct": "pain",
            "cSetupFamily": "food-plain",
            "dMfgLotMin": "200",
            "dMfgLotMultiple": "100",
            "attributes": [{"cAttribute": " Poids ", "cUOM": "g", "dNumber": "675"}, {"cAttribute": ""}],
        }
    )
    assert (row["cProduct"], row["cMakeBuy"], row["cTraceLevel"], row["cSetupFamily"]) == (
        "PAIN",
        "make",
        "lot",
        "FOOD-PLAIN",
    )
    assert row["attributes"] == [{"cAttribute": "Poids", "cUOM": "g", "dNumber": "675", "cValue": ""}]
    v = s.view(s.get("PAIN"), full=False)
    assert (v["cDescFR"], v["cStockUOM"], v["iAttributes"]) == ("Pain", "UN", 1)
    assert registry.is_used("setup_family", "food-plain") and s.is_made("PAIN")


@pytest.mark.parametrize(
    "body, error",
    [
        ({"cProduct": ""}, ("required", "cProduct")),
        ({"cProduct": "NOPE"}, ("unknown_ref", "cProduct")),
        ({"cProduct": "PAIN", "cSetupFamily": "ZZ"}, ("unknown_ref", "cSetupFamily")),
        ({"cProduct": "PAIN", "dMfgLotMin": "-1"}, ("negative", "dMfgLotMin")),
        ({"cProduct": "PAIN", "iMfgLeadDays": "-2"}, ("negative", "iMfgLeadDays")),
        ({"cProduct": "PAIN", "cMakeBuy": "buy", "lPhantom": True}, ("phantom_is_made", "lPhantom")),
        ({"cProduct": "VIS"}, ("lot_control_required", "cTraceLevel")),  # traced by lot by default
        ({"cProduct": "PAIN", "cTraceLevel": "serial"}, ("serial_control_required", "cTraceLevel")),
        ({"cProduct": "PAIN", "attributes": [{"cAttribute": "A"}, {"cAttribute": "a"}]}, ("duplicate", "attributes")),
    ],
)
def test_rules(svc, body, error):
    s, _r = svc
    assert code_of(s.create, body) == error


def test_trace_levels_and_buy(svc):
    s, _r = svc
    assert s.create({"cProduct": "CADRE", "cTraceLevel": "serial"})["cTraceLevel"] == "serial"
    assert s.create({"cProduct": "VIS", "cMakeBuy": "buy", "cTraceLevel": "none"})["cMakeBuy"] == "buy"
    assert not s.is_made("VIS") and not s.is_made("NOPE")


@pytest.mark.parametrize("needed, qty", [(30, 200), (200, 200), (250, 300), (0, 0)])
def test_lot_quantity(svc, needed, qty):
    s, _r = svc
    s.create({"cProduct": "PAIN", "dMfgLotMin": "200", "dMfgLotMultiple": "100"})
    assert s.lot_quantity("PAIN", needed) == qty


def test_delete_with_the_product(svc):
    s, _r = svc
    s.create({"cProduct": "PAIN"})
    s.delete_for("pain")
    s.delete_for("pain")  # nothing left: no error
    assert s.find("PAIN") is None
