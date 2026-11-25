"""Unit tests of the stock rules on memory repositories and a memory ledger (no Flask, no database)."""

import pytest

from powererp.core.errors import AppError
from powererp.modules.common.memory import MemoryRepository
from powererp.modules.inventory import build_services
from powererp.modules.inventory.costing import StandardCosting, costing_of


@pytest.fixture
def svc():
    from powererp.modules.inventory.ledger import MemoryLedger

    repos = {
        "warehouses": MemoryRepository([{"cCode": "W1", "lUseLocations": True, "lAllowNegative": False}]),
        "locations": MemoryRepository(
            [
                {"cWarehouse": "W1", "cCode": "A-1", "lActive": True, "lMixProducts": True},
                {"cWarehouse": "W1", "cCode": "B-1", "lActive": True, "lMixProducts": False},
                {"cWarehouse": "W1", "cCode": "X-1", "lActive": True, "lBlocked": True},
            ],
            keys=("cWarehouse", "cCode"),
        ),
        "products": MemoryRepository(
            [
                {"cCode": "P1", "lStocked": True, "cCostMethod": "avg", "dAvgCost": "", "dLastCost": "", "lines": []},
                {"cCode": "P2", "lStocked": True, "cCostMethod": "avg", "dAvgCost": "", "lines": []},
                {"cCode": "SVC", "lStocked": False},
            ]
        ),
        "stock_params": MemoryRepository([], keys=("cProduct", "cWarehouse")),
    }
    return build_services(repos, MemoryLedger(), {}, username=lambda: "tester")["stock"]


def move(svc, **kw):
    return svc.add({"cType": "IN", "cProduct": "P1", "dQty": "1", "cWarehouse": "W1", "cLocation": "A-1", **kw})


def test_moving_average_cost(svc):
    move(svc, dQty="10", dUnitCost="2")
    move(svc, dQty="10", dUnitCost="4")
    p1 = svc.products_repo.get("P1")
    assert (p1["dAvgCost"], p1["dLastCost"]) == ("3.00", "4.00")
    out = move(svc, cType="OUT", dQty="5")
    assert (out["dUnitCost"], out["dValue"], out["cUser"]) == ("3.00", "-15.00", "tester")
    assert svc.product_totals("P1") == (15.0, 0.0)


def test_no_negative_stock_and_reservations(svc):
    move(svc, dQty="3")
    with pytest.raises(AppError) as e:
        move(svc, cType="OUT", dQty="4")
    assert (e.value.code, e.value.detail) == ("insufficient_stock", "3")
    move(svc, cType="RSV", dQty="2")
    with pytest.raises(AppError):
        move(svc, cType="OUT", dQty="2")  # only 1 available
    with pytest.raises(AppError) as e:
        move(svc, cType="RSV", dQty="-3")
    assert e.value.code == "insufficient_reserved"


def test_location_rules(svc):
    with pytest.raises(AppError) as e:
        move(svc, cLocation="")
    assert (e.value.code, e.value.field) == ("required", "cLocation")
    with pytest.raises(AppError) as e:
        move(svc, cLocation="X-1")
    assert e.value.code == "blocked_location"
    move(svc, cLocation="B-1")
    with pytest.raises(AppError) as e:
        move(svc, cProduct="P2", cLocation="B-1")
    assert e.value.code == "location_mixed"
    with pytest.raises(AppError) as e:
        move(svc, cProduct="SVC")
    assert e.value.code == "not_stocked"


def test_one_lot_of_a_product_per_location(svc):
    move(svc, dQty="5", cLot="L1")
    move(svc, dQty="2", cLot="l1")  # the same lot (case does not matter)
    move(svc, cProduct="P2", cLot="K9")  # another product, with its own lot: fine
    for kw in ({"cLot": "L2"}, {"cType": "ADJ", "cLot": "L2"}, {"cType": "CNT", "cLot": ""}):
        with pytest.raises(AppError) as e:
            move(svc, **kw)
        assert (e.value.code, e.value.field, e.value.detail) == ("location_mixed_lots", "cLocation", "L1")
    move(svc, cLot="L2", cLocation="B-1")  # another location
    with pytest.raises(AppError) as e:
        move(svc, cType="TRF", cLot="L2", cLocation="B-1", cWhTo="W1", cLocTo="A-1")
    assert (e.value.code, e.value.field) == ("location_mixed_lots", "cLocTo")
    move(svc, cType="OUT", dQty="7", cLot="L1")  # A-1 has no more L1: L2 can come in
    move(svc, cType="TRF", cLot="L2", cLocation="B-1", cWhTo="W1", cLocTo="A-1")
    assert svc.quantity_at("W1", "A-1") == 2


def test_transfer_moves_quantity_without_value(svc):
    move(svc, dQty="5", dUnitCost="1")
    t = move(svc, cType="TRF", dQty="2", cWhTo="W1", cLocTo="B-1")
    assert t["dValue"] == "0.00"
    assert svc.quantity_at("W1", "A-1") == 3 and svc.quantity_at("W1", "B-1") == 2


def test_costing_strategies():
    assert isinstance(costing_of({"cCostMethod": "std"}), StandardCosting)
    assert costing_of({"cCostMethod": "std", "dStdCost": "9", "dAvgCost": "3"}).unit_cost({"dStdCost": "9"}) == 9
    assert costing_of({"cCostMethod": "avg", "dAvgCost": "3"}).unit_cost({"dAvgCost": "3"}) == 3
