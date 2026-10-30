"""Sample internal purchase requisitions ("Demande d'achat") for the SkyAI Offer demo.

Writes samples/requisitions/DA-0101.pdf ... DA-0103.pdf. Email one of them as an attachment
to the SkyAI inbox: SkyAI extracts it, asks the ERP for the best supplier per item, the
account manager approves and one PO is created per supplier.

  DA-0101  aluminium only: everything goes to one supplier (one PO)
  DA-0102  aluminium + fasteners + paper: a close call on the screws (choose) and 3 to 4 POs
  DA-0103  safety items never bought before: no history, the account manager picks the supplier

Usage: python tools/make_requisition_pdfs.py   (needs reportlab)
"""
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

OUT = Path(__file__).resolve().parent.parent / "samples" / "requisitions"
COMPANY = "Les Industries Démo inc. · 1200 boul. Industriel, Laval QC H7L 4R9"

REQUISITIONS = [
    dict(no="DA-0101", date="2026-10-14", required="2026-10-24", requester="Marc Gagnon", email="marc.gagnon@example.com",
         dept="Fabrication", cc="CC-210", address="Usine 1, quai de réception B",
         notes="Commande pour le projet de garde-corps du client Bélanger.",
         items=[("AL6061-F125-48", "Feuille aluminium 6061-T6 1/8 po x 4 x 8 pi", 12, "feuille"),
                ("AL5052-F063-48", "Feuille aluminium 5052-H32 0,063 po x 4 x 8 pi", 8, "feuille"),
                ("AL6061-T200-20", "Tube carré aluminium 6061 2 x 2 x 1/8 po, 20 pi", 15, "longueur")]),
    dict(no="DA-0102", date="2026-10-14", required="2026-10-28", requester="Julie Tremblay", email="julie.tremblay@example.com",
         dept="Production", cc="CC-120", address="Usine 1, quai de réception A",
         notes="Réapprovisionnement mensuel de l'atelier et du bureau.",
         items=[("AL6061-F125-48", "Feuille aluminium 6061-T6 1/8 po x 4 x 8 pi", 10, "feuille"),
                ("AL6063-C1515-20", "Cornière aluminium 6063 1-1/2 x 1-1/2 x 1/8 po, 20 pi", 12, "longueur"),
                ("AL6061-B100-12", "Barre ronde aluminium 6061 1 po x 12 pi", 6, "longueur"),
                ("VIS-INOX-1420", "Vis inox 1/4-20 x 1 po, boîte de 100", 6, "boîte"),
                ("ECR-INOX-14", "Écrous inox 1/4-20, boîte de 100", 6, "boîte"),
                ("PAP-LET-500", "Papier lettre 8,5 x 11 po, 20 lb, caisse de 10 rames", 4, "caisse")]),
    dict(no="DA-0103", date="2026-10-15", required="2026-10-22", requester="Karim Benali", email="karim.benali@example.com",
         dept="Santé et sécurité", cc="CC-900", address="Usine 1, magasin central",
         notes="Équipements de protection pour les nouveaux employés.",
         items=[("", "Gants de travail en nitrile, taille L", 40, "paire"),
                ("", "Lunettes de sécurité anti-buée", 25, "unité")]),
]


def build(r):
    styles = getSampleStyleSheet()
    small = styles["Normal"].clone("small", fontSize=9, leading=11)
    doc = SimpleDocTemplate(str(OUT / f"{r['no']}.pdf"), pagesize=letter, leftMargin=18 * mm, rightMargin=18 * mm,
                            topMargin=16 * mm, bottomMargin=16 * mm, title=f"Demande d'achat {r['no']}")
    head = Table([[Paragraph("<b>DEMANDE D'ACHAT</b><br/><font size=9>Réquisition interne</font>", styles["Title"]),
                   Paragraph(f"<b>No de demande :</b> {r['no']}<br/><b>Date de la demande :</b> {r['date']}<br/>"
                             f"<b>Date requise :</b> {r['required']}", styles["Normal"])]],
                 colWidths=[95 * mm, 80 * mm])
    head.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    info = Table([
        ["Demandeur", r["requester"], "Service", r["dept"]],
        ["Courriel", r["email"], "Centre de coûts", r["cc"]],
        ["Lieu de livraison", r["address"], "", ""],
    ], colWidths=[32 * mm, 62 * mm, 32 * mm, 49 * mm])
    info.setStyle(TableStyle([("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"), ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
                              ("FONTSIZE", (0, 0), (-1, -1), 9), ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                              ("SPAN", (1, 2), (3, 2)), ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),
                              ("BACKGROUND", (2, 0), (2, 1), colors.whitesmoke)]))
    rows = [["Ligne", "Code article", "Description", "Quantité", "Unité"]]
    rows += [[str(i), code or "—", Paragraph(desc, small), str(qty), unit] for i, (code, desc, qty, unit) in enumerate(r["items"], 1)]
    items = Table(rows, colWidths=[13 * mm, 33 * mm, 89 * mm, 20 * mm, 20 * mm], repeatRows=1)
    items.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f4e79")), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                               ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"), ("FONTSIZE", (0, 0), (-1, -1), 9),
                               ("GRID", (0, 0), (-1, -1), 0.4, colors.grey), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                               ("ALIGN", (3, 1), (3, -1), "RIGHT")]))
    sign = Table([["Signature du demandeur", "Approbation du gestionnaire"], [r["requester"], ""]],
                 colWidths=[87 * mm, 88 * mm], rowHeights=[6 * mm, 14 * mm])
    sign.setStyle(TableStyle([("FONTSIZE", (0, 0), (-1, -1), 9), ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                              ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"), ("VALIGN", (0, 1), (-1, 1), "BOTTOM")]))
    doc.build([Paragraph(COMPANY, small), Spacer(1, 4 * mm), head, Spacer(1, 5 * mm), info, Spacer(1, 6 * mm),
               Paragraph("<b>Articles demandés</b>", styles["Normal"]), Spacer(1, 2 * mm), items, Spacer(1, 6 * mm),
               Paragraph(f"<b>Justification :</b> {r['notes']}", styles["Normal"]), Spacer(1, 10 * mm), sign])


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for r in REQUISITIONS:
        build(r)
        print(OUT / f"{r['no']}.pdf")


if __name__ == "__main__":
    main()
