"""Unit tests of the tax services: no Flask, no database."""

import pytest

from powererp.core.errors import AppError
from powererp.modules.common.registry import ReferenceRegistry
from powererp.modules.taxes import TaxCalculator, TaxCodeService, TaxGroupService, rate_on
from tests.unit.helpers import memory

TPS = {
    "cCode": "TPS",
    "cDescFR": "TPS",
    "cKind": "gst",
    "dRecoverablePct": "100",
    "lines": [{"dStartDate": "2008-01-01", "dEndDate": "", "dRate": "5"}],
}
TVQ = {
    "cCode": "TVQ",
    "cDescFR": "TVQ",
    "cKind": "pst",
    "dRecoverablePct": "50",
    "lines": [
        {"dStartDate": "2012-01-01", "dEndDate": "2012-12-31", "dRate": "9.5"},
        {"dStartDate": "2013-01-01", "dEndDate": "", "dRate": "9.975"},
    ],
}
QC = {
    "cCode": "QC",
    "cDescFR": "Québec",
    "cTreatment": "taxable",
    "lines": [{"iSeq": 1, "cTaxCode": "TPS", "lCompound": False}, {"iSeq": 2, "cTaxCode": "TVQ", "lCompound": False}],
}


@pytest.fixture
def services():
    refs = ReferenceRegistry()
    codes = TaxCodeService(memory([TPS, TVQ]), refs)
    groups = TaxGroupService(memory([QC]), codes, refs)
    return codes, groups, TaxCalculator(codes, groups), refs


def test_rate_history():
    assert rate_on(TVQ, "2012-06-01") == 9.5
    assert rate_on(TVQ, "2026-01-01") == 9.975
    assert rate_on(TVQ, "2010-01-01") is None


def test_calculation_by_date(services):
    _, _, calc, _ = services
    now = calc.calc("QC", 100, "2026-01-01")
    assert [t["dTax"] for t in now["taxes"]] == ["5.00", "9.98"] and now["dTotal"] == "114.98"
    assert now["taxes"][1]["dRecoverable"] == "4.99"
    assert calc.calc("QC", 100, "2012-06-01")["dTotalTax"] == "14.50"
    assert calc.calc("NOPE", 100) is None


def test_compound_tax(services):
    codes, groups, calc, _ = services
    groups.create(
        {
            "cCode": "CMP",
            "cDescFR": "c",
            "lines": [{"iSeq": 1, "cTaxCode": "tps"}, {"iSeq": 2, "cTaxCode": "TVQ", "lCompound": True}],
        }
    )
    res = calc.calc("CMP", 100, "2026-01-01")
    assert [t["dBase"] for t in res["taxes"]] == ["100.00", "105.00"]


def test_group_validation(services):
    _, groups, _, _ = services
    with pytest.raises(AppError) as e:
        groups.create({"cCode": "X", "cDescFR": "x", "lines": [{"cTaxCode": "NOPE"}]})
    assert (e.value.code, e.value.field) == ("unknown_ref", "lines")
    g = groups.create({"cCode": "Y", "cDescFR": "y", "lines": [{"cTaxCode": "tvq"}]})
    assert g["lines"][0] == {"iSeq": 1, "cTaxCode": "TVQ", "lCompound": False}


def test_a_used_tax_code_cannot_be_deleted(services):
    codes, _, _, refs = services
    with pytest.raises(AppError) as e:
        codes.delete(["TPS"])
    assert e.value.status == 409
    refs.register("tax_group", lambda code: code == "QC")  # e.g. the products
    _, groups, _, _ = services
    with pytest.raises(AppError):
        groups.delete(["QC"])
