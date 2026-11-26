"""Demo data of the maple products company (Administration > System settings > Maple products, the default scenario).

Érablière Démo inc. (Saint-Georges, Beauce) buys pure maple syrup in barrels from three sugar bushes, standardizes
it (filtered, Brix checked) and makes five products: syrup in cans (amber) and in glass bottles (dark), maple butter,
maple candy and maple fudge (with cream and butter: milk allergen). Each barrel is a lot: its supplier lot is the
producer's barrel number and its harvest, so that a can sold is traced back to the sugar bush it came from.

Two parts, both written to data/maple/:
1. The master data and the purchases (written here, like any reference data):
    inventory.json        categories, plant, locations, products, stock parameters, the stock received
    production.json       calendar, work centers, machines, standard operations, manufacturing data, recipes and steps
    suppliers.json        the suppliers (three sugar bushes, a dairy, packaging, equipment)
    purchase_orders.json  the purchase orders (one still open)
    receptions.json       the receptions (in the stock: their lines carry the location, the lot, the supplier's
                          lot and the expiry; one barrel received short)
    invoices.json         the supplier invoices (posted)
    sales.json            the company profile, the price lists and the customers
2. The story (story.json): October and November 2026 played through the ERP itself (the same API as the screens,
   at the dates of the story), so that every rule applies: production orders (released, issued by lot, the recipe
   steps recorded, reported, completed and closed; one cooked too hot, its lot held), sales invoices (posted, a
   credit note, drafts), nonconformances (a barrel tasting of "bourgeon" returned to the sugar bush, the candy
   cooked too hot, a customer complaint). The ERP tables it changed are kept as they are after the story: products
   (their average cost), stock movements, production orders, lot status, nonconformances, sales invoices. They
   replace the seed of those tables (DemoData.story), so the demo opens with history for the traceability and the
   supply chain indicators.

Usage (from the PowerERP folder, a PostgreSQL database that may be emptied, its name containing "scratch" or "test"):
    pip install time-machine     (the story runs at its own dates)
    MAPLE_DATABASE_URL=postgresql+psycopg://powererp:powererp@127.0.0.1:5432/powererp_scratch \
        python tools/make_maple_data.py
Same output every run.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from powererp import schemas as S  # noqa: E402

OUT = ROOT / "data" / "maple"
WH = "PLANT"
BUYER = "Cassiano"
STORY_KEYS = ("inv_products", "inv_movements", "prod_orders", "qa_lot_status", "qa_nonconformances", "sales_invoices")


def money(v: float) -> str:
    return f"{v:.2f}"


def num(v: float) -> str:
    return f"{v:g}"


def full(schema: dict, row: dict) -> dict:
    """Every field of the schema, with the defaults of an empty form, then the values given."""
    out = {}
    for f, kind in schema.items():
        if isinstance(kind, tuple):
            out[f] = kind[0]
        elif kind == "i":
            out[f] = 0
        elif kind == "b":
            out[f] = False
        else:
            out[f] = ""
    out.update(row)
    return out


# ------------------------------------------------------------------ item master

CATEGORIES = [
    ("RAW", "Matières premières", "Raw materials", ""),
    ("RAW-SYRUP", "Sirop d'érable en vrac", "Bulk maple syrup", "RAW"),
    ("RAW-DAIRY", "Produits laitiers", "Dairy products", "RAW"),
    ("PACK", "Emballages", "Packaging", ""),
    ("WIP", "Produits semi-finis", "Semi-finished products", ""),
    ("MAPLE", "Produits de l'érable", "Maple products", ""),
    ("SUPPLIES", "Fournitures", "Supplies", ""),
    ("EQUIP", "Équipement", "Equipment", ""),
]

# a location holds one lot of a product: each barrel has its place, each lot made goes to a free place
LOCATIONS = (
    [("REC", "REC", "Quai de réception", "receiving")]
    + [(f"BAR-{i:02}", "BARILS", f"Baril, rangée {(i + 3) // 4}", "picking") for i in range(1, 13)]
    + [(f"TANK-{i:02}", "CUVES", f"Cuve de sirop standardisé {i}", "staging") for i in (1, 2)]
    + [(f"COLD-{i:02}", "FROID", f"Chambre froide (0 à 4 °C), tablette {i}", "picking") for i in range(1, 5)]
    + [
        ("PACK-01", "SEC", "Emballages et fournitures", "reserve"),
        ("PROD-01", "PROD", "Salle de production", "staging"),
    ]
    + [(f"FG-{i:02}", "PF", f"Produits finis, palette {i}", "shipping") for i in range(1, 13)]
)

# code: FR, EN, category, unit, location, purchase price, supplier, shelf life (days, 0 = no lot)
BOUGHT = {
    "SYRUP-BULK-AMB": (
        "Sirop d'érable en vrac, ambré (baril)",
        "Bulk maple syrup, amber (barrel)",
        "RAW-SYRUP",
        "KG",
        "",
        7.40,
        "GAGNON",
        730,
    ),
    "SYRUP-BULK-DRK": (
        "Sirop d'érable en vrac, foncé (baril)",
        "Bulk maple syrup, dark (barrel)",
        "RAW-SYRUP",
        "KG",
        "",
        6.90,
        "CANTONS",
        730,
    ),
    "CREAM-35": ("Crème 35 %", "Cream 35%", "RAW-DAIRY", "L", "", 6.20, "LAITERIE", 21),
    "BUTTER": ("Beurre non salé", "Unsalted butter", "RAW-DAIRY", "KG", "", 11.50, "LAITERIE", 60),
    "CAN-540": ("Canne de métal 540 ml", "Metal can, 540 ml", "PACK", "UN", "PACK-01", 0.62, "BOREAL", 0),
    "BOTTLE-250": ("Bouteille de verre 250 ml", "Glass bottle, 250 ml", "PACK", "UN", "PACK-01", 0.85, "BOREAL", 0),
    "CAP-28": ("Bouchon 28 mm", "Cap, 28 mm", "PACK", "UN", "PACK-01", 0.06, "BOREAL", 0),
    "JAR-200": ("Pot de verre 200 g", "Glass jar, 200 g", "PACK", "UN", "PACK-01", 0.48, "BOREAL", 0),
    "BOX-12": ("Boîte de 12 bonbons", "Box for 12 candies", "PACK", "UN", "PACK-01", 0.35, "BOREAL", 0),
    "TRAY-250": ("Barquette 250 g", "Tray, 250 g", "PACK", "UN", "PACK-01", 0.30, "BOREAL", 0),
    "LABEL": ("Étiquette imprimée", "Printed label", "PACK", "UN", "PACK-01", 0.04, "BOREAL", 0),
}
WIP = {"SYRUP-STD": ("Sirop d'érable standardisé (filtré)", "Standardized maple syrup (filtered)", "KG", 365)}
# code: FR, EN, unit, shelf life, price, sales tax group (pure syrup and butter: basic groceries, zero-rated;
# candy and fudge: confectionery, GST + QST), weight (kg)
FINISHED = {
    "MAPLE-SYRUP-540": (
        "Sirop d'érable ambré, canne 540 ml",
        "Amber maple syrup, 540 ml can",
        730,
        11.50,
        "ZERO",
        0.75,
    ),
    "MAPLE-SYRUP-250": (
        "Sirop d'érable foncé, bouteille 250 ml",
        "Dark maple syrup, 250 ml bottle",
        730,
        8.25,
        "ZERO",
        0.55,
    ),
    "MAPLE-BUTTER-200": ("Beurre d'érable, pot 200 g", "Maple butter, 200 g jar", 180, 7.95, "ZERO", 0.38),
    "MAPLE-CANDY-12": ("Bonbons d'érable, boîte de 12", "Maple candy, box of 12", 365, 6.50, "QC", 0.14),
    "MAPLE-FUDGE-250": (
        "Sucre à la crème à l'érable, 250 g",
        "Maple fudge, 250 g",
        90,
        7.25,
        "QC",
        0.27,
    ),
}


def product(code: str, **row) -> dict:
    base = {
        "cCode": code,
        "cStatus": "active",
        "cStockType": "physical",
        "cNature": "product",
        "cCostMethod": "avg",
        "cCurrency": "CAD",
        "cSalesTaxGroup": "ZERO",
        "cPurchaseTaxGroup": "ZERO",
        "cWeightUOM": "kg",
        "cDimUOM": "cm",
        "cCountryOrigin": "CA",
        "cDefaultWarehouse": WH,
        "lStocked": True,
        "lPORequired": True,
        "dAvgCost": "",
        "dLastCost": "",
        "lines": [],
        "conversions": [],
    }
    row = {**base, **row}
    row.setdefault("cPurchaseUOM", row["cStockUOM"])
    row.setdefault("cSalesUOM", row["cStockUOM"])
    return full(S.PRODUCT, row)


def _line(sup: str, price: float, lead: int = 5) -> dict:
    return {
        "cSupplierCode": sup,
        "cSupplierItem": "",
        "dPurchasePrice": money(price),
        "cCurrency": "CAD",
        "iLeadTimeDays": lead,
        "dMinOrderQty": "",
        "lPreferred": True,
    }


def products() -> list[dict]:
    rows = []
    for code, (fr, en, cat, uom, _loc, price, sup, days) in BOUGHT.items():
        lines = [_line(sup, price, 7 if cat == "RAW-SYRUP" else 3)]
        if code == "SYRUP-BULK-AMB":  # the three sugar bushes sell amber syrup
            lines += [
                {**_line("CANTONS", 7.55, 7), "lPreferred": False},
                {**_line("TREMBLAY", 7.25, 10), "lPreferred": False},
            ]
        if code == "SYRUP-BULK-DRK":
            lines += [{**_line("TREMBLAY", 6.80, 10), "lPreferred": False}]
        rows.append(
            product(
                code,
                cDescFR=fr,
                cDescEN=en,
                cCategory=cat,
                cStockUOM=uom,
                cClass="raw",
                lSellable=False,
                lPurchasable=True,
                cPurchaseTaxGroup="QC" if cat == "PACK" else "ZERO",
                lLotControl=days > 0,
                lExpiryControl=days > 0,
                iShelfLifeDays=days,
                cABCClass="A" if cat == "RAW-SYRUP" else "B",
                lines=lines,
                cNotes=(
                    "Un baril = un lot. Lot du fournisseur : numéro du baril du producteur et date de récolte."
                    if cat == "RAW-SYRUP"
                    else ""
                ),
            )
        )
    for code, (fr, en, uom, days) in WIP.items():
        rows.append(
            product(
                code,
                cDescFR=fr,
                cDescEN=en,
                cCategory="WIP",
                cStockUOM=uom,
                cClass="kit",
                lSellable=False,
                lPurchasable=False,
                lPORequired=False,
                lLotControl=True,
                lExpiryControl=True,
                iShelfLifeDays=days,
            )
        )
    for code, (fr, en, days, price, tax, weight) in FINISHED.items():
        rows.append(
            product(
                code,
                cDescFR=fr,
                cDescEN=en,
                cCategory="MAPLE",
                cStockUOM="UN",
                cClass="finished",
                cSalesTaxGroup=tax,
                lSellable=True,
                lPurchasable=False,
                lPORequired=False,
                lLotControl=True,
                lExpiryControl=True,
                iShelfLifeDays=days,
                cPickPolicy="FEFO",
                dPrice1=money(price),
                dWeight=num(weight),
                cNotes="Contient : lait." if code == "MAPLE-FUDGE-250" else "",
            )
        )
    rows.append(
        product(
            "FILTER-PAPER",
            cDescFR="Papier filtre pour filtre-presse",
            cDescEN="Filter paper for the filter press",
            cCategory="SUPPLIES",
            cStockUOM="UN",
            cClass="consumable",
            lSellable=False,
            lPurchasable=True,
            cPurchaseTaxGroup="QC",
            lines=[_line("BOREAL", 2.75)],
        )
    )
    rows.append(
        product(
            "GLOVES",
            cDescFR="Gants jetables en nitrile (boîte de 100)",
            cDescEN="Disposable nitrile gloves (box of 100)",
            cCategory="SUPPLIES",
            cStockUOM="BTE",
            cClass="consumable",
            lSellable=False,
            lPurchasable=True,
            cPurchaseTaxGroup="QC",
            lines=[_line("BOREAL", 9.50)],
        )
    )
    for code, fr, en, price in (
        ("CANDY-COOKER", "Cuiseur à sucre 40 L", "Sugar cooker, 40 L", 8900.00),
        ("FILLER", "Remplisseuse à chaud 2 becs", "Hot filler, 2 heads", 14500.00),
    ):
        rows.append(
            product(
                code,
                cDescFR=fr,
                cDescEN=en,
                cCategory="EQUIP",
                cStockUOM="UN",
                cClass="asset",
                lStocked=False,
                lSellable=False,
                lPurchasable=True,
                cPurchaseTaxGroup="QC",
                cDefaultWarehouse="",
                lines=[_line("ACERI-EQ", price, 30)],
            )
        )
    return rows


# ------------------------------------------------------------------ purchases

SUPPLIER_BASE = {
    "cTermCode": "n30",
    "cTermDesc": "net 30 jours",
    "cAddress2": "",
    "cCountry": "CA",
    "cProvince": "qc",
    "cDeptSauv": "",
    "iStatutAch": 1,
    "cCodeAch": BUYER,
    "cDescAch": BUYER,
    "iTypePO": 1,
}
SUPPLIERS = [
    ("GAGNON", "Érablière Gagnon et fils", "2140, rang Saint-Joseph", "Saint-Prosper", "G0M 1Y0", "812345671"),
    ("CANTONS", "Érablière des Cantons inc.", "815, chemin de la Montagne", "Sutton", "J0E 2K0", "823456712"),
    ("TREMBLAY", "Sucrerie Tremblay", "47, rang du Lac", "Pohénégamook", "G0L 1J0", "834567123"),
    ("LAITERIE", "Laiterie du Terroir inc.", "300, rue Principale", "Coaticook", "J1A 2R6", "845671234"),
    ("BOREAL", "Emballages Boréal inc.", "1200, rue de l'Industrie", "Lévis", "G6Z 1X3", "856712345"),
    ("ACERI-EQ", "Équipements Acéricoles Beauce", "560, 90e Rue", "Saint-Georges", "G5Y 3L1", "867123456"),
]
TAXED = {"BOREAL", "ACERI-EQ"}  # food is zero-rated

# a barrel: (kg ordered, kg received, location, harvest day, producer's barrel number)
AMB, DRK = "SYRUP-BULK-AMB", "SYRUP-BULK-DRK"
# PO, supplier, order date, reception date (None = still open), invoice no, lines (item, qty, barrel or location)
PURCHASES = [
    ("810101", "ACERI-EQ", "2026-09-01", "2026-09-15", "EAB-4471", [("CANDY-COOKER", 1, None)]),
    (
        "810102",
        "GAGNON",
        "2026-09-08",
        "2026-09-10",
        "EGF-2611",
        [
            (AMB, 275, (275, "BAR-01", "2026-03-24", "B-0412")),
            (AMB, 268, (268, "BAR-02", "2026-03-29", "B-0418")),
            (AMB, 281, (281, "BAR-03", "2026-04-02", "B-0425")),
            (AMB, 270, (270, "BAR-04", "2026-04-08", "B-0431")),
        ],
    ),
    (
        "810103",
        "BOREAL",
        "2026-09-08",
        "2026-09-12",
        "EB-30915",
        [
            ("CAN-540", 3000, None),
            ("BOTTLE-250", 1200, None),
            ("CAP-28", 1200, None),
            ("JAR-200", 800, None),
            ("BOX-12", 900, None),
            ("TRAY-250", 700, None),
            ("LABEL", 8000, None),
            ("FILTER-PAPER", 40, None),
            ("GLOVES", 10, None),
        ],
    ),
    (
        "810104",
        "CANTONS",
        "2026-09-28",
        "2026-09-30",
        "EDC-1187",
        [
            (DRK, 272, (272, "BAR-05", "2026-04-14", "C-2207")),
            (DRK, 266, (266, "BAR-06", "2026-04-17", "C-2213")),
            (AMB, 279, (279, "BAR-07", "2026-03-31", "C-2101")),
            (AMB, 274, (274, "BAR-08", "2026-04-04", "C-2124")),
        ],
    ),
    (
        "810105",
        "LAITERIE",
        "2026-10-05",
        "2026-10-06",
        "LT-80213",
        [("CREAM-35", 30, "COLD-01"), ("BUTTER", 10, "COLD-02")],
    ),
    (
        "810106",
        "TREMBLAY",
        "2026-10-26",
        "2026-10-28",
        "ST-0577",
        [
            (AMB, 280, (266, "BAR-09", "2026-04-06", "T-118")),  # received short: 266 of 280 kg
            (AMB, 276, (276, "BAR-10", "2026-04-10", "T-121")),
            (AMB, 278, (278, "BAR-11", "2026-04-26", "T-140")),  # end of season: tastes of "bourgeon" (NC)
        ],
    ),
    (
        "810107",
        "LAITERIE",
        "2026-11-09",
        "2026-11-10",
        "LT-80977",
        [("CREAM-35", 30, "COLD-03"), ("BUTTER", 10, "COLD-04")],
    ),
    (
        "810108",
        "GAGNON",
        "2026-11-23",
        None,
        "",
        [(AMB, 275, None), (AMB, 275, None), (AMB, 275, None), (AMB, 275, None)],
    ),
]


def build_purchases(prods: dict[str, dict]):
    names = {s[0]: s[1] for s in SUPPLIERS}
    suppliers = [
        {
            **SUPPLIER_BASE,
            "cCode": code,
            "cName": name,
            "cAddress1": addr,
            "cCity": city,
            "cZipCode": zipc,
            "cNoTPS": bn + "RT0001",
            "cNoTVQ": "12" + bn + "TQ0001",
        }
        for code, name, addr, city, zipc, bn in SUPPLIERS
    ]
    po_details, unbilled_po, rec_details, invoices, movements = [], [], [], [], []

    def price(sup: str, code: str) -> float:
        lines = prods[code]["lines"]
        return float(next((ln for ln in lines if ln["cSupplierCode"] == sup), lines[0])["dPurchasePrice"])

    for n, (cpo, sup, ordered, received, inv_no, lines) in enumerate(PURCHASES, 1):
        got = [(code, q, extra[0] if isinstance(extra, tuple) else q, extra) for code, q, extra in lines]
        sub_po = sum(q * price(sup, code) for code, q, _r, _e in got)
        sub = sum(r * price(sup, code) for code, _q, r, _e in got)
        tax = sup in TAXED
        po_details.append(
            {
                "COMPANY": "MA2",
                "cPO": cpo,
                "ttPOheader": {
                    "cSupplierCode": sup,
                    "cSupplierName": names[sup],
                    "cBuyerCode": BUYER,
                    "cBuyerName": BUYER,
                    "cApplicantCode": BUYER,
                    "dOrderDate": ordered,
                    "dSubTotal": money(sub_po),
                    "dFreight": "0.00",
                    "dGST": money(round(sub_po * 0.05 + 1e-9, 2) if tax else 0),
                    "dPST": money(round(sub_po * 0.09975 + 1e-9, 2) if tax else 0),
                    "dTotalAmount": money(
                        sub_po + (round(sub_po * 0.05 + 1e-9, 2) + round(sub_po * 0.09975 + 1e-9, 2) if tax else 0)
                    ),
                },
                "ttPOdetail": [
                    {
                        "cUnique": str(i),
                        "cProductcode": code,
                        "cProductDesc": prods[code]["cDescFR"],
                        "dQuantity": num(q),
                        "dUnitCost": money(price(sup, code)),
                        "dSubTotal": money(q * price(sup, code)),
                        "dTotalAmount": money(q * price(sup, code)),
                    }
                    for i, (code, q, _r, _e) in enumerate(got, 1)
                ],
            }
        )
        if received is None:
            unbilled_po.append(
                {
                    "COMPANY": "MA2",
                    "cPO": cpo,
                    "dCreationDate": ordered,
                    "cSupplierName": names[sup],
                    "cSupplierCode": sup,
                }
            )
            continue
        gst = round(sub * 0.05 + 1e-9, 2) if tax else 0.0
        qst = round(sub * 0.09975 + 1e-9, 2) if tax else 0.0
        rec = str(900100 + n)
        articles = []
        for i, (code, q, r, extra) in enumerate(got, 1):
            p = prods[code]
            line = {
                "CodeArticle": code,
                "Description": p["cDescFR"],
                "QuantiteCommandee": num(q),
                "QuantiteRecue": num(r),
                "PrixUnitaire": money(price(sup, code)),
                "Devise": "CAD",
            }
            articles.append(line)
            if not p["lStocked"]:
                continue  # the sugar cooker is a fixed asset: no stock
            if isinstance(extra, tuple):  # a barrel: its place, the harvest, the producer's barrel number
                _kg, loc, harvest, barrel = extra
                expiry = (date.fromisoformat(harvest) + timedelta(days=p["iShelfLifeDays"])).isoformat()
                supplier_lot = f"{barrel} / récolte {harvest}"
            else:
                loc = extra or (BOUGHT[code][4] if code in BOUGHT else "") or "PACK-01"
                days = p["iShelfLifeDays"] if p["lExpiryControl"] else 0
                expiry = (date.fromisoformat(received) + timedelta(days=days)).isoformat() if days else ""
                supplier_lot = f"{inv_no}-{i}" if p["lLotControl"] else ""
            lot = f"{rec}-{i}" if p["lLotControl"] else ""
            movements.append(
                {
                    "dDate": received,
                    "cType": "IN",
                    "cProduct": code,
                    "dQty": num(r),
                    "dUnitCost": money(price(sup, code)),
                    "cWarehouse": WH,
                    "cLocation": loc,
                    "cWhTo": "",
                    "cLocTo": "",
                    "cLot": lot,
                    "cSerial": "",
                    "dExpiry": expiry,
                    "cDocType": "REC",
                    "cDocNo": rec,
                    "cReason": "Réception fournisseur",
                    "cComment": inv_no,
                }
            )
            # the reception went into the stock: its line says where and how (lot, the supplier's lot, expiry)
            line.update({"cLocation": loc, "cLot": lot, "cSupplierLot": supplier_lot, "dExpiry": expiry})
        rec_details.append(
            {
                "NoReception": rec,
                "COMPANY": "MA2",
                "DateReception": received,
                "Fournisseur": names[sup],
                "CodeFournisseur": sup,
                "NoBonCommande": cpo,
                "Statut": "Reçu",
                "Entrepot": WH,
                "Articles": articles,
                "MontantTotal": money(sub + gst + qst),
                "ResponsableReception": BUYER,
                "Commentaires": "Baril T-118 : 266 kg reçus sur 280 kg commandés." if cpo == "810106" else "",
                "SousTotal": money(sub),
                "Transport": "0.00",
                "TPS": money(gst),
                "TVQ": money(qst),
                "lStockPosted": True,
                "dStockPosted": received + "T16:00:00",
                "cStockPostedBy": BUYER,
            }
        )
        invoices.append(
            {
                "cNoFourn": sup,
                "cNoFacture": inv_no,
                "dDateFacture": received,
                "cNoCommAch": cpo,
                "cDevise": "CAD",
                "cStatut": "Posted",
                "cSource": "ERP",
                "dTransport": "0.00",
                "dTotalTPS": money(gst),
                "dTotalTVP": money(qst),
                "lines": [
                    {
                        "cCodeProduit": code,
                        "cDescription": prods[code]["cDescFR"],
                        "dQuantite": num(r),
                        "dCoutUnitaire": money(price(sup, code)),
                        "cGL": "",
                        "cCC1": "",
                        "cCC2": "",
                        "iNoReception": rec,
                    }
                    for code, _q, r, _e in got
                ],
            }
        )
    return (
        suppliers,
        {"po_details": po_details, "unbilled_po": unbilled_po},
        {"receiving_details": rec_details, "unbilled_receiving": []},
        invoices,
        movements,
    )


# ------------------------------------------------------------------ production

CALENDAR = {
    "cCode": "MPL-1X5",
    "cDescFR": "Usine : 1 équipe, lundi au vendredi",
    "cDescEN": "Plant: 1 shift, Monday to Friday",
    "lActive": True,
    "lines": [
        {"iWeekday": d, "cShift": "JOUR", "cStart": "07:00", "cEnd": "15:30", "iBreakMin": 30} for d in range(1, 6)
    ],
}
CAPABILITIES = [
    ("FILTER", "Filtration", "Filtering"),
    ("COOK", "Cuisson", "Cooking"),
    ("FILL", "Remplissage", "Filling"),
    ("PACK", "Emballage", "Packing"),
]
WORK_CENTERS = [
    ("MPL-FILTER", "Filtre-presse", "Filter press", "machine", "30", "15"),
    ("MPL-COOKER", "Cuiseurs à sucre", "Sugar cookers", "machine", "35", "25"),
    ("MPL-FILLER", "Ligne de remplissage", "Filling line", "machine", "40", "30"),
    ("MPL-CREW", "Équipe de production", "Production crew", "labor", "26", "0"),
]
RESOURCES = [
    ("FPRESS1", "Filtre-presse 10 plaques", "Filter press, 10 plates", "MPL-FILTER", "FILTER", 1),
    ("COOKER1", "Cuiseur à sucre 40 L (1)", "Sugar cooker 40 L (1)", "MPL-COOKER", "COOK", 1),
    ("COOKER2", "Cuiseur à sucre 40 L (2)", "Sugar cooker 40 L (2)", "MPL-COOKER", "COOK", 1),
    ("FILLER1", "Remplisseuse à chaud 2 becs", "Hot filler, 2 heads", "MPL-FILLER", "FILL", 2),
]
# code, FR, EN, work center, capability, run format, setup, run value, crew
OPERATIONS = [
    ("MPL-BLEND", "Mélange des barils", "Blending the barrels", "MPL-CREW", "", "min_per_lot", "10", "30", 2),
    ("MPL-FILTER", "Filtration", "Filtering", "", "FILTER", "min_per_lot", "15", "60", 1),
    ("MPL-HEAT", "Chauffage pour le remplissage", "Heating for the filling", "", "COOK", "min_per_lot", "5", "30", 1),
    ("MPL-FILL", "Remplissage à chaud", "Hot filling", "", "FILL", "units_per_hour", "15", "600", 2),
    ("MPL-COOK", "Cuisson du sirop", "Cooking the syrup", "", "COOK", "min_per_lot", "10", "45", 1),
    ("MPL-COOL", "Refroidissement rapide", "Fast cooling", "MPL-CREW", "", "min_per_lot", "0", "40", 1),
    ("MPL-WHIP", "Brassage", "Whipping", "MPL-CREW", "", "min_per_lot", "5", "20", 1),
    ("MPL-MOULD", "Moulage et démoulage", "Moulding and unmoulding", "MPL-CREW", "", "units_per_hour", "10", "300", 2),
    ("MPL-PACK", "Étiquetage et emballage", "Labelling and packing", "MPL-CREW", "", "units_per_hour", "0", "500", 1),
]


def production() -> dict:
    work_centers = [
        full(
            S.WORK_CENTER,
            {
                "cCode": code,
                "cDescFR": fr,
                "cDescEN": en,
                "cType": kind,
                "cCalendar": CALENDAR["cCode"],
                "lFinite": kind != "labor",
                "dEfficiencyPct": "100",
                "dUtilizationPct": "90" if kind != "labor" else "100",
                "dSetupRateHr": "0" if kind == "labor" else setup_rate,
                "dRunRateHr": run_rate if kind != "labor" else setup_rate,
                "dBurdenRateHr": "0" if kind == "labor" else "12",
                "cWarehouse": WH,
                "cInLocation": "PROD-01",
                "lActive": True,
            },
        )
        for code, fr, en, kind, setup_rate, run_rate in WORK_CENTERS
    ]
    resources = [
        full(
            S.RESOURCE,
            {
                "cCode": code,
                "cDescFR": fr,
                "cDescEN": en,
                "cWorkCenter": wc,
                "dSpeedFactor": "1",
                "iParallel": parallel,
                "lActive": True,
                "capabilities": [{"cCapability": cap, "iPreference": 1}],
                "attributes": [],
                "subresources": [],
                "downtime": [],
            },
        )
        for code, fr, en, wc, cap, parallel in RESOURCES
    ]
    operations = [
        full(
            S.OPERATION,
            {
                "cCode": code,
                "cDescFR": fr,
                "cDescEN": en,
                "cWorkCenter": wc,
                "cCapability": cap,
                "cRunFormat": fmt,
                "dSetupMin": setup,
                "dRunValue": run,
                "iCrew": crew,
                "lReportingPoint": True,
                "lActive": True,
            },
        )
        for code, fr, en, wc, cap, fmt, setup, run, crew in OPERATIONS
    ]
    product_mfg = [
        full(
            S.PRODUCT_MFG,
            {
                "cProduct": code,
                "cMakeBuy": "make",
                "dMfgLotMin": "",
                "iMfgLeadDays": 0,
                "cTraceLevel": "lot",
                "attributes": [],
            },
        )
        for code in [*WIP, *FINISHED]
    ]
    return {
        "_comment": "Maple products demo (tools/make_maple_data.py): syrup, butter, candy and fudge from bulk syrup.",
        "capabilities": [{"cCode": c, "cDescFR": fr, "cDescEN": en, "lActive": True} for c, fr, en in CAPABILITIES],
        "setup_families": [],
        "downtime_reasons": [
            {
                "cCode": "CLEAN",
                "cDescFR": "Lavage (changement de produit)",
                "cDescEN": "Washing (product change)",
                "cGroup": "planned",
                "lAffectsOEE": False,
                "lActive": True,
            },
            {
                "cCode": "BRK-MECH",
                "cDescFR": "Panne",
                "cDescEN": "Breakdown",
                "cGroup": "breakdown",
                "lAffectsOEE": True,
                "lActive": True,
            },
        ],
        "scrap_reasons": [
            {
                "cCode": "OVERCOOK",
                "cDescFR": "Trop cuit (cristallisé)",
                "cDescEN": "Overcooked (crystallized)",
                "cGroup": "process",
                "lActive": True,
            },
            {
                "cCode": "BROKEN",
                "cDescFR": "Bonbon cassé",
                "cDescEN": "Broken candy",
                "cGroup": "process",
                "lActive": True,
            },
            {
                "cCode": "FILL-LEAK",
                "cDescFR": "Contenant mal scellé",
                "cDescEN": "Container badly sealed",
                "cGroup": "process",
                "lActive": True,
            },
        ],
        "calendars": [CALENDAR],
        "calendar_exceptions": [
            {
                "cCalendar": "*",
                "dDate": day,
                "cDescFR": fr,
                "cDescEN": en,
                "lClosed": True,
                "cStart": "",
                "cEnd": "",
                "iBreakMin": 0,
            }
            for day, fr, en in (
                ("2026-10-12", "Action de grâce", "Thanksgiving"),
                ("2026-12-25", "Noël", "Christmas"),
            )
        ],
        "work_centers": work_centers,
        "resources": resources,
        "operations": operations,
        "setup_matrices": [],
        "product_mfg": product_mfg,
        "recipes": recipes(),
    }


def material(seq: int, item: str, qty: float, op_seq: int, method: str = "manual") -> dict:
    return {"iSeq": seq, "cComponent": item, "dQtyPer": num(qty), "iOpSeq": op_seq, "cIssueMethod": method}


def op(seq: int, operation: str, resource: str = "") -> dict:
    return {"iOpSeq": seq, "cOperation": operation, "cResource": resource, "lReportingPoint": True}


def step(op_seq: int, seq: int, kind: str, fr: str, en: str, **extra) -> dict:
    return {"iOpSeq": op_seq, "iStep": seq, "cKind": kind, "cTitleFR": fr, "cTitleEN": en, **extra}


def recipe(product: str, process: str, base: float, materials, operations, steps, notes: str = "") -> dict:
    return {
        "cProduct": product,
        "cRevision": "A",
        "cProcessType": process,
        "dBaseQty": num(base),
        "cNotes": notes,
        "materials": materials,
        "outputs": [],
        "operations": operations,
        "steps": steps,
        "cStatus": "approved",
        "lDefault": True,
        "cSubmittedBy": "demo",
        "cApprovedBy": "admin",
        "dApprovedAt": "2026-09-16T09:00:00",
        "cChangeReason": "Première version",
        "dEffectiveFrom": "2026-09-16",
        "history": [
            {
                "dAt": "2026-09-15T14:00:00",
                "cUser": "demo",
                "cAction": "submit",
                "cFrom": "draft",
                "cTo": "in_review",
                "cComment": "",
            },
            {
                "dAt": "2026-09-16T09:00:00",
                "cUser": "admin",
                "cAction": "approve",
                "cFrom": "in_review",
                "cTo": "approved",
                "cComment": "",
            },
        ],
    }


# critical control points: out of the limits, the lot is held (quality decides) or the order is blocked
HOLD = {"lRequired": True, "lCritical": True, "cOnFail": "hold_lot", "cFrequency": "per_lot"}
BLOCK = {"lRequired": True, "lCritical": True, "cOnFail": "block"}


def brix(op_seq: int, seq: int) -> dict:
    return step(
        op_seq,
        seq,
        "measure",
        "Brix du sirop (66 à 68,9)",
        "Syrup Brix (66 to 68.9)",
        cParam="BRIX",
        cUOM="°Bx",
        dTarget="67.2",
        dMin="66",
        dMax="68.9",
        **BLOCK,
    )


def cook(op_seq: int, seq: int, target: float, low: float, high: float, fr: str, en: str) -> dict:
    return step(
        op_seq,
        seq,
        "measure",
        fr,
        en,
        cParam="TEMP_CUISSON",
        cUOM="°C",
        dTarget=num(target),
        dMin=num(low),
        dMax=num(high),
        **HOLD,
    )


def hot_fill(op_seq: int, seq: int) -> dict:
    return step(
        op_seq,
        seq,
        "measure",
        "Température de remplissage (82 °C ou plus)",
        "Filling temperature (82 °C or more)",
        cParam="TEMP_REMPLISSAGE",
        cUOM="°C",
        dTarget="85",
        dMin="82",
        dMax="90",
        **HOLD,
    )


def recipes() -> list[dict]:
    return [
        recipe(
            "SYRUP-STD",
            "batch",
            100,
            [material(10, AMB, 101, 10), material(20, "FILTER-PAPER", 0.5, 20, "backflush")],
            [op(10, "MPL-BLEND"), op(20, "MPL-FILTER", "FPRESS1")],
            [
                step(
                    10,
                    10,
                    "material_add",
                    "Vider les barils (lire le lot)",
                    "Empty the barrels (scan the lot)",
                    iMaterialSeq=10,
                ),
                step(
                    10,
                    20,
                    "check",
                    "Goût et odeur des barils conformes",
                    "Taste and smell of the barrels are right",
                    **BLOCK,
                ),
                step(20, 10, "timer", "Filtrer 60 minutes", "Filter for 60 minutes", dDurationMin="60"),
                brix(20, 20),
            ],
            "100 kg de sirop filtré : 101 kg de sirop en vrac (1 % reste dans le filtre).",
        ),
        recipe(
            "MAPLE-SYRUP-540",
            "discrete",
            100,
            [
                material(10, "SYRUP-STD", 72, 10),
                material(20, "CAN-540", 100, 20, "backflush"),
                material(30, "LABEL", 100, 30, "backflush"),
            ],
            [op(10, "MPL-HEAT", "COOKER1"), op(20, "MPL-FILL", "FILLER1"), op(30, "MPL-PACK")],
            [
                step(
                    10,
                    10,
                    "material_add",
                    "Pomper le sirop standardisé (lire le lot)",
                    "Pump the standardized syrup (scan the lot)",
                    iMaterialSeq=10,
                ),
                hot_fill(20, 10),
                step(20, 20, "check", "Cannes bien scellées", "Cans well sealed", **BLOCK),
                step(30, 10, "output", "Déclarer la production", "Report the production"),
            ],
            "100 cannes de 540 ml = 72 kg de sirop. Remplissage à chaud : 82 °C ou plus, sinon le lot est retenu.",
        ),
        recipe(
            "MAPLE-SYRUP-250",
            "discrete",
            100,
            [
                material(10, DRK, 33.5, 10),
                material(20, "FILTER-PAPER", 0.2, 10, "backflush"),
                material(30, "BOTTLE-250", 100, 20, "backflush"),
                material(40, "CAP-28", 100, 20, "backflush"),
                material(50, "LABEL", 100, 30, "backflush"),
            ],
            [op(10, "MPL-FILTER", "FPRESS1"), op(20, "MPL-FILL", "FILLER1"), op(30, "MPL-PACK")],
            [
                step(
                    10,
                    10,
                    "material_add",
                    "Vider le baril de sirop foncé (lire le lot)",
                    "Empty the barrel of dark syrup (scan the lot)",
                    iMaterialSeq=10,
                ),
                brix(10, 20),
                hot_fill(20, 10),
                step(30, 10, "output", "Déclarer la production", "Report the production"),
            ],
            "100 bouteilles de 250 ml = 33,5 kg de sirop foncé, filtré au moment de l'embouteillage.",
        ),
        recipe(
            "MAPLE-BUTTER-200",
            "batch",
            100,
            [
                material(10, "SYRUP-STD", 23, 10),
                material(20, "JAR-200", 100, 30, "backflush"),
                material(30, "LABEL", 100, 30, "backflush"),
            ],
            [op(10, "MPL-COOK", "COOKER1"), op(20, "MPL-COOL"), op(30, "MPL-WHIP")],
            [
                step(
                    10,
                    10,
                    "material_add",
                    "Verser le sirop (lire le lot)",
                    "Pour the syrup (scan the lot)",
                    iMaterialSeq=10,
                ),
                cook(10, 20, 112, 111, 113, "Cuire à 112 °C", "Cook to 112 °C"),
                step(
                    20,
                    10,
                    "measure",
                    "Refroidir sous 10 °C avant de brasser",
                    "Cool below 10 °C before whipping",
                    cParam="TEMP_REFROID",
                    cUOM="°C",
                    dTarget="8",
                    dMin="0",
                    dMax="10",
                    **HOLD,
                ),
                step(30, 10, "timer", "Brasser 20 minutes", "Whip for 20 minutes", dDurationMin="20"),
            ],
            "100 pots de 200 g = 23 kg de sirop. Le sirop cuit est refroidi vite sous 10 °C, puis brassé jusqu'à être crémeux.",
        ),
        recipe(
            "MAPLE-CANDY-12",
            "batch",
            100,
            [
                material(10, "SYRUP-STD", 14, 10),
                material(20, "BOX-12", 100, 20, "backflush"),
                material(30, "LABEL", 100, 20, "backflush"),
            ],
            [op(10, "MPL-COOK", "COOKER2"), op(20, "MPL-MOULD")],
            [
                step(
                    10,
                    10,
                    "material_add",
                    "Verser le sirop (lire le lot)",
                    "Pour the syrup (scan the lot)",
                    iMaterialSeq=10,
                ),
                cook(10, 20, 115, 114, 116, "Cuire à 115 °C", "Cook to 115 °C"),
                step(
                    20,
                    10,
                    "timer",
                    "Laisser figer dans les moules 30 minutes",
                    "Let set in the moulds for 30 minutes",
                    dDurationMin="30",
                ),
            ],
            "100 boîtes de 12 bonbons (120 g) = 14 kg de sirop.",
        ),
        recipe(
            "MAPLE-FUDGE-250",
            "batch",
            100,
            [
                material(10, "SYRUP-STD", 18, 10),
                material(20, "CREAM-35", 6, 10),
                material(30, "BUTTER", 1.5, 10),
                material(40, "TRAY-250", 100, 20, "backflush"),
                material(50, "LABEL", 100, 20, "backflush"),
            ],
            [op(10, "MPL-COOK", "COOKER2"), op(20, "MPL-PACK")],
            [
                step(
                    10,
                    10,
                    "material_add",
                    "Verser le sirop (lire le lot)",
                    "Pour the syrup (scan the lot)",
                    iMaterialSeq=10,
                ),
                step(
                    10,
                    20,
                    "material_add",
                    "Ajouter la crème (lire le lot)",
                    "Add the cream (scan the lot)",
                    iMaterialSeq=20,
                ),
                cook(10, 30, 113, 112, 114, "Cuire à 113 °C", "Cook to 113 °C"),
                step(
                    20,
                    10,
                    "check",
                    "Étiquette avec l'allergène « lait »",
                    'Label shows the allergen "milk"',
                    **BLOCK,
                ),
            ],
            "100 barquettes de 250 g = 18 kg de sirop, 6 L de crème et 1,5 kg de beurre. Contient du lait.",
        ),
    ]


# ------------------------------------------------------------------ sales master data

COMPANY = {
    "cCode": "MAIN",
    "cName": "Érablière Démo",
    "cLegalName": "Érablière Démo inc.",
    "cAddress1": "1250, 1re Avenue Est",
    "cAddress2": "",
    "cCity": "Saint-Georges",
    "cProvince": "QC",
    "cZipCode": "G5Y 5B2",
    "cCountry": "CA",
    "cPhone": "418 555-0400",
    "cEmail": "factures@erabliere-demo.ca",
    "cWebsite": "www.erabliere-demo.ca",
    "cNEQ": "1170000003",
    "cInvoiceNoteFR": "Produits de l'érable purs du Québec. Sirop et beurre : conserver au froid après ouverture. Merci !",
    "cInvoiceNoteEN": "Pure maple products from Quebec. Syrup and butter: keep cold once opened. Thank you!",
}
# price list: FR, EN, notes, (product, min qty, price)
PRICE_LISTS = {
    "RETAIL": (
        "Détaillants",
        "Retailers",
        "",
        [
            ("MAPLE-SYRUP-540", 0, 10.25),
            ("MAPLE-SYRUP-540", 120, 9.75),
            ("MAPLE-SYRUP-250", 0, 7.40),
            ("MAPLE-BUTTER-200", 0, 7.10),
            ("MAPLE-CANDY-12", 0, 5.80),
            ("MAPLE-FUDGE-250", 0, 6.50),
        ],
    ),
    "DISTRIB": (
        "Distributeurs",
        "Distributors",
        "Prix à la palette ; l'escompte du client s'ajoute.",
        [
            ("MAPLE-SYRUP-540", 0, 9.20),
            ("MAPLE-SYRUP-540", 300, 8.80),
            ("MAPLE-SYRUP-250", 0, 6.60),
            ("MAPLE-BUTTER-200", 0, 6.35),
            ("MAPLE-CANDY-12", 0, 5.15),
            ("MAPLE-FUDGE-250", 0, 5.80),
        ],
    ),
    "HOTELS": (
        "Hôtels et restaurants",
        "Hotels and restaurants",
        "",
        [
            ("MAPLE-SYRUP-540", 0, 9.90),
            ("MAPLE-SYRUP-250", 0, 6.95),
            ("MAPLE-BUTTER-200", 0, 6.90),
            ("MAPLE-CANDY-12", 0, 5.60),
        ],
    ),
}
# code, name, language, address, city, zip, phone, email domain, price list, discount, terms, contact
CUSTOMERS = [
    (
        "EPICERIE-STDENIS",
        "Épicerie fine Saint-Denis",
        "fr",
        "4280, rue Saint-Denis",
        "Montréal",
        "H2J 2K8",
        "514 555-0421",
        "epiceriestdenis.ca",
        "RETAIL",
        "",
        ("n30", "net 30 jours"),
        ("Mélanie Roy", "Acheteuse"),
    ),
    (
        "BOUTIQUE-VQ",
        "Boutique Souvenirs du Vieux-Québec",
        "fr",
        "38, rue du Petit-Champlain",
        "Québec",
        "G1K 4H5",
        "418 555-0433",
        "souvenirsvieuxquebec.ca",
        "RETAIL",
        "",
        ("n30", "net 30 jours"),
        ("Patrice Gagné", "Propriétaire"),
    ),
    (
        "LAURENTIAN-HOTELS",
        "Laurentian Hotels Group",
        "en",
        "1000, chemin du Village",
        "Mont-Tremblant",
        "J8E 1K4",
        "819 555-0447",
        "laurentianhotels.ca",
        "HOTELS",
        "",
        ("n30", "net 30 days"),
        ("Emily Clarke", "Purchasing manager"),
    ),
    (
        "DISTRIB-CHAUDIERE",
        "Distribution Alimentaire Chaudière inc.",
        "fr",
        "2500, boul. de la Rive-Sud",
        "Lévis",
        "G6W 6N7",
        "418 555-0459",
        "distchaudiere.ca",
        "DISTRIB",
        "3",
        ("n45", "net 45 jours"),
        ("Jean-François Poulin", "Directeur des achats"),
    ),
]


def sales() -> dict:
    lists = [
        {
            "cCode": code,
            "cDescFR": fr,
            "cDescEN": en,
            "dStartDate": "",
            "dEndDate": "",
            "cNotes": notes,
            "lActive": True,
            "lines": [
                {"cProduct": p, "cUOM": "UN", "dMinQty": num(q), "dPrice": money(v), "dDiscountPct": ""}
                for p, q, v in lines
            ],
            "discounts": [],
        }
        for code, (fr, en, notes, lines) in PRICE_LISTS.items()
    ]
    customers = []
    for code, name, lang, addr, city, zipc, phone, domain, plist, disc, (term, term_desc), (who, title) in CUSTOMERS:
        site = {"fr": "MAGASIN", "en": "MAIN"}[lang]
        customers.append(
            {
                "cCode": code,
                "cName": name,
                "cLegalName": name,
                "cLang": lang,
                "cAddress1": addr,
                "cAddress2": "",
                "cCity": city,
                "cProvince": "QC",
                "cZipCode": zipc,
                "cCountry": "CA",
                "cPhone": phone,
                "cEmail": f"comptes@{domain}",
                "cTaxGroup": "QC",
                "cTaxExemptNo": "",
                "cTermCode": term,
                "cTermDesc": term_desc,
                "cPriceList": plist,
                "dDiscountPct": disc,
                "cWarehouse": WH,
                "cNotes": "",
                "lActive": True,
                "addresses": [
                    {
                        "cCode": site,
                        "cName": name,
                        "cAddress1": addr,
                        "cAddress2": "",
                        "cCity": city,
                        "cProvince": "QC",
                        "cZipCode": zipc,
                        "cCountry": "CA",
                        "cContact": who,
                        "cPhone": phone,
                        "cTaxGroup": "",
                        "lDefault": True,
                    }
                ],
                "contacts": [
                    {"cName": who, "cTitle": title, "cPhone": phone, "cEmail": f"achats@{domain}", "lInvoices": False},
                    {
                        "cName": "Comptabilité" if lang == "fr" else "Accounts payable",
                        "cTitle": "",
                        "cPhone": phone,
                        "cEmail": f"comptes@{domain}",
                        "lInvoices": True,
                    },
                ],
            }
        )
    return {
        "_about": "Maple products scenario (tools/make_maple_data.py): the company profile, the retailers, hotels and "
        "the distributor buying the maple products, and their price lists. The invoices are in story.json.",
        "company_profile": [COMPANY],
        "price_lists": lists,
        "customers": customers,
        "sales_invoices": [],
    }


# ------------------------------------------------------------------ files


def inventory(prods: list[dict], movements: list[dict]) -> dict:
    return {
        "_about": "Maple products demo (tools/make_maple_data.py). Taxes and units come from data/inventory.json.",
        "categories": [
            {"cCode": c, "cDescFR": fr, "cDescEN": en, "cParent": parent, "lActive": True}
            for c, fr, en, parent in CATEGORIES
        ],
        "warehouses": [
            full(
                S.WAREHOUSE,
                {
                    "cCode": WH,
                    "cNameFR": "Usine de transformation - Saint-Georges",
                    "cNameEN": "Processing plant - Saint-Georges",
                    "cType": "main",
                    "cAddress1": "1250, 1re Avenue Est",
                    "cCity": "Saint-Georges",
                    "cProvince": "QC",
                    "cZipCode": "G5Y 5B2",
                    "cCountry": "CA",
                    "cManager": BUYER,
                    "lUseLocations": True,
                    "cReceivingLoc": "REC",
                    "cShippingLoc": "FG-01",
                    "lActive": True,
                },
            )
        ],
        "locations": [
            full(
                S.LOCATION,
                {
                    "cWarehouse": WH,
                    "cCode": code,
                    "cZone": zone,
                    "cDescription": desc,
                    "cType": kind,
                    "lMixProducts": True,
                    "iPickSeq": i,
                    "lActive": True,
                },
            )
            for i, (code, zone, desc, kind) in enumerate(LOCATIONS, 1)
        ],
        "products": prods,
        "stock_params": [
            full(
                S.STOCK_PARAM,
                {
                    "cProduct": code,
                    "cWarehouse": WH,
                    "dReorderPoint": num(rp),
                    "dMinQty": num(rp),
                    "dMaxQty": num(mx),
                    "cDefaultLocation": loc,
                    "iLeadTimeDays": lead,
                    "lActive": True,
                },
            )
            for code, rp, mx, loc, lead in [
                (AMB, 1100, 3300, "", 7),
                (DRK, 270, 820, "", 10),
                ("CREAM-35", 10, 40, "", 2),
                ("BUTTER", 4, 15, "", 2),
                ("CAN-540", 1000, 4000, "PACK-01", 5),
                ("BOTTLE-250", 400, 1500, "PACK-01", 5),
                ("LABEL", 2000, 10000, "PACK-01", 5),
            ]
        ],
        "movements": movements,
    }


def write(name: str, data) -> None:
    (OUT / name).write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def main() -> None:
    prods = products()
    by_code = {p["cCode"]: p for p in prods}
    suppliers, pos, recs, invoices, movements = build_purchases(by_code)
    OUT.mkdir(parents=True, exist_ok=True)
    files = {
        "inventory.json": inventory(prods, movements),
        "production.json": production(),
        "suppliers.json": suppliers,
        "purchase_orders.json": pos,
        "receptions.json": recs,
        "invoices.json": invoices,
        "sales.json": sales(),
    }
    for name, data in files.items():
        write(name, data)
    print(f"{OUT}: {len(prods)} products, {len(movements)} movements received, {len(invoices)} supplier invoices")
    from maple_story import play  # noqa: E402  (tools/maple_story.py: needs a database and time-machine)

    story = play(STORY_KEYS)
    write("story.json", story)
    print("story.json: " + ", ".join(f"{len(story[k])} {k}" for k in STORY_KEYS))


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    os.environ.setdefault("ERP_SCENARIO", "maple")
    main()
