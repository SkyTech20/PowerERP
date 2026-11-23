"""Unit tests of the price rules (V2): quantity breaks across units, category tree, validity."""

import pytest

from powererp.modules.catalog import UnitConverter
from powererp.modules.common.registry import ReferenceRegistry
from powererp.modules.sales.pricing import PriceListService, PriceResolver, is_valid_on
from tests.unit.helpers import memory

PRODUCTS = [
    {
        "cCode": "P1",
        "cCategory": "SUB",
        "cStockUOM": "UN",
        "cSalesUOM": "UN",
        "dPrice1": "10",
        "dMinPrice": "",
        "lSellable": True,
        "conversions": [{"cUOM": "CS", "dFactor": "12"}],
    }
]


class Finder:
    """What the resolver uses of a service: find(code)."""

    def __init__(self, repo):
        self.find = repo.get


class NoGeneralConversions:
    class repo:
        @staticmethod
        def all(lines=False):
            return []


@pytest.fixture
def world():
    products = memory(PRODUCTS)
    # a loop in the tree must not hang the search of a category discount
    categories = memory([{"cCode": "SUB", "cParent": "TOP"}, {"cCode": "TOP", "cParent": "SUB"}])
    converter = UnitConverter(NoGeneralConversions())  # type: ignore[arg-type]
    refs = {"products": products.get, "categories": categories.get, "converter": converter}
    lists = PriceListService(memory([]), refs, ReferenceRegistry())
    customers = memory([{"cCode": "C1", "cPriceList": "L1", "dDiscountPct": "2"}])
    return lists, PriceResolver(lists, Finder(customers), Finder(products), Finder(categories), converter)


def test_breaks_in_another_unit(world):
    lists, resolver = world
    lists.create(
        {
            "cCode": "l1",
            "cDescFR": "L1",
            "lines": [
                {"cProduct": "p1", "dPrice": "9"},
                {"cProduct": "p1", "cUOM": "cs", "dMinQty": "2", "dPrice": "96"},  # 8 per unit from 24 units
            ],
            "discounts": [{"cCategory": "top", "dDiscountPct": "10"}],
        }
    )
    assert resolver.price("C1", "P1", "23")["dPrice"] == "9.00"
    p = resolver.price("C1", "P1", "24")
    assert (p["dPrice"], p["dMinQty"], p["cDiscountCategory"], p["dNetPrice"]) == ("8.00", "2", "TOP", "7.20")
    assert resolver.price("C1", "P1", "2", "CS")["dPrice"] == "96.00"


def test_no_category_discount_in_a_loop(world):
    lists, resolver = world
    lists.create({"cCode": "l1", "cDescFR": "L1", "discounts": [{"cCategory": "sub", "dDiscountPct": "1"}]})
    lists.update(["L1"], {"discounts": []})
    p = resolver.price("C1", "P1")
    assert (p["cPriceSource"], p["cDiscountSource"], p["dNetPrice"]) == ("product", "customer", "9.80")


def test_validity():
    plist = {"lActive": True, "dStartDate": "2026-01-01", "dEndDate": "2026-12-31"}
    assert is_valid_on(plist, "2026-01-01") and is_valid_on(plist, "2026-12-31")
    assert not is_valid_on(plist, "2027-01-01") and not is_valid_on({**plist, "lActive": False}, "2026-06-01")
    assert is_valid_on({"lActive": True, "dStartDate": "", "dEndDate": ""}, "1999-01-01")
