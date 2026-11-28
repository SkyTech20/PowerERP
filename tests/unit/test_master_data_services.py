"""Unit tests of the master data services: suppliers, GL accounts, cost centers, units, categories."""

import pytest

from powererp.core.errors import AppError, NotFound
from powererp.modules.catalog import CategoryService, UnitService
from powererp.modules.common.registry import ReferenceRegistry
from powererp.modules.ledger import CostCenterService, GLAccountService
from powererp.modules.suppliers import SupplierService
from tests.unit.helpers import memory


def code_of(fn, *args):
    with pytest.raises(AppError) as e:
        fn(*args)
    return e.value.code, e.value.field, e.value.status


def test_supplier_create_update_and_lookups():
    s = SupplierService(memory([{"cCode": "LUM", "cName": "Lumen", "cTermCode": "N30", "cTermDesc": "Net 30"}]))
    row = s.create({"cCode": " ACME ", "cName": "Acme", "iTypePO": "2", "cTermCode": "N30", "cTermDesc": "Net 30"})
    assert (row["cCode"], row["iTypePO"], row["iStatutAch"], row["cCity"]) == ("ACME", 2, 1, "")
    assert code_of(s.create, {"cCode": "lum", "cName": "x"}) == ("duplicate", "cCode", 409)
    assert code_of(s.create, {"cCode": "X"}) == ("required", "cName", 400)
    assert s.update("ACME", {"cName": "Acme inc.", "cCode": "OTHER"})["cCode"] == "ACME"
    assert s.name_of("acme") == "Acme inc." and s.name_of("") == "" and s.name_of("nope") == ""
    assert s.terms_lookup() == ([{"code": "N30", "label": "Net 30"}], 200)  # distinct terms
    with pytest.raises(NotFound):
        s.get("acme")  # a screen URL must match the code exactly


def test_gl_accounts():
    gl = GLAccountService(memory([{"cCode": "1000", "cDesc": "Cash"}]))
    row = gl.create({"cCode": "2000", "cDesc": "Payables"})
    assert (row["cCode"], row["cDesc"], row["cType"], row["lActive"], row["lRequiresCC"]) == (
        "2000",
        "Payables",
        "liability",
        True,
        False,
    )
    assert code_of(gl.create, {"cCode": "1000", "cDesc": "x"}) == ("duplicate", "cCode", 409)
    assert code_of(gl.update, "1000", {"cDesc": ""}) == ("required", "cDesc", 400)
    gl.delete("2000")
    assert gl.lookup() == ([{"code": "1000", "label": "Cash"}], 20)


def test_cost_centers_have_a_two_part_key():
    cc = CostCenterService(
        memory([{"cCC1": "100", "cCC2": "", "cDesc": "Admin", "lActive": True}], keys=("cCC1", "cCC2"))
    )
    cc.create({"cCC1": "100", "cCC2": "01", "cDesc": "Admin, IT"})
    assert code_of(cc.create, {"cCC1": "100", "cDesc": "again"}) == ("duplicate", "cCC1", 409)
    assert code_of(cc.create, {"cCC1": "100", "cCC2": "01", "cDesc": "x"}) == ("duplicate", "cCC2", 409)
    assert cc.get("100")["cDesc"] == "Admin" and cc.get("100", "01")["cDesc"] == "Admin, IT"
    assert [r["code"] for r in cc.lookup()[0]] == ["100", "100-01"]


def test_units_cannot_be_deleted_while_used():
    refs = ReferenceRegistry()
    units = UnitService(memory([{"cCode": "KG", "cDescFR": "Kilogramme"}]), refs)
    refs.register("uom", lambda code: code == "KG")
    assert code_of(units.create, {"cCode": "L"}) == ("required", "cDescFR", 400)
    assert code_of(units.delete, ["KG"]) == ("in_use", None, 409)


def test_category_tree_rules():
    refs = ReferenceRegistry()
    cats = CategoryService(memory([{"cCode": "HW", "cDescFR": "Quincaillerie", "cParent": ""}]), refs)
    cats.create({"cCode": "SCR", "cDescFR": "Vis", "cParent": "hw"})
    assert code_of(cats.create, {"cCode": "X", "cDescFR": "x", "cParent": "NOPE"}) == ("unknown_ref", "cParent", 400)
    assert code_of(cats.update, ["HW"], {"cParent": "HW"}) == ("invalid_ref", "cParent", 400)
    assert code_of(cats.delete, ["HW"]) == ("in_use", None, 409)  # it has a child
    cats.delete(["SCR"])
    cats.delete(["HW"])
    assert cats.list() == []
