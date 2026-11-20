"""CRUD of a master file: one service class (Template Method) and its five routes.

A module subclasses CrudService and fills in only what is specific to it:
    validate(row, is_new)   business checks (required fields, references), may normalize the row
    view(row, full)         what the API returns (full=False in lists)
    before_delete(row)      e.g. references.check(...) -> 409 in_use
    keep_line(line)         which (almost) empty lines of a document are kept
"""

from __future__ import annotations

import copy
from collections.abc import Iterable
from typing import Any

from flask import Blueprint, jsonify, request

from powererp.core.errors import AppError, NotFound
from powererp.core.http import json_payload
from powererp.core.pagination import paginate_request
from powererp.core.values import text
from powererp.store import Store

from .forms import RecordForm, Row


class CrudService:
    keys: tuple[str, ...] = ("cCode",)
    readonly: tuple[str, ...] = ()
    line_schema: dict[str, Any] | None = None
    full_view_on_create: bool = True  # False: the record created is returned with the list's (short) view

    def __init__(self, repo: Store, schema: dict[str, Any], defaults: Row | None = None):
        self.repo = repo
        self.form = RecordForm(schema, defaults)
        self.line_form = RecordForm(self.line_schema) if self.line_schema else None

    # ---------------------------------------------------------- hooks for the subclasses
    def validate(self, row: Row, is_new: bool) -> None:
        """Business checks of a record about to be saved."""

    def view(self, row: Row, full: bool = True) -> Row:
        return row

    def before_delete(self, row: Row) -> None:
        """Refuse the deletion (AppError) while the record is used."""

    def keep_line(self, line: Row) -> bool:
        return True

    # ---------------------------------------------------------- operations
    def list(self) -> list[Row]:
        return self.repo.all()

    def find(self, *key_values: str) -> Row | None:
        return self.repo.get(*key_values)

    def get(self, *key_values: str) -> Row:
        row = self.find(*key_values)
        if row is None:
            raise NotFound()
        return row

    def _fill(self, row: Row, payload: Row, is_new: bool) -> Row:
        self.form.apply(row, payload, skip=(() if is_new else self.keys) + self.readonly)
        if self.line_form is not None and "lines" in payload:
            row["lines"] = self.line_form.lines(payload, self.keep_line)
        self.validate(row, is_new)
        return row

    def create(self, payload: Row) -> Row:
        row = self.form.blank()
        if self.line_form is not None:
            row["lines"] = []
        self._fill(row, payload, True)
        for k in self.keys:
            if not text(row.get(k)):
                raise AppError("required", k)
        if self.find(*[row[k] for k in self.keys]):
            raise AppError("duplicate", self.keys[-1], 409)
        self.repo.insert(row)
        return row

    def update(self, key_values: Iterable[str], payload: Row) -> Row:
        current = self.get(*list(key_values))
        row = self._fill(copy.deepcopy(current), payload, False)
        self.repo.update(row, [current[k] for k in self.keys])
        return row

    def delete(self, key_values: Iterable[str]) -> None:
        row = self.get(*list(key_values))
        self.before_delete(row)
        self.repo.delete(row)


def register_crud_routes(bp: Blueprint, url: str, name: str, service: CrudService, search: tuple[str, ...]) -> None:
    """GET/POST /api/<url> and GET/PUT/DELETE /api/<url>/<key> (key parts separated by "/")."""

    def collection():
        if request.method == "GET":
            rows = [{k: v for k, v in service.view(r, full=False).items() if k != "lines"} for r in service.list()]
            return jsonify(paginate_request(rows, search))
        row = service.create(json_payload())
        return jsonify(service.view(row, full=service.full_view_on_create)), 201

    def item(key: str):
        parts = key.split("/")
        if len(parts) != len(service.keys):
            raise NotFound()
        current = service.get(*parts)  # 404 before anything else
        if request.method == "GET":
            return jsonify(service.view(current))
        if request.method == "DELETE":
            service.delete(parts)
            return jsonify({"ok": True})
        return jsonify(service.view(service.update(parts, json_payload())))

    bp.add_url_rule(f"/api/{url}", f"{name}_collection", collection, methods=["GET", "POST"])
    bp.add_url_rule(f"/api/{url}/<path:key>", f"{name}_item", item, methods=["GET", "PUT", "DELETE"])
