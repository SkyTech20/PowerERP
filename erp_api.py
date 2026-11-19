"""
PowerERP (demo ERP) — JSON API and static UI.

UI:  http://localhost:5050/
API: http://localhost:5050/api/<resource>

GL accounts, cost centers and suppliers (powererp.store), purchase orders, receptions and
invoices (powererp.purchasing) are relational tables, seeded from data/*.json (the inventory
module adds its own with add_stores). add_tables still accepts in-memory lists, saved by app.py
to legacy_datasets, for a module that has not moved yet; none uses it today.
POST /api/reset restores the original demo data.
"""
import copy
import re
from datetime import datetime
from pathlib import Path

from flask import Blueprint, jsonify, request, send_from_directory

from powererp import purchasing as purch
from powererp.store import store

ERP_STATIC_DIR = Path(__file__).resolve().parent / "static"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _s(value):
    """Normalize any incoming value to a trimmed string."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value).strip()


def _dec(value, default="0"):
    """Keep only the number of a typed amount ("$12.50", "12,50 $", "1 234.5") as "12.50"."""
    s = re.sub(r"[^\d,.\-]", "", _s(value))
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


def _num(value, default=0.0):
    try:
        return float(_dec(value, ""))
    except (TypeError, ValueError, AttributeError):
        return default


def _money(value):
    return f"{_num(value):.2f}"


def _qty(value):
    q = _num(value)
    return f"{q:.0f}" if q == int(q) else f"{q:.2f}"


def _bool(value):
    return value in (True, "true", "True", 1, "1", "on", "yes")


class ApiError(Exception):
    def __init__(self, code, field=None, status=400, detail=None):
        super().__init__(code)
        self.code = code
        self.field = field
        self.status = status
        self.detail = detail


def _require(payload, *fields):
    for f in fields:
        if not _s(payload.get(f)):
            raise ApiError("required", f)


def _paginate(rows, search_fields):
    """Filter (q), sort (sort, dir) and paginate (page, size) a list of dicts."""
    q = (request.args.get("q") or "").strip().lower()
    if q:
        rows = [r for r in rows if any(q in _s(r.get(f)).lower() for f in search_fields)]
    for key, val in request.args.items():
        if key.startswith("f_") and val != "":
            field = key[2:]
            rows = [r for r in rows if _s(r.get(field)).lower() == val.lower()]
    sort = request.args.get("sort")
    if sort:
        reverse = request.args.get("dir") == "desc"

        def sort_key(r):
            v = r.get(sort)
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                return (0, v, "")
            sv = _s(v)
            try:
                return (0, float(sv), "")
            except ValueError:
                return (1, 0, sv.lower())

        rows = sorted(rows, key=sort_key, reverse=reverse)
    total = len(rows)
    try:
        size = max(1, min(int(request.args.get("size", 25)), 500))
        page = max(1, int(request.args.get("page", 1)))
    except ValueError:
        size, page = 25, 1
    start = (page - 1) * size
    return {"total": total, "page": page, "size": size, "items": rows[start:start + size]}


# ---------------------------------------------------------------------------
# Seed data for invoices
# ---------------------------------------------------------------------------

_SEED_INVOICES = [
    {
        "cNoFourn": "ZEPMAN", "cNoFacture": "ZM-48812", "dDateFacture": "2026-09-02",
        "cNoCommAch": "", "cDevise": "CAD", "cStatut": "Posted", "cSource": "ERP",
        "dTransport": "0.00", "dTotalTPS": "12.50", "dTotalTVP": "24.94",
        "lines": [
            {"cCodeProduit": "CLEAN-01", "cDescription": "Industrial degreaser 20L", "dQuantite": "2",
             "dCoutUnitaire": "125.00", "cGL": "5960", "cCC1": "100", "cCC2": "215", "iNoReception": ""},
        ],
    },
    {
        "cNoFourn": "MANSCO", "cNoFacture": "SC-2024-0311", "dDateFacture": "2024-03-15",
        "cNoCommAch": "266009", "cDevise": "CAD", "cStatut": "Approved", "cSource": "ERP",
        "dTransport": "15.00", "dTotalTPS": "0.00", "dTotalTVP": "0.00",
        "lines": [
            {"cCodeProduit": "AIR00276", "cDescription": "MRFCP.08.1/8 Flow regulator", "dQuantite": "10",
             "dCoutUnitaire": "8.82", "cGL": "", "cCC1": "", "cCC2": "", "iNoReception": "335871"},
            {"cCodeProduit": "AIR00273", "cDescription": "MRFCP.1/4.1/4 Flow regulator", "dQuantite": "10",
             "dCoutUnitaire": "8.82", "cGL": "", "cCC1": "", "cCC2": "", "iNoReception": "335871"},
        ],
    },
    {
        "cNoFourn": "RE3DIS", "cNoFacture": "INV-77120", "dDateFacture": "2026-09-20",
        "cNoCommAch": "", "cDevise": "CAD", "cStatut": "Draft", "cSource": "ERP",
        "dTransport": "0.00", "dTotalTPS": "22.50", "dTotalTVP": "44.89",
        "lines": [
            {"cCodeProduit": "SIGN", "cDescription": "Trade show banners", "dQuantite": "3",
             "dCoutUnitaire": "150.00", "cGL": "5960", "cCC1": "100", "cCC2": "400", "iNoReception": ""},
        ],
    },
]


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


def register_erp(app, ns):
    """
    Mount the ERP on `app`.
    `ns` is a dict holding the data lists (see app.py: load_data()).
    """
    # Relational tables (seeded from these lists, which are not used afterwards)
    gl_db, cc_db, sup_db = store("gl_accounts"), store("cost_centers"), store("suppliers")
    stores = [(gl_db, "gl", ns["gl_ttGL_data"]), (cc_db, "cc", ns["gl_ttCC_data"]),
              (sup_db, "suppliers", ns["supplier_terms_data"])]
    # Seed of the purchasing tables (the lists are not used afterwards)
    seed_lists = {"po_details": ns["po_details"], "unbilled_po": ns["unbilled_po"],
                  "receiving_details": ns["receiving_details"], "unbilled_receiving": ns["unbilled_receiving"]}
    seed_invoices = []
    # Tables, lookups and dashboard figures added by other modules (inventory_api.py)
    extra = {"tables": [], "stores": [], "lookups": {}, "summary": [], "after_load": [], "on_clear": []}

    def _add_invoice(inv):
        if seeding["on"]:
            inv["id"] = len(seed_invoices) + 1
            _compute_invoice(inv)
            seed_invoices.append(inv)
            return inv
        inv["id"] = purch.next_number("AP_INVOICE")
        _compute_invoice(inv)
        purch.inv_put(inv)
        return inv

    bp = Blueprint("erp", __name__)
    seeding = {"on": False}  # the seed invoices are prepared at start-up, from the seed suppliers

    @bp.errorhandler(ApiError)
    def _api_error(err):
        body = {"error": err.code}
        if err.field:
            body["field"] = err.field
        if err.detail:
            body["detail"] = err.detail
        return jsonify(body), err.status

    def _payload():
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            raise ApiError("invalid_body")
        return data


    def _supplier_name(code):
        if not _s(code):
            return ""
        if seeding["on"]:
            s = next((x for x in ns["supplier_terms_data"] if x["cCode"].upper() == _s(code).upper()), None)
        else:
            s = sup_db.get(_s(code))
        return s["cName"] if s else ""

    # ---------------- Static UI ----------------

    @bp.route("/")
    def erp_index():
        return send_from_directory(ERP_STATIC_DIR, "index.html")

    @bp.route("/assets/<path:filename>")
    def erp_assets(filename):
        return send_from_directory(ERP_STATIC_DIR, filename)

    # ---------------- Meta ----------------

    @bp.route("/api/summary")
    def erp_summary():
        pos, recs, invoices = purch.po_all(), purch.rec_all(), purch.inv_all()
        open_inv = [i for i in invoices if i.get("cStatut") in ("Draft", "Approved")]
        return jsonify({
            "glAccounts": gl_db.count(),
            "costCenters": cc_db.count(),
            "suppliers": sup_db.count(),
            "activeSuppliers": sup_db.count(lambda c: [c["iStatutAch"] == 1]),
            "purchaseOrders": len(pos),
            "unbilledPOs": sum(1 for _n, _d, u in pos if u is not None),
            "receptions": len(recs),
            "unbilledReceptions": sum(1 for _n, _d, u in recs if u is not None),
            "invoices": len(invoices),
            "openInvoices": len(open_inv),
            "openInvoicesAmount": round(sum(_num(i.get("dTotalFacture")) for i in open_inv), 2),
            "recentInvoices": [{**i, "lineCount": len(i.get("lines", []))}
                               for i in sorted(invoices, key=lambda i: i["id"], reverse=True)[:5]],
            **{k: v for fn in extra["summary"] for k, v in fn().items()},
        })

    @bp.route("/api/lookups/<kind>")
    def erp_lookup(kind):
        q = (request.args.get("q") or "").strip().lower()
        limit = 20
        if kind == "suppliers":
            rows = [{"code": s["cCode"], "label": s["cName"]} for s in sup_db.all()]
        elif kind == "gl":
            rows = [{"code": g["cCode"], "label": g["cDesc"]} for g in gl_db.all()]
        elif kind == "cc":
            rows = [{"code": f'{c["cCC1"]}-{c["cCC2"]}' if c["cCC2"] else c["cCC1"], "label": c["cDesc"]}
                    for c in cc_db.all()]
        elif kind == "po":
            rows = [{"code": p["cPO"], "label": p["cSupplierName"]} for p in _all_pos()]
        elif kind == "terms":
            seen = {}
            for s in sup_db.all():
                if s["cTermCode"] and s["cTermCode"] not in seen:
                    seen[s["cTermCode"]] = s["cTermDesc"]
            rows = [{"code": k, "label": v} for k, v in sorted(seen.items())]
            limit = 200
        elif kind == "buyers":
            seen = {}
            for s in sup_db.all():
                if s["cCodeAch"] and s["cCodeAch"] not in seen:
                    seen[s["cCodeAch"]] = s["cDescAch"]
            rows = [{"code": k, "label": v} for k, v in sorted(seen.items())]
            limit = 200
        elif kind in extra["lookups"]:
            rows, limit = extra["lookups"][kind]()
        else:
            raise ApiError("not_found", status=404)
        if q:
            rows = [r for r in rows if q in r["code"].lower() or q in (r["label"] or "").lower()]
        return jsonify(rows if request.args.get("all") else rows[:limit])

    def _tables():
        """The tables of other modules still kept as in-memory lists (saved as JSON in legacy_datasets)."""
        return tuple(extra["tables"])

    PURCHASING_KEYS = ("po_details", "unbilled_po", "receiving_details", "unbilled_receiving", "invoices")

    def add_tables(pairs):
        """Other modules' tables ((list, key), ...): saved, loaded, reset and cleared with the ERP's."""
        extra["tables"].extend(pairs)
        for target, key in pairs:
            snapshot[key] = copy.deepcopy(target)

    def add_stores(triples):
        """Other modules' relational tables ((store, key, seed rows), ...): seeded, reset and cleared with the ERP's."""
        extra["stores"].extend(triples)
        for _st, key, rows in triples:
            snapshot[key] = copy.deepcopy(rows)

    def _all_stores():
        return [(st, key) for st, key, _rows in stores + extra["stores"]]

    def dump():
        """The in-memory ERP tables, for legacy_datasets."""
        return {key: target for target, key in _tables()}

    def load(data):
        """Replace the ERP tables (lists in place: powerware_api shares them). Keys of relational tables
        (old JSON datasets, or the reset snapshot) are loaded into those tables. Needs a database session."""
        for target, key in _tables():
            if key in data:
                target[:] = data[key]
        for st, key in _all_stores():
            if key in data:
                st.replace_all(data[key])
        if "po_details" in data or "unbilled_po" in data:
            purch.po_replace_all(data.get("po_details", []), data.get("unbilled_po", []))
        if "receiving_details" in data or "unbilled_receiving" in data:
            purch.rec_replace_all(data.get("receiving_details", []), data.get("unbilled_receiving", []))
        if "invoices" in data:
            purch.inv_replace_all(data["invoices"])
        for fn in extra["after_load"]:  # e.g. the stock balances, recalculated from the movements
            fn(data)

    def store_keys():
        return [key for _st, key in _all_stores()] + list(PURCHASING_KEYS)

    def seed():
        """Load the original data (empty database or other dataset)."""
        load(copy.deepcopy(snapshot))

    @bp.route("/api/reset", methods=["POST"])
    def erp_reset():
        seed()
        return jsonify({"ok": True})

    @bp.route("/api/clear", methods=["POST"])
    def erp_clear():
        """Empty every table (for demos that start from a blank ERP). /api/reset brings the demo data back."""
        for target, _key in _tables():
            target[:] = []
        for fn in extra["on_clear"]:
            fn()
        purch.inv_clear()
        purch.rec_clear()
        purch.po_clear()
        for st, _key in reversed(_all_stores()):
            st.clear()
        return jsonify({"ok": True})

    # ---------------- GL accounts ----------------

    @bp.route("/api/gl-accounts", methods=["GET", "POST"])
    def gl_collection():
        if request.method == "GET":
            return jsonify(_paginate(gl_db.all(), ("cCode", "cDesc")))
        p = _payload()
        _require(p, "cCode", "cDesc")
        code = _s(p["cCode"])
        if gl_db.get(code):
            raise ApiError("duplicate", "cCode", 409)
        row = {"cCode": code, "cDesc": _s(p["cDesc"])}
        gl_db.insert(row)
        return jsonify(row), 201

    @bp.route("/api/gl-accounts/<code>", methods=["GET", "PUT", "DELETE"])
    def gl_item(code):
        row = gl_db.get(code, ci=False)
        if row is None:
            raise ApiError("not_found", status=404)
        if request.method == "GET":
            return jsonify(row)
        if request.method == "DELETE":
            gl_db.delete(row)
            return jsonify({"ok": True})
        p = _payload()
        _require(p, "cDesc")
        row["cDesc"] = _s(p["cDesc"])
        gl_db.update(row)
        return jsonify(row)

    # ---------------- Cost centers (key: cCC1 + cCC2) ----------------

    def _cc_find(cc1, cc2):
        return cc_db.get(cc1, cc2 or "", ci=False)

    @bp.route("/api/cost-centers", methods=["GET", "POST"])
    def cc_collection():
        if request.method == "GET":
            return jsonify(_paginate(cc_db.all(), ("cCC1", "cCC2", "cDesc")))
        p = _payload()
        _require(p, "cCC1", "cDesc")
        cc1, cc2 = _s(p["cCC1"]), _s(p.get("cCC2"))
        if _cc_find(cc1, cc2):
            raise ApiError("duplicate", "cCC2" if cc2 else "cCC1", 409)
        if cc_db.get(cc1, cc2):
            raise ApiError("duplicate", "cCC2" if cc2 else "cCC1", 409)
        row = {"cCC1": cc1, "cCC2": cc2, "cDesc": _s(p["cDesc"])}
        cc_db.insert(row)
        return jsonify(row), 201

    @bp.route("/api/cost-centers/<cc1>", defaults={"cc2": ""}, methods=["GET", "PUT", "DELETE"])
    @bp.route("/api/cost-centers/<cc1>/<cc2>", methods=["GET", "PUT", "DELETE"])
    def cc_item(cc1, cc2):
        row = _cc_find(cc1, cc2)
        if row is None:
            raise ApiError("not_found", status=404)
        if request.method == "GET":
            return jsonify(row)
        if request.method == "DELETE":
            cc_db.delete(row)
            return jsonify({"ok": True})
        p = _payload()
        _require(p, "cDesc")
        row["cDesc"] = _s(p["cDesc"])
        cc_db.update(row)
        return jsonify(row)

    # ---------------- Suppliers (getSupplierTerm.p) ----------------

    _SUPPLIER_STR = ("cName", "cTermCode", "cTermDesc", "cAddress1", "cAddress2", "cCity", "cProvince",
                     "cCountry", "cZipCode", "cNoTPS", "cNoTVQ", "cCodeAch", "cDescAch", "cDeptSauv")

    def _supplier_apply(row, p):
        for f in _SUPPLIER_STR:
            if f in p:
                row[f] = _s(p[f])
        for f in ("iTypePO", "iStatutAch"):
            if f in p:
                row[f] = int(_num(p[f]))

    @bp.route("/api/suppliers", methods=["GET", "POST"])
    def supplier_collection():
        if request.method == "GET":
            return jsonify(_paginate(sup_db.all(), ("cCode", "cName", "cCity", "cTermCode", "cDescAch")))
        p = _payload()
        _require(p, "cCode", "cName")
        code = _s(p["cCode"])
        if sup_db.get(code):
            raise ApiError("duplicate", "cCode", 409)
        row = {"cCode": code, **{f: "" for f in _SUPPLIER_STR}, "iTypePO": 1, "iStatutAch": 1}
        _supplier_apply(row, p)
        sup_db.insert(row)
        return jsonify(row), 201

    @bp.route("/api/suppliers/<code>", methods=["GET", "PUT", "DELETE"])
    def supplier_item(code):
        row = sup_db.get(code, ci=False)
        if row is None:
            raise ApiError("not_found", status=404)
        if request.method == "GET":
            return jsonify(row)
        if request.method == "DELETE":
            sup_db.delete(row)
            return jsonify({"ok": True})
        p = _payload()
        _require(p, "cName")
        _supplier_apply(row, p)
        sup_db.update(row)
        return jsonify(row)

    # ---------------- Purchase orders (getPODetails.p + getUnbilledPO.p) ----------------

    _PO_HEADER_STR = ("cSupplierCode", "cSupplierName", "cBuyerCode", "cBuyerName", "cApplicantCode", "dOrderDate")

    def _po_view(cpo, records=None):
        det, unb = records if records is not None else purch.po_get(cpo)
        if det is None and unb is None:
            return None
        h = (det or {}).get("ttPOheader", {})
        lines = []
        for ln in (det or {}).get("ttPOdetail", []):
            lines.append({
                "cUnique": _s(ln.get("cUnique")), "cProductcode": _s(ln.get("cProductcode")),
                "cProductDesc": _s(ln.get("cProductDesc")), "dQuantity": _s(ln.get("dQuantity")),
                "dUnitCost": _s(ln.get("dUnitCost")),
                "dTotalAmount": _s(ln.get("dTotalAmount")) or _money(_num(ln.get("dQuantity")) * _num(ln.get("dUnitCost"))),
            })
        sub = _s(h.get("dSubTotal")) or _money(sum(_num(l["dTotalAmount"]) for l in lines))
        return {
            "cPO": cpo,
            "COMPANY": (det or unb).get("COMPANY", "MA2"),
            "dCreationDate": _s((unb or {}).get("dCreationDate")) or _s(h.get("dOrderDate")),
            "cSupplierCode": _s(h.get("cSupplierCode")) or _s((unb or {}).get("cSupplierCode")),
            "cSupplierName": _s(h.get("cSupplierName")) or _s((unb or {}).get("cSupplierName")),
            "cBuyerCode": _s(h.get("cBuyerCode")), "cBuyerName": _s(h.get("cBuyerName")),
            "cApplicantCode": _s(h.get("cApplicantCode")),
            "dDueDate": _s(h.get("dDueDate")), "cReference": _s(h.get("cReference")), "cSource": _s(h.get("cSource")),
            "lBlanketOrder": _bool((unb or {}).get("lBlanketOrder")),
            "lUnbilled": unb is not None,
            "dSubTotal": sub, "dFreight": _s(h.get("dFreight")), "dGST": _s(h.get("dGST")),
            "dPST": _s(h.get("dPST")),
            "dTotalAmount": _s(h.get("dTotalAmount")) or _money(
                _num(sub) + _num(h.get("dFreight")) + _num(h.get("dGST")) + _num(h.get("dPST"))),
            "lines": lines,
            "lineCount": len(lines),
        }

    def _all_pos():
        return [_po_view(no, (det, unb)) for no, det, unb in purch.po_all()]

    def _po_save(cpo, p, existing):
        company = _s(p.get("COMPANY")) or "MA2"
        if _s(p.get("cSupplierCode")) and not _s(p.get("cSupplierName")):
            p["cSupplierName"] = _supplier_name(p["cSupplierCode"])
        lines = []
        for i, ln in enumerate(p.get("lines") or [], start=1):
            if not _s(ln.get("cProductcode")) and not _s(ln.get("cProductDesc")):
                continue
            total = _num(ln.get("dQuantity")) * _num(ln.get("dUnitCost"))
            lines.append({
                "cUnique": _s(ln.get("cUnique")) or str(i), "cProductcode": _s(ln.get("cProductcode")),
                "cProductDesc": _s(ln.get("cProductDesc")), "dQuantity": _qty(ln.get("dQuantity")),
                "dUnitCost": _dec(ln.get("dUnitCost")), "dTotalAmount": _money(total),
            })
        sub = sum(_num(l["dTotalAmount"]) for l in lines)
        freight, gst, pst = _num(p.get("dFreight")), _num(p.get("dGST")), _num(p.get("dPST"))
        header = {f: _s(p.get(f)) for f in _PO_HEADER_STR}
        header["dOrderDate"] = header["dOrderDate"] or _s(p.get("dCreationDate"))
        header.update({"dSubTotal": _money(sub), "dFreight": _money(freight), "dGST": _money(gst),
                       "dPST": _money(pst), "dTotalAmount": _money(sub + freight + gst + pst)})

        det, unb = purch.po_get(cpo)
        if det is None:
            det = {"COMPANY": company, "cPO": cpo, "ttPOheader": {}, "ttPOdetail": []}
        det["COMPANY"] = company
        det["ttPOheader"].update(header)
        det["ttPOdetail"] = lines

        if _bool(p.get("lUnbilled", True)):
            if unb is None:
                unb = {"COMPANY": company, "cPO": cpo}
            unb.update({
                "COMPANY": company, "dCreationDate": _s(p.get("dCreationDate")) or datetime.now().strftime("%Y-%m-%d"),
                "cSupplierName": header["cSupplierName"], "cSupplierCode": header["cSupplierCode"],
                "lBlanketOrder": _bool(p.get("lBlanketOrder")),
            })
        else:
            unb = None
        purch.po_put(cpo, det, unb)
        return _po_view(cpo, (det, unb))

    def _po_update_header(cpo, fields):
        """Add header fields to a saved PO (due date, reference, source of the POs created by services)."""
        det, unb = purch.po_get(cpo)
        det["ttPOheader"].update(fields)
        purch.po_put(cpo, det, unb)

    @bp.route("/api/purchase-orders", methods=["GET", "POST"])
    def po_collection():
        if request.method == "GET":
            rows = [{k: v for k, v in r.items() if k != "lines"} for r in _all_pos()]
            return jsonify(_paginate(rows, ("cPO", "cSupplierCode", "cSupplierName", "cBuyerName")))
        p = _payload()
        _require(p, "cPO", "cSupplierCode")
        cpo = _s(p["cPO"])
        if _po_view(cpo):
            raise ApiError("duplicate", "cPO", 409)
        return jsonify(_po_save(cpo, p, None)), 201

    @bp.route("/api/purchase-orders/<cpo>", methods=["GET", "PUT", "DELETE"])
    def po_item(cpo):
        view = _po_view(cpo)
        if view is None:
            raise ApiError("not_found", status=404)
        if request.method == "GET":
            return jsonify(view)
        if request.method == "DELETE":
            purch.po_put(cpo, None, None)
            return jsonify({"ok": True})
        p = _payload()
        _require(p, "cSupplierCode")
        return jsonify(_po_save(cpo, p, view))

    # ---------------- Receptions (getReceivingDetails.p + getUnbilledReceiving.p) ----------------

    _REC_STR = ("DateReception", "NoBonCommande", "CodeFournisseur", "Fournisseur", "Statut", "Entrepot",
                "ResponsableReception", "Commentaires")

    def _rec_view(no, records=None):
        det, unb = records if records is not None else purch.rec_get(no)
        if det is None and unb is None:
            return None
        src = det or unb
        lines = []
        for a in (det or {}).get("Articles", []):
            unit = a.get("PrixUnitaire") or a.get("dUnitCost") or ""
            lines.append({
                "CodeArticle": _s(a.get("CodeArticle")), "Description": _s(a.get("Description")),
                "QuantiteCommandee": _s(a.get("QuantiteCommandee")), "QuantiteRecue": _s(a.get("QuantiteRecue")),
                "PrixUnitaire": _s(unit), "cGL": _s(a.get("cGL")), "cCC1": _s(a.get("cCC1")),
                "cCC2": _s(a.get("cCC2")),
                "Montant": _s(a.get("dTotalAmount")) or _money(_num(a.get("QuantiteRecue")) * _num(unit)),
            })
        total = _s((det or {}).get("MontantTotal")) or _s((unb or {}).get("MontantRecu"))
        return {
            "NoReception": no, "COMPANY": src.get("COMPANY", "MA2"),
            "DateReception": _s(src.get("DateReception")), "NoBonCommande": _s(src.get("NoBonCommande")),
            "CodeFournisseur": _s(src.get("CodeFournisseur")), "Fournisseur": _s(src.get("Fournisseur")),
            "Statut": _s((det or {}).get("Statut")), "Entrepot": _s(src.get("Entrepot")),
            "ResponsableReception": _s((det or {}).get("ResponsableReception")),
            "Commentaires": _s((det or {}).get("Commentaires")),
            "Devise": _s((unb or {}).get("Devise")) or next(
                (_s(a.get("Devise")) for a in (det or {}).get("Articles", []) if a.get("Devise")), "CAD"),
            "SousTotal": _s((det or {}).get("SousTotal")), "Transport": _s((det or {}).get("Transport")),
            "TPS": _s((det or {}).get("TPS")), "TVQ": _s((det or {}).get("TVQ")),
            "MontantTotal": total, "lUnbilled": unb is not None,
            "lines": lines, "lineCount": len(lines),
        }

    def _all_recs():
        return [_rec_view(no, (det, unb)) for no, det, unb in purch.rec_all()]

    def _rec_save(no, p):
        company = _s(p.get("COMPANY")) or "MA2"
        if _s(p.get("CodeFournisseur")) and not _s(p.get("Fournisseur")):
            p["Fournisseur"] = _supplier_name(p["CodeFournisseur"])
        devise = _s(p.get("Devise")) or "CAD"
        articles = []
        for ln in p.get("lines") or []:
            if not _s(ln.get("CodeArticle")) and not _s(ln.get("Description")):
                continue
            amount = _num(ln.get("QuantiteRecue")) * _num(ln.get("PrixUnitaire"))
            articles.append({
                "CodeArticle": _s(ln.get("CodeArticle")), "Description": _s(ln.get("Description")),
                "QuantiteCommandee": _qty(ln.get("QuantiteCommandee")), "QuantiteRecue": _qty(ln.get("QuantiteRecue")),
                "PrixUnitaire": _dec(ln.get("PrixUnitaire")), "Devise": devise,
                "dTotalAmount": _money(amount),
                "cGL": _s(ln.get("cGL")), "cCC1": _s(ln.get("cCC1")), "cCC2": _s(ln.get("cCC2")),
            })
        sub = sum(_num(a["dTotalAmount"]) for a in articles)
        freight, tps, tvq = _num(p.get("Transport")), _num(p.get("TPS")), _num(p.get("TVQ"))
        total = sub + freight + tps + tvq

        det, unb = purch.rec_get(no)
        if det is None:
            det = {"NoReception": no}
        det.update({f: _s(p.get(f)) for f in _REC_STR})
        det.update({"COMPANY": company, "Articles": articles, "SousTotal": _money(sub),
                    "Transport": _money(freight), "TPS": _money(tps), "TVQ": _money(tvq),
                    "MontantTotal": _money(total)})

        if _bool(p.get("lUnbilled", True)):
            if unb is None:
                unb = {"NoReception": no, "StatutFacturation": "En attente de facture", "JoursEnAttente": "0",
                       "ResponsableFacturation": "Comptabilité", "PrioriteFacturation": "Normale",
                       "TypeReception": "Standard"}
            unb.update({"COMPANY": company, "DateReception": det["DateReception"],
                        "NoBonCommande": det["NoBonCommande"], "Fournisseur": det["Fournisseur"],
                        "CodeFournisseur": det["CodeFournisseur"], "MontantRecu": _money(total),
                        "Devise": devise, "Entrepot": det["Entrepot"]})
        else:
            unb = None
        purch.rec_put(no, det, unb)
        return _rec_view(no, (det, unb))

    @bp.route("/api/receptions", methods=["GET", "POST"])
    def rec_collection():
        if request.method == "GET":
            rows = [{k: v for k, v in r.items() if k != "lines"} for r in _all_recs()]
            return jsonify(_paginate(rows, ("NoReception", "NoBonCommande", "CodeFournisseur", "Fournisseur")))
        p = _payload()
        _require(p, "NoReception", "NoBonCommande", "DateReception")
        no = _s(p["NoReception"])
        if not no.isdigit():
            raise ApiError("numeric", "NoReception")
        if _rec_view(no):
            raise ApiError("duplicate", "NoReception", 409)
        return jsonify(_rec_save(no, p)), 201

    @bp.route("/api/receptions/<no>", methods=["GET", "PUT", "DELETE"])
    def rec_item(no):
        view = _rec_view(no)
        if view is None:
            raise ApiError("not_found", status=404)
        if request.method == "GET":
            return jsonify(view)
        if request.method == "DELETE":
            purch.rec_put(no, None, None)
            return jsonify({"ok": True})
        p = _payload()
        _require(p, "NoBonCommande", "DateReception")
        return jsonify(_rec_save(no, p))

    # ---------------- Invoices ----------------

    def _compute_invoice(inv):
        lines = []
        for ln in inv.get("lines") or []:
            if not _s(ln.get("cCodeProduit")) and not _s(ln.get("cDescription")) and not _num(ln.get("dMontant")):
                continue
            qty, unit = _num(ln.get("dQuantite"), 1), _num(ln.get("dCoutUnitaire"))
            amount = qty * unit if unit else _num(ln.get("dMontant"))
            lines.append({
                "cCodeProduit": _s(ln.get("cCodeProduit")) or "LINE", "cDescription": _s(ln.get("cDescription")),
                "dQuantite": _qty(qty), "dCoutUnitaire": _money(unit if unit else amount / (qty or 1)),
                "dMontant": _money(amount), "cGL": _s(ln.get("cGL")), "cCC1": _s(ln.get("cCC1")),
                "cCC2": _s(ln.get("cCC2")), "iNoReception": _s(ln.get("iNoReception")),
            })
        inv["lines"] = lines
        sub = sum(_num(l["dMontant"]) for l in lines)
        inv["dSousTotal"] = _money(sub)
        for f in ("dTransport", "dTotalTPS", "dTotalTVP"):
            inv[f] = _money(inv.get(f))
        if not inv.get("_keepTotal"):
            inv["dTotalFacture"] = _money(sub + _num(inv["dTransport"]) + _num(inv["dTotalTPS"]) + _num(inv["dTotalTVP"]))
        inv.pop("_keepTotal", None)
        inv["cNomFourn"] = _supplier_name(inv.get("cNoFourn")) or _s(inv.get("cNomFourn"))
        inv["lineCount"] = len(lines)
        return inv

    _INV_STR = ("cNoFourn", "cNoFacture", "dDateFacture", "cNoCommAch", "cDevise", "cStatut")

    def _inv_from_payload(p, inv):
        for f in _INV_STR:
            if f in p:
                inv[f] = _s(p[f])
        for f in ("dTransport", "dTotalTPS", "dTotalTVP"):
            inv[f] = p.get(f, inv.get(f))
        inv["lines"] = p.get("lines") or []
        inv["cDevise"] = inv.get("cDevise") or "CAD"
        inv["cStatut"] = inv.get("cStatut") or "Draft"
        return _compute_invoice(inv)

    def _mark_billed(inv):
        """An invoice bills the receptions on its lines (iNoReception); an invoice with a PO and
        no reception numbers bills every open reception of that PO. Billed receptions leave
        getUnbilledReceiving.p, and a PO whose receptions are all billed leaves getUnbilledPO.p."""
        recs = {_s(ln.get("iNoReception")) for ln in inv.get("lines") or []} - {"", "0"}
        po = _s(inv.get("cNoCommAch"))
        all_recs = purch.rec_all()
        unbilled_receiving = [u for _n, _d, u in all_recs if u is not None]
        if po and not recs:
            recs = {r["NoReception"] for r in unbilled_receiving if _s(r.get("NoBonCommande")) == po}
        if not recs:
            return
        pos = {po} if po else set()
        pos |= {_s(r.get("NoBonCommande")) for _n, d, u in all_recs for r in (d, u)
                if r is not None and r["NoReception"] in recs}
        purch.rec_set_billed(recs)
        still_open = {_s(r.get("NoBonCommande")) for r in unbilled_receiving if r["NoReception"] not in recs}
        purch.po_set_billed([p["cPO"] for p in purch.unbilled_po_list()
                             if p["cPO"] in pos - {""} and p["cPO"] not in still_open])

    def _inv_duplicate(supplier, number, exclude_id=None):
        return purch.inv_duplicate(supplier, number, exclude_id)

    @bp.route("/api/invoices", methods=["GET", "POST"])
    def inv_collection():
        if request.method == "GET":
            rows = [{**{k: v for k, v in i.items() if k != "lines"}, "lineCount": len(i.get("lines", []))}
                    for i in purch.inv_all()]
            return jsonify(_paginate(rows, ("cNoFacture", "cNoFourn", "cNomFourn", "cNoCommAch")))
        p = _payload()
        _require(p, "cNoFourn", "cNoFacture", "dDateFacture")
        if _inv_duplicate(_s(p["cNoFourn"]), _s(p["cNoFacture"])):
            raise ApiError("duplicate", "cNoFacture", 409)
        inv = _inv_from_payload(p, {"cSource": "ERP"})
        inv["id"] = purch.next_number("AP_INVOICE")
        purch.inv_put(inv)
        _mark_billed(inv)
        return jsonify(inv), 201

    @bp.route("/api/invoices/<int:inv_id>", methods=["GET", "PUT", "DELETE"])
    def inv_item(inv_id):
        inv = purch.inv_get(inv_id)
        if inv is None:
            raise ApiError("not_found", status=404)
        if request.method == "GET":
            return jsonify({**inv, "lineCount": len(inv.get("lines", []))})
        if request.method == "DELETE":
            purch.inv_delete(inv_id)
            return jsonify({"ok": True})
        p = _payload()
        _require(p, "cNoFourn", "cNoFacture", "dDateFacture")
        if _inv_duplicate(_s(p["cNoFourn"]), _s(p["cNoFacture"]), inv_id):
            raise ApiError("duplicate", "cNoFacture", 409)
        _inv_from_payload(p, inv)
        purch.inv_put(inv)
        _mark_billed(inv)
        return jsonify(inv)

    # The demo dataset starts without invoices (app.py passes seed_invoices=[]).
    seeding["on"] = True
    for seed_inv in ns.get("seed_invoices", _SEED_INVOICES):
        _add_invoice(copy.deepcopy(seed_inv))
    seeding["on"] = False

    snapshot = copy.deepcopy({
        **{key: rows for _st, key, rows in stores}, **seed_lists, "invoices": seed_invoices,
    })

    app.register_blueprint(bp)

    # ---------------- Invoices created by SkyAI (PowerWARE apInvoice*.p) ----------------

    def invoice_exists(supplier, number):
        return _inv_duplicate(supplier, number)

    def record_invoice(header, lines, with_po):
        """Create an ERP invoice from a PowerWARE dsInput (ttInputHD / ttInputDT)."""
        po = header.get("cNoCommAch", "")
        inv = {
            "cNoFourn": header.get("cNoFourn", ""), "cNoFacture": header.get("cNoFacture", ""),
            "dDateFacture": header.get("dDateFacture", "") or datetime.now().strftime("%Y-%m-%d"),
            "cNoCommAch": po, "cDevise": "CAD",
            "cStatut": "Draft" if _bool(header.get("lIncomplete")) else "Posted",
            "cSource": "SkyAI", "dTransport": header.get("dTransport", "0"),
            "dTotalTPS": header.get("dTotalTPS", "0"), "dTotalTVP": header.get("dTotalTVP", "0"), "lines": [],
        }
        for d in lines:
            rec_no = d.get("iNoReception", "")
            rec_no = "" if rec_no in ("", "0") else rec_no
            code = d.get("cCodeProduit", "")
            desc = ""
            if rec_no:
                rec = purch.rec_get(rec_no)[0]
                art = next((a for a in (rec or {}).get("Articles", []) if a.get("CodeArticle") == code), None)
                desc = (art or {}).get("Description", "")
                inv["cDevise"] = (art or {}).get("Devise") or inv["cDevise"]
            inv["lines"].append({
                "cCodeProduit": code, "cDescription": desc,
                "dQuantite": d.get("dQteFacturee") or d.get("dQuantite") or "1",
                "dCoutUnitaire": d.get("dCoutUnitaire", ""), "dMontant": d.get("dMontant", ""),
                "cGL": d.get("cGL", ""), "cCC1": d.get("cCC1", ""), "cCC2": d.get("cCC2", ""),
                "iNoReception": rec_no,
            })
        if header.get("dTotalFacture"):
            inv["dTotalFacture"] = _money(header["dTotalFacture"])
            inv["_keepTotal"] = True
        _add_invoice(inv)
        # Invoiced receptions (and fully invoiced POs) are no longer "unbilled"
        _mark_billed(inv)
        return inv

    def po_exists(cpo):
        return _po_view(cpo) is not None

    def next_po_number(first):
        """Next PO number: from the "PO" sequence, never below `first` nor an existing (typed) number."""
        nums = [int(no) for no, _d, _u in purch.po_all() if str(no).isdigit()]
        return str(purch.next_number("PO", start=first, minimum=max([first - 1] + nums) + 1))

    return {"invoice_exists": invoice_exists, "record_invoice": record_invoice, "dump": dump, "load": load,
            "seed": seed, "add_stores": add_stores, "store_keys": store_keys,
            "after_load": extra["after_load"], "on_clear": extra["on_clear"],
            "suppliers": sup_db, "gl_accounts": gl_db, "cost_centers": cc_db,
            "save_po": _po_save, "po_exists": po_exists, "all_pos": _all_pos,
            "update_po_header": _po_update_header, "next_po_number": next_po_number,
            "add_tables": add_tables, "lookups": extra["lookups"], "summary": extra["summary"],
            "api_error": ApiError, "paginate": _paginate}
