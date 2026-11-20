"""Unit tests of the steps of the recipe operations (P9): rules, value checks, conditions."""

import pytest

from powererp.core.errors import AppError
from powererp.modules.production.steps import check_value, condition_met, parse_condition, validate_steps


def step(op=10, n=10, kind="instruction", title="Pas", **kw):
    s = {
        "iOpSeq": op,
        "iStep": n,
        "cKind": kind,
        "cTitleFR": title,
        "cTitleEN": "",
        "cInstructionFR": "",
        "cInstructionEN": "",
        "cAttachmentUrl": "",
        "dDurationMin": "",
        "cParam": "",
        "cDataType": "number",
        "cUOM": "",
        "dTarget": "",
        "dMin": "",
        "dMax": "",
        "cOptions": "",
        "lRequired": False,
        "lCritical": False,
        "cOnFail": "block",
        "cFrequency": "once",
        "dFrequencyValue": "",
        "iMaterialSeq": 0,
        "cRequiredRole": "",
        "lSecondSignature": False,
        "cCondition": "",
    }
    s.update(kw)
    return s


def recipe(*steps):
    return {
        "operations": [{"iOpSeq": 10}, {"iOpSeq": 20}],
        "materials": [{"iSeq": 10, "iOpSeq": 10}, {"iSeq": 20, "iOpSeq": 0}, {"iSeq": 30, "iOpSeq": 20}],
        "steps": list(steps),
    }


def code_of(r):
    with pytest.raises(AppError) as e:
        validate_steps(r)
    return e.value.code


def test_order_numbering_and_kind_rules():
    r = recipe(
        step(20, 20, "timer", "Pétrir", dDurationMin="12"),
        step(10, 0, "material_add", "Farine", iMaterialSeq=10),
        step(10, 0, "material_add", "Levure", iMaterialSeq=20),  # op 0 = the first operation
        step(20, 10, "check", "Propre", lCritical=True, cDataType="number"),
        step(20, 30, "instruction", "Lire", lCritical=True, iMaterialSeq=30),
        step(20, 40, "signature", "Signer"),
    )
    validate_steps(r)
    assert [(s["iOpSeq"], s["iStep"]) for s in r["steps"]] == [
        (10, 10),
        (10, 20),
        (20, 10),
        (20, 20),
        (20, 30),
        (20, 40),
    ]
    by = {s["cTitleFR"]: s for s in r["steps"]}
    assert by["Propre"]["cDataType"] == "yes_no" and by["Propre"]["lCritical"] is True
    assert by["Lire"]["lCritical"] is False and by["Lire"]["iMaterialSeq"] == 0  # nothing to compare, no material
    assert by["Signer"]["lSecondSignature"] is True


@pytest.mark.parametrize(
    "s, error",
    [
        (step(30), "unknown_ref"),
        (step(title=""), "required"),
        (step(kind="measure"), "required"),  # no parameter code
        (step(kind="measure", cParam="1BAD"), "invalid_param"),
        (step(kind="measure", cParam="T", dMin="26", dMax="24"), "max_below_min"),
        (step(kind="measure", cParam="T", dMin="24", dMax="26", dTarget="30"), "target_out_of_limits"),
        (step(kind="measure", cParam="T", cDataType="list"), "required"),
        (step(kind="material_add", iMaterialSeq=99), "unknown_ref"),
        (step(kind="material_add", iMaterialSeq=30), "material_other_operation"),
        (step(kind="timer"), "positive"),
        (step(cFrequency="every_n_units"), "positive"),
        (step(cCondition="TEMP < 24"), "invalid_condition"),  # no earlier step records TEMP
        (step(cCondition="TEMP is low"), "invalid_condition"),
    ],
)
def test_rules(s, error):
    assert code_of(recipe(s)) == error


def test_duplicates_and_conditions_on_earlier_values():
    assert code_of(recipe(step(n=10), step(n=10))) == "duplicate"
    two = recipe(step(n=10, kind="measure", cParam="t"), step(n=20, kind="measure", cParam="T"))
    assert code_of(two) == "duplicate"  # the same parameter code twice
    later = recipe(step(n=10, cCondition="T < 24"), step(n=20, kind="measure", cParam="T"))
    assert code_of(later) == "invalid_condition"  # the value is recorded after
    ok = recipe(step(n=10, kind="measure", cParam="temp_pate"), step(n=20, cCondition=" temp_pate<24 "))
    validate_steps(ok)
    assert ok["steps"][0]["cParam"] == "TEMP_PATE" and ok["steps"][1]["cCondition"] == "TEMP_PATE < 24"


def test_conditions():
    assert parse_condition("") is None and parse_condition("A >= 2,5") == ("A", ">=", "2,5")
    assert condition_met("", {}) is True
    assert condition_met("TEMP < 24", {"TEMP": "23,5"}) is True
    assert condition_met("TEMP < 24", {"TEMP": 25}) is False
    assert condition_met("TEMP < 24", {}) is False  # not recorded yet
    assert condition_met("ASPECT = Retouche", {"ASPECT": "retouche"}) is True
    assert condition_met("ASPECT != OK", {"ASPECT": "OK"}) is False
    assert condition_met("ASPECT > OK", {"ASPECT": "OK"}) is False  # no order between texts


@pytest.mark.parametrize(
    "s, value, result",
    [
        (step(kind="measure", cParam="T", dMin="24", dMax="26", lCritical=True, cOnFail="warn"), "25", (True, "", "")),
        (
            step(kind="measure", cParam="T", dMin="24", dMax="26", lCritical=True, cOnFail="hold_lot"),
            "26,5",
            (False, "above_max", "hold_lot"),
        ),
        (step(kind="measure", cParam="T", dMin="92"), "90", (False, "below_min", "warn")),  # not critical: a warning
        (step(kind="measure", cParam="T"), "abc", (False, "numeric", "block")),
        (step(kind="measure", cParam="T", lRequired=True), "", (False, "required", "warn")),
        (step(kind="measure", cParam="T"), "", (True, "", "")),
        (step(kind="check", lCritical=True), "oui", (True, "", "")),
        (step(kind="check", lCritical=True), "non", (False, "not_confirmed", "block")),
        (
            step(kind="measure", cParam="A", cDataType="list", cOptions="OK, Retouche, Rebut"),
            "retouche",
            (True, "", ""),
        ),
        (
            step(kind="measure", cParam="A", cDataType="list", cOptions="OK, Retouche"),
            "Bof",
            (False, "not_in_list", "warn"),
        ),
    ],
)
def test_check_value(s, value, result):
    r = check_value(s, value)
    assert (r["ok"], r["reason"], r["action"]) == result
