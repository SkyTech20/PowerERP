"""Purchase history for the supplier-selection demo (SkyAI Offer / internal requisitions).

Writes data/demo/history.json: extra suppliers plus 12 months of closed purchase orders,
their receptions and their invoices, with suppliers selling the same items
(aluminium, fasteners, office paper). SkyAI builds its demo purchase history from this file. Everything is already received and invoiced, so it
never shows up in the unbilled lists used by the invoice scenarios.

Usage: python tools/make_history_data.py   (deterministic: same output every run)
"""
import json
import random
from datetime import date, timedelta
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "data" / "demo" / "history.json"
rnd = random.Random(2026)
m = lambda v: f"{v:.2f}"
tps = lambda s: round(s * 0.05 + 1e-9, 2)
tvq = lambda s: round(s * 0.09975 + 1e-9, 2)

BASE = {"cTermCode": "n30", "cTermDesc": "net 30 jours", "cAddress2": "", "cCountry": "CA", "cProvince": "qc",
        "cDeptSauv": "", "iStatutAch": 1, "cCodeAch": "Cassiano", "cDescAch": "Cassiano", "iTypePO": 1}
NEW_SUPPLIERS = [
    ("ALUQC", "Aluminium Québec inc.", "3500 boul. Industriel", "Laval", "H7L 4S3", "811223344RT0001", "1221122334TQ0001"),
    ("METALX", "Métal Express inc.", "780 rue Bergar", "Laval", "H7L 5A1", "822334455RT0001", "1222233445TQ0001"),
    ("ALCOR", "Alu-Cor Distribution inc.", "12 rue du Parc-Industriel", "Saint-Hyacinthe", "J2R 1C7", "833445566RT0001", "1223344556TQ0001"),
    ("VISNOR", "Visserie Nordique inc.", "1450 boul. Saint-Elzéar Ouest", "Laval", "H7L 3N7", "844556677RT0001", "1224455667TQ0001"),
    ("FIXPRO", "Fixations Pro inc.", "2200 rue Michelin", "Laval", "H7L 5B7", "855667788RT0001", "1225566778TQ0001"),
    ("BUREXP", "Bureau Express inc.", "9100 boul. Pie-IX", "Montréal", "H1Z 3T8", "866778899RT0001", "1226677889TQ0001"),
]

# Catalogue: code, description, base unit price
PRODUCTS = {
    "AL6061-F125-48": ("Feuille aluminium 6061-T6 1/8 po x 4 x 8 pi", 182.00),
    "AL5052-F063-48": ("Feuille aluminium 5052-H32 0,063 po x 4 x 8 pi", 118.00),
    "AL6061-B100-12": ("Barre ronde aluminium 6061 1 po x 12 pi", 64.00),
    "AL6063-C1515-20": ("Cornière aluminium 6063 1-1/2 x 1-1/2 x 1/8 po, 20 pi", 41.50),
    "AL6061-T200-20": ("Tube carré aluminium 6061 2 x 2 x 1/8 po, 20 pi", 96.00),
    "VIS-INOX-1420": ("Vis inox 1/4-20 x 1 po, boîte de 100", 28.40),
    "ECR-INOX-14": ("Écrous inox 1/4-20, boîte de 100", 16.90),
    "RIV-ALU-316": ("Rivets aveugles aluminium 3/16 po, boîte de 250", 22.75),
    "PAP-LET-500": ("Papier lettre 8,5 x 11 po, 20 lb, caisse de 10 rames", 52.00),
}

# Supplier profiles: items sold, price factor, promised days, actual delay (mean, spread),
# share of deliveries short, number of orders in 12 months.
PROFILES = {
    # Good price, reliable: should win aluminium.
    "ALUQC": dict(items=["AL6061-F125-48", "AL5052-F063-48", "AL6061-B100-12", "AL6063-C1515-20", "AL6061-T200-20"],
                  price=1.00, promised=7, lead=(5, 1), short=0.03, orders=11),
    # Fast but more expensive.
    "METALX": dict(items=["AL6061-F125-48", "AL5052-F063-48", "AL6061-B100-12", "AL6061-T200-20"],
                   price=1.12, promised=5, lead=(3, 1), short=0.05, orders=8),
    # Cheapest but late and often short.
    "ALCOR": dict(items=["AL6061-F125-48", "AL6063-C1515-20", "AL6061-T200-20"],
                  price=0.95, promised=7, lead=(12, 4), short=0.35, orders=7),
    # Two fastener suppliers that end up very close (the "tie" shown in the SkyAI list).
    "VISNOR": dict(items=["VIS-INOX-1420", "ECR-INOX-14", "RIV-ALU-316"],
                   price=1.00, promised=5, lead=(4, 1), short=0.05, orders=9),
    "FIXPRO": dict(items=["VIS-INOX-1420", "ECR-INOX-14", "RIV-ALU-316"],
                   price=0.97, promised=5, lead=(5, 1), short=0.08, orders=9),
    # Office paper: existing PAPCEN vs a new competitor.
    "PAPCEN": dict(items=["PAP-LET-500"], price=1.00, promised=3, lead=(2, 1), short=0.0, orders=8),
    "BUREXP": dict(items=["PAP-LET-500"], price=1.06, promised=3, lead=(4, 2), short=0.10, orders=5),
}
NAMES = {c: n for c, n, *_ in NEW_SUPPLIERS}
NAMES["PAPCEN"] = "Papeterie Centrale inc."
INV_PREFIX = {"ALUQC": "AQ", "METALX": "MX", "ALCOR": "AC", "VISNOR": "VN", "FIXPRO": "FP", "PAPCEN": "PC", "BUREXP": "BE"}

START, END = date(2025, 10, 1), date(2026, 9, 30)


def main():
    suppliers = [dict(BASE, cCode=c, cName=n, cAddress1=a, cCity=ci, cZipCode=z, cNoTPS=g, cNoTVQ=q)
                 for c, n, a, ci, z, g, q in NEW_SUPPLIERS]
    po_details, receptions, invoices = [], [], []
    po_no, rec_no, inv_no = 400001, 600001, 10001
    span = (END - START).days

    for sup, prof in PROFILES.items():
        n = prof["orders"]
        for k in range(n):
            order = START + timedelta(days=int(span * (k + rnd.random() * 0.8) / n))
            items = rnd.sample(prof["items"], k=min(len(prof["items"]), rnd.randint(1, 3)))
            lines = []
            for i, code in enumerate(items, 1):
                desc, base = PRODUCTS[code]
                drift = 1 + 0.04 * (order - START).days / span  # prices go up ~4 % over the year
                unit = round(base * prof["price"] * drift * rnd.uniform(0.98, 1.02), 2)
                qty = rnd.choice([5, 8, 10, 12, 15, 20, 25]) if code.startswith("AL") else rnd.choice([4, 6, 10, 12, 20])
                lines.append((str(i), code, desc, qty, unit))
            sub = round(sum(q * p for *_, q, p in lines), 2)
            g, t = tps(sub), tvq(sub)
            due = order + timedelta(days=prof["promised"])
            cpo = str(po_no); po_no += 1
            po_details.append({"COMPANY": "MA2", "cPO": cpo, "ttPOheader": {
                "cSupplierCode": sup, "cSupplierName": NAMES[sup], "cBuyerCode": "Cassiano", "cBuyerName": "Cassiano",
                "cApplicantCode": "Cassiano", "dOrderDate": order.isoformat(), "dDueDate": due.isoformat(),
                "dSubTotal": m(sub), "dFreight": "0.00", "dGST": m(g), "dPST": m(t), "dTotalAmount": m(sub + g + t)},
                "ttPOdetail": [{"cUnique": u, "cProductcode": c, "cProductDesc": d, "dQuantity": str(q), "dUnitCost": m(p),
                                "dSubTotal": m(q * p), "dTotalAmount": m(q * p)} for u, c, d, q, p in lines]})

            mean, spread = prof["lead"]
            received = order + timedelta(days=max(1, round(rnd.gauss(mean, spread))))
            arts = []
            for _, c, d, q, p in lines:
                got = q if rnd.random() >= prof["short"] else max(1, int(q * rnd.uniform(0.6, 0.9)))
                arts.append({"CodeArticle": c, "Description": d, "QuantiteCommandee": str(q), "QuantiteRecue": str(got),
                             "PrixUnitaire": m(p), "Devise": "CAD"})
            rs = round(sum(int(a["QuantiteRecue"]) * float(a["PrixUnitaire"]) for a in arts), 2)
            rg, rt = tps(rs), tvq(rs)
            rno = str(rec_no); rec_no += 1
            receptions.append({"NoReception": rno, "COMPANY": "MA2", "DateReception": received.isoformat(),
                               "Fournisseur": NAMES[sup], "CodeFournisseur": sup, "NoBonCommande": cpo, "Statut": "Reçu",
                               "Entrepot": "ENT-01", "Articles": arts, "MontantTotal": m(rs + rg + rt),
                               "ResponsableReception": "Cassiano",
                               "Commentaires": "Livraison partielle" if any(a["QuantiteRecue"] != a["QuantiteCommandee"] for a in arts) else "",
                               "SousTotal": m(rs), "Transport": "0.00", "TPS": m(rg), "TVQ": m(rt)})

            invoices.append({"cNoFourn": sup, "cNoFacture": f"{INV_PREFIX[sup]}-{inv_no}",
                             "dDateFacture": (received + timedelta(days=1)).isoformat(), "cNoCommAch": cpo, "cDevise": "CAD",
                             "cStatut": "Posted", "cSource": "ERP", "dTransport": "0.00", "dTotalTPS": m(rg), "dTotalTVP": m(rt),
                             "lines": [{"cCodeProduit": a["CodeArticle"], "cDescription": a["Description"],
                                        "dQuantite": a["QuantiteRecue"], "dCoutUnitaire": a["PrixUnitaire"],
                                        "cGL": "", "cCC1": "", "cCC2": "", "iNoReception": rno} for a in arts]})
            inv_no += 1

    OUT.write_text(json.dumps({"suppliers": suppliers, "po_details": po_details, "receiving_details": receptions,
                               "invoices": invoices}, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"{OUT}: {len(suppliers)} suppliers, {len(po_details)} POs, {len(receptions)} receptions, {len(invoices)} invoices")


if __name__ == "__main__":
    main()
