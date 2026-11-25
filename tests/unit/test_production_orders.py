"""Unit tests of the production orders (M3a), on memory repositories: recipe, explosion, life of an order."""

import pytest

from powererp.core.errors import AppError
from powererp.modules.common.registry import ReferenceRegistry
from powererp.modules.production.orders import ProductionOrderService
from powererp.modules.production.recipe_flow import RecipeFlow
from powererp.modules.production.recipes import RecipeService
from tests.unit.helpers import Numbering, memory
from tests.unit.test_production_recipes import BREAD, LISTS

PRODUCTS = LISTS["products"] + [{"cCode": "BOIS", "cDescFR": "Bois", "cStockUOM": "UN"}]
MFG = LISTS["product_mfg"] + [{"cProduct": "BOIS", "cMakeBuy": "buy"}]
WAREHOUSES = [{"cCode": "W1"}, {"cCode": "W2"}]


class Stock:
    """Stand-in of the stock service: the balances by (product, warehouse, location, lot, serial)."""

    def __init__(self, rows):
        self.rows = rows

    def balances(self):
        return self.rows


@pytest.fixture
def world():
    keys = {"product_mfg": ("cProduct",)}
    lists = {**LISTS, "products": PRODUCTS, "product_mfg": MFG}
    refs = {k: memory(v, keys=keys.get(k, ("cCode",))).get for k, v in lists.items()}
    recipes = RecipeService(memory([], keys=("cProduct", "cRevision")), refs, ReferenceRegistry())
    flow = RecipeFlow(recipes, lambda: "marie", lambda: True)
    recipes.create(BREAD)
    flow.submit("PAIN", "A")
    flow.approve("PAIN", "A")
    stock = Stock(
        {
            ("FARINE", "W1", "A-1", "L1", ""): {"qty": 50.0, "reserved": 10.0},
            ("FARINE", "W1", "A-2", "L0", ""): {"qty": 99.0, "reserved": 0.0, "dExpiry": "2000-01-01"},  # expired
            ("SAC", "W1", "A-1", "", ""): {"qty": 500.0, "reserved": 0.0},
        }
    )
    order_refs = {
        "products": refs["products"],
        "product_mfg": refs["product_mfg"],
        "warehouses": memory(WAREHOUSES).get,
        "recipes": recipes,
        "current_recipe": flow.current,
        "stock": lambda: stock,
    }
    references = ReferenceRegistry()
    svc = ProductionOrderService(memory([], keys=("iNo",)), order_refs, Numbering(), lambda: "paul", references)
    return svc, recipes, flow, references


def error_of(fn, *args):
    with pytest.raises(AppError) as e:
        fn(*args)
    return e.value.code, e.value.field


def test_create_explodes_the_approved_recipe(world):
    svc, recipes, _flow, _refs = world
    o = svc.create({"cProduct": "pain", "dQty": "400", "cWarehouse": "w1", "dStart": "2026-12-01"})
    assert (o["iNo"], o["cProduct"], o["cRevision"], o["cWarehouse"], o["cUOM"], o["cUser"]) == (
        1,
        "PAIN",
        "A",
        "W1",
        "UN",
        "paul",
    )
    e = recipes.explode("PAIN", "A", 400)
    mats = {m["cComponent"]: m for m in o["materials"]}
    assert float(mats["FARINE"]["dQtyRequired"]) == pytest.approx(170)  # 85 per 200
    assert float(o["dEstCost"]) == pytest.approx(e["dTotalCost"], abs=0.01)
    # available = on hand - reserved, the expired lot does not count
    assert (float(mats["FARINE"]["dAvailable"]), float(mats["FARINE"]["dShort"])) == (40, 130)
    assert float(mats["SAC"]["dShort"]) == 0
    assert o["lShort"] is True
    assert [h["cAction"] for h in o["history"]] == ["created"]


@pytest.mark.parametrize(
    "payload, error",
    [
        ({"dQty": "1", "cWarehouse": "W1"}, ("required", "cProduct")),
        ({"cProduct": "NOPE", "dQty": "1", "cWarehouse": "W1"}, ("unknown_ref", "cProduct")),
        ({"cProduct": "BOIS", "dQty": "1", "cWarehouse": "W1"}, ("not_made", "cProduct")),
        ({"cProduct": "VIS", "dQty": "1", "cWarehouse": "W1"}, ("no_approved_recipe", "cProduct")),
        ({"cProduct": "PAIN", "cRevision": "Z", "dQty": "1", "cWarehouse": "W1"}, ("unknown_ref", "cRevision")),
        ({"cProduct": "PAIN", "dQty": "0", "cWarehouse": "W1"}, ("positive", "dQty")),
        ({"cProduct": "PAIN", "dQty": "", "cWarehouse": "W1"}, ("required", "dQty")),
        ({"cProduct": "PAIN", "dQty": "1"}, ("required", "cWarehouse")),
        ({"cProduct": "PAIN", "dQty": "1", "cWarehouse": "W9"}, ("unknown_ref", "cWarehouse")),
        (
            {"cProduct": "PAIN", "dQty": "1", "cWarehouse": "W1", "dStart": "2026-12-02", "dDue": "2026-12-01"},
            ("end_before_start", "dDue"),
        ),
    ],
)
def test_create_refused(world, payload, error):
    svc = world[0]
    assert error_of(svc.create, payload) == error


def test_a_revision_must_be_approved(world):
    svc, recipes, _flow, _refs = world
    recipes.create({**BREAD, "cRevision": "B"})
    assert error_of(svc.create, {"cProduct": "PAIN", "cRevision": "B", "dQty": "1", "cWarehouse": "W1"}) == (
        "no_approved_recipe",
        "cRevision",
    )


def test_preview_takes_the_base_quantity_and_saves_nothing(world):
    svc = world[0]
    p = svc.preview({"cProduct": "PAIN", "cWarehouse": "W1"})
    assert p["dQty"] == "200" and p["materials"] and p["iNo"] == 0
    assert svc.preview({})["materials"] == []
    assert svc.list() == []


def test_life_of_an_order(world):
    svc = world[0]
    no = svc.create({"cProduct": "PAIN", "dQty": "200", "cWarehouse": "W1"})["iNo"]
    assert float(svc.update(no, {"dQty": "400"})["materials"][0]["dQtyRequired"]) == pytest.approx(170)
    r = svc.move(no, "release", "go")
    assert (r["cStatus"], r["cReleasedBy"]) == ("released", "paul") and r["dReleased"]
    assert error_of(svc.update, no, {"dQty": "1"})[0] == "invalid_status"  # only a draft is changed
    assert error_of(svc.delete, no)[0] == "invalid_status"
    assert error_of(svc.move, no, "release")[0] == "invalid_status"
    r = svc.move(no, "unrelease")
    assert (r["cStatus"], r["dReleased"], r["cReleasedBy"]) == ("draft", "", "")
    r = svc.move(no, "cancel", "no flour")
    assert r["cStatus"] == "cancelled"
    assert [(h["cAction"], h["cFrom"], h["cTo"], h["cComment"]) for h in r["history"]] == [
        ("created", "", "draft", ""),
        ("release", "draft", "released", "go"),
        ("unrelease", "released", "draft", ""),
        ("cancel", "draft", "cancelled", "no flour"),
    ]
    assert error_of(svc.move, no, "nope")[0] == "not_found"


def test_nothing_moves_once_stock_moved(world):
    svc = world[0]
    o = svc.create({"cProduct": "PAIN", "dQty": "200", "cWarehouse": "W1"})
    o["materials"][0]["dQtyIssued"] = "1"
    svc.repo.update(o, [o["iNo"]])
    assert error_of(svc.move, o["iNo"], "cancel")[0] == "invalid_status"


def test_release_checks_the_recipe_again(world):
    svc, _recipes, flow, _refs = world
    no = svc.create({"cProduct": "PAIN", "dQty": "200", "cWarehouse": "W1"})["iNo"]
    flow.obsolete("PAIN", "A")
    assert error_of(svc.move, no, "release")[0] == "no_approved_recipe"


def test_references(world):
    svc, _recipes, _flow, refs = world
    svc.create({"cProduct": "PAIN", "dQty": "200", "cWarehouse": "W1"})
    assert svc._uses_product("sac") and svc._uses_product("PAIN") and not svc._uses_product("VIS")
    assert svc._uses("cWarehouse", "w1") and not svc._uses("cWarehouse", "W2")
