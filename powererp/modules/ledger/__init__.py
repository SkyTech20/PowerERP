"""General ledger module: GL accounts (/api/gl-accounts) and cost centers (/api/cost-centers).

Read by SkyAI through getGLaccounts.p (powererp.integrations / powerware_api).
"""

from __future__ import annotations

from flask import Blueprint, Flask, jsonify, request

from powererp.container import Container
from powererp.core.errors import AppError, NotFound
from powererp.core.http import json_payload, require
from powererp.core.pagination import paginate_request
from powererp.core.values import text
from powererp.modules.common.forms import Row
from powererp.store import Store, store


class GLAccountService:
    """GL accounts: code + description. The code of a screen URL must match exactly; duplicates ignore case."""

    def __init__(self, repo: Store):
        self.repo = repo

    def list(self) -> list[Row]:
        return self.repo.all()

    def get(self, code: str) -> Row:
        row = self.repo.get(code, ci=False)
        if row is None:
            raise NotFound()
        return row

    def create(self, payload: Row) -> Row:
        require(payload, "cCode", "cDesc")
        code = text(payload["cCode"])
        if self.repo.get(code):
            raise AppError("duplicate", "cCode", 409)
        row = {"cCode": code, "cDesc": text(payload["cDesc"])}
        self.repo.insert(row)
        return row

    def update(self, code: str, payload: Row) -> Row:
        row = self.get(code)
        require(payload, "cDesc")
        row["cDesc"] = text(payload["cDesc"])
        self.repo.update(row)
        return row

    def delete(self, code: str) -> None:
        self.repo.delete(self.get(code))

    def lookup(self):
        return [{"code": g["cCode"], "label": g["cDesc"]} for g in self.repo.all()], 20


class CostCenterService:
    """Cost centers: key cCC1 + cCC2 (cCC2 may be empty)."""

    def __init__(self, repo: Store):
        self.repo = repo

    def list(self) -> list[Row]:
        return self.repo.all()

    def get(self, cc1: str, cc2: str = "") -> Row:
        row = self.repo.get(cc1, cc2 or "", ci=False)
        if row is None:
            raise NotFound()
        return row

    def create(self, payload: Row) -> Row:
        require(payload, "cCC1", "cDesc")
        cc1, cc2 = text(payload["cCC1"]), text(payload.get("cCC2"))
        if self.repo.get(cc1, cc2, ci=False) or self.repo.get(cc1, cc2):
            raise AppError("duplicate", "cCC2" if cc2 else "cCC1", 409)
        row = {"cCC1": cc1, "cCC2": cc2, "cDesc": text(payload["cDesc"])}
        self.repo.insert(row)
        return row

    def update(self, cc1: str, cc2: str, payload: Row) -> Row:
        row = self.get(cc1, cc2)
        require(payload, "cDesc")
        row["cDesc"] = text(payload["cDesc"])
        self.repo.update(row)
        return row

    def delete(self, cc1: str, cc2: str) -> None:
        self.repo.delete(self.get(cc1, cc2))

    def lookup(self):
        rows = [
            {"code": f'{c["cCC1"]}-{c["cCC2"]}' if c["cCC2"] else c["cCC1"], "label": c["cDesc"]}
            for c in self.repo.all()
        ]
        return rows, 20


def _blueprint(accounts: GLAccountService, centers: CostCenterService) -> Blueprint:
    bp = Blueprint("ledger", __name__)

    @bp.route("/api/gl-accounts", methods=["GET", "POST"])
    def gl_collection():
        if request.method == "GET":
            return jsonify(paginate_request(accounts.list(), ("cCode", "cDesc")))
        return jsonify(accounts.create(json_payload())), 201

    @bp.route("/api/gl-accounts/<code>", methods=["GET", "PUT", "DELETE"])
    def gl_item(code):
        if request.method == "GET":
            return jsonify(accounts.get(code))
        if request.method == "DELETE":
            accounts.delete(code)
            return jsonify({"ok": True})
        accounts.get(code)  # 404 before validating the body
        return jsonify(accounts.update(code, json_payload()))

    @bp.route("/api/cost-centers", methods=["GET", "POST"])
    def cc_collection():
        if request.method == "GET":
            return jsonify(paginate_request(centers.list(), ("cCC1", "cCC2", "cDesc")))
        return jsonify(centers.create(json_payload())), 201

    @bp.route("/api/cost-centers/<cc1>", defaults={"cc2": ""}, methods=["GET", "PUT", "DELETE"])
    @bp.route("/api/cost-centers/<cc1>/<cc2>", methods=["GET", "PUT", "DELETE"])
    def cc_item(cc1, cc2):
        if request.method == "GET":
            return jsonify(centers.get(cc1, cc2))
        if request.method == "DELETE":
            centers.delete(cc1, cc2)
            return jsonify({"ok": True})
        centers.get(cc1, cc2)
        return jsonify(centers.update(cc1, cc2, json_payload()))

    return bp


def register(app: Flask, c: Container, seed: dict) -> None:
    accounts = c.register("gl_accounts", GLAccountService(store("gl_accounts")))
    centers = c.register("cost_centers", CostCenterService(store("cost_centers")))
    app.register_blueprint(_blueprint(accounts, centers))
    c.get("lookups").register("gl", accounts.lookup)
    c.get("lookups").register("cc", centers.lookup)
    c.get("seeds").add(accounts.repo, "gl", seed.get("gl_ttGL_data", []))
    c.get("seeds").add(centers.repo, "cc", seed.get("gl_ttCC_data", []))
