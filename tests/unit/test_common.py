"""Unit tests of the shared building blocks: CrudService (Template Method), the field forms, the registries,
list paging."""

import pytest

from powererp.core.errors import AppError, NotFound
from powererp.core.pagination import paginate
from powererp.modules.common.crud import CrudService
from powererp.modules.common.forms import RecordForm
from powererp.modules.common.registry import LookupRegistry, ReferenceRegistry
from tests.unit.helpers import memory

SCHEMA = {"cCode": "s", "cName": "s", "dPrice": "d", "iSeq": "i", "lActive": "b", "dDate": "date", "cKind": ("a", "b")}
LINE = {"cItem": "s", "dQty": "d"}


class Thing(CrudService):
    """A minimal master file: every hook used once."""

    readonly = ("dPrice",)
    line_schema = LINE

    def __init__(self, repo):
        super().__init__(repo, SCHEMA, {"lActive": True})
        self.deleted_check = []

    def validate(self, row, is_new):
        if not row["cName"]:
            raise AppError("required", "cName")
        row["cName"] = row["cName"].upper()

    def keep_line(self, line):
        return bool(line["cItem"])

    def before_delete(self, row):
        self.deleted_check.append(row["cCode"])
        if row["cCode"] == "USED":
            raise AppError("in_use", status=409)


@pytest.fixture
def things():
    return Thing(memory([{"cCode": "A1", "cName": "OLD", "dPrice": "5", "lines": []}, {"cCode": "USED", "cName": "U"}]))


def error(fn, *args):
    with pytest.raises(AppError) as e:
        fn(*args)
    return e.value.code, e.value.field, e.value.status


def test_create_fills_defaults_cleans_and_validates(things):
    row = things.create({"cCode": "B2", "cName": "new", "iSeq": "3", "lines": [{"cItem": "X", "dQty": "2"}, {}]})
    assert row["cName"] == "NEW" and row["iSeq"] == 3 and row["lActive"] is True and row["cKind"] == "a"
    assert row["lines"] == [{"cItem": "X", "dQty": "2"}]  # the empty line is dropped by keep_line
    assert things.find("b2")["cName"] == "NEW"  # keys ignore case


def test_create_errors(things):
    assert error(things.create, {"cName": "x"}) == ("required", "cCode", 400)
    assert error(things.create, {"cCode": "a1", "cName": "x"}) == ("duplicate", "cCode", 409)
    assert error(things.create, {"cCode": "C", "cName": ""}) == ("required", "cName", 400)
    assert error(things.create, {"cCode": "C", "cName": "x", "lines": [{"cItem": "I", "dQty": "abc"}]})[:2] == (
        "numeric",
        "dQty",
    )
    assert things.create({"cCode": "D", "cName": "x", "dPrice": "abc"})["dPrice"] == ""  # read-only: ignored
    assert error(things.create, {"cCode": "C", "cName": "x", "dDate": "2026-13-01"})[0] == "invalid_date"
    assert error(things.create, {"cCode": "C", "cName": "x", "cKind": "z"})[0] == "invalid_choice"


def test_update_keeps_the_key_and_read_only_fields(things):
    row = things.update(["A1"], {"cCode": "ZZ", "cName": "renamed", "dPrice": "99"})
    assert (row["cCode"], row["cName"], row["dPrice"]) == ("A1", "RENAMED", "5")
    with pytest.raises(NotFound):
        things.update(["nope"], {"cName": "x"})


def test_delete_asks_the_hook_first(things):
    assert error(things.delete, ["USED"]) == ("in_use", None, 409)
    things.delete(["A1"])
    assert things.find("A1") is None and things.deleted_check == ["USED", "A1"]


def test_record_form_blank_values():
    blank = RecordForm(SCHEMA, {"cName": "x"}).blank()
    assert blank == {"cCode": "", "cName": "x", "dPrice": "", "iSeq": 0, "lActive": False, "dDate": "", "cKind": "a"}


def test_reference_registry():
    refs = ReferenceRegistry()
    refs.register("uom", lambda code: code == "KG")
    refs.register("uom", lambda code: code == "L")
    assert refs.is_used("uom", "L") and not refs.is_used("uom", "M") and not refs.is_used("other", "KG")
    with pytest.raises(AppError) as e:
        refs.check("uom", "KG")
    assert (e.value.code, e.value.status) == ("in_use", 409)


def test_lookup_registry():
    lookups = LookupRegistry()
    lookups.register("colors", lambda: ([{"code": "R", "label": "Red"}], 10))
    assert lookups["colors"]() == ([{"code": "R", "label": "Red"}], 10)


ROWS = [
    {"cCode": "B", "n": 10, "c": "Montréal"},
    {"cCode": "a", "n": 9, "c": "Laval"},
    {"cCode": "C", "n": 100, "c": "laval"},
]


@pytest.mark.parametrize(
    "args, codes, total",
    [
        ({}, ["B", "a", "C"], 3),
        ({"q": "LAV"}, ["a", "C"], 2),
        ({"f_c": "LAVAL"}, ["a", "C"], 2),
        ({"sort": "n"}, ["a", "B", "C"], 3),  # numbers sort as numbers
        ({"sort": "cCode", "dir": "desc"}, ["C", "B", "a"], 3),  # text ignores case
        ({"sort": "n", "size": "2", "page": "2"}, ["C"], 3),
        ({"size": "abc"}, ["B", "a", "C"], 3),
    ],
)
def test_paginate(args, codes, total):
    page = paginate(ROWS, ("cCode", "c"), args)
    assert [r["cCode"] for r in page["items"]] == codes and page["total"] == total
