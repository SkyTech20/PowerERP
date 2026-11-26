"""Unit tests of the lot status service (quality, step 5): a lot without a row is released, the list of the lots,
the held lots the pick order leaves out."""

import pytest

from powererp.core.errors import AppError
from powererp.modules.quality.lots import LotStatusService


class Repo:
    def __init__(self):
        self.rows = []

    def all(self, lines=True, where=None):
        return [dict(r) for r in self.rows]

    def get(self, product, lot):
        return next(
            (
                dict(r)
                for r in self.rows
                if (r["cProduct"].upper(), r["cLot"].upper()) == (product.upper(), lot.upper())
            ),
            None,
        )

    def insert(self, row):
        self.rows.append(dict(row))

    def update(self, row, keys):
        self.rows = [
            row if (r["cProduct"].upper(), r["cLot"].upper()) == (keys[0].upper(), keys[1].upper()) else r
            for r in self.rows
        ]


class Ledger:
    def all(self):
        return [
            {"cProduct": "P1", "cLot": "A", "dExpiry": "2027-01-01"},
            {"cProduct": "P1", "cLot": "B", "dExpiry": ""},
            {"cProduct": "P2", "cLot": "", "dExpiry": ""},
        ]


class Stock:
    ledger = Ledger()

    def balances(self):
        return {
            ("P1", "W1", "L1", "A", ""): {"qty": 4.0, "reserved": 0.0},
            ("P1", "W1", "L2", "A", ""): {"qty": 1.0, "reserved": 0.0},
            ("P1", "W1", "L3", "B", ""): {"qty": 0.0, "reserved": 0.0},
        }


@pytest.fixture
def svc():
    products = {"P1": {"cCode": "P1", "cDescFR": "Pain", "cStockUOM": "UN"}}
    return LotStatusService(Repo(), {"stock": Stock, "products": lambda: products.get}, lambda: "ann")


def test_lots_in_stock_are_released_until_changed(svc):
    data = svc.lots({})
    assert [(r["cLot"], r["cStatus"], r["dOnHand"], r["cWhere"]) for r in data["items"]] == [
        ("A", "released", "5", "W1/L1, W1/L2")
    ]
    assert svc.held() == set() and svc.status_of("P1", "A") == "released"


def test_a_lot_used_up_shows_while_it_is_not_released(svc):
    svc.change("p1", "b", "rejected", "mould")
    data = svc.lots({"status": "blocked"})
    assert [(r["cLot"], r["cStatus"], r["cUser"]) for r in data["items"]] == [("B", "rejected", "ann")]
    assert data["counts"] == {"released": 1, "on_hold": 0, "quarantine": 0, "rejected": 1}
    assert svc.held() == {("P1", "B")}


def test_changes_are_checked(svc):
    with pytest.raises(AppError) as e:
        svc.change("P1", "A", "on_hold", " ")
    assert e.value.field == "cReason"
    with pytest.raises(AppError) as e:
        svc.change("P1", "NONE", "on_hold", "x")
    assert e.value.code == "unknown_lot"
    svc.change("P1", "A", "on_hold", "x")
    with pytest.raises(AppError) as e:
        svc.change("P1", "A", "on_hold", "again")
    assert e.value.code == "same_status"
    assert [c["label"] for c in svc.lot_choices("p1")] == ["On hold · 2027-01-01 · 5", "0"]
    assert svc.lot_choices("P1", "fr")[0]["label"] == "En attente · 2027-01-01 · 5"
