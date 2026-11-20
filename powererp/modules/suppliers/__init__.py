"""Suppliers module (/api/suppliers): identification, address, payment terms, buyer, TPS / TVQ numbers.

Read by SkyAI through getSupplierTerm.p; used by purchasing (names on POs, receptions, invoices) and products.
"""

from __future__ import annotations

from flask import Blueprint, Flask, jsonify, request

from powererp.container import Container
from powererp.core.errors import AppError, NotFound
from powererp.core.http import json_payload, require
from powererp.core.pagination import paginate_request
from powererp.core.values import number, text
from powererp.modules.common.forms import Row
from powererp.store import Store, store

TEXT_FIELDS = (
    "cName",
    "cTermCode",
    "cTermDesc",
    "cAddress1",
    "cAddress2",
    "cCity",
    "cProvince",
    "cCountry",
    "cZipCode",
    "cNoTPS",
    "cNoTVQ",
    "cCodeAch",
    "cDescAch",
    "cDeptSauv",
)
INT_FIELDS = ("iTypePO", "iStatutAch")
SEARCH = ("cCode", "cName", "cCity", "cTermCode", "cDescAch")


class SupplierService:
    def __init__(self, repo: Store):
        self.repo = repo

    @staticmethod
    def _apply(row: Row, payload: Row) -> None:
        for f in TEXT_FIELDS:
            if f in payload:
                row[f] = text(payload[f])
        for f in INT_FIELDS:
            if f in payload:
                row[f] = int(number(payload[f]))

    def list(self) -> list[Row]:
        return self.repo.all()

    def find(self, code: str) -> Row | None:
        """A supplier by code, ignoring case (None when unknown)."""
        return self.repo.get(text(code)) if text(code) else None

    def name_of(self, code: str) -> str:
        s = self.find(code)
        return s["cName"] if s else ""

    def get(self, code: str) -> Row:
        row = self.repo.get(code, ci=False)
        if row is None:
            raise NotFound()
        return row

    def create(self, payload: Row) -> Row:
        require(payload, "cCode", "cName")
        code = text(payload["cCode"])
        if self.repo.get(code):
            raise AppError("duplicate", "cCode", 409)
        row: Row = {"cCode": code, **{f: "" for f in TEXT_FIELDS}, "iTypePO": 1, "iStatutAch": 1}
        self._apply(row, payload)
        self.repo.insert(row)
        return row

    def update(self, code: str, payload: Row) -> Row:
        row = self.get(code)
        require(payload, "cName")
        self._apply(row, payload)
        self.repo.update(row)
        return row

    def delete(self, code: str) -> None:
        self.repo.delete(self.get(code))

    def count(self, active_only: bool = False) -> int:
        return self.repo.count(lambda c: [c["iStatutAch"] == 1]) if active_only else self.repo.count()

    def lookup(self):
        return [{"code": s["cCode"], "label": s["cName"]} for s in self.repo.all()], 20

    def _distinct(self, code_field: str, label_field: str):
        seen: dict[str, str] = {}
        for s in self.repo.all():
            if s[code_field] and s[code_field] not in seen:
                seen[s[code_field]] = s[label_field]
        return [{"code": k, "label": v} for k, v in sorted(seen.items())], 200

    def terms_lookup(self):
        return self._distinct("cTermCode", "cTermDesc")

    def buyers_lookup(self):
        return self._distinct("cCodeAch", "cDescAch")


def _blueprint(suppliers: SupplierService) -> Blueprint:
    bp = Blueprint("suppliers", __name__)

    @bp.route("/api/suppliers", methods=["GET", "POST"])
    def supplier_collection():
        if request.method == "GET":
            return jsonify(paginate_request(suppliers.list(), SEARCH))
        return jsonify(suppliers.create(json_payload())), 201

    @bp.route("/api/suppliers/<code>", methods=["GET", "PUT", "DELETE"])
    def supplier_item(code):
        if request.method == "GET":
            return jsonify(suppliers.get(code))
        if request.method == "DELETE":
            suppliers.delete(code)
            return jsonify({"ok": True})
        suppliers.get(code)
        return jsonify(suppliers.update(code, json_payload()))

    return bp


def register(app: Flask, c: Container, seed: dict) -> None:
    suppliers = c.register("suppliers", SupplierService(store("suppliers")))
    app.register_blueprint(_blueprint(suppliers))
    lookups = c.get("lookups")
    lookups.register("suppliers", suppliers.lookup)
    lookups.register("terms", suppliers.terms_lookup)
    lookups.register("buyers", suppliers.buyers_lookup)
    c.get("dashboard").register(
        lambda: {"suppliers": suppliers.count(), "activeSuppliers": suppliers.count(active_only=True)}
    )
    c.get("lifecycle").add(suppliers.repo, "suppliers", seed.get("supplier_terms_data", []))
