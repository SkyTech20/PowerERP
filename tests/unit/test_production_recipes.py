"""Unit tests of the recipes (P8): rules, values from the standard operations, explosion for a quantity."""

import pytest

from powererp.core.errors import AppError
from powererp.modules.common.registry import ReferenceRegistry
from powererp.modules.production.recipes import RecipeService, parse_predecessors, prepare_demo
from tests.unit.helpers import memory


def std_op(code, fr, en, wc, cap, fmt, setup, run, crew, ifr=""):
    return {
        "cCode": code,
        "cDescFR": fr,
        "cDescEN": en,
        "cWorkCenter": wc,
        "cCapability": cap,
        "cRunFormat": fmt,
        "dSetupMin": setup,
        "dRunValue": run,
        "iCrew": crew,
        "lSubcontract": False,
        "cSupplier": "",
        "dSubcontractCost": "",
        "iSubcontractDays": 0,
        "cInstructionFR": ifr,
        "cInstructionEN": "",
    }


LISTS = {
    "products": [
        {"cCode": "PAIN", "cDescFR": "Pain", "cStockUOM": "UN"},
        {"cCode": "FARINE", "cDescFR": "Farine", "cStockUOM": "KG", "dStdCost": "0.60"},
        {"cCode": "SAC", "cDescFR": "Sac", "cStockUOM": "UN", "dAvgCost": "0.05"},
        {"cCode": "MIETTES", "cDescFR": "Miettes", "cStockUOM": "KG"},
        {"cCode": "VIS", "cDescFR": "Vis", "cStockUOM": "BTE"},
    ],
    "product_mfg": [
        {"cProduct": "PAIN", "cMakeBuy": "make", "attributes": [{"cAttribute": "Poids", "dNumber": "900"}]}
    ],
    "operations": [
        std_op("PETRIS", "Pétrissage", "Mixing", "", "MIX", "min_per_lot", "10", "12", 1, "Vérifier la cuve"),
        std_op("EMB", "Emballage", "Packing", "EMB-WC", "", "units_per_hour", "10", "600", 2),
    ],
    "work_centers": [
        {
            "cCode": "MIX-WC",
            "cType": "machine",
            "dEfficiencyPct": "100",
            "dSetupRateHr": "60",
            "dRunRateHr": "60",
            "dBurdenRateHr": "0",
        },
        {
            "cCode": "EMB-WC",
            "cType": "labor",
            "dEfficiencyPct": "100",
            "dSetupRateHr": "30",
            "dRunRateHr": "30",
            "dBurdenRateHr": "0",
        },
    ],
    "resources": [
        {
            "cCode": "PET1",
            "cWorkCenter": "MIX-WC",
            "dSpeedFactor": "1.2",
            "attributes": [{"cAttribute": "poids", "dMin": "", "dMax": "800"}],
        }
    ],
    "capabilities": [{"cCode": "MIX"}],
    "suppliers": [{"cCode": "SOUS"}],
}


@pytest.fixture
def svc():
    keys = {"product_mfg": ("cProduct",)}
    refs = {k: memory(v, keys=keys.get(k, ("cCode",))).get for k, v in LISTS.items()}
    registry = ReferenceRegistry()
    return RecipeService(memory([], keys=("cProduct", "cRevision")), refs, registry), registry


OPS = [{"iOpSeq": 20, "cOperation": "emb"}, {"iOpSeq": 10, "cOperation": "petris", "cResource": "pet1"}]
BREAD = {
    "cProduct": "pain",
    "dBaseQty": "200",
    "dMaxBatch": "200",
    "dYieldPct": "100",
    "materials": [
        {"cComponent": "farine", "dQtyPer": "85", "iOpSeq": 10},
        {"cComponent": "SAC", "dQtyPer": "200", "iOpSeq": 20, "dScrapPct": "1"},
        {"cComponent": "", "dQtyPer": "1"},
    ],
    "operations": OPS,
}


def code_of(fn, *args):
    with pytest.raises(AppError) as e:
        fn(*args)
    return e.value.code, e.value.field


def test_create_takes_the_standard_values(svc):
    s, _r = svc
    r = s.create(BREAD)
    assert (r["cProduct"], r["cRevision"], r["cStatus"], r["cUOM"], r["cDescFR"]) == (
        "PAIN",
        "A",
        "draft",
        "UN",
        "Pain",
    )
    mix, pack = r["operations"]  # sorted by sequence
    assert (mix["iOpSeq"], mix["cDescFR"], mix["cRunFormat"], mix["dRunValue"], mix["iCrew"]) == (
        10,
        "Pétrissage",
        "min_per_lot",
        "12",
        1,
    )
    assert (mix["cResource"], mix["cWorkCenter"], mix["cCapability"]) == (
        "PET1",
        "MIX-WC",
        "",
    )  # the resource says where
    assert (pack["cWorkCenter"], pack["cRunFormat"], pack["iCrew"]) == ("EMB-WC", "units_per_hour", 2)
    assert [m["cComponent"] for m in r["materials"]] == ["FARINE", "SAC"] and r["materials"][0]["cUOM"] == "KG"


@pytest.mark.parametrize(
    "change, error",
    [
        ({"cProduct": "FARINE"}, ("not_made", "cProduct")),
        ({"cProduct": "NOPE"}, ("unknown_ref", "cProduct")),
        ({"dBaseQty": "0"}, ("positive", "dBaseQty")),
        ({"dMinBatch": "300"}, ("max_below_min", "dMaxBatch")),
        ({"dYieldPct": "120"}, ("out_of_range", "dYieldPct")),
        ({"materials": [{"cComponent": "PAIN", "dQtyPer": "1"}]}, ("component_is_product", "materials")),
        ({"materials": [{"cComponent": "FARINE", "dQtyPer": "0"}]}, ("positive", "materials")),
        ({"materials": [{"cComponent": "FARINE", "dQtyPer": "1", "iOpSeq": 99}]}, ("unknown_ref", "materials")),
        ({"materials": [{"cComponent": "FARINE", "dQtyPer": "1", "dScrapPct": "100"}]}, ("out_of_range", "materials")),
        ({"operations": [{"iOpSeq": 10, "cOperation": "ZZ"}]}, ("unknown_ref", "operations")),
        ({"operations": [{"iOpSeq": 10, "cDescFR": "x"}]}, ("work_center_or_capability", "operations")),
        (
            {"operations": [{"iOpSeq": 10, "cOperation": "EMB"}, {"iOpSeq": 10, "cOperation": "EMB"}]},
            ("duplicate", "operations"),
        ),
        (
            {"operations": [{"iOpSeq": 10, "cOperation": "EMB", "cPredecessors": "30"}]},
            ("invalid_predecessors", "operations"),
        ),
        (
            {
                "operations": [
                    {"iOpSeq": 10, "cOperation": "EMB", "cPredecessors": "20"},
                    {"iOpSeq": 20, "cOperation": "EMB"},
                ]
            },
            ("predecessor_cycle", "operations"),
        ),
        (
            {"operations": [{"iOpSeq": 10, "cOperation": "EMB", "dMinWaitMin": "60", "dMaxWaitMin": "30"}]},
            ("max_below_min", "operations"),
        ),
        ({"operations": [{"iOpSeq": 10, "cDescFR": "Traitement", "lSubcontract": True}]}, ("required", "operations")),
        ({"outputs": [{"cProduct": "MIETTES", "dQtyPer": "2", "dCostPct": "100"}]}, ("cost_share_too_high", "outputs")),
    ],
)
def test_rules(svc, change, error):
    s, _r = svc
    body = {**BREAD, **change}
    if "operations" in change:
        body["materials"] = []
    assert code_of(s.create, body) == error


def test_predecessors_and_parallel_operations(svc):
    s, _r = svc
    assert parse_predecessors("10; 20, ") == [10, 20]
    ops = [
        {"iOpSeq": 10, "cOperation": "EMB"},
        {"iOpSeq": 20, "cOperation": "EMB", "cPredecessors": "10"},
        {"iOpSeq": 30, "cOperation": "EMB", "cPredecessors": "10"},
        {"iOpSeq": 40, "cOperation": "EMB", "cPredecessors": "20,30"},
    ]
    r = s.create({**BREAD, "materials": [], "operations": ops})
    assert r["operations"][3]["cPredecessors"] == "20, 30"


def test_explode(svc):
    s, _r = svc
    s.create({**BREAD, "outputs": [{"cProduct": "MIETTES", "cKind": "byproduct", "dQtyPer": "4", "dCostPct": "10"}]})
    e = s.explode("PAIN", "A", 400)
    assert e["iBatches"] == 2
    flour, bags = e["materials"]
    assert (flour["dQty"], flour["dCost"]) == (170, 102)  # 85 x 2, at the standard cost 0.60
    assert bags["dQty"] == 404  # one bag per bread + 1 % scrap
    mix, pack = e["operations"]
    assert (mix["dSetupMin"], mix["dRunMin"], mix["cWhere"]) == (10, 20, "PET1")  # 2 lots x 12 min / speed 1.2
    assert mix["dCost"] == round(10 / 60 * 60 + 20 / 60 * 60, 2)
    assert (pack["dRunMin"], pack["dCost"]) == (40, round((10 + 40) / 60 * 30 * 2, 2))  # labour x crew of 2
    assert e["outputs"][0]["dQty"] == 8
    assert e["dUnitCost"] == round(e["dTotalCost"] * 0.9 / 400, 4)  # the by-product carries 10 % of the cost
    # the product weighs 900, the mixer takes up to 800
    assert e["warnings"] == [
        {"iOpSeq": 10, "cResource": "PET1", "cAttribute": "poids", "dValue": 900, "dMin": "", "dMax": "800"}
    ]
    assert code_of(s.explode, "PAIN", "A", 0) == ("positive", "qty")


def test_yield_and_fixed_quantities(svc):
    s, _r = svc
    mats = [
        {"cComponent": "FARINE", "dQtyPer": "80", "iOpSeq": 10},
        {"cComponent": "SAC", "dQtyPer": "5", "lFixedQty": True},
    ]
    s.create({**BREAD, "dYieldPct": "80", "materials": mats})
    flour, fixed = s.explode("PAIN", "A", 200)["materials"]
    assert flour["dQty"] == 100 and fixed["dQty"] == 5  # 80 / 0.8; fixed: once per batch


def test_references_and_locked_versions(svc):
    s, registry = svc
    s.create(BREAD)
    used = (
        ("product", "PAIN"),
        ("product", "farine"),
        ("operation", "EMB"),
        ("resource", "PET1"),
        ("work_center", "EMB-WC"),
    )
    for kind, code in used:
        assert registry.is_used(kind, code), (kind, code)
    assert not registry.is_used("product", "VIS")
    row = s.get("PAIN", "A")
    s.repo.update({**row, "cStatus": "approved"})
    assert code_of(s.update, ["PAIN", "A"], {"cNotes": "x"}) == ("recipe_locked", "cStatus")
    assert code_of(s.delete, ["PAIN", "A"]) == ("recipe_locked", "cStatus")


def test_prepare_demo():
    rows = prepare_demo([{**BREAD, "cStatus": "approved"}], LISTS)
    assert rows[0]["cStatus"] == "approved" and rows[0]["operations"][0]["cDescFR"] == "Pétrissage"
