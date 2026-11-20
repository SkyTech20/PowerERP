"""
PowerERP — products, taxes and inventory management.

Master files (list / create / edit / delete, like the other ERP screens):
  /api/tax-codes          one tax each (TPS, TVQ, TVH...), with its rate history, registration number and GL accounts
  /api/tax-groups         what a product, supplier or document uses (QC = TPS + TVQ, EXO, ZERO, ON...)
  /api/uom                units of measure
  /api/categories         product categories (with a parent, for families / sub-families)
  /api/products           the item master (FR / EN descriptions, units, costs, prices, taxes, GL, suppliers, logistics)
  /api/warehouses         warehouses (entrepôts)
  /api/locations          locations inside a warehouse (zone > aisle > rack > level > bin), key <warehouse>/<code>
  /api/stock-params       replenishment per product x warehouse (reorder point, min / max, order quantity), key <product>/<warehouse>

Inventory management:
  /api/stock-movements    receipts, issues, transfers, adjustments, counts, reservations; never changed once posted:
                          a wrong movement is corrected with another one. Stock balances are calculated from them.
  /api/inventory/stock          balances per product + warehouse + location + lot / serial
  /api/inventory/valuation      quantity x moving average cost (or standard cost), per product and warehouse
  /api/inventory/replenishment  products at or below their reorder point, with the suggested quantity and supplier;
                                POST .../replenishment/po creates one purchase order per supplier
  /api/stock-counts             physical / cycle counts: generate the sheet from the balances, enter the counted
                                quantities, post (creates the adjustment movements)
  /api/tax-groups/<code>/calc   taxes of an amount for a tax group at a date (for any other screen or service)

WMS later: locations already have a type, capacity (weight / volume / pallets), mixing rules, a blocked flag and a
picking sequence, and every balance and movement is by location; a WMS only adds tasks (put-away, picking) on top.

Every table is relational (powererp.store): taxes, units, categories, products, warehouses, locations, stock
parameters, movements (the ledger, insert only) and counts. The balances are a table too (powererp.stock), updated
in the same transaction as each movement, with a lock per product so two simultaneous movements cannot both use
the same stock.
"""
import copy
import json
import math
from datetime import date, datetime
from pathlib import Path

from flask import Blueprint, g, jsonify, request
from sqlalchemy import func

from auth import current_user
from erp_api import ApiError, _bool, _dec, _num, _s

from powererp.schemas import *  # noqa: F401,F403  (choices, schemas and DEFAULTS)
from powererp.schemas import DEFAULTS, PRODUCT, PRODUCT_SUPPLIER  # noqa: F401
from powererp import purchasing as purch
from powererp import stock as stockdb
from powererp.store import store

SEED_FILE = Path(__file__).resolve().parent / "data" / "inventory.json"

# Master files in relational tables: API name -> table
MASTER = {"tax_codes": "tax_codes", "tax_groups": "tax_groups", "uom": "uoms", "categories": "product_categories",
          "warehouses": "warehouses", "locations": "locations", "products": "products",
          "stock_params": "stock_params"}


def _clean(kind, value):
    if isinstance(kind, tuple):
        v = _s(value)
        if v not in kind:
            raise ValueError
        return v
    if kind == "b":
        return _bool(value)
    if kind == "i":
        return int(_num(value)) if _s(value) else 0
    if kind == "d":
        v = _s(value)
        if v == "":
            return ""
        out = _dec(v, None)
        if out is None:
            raise ValueError
        float(out)
        return out
    if kind == "date":
        v = _s(value)[:10]
        if v:
            datetime.strptime(v, "%Y-%m-%d")
        return v
    return _s(value)


def _apply(row, p, schema, skip=()):
    """Copy the schema fields present in the payload, cleaned. A bad value raises ApiError on its field."""
    for f, kind in schema.items():
        if f in p and f not in skip:
            try:
                row[f] = _clean(kind, p[f])
            except (ValueError, TypeError):
                raise ApiError("invalid_choice" if isinstance(kind, tuple) else "numeric" if kind in ("d", "i")
                               else "invalid_date", f)
    return row


def _blank(schema, defaults=None):
    row = {f: (False if k == "b" else 0 if k == "i" else (k[0] if isinstance(k, tuple) else "")) for f, k in schema.items()}
    row.update(copy.deepcopy(defaults or {}))
    return row


def _lines(p, schema, keep):
    """Clean the "lines" of a payload; keep(line) says whether an (almost) empty line is kept."""
    out = []
    for i, ln in enumerate(p.get("lines") or [], 1):
        if not isinstance(ln, dict):
            continue
        row = _apply(_blank(schema), ln, schema)
        if keep(row):
            out.append(row)
    return out


def _f(v):
    return _num(v)


def _q(v):
    """A quantity as text: "12", "12.5", "0.125"."""
    v = round(float(v), 4)
    return str(int(v)) if v == int(v) else f"{v:.4f}".rstrip("0").rstrip(".")


def _m(v):
    return f"{round(float(v) + 1e-9, 2):.2f}"


def _c(v):
    """A unit cost (4 decimals, trailing zeros removed down to 2)."""
    s = f"{float(v):.4f}"
    return s[:-2] if s.endswith("00") else s.rstrip("0")


def _today():
    return date.today().isoformat()


# --------------------------------------------------------------------------- module

def register_inventory(app, ns, hooks):
    DB = {name: store(table) for name, table in MASTER.items()}
    MOV, CNT = store("stock_movements"), store("stock_counts")
    # The opening movements of the seed, posted in memory at start-up (see "seed" at the end)
    T = {"movements": []}
    # While the seed is prepared (start-up, no database session), the master files are these lists.
    seeding = {"rows": None}

    def M(name):
        """Every row of a master file."""
        if seeding["rows"] is not None:
            return seeding["rows"][name]
        return DB[name].all()

    def save_master(name, row):
        """Write back a master row changed outside its screen (e.g. the average cost of a product)."""
        if seeding["rows"] is None:
            DB[name].update(row)
    suppliers = ns["supplier_terms_data"]
    paginate = hooks["paginate"]

    bp = Blueprint("inventory", __name__)

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

    def _find(name, code, field="cCode"):
        cu = _s(code).upper()
        if not cu:
            return None
        if name in MASTER and seeding["rows"] is None and field == "cCode" and DB[name].spec.keys == ("cCode",):
            return DB[name].get(cu)
        rows = M(name) if name in MASTER else T[name]
        return next((r for r in rows if _s(r.get(field)).upper() == cu), None)

    def _must(name, p, field, target=None, required=False):
        """A reference to another master file must exist (empty is fine unless required)."""
        v = _s(p.get(field))
        if not v:
            if required:
                raise ApiError("required", field)
            return None
        row = _find(target or name, v)
        if row is None:
            raise ApiError("unknown_ref", field)
        return row

    def _require(p, *fields):
        for f in fields:
            if not _s(p.get(f)):
                raise ApiError("required", f)

    # ------------------------------------------------------------------ generic master CRUD

    def crud(name, url, schema, search, validate=None, view=None, on_delete=None, keys=("cCode",),
             line_schema=None, keep_line=None, sort=None, readonly=()):
        """List / create / read / update / delete routes of a master file (relational table, or in-memory list)."""
        view = view or (lambda r: r)
        db = DB.get(name)

        def all_rows(lines=True):
            return db.all(lines=lines) if db else T[name]

        def find(parts):
            if db:
                return db.get(*parts)
            return next((r for r in T[name] if all(_s(r.get(k)).upper() == _s(v).upper() for k, v in zip(keys, parts))), None)

        def add(row):
            if db:
                db.insert(row)
                return
            T[name].append(row)
            if sort:
                T[name].sort(key=sort)

        def remove(row):
            if db:
                db.delete(row)
            else:
                T[name].remove(row)

        def replace(row, work):
            if db:
                db.update(work, [row[k] for k in keys])
            else:
                row.clear()
                row.update(work)
            return work

        def save(row, p, is_new):
            _apply(row, p, schema, skip=(keys if not is_new else ()) + tuple(readonly))
            if line_schema is not None and "lines" in p:
                row["lines"] = _lines(p, line_schema, keep_line or (lambda r: True))
            if validate:
                validate(row, is_new)
            return row

        def collection():
            if request.method == "GET":
                return jsonify(paginate([{k: v for k, v in view(r).items() if k != "lines"}
                                         for r in all_rows()], search))
            p = _payload()
            row = _blank(schema, DEFAULTS.get(name))
            if line_schema is not None:
                row["lines"] = []
            save(row, p, True)
            for k in keys:
                if not _s(row.get(k)):
                    raise ApiError("required", k)
            if find([row[k] for k in keys]):
                raise ApiError("duplicate", keys[-1], 409)
            add(row)
            return jsonify(view(row)), 201

        def item(key):
            parts = key.split("/")
            if len(parts) != len(keys):
                raise ApiError("not_found", status=404)
            row = find(parts)
            if row is None:
                raise ApiError("not_found", status=404)
            if request.method == "GET":
                return jsonify(view(row))
            if request.method == "DELETE":
                if on_delete:
                    on_delete(row)
                remove(row)
                return jsonify({"ok": True})
            p = _payload()
            work = copy.deepcopy(row)
            save(work, p, False)
            return jsonify(view(replace(row, work)))

        bp.add_url_rule(f"/api/{url}", f"{name}_collection", collection, methods=["GET", "POST"])
        bp.add_url_rule(f"/api/{url}/<path:key>", f"{name}_item", item, methods=["GET", "PUT", "DELETE"])
        return find

    def in_use(cond):
        if cond:
            raise ApiError("in_use", status=409)

    # ------------------------------------------------------------------ taxes

    def rate_on(tax, on=None):
        """The tax rate (percent) valid at a date, from the rate history (latest start date that applies)."""
        on = on or _today()
        valid = [r for r in tax.get("lines", []) if (r.get("dStartDate") or "0000") <= on
                 and (not r.get("dEndDate") or r["dEndDate"] >= on)]
        if not valid:
            return None
        return _f(max(valid, key=lambda r: r.get("dStartDate") or "")["dRate"])

    def tax_code_view(r):
        rate = rate_on(r)
        return {**r, "dCurrentRate": "" if rate is None else _q(rate)}

    def tax_code_validate(row, is_new):
        _require(row, "cDescFR")
        for i, ln in enumerate(row.get("lines", [])):
            if ln["dRate"] == "":
                raise ApiError("required", "lines", detail=f"line {i + 1}: rate")
            if ln["dEndDate"] and ln["dStartDate"] and ln["dEndDate"] < ln["dStartDate"]:
                raise ApiError("invalid_dates", "lines", detail=f"line {i + 1}")
        row.setdefault("lines", []).sort(key=lambda r: r.get("dStartDate") or "")

    crud("tax_codes", "tax-codes", TAX_CODE, ("cCode", "cDescFR", "cDescEN", "cJurisdiction"),
         validate=tax_code_validate, view=tax_code_view, line_schema=TAX_RATE,
         keep_line=lambda r: r["dRate"] != "" or r["dStartDate"],
         on_delete=lambda r: in_use(any(_s(l["cTaxCode"]).upper() == r["cCode"].upper()
                                        for g in M("tax_groups") for l in g.get("lines", []))),
         sort=lambda r: r["cCode"])

    def tax_group_view(r):
        lines = sorted(r.get("lines", []), key=lambda l: l["iSeq"])
        names = [l["cTaxCode"] for l in lines]
        return {**r, "cTaxList": " + ".join(names) if names and r.get("cTreatment") == "taxable"
                else ""}

    def tax_group_validate(row, is_new):
        _require(row, "cDescFR")
        for i, ln in enumerate(row.get("lines", []), 1):
            if not _find("tax_codes", ln["cTaxCode"]):
                raise ApiError("unknown_ref", "lines", detail=f"line {i}: {ln['cTaxCode']}")
            ln["cTaxCode"] = _find("tax_codes", ln["cTaxCode"])["cCode"]
            ln["iSeq"] = ln["iSeq"] or i
        row["lines"] = sorted(row.get("lines", []), key=lambda l: l["iSeq"])

    def group_used(code):
        cu = code.upper()
        return DB["products"].exists(lambda c: [(func.upper(c["cSalesTaxGroup"]) == cu)
                                                | (func.upper(c["cPurchaseTaxGroup"]) == cu)])

    crud("tax_groups", "tax-groups", TAX_GROUP, ("cCode", "cDescFR", "cDescEN", "cProvince"),
         validate=tax_group_validate, view=tax_group_view, line_schema=TAX_GROUP_LINE,
         keep_line=lambda r: bool(r["cTaxCode"]), on_delete=lambda r: in_use(group_used(r["cCode"])),
         sort=lambda r: r["cCode"])

    def tax_calc(group_code, amount, on=None):
        """Taxes of `amount` for a tax group at a date. Compound taxes are calculated on the amount + the taxes before them."""
        group = _find("tax_groups", group_code)
        if group is None:
            return None
        on = on or _today()
        out, total = [], 0.0
        if group.get("cTreatment") == "taxable":
            for ln in sorted(group.get("lines", []), key=lambda l: l["iSeq"]):
                tax = _find("tax_codes", ln["cTaxCode"])
                rate = rate_on(tax, on) if tax else None
                if rate is None:
                    continue
                base = amount + (total if ln.get("lCompound") else 0.0)
                value = round(base * rate / 100 + 1e-9, 2)
                total += value
                out.append({"cTaxCode": tax["cCode"], "cKind": tax.get("cKind", ""), "dRate": _q(rate),
                            "dBase": _m(base), "dTax": _m(value), "cGLCollected": tax.get("cGLCollected", ""),
                            "cGLRecoverable": tax.get("cGLRecoverable", ""),
                            "dRecoverable": _m(value * _f(tax.get("dRecoverablePct") or 100) / 100)})
        return {"cTaxGroup": group["cCode"], "cTreatment": group.get("cTreatment"), "dDate": on,
                "dAmount": _m(amount), "taxes": out, "dTotalTax": _m(total), "dTotal": _m(amount + total)}

    @bp.route("/api/tax-groups/<code>/calc")
    def tax_group_calc(code):
        res = tax_calc(code, _num(request.args.get("amount")), _s(request.args.get("date"))[:10] or None)
        if res is None:
            raise ApiError("not_found", status=404)
        return jsonify(res)

    # ------------------------------------------------------------------ units and categories

    def uom_used(code):
        cu = code.upper()
        return DB["products"].exists(lambda c: [(func.upper(c["cStockUOM"]) == cu) | (func.upper(c["cPurchaseUOM"]) == cu)
                                                | (func.upper(c["cSalesUOM"]) == cu)])

    def simple_validate(row, is_new):
        _require(row, "cDescFR")

    crud("uom", "uom", UOM, ("cCode", "cDescFR", "cDescEN"), validate=simple_validate,
         on_delete=lambda r: in_use(uom_used(r["cCode"])), sort=lambda r: r["cCode"])

    def category_validate(row, is_new):
        _require(row, "cDescFR")
        if row["cParent"]:
            if row["cParent"].upper() == row["cCode"].upper():
                raise ApiError("invalid_ref", "cParent")
            _must("categories", row, "cParent")

    crud("categories", "categories", CATEGORY, ("cCode", "cDescFR", "cDescEN", "cParent"),
         validate=category_validate,
         on_delete=lambda r: in_use(
             DB["products"].exists(lambda c: [func.upper(c["cCategory"]) == r["cCode"].upper()])
             or DB["categories"].exists(lambda c: [func.upper(c["cParent"]) == r["cCode"].upper()])),
         sort=lambda r: r["cCode"])

    # ------------------------------------------------------------------ balances (calculated from the movements)

    def _effects(m):
        """(warehouse, location, on-hand change, reserved change) of a movement."""
        q = _f(m["dQty"])
        wh, loc = m["cWarehouse"], m.get("cLocation", "")
        t = m["cType"]
        if t == "IN":
            return [(wh, loc, q, 0.0)]
        if t == "OUT":
            return [(wh, loc, -q, 0.0)]
        if t == "TRF":
            return [(wh, loc, -q, 0.0), (m["cWhTo"], m.get("cLocTo", ""), q, 0.0)]
        if t in ("ADJ", "CNT"):
            return [(wh, loc, q, 0.0)]
        if t == "RSV":
            return [(wh, loc, 0.0, q)]
        return []

    def balances(extra=()):
        """{(product, warehouse, location, lot, serial): {"qty", "reserved", "expiry"}}: the balances table plus the
        effects of the `extra` movements (staged, not posted yet). Without `extra`, cached for the request (lists
        call it once per row) until the next movement."""
        if seeding["rows"] is not None:
            return replay(T["movements"], extra)
        try:
            cached = g.get("inv_bal")
        except RuntimeError:
            cached = None
        if cached is None:
            cached = stockdb.read()
            try:
                g.inv_bal = cached
            except RuntimeError:
                pass
        if not extra:
            return cached
        return replay(extra, (), copy.deepcopy(cached))

    def forget_balances():
        try:
            g.pop("inv_bal", None)
        except RuntimeError:
            pass

    def replay(movements, extra=(), out=None):
        """Balances obtained by adding the effects of movements to `out`."""
        out = {} if out is None else out
        for m in list(movements) + list(extra):
            for wh, loc, dq, dr in _effects(m):
                key = (m["cProduct"].upper(), wh.upper(), loc.upper(), m.get("cLot", "").upper(), m.get("cSerial", "").upper())
                b = out.setdefault(key, {"cProduct": m["cProduct"], "cWarehouse": wh, "cLocation": loc,
                                         "cLot": m.get("cLot", ""), "cSerial": m.get("cSerial", ""), "qty": 0.0,
                                         "reserved": 0.0, "dExpiry": ""})
                b["qty"] = round(b["qty"] + dq, 6)
                b["reserved"] = round(b["reserved"] + dr, 6)
                if m.get("dExpiry") and dq > 0:
                    b["dExpiry"] = m["dExpiry"]
        return out

    def product_totals(code, wh=None, bal=None):
        bal = balances() if bal is None else bal
        qty = res = 0.0
        for (p, w, *_rest), b in bal.items():
            if p == code.upper() and (wh is None or w == wh.upper()):
                qty += b["qty"]
                res += b["reserved"]
        return qty, res

    def on_order(code):
        """Quantity ordered on open POs (not invoiced yet) and not received yet."""
        open_pos = {p["cPO"] for p in purch.unbilled_po_list()}
        receiving_details = purch.receiving_details_list()
        ordered = received = 0.0
        for po in purch.po_details_list():
            if po["cPO"] not in open_pos:
                continue
            ordered += sum(_f(l.get("dQuantity")) for l in po.get("ttPOdetail", [])
                           if _s(l.get("cProductcode")).upper() == code.upper())
            received += sum(_f(a.get("QuantiteRecue")) for r in receiving_details
                            if _s(r.get("NoBonCommande")) == po["cPO"] for a in r.get("Articles", [])
                            if _s(a.get("CodeArticle")).upper() == code.upper())
        return max(0.0, ordered - received)

    def unit_cost(prod):
        if prod.get("cCostMethod") == "std" and _s(prod.get("dStdCost")):
            return _f(prod["dStdCost"])
        return _f(prod.get("dAvgCost"))

    # ------------------------------------------------------------------ products

    def product_view(r, full=True):
        out = dict(r)
        if not full:
            qty, res = product_totals(r["cCode"])
            out.update({"dQtyOnHand": _q(qty), "dQtyAvailable": _q(qty - res)})
            return out
        bal = balances()
        rows = {}
        for (p, w, *_rest), b in bal.items():
            if p != r["cCode"].upper():
                continue
            s = rows.setdefault(w, {"cWarehouse": b["cWarehouse"], "qty": 0.0, "reserved": 0.0})
            s["qty"] += b["qty"]
            s["reserved"] += b["reserved"]
        cost = unit_cost(r)
        stock = []
        for s in rows.values():
            wh = _find("warehouses", s["cWarehouse"])
            par = DB["stock_params"].get(r["cCode"], s["cWarehouse"])
            stock.append({"cWarehouse": s["cWarehouse"], "cWarehouseName": (wh or {}).get("cNameFR", ""),
                          "dQtyOnHand": _q(s["qty"]), "dQtyReserved": _q(s["reserved"]),
                          "dQtyAvailable": _q(s["qty"] - s["reserved"]), "dValue": _m(s["qty"] * cost),
                          "dReorderPoint": (par or {}).get("dReorderPoint", "")})
        qty = sum(s["qty"] for s in rows.values())
        res = sum(s["reserved"] for s in rows.values())
        price = _f(r.get("dPrice1"))
        out.update({"stock": sorted(stock, key=lambda s: s["cWarehouse"]), "dQtyOnHand": _q(qty),
                    "dQtyReserved": _q(res), "dQtyAvailable": _q(qty - res), "dQtyOnOrder": _q(on_order(r["cCode"])),
                    "dStockValue": _m(qty * cost),
                    "dMarginPct": f"{(price - cost) / price * 100:.1f}" if price and cost else ""})
        return out

    def product_validate(row, is_new):
        _require(row, "cDescFR")
        _must("categories", row, "cCategory")
        for f in ("cStockUOM", "cPurchaseUOM", "cSalesUOM"):
            _must("uom", row, f, required=(f == "cStockUOM"))
        for f in ("cSalesTaxGroup", "cPurchaseTaxGroup"):
            _must("tax_groups", row, f)
        _must("warehouses", row, "cDefaultWarehouse")
        for f in ("dPurchaseFactor", "dSalesFactor"):
            if _s(row.get(f)) and _f(row[f]) <= 0:
                raise ApiError("positive", f)
            row[f] = row[f] or "1"
        if row["cType"] not in STOCKED_TYPES:
            row["lStocked"] = False
        if not is_new and not row["lStocked"]:
            in_use(abs(product_totals(row["cCode"])[0]) > 1e-9)  # still has stock
        codes = {s["cCode"].upper(): s["cCode"] for s in suppliers}
        for i, ln in enumerate(row.get("lines", []), 1):
            if ln["cSupplierCode"].upper() not in codes:
                raise ApiError("unknown_ref", "lines", detail=f"line {i}: {ln['cSupplierCode']}")
            ln["cSupplierCode"] = codes[ln["cSupplierCode"].upper()]
            ln["cCurrency"] = ln["cCurrency"] or row.get("cCurrency") or "CAD"
        for f in ("dAvgCost", "dLastCost"):
            row.setdefault(f, "")

    def product_delete(r):
        cu = r["cCode"].upper()
        in_use(MOV.exists(lambda c: [func.upper(c["cProduct"]) == cu]))
        DB["stock_params"].delete_where(lambda c: [func.upper(c["cProduct"]) == cu])

    crud("products", "products", PRODUCT,
         ("cCode", "cDescFR", "cDescEN", "cCategory", "cBrand", "cUPC", "cMfrPartNo", "cManufacturer"),
         validate=product_validate, view=lambda r: product_view(r, full=request.method != "GET" or
                                                                 request.endpoint.endswith("_item")),
         on_delete=product_delete, line_schema=PRODUCT_SUPPLIER, keep_line=lambda r: bool(r["cSupplierCode"]),
         sort=lambda r: r["cCode"], readonly=("dAvgCost", "dLastCost"))

    # ------------------------------------------------------------------ warehouses and locations

    def wh_validate(row, is_new):
        _require(row, "cNameFR")
        for f in ("cReceivingLoc", "cShippingLoc"):
            if row[f] and not find_location(row["cCode"], row[f]):
                raise ApiError("unknown_ref", f)

    def wh_delete(r):
        cu = r["cCode"].upper()
        in_use(MOV.exists(lambda c: [(func.upper(c["cWarehouse"]) == cu) | (func.upper(c["cWhTo"]) == cu)]))
        DB["locations"].delete_where(lambda c: [func.upper(c["cWarehouse"]) == cu])
        DB["stock_params"].delete_where(lambda c: [func.upper(c["cWarehouse"]) == cu])

    crud("warehouses", "warehouses", WAREHOUSE, ("cCode", "cNameFR", "cNameEN", "cCity", "cManager"),
         validate=wh_validate, on_delete=wh_delete, sort=lambda r: r["cCode"])

    def find_location(wh, code):
        if seeding["rows"] is None:
            return DB["locations"].get(_s(wh), _s(code)) if _s(code) else None
        return next((l for l in M("locations") if l["cWarehouse"].upper() == _s(wh).upper()
                     and l["cCode"].upper() == _s(code).upper()), None)

    def has_locations(wh):
        if seeding["rows"] is None:
            return DB["locations"].exists(lambda c: [func.upper(c["cWarehouse"]) == wh.upper()])
        return any(l["cWarehouse"].upper() == wh.upper() for l in M("locations"))

    def loc_validate(row, is_new):
        if is_new:
            wh = _must("warehouses", row, "cWarehouse", required=True)
            row["cWarehouse"] = wh["cCode"]
            if not row["cCode"]:
                row["cCode"] = "-".join(x for x in (row["cZone"], row["cAisle"], row["cRack"], row["cLevel"], row["cBin"]) if x)
            if not row["cCode"]:
                raise ApiError("required", "cCode")
            row["cCode"] = row["cCode"].upper()

    def loc_view(r):
        q = sum(b["qty"] for (p, w, l, *_x), b in balances().items()
                if w == r["cWarehouse"].upper() and l == r["cCode"].upper())
        return {**r, "dQtyOnHand": _q(q)} if request.endpoint and request.endpoint.endswith("_item") else r

    def loc_delete(r):
        wh, code = r["cWarehouse"].upper(), r["cCode"].upper()
        in_use(MOV.exists(lambda c: [((func.upper(c["cWarehouse"]) == wh) & (func.upper(c["cLocation"]) == code))
                                     | ((func.upper(c["cWhTo"]) == wh) & (func.upper(c["cLocTo"]) == code))]))

    crud("locations", "locations", LOCATION, ("cWarehouse", "cCode", "cZone", "cDescription", "cType"),
         keys=("cWarehouse", "cCode"), validate=loc_validate, view=loc_view, on_delete=loc_delete,
         sort=lambda r: (r["cWarehouse"], r.get("iPickSeq") or 0, r["cCode"]))

    # ------------------------------------------------------------------ replenishment parameters

    def param_validate(row, is_new):
        if is_new:
            row["cProduct"] = _must("products", row, "cProduct", required=True)["cCode"]
            row["cWarehouse"] = _must("warehouses", row, "cWarehouse", required=True)["cCode"]
        if row["cDefaultLocation"] and not find_location(row["cWarehouse"], row["cDefaultLocation"]):
            raise ApiError("unknown_ref", "cDefaultLocation")
        if _s(row["dMaxQty"]) and _s(row["dMinQty"]) and _f(row["dMaxQty"]) < _f(row["dMinQty"]):
            raise ApiError("max_below_min", "dMaxQty")

    def param_view(r):
        prod = _find("products", r["cProduct"]) or {}
        qty, res = product_totals(r["cProduct"], r["cWarehouse"])
        return {**r, "cDescFR": prod.get("cDescFR", ""), "cDescEN": prod.get("cDescEN", ""),
                "dQtyAvailable": _q(qty - res)}

    crud("stock_params", "stock-params", STOCK_PARAM, ("cProduct", "cWarehouse", "cDescFR", "cDescEN"),
         keys=("cProduct", "cWarehouse"), validate=param_validate, view=param_view,
         sort=lambda r: (r["cProduct"], r["cWarehouse"]))

    # ------------------------------------------------------------------ movements

    def _user():
        try:
            u = current_user()
        except RuntimeError:  # outside a request (seed)
            return "system"
        return u["username"] if u else "api"

    def increases_stock(m):
        return m["cType"] == "IN" or (m["cType"] in ("ADJ", "CNT") and _f(m["dQty"]) > 0)

    def check_movement(m, staged=()):
        """Validate a movement against the master files and the stock (balances + `staged` movements). Fills names."""
        prod = _find("products", m["cProduct"])
        if prod is None:
            raise ApiError("required" if not m["cProduct"] else "unknown_ref", "cProduct")
        m["cProduct"] = prod["cCode"]
        if seeding["rows"] is None:
            # One movement of this product at a time; then read the stock again (another request may have changed it)
            stockdb.lock_product(prod["cCode"])
            forget_balances()
            prod = _find("products", m["cProduct"])
        if not prod.get("lStocked"):
            raise ApiError("not_stocked", "cProduct")
        q = _f(m["dQty"])
        if m["cType"] in ("IN", "OUT", "TRF") and q <= 0:
            raise ApiError("positive", "dQty")
        if abs(q) < 1e-9:
            raise ApiError("required", "dQty")

        def place(wf, lf):
            wh = _find("warehouses", m.get(wf))
            if wh is None:
                raise ApiError("required" if not m.get(wf) else "unknown_ref", wf)
            m[wf] = wh["cCode"]
            has_locs = wh.get("lUseLocations") and has_locations(wh["cCode"])
            if has_locs and not m.get(lf):
                raise ApiError("required", lf)
            if m.get(lf):
                loc = find_location(wh["cCode"], m[lf])
                if loc is None:
                    raise ApiError("unknown_ref", lf)
                m[lf] = loc["cCode"]
                if loc.get("lBlocked") or not loc.get("lActive", True):
                    raise ApiError("blocked_location", lf)
                return wh, loc
            return wh, None

        wh, loc = place("cWarehouse", "cLocation")
        dest = None
        if m["cType"] == "TRF":
            dest = place("cWhTo", "cLocTo")
            if dest[0]["cCode"] == wh["cCode"] and (m.get("cLocTo") or "") == (m.get("cLocation") or ""):
                raise ApiError("same_location", "cLocTo")
        else:
            m["cWhTo"], m["cLocTo"] = "", ""

        if prod.get("lLotControl") and not m.get("cLot"):
            raise ApiError("lot_required", "cLot")
        if prod.get("lSerialControl"):
            if not m.get("cSerial"):
                raise ApiError("serial_required", "cSerial")
            if abs(q) != 1 and m["cType"] != "RSV":
                raise ApiError("serial_qty", "dQty")
        if prod.get("lExpiryControl") and m["cType"] == "IN" and not m.get("dExpiry"):
            raise ApiError("required", "dExpiry")

        bal = balances(staged)
        key = (prod["cCode"].upper(), wh["cCode"].upper(), _s(m.get("cLocation")).upper(),
               _s(m.get("cLot")).upper(), _s(m.get("cSerial")).upper())
        b = bal.get(key, {"qty": 0.0, "reserved": 0.0})
        decrease = -q if m["cType"] in ("ADJ", "CNT") and q < 0 else q if m["cType"] in ("OUT", "TRF") else 0
        if decrease and b["qty"] - b["reserved"] - decrease < -1e-9 and not wh.get("lAllowNegative"):
            raise ApiError("insufficient_stock", "dQty", detail=_q(b["qty"] - b["reserved"]))
        if m["cType"] == "RSV":
            if q > 0 and b["qty"] - b["reserved"] - q < -1e-9:
                raise ApiError("insufficient_stock", "dQty", detail=_q(b["qty"] - b["reserved"]))
            if q < 0 and b["reserved"] + q < -1e-9:
                raise ApiError("insufficient_reserved", "dQty", detail=_q(b["reserved"]))
        if prod.get("lSerialControl") and increases_stock(m) and any(
                k[0] == prod["cCode"].upper() and k[4] == _s(m.get("cSerial")).upper() and v["qty"] > 1e-9
                for k, v in bal.items()):
            raise ApiError("duplicate", "cSerial", 409)  # a serial number is in stock once only

        # Mixing rules of the location that receives the stock
        incoming = dest if m["cType"] == "TRF" else (wh, loc) if (m["cType"] == "IN" or (m["cType"] in ("ADJ", "CNT") and q > 0)) else None
        if incoming and incoming[1] is not None:
            iw, il = incoming
            others = [k for k, v in bal.items() if k[1] == iw["cCode"].upper() and k[2] == il["cCode"].upper() and v["qty"] > 1e-9]
            if not il.get("lMixProducts", True) and any(k[0] != prod["cCode"].upper() for k in others):
                raise ApiError("location_mixed", "cLocTo" if m["cType"] == "TRF" else "cLocation")
            if not il.get("lMixLots", True) and any(k[0] == prod["cCode"].upper() and k[3] != _s(m.get("cLot")).upper() for k in others):
                raise ApiError("location_mixed_lots", "cLocTo" if m["cType"] == "TRF" else "cLocation")
        return prod

    def post_movement(m, prod):
        """Cost the movement (moving average per product) and add it."""
        q = _f(m["dQty"])
        qty_before = product_totals(prod["cCode"])[0]
        avg = _f(prod.get("dAvgCost"))
        increases = m["cType"] == "IN" or (m["cType"] in ("ADJ", "CNT") and q > 0)
        if increases:
            cost = _f(m["dUnitCost"]) if _s(m.get("dUnitCost")) else (avg or _f(prod.get("dLastCost")) or _f(prod.get("dStdCost")))
            new_qty = qty_before + q
            new_avg = cost if qty_before <= 0 or new_qty <= 0 else (qty_before * avg + q * cost) / new_qty
            prod["dAvgCost"] = _c(new_avg)
            if m["cType"] == "IN":
                prod["dLastCost"] = _c(cost)
            save_master("products", prod)
            m["dUnitCost"] = _c(cost)
            m["dValue"] = _m(q * cost)
        elif m["cType"] in ("OUT", "ADJ", "CNT"):
            m["dUnitCost"] = _c(avg)
            m["dValue"] = _m(-abs(q) * avg)
        else:  # TRF, RSV: no change in value
            m["dUnitCost"] = _c(avg)
            m["dValue"] = "0.00"
        m["dAvgCostAfter"] = prod.get("dAvgCost", "")
        m["cUser"] = m.get("cUser") or _user()
        m["dCreated"] = datetime.now().isoformat(timespec="seconds")
        if seeding["rows"] is not None:
            m["iNo"] = len(T["movements"]) + 1
            T["movements"].append(m)
            return m
        m["iNo"] = purch.next_number("STOCK_MOVE")
        MOV.insert(m)
        stockdb.apply(m, _effects(m))
        forget_balances()
        return m

    def movement_from(p):
        m = _apply(_blank(MOVEMENT), p, MOVEMENT)
        m["cType"] = m["cType"] or "IN"
        m["cDocType"] = m["cDocType"] or "MAN"
        m["dDate"] = m["dDate"] or _today()
        if m["dQty"] == "":
            raise ApiError("required", "dQty")
        m["dQty"] = _q(_f(m["dQty"]))
        return m

    def movement_view(m):
        prod = _find("products", m["cProduct"]) or {}
        return {**m, "cDescFR": prod.get("cDescFR", ""), "cDescEN": prod.get("cDescEN", ""),
                "cUOM": prod.get("cStockUOM", "")}

    @bp.route("/api/stock-movements", methods=["GET", "POST"])
    def movements_collection():
        if request.method == "GET":
            return jsonify(paginate([movement_view(m) for m in MOV.all()],
                                    ("cProduct", "cDescFR", "cDescEN", "cDocNo", "cLot", "cSerial", "cReason", "cWarehouse")))
        m = movement_from(_payload())
        prod = check_movement(m)
        return jsonify(movement_view(post_movement(m, prod))), 201

    @bp.route("/api/stock-movements/<int:no>", methods=["GET", "PUT", "DELETE"])
    def movements_item(no):
        m = MOV.get(no)
        if m is None:
            raise ApiError("not_found", status=404)
        if request.method != "GET":
            raise ApiError("posted", status=409)  # correct a movement with another movement
        return jsonify(movement_view(m))

    # ------------------------------------------------------------------ stock, valuation, replenishment

    def stock_rows(include_zero=False):
        rows = []
        products = {p["cCode"].upper(): p for p in M("products")}
        for b in balances().values():
            if not include_zero and abs(b["qty"]) < 1e-9 and abs(b["reserved"]) < 1e-9:
                continue
            prod = products.get(b["cProduct"].upper(), {})
            loc = find_location(b["cWarehouse"], b["cLocation"]) if b["cLocation"] else None
            rows.append({"cProduct": b["cProduct"], "cDescFR": prod.get("cDescFR", ""), "cDescEN": prod.get("cDescEN", ""),
                         "cCategory": prod.get("cCategory", ""), "cWarehouse": b["cWarehouse"], "cLocation": b["cLocation"],
                         "cZone": (loc or {}).get("cZone", ""), "cLocationType": (loc or {}).get("cType", ""),
                         "cLot": b["cLot"], "cSerial": b["cSerial"], "dExpiry": b["dExpiry"],
                         "dQtyOnHand": _q(b["qty"]), "dQtyReserved": _q(b["reserved"]),
                         "dQtyAvailable": _q(b["qty"] - b["reserved"]), "cUOM": prod.get("cStockUOM", ""),
                         "dValue": _m(b["qty"] * unit_cost(prod)) if prod else "0.00"})
        rows.sort(key=lambda r: (r["cProduct"], r["cWarehouse"], r["cLocation"], r["cLot"], r["cSerial"]))
        return rows

    @bp.route("/api/inventory/stock")
    def inventory_stock():
        return jsonify(paginate(stock_rows(_bool(request.args.get("zero"))),
                                ("cProduct", "cDescFR", "cDescEN", "cLocation", "cLot", "cSerial")))

    def valuation_rows():
        per = {}
        for b in balances().values():
            k = (b["cProduct"].upper(), b["cWarehouse"].upper())
            per.setdefault(k, {"cProduct": b["cProduct"], "cWarehouse": b["cWarehouse"], "qty": 0.0})["qty"] += b["qty"]
        rows = []
        for v in per.values():
            prod = _find("products", v["cProduct"]) or {}
            cost = unit_cost(prod)
            if abs(v["qty"]) < 1e-9:
                continue
            rows.append({"cProduct": v["cProduct"], "cDescFR": prod.get("cDescFR", ""), "cDescEN": prod.get("cDescEN", ""),
                         "cCategory": prod.get("cCategory", ""), "cWarehouse": v["cWarehouse"],
                         "cCostMethod": prod.get("cCostMethod", "avg"), "dQtyOnHand": _q(v["qty"]),
                         "cUOM": prod.get("cStockUOM", ""), "dUnitCost": _c(cost), "dValue": _m(v["qty"] * cost),
                         "cGLInventory": prod.get("cGLInventory", "")})
        rows.sort(key=lambda r: (r["cProduct"], r["cWarehouse"]))
        return rows

    @bp.route("/api/inventory/valuation")
    def inventory_valuation():
        rows = valuation_rows()
        page = paginate(rows, ("cProduct", "cDescFR", "cDescEN", "cCategory", "cGLInventory"))
        # The total follows the search and the filters, not only the page shown
        total = 0.0
        q = (request.args.get("q") or "").strip().lower()
        for r in rows:
            if q and not any(q in _s(r.get(f)).lower() for f in ("cProduct", "cDescFR", "cDescEN", "cCategory", "cGLInventory")):
                continue
            if any(k.startswith("f_") and v and _s(r.get(k[2:])).lower() != v.lower() for k, v in request.args.items()):
                continue
            total += _f(r["dValue"])
        page["totalValue"] = _m(total)
        return jsonify(page)

    def preferred_supplier(prod):
        lines = prod.get("lines") or []
        return next((l for l in lines if l.get("lPreferred")), lines[0] if lines else None)

    def replenishment_rows():
        rows = []
        bal = balances()
        params = M("stock_params")
        for par in params:
            if not par.get("lActive", True):
                continue
            prod = _find("products", par["cProduct"])
            if not prod or prod.get("cStatus") != "active" or not prod.get("lPurchasable", True):
                continue
            qty, res = product_totals(prod["cCode"], par["cWarehouse"], bal)
            avail = qty - res
            # Open POs are not by warehouse: they count for the product's default warehouse (or its only one)
            params_of_prod = [x for x in params if x["cProduct"].upper() == prod["cCode"].upper()]
            home = prod.get("cDefaultWarehouse") or (params_of_prod[0]["cWarehouse"] if len(params_of_prod) == 1 else "")
            ordered = on_order(prod["cCode"]) if home.upper() == par["cWarehouse"].upper() else 0.0
            projected = avail + ordered
            rop, mn, mx, oq = (_f(par.get(f)) if _s(par.get(f)) else None for f in ("dReorderPoint", "dMinQty", "dMaxQty", "dOrderQty"))
            trigger = rop if rop is not None else mn
            if trigger is None or projected > trigger + 1e-9:
                continue
            if mx is not None and mx > projected:
                need = mx - projected
            elif oq:
                need = oq
            else:
                need = max((mn or 0) - projected, trigger - projected, 0) or 1
            if oq and need < oq:
                need = oq
            sup = preferred_supplier(prod)
            moq = _f((sup or {}).get("dMinOrderQty"))
            if moq and need < moq:
                need = moq
            factor = _f(prod.get("dPurchaseFactor")) or 1
            purchase_qty = math.ceil(need / factor - 1e-9)
            # Price per purchase unit (e.g. a case): the supplier's, else the last / average cost x the factor
            price = _f((sup or {}).get("dPurchasePrice")) or (_f(prod.get("dLastCost")) or _f(prod.get("dAvgCost"))) * factor
            rows.append({"cProduct": prod["cCode"], "cDescFR": prod.get("cDescFR", ""), "cDescEN": prod.get("cDescEN", ""),
                         "cWarehouse": par["cWarehouse"], "dQtyAvailable": _q(avail), "dQtyOnOrder": _q(ordered),
                         "dReorderPoint": par.get("dReorderPoint", ""), "dMinQty": par.get("dMinQty", ""),
                         "dMaxQty": par.get("dMaxQty", ""), "dSuggestedQty": _q(purchase_qty * factor),
                         "cStockUOM": prod.get("cStockUOM", ""), "dPurchaseQty": _q(purchase_qty),
                         "cPurchaseUOM": prod.get("cPurchaseUOM", ""), "dPurchaseFactor": _q(factor),
                         "cSupplierCode": (sup or {}).get("cSupplierCode", ""),
                         "cSupplierName": next((s["cName"] for s in suppliers if s["cCode"] == (sup or {}).get("cSupplierCode")), ""),
                         "cSupplierItem": (sup or {}).get("cSupplierItem", ""),
                         "dUnitCost": _c(price), "iLeadTimeDays": (sup or {}).get("iLeadTimeDays") or par.get("iLeadTimeDays") or 0})
        rows.sort(key=lambda r: (r["cSupplierCode"] or "~", r["cProduct"]))
        return rows

    @bp.route("/api/inventory/replenishment")
    def inventory_replenishment():
        return jsonify(paginate(replenishment_rows(), ("cProduct", "cDescFR", "cDescEN", "cSupplierCode", "cSupplierName")))

    def next_po_number():
        return hooks["next_po_number"](500501)

    def po_taxes(prod, supplier, amount, on):
        """TPS / TVQ of a PO line: the product's purchase tax group, else the supplier's TPS / TVQ numbers."""
        res = tax_calc(prod.get("cPurchaseTaxGroup"), amount, on) if prod.get("cPurchaseTaxGroup") else None
        if res is None:
            return (round(amount * 0.05 + 1e-9, 2) if supplier.get("cNoTPS") else 0.0,
                    round(amount * 0.09975 + 1e-9, 2) if supplier.get("cNoTVQ") else 0.0)
        gst = sum(_f(t["dTax"]) for t in res["taxes"] if t["cKind"] in ("gst", "hst"))
        pst = sum(_f(t["dTax"]) for t in res["taxes"] if t["cKind"] not in ("gst", "hst"))
        return gst, pst

    @bp.route("/api/inventory/replenishment/po", methods=["POST"])
    def replenishment_po():
        """Create one PO per supplier: {"lines": [{"cProduct", "dPurchaseQty", "cSupplierCode"?, "dUnitCost"?}]}"""
        p = _payload()
        lines = [l for l in (p.get("lines") or []) if isinstance(l, dict) and _f(l.get("dPurchaseQty")) > 0]
        if not lines:
            raise ApiError("required", "lines")
        groups = {}
        for i, l in enumerate(lines, 1):
            prod = _find("products", l.get("cProduct"))
            if prod is None:
                raise ApiError("unknown_ref", "lines", detail=f"line {i}: {l.get('cProduct')}")
            sup_line = preferred_supplier(prod) or {}
            code = _s(l.get("cSupplierCode")) or sup_line.get("cSupplierCode", "")
            supplier = next((s for s in suppliers if s["cCode"].upper() == code.upper()), None)
            if supplier is None:
                raise ApiError("no_supplier", "lines", detail=f"line {i}: {prod['cCode']}")
            item = next((x for x in prod.get("lines", []) if x["cSupplierCode"] == supplier["cCode"]), sup_line)
            factor = _f(prod.get("dPurchaseFactor")) or 1
            price = _f(l.get("dUnitCost")) if _s(l.get("dUnitCost")) else (
                _f(item.get("dPurchasePrice")) or (_f(prod.get("dLastCost")) or _f(prod.get("dAvgCost"))) * factor)
            # PO lines are in stock units (like the receptions), so "on order" compares with the stock
            groups.setdefault(supplier["cCode"], (supplier, []))[1].append(
                (prod, _f(l["dPurchaseQty"]) * factor, price / factor, _f(l["dPurchaseQty"])))
        today = _today()
        created = []
        for code, (supplier, items) in groups.items():
            po_lines, gst, pst = [], 0.0, 0.0
            for n, (prod, qty, price, pqty) in enumerate(items, 1):
                desc = prod.get("cDescFR", "")
                if prod.get("cPurchaseUOM") and prod.get("cPurchaseUOM") != prod.get("cStockUOM"):
                    desc += f" ({_q(pqty)} {prod['cPurchaseUOM']})"
                po_lines.append({"cUnique": str(n), "cProductcode": prod["cCode"], "cProductDesc": desc,
                                 "dQuantity": _q(qty), "dUnitCost": _c(price)})
                g, s_ = po_taxes(prod, supplier, qty * price, today)
                gst, pst = gst + g, pst + s_
            cpo = next_po_number()
            view = hooks["save_po"](cpo, {
                "cSupplierCode": code, "cSupplierName": supplier.get("cName", ""),
                "cBuyerCode": supplier.get("cCodeAch", ""), "cBuyerName": supplier.get("cDescAch", ""),
                "cApplicantCode": _user(), "dOrderDate": today, "dCreationDate": today, "dFreight": 0,
                "dGST": gst, "dPST": pst, "lines": po_lines, "lUnbilled": True}, None)
            hooks["update_po_header"](cpo, {"cReference": "REAPPRO " + _s(p.get("cWarehouse")), "cSource": "ERP"})
            created.append({"cPO": cpo, "cSupplierCode": code, "cSupplierName": supplier.get("cName", ""),
                            "lineCount": len(po_lines), "dTotalAmount": view["dTotalAmount"]})
        return jsonify({"purchaseOrders": created}), 201

    # ------------------------------------------------------------------ physical counts

    def count_find(no):
        return CNT.get(no)

    def count_generate(c):
        """Fill the sheet with the current balances of the warehouse (optionally only some locations / products)."""
        lp, pp = _s(c.get("cLocationPrefix")).upper(), _s(c.get("cProductPrefix")).upper()
        keep = {(l["cProduct"], l["cLocation"], l["cLot"], l["cSerial"]): l["dQtyCounted"] for l in c.get("lines", [])}
        lines = []
        for r in stock_rows():
            if r["cWarehouse"].upper() != c["cWarehouse"].upper():
                continue
            if lp and not r["cLocation"].upper().startswith(lp):
                continue
            if pp and not r["cProduct"].upper().startswith(pp):
                continue
            k = (r["cProduct"], r["cLocation"], r["cLot"], r["cSerial"])
            lines.append({"cProduct": r["cProduct"], "cDescFR": r["cDescFR"], "cLocation": r["cLocation"],
                          "cLot": r["cLot"], "cSerial": r["cSerial"], "dQtyExpected": r["dQtyOnHand"],
                          "dQtyCounted": keep.get(k, ""), "dDiff": ""})
        c["lines"] = lines

    def count_view(c):
        out = dict(c)
        lines = []
        for l in c.get("lines", []):
            l = dict(l)
            if l.get("dQtyCounted", "") != "" and c["cStatus"] == "Draft":
                l["dDiff"] = _q(_f(l["dQtyCounted"]) - _f(l.get("dQtyExpected")))
            lines.append(l)
        out["lines"] = lines
        out["lineCount"] = len(lines)
        out["countedLines"] = sum(1 for l in lines if l.get("dQtyCounted", "") != "")
        return out

    def count_save(c, p, is_new):
        if c["cStatus"] != "Draft":
            raise ApiError("posted", status=409)
        _apply(c, p, COUNT, skip=() if is_new else ("cWarehouse",))
        wh = _must("warehouses", c, "cWarehouse", required=True)
        c["cWarehouse"] = wh["cCode"]
        c["dDate"] = c["dDate"] or _today()
        if "lines" in p:
            lines = []
            for i, ln in enumerate(p.get("lines") or [], 1):
                if not isinstance(ln, dict):
                    continue
                row = _apply(_blank(COUNT_LINE), ln, COUNT_LINE)
                if not row["cProduct"]:
                    continue
                prod = _find("products", row["cProduct"])
                if prod is None:
                    raise ApiError("unknown_ref", "lines", detail=f"line {i}: {row['cProduct']}")
                row["cProduct"] = prod["cCode"]
                row["cDescFR"] = prod.get("cDescFR", "")
                row["cLocation"] = row["cLocation"].upper()
                if not row["dQtyExpected"]:
                    k = (prod["cCode"].upper(), wh["cCode"].upper(), row["cLocation"], row["cLot"].upper(), row["cSerial"].upper())
                    row["dQtyExpected"] = _q(balances().get(k, {"qty": 0.0})["qty"])
                row["dDiff"] = ""
                lines.append(row)
            c["lines"] = lines

    @bp.route("/api/stock-counts", methods=["GET", "POST"])
    def counts_collection():
        if request.method == "GET":
            return jsonify(paginate([{k: v for k, v in count_view(c).items() if k != "lines"} for c in CNT.all()],
                                    ("cWarehouse", "cDescription", "cStatus")))
        p = _payload()
        c = {**_blank(COUNT), "cStatus": "Draft", "lines": []}
        count_save(c, p, True)
        if not c["lines"]:
            count_generate(c)
        c["iNo"] = purch.next_number("STOCK_COUNT")
        c["cUser"] = _user()
        CNT.insert(c)
        return jsonify(count_view(c)), 201

    @bp.route("/api/stock-counts/<int:no>", methods=["GET", "PUT", "DELETE"])
    def counts_item(no):
        c = count_find(no)
        if c is None:
            raise ApiError("not_found", status=404)
        if request.method == "GET":
            return jsonify(count_view(c))
        if c["cStatus"] != "Draft":
            raise ApiError("posted", status=409)
        if request.method == "DELETE":
            CNT.delete(c)
            return jsonify({"ok": True})
        work = copy.deepcopy(c)
        count_save(work, _payload(), False)
        CNT.update(work)
        return jsonify(count_view(work))

    @bp.route("/api/stock-counts/<int:no>/generate", methods=["POST"])
    def counts_generate(no):
        c = count_find(no)
        if c is None:
            raise ApiError("not_found", status=404)
        if c["cStatus"] != "Draft":
            raise ApiError("posted", status=409)
        count_generate(c)
        CNT.update(c)
        return jsonify(count_view(c))

    @bp.route("/api/stock-counts/<int:no>/post", methods=["POST"])
    def counts_post(no):
        """Post the count: one CNT movement per counted line whose quantity differs from the stock now.
        Lines without a counted quantity are ignored. All or nothing."""
        c = count_find(no)
        if c is None:
            raise ApiError("not_found", status=404)
        if c["cStatus"] != "Draft":
            raise ApiError("posted", status=409)
        counted = [l for l in c.get("lines", []) if l.get("dQtyCounted", "") != ""]
        if not counted:
            raise ApiError("nothing_counted", "lines")
        bal = balances()
        staged = []
        for i, l in enumerate(counted, 1):
            k = (l["cProduct"].upper(), c["cWarehouse"].upper(), l["cLocation"].upper(), l["cLot"].upper(), l["cSerial"].upper())
            now = bal.get(k, {"qty": 0.0})["qty"]
            diff = round(_f(l["dQtyCounted"]) - now, 6)
            l["dQtyExpected"] = _q(now)
            l["dDiff"] = _q(diff)
            if abs(diff) < 1e-9:
                continue
            m = movement_from({"cType": "CNT", "cProduct": l["cProduct"], "dQty": diff, "cWarehouse": c["cWarehouse"],
                               "cLocation": l["cLocation"], "cLot": l["cLot"], "cSerial": l["cSerial"],
                               "cDocType": "CNT", "cDocNo": str(no), "cReason": c.get("cDescription", ""),
                               "dDate": c.get("dDate") or _today()})
            try:
                prod = check_movement(m, staged)
            except ApiError as e:
                raise ApiError(e.code, "lines", e.status, detail=f"line {i}: {l['cProduct']} {l['cLocation']}".strip())
            staged.append(m)
            m["_prod"] = prod
        posted, value = [], 0.0
        for m in staged:
            prod = m.pop("_prod")
            done = post_movement(m, prod)
            posted.append(done["iNo"])
            value += _f(done["dValue"])
        c.update({"cStatus": "Posted", "dPosted": datetime.now().isoformat(timespec="seconds"), "movements": posted,
                  "dValueDiff": _m(value)})
        CNT.update(c)
        return jsonify(count_view(c))

    # ------------------------------------------------------------------ lookups and dashboard

    def lk(name, label_fields, extra=None, limit=200):
        def fn():
            lang_fr = (request.args.get("lang") or "fr") != "en"
            rows = []
            for r in DB[name].all(lines=False):
                if extra and not extra(r):
                    continue
                label = " · ".join(_s(r.get(f)) for f in label_fields(lang_fr) if _s(r.get(f)))
                rows.append({"code": r["cCode"], "label": label})
            return rows, limit
        return fn

    desc = lambda fr: ("cDescFR",) if fr else ("cDescEN", "cDescFR")  # noqa: E731
    hooks["lookups"].update({
        "taxcodes": lk("tax_codes", desc),
        "taxgroups": lk("tax_groups", desc),
        "uom": lk("uom", desc),
        "categories": lk("categories", desc),
        "products": lk("products", lambda fr: ("cDescFR",) if fr else ("cDescEN", "cDescFR"), limit=30),
        "stockproducts": lk("products", desc, extra=lambda r: r.get("lStocked"), limit=30),
        "warehouses": lk("warehouses", lambda fr: ("cNameFR",) if fr else ("cNameEN", "cNameFR")),
    })

    def locations_lookup():
        wh = _s(request.args.get("wh")).upper()
        rows = [{"code": l["cCode"], "label": " · ".join(x for x in (l["cWarehouse"], l.get("cDescription") or l.get("cType", "")) if x)}
                for l in M("locations") if not wh or l["cWarehouse"].upper() == wh]
        return rows, 200

    hooks["lookups"]["locations"] = locations_lookup

    def summary():
        total = sum(_f(r["dValue"]) for r in valuation_rows())
        return {"products": DB["products"].count(), "warehouses": DB["warehouses"].count(),
                "stockValue": round(total, 2), "reorderItems": len(replenishment_rows())}

    hooks["summary"].append(summary)

    app.register_blueprint(bp)

    # ------------------------------------------------------------------ seed
    # Prepared in memory (the opening movements give the products their average cost), then handed to the ERP,
    # which loads it into the tables when the database is empty and on /api/reset.
    seed = json.loads(SEED_FILE.read_text(encoding="utf-8")) if SEED_FILE.exists() else {}
    seeding["rows"] = {name: copy.deepcopy(seed.get(name, [])) for name in MASTER}
    for p in seeding["rows"]["products"]:
        p.setdefault("lines", [])
        p.setdefault("dAvgCost", "")
        p.setdefault("dLastCost", "")
    for raw in seed.get("movements", []):
        m = movement_from(raw)
        prod = check_movement(m)
        m["cUser"] = "system"
        post_movement(m, prod)
    master_seed = seeding["rows"]
    seeding["rows"] = None
    # Parents before children (cleared in the reverse order)
    hooks["add_stores"]([(DB[name], "inv_" + name, master_seed[name]) for name in
                         ("tax_codes", "tax_groups", "uom", "categories", "warehouses", "locations", "products",
                          "stock_params")]
                        + [(MOV, "inv_movements", T["movements"]), (CNT, "inv_counts", [])])

    def after_load(data):
        """Balances and numbering follow the movements and counts that were loaded."""
        if "inv_movements" in data:
            stockdb.rebuild(MOV.all(), _effects)
            purch.set_next_number("STOCK_MOVE", max((int(x["iNo"]) for x in data["inv_movements"]), default=0) + 1)
        if "inv_counts" in data:
            purch.set_next_number("STOCK_COUNT", max((int(x["iNo"]) for x in data["inv_counts"]), default=0) + 1)
        forget_balances()

    hooks["after_load"].append(after_load)
    hooks["on_clear"].append(stockdb.clear)

    def add_movement(p):
        """Post a movement from another module (e.g. a reception), validated like the screen's."""
        m = movement_from(p)
        return post_movement(m, check_movement(m))

    return {"tax_calc": tax_calc, "balances": balances, "add_movement": add_movement}
