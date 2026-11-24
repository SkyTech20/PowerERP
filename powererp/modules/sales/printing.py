"""Printing the sales invoices (V5): one HTML page in the invoice's language (FR or EN), printed or saved as PDF
by the browser.

What is printed:
- the company (profile, V1): name, address, NEQ, and the GST / HST and QST registration numbers of the active tax
  codes (an invoice with taxes must show them in Quebec);
- the customer: billing address, ship-to address, customer PO, payment terms and due date (terms "n30" = 30 days
  after the invoice date);
- the lines: product, description, quantity, unit, price, discount, net price, amount, and under each line the lots /
  serial numbers that went out of the stock (a posted invoice);
- the totals: subtotal, each tax (code, rate, registration number), total; the note of the company in the language.
A draft prints as such ("DRAFT", its draft number), never with an invoice number.
"""

from __future__ import annotations

import re
from datetime import date, timedelta
from typing import Any

from powererp.core.values import number

Row = dict[str, Any]

TEXTS: dict[str, dict[str, str]] = {
    "fr": {
        "invoice": "Facture",
        "draft": "BROUILLON",
        "draftNo": "Brouillon no",
        "invoiceNo": "No de facture",
        "date": "Date",
        "due": "Échéance",
        "terms": "Conditions",
        "customerPO": "Votre bon de commande",
        "customer": "Client",
        "billTo": "Facturer à",
        "shipTo": "Livrer à",
        "product": "Produit",
        "description": "Description",
        "qty": "Qté",
        "unit": "Unité",
        "price": "Prix",
        "discount": "Esc. %",
        "net": "Prix net",
        "amount": "Montant",
        "subTotal": "Sous-total",
        "discountTotal": "Escomptes accordés",
        "total": "Total",
        "lot": "Lot",
        "serial": "No de série",
        "expiry": "exp.",
        "neq": "NEQ",
        "exempt": "No d'exemption",
        "page": "Imprimer",
        "currency": "Montants en dollars canadiens (CAD).",
    },
    "en": {
        "invoice": "Invoice",
        "draft": "DRAFT",
        "draftNo": "Draft no.",
        "invoiceNo": "Invoice no.",
        "date": "Date",
        "due": "Due date",
        "terms": "Terms",
        "customerPO": "Your PO",
        "customer": "Customer",
        "billTo": "Bill to",
        "shipTo": "Ship to",
        "product": "Product",
        "description": "Description",
        "qty": "Qty",
        "unit": "Unit",
        "price": "Price",
        "discount": "Disc. %",
        "net": "Net price",
        "amount": "Amount",
        "subTotal": "Subtotal",
        "discountTotal": "Discounts given",
        "total": "Total",
        "lot": "Lot",
        "serial": "Serial no.",
        "expiry": "exp.",
        "neq": "NEQ",
        "exempt": "Exemption no.",
        "page": "Print",
        "currency": "Amounts in Canadian dollars (CAD).",
    },
}


def money(v: Any, lang: str) -> str:
    """1234.5 -> "1 234,50 $" (fr) / "$1,234.50" (en)."""
    n = round(number(v), 2)
    s = f"{abs(n):,.2f}"
    sign = "-" if n < 0 else ""
    if lang == "fr":
        return sign + s.replace(",", " ").replace(".", ",") + " $"
    return f"{sign}${s}"


def decimal(v: Any, lang: str, places: int | None = None) -> str:
    """A quantity, a price or a rate as typed (trailing zeros dropped unless `places`), with the decimal comma in fr."""
    n = number(v)
    s = f"{n:,.{places}f}" if places is not None else f"{n:,.6f}".rstrip("0").rstrip(".")
    if lang == "fr":
        return s.replace(",", " ").replace(".", ",")
    return s


def due_date(term_code: str, day: str) -> str:
    """Terms "n30" (net 30 days) -> the invoice date + 30 days; "" when the terms say no number of days."""
    m = re.fullmatch(r"n(?:et)?\s*(\d+)", (term_code or "").strip().lower())
    if not m or not day:
        return ""
    try:
        return (date.fromisoformat(day[:10]) + timedelta(days=int(m.group(1)))).isoformat()
    except ValueError:
        return ""


def address_lines(a: Row | None) -> list[str]:
    if not a:
        return []
    city = " ".join(x for x in (a.get("cCity", ""), a.get("cProvince", ""), a.get("cZipCode", "")) if x)
    country = a.get("cCountry", "")
    lines = [a.get("cAddress1", ""), a.get("cAddress2", ""), city, "" if country in ("", "CA") else country]
    return [x for x in lines if x]


def context(
    inv: Row, company: Row, customer: Row | None, ship_to: Row | None, tax_codes: dict[str, Row], lang: str
) -> Row:
    """Everything the template prints, already formatted in the language."""
    lang = lang if lang in TEXTS else "fr"
    desc = "cDescEN" if lang == "en" else "cDescFR"
    by_line: dict[int, list[str]] = {}
    tx = TEXTS[lang]
    for a in inv.get("allocations", []):
        what = (
            f"{tx['lot']} {a['cLot']}"
            if a.get("cLot")
            else f"{tx['serial']} {a['cSerial']}" if a.get("cSerial") else ""
        )
        if not what:
            continue
        if a.get("dExpiry"):
            what += f" ({tx['expiry']} {a['dExpiry']})"
        by_line.setdefault(int(a["iLine"]), []).append(f"{what} × {decimal(a['dQty'], lang)}")
    lines = [
        {
            "cProduct": ln["cProduct"],
            "cDescription": ln["cDescription"],
            "qty": decimal(ln["dQty"], lang),
            "cUOM": ln["cUOM"],
            "price": decimal(ln["dPrice"], lang, 2),
            "discount": decimal(ln["dDiscountPct"], lang) if number(ln["dDiscountPct"]) else "",
            "net": decimal(ln["dNetPrice"], lang, 2),
            "amount": money(ln["dAmount"], lang),
            "taxGroup": ln.get("cTaxGroup", "") if ln.get("cTaxGroup") != inv.get("cTaxGroup") else "",
            "lots": by_line.get(i, []),
        }
        for i, ln in enumerate(inv.get("lines", []), 1)
    ]
    taxes = []
    for t in inv.get("taxes", []):
        code = tax_codes.get(t["cTaxCode"].upper(), {})
        taxes.append(
            {
                "label": code.get(desc) or t["cTaxCode"],
                "code": t["cTaxCode"],
                "rate": decimal(t["dRate"], lang),
                "number": code.get("cRegistrationNo", ""),
                "base": money(t["dBase"], lang),
                "tax": money(t["dTax"], lang),
            }
        )
    posted = inv.get("cStatus") == "posted"
    customer = customer or {}
    return {
        "lang": lang,
        "t": tx,
        "posted": posted,
        "number": inv.get("cInvoiceNo") if posted else str(inv.get("iNo", "")),
        "inv": inv,
        "due": due_date(inv.get("cTermCode", ""), inv.get("dDate", "")),
        "company": company,
        "companyAddress": address_lines(company),
        "taxNumbers": company.get("taxNumbers", []),
        "customerName": customer.get("cLegalName") or customer.get("cName") or inv.get("cCustomerName", ""),
        "billTo": address_lines(customer),
        "shipToName": (ship_to or {}).get("cName", ""),
        "shipTo": address_lines(ship_to),
        "exemptNo": customer.get("cTaxExemptNo", "") if not inv.get("taxes") else "",
        "lines": lines,
        "taxes": taxes,
        "subTotal": money(inv.get("dSubTotal", 0), lang),
        "discountTotal": money(inv.get("dDiscountTotal", 0), lang) if number(inv.get("dDiscountTotal")) else "",
        "total": money(inv.get("dTotal", 0), lang),
        "note": company.get("cInvoiceNoteEN" if lang == "en" else "cInvoiceNoteFR", ""),
    }
