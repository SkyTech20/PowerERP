"""Purchasing tables (phase R2): purchase orders, receptions, supplier invoices, each with its lines.

PowerWARE (and so SkyAI) sees a purchase order as two records: its detail (getPODetails.p: ttPOheader +
ttPOdetail) and, while it is not fully invoiced, an "unbilled" record (getUnbilledPO.p). Here a purchase order
is one row with two flags, has_detail and unbilled, and the fields of both records; receptions likewise
(getReceivingDetails.p / getUnbilledReceiving.p). powererp.purchasing rebuilds the PowerWARE records from them.

Field maps: PowerWARE / API key -> (column, kind). Kinds: s = TEXT, d = NUMERIC (keeps the scale), date = DATE,
b = BOOLEAN. Every mapped column is nullable: NULL means the record did not have that key. Keys that are not
mapped are kept in the JSONB column `extra`, so nothing sent by SkyAI or found in older data is lost.
"""
from sqlalchemy import BigInteger, Boolean, Column, Date, ForeignKey, Index, Integer, Numeric, Table, Text, text
from sqlalchemy.dialects.postgresql import JSONB

from ..database import Base

_TYPES = {"s": Text, "d": Numeric, "date": Date, "b": Boolean}

# ------------------------------------------------------------------ purchase orders
PO_DOC = {"COMPANY": ("pw_company", "s")}
PO_HEADER = {
    "cSupplierCode": ("supplier_code", "s"), "cSupplierName": ("supplier_name", "s"),
    "cBuyerCode": ("buyer_code", "s"), "cBuyerName": ("buyer_name", "s"), "cApplicantCode": ("applicant_code", "s"),
    "dOrderDate": ("order_date", "date"), "dDueDate": ("due_date", "date"), "cReference": ("reference", "s"),
    "cSource": ("source", "s"), "dSubTotal": ("sub_total", "d"), "dFreight": ("freight", "d"),
    "dGST": ("gst", "d"), "dPST": ("pst", "d"), "dTotalAmount": ("total_amount", "d"),
}
PO_UNBILLED = {
    "COMPANY": ("unb_pw_company", "s"), "dCreationDate": ("creation_date", "date"),
    "cSupplierCode": ("unb_supplier_code", "s"), "cSupplierName": ("unb_supplier_name", "s"),
    "lBlanketOrder": ("blanket_order", "b"),
}
PO_LINE = {
    "cUnique": ("line_ref", "s"), "cProductcode": ("product_code", "s"), "cProductDesc": ("product_desc", "s"),
    "dQuantity": ("quantity", "d"), "dUnitCost": ("unit_cost", "d"), "dSubTotal": ("sub_total", "d"),
    "dTotalAmount": ("total_amount", "d"), "dFreight": ("freight", "d"), "dGST": ("gst", "d"), "dPST": ("pst", "d"),
}

# ------------------------------------------------------------------ receptions
REC_DOC = {
    "COMPANY": ("pw_company", "s"), "DateReception": ("reception_date", "date"), "Fournisseur": ("supplier_name", "s"),
    "CodeFournisseur": ("supplier_code", "s"), "NoBonCommande": ("po_no", "s"), "Statut": ("status", "s"),
    "Entrepot": ("warehouse", "s"), "MontantTotal": ("total_amount", "d"), "ResponsableReception": ("received_by", "s"),
    "Commentaires": ("comments", "s"), "SousTotal": ("sub_total", "d"), "Transport": ("freight", "d"),
    "TPS": ("gst", "d"), "TVQ": ("pst", "d"),
}
REC_UNBILLED = {
    "COMPANY": ("unb_pw_company", "s"), "DateReception": ("unb_reception_date", "date"),
    "NoBonCommande": ("unb_po_no", "s"), "Fournisseur": ("unb_supplier_name", "s"),
    "CodeFournisseur": ("unb_supplier_code", "s"), "MontantRecu": ("amount_received", "d"),
    "StatutFacturation": ("billing_status", "s"), "JoursEnAttente": ("days_waiting", "s"),
    "ResponsableFacturation": ("billing_owner", "s"), "PrioriteFacturation": ("billing_priority", "s"),
    "Devise": ("currency", "s"), "Entrepot": ("unb_warehouse", "s"), "TypeReception": ("reception_type", "s"),
}
REC_LINE = {
    "CodeArticle": ("item_code", "s"), "Description": ("description", "s"),
    "QuantiteCommandee": ("qty_ordered", "d"), "QuantiteRecue": ("qty_received", "d"),
    "PrixUnitaire": ("unit_price", "d"), "Devise": ("currency", "s"), "dTotalAmount": ("total_amount", "d"),
    "dUnitCost": ("unit_cost", "d"), "dSubTotal": ("sub_total", "d"), "dFreight": ("freight", "d"),
    "dGST": ("gst", "d"), "dPST": ("pst", "d"), "cGL": ("gl_account", "s"), "cCC1": ("cc1", "s"), "cCC2": ("cc2", "s"),
}

# ------------------------------------------------------------------ supplier invoices
INV_DOC = {
    "cNoFourn": ("supplier_code", "s"), "cNomFourn": ("supplier_name", "s"), "cNoFacture": ("invoice_number", "s"),
    "dDateFacture": ("invoice_date", "date"), "cNoCommAch": ("po_no", "s"), "cDevise": ("currency", "s"),
    "cStatut": ("status", "s"), "cSource": ("source", "s"), "dTransport": ("freight", "d"),
    "dTotalTPS": ("gst", "d"), "dTotalTVP": ("pst", "d"), "dSousTotal": ("sub_total", "d"),
    "dTotalFacture": ("total", "d"),
}
INV_LINE = {
    "cCodeProduit": ("product_code", "s"), "cDescription": ("description", "s"), "dQuantite": ("quantity", "d"),
    "dCoutUnitaire": ("unit_cost", "d"), "dMontant": ("amount", "d"), "cGL": ("gl_account", "s"),
    "cCC1": ("cc1", "s"), "cCC2": ("cc2", "s"), "iNoReception": ("reception_no", "s"),
}


def _cols(*maps):
    seen, out = set(), []
    for m in maps:
        for col, kind in m.values():
            if col not in seen:
                seen.add(col)
                out.append(Column(col, _TYPES[kind], nullable=True))
    return out


def _doc_table(name, key_col, maps):
    return Table(
        name, Base.metadata,
        Column("id", BigInteger, primary_key=True, autoincrement=True),
        Column("company_id", BigInteger, ForeignKey("companies.id"), nullable=False, index=True),
        Column(key_col, Text, nullable=False),
        *maps,
        Column("extra", JSONB, nullable=False, server_default=text("'{}'::jsonb")),
        Index(f"uq_{name}_key", "company_id", key_col, unique=True),
    )


def _line_table(name, parent, maps):
    return Table(
        name, Base.metadata,
        Column("id", BigInteger, primary_key=True, autoincrement=True),
        Column("parent_id", BigInteger, ForeignKey(f"{parent}.id", ondelete="CASCADE"), nullable=False, index=True),
        Column("line_no", Integer, nullable=False),
        *maps,
        Column("extra", JSONB, nullable=False, server_default=text("'{}'::jsonb")),
    )


purchase_orders = _doc_table("purchase_orders", "po_no", [
    Column("has_detail", Boolean, nullable=False, server_default="false"),
    Column("unbilled", Boolean, nullable=False, server_default="false"),
    # position in the unbilled list (getUnbilledPO.p / getUnbilledReceiving.p keep the order they were added in)
    Column("unbilled_order", BigInteger, nullable=True),
    *_cols(PO_DOC, PO_HEADER, PO_UNBILLED)])
purchase_order_lines = _line_table("purchase_order_lines", "purchase_orders", _cols(PO_LINE))

receptions = _doc_table("receptions", "reception_no", [
    Column("has_detail", Boolean, nullable=False, server_default="false"),
    Column("unbilled", Boolean, nullable=False, server_default="false"),
    # position in the unbilled list (getUnbilledPO.p / getUnbilledReceiving.p keep the order they were added in)
    Column("unbilled_order", BigInteger, nullable=True),
    *_cols(REC_DOC, REC_UNBILLED)])
reception_lines = _line_table("reception_lines", "receptions", _cols(REC_LINE))

# invoice_no is the number shown in the ERP (/api/invoices/<no>), from doc_sequences ("AP_INVOICE")
ap_invoices = Table(
    "ap_invoices", Base.metadata,
    Column("id", BigInteger, primary_key=True, autoincrement=True),
    Column("company_id", BigInteger, ForeignKey("companies.id"), nullable=False, index=True),
    Column("invoice_no", Integer, nullable=False),
    *_cols(INV_DOC),
    Column("extra", JSONB, nullable=False, server_default=text("'{}'::jsonb")),
    Index("uq_ap_invoices_no", "company_id", "invoice_no", unique=True),
    Index("ix_ap_invoices_supplier_number", "company_id", text("lower(supplier_code)"), text("lower(invoice_number)")),
)
ap_invoice_lines = _line_table("ap_invoice_lines", "ap_invoices", _cols(INV_LINE))
