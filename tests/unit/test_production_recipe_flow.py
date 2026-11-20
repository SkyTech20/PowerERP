"""Unit tests of the versions and approval of the recipes (P10), on memory repositories."""

from datetime import date

import pytest

from powererp.core.errors import AppError
from powererp.modules.common.registry import ReferenceRegistry
from powererp.modules.production.recipe_flow import RecipeFlow, next_revision
from powererp.modules.production.recipes import RecipeService
from tests.unit.helpers import memory
from tests.unit.test_production_recipes import BREAD, LISTS


@pytest.fixture
def world():
    keys = {"product_mfg": ("cProduct",)}
    refs = {k: memory(v, keys=keys.get(k, ("cCode",))).get for k, v in LISTS.items()}
    recipes = RecipeService(memory([], keys=("cProduct", "cRevision")), refs, ReferenceRegistry())
    who = {"name": "marie", "admin": True}
    flow = RecipeFlow(recipes, lambda: who["name"], lambda: who["admin"])
    recipes.create(BREAD)
    return recipes, flow, who


def code_of(fn, *args):
    with pytest.raises(AppError) as e:
        fn(*args)
    return e.value.code, e.value.status


@pytest.mark.parametrize(
    "existing, nxt",
    [
        ([], "A"),
        (["A"], "B"),
        (["A", "C", "B"], "D"),
        (["Z"], "AA"),
        (["AZ"], "BA"),
        (["1", "2"], "3"),
        (["A1"], "A1A"),
    ],
)
def test_next_revision(existing, nxt):
    assert next_revision(existing) == nxt


def test_flow(world):
    recipes, flow, who = world
    assert code_of(flow.approve, "PAIN", "A") == ("invalid_status", 409)  # a draft is submitted first
    r = flow.submit("PAIN", "A")
    assert (r["cStatus"], r["cSubmittedBy"], r["history"][0]["cAction"]) == ("in_review", "marie", "submit")
    assert code_of(recipes.update, ["PAIN", "A"], {"cNotes": "x"})[0] == "recipe_locked"
    who.update(name="paul", admin=False)
    assert code_of(flow.approve, "PAIN", "A") == ("forbidden", 403)
    who.update(name="chef", admin=True)
    r = flow.approve("PAIN", "A", "ok")
    assert (r["cStatus"], r["cApprovedBy"], r["lDefault"]) == ("approved", "chef", True)
    assert [h["cTo"] for h in recipes.get("PAIN", "A")["history"]] == ["in_review", "approved"]
    b = flow.new_version("PAIN", "A", reason="moins de sel")
    assert (b["cRevision"], b["cStatus"], b["cChangeReason"], b["history"][0]["cFrom"]) == (
        "B",
        "draft",
        "moins de sel",
        "A (approved)",
    )
    flow.submit("PAIN", "B")
    flow.approve("PAIN", "B")
    assert recipes.get("PAIN", "A")["lDefault"] is False and flow.current("PAIN")["cRevision"] == "B"
    flow.obsolete("PAIN", "B")
    assert flow.current("PAIN")["cRevision"] == "A"  # the latest approved left


def test_submit_needs_operations_and_reject_a_comment(world):
    recipes, flow, _who = world
    recipes.create({**BREAD, "cRevision": "X", "operations": [], "materials": [], "steps": []})
    assert code_of(flow.submit, "PAIN", "X")[0] == "no_operations"
    flow.submit("PAIN", "A")
    assert code_of(flow.reject, "PAIN", "A", "")[0] == "required"
    assert flow.reject("PAIN", "A", "revoir le sel")["cStatus"] == "draft"


def test_current_follows_validity(world):
    recipes, flow, _who = world
    recipes.update(["PAIN", "A"], {"dEffectiveFrom": "2026-01-01", "dEffectiveTo": "2026-06-30"})
    flow.submit("PAIN", "A")
    flow.approve("PAIN", "A")
    assert flow.current("PAIN", date(2026, 3, 1))["cRevision"] == "A"
    assert flow.current("PAIN", date(2026, 7, 1)) is None
    assert (
        code_of(
            recipes.create, {**BREAD, "cRevision": "Z", "dEffectiveFrom": "2026-02-01", "dEffectiveTo": "2026-01-01"}
        )[0]
        == "end_before_start"
    )


def test_compare(world):
    recipes, flow, _who = world
    flow.new_version("PAIN", "A")
    b = recipes.get("PAIN", "B")
    b["materials"][0]["dQtyPer"] = "90"
    recipes.update(
        ["PAIN", "B"], {"dYieldPct": "97", "materials": b["materials"][:1], "operations": b["operations"][:1]}
    )
    diff = flow.compare("PAIN", "A", "B")
    assert diff["header"] == [{"cField": "dYieldPct", "cFrom": "100", "cTo": "97"}]
    flour = next(x for x in diff["materials"] if x["cKey"] == "FARINE")
    assert flour["cChange"] == "changed" and {"cField": "dQtyPer", "cFrom": "85", "cTo": "90"} in flour["fields"]
    assert [x["cChange"] for x in diff["operations"]] == ["removed"]  # op 20 left, and its bags
    assert [(x["cKey"], x["cChange"]) for x in diff["materials"] if x["cChange"] == "removed"] == [("SAC", "removed")]
