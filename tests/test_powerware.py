"""
PowerWARE web services read by SkyAI (same paths, parameters and XML as the real ones).
These pin the XML contract so SkyAI keeps parsing the ERP the same way.
"""
import xml.etree.ElementTree as ET

from conftest import PW, new_po, new_reception


def _xml(resp):
    assert resp.status_code == 200, resp.get_data(as_text=True)
    assert resp.mimetype == "application/xml"
    return ET.fromstring(resp.get_data())


def _local(e):
    return e.tag.split("}")[-1]


def _all(root, name):
    return [e for e in root.iter() if _local(e) == name]


def _text(elem, name):
    for c in elem:
        if _local(c) == name:
            return (c.text or "").strip()
    return None


def test_company_is_required(client):
    for svc in ("getReceivingDetails.p?NoReception=700101", "getUnbilledPO.p", "getUnbilledReceiving.p",
                "getGLaccounts.p", "getPODetails.p?PO=500101", "getSupplierTerm.p"):
        assert client.get(f"{PW}/{svc}").status_code == 400, svc


def test_get_po_details(client):
    root = _xml(client.get(f"{PW}/getPODetails.p?COMPANY=MA2&PO=500101"))
    assert _local(root) == "dsPOdetail"
    hd = _all(root, "ttPOheader")[0]
    assert _text(hd, "cSupplierCode") == "TECBUR" and _text(hd, "dTotalAmount") == "6714.54"
    lines = _all(root, "ttPOdetail")
    assert [_text(l, "dUnitCost") for l in lines] == ["1250.00", "210.00"]


def test_get_po_details_not_found(client):
    assert client.get(f"{PW}/getPODetails.p?COMPANY=MA2&PO=000000").status_code == 404
    assert client.get(f"{PW}/getPODetails.p?COMPANY=XXX&PO=500101").status_code == 404


def test_po_saved_with_dollar_sign_reaches_skyai_as_numbers(client):
    """Regression: SkyAI received "<dUnitCost>$10.00</dUnitCost>" and lost the amount."""
    new_po(client, lines=[{"cUnique": "1", "cProductcode": "A", "dQuantity": "2", "dUnitCost": "$10.00"}], dGST="$1")
    root = _xml(client.get(f"{PW}/getPODetails.p?COMPANY=MA2&PO=990001"))
    for elem in _all(root, "ttPOheader") + _all(root, "ttPOdetail"):
        for c in elem:
            if _local(c).startswith("d") and _local(c) not in ("dOrderDate", "dDueDate", "dCreationDate"):
                assert "$" not in (c.text or ""), (_local(c), c.text)
    assert _text(_all(root, "ttPOdetail")[0], "dUnitCost") == "10.00"
    assert _text(_all(root, "ttPOheader")[0], "dTotalAmount") == "21.00"


def test_get_receiving_details(client):
    root = _xml(client.get(f"{PW}/getReceivingDetails.p?COMPANY=MA2&NoReception=700101"))
    hd = _all(root, "ttRcvHeader")[0]
    assert _text(hd, "cPO") == "500101" and _text(hd, "dTotalAmount") == "5748.75"
    det = _all(root, "ttRcvDetail")
    assert _text(det[0], "cProductCode") == "LAP-14I7"
    assert float(_text(det[0], "dQtyReceived")) == 4


def test_reception_saved_with_dollar_sign_reaches_skyai_as_numbers(client):
    new_reception(client, lines=[{"CodeArticle": "A", "QuantiteRecue": "3", "PrixUnitaire": "$4.50"}])
    root = _xml(client.get(f"{PW}/getReceivingDetails.p?COMPANY=MA2&NoReception=990101"))
    det = _all(root, "ttRcvDetail")[0]
    assert _text(det, "dUnitCost") == "4.50"
    assert float(_text(det, "dTotalAmount")) == 13.5
    assert _text(_all(root, "ttRcvHeader")[0], "dTotalAmount") == "13.50"


def test_get_unbilled_po_with_supplier_filter(client):
    root = _xml(client.get(f"{PW}/getUnbilledPO.p?COMPANY=MA2&Supplier=tecbur"))
    pos = _all(root, "ttPO")
    assert pos and {_text(p, "cSupplierCode") for p in pos} == {"TECBUR"}
    empty = _xml(client.get(f"{PW}/getUnbilledPO.p?COMPANY=MA2&Supplier=NOPE"))
    assert _all(empty, "ttPO") == []


def test_get_unbilled_receiving(client):
    root = _xml(client.get(f"{PW}/getUnbilledReceiving.p?COMPANY=MA2"))
    nos = {_text(r, "iReceiving") for r in _all(root, "ttReceiving")}
    assert {"700101", "700102", "700201"} <= nos
    assert client.get(f"{PW}/getUnbilledReceiving.p?COMPANY=XXX").status_code == 404


def test_get_supplier_term(client):
    root = _xml(client.get(f"{PW}/getSupplierTerm.p?COMPANY=MA2&SupplierCode=lumpro"))
    codes = [e.text for e in _all(root, "cCode")]
    assert codes == ["LUMPRO"]
    assert client.get(f"{PW}/getSupplierTerm.p?COMPANY=MA2&SupplierCode=NOPE").status_code == 404


def test_get_gl_accounts_xml_and_json(client):
    root = _xml(client.get(f"{PW}/getGLaccounts.p?COMPANY=MA2"))
    assert _all(root, "ttGL") and _all(root, "ttCC")
    js = client.get(f"{PW}/getGLaccounts.p?COMPANY=MA2&format=json").get_json()
    assert js["gl_accounts"] and "cost_centers" in js


def _dsinput(supplier="TECBUR", number="SKY-1", po="", lines="", **hd):
    extra = "".join(f"<{k}>{v}</{k}>" for k, v in hd.items())
    return f"""<?xml version="1.0"?><dsInput><ttInputHD>
        <cNoFourn>{supplier}</cNoFourn><cNoFacture>{number}</cNoFacture><dDateFacture>2026-10-10</dDateFacture>
        <cNoCommAch>{po}</cNoCommAch>{extra}</ttInputHD>{lines}</dsInput>"""


def _post_invoice(client, svc, body):
    return _xml(client.post(f"{PW}/{svc}", data=body, content_type="application/xml"))


def test_ap_invoice_no_po_creates_erp_invoice(client):
    lines = "<ttInputDT><cCodeProduit>SRV</cCodeProduit><dMontant>100</dMontant><cGL>5960</cGL></ttInputDT>"
    root = _post_invoice(client, "apInvoiceNoPO.p", _dsinput("HORIZN", "H-1", lines=lines, dTotalTPS="5", dTotalTVP="9.98"))
    assert _all(root, "ttInvoice") and not _all(root, "ttError")
    inv = [i for i in client.get("/api/invoices?q=H-1").get_json()["items"] if i["cNoFacture"] == "H-1"][0]
    assert inv["cSource"] == "SkyAI" and inv["cStatut"] == "Posted" and inv["dTotalFacture"] == "114.98"


def test_ap_invoice_with_po_bills_the_reception(client):
    lines = "<ttInputDT><cCodeProduit>LAP-14I7</cCodeProduit><dQteFacturee>4</dQteFacturee><dCoutUnitaire>1250</dCoutUnitaire><iNoReception>700101</iNoReception></ttInputDT>"
    root = _post_invoice(client, "apInvoiceWithPO.p", _dsinput(po="500101", lines=lines, dTotalFacture="5748.75"))
    assert _all(root, "ttInvoice")
    unb = {_text(r, "iReceiving") for r in _all(_xml(client.get(f"{PW}/getUnbilledReceiving.p?COMPANY=MA2")), "ttReceiving")}
    assert "700101" not in unb and "700102" in unb
    inv = client.get("/api/invoices?q=SKY-1").get_json()["items"][0]
    assert inv["dTotalFacture"] == "5748.75"


def test_ap_invoice_incomplete_is_draft(client):
    _post_invoice(client, "apInvoiceNoPO.p", _dsinput(number="SKY-D", lIncomplete="true",
                                                      lines="<ttInputDT><dMontant>1</dMontant></ttInputDT>"))
    assert client.get("/api/invoices?q=SKY-D").get_json()["items"][0]["cStatut"] == "Draft"


def test_ap_invoice_errors(client):
    def err(body, svc="apInvoiceNoPO.p"):
        root = _post_invoice(client, svc, body)
        e = _all(root, "ttError")
        assert e, ET.tostring(root)
        return _text(e[0], "cErreur")

    assert "vide" in err("")
    assert "XML invalide" in err("<dsInput>")
    assert "ttInputHD" in err("<dsInput></dsInput>")
    assert "requis" in err(_dsinput(supplier=""))
    assert err(_dsinput(number="FAIL-1")) == "Facture existante"
    _post_invoice(client, "apInvoiceNoPO.p", _dsinput(number="DUP-1"))
    assert err(_dsinput(number="DUP-1")) == "Facture existante"


def test_simulate_error_flag(client):
    root = _xml(client.post(f"{PW}/apInvoiceNoPO.p?simulate_error=1", data=_dsinput(number="OK-1"), content_type="application/xml"))
    assert _all(root, "ttError")
