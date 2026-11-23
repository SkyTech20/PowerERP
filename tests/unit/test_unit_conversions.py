"""Unit tests of the unit conversions: the general ones (1 KG = 1000 G), those of a product (1 BAG = 25 KG),
the converter that chains them, and their use by the recipes (a material in G of a product stocked in KG)."""

import pytest

from powererp.core.errors import AppError
from powererp.modules.catalog import STANDARD_CONVERSIONS, UnitConversionService, UnitConverter, UnitService
from powererp.modules.common.registry import ReferenceRegistry
from powererp.modules.production.recipes import RecipeService
from tests.unit.helpers import memory

UNITS = [
    {"cCode": c, "cDescFR": c, "cType": "weight", "lActive": True} for c in ("KG", "G", "LB", "UN", "BAG", "M", "REEL")
]
CONVERSIONS = [
    {"cFromUOM": "KG", "cToUOM": "G", "dFactor": "1000", "cNotes": "", "lActive": True},
    {"cFromUOM": "LB", "cToUOM": "KG", "dFactor": "0.45359237", "cNotes": "", "lActive": True},
    {"cFromUOM": "M", "cToUOM": "G", "dFactor": "1", "cNotes": "inactive: never used", "lActive": False},
]
FLOUR = {"cCode": "FLOUR", "cStockUOM": "KG", "conversions": [{"cUOM": "BAG", "dFactor": "25", "cNotes": ""}]}
WIRE = {"cCode": "WIRE", "cStockUOM": "M", "conversions": [{"cUOM": "REEL", "dFactor": "25", "cNotes": ""}]}


def code_of(fn, *args):
    with pytest.raises(AppError) as e:
        fn(*args)
    return e.value.code, e.value.field


@pytest.fixture
def conv():
    refs = ReferenceRegistry()
    units = UnitService(memory(UNITS), refs)
    service = UnitConversionService(memory(CONVERSIONS, keys=("cFromUOM", "cToUOM")), units)
    return service, UnitConverter(service), refs


def test_general_conversions_both_ways_and_in_a_chain(conv):
    _s, c, _r = conv
    assert c.factor("KG", "G") == 1000
    assert c.factor("g", "kg") == pytest.approx(0.001)  # the reverse is deduced, codes ignore case
    assert c.factor("LB", "G") == pytest.approx(453.59237)  # LB -> KG -> G
    assert c.factor("KG", "KG") == 1
    assert c.factor("M", "G") is None  # an inactive conversion is not used
    assert c.factor("KG", "UN") is None
    assert c.factor("", "KG") is None


def test_the_units_of_a_product(conv):
    _s, c, _r = conv
    assert c.factor("BAG", "KG", FLOUR) == 25
    assert c.factor("BAG", "G", FLOUR) == pytest.approx(25000)  # its bag, then the general KG -> G
    assert c.factor("G", "BAG", FLOUR) == pytest.approx(1 / 25000)
    assert c.factor("BAG", "KG") is None  # a bag is a unit of the flour only
    assert c.factor("REEL", "M", WIRE) == 25
    assert c.to_stock(2, "REEL", WIRE) == 50


def test_conversion_rules(conv):
    s, _c, _r = conv
    assert code_of(s.create, {"cFromUOM": "KG", "cToUOM": "kg", "dFactor": "1"}) == ("same_unit", "cToUOM")
    assert code_of(s.create, {"cFromUOM": "KG", "cToUOM": "TON", "dFactor": "1"}) == ("unknown_ref", "cToUOM")
    assert code_of(s.create, {"cFromUOM": "BAG", "cToUOM": "KG", "dFactor": "0"}) == ("positive", "dFactor")
    assert code_of(s.create, {"cFromUOM": "G", "cToUOM": "KG", "dFactor": "0.001"}) == ("conversion_exists", "cToUOM")
    row = s.create({"cFromUOM": "bag", "cToUOM": "kg", "dFactor": "25"})
    assert (row["cFromUOM"], row["cToUOM"]) == ("BAG", "KG")  # the codes of the units


def test_a_unit_used_by_a_conversion_is_not_deleted(conv):
    s, _c, refs = conv
    assert refs.is_used("uom", "lb")
    assert not refs.is_used("uom", "UN")
    assert code_of(s.units.delete, ["G"])[0] == "in_use"


def test_standard_conversions_add_what_is_missing_once(conv):
    s, c, _r = conv
    first = s.add_standard()
    assert first["iUnits"] > 0
    assert first["iConversions"] == len(STANDARD_CONVERSIONS) - 1  # KG -> G was there already
    assert s.add_standard() == {"iUnits": 0, "iConversions": 0}
    assert c.factor("DZ", "UN") == 12
    assert c.factor("L", "ML") == 1000


# ---------------------------------------------------------- recipes
PRODUCTS = [
    {"cCode": "DOUGH", "cDescFR": "Pâte", "cStockUOM": "KG"},
    {**FLOUR, "cDescFR": "Farine", "dStdCost": "2.00"},  # 2.00 / KG
    {"cCode": "EGG", "cDescFR": "Oeuf", "cStockUOM": "UN", "dStdCost": "0.30"},
]


@pytest.fixture
def recipes(conv):
    _s, c, _r = conv
    lists = {"products": PRODUCTS, "product_mfg": [{"cProduct": "DOUGH", "cMakeBuy": "make"}]}
    keys = {"product_mfg": ("cProduct",)}
    refs = {k: memory(v, keys=keys.get(k, ("cCode",))).get for k, v in lists.items()}
    for k in ("operations", "work_centers", "resources", "capabilities", "suppliers"):
        refs[k] = memory([]).get
    refs["unit_factor"] = c.factor
    return RecipeService(memory([], keys=("cProduct", "cRevision")), refs, ReferenceRegistry())


def test_a_material_in_grams_costs_and_leaves_the_stock_in_kilograms(recipes):
    recipes.create(
        {
            "cProduct": "DOUGH",
            "dBaseQty": "1",
            "materials": [
                {"cComponent": "FLOUR", "dQtyPer": "600", "cUOM": "G"},
                {"cComponent": "EGG", "dQtyPer": "2"},
            ],
        }
    )
    e = recipes.explode("DOUGH", "A", 10)
    flour, egg = e["materials"]
    assert (flour["dQty"], flour["cUOM"], flour["dStockQty"], flour["cStockUOM"]) == (6000, "G", 6, "KG")
    assert flour["dUnitCost"] == pytest.approx(0.002)  # per gram
    assert flour["dStockUnitCost"] == 2  # per KG
    assert flour["dCost"] == 12  # 6 KG x 2.00, not 6000 x 2.00
    assert (egg["cUOM"], egg["dStockQty"], egg["dCost"]) == ("UN", 20, 6)
    assert e["dMaterialCost"] == 18


def test_a_material_in_the_bag_of_the_product(recipes):
    recipes.create(
        {"cProduct": "DOUGH", "dBaseQty": "50", "materials": [{"cComponent": "FLOUR", "dQtyPer": "1", "cUOM": "BAG"}]}
    )
    m = recipes.explode("DOUGH", "A", 50)["materials"][0]
    assert (m["dStockQty"], m["dCost"]) == (25, 50)


def test_a_unit_without_conversion_is_refused(recipes):
    bad = {"cProduct": "DOUGH", "materials": [{"cComponent": "EGG", "dQtyPer": "1", "cUOM": "KG"}]}
    assert code_of(recipes.create, bad) == ("no_conversion", "materials")
    assert code_of(recipes.create, {"cProduct": "DOUGH", "cUOM": "UN"}) == ("no_conversion", "cUOM")
