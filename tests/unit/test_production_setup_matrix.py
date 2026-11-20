"""Unit tests of the setup matrix (P6): the rules of a matrix and the lookup of a changeover."""

import pytest

from powererp.core.errors import AppError
from powererp.modules.common.registry import ReferenceRegistry
from powererp.modules.production.setup_matrix import SetupMatrixService
from tests.unit.helpers import memory


@pytest.fixture
def svc():
    families = memory(
        [{"cCode": "WHITE", "lActive": True}, {"cCode": "COLOR", "lActive": True}, {"cCode": "KRAFT", "lActive": True}]
    )
    refs = {
        "work_centers": memory([{"cCode": "MP"}, {"cCode": "REB"}]).get,
        "resources": memory([{"cCode": "REB2", "cWorkCenter": "REB"}, {"cCode": "MP1", "cWorkCenter": "MP"}]).get,
        "setup_families": families.get,
        "families": families.all,
    }
    registry = ReferenceRegistry()
    return SetupMatrixService(memory([], keys=("cScope", "cScopeCode")), refs, registry), registry


def line(a, b, minutes, cost="", scrap=""):
    return {"cFromFamily": a, "cToFamily": b, "dSetupMin": minutes, "dSetupCost": cost, "dScrapQty": scrap}


def code_of(fn, *args):
    with pytest.raises(AppError) as e:
        fn(*args)
    return e.value.code, e.value.field


@pytest.fixture
def paper(svc):
    s, _r = svc
    s.create(
        {
            "cScope": "work_center",
            "cScopeCode": "mp",
            "lines": [
                line("*", "*", "30"),
                line("white", "color", "20"),
                line("COLOR", "WHITE", "45", "400", "1200"),
                line("color", "", "25"),
            ],
        }
    )
    return s


def test_matrix_rules_and_order(paper):
    row = paper.get("work_center", "MP")
    # exact pairs first, "*" last; empty family = "*"
    assert [(ln["cFromFamily"], ln["cToFamily"]) for ln in row["lines"]] == [
        ("COLOR", "WHITE"),
        ("WHITE", "COLOR"),
        ("COLOR", "*"),
        ("*", "*"),
    ]


@pytest.mark.parametrize(
    "body, error",
    [
        ({"cScope": "work_center", "cScopeCode": "NOPE"}, ("unknown_ref", "cScopeCode")),
        ({"cScope": "resource", "cScopeCode": ""}, ("required", "cScopeCode")),
        ({"cScope": "machine", "cScopeCode": "MP"}, ("invalid_choice", "cScope")),
        ({"cScope": "resource", "cScopeCode": "REB2", "lines": [line("GREEN", "*", "5")]}, ("unknown_ref", "lines")),
        (
            {"cScope": "resource", "cScopeCode": "REB2", "lines": [line("*", "*", "5"), line("*", "", "6")]},
            ("duplicate", "lines"),
        ),
        ({"cScope": "resource", "cScopeCode": "REB2", "lines": [line("*", "*", "-5")]}, ("negative", "lines")),
    ],
)
def test_rules(svc, body, error):
    s, _r = svc
    assert code_of(s.create, body) == error


@pytest.mark.parametrize(
    "src, dst, minutes, rule, match",
    [
        ("WHITE", "COLOR", 20, "matrix", ("WHITE", "COLOR")),  # exact pair
        ("COLOR", "KRAFT", 25, "matrix", ("COLOR", "*")),  # (from, *)
        ("KRAFT", "WHITE", 30, "matrix", ("*", "*")),  # (*, *)
        ("color", "white", 45, "matrix", ("COLOR", "WHITE")),
    ],
)
def test_lookup_order(paper, src, dst, minutes, rule, match):
    r = paper.changeover(src, dst, work_center="MP")
    assert (r["dSetupMin"], r["cRule"], (r["cFromFamily"], r["cToFamily"])) == (minutes, rule, match)


def test_resource_matrix_wins_and_fallbacks(svc):
    s, _r = svc
    s.create({"cScope": "work_center", "cScopeCode": "REB", "lines": [line("*", "*", "30")]})
    s.create({"cScope": "resource", "cScopeCode": "REB2", "lines": [line("*", "*", "45")]})
    assert s.changeover("WHITE", "COLOR", resource="REB2")["dSetupMin"] == 45  # its own matrix
    s.update(["resource", "REB2"], {"lActive": False})
    assert s.changeover("WHITE", "COLOR", resource="REB2")["cScope"] == "work_center"  # inactive: the work center's
    # no matrix at all: same family = no changeover, else the operation's setup
    assert s.changeover("WHITE", "WHITE", resource="MP1", default_min=40)["cRule"] == "same_family"
    r = s.changeover("WHITE", "COLOR", resource="MP1", default_min=40)
    assert (r["dSetupMin"], r["cRule"]) == (40, "operation")
    assert code_of(s.changeover, "A", "B", "NOPE") == ("unknown_ref", "resource")


def test_grid_and_references(paper, svc):
    _s, registry = svc
    g = paper.grid("work_center", "MP", default_min=99)
    assert g["families"] == ["WHITE", "COLOR", "KRAFT"]
    assert [c["dSetupMin"] for c in g["cells"][1]] == [45, 25, 25]  # from COLOR: exact, then (COLOR, *)
    assert registry.is_used("setup_family", "white") and not registry.is_used("setup_family", "KRAFT")
    assert registry.is_used("work_center", "MP") and not registry.is_used("resource", "REB2")
