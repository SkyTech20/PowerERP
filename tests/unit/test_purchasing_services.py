"""Unit tests of the purchasing rules that need no database: invoice totals, PO and reception views."""

from powererp.modules.purchasing import InvoiceService, PurchaseOrderService, ReceptionService, compute_invoice

NAMES = {"LUMPRO": "Lumen Pro"}


def name_of(code):
    return NAMES.get(str(code).upper(), "")


def test_invoice_lines_and_totals():
    inv = compute_invoice(
        {
            "cNoFourn": "lumpro",
            "dTransport": "$5",
            "dTotalTPS": "1,25",
            "lines": [
                {"cCodeProduit": "A", "dQuantite": "2", "dCoutUnitaire": "10"},
                {"cDescription": "freight adj.", "dMontant": "3"},
                {"cCodeProduit": "", "cDescription": "", "dMontant": ""},  # empty line: dropped
            ],
        },
        name_of,
    )
    assert [ln["dMontant"] for ln in inv["lines"]] == ["20.00", "3.00"]
    assert inv["lines"][1]["cCodeProduit"] == "LINE" and inv["lines"][1]["dCoutUnitaire"] == "3.00"
    assert (inv["dSousTotal"], inv["dTotalFacture"], inv["lineCount"]) == ("23.00", "29.25", 2)
    assert inv["cNomFourn"] == "Lumen Pro"


def test_total_given_by_the_supplier_is_kept():
    inv = compute_invoice({"dTotalFacture": "99.99", "_keepTotal": True, "lines": []}, name_of)
    assert inv["dTotalFacture"] == "99.99" and "_keepTotal" not in inv


def test_seed_invoices_are_numbered_in_order():
    out = InvoiceService.prepare_seed([{"cNoFourn": "LUMPRO", "lines": []}, {"lines": []}], name_of)
    assert [i["id"] for i in out] == [1, 2] and out[0]["cNomFourn"] == "Lumen Pro"


def test_po_view_from_powerware_records():
    det = {
        "COMPANY": "MA2",
        "cPO": "1",
        "ttPOheader": {"cSupplierCode": "LUMPRO", "dFreight": "5.00", "dGST": "", "dPST": ""},
        "ttPOdetail": [{"cUnique": "1", "cProductcode": "A", "dQuantity": "2", "dUnitCost": "10"}],
    }
    view = PurchaseOrderService.view("1", (det, None))
    assert view["dSubTotal"] == "20.00" and view["dTotalAmount"] == "25.00" and not view["lUnbilled"]
    unbilled_only = PurchaseOrderService.view(
        "2", (None, {"COMPANY": "MA2", "cPO": "2", "dCreationDate": "2026-01-01"})
    )
    assert (
        unbilled_only["lUnbilled"] and unbilled_only["dCreationDate"] == "2026-01-01" and unbilled_only["lines"] == []
    )
    assert PurchaseOrderService.view("3", (None, None)) is None


def test_reception_view_currency_falls_back_to_the_lines():
    det = {
        "NoReception": "7",
        "Articles": [{"CodeArticle": "A", "QuantiteRecue": "2", "PrixUnitaire": "4", "Devise": "USD"}],
    }
    view = ReceptionService.view("7", (det, None))
    assert view["Devise"] == "USD" and view["lines"][0]["Montant"] == "8.00"
