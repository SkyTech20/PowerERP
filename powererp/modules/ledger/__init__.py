"""General ledger module: GL accounts (/api/gl-accounts) and cost centers (/api/cost-centers).

The two are independent: the account says what the amount is (type asset, liability, equity, revenue or expense),
the cost center says which department (cCC1) or sub-department (cCC1 + cCC2) it is for. A purchase line names both
(AccountingCheck); an account can require a cost center. Lookups gl, cc, cc1 (departments), cc2 (?cc1=: its
sub-departments). Read by SkyAI through getGLaccounts.p (powererp.integrations / powerware_api).
"""

from __future__ import annotations

from flask import Blueprint, Flask, has_request_context, jsonify, request

from powererp import schemas as S
from powererp.container import Container
from powererp.core.errors import AppError, NotFound
from powererp.core.http import json_payload, require
from powererp.core.pagination import paginate_request
from powererp.core.values import text
from powererp.modules.common.forms import RecordForm, Row
from powererp.store import Store, store


class GLAccountService:
    """GL accounts: what an amount is (bank, stock, supplier, sale, expense…). The code of a screen URL must match
    exactly; duplicates ignore case. Type empty on create: guessed from the first digit of the code (TYPE_OF_DIGIT)."""

    def __init__(self, repo: Store):
        self.repo = repo
        self.form = RecordForm(S.GL_ACCOUNT, S.DEFAULTS["gl_accounts"])

    def list(self) -> list[Row]:
        return self.repo.all()

    def get(self, code: str) -> Row:
        row = self.repo.get(code, ci=False)
        if row is None:
            raise NotFound()
        return row

    def find(self, code: str) -> Row | None:
        return self.repo.get(text(code)) if text(code) else None

    def _apply(self, row: Row, payload: Row) -> Row:
        p = dict(payload)
        if "cType" in p and not text(p["cType"]):
            p["cType"] = guess_type(row["cCode"])
        self.form.apply(row, p, skip=("cCode",))
        require(row, "cDesc")
        return row

    def create(self, payload: Row) -> Row:
        require(payload, "cCode", "cDesc")
        code = text(payload["cCode"])
        if self.repo.get(code):
            raise AppError("duplicate", "cCode", 409)
        row = {**self.form.blank(), "cCode": code, "cType": guess_type(code)}
        self._apply(row, payload)
        self.repo.insert(row)
        return row

    def update(self, code: str, payload: Row) -> Row:
        row = self._apply(dict(self.get(code)), payload)
        self.repo.update(row)
        return row

    def delete(self, code: str) -> None:
        self.repo.delete(self.get(code))

    def lookup(self):
        en = _english()
        rows = [
            {"code": g["cCode"], "label": (g.get("cDescEN") if en else "") or g["cDesc"]}
            for g in self.repo.all()
            if g.get("lActive", True)
        ]
        return rows, 20


class CostCenterService:
    """Cost centers: who / where the money is spent. A department (cCC1, cCC2 empty) and its sub-departments
    (cCC1 + cCC2); a sub-department needs its department. Not tied to the GL accounts: a purchase line names both."""

    def __init__(self, repo: Store):
        self.repo = repo
        self.form = RecordForm(S.COST_CENTER, S.DEFAULTS["cost_centers"])

    def list(self) -> list[Row]:
        return self.repo.all()

    def get(self, cc1: str, cc2: str = "") -> Row:
        row = self.repo.get(cc1, cc2 or "", ci=False)
        if row is None:
            raise NotFound()
        return row

    def find(self, cc1: str, cc2: str = "") -> Row | None:
        return self.repo.get(text(cc1), text(cc2)) if text(cc1) else None

    def create(self, payload: Row) -> Row:
        require(payload, "cCC1", "cDesc")
        cc1, cc2 = text(payload["cCC1"]), text(payload.get("cCC2"))
        if self.repo.get(cc1, cc2, ci=False) or self.repo.get(cc1, cc2):
            raise AppError("duplicate", "cCC2" if cc2 else "cCC1", 409)
        if cc2 and self.find(cc1) is None:
            raise AppError("no_department", "cCC1")
        row = {**self.form.blank(), "cCC1": cc1, "cCC2": cc2}
        self.form.apply(row, payload, skip=("cCC1", "cCC2"))
        require(row, "cDesc")
        self.repo.insert(row)
        return row

    def update(self, cc1: str, cc2: str, payload: Row) -> Row:
        row = dict(self.get(cc1, cc2))
        self.form.apply(row, payload, skip=("cCC1", "cCC2"))
        require(row, "cDesc")
        self.repo.update(row)
        return row

    def delete(self, cc1: str, cc2: str) -> None:
        row = self.get(cc1, cc2)
        if not cc2 and any(c["cCC1"].upper() == cc1.upper() and c["cCC2"] for c in self.repo.all()):
            raise AppError("has_sub_departments", status=409)
        self.repo.delete(row)

    def _label(self, c: Row) -> str:
        return ((c.get("cDescEN") if _english() else "") or c["cDesc"]) if c else ""

    def lookup(self):
        rows = [
            {"code": f'{c["cCC1"]}-{c["cCC2"]}' if c["cCC2"] else c["cCC1"], "label": self._label(c)}
            for c in self.repo.all()
            if c.get("lActive", True)
        ]
        return rows, 20

    def departments_lookup(self):
        """The departments (cCC1) of a purchase line."""
        rows = [
            {"code": c["cCC1"], "label": self._label(c)}
            for c in self.repo.all()
            if not c["cCC2"] and c.get("lActive", True)
        ]
        return rows, 50

    def subs_lookup(self):
        """The sub-departments (cCC2) of the department given (?cc1=) of a purchase line."""
        cc1 = text(request.args.get("cc1")).upper() if has_request_context() else ""
        rows = [
            {"code": c["cCC2"], "label": self._label(c)}
            for c in self.repo.all()
            if c["cCC2"] and c["cCC1"].upper() == cc1 and c.get("lActive", True)
        ]
        return rows, 200


def _english() -> bool:
    """Is the list asked in English (?lang=en)? French otherwise, and outside a request."""
    return has_request_context() and request.args.get("lang") == "en"


def guess_type(code: str) -> str:
    """The usual type of an account of a Canadian chart of accounts, from the first digit of its code."""
    return TYPE_OF_DIGIT.get(text(code)[:1], "expense")


TYPE_OF_DIGIT = {"1": "asset", "2": "liability", "3": "equity", "4": "revenue"}


def normalize_accounts(rows: list[Row]) -> list[Row]:
    return [{**g, "cType": g.get("cType") or guess_type(g["cCode"]), "lActive": g.get("lActive", True)} for g in rows]


def normalize_centers(rows: list[Row]) -> list[Row]:
    return [{**cc, "lActive": cc.get("lActive", True)} for cc in rows]


class AccountingCheck:
    """The GL account and cost center of the purchase lines (supplier invoices, receptions): they must exist and be
    active, and an account marked Requires a cost center needs one. Empty stays allowed (filled later)."""

    def __init__(self, accounts: GLAccountService, centers: CostCenterService):
        self.accounts = accounts
        self.centers = centers

    def lines(self, lines: list[Row]) -> None:
        for i, ln in enumerate(lines, 1):
            gl, cc1, cc2 = text(ln.get("cGL")), text(ln.get("cCC1")), text(ln.get("cCC2"))
            if not (gl or cc1 or cc2):
                continue
            account = self.accounts.find(gl) if gl else None
            if gl and (account is None or not account.get("lActive", True)):
                raise AppError("unknown_gl", "lines", detail=f"{i}: {gl}")
            if cc2 and not cc1:
                raise AppError("no_department", "lines", detail=f"{i}: {cc2}")
            if cc1:
                center = self.centers.find(cc1, cc2)
                if center is None or not center.get("lActive", True):
                    raise AppError("unknown_cc", "lines", detail=f"{i}: {cc1}{'-' + cc2 if cc2 else ''}")
            if account and account.get("lRequiresCC") and not cc1:
                raise AppError("cc_required", "lines", detail=f"{i}: {gl}")


def _blueprint(accounts: GLAccountService, centers: CostCenterService) -> Blueprint:
    bp = Blueprint("ledger", __name__)

    @bp.route("/api/gl-accounts", methods=["GET", "POST"])
    def gl_collection():
        if request.method == "GET":
            return jsonify(paginate_request(accounts.list(), ("cCode", "cDesc", "cDescEN")))
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
            return jsonify(paginate_request(centers.list(), ("cCC1", "cCC2", "cDesc", "cDescEN")))
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
    c.register("accounting_check", AccountingCheck(accounts, centers))
    c.get("lookups").register("gl", accounts.lookup)
    c.get("lookups").register("cc", centers.lookup)
    c.get("lookups").register("cc1", centers.departments_lookup)
    c.get("lookups").register("cc2", centers.subs_lookup)
    c.get("dashboard").register(lambda: {"glAccounts": accounts.repo.count(), "costCenters": centers.repo.count()})
    lifecycle = c.get("lifecycle")
    lifecycle.add(accounts.repo, "gl", normalize_accounts(seed.get("gl_ttGL_data", [])))
    lifecycle.add(centers.repo, "cc", normalize_centers(seed.get("gl_ttCC_data", [])))

    def complete(data: dict) -> None:
        """Rows of a seed or of an older backup without type / active: guessed type, active."""
        if any("cType" not in g or "lActive" not in g for g in data.get("gl") or []):
            accounts.repo.replace_all(normalize_accounts(data["gl"]))
        if any("lActive" not in cc for cc in data.get("cc") or []):
            centers.repo.replace_all(normalize_centers(data["cc"]))

    lifecycle.after_load(complete)
