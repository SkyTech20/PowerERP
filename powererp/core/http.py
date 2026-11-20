"""HTTP helpers shared by the API modules."""

from __future__ import annotations

from typing import Any

from flask import request

from .errors import AppError
from .values import text


def json_payload() -> dict[str, Any]:
    """The JSON object of the request body (400 invalid_body otherwise)."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise AppError("invalid_body")
    return data


def require(payload: dict[str, Any], *fields: str) -> None:
    """400 required/<field> for the first empty field."""
    for f in fields:
        if not text(payload.get(f)):
            raise AppError("required", f)
