"""Unit tests of the entry of a reception into the stock (ReceptionStockService.check), on memory repositories."""

import pytest

from powererp.core.errors import AppError
from powererp.modules.purchasing.receiving import ReceptionStockService


class Receptions:
    """Stand-in for ReceptionService: one reception, not posted."""

    def __init__(self, rec):
        self.rec = rec

    def not_posted(self, no):
        if self.rec.get("lStockPosted"):
            raise AppError("posted", status=409)
        return self.rec


def reception(lines, **over):
    return {
        "NoReception": "900107",
        "DateReception": "2026-11-21",
        "NoBonCommande": "800107",
        "CodeFournisseur": "MEATCO",
        "Entrepot": "W1",
        "Devise": "CAD",
        "lines": lines,
        **over,
    }


@pytest.fixture
def svc(inventory):
    repos = inventory["repos"]
    wh = repos["warehouses"].get("W1")
    repos["warehouses"].update({**wh, "cReceivingLoc": "A-2"})
    p1 = repos["products"].get("P1")
    repos["products"].update(
        {**p1, "lLotControl": True, "lExpiryControl": True, "iShelfLifeDays": 10, "cStockUOM": "KG"}
    )
    repos["stock_params"].rows.append({"cProduct": "P1", "cWarehouse": "W1", "cDefaultLocation": "A-1"})

    def make(rec):
        return ReceptionStockService(Receptions(rec), lambda: inventory["stock"], lambda: "tester")

    return make


def test_lot_expiry_and_location_are_proposed(svc):
    res = svc(reception([{"CodeArticle": "P1", "QuantiteRecue": "5", "PrixUnitaire": "3"}])).check("900107")
    assert res["ok"], res["problems"]
    e = res["entries"][0]
    assert (e["cLot"], e["dExpiry"], e["cLocation"], e["cUOM"]) == ("900107-1", "2026-12-01", "A-1", "KG")
    assert e["cDescription"] == "Vis"  # the product's when the line has none


def test_default_location_with_another_lot_gives_way_to_receiving(svc, inventory):
    inventory["stock"].add(
        {"cType": "IN", "cProduct": "P1", "dQty": "1", "cWarehouse": "W1", "cLocation": "A-1", "cLot": "OLD"}
        | {"dExpiry": "2027-01-01"}
    )
    res = svc(reception([{"CodeArticle": "P1", "QuantiteRecue": "5", "PrixUnitaire": "3"}])).check("900107")
    assert res["ok"] and res["entries"][0]["cLocation"] == "A-2"


def test_typed_location_is_not_changed(svc, inventory):
    inventory["stock"].add(
        {"cType": "IN", "cProduct": "P1", "dQty": "1", "cWarehouse": "W1", "cLocation": "A-1", "cLot": "OLD"}
        | {"dExpiry": "2027-01-01"}
    )
    line = {"CodeArticle": "P1", "QuantiteRecue": "5", "PrixUnitaire": "3", "cLocation": "A-1"}
    res = svc(reception([line])).check("900107")
    assert [p["code"] for p in res["problems"]] == ["location_mixed_lots"]


def test_two_lines_of_the_same_new_lot_count_together(svc):
    lines = [
        {"CodeArticle": "P2", "QuantiteRecue": "2", "PrixUnitaire": "1", "cLocation": "A-1"},
        {"CodeArticle": "SVC", "QuantiteRecue": "1", "PrixUnitaire": "9"},
        {"CodeArticle": "P2", "QuantiteRecue": "0", "PrixUnitaire": "1"},
    ]
    res = svc(reception(lines)).check("900107")
    assert res["ok"]
    assert [e["cSkip"] for e in res["entries"]] == ["", "not_stocked", "nothing_received"]


def test_expiry_needed_without_shelf_life(svc, inventory):
    products = inventory["repos"]["products"]
    products.update({**products.get("P1"), "iShelfLifeDays": 0})
    res = svc(reception([{"CodeArticle": "P1", "QuantiteRecue": "5", "PrixUnitaire": "3"}])).check("900107")
    assert [(p["iLine"], p["code"], p["field"]) for p in res["problems"]] == [(1, "required", "dExpiry")]


def test_posted_reception_is_refused(svc):
    with pytest.raises(AppError) as e:
        svc(reception([], lStockPosted=True)).check("900107")
    assert e.value.code == "posted"
