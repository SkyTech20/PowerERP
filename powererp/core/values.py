"""Parsing and formatting of the values typed in the screens or sent by SkyAI.

Numbers are typed in many ways ("$12.50", "12,50 $", "1 234.5"); the API keeps them as text ("12.50").
"""

from __future__ import annotations

import re
from datetime import date
from typing import Any

TRUE_VALUES = (True, "true", "True", 1, "1", "on", "yes")


def text(value: Any) -> str:
    """Any incoming value as a trimmed string (None -> "", booleans -> "true" / "false")."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value).strip()


def decimal_text(value: Any, default: str | None = "0") -> str | None:
    """Only the number of a typed amount ("$12.50", "12,50 $", "1 234.5") as "12.50"; `default` when there is none."""
    s = re.sub(r"[^\d,.\-]", "", text(value))
    neg = s.startswith("-")
    s = s.replace("-", "")
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".") if s.rfind(",") > s.rfind(".") else s.replace(",", "")
    elif "," in s:
        s = s.replace(",", ".") if s.count(",") == 1 else s.replace(",", "")
    if s.count(".") > 1:
        cut = s.rfind(".")
        s = s[:cut].replace(".", "") + s[cut:]
    if not re.search(r"\d", s):
        return default
    return ("-" if neg else "") + s


def number(value: Any, default: float = 0.0) -> float:
    try:
        return float(decimal_text(value, "") or "")
    except (TypeError, ValueError, AttributeError):
        return default


def boolean(value: Any) -> bool:
    return value in TRUE_VALUES


def money(value: Any) -> str:
    """An amount with 2 decimals, from anything typed ("$12.5" -> "12.50")."""
    return f"{number(value):.2f}"


def qty_text(value: Any) -> str:
    """A quantity of a document line: "12" or "12.50"."""
    q = number(value)
    return f"{q:.0f}" if q == int(q) else f"{q:.2f}"


def quantity(v: float) -> str:
    """A stock quantity as text: "12", "12.5", "0.125" (4 decimals at most)."""
    v = round(float(v), 4)
    return str(int(v)) if v == int(v) else f"{v:.4f}".rstrip("0").rstrip(".")


def amount(v: float) -> str:
    """A calculated amount, rounded half up to 2 decimals."""
    return f"{round(float(v) + 1e-9, 2):.2f}"


def unit_cost(v: float) -> str:
    """A unit cost (4 decimals, trailing zeros removed down to 2)."""
    s = f"{float(v):.4f}"
    return s[:-2] if s.endswith("00") else s.rstrip("0")


def today() -> str:
    return date.today().isoformat()
