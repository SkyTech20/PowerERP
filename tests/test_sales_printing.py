"""Sales API (V5): the invoice printed in its language (FR / EN), with the tax numbers and the lots."""

from powererp.modules.sales.printing import decimal, due_date, money


def invoice(client, customer="HOTEL-LAURIER", lines=None, post=False, **over):
    body = {
        "cCustomer": customer,
        "dDate": "2026-11-23",
        "lines": lines or [{"cProduct": "TUBE-T8", "dQty": "10"}],
        **over,
    }
    no = client.post("/api/sales-invoices", json=body).get_json()["iNo"]
    if post:
        assert client.post(f"/api/sales-invoices/{no}/post").status_code == 200
    return no


def page(client, no, lang=""):
    r = client.get(f"/api/sales-invoices/{no}/print" + (f"?lang={lang}" if lang else ""))
    assert r.status_code == 200 and r.mimetype == "text/html"
    return r.get_data(as_text=True)


def test_a_posted_invoice_in_french(client):
    no = invoice(client, lines=[{"cProduct": "TUBE-T8", "dQty": "10"}, {"cProduct": "EXT-5LB", "dQty": "1"}], post=True)
    html = page(client, no)
    assert '<html lang="fr">' in html and "BROUILLON" not in html
    assert "No de facture" in html and "<b>1</b>" in html
    assert "123456789 RT0001" in html and "1234567890 TQ0001" in html and "NEQ 1170000001" in html
    assert "Échéance</td><td>2026-12-23" in html  # net 30 jours
    assert "Hôtel Laurier" in html and "Tube DEL" in html
    assert "152,78 $" in html and "Lot L2026-09 (exp. 2032-09-30) × 1" in html
    assert "Merci de votre confiance" in html


def test_english_and_a_draft(client):
    no = invoice(
        client, customer="MAPLE-FOODS", lines=[{"cProduct": "DOCK-USBC", "dQty": "1"}], cCustomerPO="PO-77 <b>"
    )
    html = page(client, no)
    assert '<html lang="en">' in html and "DRAFT" in html and "Draft no." in html
    assert "$239.04" in html and "Thank you for your business" in html
    assert "PO-77 &lt;b&gt;" in html  # escaped
    assert "Facture" in page(client, no, "fr")
    assert client.get("/api/sales-invoices/999/print").status_code == 404


def test_formats():
    assert money("1234.5", "fr") == "1 234,50 $" and money("-3", "en") == "-$3.00"
    assert decimal("2.500", "fr") == "2,5" and decimal("15.2775", "en", 2) == "15.28"
    assert due_date("n45", "2026-11-23") == "2027-01-07" and due_date("cod", "2026-11-23") == ""
