"""Unit tests for the value helpers shared by every ERP screen and service."""

import pytest

from powererp.core import values


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("12.50", "12.50"),
        ("$12.50", "12.50"),
        ("12,50 $", "12.50"),
        ("$1,234.56", "1234.56"),
        ("1 234,56 $", "1234.56"),
        ("1.234,56", "1234.56"),
        ("1,234,567", "1234567"),
        ("1.2.3", "12.3"),
        ("CAD 99.9", "99.9"),
        ("-$5", "-5"),
        (" 7 ", "7"),
        (42, "42"),
        (3.5, "3.5"),
    ],
)
def test_dec_keeps_only_the_number(raw, expected):
    assert values.decimal_text(raw) == expected


@pytest.mark.parametrize("raw", ["", None, "abc", "$", " - "])
def test_dec_without_number_returns_default(raw):
    assert values.decimal_text(raw) == "0"
    assert values.decimal_text(raw, "") == ""


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("10", 10.0),
        ("10,5", 10.5),
        ("$10.25", 10.25),
        ("abc", 0.0),
        (None, 0.0),
        ("", 0.0),
    ],
)
def test_num(raw, expected):
    assert values.number(raw) == expected


def test_num_default():
    assert values.number("", 1) == 1
    assert values.number("xyz", 1) == 1


@pytest.mark.parametrize("raw, expected", [("12.5", "12.50"), ("$3", "3.00"), ("", "0.00"), (1 / 3, "0.33")])
def test_money(raw, expected):
    assert values.money(raw) == expected


@pytest.mark.parametrize("raw, expected", [("2", "2"), ("2.0", "2"), ("2.5", "2.50"), ("", "0")])
def test_qty(raw, expected):
    assert values.qty_text(raw) == expected


@pytest.mark.parametrize(
    "raw, expected",
    [
        (True, True),
        ("true", True),
        ("1", True),
        (1, True),
        ("on", True),
        ("yes", True),
        (False, False),
        ("false", False),
        ("0", False),
        (None, False),
        ("", False),
    ],
)
def test_bool(raw, expected):
    assert values.boolean(raw) is expected


@pytest.mark.parametrize("raw, expected", [(None, ""), ("  a ", "a"), (True, "true"), (False, "false"), (5, "5")])
def test_s(raw, expected):
    assert values.text(raw) == expected


def test_purchasing_uses_the_same_number_parser():
    # Regression: apCreatePO.p used its own parser that read "$12.50" as 0.
    assert values.number("$12.50") == 12.5
