"""Unit tests of the inventory services around the stock: master files, counts, replenishment."""

import pytest

from powererp.core.errors import AppError
from powererp.modules.catalog import UnitConversionService, UnitConverter, UnitService
from powererp.modules.common.registry import ReferenceRegistry
from powererp.modules.inventory.counts import CountService
from powererp.modules.inventory.masters import ProductService
from powererp.modules.inventory.replenishment import ReplenishmentService, preferred_supplier
from tests.unit.helpers import Numbering, memory, receive


def code_of(fn, *args):
    with pytest.raises(AppError) as e:
        fn(*args)
    return e.value.code, e.value.field, e.value.status


# ------------------------------------------------------------------ master files


def test_location_code_is_built_from_its_parts(inventory):
    locations = inventory["locations"]
    row = locations.create({"cWarehouse": "w1", "cZone": "b", "cAisle": "02", "cBin": "3"})
    assert (row["cWarehouse"], row["cCode"]) == ("W1", "B-02-3")
    assert code_of(locations.create, {"cWarehouse": "W9", "cCode": "X"}) == ("unknown_ref", "cWarehouse", 400)
    assert code_of(locations.create, {"cWarehouse": "W1"}) == ("required", "cCode", 400)


def test_a_location_or_warehouse_with_stock_cannot_be_deleted(inventory):
    receive(inventory["stock"])
    assert code_of(inventory["locations"].delete, ["W1", "A-1"])[0] == "in_use"
    assert code_of(inventory["warehouses"].delete, ["W1"])[0] == "in_use"
    inventory["locations"].delete(["W1", "A-2"])  # empty: fine


def test_deleting_a_warehouse_removes_its_locations_and_parameters(inventory):
    inventory["params"].create({"cProduct": "P1", "cWarehouse": "W1", "dMinQty": "1"})
    inventory["warehouses"].delete(["W1"])
    assert inventory["repos"]["locations"].rows == [] and inventory["repos"]["stock_params"].rows == []


def test_warehouse_receiving_location_must_exist(inventory):
    assert code_of(inventory["warehouses"].update, ["W1"], {"cReceivingLoc": "Z-9"})[1] == "cReceivingLoc"
    assert inventory["warehouses"].update(["W1"], {"cReceivingLoc": "A-1"})["cReceivingLoc"] == "A-1"


@pytest.fixture
def products():
    refs = {
        "categories": memory([{"cCode": "HW"}]).get,
        "uom": memory([{"cCode": "UN"}, {"cCode": "EA"}, {"cCode": "BX"}]).get,  # UN: the default unit
        "tax_groups": memory([{"cCode": "QC"}]).get,
        "warehouses": memory([{"cCode": "W1"}]).get,
        "suppliers": lambda: [{"cCode": "LUM"}],
    }
    return ProductService(memory([]), refs)


def test_product_references(products):
    row = products.create(
        {
            "cCode": "P9",
            "cDescFR": "Boulon",
            "cType": "stock",
            "cStockUOM": "EA",
            "cPurchaseUOM": "BX",
            "lines": [{"cSupplierCode": "lum", "dPurchasePrice": "3"}, {"cSupplierCode": ""}],
        }
    )
    assert "dPurchaseFactor" not in row and row["cSalesUOM"] == "UN" and row["lines"][0]["cSupplierCode"] == "LUM"
    assert row["lines"][0]["cCurrency"] == "CAD" and len(row["lines"]) == 1
    base = {"cCode": "P8", "cDescFR": "x", "cStockUOM": "EA"}
    assert code_of(products.create, {**base, "cStockUOM": ""}) == ("required", "cStockUOM", 400)
    assert code_of(products.create, {**base, "cCategory": "NOPE"}) == ("unknown_ref", "cCategory", 400)
    assert code_of(products.create, {**base, "cSalesTaxGroup": "ON"}) == ("unknown_ref", "cSalesTaxGroup", 400)
    assert code_of(products.create, {**base, "lines": [{"cSupplierCode": "ZZ"}]})[:2] == ("unknown_ref", "lines")


def test_a_service_is_never_stocked(products):
    row = products.create({"cCode": "S1", "cDescFR": "Pose", "cNature": "service", "cStockUOM": "EA", "lStocked": True})
    assert (row["lStocked"], row["cStockType"], row["cClass"]) == (False, "nonphysical", "")


def test_only_a_physical_product_is_stocked(products):
    base = {"cDescFR": "Licence", "cStockUOM": "EA", "lStocked": True}
    licence = products.create({**base, "cCode": "LIC1", "cStockType": "nonphysical", "cClass": "consumable"})
    assert (licence["lStocked"], licence["cNature"], licence["cClass"]) == (False, "product", "consumable")
    chair = products.create({**base, "cCode": "CHAIR", "cDescFR": "Chaise", "cClass": "asset"})
    assert (chair["lStocked"], chair["cStockType"], chair["cClass"]) == (True, "physical", "asset")
    assert code_of(products.create, {**base, "cCode": "X", "cStockType": "digital"})[:2] == (
        "invalid_choice",
        "cStockType",
    )


def test_stock_parameters(inventory):
    params = inventory["params"]
    row = params.create({"cProduct": "p1", "cWarehouse": "w1", "dMinQty": "5", "dMaxQty": "20"})
    assert (row["cProduct"], row["cWarehouse"]) == ("P1", "W1")
    assert code_of(params.update, ["P1", "W1"], {"dMaxQty": "2"}) == ("max_below_min", "dMaxQty", 400)
    assert code_of(params.update, ["P1", "W1"], {"cDefaultLocation": "Z-1"})[1] == "cDefaultLocation"
    assert code_of(params.create, {"cProduct": "NOPE", "cWarehouse": "W1"})[1] == "cProduct"


# ------------------------------------------------------------------ counts


@pytest.fixture
def counts(inventory):
    receive(inventory["stock"], "P1", "10", "A-1")
    receive(inventory["stock"], "P2", "4", "A-2")
    return CountService(
        memory([], keys=("iNo",)), inventory["stock"], inventory["repos"]["warehouses"], Numbering(), lambda: "tester"
    )


def test_count_sheet_is_built_from_the_stock(counts):
    sheet = counts.create({"cWarehouse": "w1"})
    assert sheet["iNo"] == 1 and sheet["cUser"] == "tester" and sheet["cStatus"] == "Draft"
    assert [(ln["cProduct"], ln["cLocation"], ln["dQtyExpected"]) for ln in sheet["lines"]] == [
        ("P1", "A-1", "10"),
        ("P2", "A-2", "4"),
    ]
    only = counts.create({"cWarehouse": "W1", "cLocationPrefix": "a-2"})
    assert [ln["cProduct"] for ln in only["lines"]] == ["P2"]


def test_posting_a_count_moves_only_the_differences(counts, inventory):
    sheet = counts.create({"cWarehouse": "W1"})
    lines = [{**ln, "dQtyCounted": q} for ln, q in zip(sheet["lines"], ("8", "4"), strict=True)]
    counts.update(sheet["iNo"], {"lines": lines})
    assert CountService.view(counts.get(sheet["iNo"]))["lines"][0]["dDiff"] == "-2"
    posted = counts.post(sheet["iNo"])
    assert posted["cStatus"] == "Posted" and len(posted["movements"]) == 1  # P2 was right: no movement
    assert inventory["stock"].product_totals("P1")[0] == 8
    assert code_of(counts.update, sheet["iNo"], {"cDescription": "late"}) == ("posted", None, 409)
    assert code_of(counts.post, sheet["iNo"])[0] == "posted"


def test_a_count_without_counted_quantity_cannot_be_posted(counts):
    sheet = counts.create({"cWarehouse": "W1"})
    assert code_of(counts.post, sheet["iNo"]) == ("nothing_counted", "lines", 400)


def test_count_lines_must_name_known_products(counts):
    assert code_of(counts.create, {"cWarehouse": "W1", "lines": [{"cProduct": "ZZ", "cLocation": "A-1"}]})[:2] == (
        "unknown_ref",
        "lines",
    )


# ------------------------------------------------------------------ replenishment


class Suppliers:
    def list(self):
        return [{"cCode": "LUM", "cName": "Lumen"}]


class PurchaseOrders:
    def __init__(self, on_order=0.0):
        self.on_order = on_order

    def quantity_on_order(self, code):
        return self.on_order


def converter(conversions=()):
    units = UnitService(memory([{"cCode": c} for c in ("UN", "EA", "BX", "CS", "DZ")]), ReferenceRegistry())
    return UnitConverter(UnitConversionService(memory(list(conversions), keys=("cFromUOM", "cToUOM")), units))


def test_purchase_and_sales_units_must_convert_to_the_stock_unit(products):
    general = {"cFromUOM": "DZ", "cToUOM": "EA", "dFactor": "12", "cNotes": "", "lActive": True}
    products.refs["unit_factor"] = converter([general]).factor
    base = {"cCode": "P7", "cDescFR": "x", "cStockUOM": "EA", "cPurchaseUOM": "BX", "cSalesUOM": "EA"}
    assert code_of(products.create, base) == ("no_conversion", "cPurchaseUOM", 400)
    assert code_of(products.create, {**base, "cPurchaseUOM": "EA", "cSalesUOM": "UN"})[:2] == (
        "no_conversion",
        "cSalesUOM",
    )
    # the product's own conversion (1 BX = 12 EA) or a general one (1 DZ = 12 EA) is enough
    assert products.missing_conversions({**base, "conversions": [{"cUOM": "BX", "dFactor": "12"}]}) == []
    assert products.missing_conversions({**base, "cPurchaseUOM": "DZ"}) == []
    assert products.missing_conversions({**base, "cSalesUOM": "BX"}) == ["cPurchaseUOM", "cSalesUOM"]
    row = products.create({**base, "conversions": [{"cUOM": "BX", "dFactor": "12", "cNotes": ""}]})
    assert row["conversions"][0]["cUOM"] == "BX"


def replenishment(inventory, on_order=0.0):
    return ReplenishmentService(
        inventory["stock"],
        inventory["repos"]["stock_params"],
        Suppliers(),
        PurchaseOrders(on_order),
        None,
        lambda: "t",
        converter().factor,
    )


@pytest.fixture
def stocked(inventory):
    products = inventory["repos"]["products"]
    p1 = products.get("P1")
    p1.update(
        {
            "cStatus": "active",
            "cDefaultWarehouse": "W1",
            "cStockUOM": "UN",
            "cPurchaseUOM": "CS",
            "conversions": [{"cUOM": "CS", "dFactor": "6", "cNotes": ""}],  # a case of 6, bought by the case
            "lines": [
                {"cSupplierCode": "OTHER", "dPurchasePrice": "50"},
                {"cSupplierCode": "LUM", "lPreferred": True, "dPurchasePrice": "30", "dMinOrderQty": ""},
            ],
        }
    )
    products.update(p1)
    receive(inventory["stock"], "P1", "4")
    inventory["params"].create({"cProduct": "P1", "cWarehouse": "W1", "dReorderPoint": "5", "dMaxQty": "20"})
    return inventory


def test_suggestion_up_to_the_maximum_in_purchase_units(stocked):
    [row] = replenishment(stocked).rows()
    # 4 available, max 20 -> 16 needed -> 3 cases of 6 (18 units) from the preferred supplier
    assert (row["dQtyAvailable"], row["dPurchaseQty"], row["dSuggestedQty"]) == ("4", "3", "18")
    assert (row["cSupplierCode"], row["cSupplierName"], row["dUnitCost"]) == ("LUM", "Lumen", "30.00")


def test_open_purchase_orders_count_as_coming_stock(stocked):
    assert replenishment(stocked, on_order=1).rows()[0]["dPurchaseQty"] == "3"  # 5 projected -> 15 -> 3 cases
    assert replenishment(stocked, on_order=2).rows() == []  # 6 projected: above the reorder point


def test_preferred_supplier():
    assert (
        preferred_supplier({"lines": [{"cSupplierCode": "A"}, {"cSupplierCode": "B", "lPreferred": True}]})[
            "cSupplierCode"
        ]
        == "B"
    )
    assert preferred_supplier({"lines": [{"cSupplierCode": "A"}]})["cSupplierCode"] == "A"
    assert preferred_supplier({}) is None
