"""Sample invoices for client demonstrations: 4 with a purchase order and 4 without, that SkyAI processes
without rejection on the demo dataset (ERP_DATASET=demo).

  1. adds to data/demo/ what the invoices need: POs 450101-450401 with their full receptions 750101-750401
     (TECBUR, LUMPRO, PAPCEN, SECNOR) and 3 suppliers without PO (TELBOR, ECLAT, LOGNUA; HORIZN exists)
  2. writes the PDFs in samples/invoices/

The PO numbers stay below 500501, where the POs created by SkyAI requisitions start (apCreatePO.p).
Each invoice can be processed once: after a run, use Dashboard > Reset demo data in the ERP and delete the
workflow in SkyAI (or the invoice is rejected as a duplicate).

Usage: python tools/make_sample_invoices.py   (needs reportlab; same output every run)
"""
import json
from pathlib import Path

from reportlab.lib.colors import HexColor, black, white
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "demo"
OUT = ROOT / "samples" / "invoices"
W, H = letter
BILL = ["Les Industries Démo inc.", "Comptes fournisseurs", "850 rue Sherbrooke Ouest", "Montréal (Québec) H3A 1G1", "Canada"]


def m(v):
    return f"{v:.2f}"


def tps(s):
    return round(s * 0.05 + 1e-9, 2)


def tvq(s):
    return round(s * 0.09975 + 1e-9, 2)


def money(v):  # Québec format: 1 250,00 $
    return f"{v:,.2f}".replace(",", " ").replace(".", ",") + " $"


# ---------------------------------------------------------------- suppliers
SUP = {
    "TECBUR": dict(name="Techno Bureau Plus inc.", addr="4200 boul. Saint-Laurent, bureau 300", city="Montréal", zip="H2W 1Z3",
                   tel="514 555-0142", gst="812345678RT0001", qst="1223456789TQ0001", dom="technobureauplus", transit="00123", acct="4567890"),
    "LUMPRO": dict(name="Lumière Pro Électrique inc.", addr="2750 rue Jean-Talon Est", city="Montréal", zip="H2A 1V1",
                   tel="514 555-0175", gst="834567129RT0001", qst="1225678901TQ0001", dom="lumierepro", transit="00211", acct="3344556"),
    "PAPCEN": dict(name="Papeterie Centrale inc.", addr="455 boul. Saint-Joseph", city="Gatineau", zip="J8Y 3Y7",
                   tel="819 555-0123", gst="856781234RT0001", qst="1227890123TQ0001", dom="papeteriecentrale", transit="00345", acct="7788990"),
    "SECNOR": dict(name="Sécurité Nordique inc.", addr="2600 boul. Laurier, bureau 120", city="Québec", zip="G1V 4T3",
                   tel="418 555-0164", gst="878912345RT0001", qst="1229012345TQ0001", dom="securitenordique", transit="00567", acct="2233445"),
    "HORIZN": dict(name="Services Conseil Horizon inc.", addr="1500 boul. Le Corbusier, bureau 210", city="Laval", zip="H7S 2K1",
                   tel="450 555-0187", gst="845612397RT0001", qst="1229876543TQ0001", dom="horizonconseil", transit="00456", acct="9876543"),
    "TELBOR": dict(name="Télécom Boréal inc.", addr="1000 rue De La Gauchetière Ouest, bureau 2400", city="Montréal", zip="H3B 4W5",
                   tel="514 555-0190", gst="867123459RT0001", qst="1230456789TQ0001", dom="telecomboreal", transit="00678", acct="5566778"),
    "ECLAT": dict(name="Entretien Ménager Éclat inc.", addr="3450 boul. Industriel", city="Laval", zip="H7L 4R9",
                  tel="450 555-0133", gst="889234561RT0001", qst="1231567890TQ0001", dom="eclatentretien", transit="00789", acct="6677889"),
    "LOGNUA": dict(name="LogiNuage inc.", addr="400 boul. Jean-Lesage, bureau 500", city="Québec", zip="G1K 8W1",
                   tel="418 555-0119", gst="890345672RT0001", qst="1232678901TQ0001", dom="loginuage", transit="00891", acct="7788001"),
}
NEW_SUPPLIERS = ["TELBOR", "ECLAT", "LOGNUA"]  # without PO (iTypePO 2), like HORIZN

# ---------------------------------------------------------------- invoices
# (file, supplier, color, invoice no, date, due, PO or None, PO date, reception no, reception date, lines, notes)
# lines: (code, description, quantity, unit price)
WITH_PO = [
    ("Facture_A1_TECBUR_TB-24601_BC450101.pdf", "TECBUR", "#1f4e8c", "TB-24601", "2026-10-09", "2026-11-08",
     "450101", "2026-10-01", "750101", "2026-10-07",
     [("MON-27Q", "Moniteur 27 po QHD", 6, 329.00), ("CLAV-SF", "Ensemble clavier et souris sans fil", 6, 59.00)],
     ["Marchandise livrée le 2026-10-07 (réception 750101).", "Garantie du fabricant de 3 ans sur les moniteurs."]),
    ("Facture_A2_LUMPRO_LP-88402_BC450201.pdf", "LUMPRO", "#b45309", "LP-88402", "2026-10-10", "2026-11-09",
     "450201", "2026-10-02", "750201", "2026-10-08",
     [("TUBE-T8", "Tube DEL T8 4 pi, 18 W", 48, 12.50), ("DET-MOUV", "Détecteur de mouvement plafonnier", 8, 64.00)],
     ["Marchandise livrée le 2026-10-08 (réception 750201).", "Garantie de 5 ans sur les tubes DEL."]),
    ("Facture_A3_PAPCEN_PC-20588_BC450301.pdf", "PAPCEN", "#7c3aed", "PC-20588", "2026-10-13", "2026-11-12",
     "450301", "2026-10-05", "750301", "2026-10-09",
     [("ENV-10", "Enveloppes no 10 (boîte de 500)", 10, 32.75), ("CRAY-HB", "Crayons HB (boîte de 12)", 15, 6.40)],
     ["Livraison effectuée le 2026-10-09 (réception 750301).", "Merci de votre confiance."]),
    ("Facture_A4_SECNOR_SN-7810_BC450401.pdf", "SECNOR", "#be123c", "SN-7810", "2026-10-14", "2026-11-13",
     "450401", "2026-10-06", "750401", "2026-10-10",
     [("EXT-5LB", "Extincteur ABC 5 lb", 10, 74.00), ("INSP-EXT", "Inspection annuelle des extincteurs", 1, 250.00)],
     ["Extincteurs livrés et inspectés le 2026-10-10 (réception 750401).", "Certificat d'inspection joint à la livraison."]),
]
WITHOUT_PO = [
    ("Facture_B1_HORIZN_H-2026-1077_sans_BC.pdf", "HORIZN", "#0f766e", "H-2026-1077", "2026-10-12", "2026-11-11",
     [("CONS-TI", "Services-conseils TI - octobre 2026 (16 h)", 16, 125.00), ("SOUT-MOIS", "Forfait de soutien mensuel - novembre 2026", 1, 450.00)],
     ["Mandat réalisé pour le service des TI (mise à jour des postes de travail).", "Feuille de temps détaillée disponible sur demande."]),
    ("Facture_B2_TELBOR_TLB-0045821_sans_BC.pdf", "TELBOR", "#0e7490", "TLB-0045821", "2026-10-01", "2026-10-31",
     [("INT-1G", "Service Internet fibre 1 Gbit/s - octobre 2026", 1, 189.95), ("TEL-IP", "Ligne téléphonique IP - octobre 2026", 10, 24.95)],
     ["Période de service : 2026-10-01 au 2026-10-31.", "Compte client 800-551-2290."]),
    ("Facture_B3_ECLAT_EME-3318_sans_BC.pdf", "ECLAT", "#15803d", "EME-3318", "2026-10-15", "2026-11-14",
     [("ENT-MEN", "Entretien ménager des bureaux - octobre 2026", 1, 1850.00), ("VITRES", "Nettoyage des vitres extérieures", 1, 420.00)],
     ["Contrat d'entretien mensuel, 850 rue Sherbrooke Ouest.", "Nettoyage des vitres effectué le 2026-10-11."]),
    ("Facture_B4_LOGNUA_LN-2026-0917_sans_BC.pdf", "LOGNUA", "#4338ca", "LN-2026-0917", "2026-10-03", "2026-11-02",
     [("SUITE-BUR", "Abonnement suite bureautique - octobre 2026 (par utilisateur)", 25, 16.50), ("STOCK-1TO", "Stockage infonuagique supplémentaire 1 To", 2, 12.00)],
     ["Abonnement mensuel, renouvellement automatique.", "Période : 2026-10-01 au 2026-10-31."]),
]


# ---------------------------------------------------------------- ERP data
def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def save(name, data):
    (DATA / name).write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8", newline="")


def add_erp_data():
    sups = load("suppliers.json")
    base = {k: v for k, v in sups[0].items() if k in ("cTermCode", "cTermDesc", "cAddress2", "cCountry", "cProvince", "cDeptSauv", "iStatutAch")}
    sups = [s for s in sups if s["cCode"] not in NEW_SUPPLIERS]
    for code in NEW_SUPPLIERS:
        s = SUP[code]
        sups.append(dict(base, cCode=code, cName=s["name"], cAddress1=s["addr"], cCity=s["city"], cZipCode=s["zip"],
                         cNoTPS=s["gst"], cNoTVQ=s["qst"], cCodeAch="", cDescAch="Cassiano", iTypePO=2))
    save("suppliers.json", sups)

    pos, recs = load("purchase_orders.json"), load("receptions.json")
    ours = {inv[6] for inv in WITH_PO}
    ours_rec = {inv[8] for inv in WITH_PO}
    pos["po_details"] = [p for p in pos["po_details"] if p["cPO"] not in ours]
    pos["unbilled_po"] = [p for p in pos["unbilled_po"] if p["cPO"] not in ours]
    recs["receiving_details"] = [r for r in recs["receiving_details"] if r["NoReception"] not in ours_rec]
    recs["unbilled_receiving"] = [r for r in recs["unbilled_receiving"] if r["NoReception"] not in ours_rec]
    for _, code, _, _, _, _, po, po_date, rec, rec_date, lines, _ in WITH_PO:
        name = SUP[code]["name"]
        sub = round(sum(q * p for _, _, q, p in lines), 2)
        g, t = tps(sub), tvq(sub)
        pos["po_details"].append({"COMPANY": "MA2", "cPO": po, "ttPOheader": {
            "cSupplierCode": code, "cSupplierName": name, "cBuyerCode": "Cassiano", "cBuyerName": "Cassiano",
            "cApplicantCode": "Cassiano", "dOrderDate": po_date, "dSubTotal": m(sub), "dFreight": "0.00",
            "dGST": m(g), "dPST": m(t), "dTotalAmount": m(sub + g + t)},
            "ttPOdetail": [{"cUnique": str(i + 1), "cProductcode": c, "cProductDesc": d, "dQuantity": f"{q:g}",
                            "dUnitCost": m(p), "dSubTotal": m(q * p), "dTotalAmount": m(q * p)}
                           for i, (c, d, q, p) in enumerate(lines)]})
        pos["unbilled_po"].append({"COMPANY": "MA2", "cPO": po, "dCreationDate": po_date, "cSupplierName": name, "cSupplierCode": code})
        recs["receiving_details"].append({
            "NoReception": rec, "COMPANY": "MA2", "DateReception": rec_date, "Fournisseur": name, "CodeFournisseur": code,
            "NoBonCommande": po, "Statut": "Reçu", "Entrepot": "ENT-01",
            "Articles": [{"CodeArticle": c, "Description": d, "QuantiteCommandee": f"{q:g}", "QuantiteRecue": f"{q:g}",
                          "PrixUnitaire": m(p), "Devise": "CAD"} for c, d, q, p in lines],
            "MontantTotal": m(sub + g + t), "ResponsableReception": "Cassiano", "Commentaires": "",
            "SousTotal": m(sub), "Transport": "0.00", "TPS": m(g), "TVQ": m(t)})
        recs["unbilled_receiving"].append({
            "COMPANY": "MA2", "NoReception": rec, "DateReception": rec_date, "NoBonCommande": po, "Fournisseur": name,
            "CodeFournisseur": code, "MontantRecu": m(sub + g + t), "StatutFacturation": "En attente de facture",
            "JoursEnAttente": "0", "ResponsableFacturation": "Comptabilité", "PrioriteFacturation": "Normale",
            "Devise": "CAD", "Entrepot": "ENT-01", "TypeReception": "Standard"})
    save("purchase_orders.json", pos)
    save("receptions.json", recs)


# ---------------------------------------------------------------- PDF (same layout as demo-invoices/)
def invoice(fn, code, color, number, date, due, po, lines, note):
    s = SUP[code]
    c = canvas.Canvas(str(OUT / fn), pagesize=letter, invariant=1)
    c.setTitle(f"Facture {number} - {s['name']}")
    c.setAuthor(s["name"])
    acc = HexColor(color)
    c.setFillColor(acc); c.rect(0, H - 110, W, 110, fill=1, stroke=0)
    c.setFillColor(white); c.setFont("Helvetica-Bold", 19); c.drawString(40, H - 50, s["name"])
    c.setFont("Helvetica", 9.5)
    for i, t in enumerate([s["addr"], f"{s['city']} (Québec) {s['zip']}", f"Tél. {s['tel']}"]):
        c.drawString(40, H - 68 - i * 12, t)
    c.setFont("Helvetica-Bold", 22); c.drawRightString(W - 40, H - 50, "FACTURE")
    c.setFont("Helvetica", 9.5)
    c.drawRightString(W - 40, H - 70, f"No TPS : {s['gst']}")
    c.drawRightString(W - 40, H - 82, f"No TVQ : {s['qst']}")
    c.drawRightString(W - 40, H - 94, f"ventes@{s['dom']}.example")
    y = H - 150
    c.setFillColor(acc); c.setFont("Helvetica-Bold", 10); c.drawString(40, y, "FACTURER À")
    c.setFillColor(black); c.setFont("Helvetica", 10)
    for i, t in enumerate(BILL):
        c.drawString(40, y - 16 - i * 13, t)
    meta = [("No de facture", number), ("Date de facture", date), ("Échéance", due),
            ("Conditions", "Net 30 jours"), ("No de client", "MA2-0042")]
    if po:
        meta.insert(1, ("Bon de commande", po))
    for i, (k, v) in enumerate(meta):
        yy = y - i * 17
        c.setFont("Helvetica", 9); c.setFillColor(HexColor("#555555")); c.drawString(330, yy, k)
        c.setFont("Helvetica-Bold", 10); c.setFillColor(black); c.drawRightString(W - 40, yy, v)
    y = H - 285
    cols = [40, 120, 375, 465]
    c.setFillColor(acc); c.rect(40, y - 6, W - 80, 22, fill=1, stroke=0)
    c.setFillColor(white); c.setFont("Helvetica-Bold", 9.5)
    c.drawString(46, y, "Article"); c.drawString(cols[1] + 6, y, "Description")
    c.drawRightString(cols[2] - 10, y, "Qté"); c.drawRightString(cols[3] - 10, y, "Prix unitaire"); c.drawRightString(W - 46, y, "Montant")
    c.setFillColor(black)
    y -= 26
    sub = 0
    for i, (lc, desc, qty, unit) in enumerate(lines):
        amt = round(qty * unit, 2)
        sub += amt
        if i % 2:
            c.setFillColor(HexColor("#f3f5f8")); c.rect(40, y - 7, W - 80, 22, fill=1, stroke=0); c.setFillColor(black)
        c.setFont("Helvetica", 10); c.drawString(46, y, lc)
        c.setFont("Helvetica", 9.5 if len(desc) < 44 else 8.5); c.drawString(cols[1] + 6, y, desc)
        c.setFont("Helvetica", 10)
        c.drawRightString(cols[2] - 10, y, f"{qty:g}"); c.drawRightString(cols[3] - 10, y, money(unit)); c.drawRightString(W - 46, y, money(amt))
        y -= 22
    c.setStrokeColor(HexColor("#cccccc")); c.line(40, y + 8, W - 40, y + 8)
    sub = round(sub, 2)
    gst, qst = tps(sub), tvq(sub)
    total = round(sub + gst + qst, 2)
    y -= 14
    for k, v in [("Sous-total", sub), ("TPS 5 %", gst), ("TVQ 9,975 %", qst)]:
        c.setFont("Helvetica", 10); c.drawString(360, y, k); c.drawRightString(W - 46, y, money(v)); y -= 17
    y -= 8
    c.setFillColor(acc); c.rect(350, y - 9, W - 390, 26, fill=1, stroke=0)
    c.setFillColor(white); c.setFont("Helvetica-Bold", 12); c.drawString(360, y, "TOTAL (CAD)"); c.drawRightString(W - 46, y, money(total))
    c.setFillColor(black)
    y -= 60
    c.setFont("Helvetica-Bold", 10); c.setFillColor(acc); c.drawString(40, y, "REMARQUES"); c.setFillColor(black)
    c.setFont("Helvetica", 9.5)
    for i, t in enumerate(note):
        c.drawString(40, y - 15 - i * 13, t)
    y -= 15 + len(note) * 13 + 20
    c.setFont("Helvetica-Bold", 10); c.setFillColor(acc); c.drawString(40, y, "PAIEMENT"); c.setFillColor(black)
    c.setFont("Helvetica", 9.5)
    pay = [f"Veuillez indiquer le numéro de facture {number} avec votre paiement.",
           f"Virement bancaire : Banque Exemple, transit {s['transit']}, compte {s['acct']}",
           f"Avis de paiement : comptes@{s['dom']}.example"]
    for i, t in enumerate(pay):
        c.drawString(40, y - 15 - i * 13, t)
    c.setFont("Helvetica-Oblique", 8); c.setFillColor(HexColor("#888888"))
    c.drawCentredString(W / 2, 30, "Document d'exemple à des fins de démonstration seulement - entreprise et données fictives.")
    c.showPage()
    c.save()
    return total


if __name__ == "__main__":
    add_erp_data()
    OUT.mkdir(parents=True, exist_ok=True)
    for fn, code, color, number, date, due, po, _, _, _, lines, note in WITH_PO:
        print(fn, money(invoice(fn, code, color, number, date, due, po, lines, note)))
    for fn, code, color, number, date, due, lines, note in WITHOUT_PO:
        print(fn, money(invoice(fn, code, color, number, date, due, None, lines, note)))
