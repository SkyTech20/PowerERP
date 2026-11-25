"""Purchase orders, receptions and supplier invoices in the tables of powererp.models.purchasing.

The ERP routes and the PowerWARE services keep working on the PowerWARE records, so this module reads and
writes them in that shape:
  purchase order  det = {"COMPANY", "cPO", "ttPOheader": {...}, "ttPOdetail": [...]}   (or None)
                  unb = {"COMPANY", "cPO", "dCreationDate", "cSupplierCode", "cSupplierName", "lBlanketOrder"} (or None)
  reception       det = {"NoReception", "COMPANY", ..., "Articles": [...]}             (or None)
                  unb = {"NoReception", "COMPANY", "MontantRecu", "StatutFacturation", ...}  (or None)
  invoice         {"id", "cNoFourn", "cNoFacture", ..., "lines": [...], "lineCount"}
Every call uses the session of the current request (powererp.database.current()).
"""

from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from sqlalchemy import delete, func, insert, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert

from powererp import database
from powererp.models import DocSequence
from powererp.models import purchasing as m
from powererp.store import company_id

# ------------------------------------------------------------------ value conversion


def _to_db(kind, v):
    if v is None:
        return None
    if kind == "d":
        sv = str(v).strip()
        if sv == "":
            return None
        try:
            return Decimal(sv)
        except InvalidOperation:
            raise ValueError(f"not a number: {v!r}") from None
    if kind == "date":
        sv = str(v).strip()[:10]
        return date.fromisoformat(sv) if sv else None
    if kind == "b":
        return v in (True, "true", "True", 1, "1", "on", "yes")
    if kind == "ts":
        sv = str(v).strip()
        return datetime.fromisoformat(sv) if sv else None
    return str(v)


def _from_db(kind, v):
    if kind == "d":
        return format(v, "f")
    if kind == "date":
        return v.isoformat()
    if kind == "ts":
        return v.isoformat(timespec="seconds")
    return v


def _split(doc, fmap, skip=()):
    """(column values, extra) of a record: mapped keys to columns, the rest to extra."""
    cols, extra = {}, {}
    for k, v in (doc or {}).items():
        if k in skip:
            continue
        if k in fmap:
            col, kind = fmap[k]
            try:
                cols[col] = _to_db(kind, v)
            except ValueError:
                # Not a number / date (e.g. a date sent as 10/01/2026): kept as sent rather than refused.
                cols[col] = None
                extra[k] = v
        else:
            extra[k] = v
    return cols, extra


def _join(row, fmap, extra=None):
    """The record of a row: keys whose column is not NULL, plus the extra keys."""
    out = {}
    for k, (col, kind) in fmap.items():
        v = row[col]
        if v is not None:
            out[k] = _from_db(kind, v)
    out.update(extra or {})
    return out


def _all_cols(*maps):
    return {col for fm in maps for col, _k in fm.values()}


def _session():
    return database.current()


def _lines_of(s, table, parent_ids):
    out: dict[int, list] = {pid: [] for pid in parent_ids}
    if parent_ids:
        q = select(table).where(table.c.parent_id.in_(list(parent_ids))).order_by(table.c.parent_id, table.c.line_no)
        for r in s.execute(q).mappings():
            out[r["parent_id"]].append(r)
    return out


def _write_lines(s, table, fmap, parent_id, lines):
    s.execute(delete(table).where(table.c.parent_id == parent_id))
    rows = []
    for i, ln in enumerate(lines or [], 1):
        cols, extra = _split(ln, fmap)
        rows.append({"parent_id": parent_id, "line_no": i, **{c: cols.get(c) for c in _all_cols(fmap)}, "extra": extra})
    if rows:
        s.execute(insert(table).values(rows))


def _bulk_insert(table, key_col, docs, line_table, line_map):
    """Insert many documents in a few statements: docs = [(key, values, lines)]."""
    if not docs:
        return
    s = _session()
    cid = company_id()
    ids = {}
    for i in range(0, len(docs), 300):
        part = docs[i : i + 300]
        q = insert(table).values([{"company_id": cid, key_col: str(k), **vals} for k, vals, _l in part])
        for r in s.execute(q.returning(table.c.id, table.c[key_col])):
            ids[r[1]] = r[0]
    cols = _all_cols(line_map)
    rows = []
    for k, _vals, lines in docs:
        for n, ln in enumerate(lines or [], 1):
            lc, extra = _split(ln, line_map)
            rows.append({"parent_id": ids[str(k)], "line_no": n, **{c: lc.get(c) for c in cols}, "extra": extra})
    for i in range(0, len(rows), 500):
        s.execute(insert(line_table).values(rows[i : i + 500]))


# ------------------------------------------------------------------ purchase orders

_PO_COLS = _all_cols(m.PO_DOC, m.PO_HEADER, m.PO_UNBILLED)


def _po_records(r, lines):
    extra = r["extra"] or {}
    det = unb = None
    if r["has_detail"]:
        det = {
            **_join(r, m.PO_DOC, extra.get("doc")),
            "cPO": r["po_no"],
            "ttPOheader": _join(r, m.PO_HEADER, extra.get("header")),
            "ttPOdetail": [_join(ln, m.PO_LINE, ln["extra"]) for ln in lines],
        }
    if r["unbilled"]:
        unb = {**_join(r, m.PO_UNBILLED, extra.get("unbilled")), "cPO": r["po_no"]}
    return det, unb


def po_all():
    """[(cPO, det, unb)] of every purchase order, in creation order."""
    s = _session()
    t = m.purchase_orders
    # PowerWARE order: the POs with a detail first (in creation order), then the unbilled-only ones
    rows = (
        s.execute(select(t).where(t.c.company_id == company_id()).order_by(t.c.has_detail.desc(), t.c.id))
        .mappings()
        .all()
    )
    lines = _lines_of(s, m.purchase_order_lines, [r["id"] for r in rows])
    return [(r["po_no"], *_po_records(r, lines[r["id"]])) for r in rows]


def po_get(cpo):
    """(det, unb) of a purchase order; (None, None) when it does not exist."""
    s = _session()
    t = m.purchase_orders
    r = s.execute(select(t).where(t.c.company_id == company_id(), t.c.po_no == str(cpo))).mappings().first()
    if r is None:
        return None, None
    return _po_records(r, _lines_of(s, m.purchase_order_lines, [r["id"]])[r["id"]])


def _po_values(det, unb):
    doc_cols, doc_extra = _split(det or {}, m.PO_DOC, skip=("cPO", "ttPOheader", "ttPOdetail"))
    hdr_cols, hdr_extra = _split((det or {}).get("ttPOheader"), m.PO_HEADER)
    unb_cols, unb_extra = _split(unb or {}, m.PO_UNBILLED, skip=("cPO",))
    vals: dict[str, Any] = {c: None for c in _PO_COLS}
    vals.update({**doc_cols, **hdr_cols, **unb_cols})
    vals.update(
        has_detail=det is not None,
        unbilled=unb is not None,
        extra={k: v for k, v in (("doc", doc_extra), ("header", hdr_extra), ("unbilled", unb_extra)) if v},
    )
    return vals


def po_put(cpo, det, unb):
    """Write a purchase order from its two PowerWARE records (both None = delete it)."""
    s = _session()
    t = m.purchase_orders
    cid = company_id()
    pid = s.scalar(select(t.c.id).where(t.c.company_id == cid, t.c.po_no == str(cpo)))
    if det is None and unb is None:
        if pid is not None:
            s.execute(delete(t).where(t.c.id == pid))
        return
    vals = _po_values(det, unb)
    vals["unbilled_order"] = _unbilled_order(s, t, "po_no", cpo, unb is not None)
    if pid is None:
        pid = s.execute(insert(t).values(company_id=cid, po_no=str(cpo), **vals).returning(t.c.id)).scalar()
    else:
        s.execute(update(t).where(t.c.id == pid).values(**vals))
    _write_lines(s, m.purchase_order_lines, m.PO_LINE, pid, (det or {}).get("ttPOdetail"))


def po_replace_all(po_details, unbilled_po):
    """Empty the purchase orders and load the two PowerWARE lists (seed, reset, older JSON data)."""
    po_clear()
    unb = {p["cPO"]: p for p in unbilled_po}
    order = {p["cPO"]: i for i, p in enumerate(unbilled_po, 1)}
    docs, seen = [], set()
    for det in po_details:
        if det["cPO"] not in seen:
            seen.add(det["cPO"])
            docs.append(
                (
                    det["cPO"],
                    {**_po_values(det, unb.get(det["cPO"])), "unbilled_order": order.get(det["cPO"])},
                    det.get("ttPOdetail"),
                )
            )
    for p in unbilled_po:
        if p["cPO"] not in seen:
            seen.add(p["cPO"])
            docs.append((p["cPO"], {**_po_values(None, p), "unbilled_order": order[p["cPO"]]}, []))
    _bulk_insert(m.purchase_orders, "po_no", docs, m.purchase_order_lines, m.PO_LINE)


def po_clear():
    _session().execute(delete(m.purchase_orders).where(m.purchase_orders.c.company_id == company_id()))


def _unbilled_order(s, table, key_col, key, unbilled):
    """Keep the position of a record that stays unbilled; a record that becomes unbilled goes last."""
    if not unbilled:
        return None
    cid = company_id()
    cur = s.scalar(select(table.c.unbilled_order).where(table.c.company_id == cid, table.c[key_col] == str(key)))
    if cur is not None:
        return cur
    return (s.scalar(select(func.max(table.c.unbilled_order)).where(table.c.company_id == cid)) or 0) + 1


def _unbilled_rows(table, key_col):
    s = _session()
    q = (
        select(table.c[key_col])
        .where(table.c.company_id == company_id(), table.c.unbilled.is_(True))
        .order_by(table.c.unbilled_order, table.c.id)
    )
    return [r[0] for r in s.execute(q)]


def po_details_list():
    return [det for _no, det, _unb in po_all() if det is not None]


def unbilled_po_list():
    """The unbilled records, in the order they became unbilled (getUnbilledPO.p)."""
    by_no = {no: unb for no, _det, unb in po_all() if unb is not None}
    return [by_no[no] for no in _unbilled_rows(m.purchase_orders, "po_no")]


# ------------------------------------------------------------------ receptions

_REC_COLS = _all_cols(m.REC_DOC, m.REC_UNBILLED)


def _rec_records(r, lines):
    extra = r["extra"] or {}
    det = unb = None
    if r["has_detail"]:
        det = {
            "NoReception": r["reception_no"],
            **_join(r, m.REC_DOC, extra.get("doc")),
            "Articles": [_join(ln, m.REC_LINE, ln["extra"]) for ln in lines],
        }
    if r["unbilled"]:
        unb = {"NoReception": r["reception_no"], **_join(r, m.REC_UNBILLED, extra.get("unbilled"))}
    return det, unb


def rec_all():
    """[(NoReception, det, unb)] of every reception, in creation order."""
    s = _session()
    t = m.receptions
    rows = (
        s.execute(select(t).where(t.c.company_id == company_id()).order_by(t.c.has_detail.desc(), t.c.id))
        .mappings()
        .all()
    )
    lines = _lines_of(s, m.reception_lines, [r["id"] for r in rows])
    return [(r["reception_no"], *_rec_records(r, lines[r["id"]])) for r in rows]


def rec_get(no):
    s = _session()
    t = m.receptions
    r = s.execute(select(t).where(t.c.company_id == company_id(), t.c.reception_no == str(no))).mappings().first()
    if r is None:
        return None, None
    return _rec_records(r, _lines_of(s, m.reception_lines, [r["id"]])[r["id"]])


def _rec_values(det, unb):
    doc_cols, doc_extra = _split(det or {}, m.REC_DOC, skip=("NoReception", "Articles"))
    unb_cols, unb_extra = _split(unb or {}, m.REC_UNBILLED, skip=("NoReception",))
    vals: dict[str, Any] = {c: None for c in _REC_COLS}
    vals.update({**doc_cols, **unb_cols})
    vals.update(
        has_detail=det is not None,
        unbilled=unb is not None,
        extra={k: v for k, v in (("doc", doc_extra), ("unbilled", unb_extra)) if v},
    )
    return vals


def rec_put(no, det, unb):
    """Write a reception from its two PowerWARE records (both None = delete it)."""
    s = _session()
    t = m.receptions
    cid = company_id()
    rid = s.scalar(select(t.c.id).where(t.c.company_id == cid, t.c.reception_no == str(no)))
    if det is None and unb is None:
        if rid is not None:
            s.execute(delete(t).where(t.c.id == rid))
        return
    vals = _rec_values(det, unb)
    vals["unbilled_order"] = _unbilled_order(s, t, "reception_no", no, unb is not None)
    if rid is None:
        rid = s.execute(insert(t).values(company_id=cid, reception_no=str(no), **vals).returning(t.c.id)).scalar()
    else:
        s.execute(update(t).where(t.c.id == rid).values(**vals))
    _write_lines(s, m.reception_lines, m.REC_LINE, rid, (det or {}).get("Articles"))


def rec_set_billed(numbers):
    """The receptions invoiced: they leave the unbilled list (their detail stays)."""
    if not numbers:
        return
    s = _session()
    t = m.receptions
    cid = company_id()
    nums = [str(n) for n in numbers]
    s.execute(
        update(t)
        .where(t.c.company_id == cid, t.c.reception_no.in_(nums))
        .values(unbilled=False, unbilled_order=None, **{c: None for c in _all_cols(m.REC_UNBILLED)})
    )
    s.execute(delete(t).where(t.c.company_id == cid, t.c.reception_no.in_(nums), t.c.has_detail.is_(False)))


def po_set_billed(numbers):
    """The purchase orders fully invoiced: they leave the unbilled list."""
    if not numbers:
        return
    s = _session()
    t = m.purchase_orders
    cid = company_id()
    nums = [str(n) for n in numbers]
    s.execute(
        update(t)
        .where(t.c.company_id == cid, t.c.po_no.in_(nums))
        .values(unbilled=False, unbilled_order=None, **{c: None for c in _all_cols(m.PO_UNBILLED)})
    )
    s.execute(delete(t).where(t.c.company_id == cid, t.c.po_no.in_(nums), t.c.has_detail.is_(False)))


def rec_replace_all(receiving_details, unbilled_receiving):
    rec_clear()
    unb = {r["NoReception"]: r for r in unbilled_receiving}
    order = {r["NoReception"]: i for i, r in enumerate(unbilled_receiving, 1)}
    docs, seen = [], set()
    for det in receiving_details:
        no = det["NoReception"]
        if no not in seen:
            seen.add(no)
            docs.append((no, {**_rec_values(det, unb.get(no)), "unbilled_order": order.get(no)}, det.get("Articles")))
    for r in unbilled_receiving:
        no = r["NoReception"]
        if no not in seen:
            seen.add(no)
            docs.append((no, {**_rec_values(None, r), "unbilled_order": order[no]}, []))
    _bulk_insert(m.receptions, "reception_no", docs, m.reception_lines, m.REC_LINE)


def rec_clear():
    _session().execute(delete(m.receptions).where(m.receptions.c.company_id == company_id()))


def receiving_details_list():
    return [det for _no, det, _unb in rec_all() if det is not None]


def unbilled_receiving_list():
    """The unbilled records, in the order they became unbilled (getUnbilledReceiving.p)."""
    by_no = {no: unb for no, _det, unb in rec_all() if unb is not None}
    return [by_no[no] for no in _unbilled_rows(m.receptions, "reception_no")]


# ------------------------------------------------------------------ supplier invoices

_INV_SKIP = ("id", "lines")


def _inv_record(r, lines):
    out = {"id": r["invoice_no"], **_join(r, m.INV_DOC, r["extra"])}
    out["lines"] = [_join(ln, m.INV_LINE, ln["extra"]) for ln in lines]
    return out


def inv_all():
    s = _session()
    t = m.ap_invoices
    rows = s.execute(select(t).where(t.c.company_id == company_id()).order_by(t.c.invoice_no)).mappings().all()
    lines = _lines_of(s, m.ap_invoice_lines, [r["id"] for r in rows])
    return [_inv_record(r, lines[r["id"]]) for r in rows]


def inv_get(no):
    s = _session()
    t = m.ap_invoices
    r = s.execute(select(t).where(t.c.company_id == company_id(), t.c.invoice_no == int(no))).mappings().first()
    if r is None:
        return None
    return _inv_record(r, _lines_of(s, m.ap_invoice_lines, [r["id"]])[r["id"]])


def inv_duplicate(supplier, number, exclude_no=None):
    """Another invoice with the same supplier and number (ignoring case)?"""
    t = m.ap_invoices
    q = select(t.c.id).where(
        t.c.company_id == company_id(),
        func.lower(t.c.supplier_code) == str(supplier).lower(),
        func.lower(t.c.invoice_number) == str(number).lower(),
    )
    if exclude_no is not None:
        q = q.where(t.c.invoice_no != int(exclude_no))
    return _session().execute(q.limit(1)).first() is not None


def next_number(doc_type, start=1, minimum=None):
    """Next number of a document type for the company (row locked until the end of the transaction)."""
    s = _session()
    cid = company_id()
    s.execute(
        pg_insert(DocSequence).values(company_id=cid, doc_type=doc_type, next_value=start).on_conflict_do_nothing()
    )
    seq = s.execute(
        select(DocSequence).where(DocSequence.company_id == cid, DocSequence.doc_type == doc_type).with_for_update()
    ).scalar_one()
    value = max(seq.next_value, minimum or 0)
    seq.next_value = value + 1
    s.flush()
    return value


def set_next_number(doc_type, value):
    s = _session()
    cid = company_id()
    s.execute(
        pg_insert(DocSequence)
        .values(company_id=cid, doc_type=doc_type, next_value=value)
        .on_conflict_do_update(index_elements=["company_id", "doc_type"], set_={"next_value": value})
    )


def _inv_values(inv):
    cols, extra = _split(inv, m.INV_DOC, skip=_INV_SKIP)
    return {**{c: cols.get(c) for c in _all_cols(m.INV_DOC)}, "extra": extra}


def inv_put(inv):
    """Insert or replace an invoice (by its "id", the ERP invoice number)."""
    s = _session()
    t = m.ap_invoices
    cid = company_id()
    vals = _inv_values(inv)
    rid = s.scalar(select(t.c.id).where(t.c.company_id == cid, t.c.invoice_no == int(inv["id"])))
    if rid is None:
        rid = s.execute(insert(t).values(company_id=cid, invoice_no=int(inv["id"]), **vals).returning(t.c.id)).scalar()
    else:
        s.execute(update(t).where(t.c.id == rid).values(**vals))
    _write_lines(s, m.ap_invoice_lines, m.INV_LINE, rid, inv.get("lines"))
    return inv


def inv_delete(no):
    t = m.ap_invoices
    _session().execute(delete(t).where(t.c.company_id == company_id(), t.c.invoice_no == int(no)))


def inv_count(statuses=None):
    t = m.ap_invoices
    q = select(func.count()).select_from(t).where(t.c.company_id == company_id())
    if statuses:
        q = q.where(t.c.status.in_(list(statuses)))
    return _session().scalar(q)


def inv_replace_all(invoices):
    inv_clear()
    docs = [(str(int(i["id"])), _inv_values(i), i.get("lines")) for i in invoices]
    if docs:
        s = _session()
        cid = company_id()
        t = m.ap_invoices
        ids = {}
        for i in range(0, len(docs), 300):
            part = docs[i : i + 300]
            q = insert(t).values([{"company_id": cid, "invoice_no": int(k), **v} for k, v, _l in part])
            for r in s.execute(q.returning(t.c.id, t.c.invoice_no)):
                ids[str(r[1])] = r[0]
        cols = _all_cols(m.INV_LINE)
        rows = []
        for k, _v, lines in docs:
            for n, ln in enumerate(lines or [], 1):
                lc, extra = _split(ln, m.INV_LINE)
                rows.append({"parent_id": ids[k], "line_no": n, **{c: lc.get(c) for c in cols}, "extra": extra})
        for i in range(0, len(rows), 500):
            s.execute(insert(m.ap_invoice_lines).values(rows[i : i + 500]))
    set_next_number("AP_INVOICE", max((int(i["id"]) for i in invoices), default=0) + 1)


def inv_clear():
    _session().execute(delete(m.ap_invoices).where(m.ap_invoices.c.company_id == company_id()))
    set_next_number("AP_INVOICE", 1)
