"""
PowerERP (demo ERP) — JSON API and static UI.

UI:  http://localhost:5050/
API: http://localhost:5050/api/<resource>

Data is loaded from data/*.json at startup and kept in memory: restarting the
app, or POST /api/reset, restores the original demo data.
"""
import copy
from datetime import datetime
from pathlib import Path

from flask import Blueprint, jsonify, request, send_from_directory

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


def _num(value, default=0.0):
    try:
        return float(str(value).replace(",", ".").strip())
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
    gl = ns["gl_ttGL_data"]
    cc = ns["gl_ttCC_data"]
    suppliers = ns["supplier_terms_data"]
    po_details = ns["po_details"]
    unbilled_po = ns["unbilled_po"]
    receiving_details = ns["receiving_details"]
    unbilled_receiving = ns["unbilled_receiving"]
    invoices = ns.setdefault("erp_invoices", [])

    state = {"next_invoice_id": 1}

    def _add_invoice(inv):
        inv["id"] = state["next_invoice_id"]
        state["next_invoice_id"] += 1
        _compute_invoice(inv)
        invoices.append(inv)
        return inv

    bp = Blueprint("erp", __name__)

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
        code_u = _s(code).upper()
        s = next((x for x in suppliers if x["cCode"].upper() == code_u), None)
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
        po_keys = {p["cPO"] for p in po_details} | {p["cPO"] for p in unbilled_po}
        rec_keys = {r["NoReception"] for r in receiving_details} | {r["NoReception"] for r in unbilled_receiving}
        open_inv = [i for i in invoices if i.get("cStatut") in ("Draft", "Approved")]
        return jsonify({
            "glAccounts": len(gl),
            "costCenters": len(cc),
            "suppliers": len(suppliers),
            "activeSuppliers": len([s for s in suppliers if s.get("iStatutAch") == 1]),
            "purchaseOrders": len(po_keys),
            "unbilledPOs": len(unbilled_po),
            "receptions": len(rec_keys),
            "unbilledReceptions": len(unbilled_receiving),
            "invoices": len(invoices),
            "openInvoices": len(open_inv),
            "openInvoicesAmount": round(sum(_num(i.get("dTotalFacture")) for i in open_inv), 2),
            "recentInvoices": sorted(invoices, key=lambda i: i["id"], reverse=True)[:5],
        })

    @bp.route("/api/lookups/<kind>")
    def erp_lookup(kind):
        q = (request.args.get("q") or "").strip().lower()
        limit = 20
        if kind == "suppliers":
            rows = [{"code": s["cCode"], "label": s["cName"]} for s in suppliers]
        elif kind == "gl":
            rows = [{"code": g["cCode"], "label": g["cDesc"]} for g in gl]
        elif kind == "cc":
            rows = [{"code": f'{c["cCC1"]}-{c["cCC2"]}' if c["cCC2"] else c["cCC1"], "label": c["cDesc"]} for c in cc]
        elif kind == "po":
            rows = [{"code": p["cPO"], "label": p["cSupplierName"]} for p in _all_pos()]
        elif kind == "terms":
            seen = {}
            for s in suppliers:
                if s["cTermCode"] and s["cTermCode"] not in seen:
                    seen[s["cTermCode"]] = s["cTermDesc"]
            rows = [{"code": k, "label": v} for k, v in sorted(seen.items())]
            limit = 200
        elif kind == "buyers":
            seen = {}
            for s in suppliers:
                if s["cCodeAch"] and s["cCodeAch"] not in seen:
                    seen[s["cCodeAch"]] = s["cDescAch"]
            rows = [{"code": k, "label": v} for k, v in sorted(seen.items())]
            limit = 200
        else:
            raise ApiError("not_found", status=404)
        if q:
            rows = [r for r in rows if q in r["code"].lower() or q in (r["label"] or "").lower()]
        return jsonify(rows[:limit])

    @bp.route("/api/reset", methods=["POST"])
    def erp_reset():
        data = copy.deepcopy(snapshot)
        for target, key in ((gl, "gl"), (cc, "cc"), (suppliers, "suppliers"), (po_details, "po_details"),
                            (unbilled_po, "unbilled_po"), (receiving_details, "receiving_details"),
                            (unbilled_receiving, "unbilled_receiving"), (invoices, "invoices")):
            target[:] = data[key]
        state["next_invoice_id"] = data["next_invoice_id"]
        return jsonify({"ok": True})

    @bp.route("/api/clear", methods=["POST"])
    def erp_clear():
        """Empty every table (for demos that start from a blank ERP). /api/reset brings the demo data back."""
        for target in (gl, cc, suppliers, po_details, unbilled_po, receiving_details, unbilled_receiving, invoices):
            target[:] = []
        state["next_invoice_id"] = 1
        return jsonify({"ok": True})

    # ---------------- GL accounts ----------------

    @bp.route("/api/gl-accounts", methods=["GET", "POST"])
    def gl_collection():
        if request.method == "GET":
            return jsonify(_paginate(gl, ("cCode", "cDesc")))
        p = _payload()
        _require(p, "cCode", "cDesc")
        code = _s(p["cCode"])
        if any(g["cCode"].upper() == code.upper() for g in gl):
            raise ApiError("duplicate", "cCode", 409)
        row = {"cCode": code, "cDesc": _s(p["cDesc"])}
        gl.append(row)
        gl.sort(key=lambda g: g["cCode"])
        return jsonify(row), 201

    @bp.route("/api/gl-accounts/<code>", methods=["GET", "PUT", "DELETE"])
    def gl_item(code):
        row = next((g for g in gl if g["cCode"] == code), None)
        if row is None:
            raise ApiError("not_found", status=404)
        if request.method == "GET":
            return jsonify(row)
        if request.method == "DELETE":
            gl.remove(row)
            return jsonify({"ok": True})
        p = _payload()
        _require(p, "cDesc")
        row["cDesc"] = _s(p["cDesc"])
        return jsonify(row)

    # ---------------- Cost centers (key: cCC1 + cCC2) ----------------

    def _cc_find(cc1, cc2):
        return next((c for c in cc if c["cCC1"] == cc1 and (c.get("cCC2") or "") == cc2), None)

    @bp.route("/api/cost-centers", methods=["GET", "POST"])
    def cc_collection():
        if request.method == "GET":
            return jsonify(_paginate(cc, ("cCC1", "cCC2", "cDesc")))
        p = _payload()
        _require(p, "cCC1", "cDesc")
        cc1, cc2 = _s(p["cCC1"]), _s(p.get("cCC2"))
        if _cc_find(cc1, cc2):
            raise ApiError("duplicate", "cCC2" if cc2 else "cCC1", 409)
        row = {"cCC1": cc1, "cCC2": cc2, "cDesc": _s(p["cDesc"])}
        cc.append(row)
        cc.sort(key=lambda c: (c["cCC1"], c.get("cCC2") or ""))
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
            cc.remove(row)
            return jsonify({"ok": True})
        p = _payload()
        _require(p, "cDesc")
        row["cDesc"] = _s(p["cDesc"])
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
            return jsonify(_paginate(suppliers, ("cCode", "cName", "cCity", "cTermCode", "cDescAch")))
        p = _payload()
        _require(p, "cCode", "cName")
        code = _s(p["cCode"])
        if any(s["cCode"].upper() == code.upper() for s in suppliers):
            raise ApiError("duplicate", "cCode", 409)
        row = {"cCode": code, **{f: "" for f in _SUPPLIER_STR}, "iTypePO": 1, "iStatutAch": 1}
        _supplier_apply(row, p)
        suppliers.append(row)
        return jsonify(row), 201

    @bp.route("/api/suppliers/<code>", methods=["GET", "PUT", "DELETE"])
    def supplier_item(code):
        row = next((s for s in suppliers if s["cCode"] == code), None)
        if row is None:
            raise ApiError("not_found", status=404)
        if request.method == "GET":
            return jsonify(row)
        if request.method == "DELETE":
            suppliers.remove(row)
            return jsonify({"ok": True})
        p = _payload()
        _require(p, "cName")
        _supplier_apply(row, p)
        return jsonify(row)

    # ---------------- Purchase orders (getPODetails.p + getUnbilledPO.p) ----------------

    _PO_HEADER_STR = ("cSupplierCode", "cSupplierName", "cBuyerCode", "cBuyerName", "cApplicantCode", "dOrderDate")

    def _po_view(cpo):
        det = next((p for p in po_details if p["cPO"] == cpo), None)
        unb = next((p for p in unbilled_po if p["cPO"] == cpo), None)
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
        keys, seen = [], set()
        for p in list(po_details) + list(unbilled_po):
            if p["cPO"] not in seen:
                seen.add(p["cPO"])
                keys.append(p["cPO"])
        return [_po_view(k) for k in keys]

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
                "dUnitCost": _s(ln.get("dUnitCost")) or "0", "dTotalAmount": _money(total),
            })
        sub = sum(_num(l["dTotalAmount"]) for l in lines)
        freight, gst, pst = _num(p.get("dFreight")), _num(p.get("dGST")), _num(p.get("dPST"))
        header = {f: _s(p.get(f)) for f in _PO_HEADER_STR}
        header["dOrderDate"] = header["dOrderDate"] or _s(p.get("dCreationDate"))
        header.update({"dSubTotal": _money(sub), "dFreight": _money(freight), "dGST": _money(gst),
                       "dPST": _money(pst), "dTotalAmount": _money(sub + freight + gst + pst)})

        det = next((x for x in po_details if x["cPO"] == cpo), None)
        if det is None:
            det = {"COMPANY": company, "cPO": cpo, "ttPOheader": {}, "ttPOdetail": []}
            po_details.append(det)
        det["COMPANY"] = company
        det["ttPOheader"].update(header)
        det["ttPOdetail"] = lines

        unb = next((x for x in unbilled_po if x["cPO"] == cpo), None)
        if _bool(p.get("lUnbilled", True)):
            if unb is None:
                unb = {"COMPANY": company, "cPO": cpo}
                unbilled_po.append(unb)
            unb.update({
                "COMPANY": company, "dCreationDate": _s(p.get("dCreationDate")) or datetime.now().strftime("%Y-%m-%d"),
                "cSupplierName": header["cSupplierName"], "cSupplierCode": header["cSupplierCode"],
                "lBlanketOrder": _bool(p.get("lBlanketOrder")),
            })
        elif unb is not None:
            unbilled_po.remove(unb)
        return _po_view(cpo)

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
            po_details[:] = [x for x in po_details if x["cPO"] != cpo]
            unbilled_po[:] = [x for x in unbilled_po if x["cPO"] != cpo]
            return jsonify({"ok": True})
        p = _payload()
        _require(p, "cSupplierCode")
        return jsonify(_po_save(cpo, p, view))

    # ---------------- Receptions (getReceivingDetails.p + getUnbilledReceiving.p) ----------------

    _REC_STR = ("DateReception", "NoBonCommande", "CodeFournisseur", "Fournisseur", "Statut", "Entrepot",
                "ResponsableReception", "Commentaires")

    def _rec_view(no):
        det = next((r for r in receiving_details if r["NoReception"] == no), None)
        unb = next((r for r in unbilled_receiving if r["NoReception"] == no), None)
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
        keys, seen = [], set()
        for r in list(receiving_details) + list(unbilled_receiving):
            if r["NoReception"] not in seen:
                seen.add(r["NoReception"])
                keys.append(r["NoReception"])
        return [_rec_view(k) for k in keys]

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
                "PrixUnitaire": _s(ln.get("PrixUnitaire")) or "0", "Devise": devise,
                "dTotalAmount": _money(amount),
                "cGL": _s(ln.get("cGL")), "cCC1": _s(ln.get("cCC1")), "cCC2": _s(ln.get("cCC2")),
            })
        sub = sum(_num(a["dTotalAmount"]) for a in articles)
        freight, tps, tvq = _num(p.get("Transport")), _num(p.get("TPS")), _num(p.get("TVQ"))
        total = sub + freight + tps + tvq

        det = next((x for x in receiving_details if x["NoReception"] == no), None)
        if det is None:
            det = {"NoReception": no}
            receiving_details.append(det)
        det.update({f: _s(p.get(f)) for f in _REC_STR})
        det.update({"COMPANY": company, "Articles": articles, "SousTotal": _money(sub),
                    "Transport": _money(freight), "TPS": _money(tps), "TVQ": _money(tvq),
                    "MontantTotal": _money(total)})

        unb = next((x for x in unbilled_receiving if x["NoReception"] == no), None)
        if _bool(p.get("lUnbilled", True)):
            if unb is None:
                unb = {"NoReception": no, "StatutFacturation": "En attente de facture", "JoursEnAttente": "0",
                       "ResponsableFacturation": "Comptabilité", "PrioriteFacturation": "Normale",
                       "TypeReception": "Standard"}
                unbilled_receiving.append(unb)
            unb.update({"COMPANY": company, "DateReception": det["DateReception"],
                        "NoBonCommande": det["NoBonCommande"], "Fournisseur": det["Fournisseur"],
                        "CodeFournisseur": det["CodeFournisseur"], "MontantRecu": _money(total),
                        "Devise": devise, "Entrepot": det["Entrepot"]})
        elif unb is not None:
            unbilled_receiving.remove(unb)
        return _rec_view(no)

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
            receiving_details[:] = [x for x in receiving_details if x["NoReception"] != no]
            unbilled_receiving[:] = [x for x in unbilled_receiving if x["NoReception"] != no]
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

    def _inv_duplicate(supplier, number, exclude_id=None):
        return any(i["cNoFourn"].upper() == supplier.upper() and i["cNoFacture"].upper() == number.upper()
                   and i["id"] != exclude_id for i in invoices)

    @bp.route("/api/invoices", methods=["GET", "POST"])
    def inv_collection():
        if request.method == "GET":
            rows = [{k: v for k, v in i.items() if k != "lines"} for i in invoices]
            return jsonify(_paginate(rows, ("cNoFacture", "cNoFourn", "cNomFourn", "cNoCommAch")))
        p = _payload()
        _require(p, "cNoFourn", "cNoFacture", "dDateFacture")
        if _inv_duplicate(_s(p["cNoFourn"]), _s(p["cNoFacture"])):
            raise ApiError("duplicate", "cNoFacture", 409)
        inv = _inv_from_payload(p, {"cSource": "ERP"})
        inv["id"] = state["next_invoice_id"]
        state["next_invoice_id"] += 1
        invoices.append(inv)
        return jsonify(inv), 201

    @bp.route("/api/invoices/<int:inv_id>", methods=["GET", "PUT", "DELETE"])
    def inv_item(inv_id):
        inv = next((i for i in invoices if i["id"] == inv_id), None)
        if inv is None:
            raise ApiError("not_found", status=404)
        if request.method == "GET":
            return jsonify(inv)
        if request.method == "DELETE":
            invoices.remove(inv)
            return jsonify({"ok": True})
        p = _payload()
        _require(p, "cNoFourn", "cNoFacture", "dDateFacture")
        if _inv_duplicate(_s(p["cNoFourn"]), _s(p["cNoFacture"]), inv_id):
            raise ApiError("duplicate", "cNoFacture", 409)
        return jsonify(_inv_from_payload(p, inv))

    # The demo dataset starts without invoices (app.py passes seed_invoices=[]).
    for seed in ns.get("seed_invoices", _SEED_INVOICES):
        _add_invoice(copy.deepcopy(seed))

    snapshot = copy.deepcopy({
        "gl": gl, "cc": cc, "suppliers": suppliers, "po_details": po_details,
        "unbilled_po": unbilled_po, "receiving_details": receiving_details,
        "unbilled_receiving": unbilled_receiving, "invoices": invoices,
        "next_invoice_id": state["next_invoice_id"],
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
        billed = set()
        for d in lines:
            rec_no = d.get("iNoReception", "")
            rec_no = "" if rec_no in ("", "0") else rec_no
            code = d.get("cCodeProduit", "")
            desc = ""
            if rec_no:
                billed.add(rec_no)
                rec = next((r for r in receiving_details if r["NoReception"] == rec_no), None)
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
        # Invoiced receptions are no longer "unbilled" (getUnbilledReceiving.p)
        if billed:
            unbilled_receiving[:] = [r for r in unbilled_receiving if r["NoReception"] not in billed]
        return inv

    return {"invoice_exists": invoice_exists, "record_invoice": record_invoice}
