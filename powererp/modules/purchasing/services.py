"""Purchasing rules: purchase orders, receptions, supplier invoices, billing and document numbering.

The records keep the PowerWARE shape that SkyAI reads (see repository.py): a purchase order is a detail
(ttPOheader + ttPOdetail) and, while not fully invoiced, an "unbilled" record; a reception likewise.
The services build the screens' views from them and apply the rules when they change.
"""

from __future__ import annotations

import copy
from collections.abc import Callable, Iterable
from datetime import datetime
from typing import Any

from powererp.core.errors import AppError, NotFound
from powererp.core.http import require
from powererp.core.values import boolean, decimal_text, money, number, qty_text, text

from . import repository as repo

Row = dict[str, Any]
Rows = list[Row]  # (a module-level alias: inside the classes, "list" is the list() method)
NameOf = Callable[[str], str]

DEFAULT_COMPANY = "MA2"  # PowerWARE company of the demo data


class DocumentNumbering:
    """Next number of each document type (doc_sequences, row locked until the end of the transaction)."""

    def next(self, doc_type: str, start: int = 1, minimum: int | None = None) -> int:
        return repo.next_number(doc_type, start=start, minimum=minimum)

    def set_next(self, doc_type: str, value: int) -> None:
        repo.set_next_number(doc_type, value)


# ---------------------------------------------------------------------- purchase orders

PO_HEADER_TEXT = ("cSupplierCode", "cSupplierName", "cBuyerCode", "cBuyerName", "cApplicantCode", "dOrderDate")


class PurchaseOrderService:
    def __init__(self, supplier_name: NameOf, numbering: DocumentNumbering):
        self.supplier_name = supplier_name
        self.numbering = numbering

    @staticmethod
    def view(cpo: str, records: tuple[Row | None, Row | None]) -> Row | None:
        """The screen's view of a PO from its PowerWARE records (detail, unbilled)."""
        det, unb = records
        if det is None and unb is None:
            return None
        h = (det or {}).get("ttPOheader", {})
        lines = []
        for ln in (det or {}).get("ttPOdetail", []):
            lines.append(
                {
                    "cUnique": text(ln.get("cUnique")),
                    "cProductcode": text(ln.get("cProductcode")),
                    "cProductDesc": text(ln.get("cProductDesc")),
                    "dQuantity": text(ln.get("dQuantity")),
                    "dUnitCost": text(ln.get("dUnitCost")),
                    "dTotalAmount": text(ln.get("dTotalAmount"))
                    or money(number(ln.get("dQuantity")) * number(ln.get("dUnitCost"))),
                }
            )
        sub = text(h.get("dSubTotal")) or money(sum(number(ln["dTotalAmount"]) for ln in lines))
        return {
            "cPO": cpo,
            "COMPANY": (det or unb or {}).get("COMPANY", DEFAULT_COMPANY),
            "dCreationDate": text((unb or {}).get("dCreationDate")) or text(h.get("dOrderDate")),
            "cSupplierCode": text(h.get("cSupplierCode")) or text((unb or {}).get("cSupplierCode")),
            "cSupplierName": text(h.get("cSupplierName")) or text((unb or {}).get("cSupplierName")),
            "cBuyerCode": text(h.get("cBuyerCode")),
            "cBuyerName": text(h.get("cBuyerName")),
            "cApplicantCode": text(h.get("cApplicantCode")),
            "dDueDate": text(h.get("dDueDate")),
            "cReference": text(h.get("cReference")),
            "cSource": text(h.get("cSource")),
            "lBlanketOrder": boolean((unb or {}).get("lBlanketOrder")),
            "lUnbilled": unb is not None,
            "dSubTotal": sub,
            "dFreight": text(h.get("dFreight")),
            "dGST": text(h.get("dGST")),
            "dPST": text(h.get("dPST")),
            "dTotalAmount": text(h.get("dTotalAmount"))
            or money(number(sub) + number(h.get("dFreight")) + number(h.get("dGST")) + number(h.get("dPST"))),
            "lines": lines,
            "lineCount": len(lines),
        }

    def find(self, cpo: str) -> Row | None:
        return self.view(cpo, repo.po_get(cpo))

    def get(self, cpo: str) -> Row:
        view = self.find(cpo)
        if view is None:
            raise NotFound()
        return view

    def exists(self, cpo: str) -> bool:
        return self.find(cpo) is not None

    def list(self) -> Rows:
        return [v for no, det, unb in repo.po_all() if (v := self.view(no, (det, unb))) is not None]

    def lookup(self):
        return [{"code": p["cPO"], "label": p["cSupplierName"]} for p in self.list()], 20

    def create(self, payload: Row) -> Row:
        require(payload, "cPO", "cSupplierCode")
        cpo = text(payload["cPO"])
        if self.exists(cpo):
            raise AppError("duplicate", "cPO", 409)
        return self.save(cpo, payload)

    def update(self, cpo: str, payload: Row) -> Row:
        self.get(cpo)
        require(payload, "cSupplierCode")
        return self.save(cpo, payload)

    def delete(self, cpo: str) -> None:
        self.get(cpo)
        repo.po_put(cpo, None, None)

    def save(self, cpo: str, p: Row) -> Row:
        """Write a PO from a screen (or service) payload: lines and totals, and its unbilled record."""
        company = text(p.get("COMPANY")) or DEFAULT_COMPANY
        if text(p.get("cSupplierCode")) and not text(p.get("cSupplierName")):
            p["cSupplierName"] = self.supplier_name(p["cSupplierCode"])
        lines = []
        for i, ln in enumerate(p.get("lines") or [], start=1):
            if not text(ln.get("cProductcode")) and not text(ln.get("cProductDesc")):
                continue
            lines.append(
                {
                    "cUnique": text(ln.get("cUnique")) or str(i),
                    "cProductcode": text(ln.get("cProductcode")),
                    "cProductDesc": text(ln.get("cProductDesc")),
                    "dQuantity": qty_text(ln.get("dQuantity")),
                    "dUnitCost": decimal_text(ln.get("dUnitCost")),
                    "dTotalAmount": money(number(ln.get("dQuantity")) * number(ln.get("dUnitCost"))),
                }
            )
        sub = sum(number(ln["dTotalAmount"]) for ln in lines)
        freight, gst, pst = number(p.get("dFreight")), number(p.get("dGST")), number(p.get("dPST"))
        header = {f: text(p.get(f)) for f in PO_HEADER_TEXT}
        header["dOrderDate"] = header["dOrderDate"] or text(p.get("dCreationDate"))
        header.update(
            {
                "dSubTotal": money(sub),
                "dFreight": money(freight),
                "dGST": money(gst),
                "dPST": money(pst),
                "dTotalAmount": money(sub + freight + gst + pst),
            }
        )
        det, unb = repo.po_get(cpo)
        if det is None:
            det = {"COMPANY": company, "cPO": cpo, "ttPOheader": {}, "ttPOdetail": []}
        det["COMPANY"] = company
        det["ttPOheader"].update(header)
        det["ttPOdetail"] = lines
        if boolean(p.get("lUnbilled", True)):
            if unb is None:
                unb = {"COMPANY": company, "cPO": cpo}
            unb.update(
                {
                    "COMPANY": company,
                    "dCreationDate": text(p.get("dCreationDate")) or datetime.now().strftime("%Y-%m-%d"),
                    "cSupplierName": header["cSupplierName"],
                    "cSupplierCode": header["cSupplierCode"],
                    "lBlanketOrder": boolean(p.get("lBlanketOrder")),
                }
            )
        else:
            unb = None
        repo.po_put(cpo, det, unb)
        view = self.view(cpo, (det, unb))
        assert view is not None
        return view

    def detail(self, cpo: str) -> Row | None:
        """The PowerWARE detail record (ttPOheader + ttPOdetail), or None."""
        return repo.po_get(cpo)[0]

    def unbilled(self) -> Rows:
        """The PowerWARE unbilled records, in the order they became unbilled (getUnbilledPO.p)."""
        return repo.unbilled_po_list()

    def update_header(self, cpo: str, fields: Row) -> None:
        """Add header fields to a saved PO (due date, reference, source of the POs created by services)."""
        det, unb = repo.po_get(cpo)
        if det is None:
            raise NotFound()
        det["ttPOheader"].update(fields)
        repo.po_put(cpo, det, unb)

    def next_number(self, first: int) -> str:
        """Next PO number: from the "PO" sequence, never below `first` nor an existing (typed) number."""
        nums = [int(no) for no, _d, _u in repo.po_all() if str(no).isdigit()]
        return str(self.numbering.next("PO", start=first, minimum=max([first - 1, *nums]) + 1))

    def last_price(self, supplier: str, product: str) -> float:
        """Unit cost of the product on the supplier's most recent PO (0 when never ordered)."""
        best: tuple[str, float] | None = None
        for po in repo.po_details_list():
            h = po.get("ttPOheader", {})
            if h.get("cSupplierCode") != supplier:
                continue
            for ln in po.get("ttPOdetail", []):
                if ln.get("cProductcode") == product and (best is None or h.get("dOrderDate", "") > best[0]):
                    best = (h.get("dOrderDate", ""), number(ln.get("dUnitCost")))
        return best[1] if best else 0.0

    def quantity_on_order(self, product: str) -> float:
        """Quantity of a product ordered on open POs (not invoiced yet) and not received yet."""
        open_pos = {p["cPO"] for p in repo.unbilled_po_list()}
        receptions = repo.receiving_details_list()
        ordered = received = 0.0
        code = product.upper()
        for po in repo.po_details_list():
            if po["cPO"] not in open_pos:
                continue
            ordered += sum(
                number(ln.get("dQuantity"))
                for ln in po.get("ttPOdetail", [])
                if text(ln.get("cProductcode")).upper() == code
            )
            received += sum(
                number(a.get("QuantiteRecue"))
                for r in receptions
                if text(r.get("NoBonCommande")) == po["cPO"]
                for a in r.get("Articles", [])
                if text(a.get("CodeArticle")).upper() == code
            )
        return max(0.0, ordered - received)

    def find_by_reference(self, reference: str, supplier: str) -> Row | None:
        """The PO a service created for a requisition and supplier (cReference), if any."""
        for po in repo.po_details_list():
            h = po.get("ttPOheader", {})
            if h.get("cReference") == reference and h.get("cSupplierCode") == supplier:
                return po
        return None

    def counts(self) -> Row:
        pos = repo.po_all()
        return {"purchaseOrders": len(pos), "unbilledPOs": sum(1 for _n, _d, u in pos if u is not None)}


# ---------------------------------------------------------------------- receptions

# Where and how a line goes into the stock (receiving.py): location, lot, supplier's lot, serial number, expiry
REC_STOCK_FIELDS = ("cLocation", "cLot", "cSupplierLot", "cSerial", "dExpiry")

REC_TEXT = (
    "DateReception",
    "NoBonCommande",
    "CodeFournisseur",
    "Fournisseur",
    "Statut",
    "Entrepot",
    "ResponsableReception",
    "Commentaires",
)
NEW_UNBILLED_RECEPTION = {
    "StatutFacturation": "En attente de facture",
    "JoursEnAttente": "0",
    "ResponsableFacturation": "Comptabilité",
    "PrioriteFacturation": "Normale",
    "TypeReception": "Standard",
}


class ReceptionService:
    def __init__(self, supplier_name: NameOf):
        self.supplier_name = supplier_name

    @staticmethod
    def view(no: str, records: tuple[Row | None, Row | None]) -> Row | None:
        det, unb = records
        if det is None and unb is None:
            return None
        src = det or unb or {}
        lines = []
        for a in (det or {}).get("Articles", []):
            unit = a.get("PrixUnitaire") or a.get("dUnitCost") or ""
            lines.append(
                {
                    "CodeArticle": text(a.get("CodeArticle")),
                    "Description": text(a.get("Description")),
                    "QuantiteCommandee": text(a.get("QuantiteCommandee")),
                    "QuantiteRecue": text(a.get("QuantiteRecue")),
                    "PrixUnitaire": text(unit),
                    "cGL": text(a.get("cGL")),
                    "cCC1": text(a.get("cCC1")),
                    "cCC2": text(a.get("cCC2")),
                    "Montant": text(a.get("dTotalAmount")) or money(number(a.get("QuantiteRecue")) * number(unit)),
                    **{f: text(a.get(f)) for f in REC_STOCK_FIELDS},
                }
            )
        total = text((det or {}).get("MontantTotal")) or text((unb or {}).get("MontantRecu"))
        return {
            "NoReception": no,
            "COMPANY": src.get("COMPANY", DEFAULT_COMPANY),
            "DateReception": text(src.get("DateReception")),
            "NoBonCommande": text(src.get("NoBonCommande")),
            "CodeFournisseur": text(src.get("CodeFournisseur")),
            "Fournisseur": text(src.get("Fournisseur")),
            "Statut": text((det or {}).get("Statut")),
            "Entrepot": text(src.get("Entrepot")),
            "ResponsableReception": text((det or {}).get("ResponsableReception")),
            "Commentaires": text((det or {}).get("Commentaires")),
            "Devise": text((unb or {}).get("Devise"))
            or next((text(a.get("Devise")) for a in (det or {}).get("Articles", []) if a.get("Devise")), "CAD"),
            "SousTotal": text((det or {}).get("SousTotal")),
            "Transport": text((det or {}).get("Transport")),
            "TPS": text((det or {}).get("TPS")),
            "TVQ": text((det or {}).get("TVQ")),
            "MontantTotal": total,
            "lUnbilled": unb is not None,
            "lStockPosted": boolean((det or {}).get("lStockPosted", False)),
            "dStockPosted": text((det or {}).get("dStockPosted")),
            "cStockPostedBy": text((det or {}).get("cStockPostedBy")),
            "lines": lines,
            "lineCount": len(lines),
        }

    def find(self, no: str) -> Row | None:
        return self.view(no, repo.rec_get(no))

    def get(self, no: str) -> Row:
        view = self.find(no)
        if view is None:
            raise NotFound()
        return view

    def list(self) -> Rows:
        return [v for no, det, unb in repo.rec_all() if (v := self.view(no, (det, unb))) is not None]

    def detail(self, no: str) -> Row | None:
        """The PowerWARE detail record (with its Articles), or None."""
        return repo.rec_get(no)[0]

    def unbilled(self) -> Rows:
        """The PowerWARE unbilled records, in the order they became unbilled (getUnbilledReceiving.p)."""
        return repo.unbilled_receiving_list()

    def create(self, payload: Row) -> Row:
        require(payload, "NoReception", "NoBonCommande", "DateReception")
        no = text(payload["NoReception"])
        if not no.isdigit():
            raise AppError("numeric", "NoReception")
        if self.find(no):
            raise AppError("duplicate", "NoReception", 409)
        return self.save(no, payload)

    def update(self, no: str, payload: Row) -> Row:
        self.not_posted(no)
        require(payload, "NoBonCommande", "DateReception")
        return self.save(no, payload)

    def delete(self, no: str) -> None:
        self.not_posted(no)
        repo.rec_put(no, None, None)

    def not_posted(self, no: str) -> Row:
        """The reception, while it is not in the stock yet: once posted it is no longer changed or deleted (409)."""
        view = self.get(no)
        if view["lStockPosted"]:
            raise AppError("posted", status=409)
        return view

    def save(self, no: str, p: Row) -> Row:
        company = text(p.get("COMPANY")) or DEFAULT_COMPANY
        if text(p.get("CodeFournisseur")) and not text(p.get("Fournisseur")):
            p["Fournisseur"] = self.supplier_name(p["CodeFournisseur"])
        currency = text(p.get("Devise")) or "CAD"
        articles = []
        for ln in p.get("lines") or []:
            if not text(ln.get("CodeArticle")) and not text(ln.get("Description")):
                continue
            articles.append(
                {
                    "CodeArticle": text(ln.get("CodeArticle")),
                    "Description": text(ln.get("Description")),
                    "QuantiteCommandee": qty_text(ln.get("QuantiteCommandee")),
                    "QuantiteRecue": qty_text(ln.get("QuantiteRecue")),
                    "PrixUnitaire": decimal_text(ln.get("PrixUnitaire")),
                    "Devise": currency,
                    "dTotalAmount": money(number(ln.get("QuantiteRecue")) * number(ln.get("PrixUnitaire"))),
                    "cGL": text(ln.get("cGL")),
                    "cCC1": text(ln.get("cCC1")),
                    "cCC2": text(ln.get("cCC2")),
                    **{f: text(ln.get(f)) for f in REC_STOCK_FIELDS},
                }
            )
        sub = sum(number(a["dTotalAmount"]) for a in articles)
        freight, tps, tvq = number(p.get("Transport")), number(p.get("TPS")), number(p.get("TVQ"))
        total = sub + freight + tps + tvq
        det, unb = repo.rec_get(no)
        if det is None:
            det = {"NoReception": no}
        det.update({f: text(p.get(f)) for f in REC_TEXT})
        det.update(
            {
                "COMPANY": company,
                "Articles": articles,
                "SousTotal": money(sub),
                "Transport": money(freight),
                "TPS": money(tps),
                "TVQ": money(tvq),
                "MontantTotal": money(total),
            }
        )
        if boolean(p.get("lUnbilled", True)):
            if unb is None:
                unb = {"NoReception": no, **NEW_UNBILLED_RECEPTION}
            unb.update(
                {
                    "COMPANY": company,
                    "DateReception": det["DateReception"],
                    "NoBonCommande": det["NoBonCommande"],
                    "Fournisseur": det["Fournisseur"],
                    "CodeFournisseur": det["CodeFournisseur"],
                    "MontantRecu": money(total),
                    "Devise": currency,
                    "Entrepot": det["Entrepot"],
                }
            )
        else:
            unb = None
        repo.rec_put(no, det, unb)
        view = self.view(no, (det, unb))
        assert view is not None
        return view

    def counts(self) -> Row:
        recs = repo.rec_all()
        return {"receptions": len(recs), "unbilledReceptions": sum(1 for _n, _d, u in recs if u is not None)}


# ---------------------------------------------------------------------- billing


class BillingService:
    """What an invoice bills. An invoice bills the receptions on its lines (iNoReception); an invoice with a PO and
    no reception numbers bills every open reception of that PO. Billed receptions leave getUnbilledReceiving.p, and
    a PO whose receptions are all billed leaves getUnbilledPO.p."""

    def mark_billed(self, invoice: Row) -> None:
        recs = {text(ln.get("iNoReception")) for ln in invoice.get("lines") or []} - {"", "0"}
        po = text(invoice.get("cNoCommAch"))
        all_recs = repo.rec_all()
        unbilled = [u for _n, _d, u in all_recs if u is not None]
        if po and not recs:
            recs = {r["NoReception"] for r in unbilled if text(r.get("NoBonCommande")) == po}
        if not recs:
            return
        pos = {po} if po else set()
        pos |= {
            text(r.get("NoBonCommande"))
            for _n, d, u in all_recs
            for r in (d, u)
            if r is not None and r["NoReception"] in recs
        }
        repo.rec_set_billed(recs)
        still_open = {text(r.get("NoBonCommande")) for r in unbilled if r["NoReception"] not in recs}
        repo.po_set_billed(
            [p["cPO"] for p in repo.unbilled_po_list() if p["cPO"] in pos - {""} and p["cPO"] not in still_open]
        )


# ---------------------------------------------------------------------- invoices

INVOICE_TEXT = ("cNoFourn", "cNoFacture", "dDateFacture", "cNoCommAch", "cDevise", "cStatut")
INVOICE_AMOUNTS = ("dTransport", "dTotalTPS", "dTotalTVP")


def compute_invoice(inv: Row, supplier_name: NameOf) -> Row:
    """Clean the lines (empty ones dropped, amount = quantity x unit cost) and compute the totals of an invoice.
    A total given by the supplier (_keepTotal) is kept as is."""
    lines = []
    for ln in inv.get("lines") or []:
        if not text(ln.get("cCodeProduit")) and not text(ln.get("cDescription")) and not number(ln.get("dMontant")):
            continue
        qty, unit = number(ln.get("dQuantite"), 1), number(ln.get("dCoutUnitaire"))
        line_amount = qty * unit if unit else number(ln.get("dMontant"))
        lines.append(
            {
                "cCodeProduit": text(ln.get("cCodeProduit")) or "LINE",
                "cDescription": text(ln.get("cDescription")),
                "dQuantite": qty_text(qty),
                "dCoutUnitaire": money(unit if unit else line_amount / (qty or 1)),
                "dMontant": money(line_amount),
                "cGL": text(ln.get("cGL")),
                "cCC1": text(ln.get("cCC1")),
                "cCC2": text(ln.get("cCC2")),
                "iNoReception": text(ln.get("iNoReception")),
            }
        )
    inv["lines"] = lines
    sub = sum(number(ln["dMontant"]) for ln in lines)
    inv["dSousTotal"] = money(sub)
    for f in INVOICE_AMOUNTS:
        inv[f] = money(inv.get(f))
    if not inv.get("_keepTotal"):
        inv["dTotalFacture"] = money(sub + sum(number(inv[f]) for f in INVOICE_AMOUNTS))
    inv.pop("_keepTotal", None)
    inv["cNomFourn"] = supplier_name(inv.get("cNoFourn") or "") or text(inv.get("cNomFourn"))
    inv["lineCount"] = len(lines)
    return inv


class InvoiceService:
    def __init__(
        self,
        supplier_name: NameOf,
        billing: BillingService,
        numbering: DocumentNumbering,
        receptions: ReceptionService,
    ):
        self.supplier_name = supplier_name
        self.billing = billing
        self.numbering = numbering
        self.receptions = receptions

    @staticmethod
    def with_count(inv: Row) -> Row:
        return {**inv, "lineCount": len(inv.get("lines", []))}

    def list(self) -> Rows:
        return repo.inv_all()

    def get(self, no: int) -> Row:
        inv = repo.inv_get(no)
        if inv is None:
            raise NotFound()
        return inv

    def exists(self, supplier: str, number_: str, exclude_no: int | None = None) -> bool:
        return repo.inv_duplicate(supplier, number_, exclude_no)

    def _from_payload(self, p: Row, inv: Row) -> Row:
        for f in INVOICE_TEXT:
            if f in p:
                inv[f] = text(p[f])
        for f in INVOICE_AMOUNTS:
            inv[f] = p.get(f, inv.get(f))
        inv["lines"] = p.get("lines") or []
        inv["cDevise"] = inv.get("cDevise") or "CAD"
        inv["cStatut"] = inv.get("cStatut") or "Draft"
        return compute_invoice(inv, self.supplier_name)

    def create(self, p: Row) -> Row:
        require(p, "cNoFourn", "cNoFacture", "dDateFacture")
        if self.exists(text(p["cNoFourn"]), text(p["cNoFacture"])):
            raise AppError("duplicate", "cNoFacture", 409)
        inv = self._from_payload(p, {"cSource": "ERP"})
        inv["id"] = self.numbering.next("AP_INVOICE")
        repo.inv_put(inv)
        self.billing.mark_billed(inv)
        return inv

    def update(self, no: int, p: Row) -> Row:
        inv = self.get(no)
        require(p, "cNoFourn", "cNoFacture", "dDateFacture")
        if self.exists(text(p["cNoFourn"]), text(p["cNoFacture"]), no):
            raise AppError("duplicate", "cNoFacture", 409)
        self._from_payload(p, inv)
        repo.inv_put(inv)
        self.billing.mark_billed(inv)
        return inv

    def delete(self, no: int) -> None:
        self.get(no)
        repo.inv_delete(no)

    def add(self, inv: Row) -> Row:
        """Number, compute, save and bill an invoice built by a service (e.g. sent by SkyAI)."""
        inv["id"] = self.numbering.next("AP_INVOICE")
        compute_invoice(inv, self.supplier_name)
        repo.inv_put(inv)
        self.billing.mark_billed(inv)
        return inv

    def from_powerware(self, header: Row, lines: Iterable[Row]) -> Row:
        """An ERP invoice from a PowerWARE dsInput (ttInputHD / ttInputDT), as SkyAI sends it."""
        inv: Row = {
            "cNoFourn": header.get("cNoFourn", ""),
            "cNoFacture": header.get("cNoFacture", ""),
            "dDateFacture": header.get("dDateFacture", "") or datetime.now().strftime("%Y-%m-%d"),
            "cNoCommAch": header.get("cNoCommAch", ""),
            "cDevise": "CAD",
            "cStatut": "Draft" if boolean(header.get("lIncomplete")) else "Posted",
            "cSource": "SkyAI",
            "dTransport": header.get("dTransport", "0"),
            "dTotalTPS": header.get("dTotalTPS", "0"),
            "dTotalTVP": header.get("dTotalTVP", "0"),
            "lines": [],
        }
        for d in lines:
            rec_no = d.get("iNoReception", "")
            rec_no = "" if rec_no in ("", "0") else rec_no
            code = d.get("cCodeProduit", "")
            desc = ""
            if rec_no:
                rec = self.receptions.detail(rec_no)
                art = next((a for a in (rec or {}).get("Articles", []) if a.get("CodeArticle") == code), None)
                desc = (art or {}).get("Description", "")
                inv["cDevise"] = (art or {}).get("Devise") or inv["cDevise"]
            inv["lines"].append(
                {
                    "cCodeProduit": code,
                    "cDescription": desc,
                    "dQuantite": d.get("dQteFacturee") or d.get("dQuantite") or "1",
                    "dCoutUnitaire": d.get("dCoutUnitaire", ""),
                    "dMontant": d.get("dMontant", ""),
                    "cGL": d.get("cGL", ""),
                    "cCC1": d.get("cCC1", ""),
                    "cCC2": d.get("cCC2", ""),
                    "iNoReception": rec_no,
                }
            )
        if header.get("dTotalFacture"):
            inv["dTotalFacture"] = money(header["dTotalFacture"])
            inv["_keepTotal"] = True
        return self.add(inv)

    @staticmethod
    def prepare_seed(invoices: Iterable[Row], supplier_name: NameOf) -> Rows:
        """The seed invoices numbered 1, 2, ... and computed (no database: done at start-up)."""
        out = []
        for i, raw in enumerate(invoices, 1):
            inv = copy.deepcopy(raw)
            inv["id"] = i
            out.append(compute_invoice(inv, supplier_name))
        return out

    def dashboard(self) -> Row:
        invoices = self.list()
        open_inv = [i for i in invoices if i.get("cStatut") in ("Draft", "Approved")]
        return {
            "invoices": len(invoices),
            "openInvoices": len(open_inv),
            "openInvoicesAmount": round(sum(number(i.get("dTotalFacture")) for i in open_inv), 2),
            "recentInvoices": [self.with_count(i) for i in sorted(invoices, key=lambda i: i["id"], reverse=True)[:5]],
        }
