"""Demo data of the pastry shop (Administration > System settings > Pastry shop).

A pastry shop that makes three pastels: beef and egg, chicken, ham and cheese. Ham and cheese are bought;
the dough, the ground beef, the boiled eggs, the cooked chicken and the shredded chicken are made. The beef and the
chickens are bought raw and whole: the beef is ground and cooked, the chicken is cooked and shredded.

Writes data/pastry/*.json:
    inventory.json        categories, kitchen, locations, products, stock parameters and the stock movements
    production.json       calendar, work centers, machines, standard operations, manufacturing data, recipes
    suppliers.json        the suppliers
    purchase_orders.json  the purchase orders (one still open)
    receptions.json       the receptions
    invoices.json         the supplier invoices (posted)
The stock of each item is what was received, and every reception is invoiced at the same quantities and prices,
so the stock value matches the invoices. Raw food is zero-rated (no GST / QST); packaging and equipment are taxed.

Usage: python tools/make_pastry_data.py   (same output every run)
"""

from __future__ import annotations

import json
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from powererp import schemas as S  # noqa: E402

OUT = ROOT / "data" / "pastry"
WH = "KITCHEN"
BUYER = "Cassiano"


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
    ("RAW-MEAT", "Viandes et volailles", "Meat and poultry", "RAW"),
    ("RAW-DAIRY", "Œufs, fromages et charcuteries", "Eggs, cheese and cold cuts", "RAW"),
    ("RAW-DRY", "Épicerie sèche et légumes", "Dry goods and vegetables", "RAW"),
    ("PACK", "Emballages", "Packaging", ""),
    ("WIP", "Produits semi-finis", "Semi-finished products", ""),
    ("PASTEL", "Pastels", "Pastels", ""),
    ("SUPPLIES", "Fournitures", "Supplies", ""),
    ("EQUIP", "Équipement", "Equipment", ""),
]

LOCATIONS = [
    ("REC", "REC", "Quai de réception", "receiving"),
    ("COLD-01", "FROID", "Chambre froide (0 à 4 °C)", "picking"),
    ("DRY-01", "SEC", "Réserve sèche", "picking"),
    ("PACK-01", "SEC", "Emballages et fournitures", "reserve"),
    ("PROD-01", "PROD", "Cuisine de production", "staging"),
    ("SHOP-01", "VENTE", "Comptoir de vente", "shipping"),
]

# code: FR, EN, category, unit, class, (location, purchase price, supplier, lot / expiry days), extra
BOUGHT = {
    "BEEF-RAW": (
        "Bœuf en pièce, cru congelé",
        "Beef, whole cut, raw frozen",
        "RAW-MEAT",
        "KG",
        "COLD-01",
        14.50,
        "MEATCO",
        180,
    ),
    "CHICKEN-RAW": (
        "Poulet entier, cru congelé",
        "Whole chicken, raw frozen",
        "RAW-MEAT",
        "KG",
        "COLD-01",
        6.80,
        "MEATCO",
        180,
    ),
    "EGG": ("Œuf frais calibre gros", "Fresh egg, large", "RAW-DAIRY", "UN", "COLD-01", 0.35, "FARMEGG", 45),
    "HAM": ("Jambon cuit tranché", "Sliced cooked ham", "RAW-DAIRY", "KG", "COLD-01", 11.50, "DELIQC", 60),
    "CHEESE": ("Fromage mozzarella", "Mozzarella cheese", "RAW-DAIRY", "KG", "COLD-01", 12.80, "DELIQC", 60),
    "FLOUR": ("Farine de blé tout usage", "All-purpose wheat flour", "RAW-DRY", "KG", "DRY-01", 1.10, "FOODWH", 0),
    "OIL-FRY": ("Huile de canola pour friture", "Canola frying oil", "RAW-DRY", "L", "DRY-01", 3.20, "FOODWH", 0),
    "SALT": ("Sel fin", "Fine salt", "RAW-DRY", "KG", "DRY-01", 1.20, "FOODWH", 0),
    "ONION": ("Oignon jaune", "Yellow onion", "RAW-DRY", "KG", "DRY-01", 2.40, "FOODWH", 0),
    "SEASONING": (
        "Assaisonnement (ail, poivre, paprika)",
        "Seasoning (garlic, pepper, paprika)",
        "RAW-DRY",
        "KG",
        "DRY-01",
        18.00,
        "FOODWH",
        0,
    ),
    "PAPER-BAG": ("Sac en papier pour pastel", "Paper bag for pastel", "PACK", "UN", "PACK-01", 0.08, "PACKPRO", 0),
}
MADE = {
    "DOUGH": ("Pâte à pastel", "Pastel dough", "KG", 2),
    "GROUND-BEEF": ("Bœuf haché cuit et assaisonné", "Ground beef, cooked and seasoned", "KG", 3),
    "BOILED-EGG": ("Œuf cuit dur haché", "Boiled egg, chopped", "UN", 3),
    "FILL-BEEF-EGG": ("Garniture bœuf et œuf", "Beef and egg filling", "KG", 2),
    "CHICKEN-COOKED": ("Poulet cuit", "Cooked chicken", "KG", 2),
    "CHICKEN-SHRED": ("Poulet effiloché assaisonné", "Shredded chicken, seasoned", "KG", 2),
}
FINISHED = {
    "PASTEL-BEEF": ("Pastel bœuf et œuf", "Beef and egg pastel", 6.50),
    "PASTEL-CHICKEN": ("Pastel au poulet", "Chicken pastel", 6.00),
    "PASTEL-HAM-CHEESE": ("Pastel jambon et fromage", "Ham and cheese pastel", 6.00),
}


def product(code: str, **row) -> dict:
    base = {
        "cCode": code,
        "cStatus": "active",
        "cStockType": "physical",
        "cNature": "product",
        "cCostMethod": "avg",
        "cCurrency": "CAD",
        "cSalesTaxGroup": "QC",
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


def products() -> list[dict]:
    rows = []
    for code, (fr, en, cat, uom, _loc, price, sup, days) in BOUGHT.items():
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
                cABCClass="A" if cat == "RAW-MEAT" else "B",
                lines=[
                    {
                        "cSupplierCode": sup,
                        "cSupplierItem": "",
                        "dPurchasePrice": money(price),
                        "cCurrency": "CAD",
                        "iLeadTimeDays": 1 if cat.startswith("RAW") else 3,
                        "dMinOrderQty": "",
                        "lPreferred": True,
                    }
                ],
            )
        )
    for code, (fr, en, uom, days) in MADE.items():
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
                iShelfLifeDays=days,
            )
        )
    for code, (fr, en, price) in FINISHED.items():
        rows.append(
            product(
                code,
                cDescFR=fr,
                cDescEN=en,
                cCategory="PASTEL",
                cStockUOM="UN",
                cClass="finished",
                lSellable=True,
                lPurchasable=False,
                lPORequired=False,
                lLotControl=True,
                iShelfLifeDays=1,
                dPrice1=money(price),
                dWeight="0.15",
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
            lines=[_line("PACKPRO", 9.50)],
        )
    )
    rows.append(
        product(
            "FRYER-2T",
            cDescFR="Friteuse électrique 2 bacs",
            cDescEN="Electric fryer, 2 tanks",
            cCategory="EQUIP",
            cStockUOM="UN",
            cClass="asset",
            lStocked=False,
            lSellable=False,
            lPurchasable=True,
            cPurchaseTaxGroup="QC",
            cDefaultWarehouse="",
            lines=[_line("KITCHEQ", 2890.00)],
        )
    )
    return rows


def _line(sup: str, price: float) -> dict:
    return {
        "cSupplierCode": sup,
        "cSupplierItem": "",
        "dPurchasePrice": money(price),
        "cCurrency": "CAD",
        "iLeadTimeDays": 3,
        "dMinOrderQty": "",
        "lPreferred": True,
    }


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
    ("MEATCO", "Boucherie Centrale Laval inc.", "2450, boul. Industriel", "Laval", "H7S 1P9", "823456781"),
    ("FARMEGG", "Ferme Avicole Saint-Hyacinthe", "1580, rang Saint-Pierre", "Saint-Hyacinthe", "J2T 4P5", "834567812"),
    ("DELIQC", "Distribution Fromages et Charcuteries QC", "780, rue Bridge", "Montréal", "H3K 2C4", "845678123"),
    ("FOODWH", "Grossiste Alimentaire Montréal", "9100, boul. Pie-IX", "Montréal", "H1Z 3T4", "856781234"),
    ("PACKPRO", "Emballages Pro inc.", "355, rue Saint-Jacques", "Longueuil", "J4H 3X1", "867812345"),
    ("KITCHEQ", "Équipements de Cuisine Pro", "6200, rue Saint-Hubert", "Montréal", "H2S 2M2", "878123456"),
]
TAXED = {"PACKPRO", "KITCHEQ"}  # raw food is zero-rated

# PO, supplier, order date, reception (date or None = still open), invoice no, lines (item, qty)
PURCHASES = [
    ("800101", "KITCHEQ", "2026-11-02", "2026-11-05", "ECP-20418", [("FRYER-2T", 1)]),
    ("800102", "MEATCO", "2026-11-09", "2026-11-10", "BCL-55210", [("BEEF-RAW", 40), ("CHICKEN-RAW", 50)]),
    ("800103", "FARMEGG", "2026-11-09", "2026-11-10", "FASH-3381", [("EGG", 360)]),
    ("800104", "DELIQC", "2026-11-10", "2026-11-12", "DFC-77105", [("HAM", 15), ("CHEESE", 15)]),
    (
        "800105",
        "FOODWH",
        "2026-11-10",
        "2026-11-12",
        "GAM-120934",
        [("FLOUR", 100), ("OIL-FRY", 60), ("SALT", 10), ("ONION", 20), ("SEASONING", 3)],
    ),
    ("800106", "PACKPRO", "2026-11-11", "2026-11-13", "EP-9902", [("PAPER-BAG", 2000), ("GLOVES", 10)]),
    ("800107", "MEATCO", "2026-11-20", None, "", [("BEEF-RAW", 40), ("CHICKEN-RAW", 50)]),
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
    po_details, unbilled_po, rec_details, unbilled_rec, invoices, movements = [], [], [], [], [], []
    for n, (cpo, sup, ordered, received, inv_no, lines) in enumerate(PURCHASES, 1):
        price = {code: float(prods[code]["lines"][0]["dPurchasePrice"]) for code, _q in lines}
        sub = sum(q * price[code] for code, q in lines)
        gst = round(sub * 0.05 + 1e-9, 2) if sup in TAXED else 0.0
        qst = round(sub * 0.09975 + 1e-9, 2) if sup in TAXED else 0.0
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
                    "dSubTotal": money(sub),
                    "dFreight": "0.00",
                    "dGST": money(gst),
                    "dPST": money(qst),
                    "dTotalAmount": money(sub + gst + qst),
                },
                "ttPOdetail": [
                    {
                        "cUnique": str(i),
                        "cProductcode": code,
                        "cProductDesc": prods[code]["cDescFR"],
                        "dQuantity": num(q),
                        "dUnitCost": money(price[code]),
                        "dSubTotal": money(q * price[code]),
                        "dTotalAmount": money(q * price[code]),
                    }
                    for i, (code, q) in enumerate(lines, 1)
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
        rec = str(900100 + n)
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
                "Articles": [
                    {
                        "CodeArticle": code,
                        "Description": prods[code]["cDescFR"],
                        "QuantiteCommandee": num(q),
                        "QuantiteRecue": num(q),
                        "PrixUnitaire": money(price[code]),
                        "Devise": "CAD",
                    }
                    for code, q in lines
                ],
                "MontantTotal": money(sub + gst + qst),
                "ResponsableReception": BUYER,
                "Commentaires": "",
                "SousTotal": money(sub),
                "Transport": "0.00",
                "TPS": money(gst),
                "TVQ": money(qst),
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
                        "dQuantite": num(q),
                        "dCoutUnitaire": money(price[code]),
                        "cGL": "",
                        "cCC1": "",
                        "cCC2": "",
                        "iNoReception": rec,
                    }
                    for code, q in lines
                ],
            }
        )
        for i, (code, q) in enumerate(lines, 1):
            p = prods[code]
            if not p["lStocked"]:
                continue  # the fryer is a fixed asset: no stock
            days = p["iShelfLifeDays"] if p["lExpiryControl"] else 0
            expiry = (date.fromisoformat(received) + timedelta(days=days)).isoformat() if days else ""
            movements.append(
                {
                    "dDate": received,
                    "cType": "IN",
                    "cProduct": code,
                    "dQty": num(q),
                    "dUnitCost": money(price[code]),
                    "cWarehouse": WH,
                    "cLocation": BOUGHT[code][4] if code in BOUGHT else "PACK-01",
                    "cWhTo": "",
                    "cLocTo": "",
                    "cLot": f"{rec}-{i}" if p["lLotControl"] else "",
                    "cSerial": "",
                    "dExpiry": expiry,
                    "cDocType": "REC",
                    "cDocNo": rec,
                    "cReason": "Réception fournisseur",
                    "cComment": inv_no,
                }
            )
    return (
        suppliers,
        {"po_details": po_details, "unbilled_po": unbilled_po},
        {"receiving_details": rec_details, "unbilled_receiving": unbilled_rec},
        invoices,
        movements,
    )


# ------------------------------------------------------------------ production

CALENDAR = {
    "cCode": "PST-1X6",
    "cDescFR": "Pâtisserie : 1 équipe, lundi au samedi",
    "cDescEN": "Pastry shop: 1 shift, Monday to Saturday",
    "lActive": True,
    "lines": [
        {"iWeekday": d, "cShift": "JOUR", "cStart": "06:00", "cEnd": "15:00", "iBreakMin": 30} for d in range(1, 7)
    ],
}
CAPABILITIES = [
    ("MIX", "Pétrissage", "Mixing"),
    ("GRIND", "Hachage", "Grinding"),
    ("COOK", "Cuisson", "Cooking"),
    ("FRY", "Friture", "Frying"),
]
WORK_CENTERS = [
    ("PST-MIXER", "Pétrin", "Dough mixer", "machine", "30", "15"),
    ("PST-GRINDER", "Hachoir à viande", "Meat grinder", "machine", "30", "10"),
    ("PST-STOVE", "Fourneaux", "Stoves", "machine", "35", "20"),
    ("PST-FRYER", "Friteuses", "Fryers", "machine", "40", "25"),
    ("PST-CREW", "Équipe de cuisine", "Kitchen crew", "labor", "24", "0"),
]
RESOURCES = [
    ("MIXER1", "Pétrin spirale 20 kg", "Spiral mixer 20 kg", "PST-MIXER", "MIX", 1),
    ("GRINDER1", "Hachoir à viande 22", "Meat grinder #22", "PST-GRINDER", "GRIND", 1),
    ("STOVE1", "Fourneau 6 feux", "6-burner range", "PST-STOVE", "COOK", 4),
    ("FRYER1", "Friteuse 2 bacs (1)", "Fryer, 2 tanks (1)", "PST-FRYER", "FRY", 2),
    ("FRYER2", "Friteuse 2 bacs (2)", "Fryer, 2 tanks (2)", "PST-FRYER", "FRY", 2),
]
# code, FR, EN, work center, capability, run format, setup, run value, crew, FR / EN instruction
OPERATIONS = [
    ("PST-WEIGH", "Pesée des ingrédients", "Weighing the ingredients", "PST-CREW", "", "min_per_lot", "0", "10", 1),
    ("PST-MIX", "Pétrissage de la pâte", "Mixing the dough", "", "MIX", "min_per_lot", "5", "15", 1),
    ("PST-REST", "Repos de la pâte", "Resting the dough", "PST-CREW", "", "min_per_lot", "0", "30", 0),
    ("PST-GRIND", "Hachage de la viande", "Grinding the meat", "", "GRIND", "min_per_lot", "10", "20", 1),
    ("PST-COOK", "Cuisson", "Cooking", "", "COOK", "min_per_lot", "5", "40", 1),
    ("PST-BOIL", "Cuisson des œufs", "Boiling the eggs", "", "COOK", "min_per_lot", "5", "12", 1),
    ("PST-CHOP", "Hachage des œufs", "Chopping the eggs", "PST-CREW", "", "min_per_lot", "0", "15", 1),
    ("PST-SHRED", "Effilochage du poulet", "Shredding the chicken", "PST-CREW", "", "min_per_lot", "0", "30", 2),
    ("PST-BLEND", "Mélange de la garniture", "Mixing the filling", "PST-CREW", "", "min_per_lot", "0", "10", 1),
    (
        "PST-SHAPE",
        "Abaisse, garniture et fermeture",
        "Rolling, filling and sealing",
        "PST-CREW",
        "",
        "units_per_hour",
        "10",
        "240",
        2,
    ),
    ("PST-FRY", "Friture", "Frying", "", "FRY", "units_per_hour", "15", "300", 1),
    ("PST-PACK", "Mise en sac", "Bagging", "PST-CREW", "", "units_per_hour", "0", "600", 1),
]


def production(prods: dict[str, dict]) -> dict:
    work_centers = [
        full(
            S.WORK_CENTER,
            {
                "cCode": code,
                "cDescFR": fr,
                "cDescEN": en,
                "cType": kind,
                "cCalendar": "PST-1X6",
                "lFinite": kind != "labor",
                "dEfficiencyPct": "100",
                "dUtilizationPct": "90" if kind != "labor" else "100",
                "dSetupRateHr": "0" if kind == "labor" else setup_rate,
                "dRunRateHr": run_rate if kind != "labor" else setup_rate,
                "dBurdenRateHr": "0" if kind == "labor" else "10",
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
        for code in [*MADE, *FINISHED]
    ]
    return {
        "_comment": "Pastry shop demo (tools/make_pastry_data.py): three pastels made from purchased raw food.",
        "capabilities": [{"cCode": c, "cDescFR": fr, "cDescEN": en, "lActive": True} for c, fr, en in CAPABILITIES],
        "setup_families": [],
        "downtime_reasons": [
            {
                "cCode": "CLEAN",
                "cDescFR": "Nettoyage",
                "cDescEN": "Cleaning",
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
            {"cCode": "BURNT", "cDescFR": "Trop cuit", "cDescEN": "Overcooked", "cGroup": "process", "lActive": True},
            {
                "cCode": "OPEN",
                "cDescFR": "Pastel ouvert",
                "cDescEN": "Pastel open",
                "cGroup": "process",
                "lActive": True,
            },
        ],
        "calendars": [CALENDAR],
        "calendar_exceptions": [
            {
                "cCalendar": "*",
                "dDate": "2026-12-25",
                "cDescFR": "Noël",
                "cDescEN": "Christmas",
                "lClosed": True,
                "cStart": "",
                "cEnd": "",
                "iBreakMin": 0,
            },
        ],
        "work_centers": work_centers,
        "resources": resources,
        "operations": operations,
        "setup_matrices": [],
        "product_mfg": product_mfg,
        "recipes": recipes(),
    }


def material(seq: int, item: str, qty: float, op: int, method: str = "manual") -> dict:
    return {"iSeq": seq, "cComponent": item, "dQtyPer": num(qty), "iOpSeq": op, "cIssueMethod": method}


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
        "dApprovedAt": "2026-11-16T09:00:00",
        "cChangeReason": "Première version",
        "dEffectiveFrom": "2026-11-16",
        "history": [
            {
                "dAt": "2026-11-15T14:00:00",
                "cUser": "demo",
                "cAction": "submit",
                "cFrom": "draft",
                "cTo": "in_review",
                "cComment": "",
            },
            {
                "dAt": "2026-11-16T09:00:00",
                "cUser": "admin",
                "cAction": "approve",
                "cFrom": "in_review",
                "cTo": "approved",
                "cComment": "",
            },
        ],
    }


def pastel(product: str, fillings: list[tuple[str, float]], filling_title: tuple[str, str]) -> dict:
    mats = [material(10, "DOUGH", 6, 10)]
    mats += [material(20 + 10 * i, item, qty, 10) for i, (item, qty) in enumerate(fillings)]
    mats += [material(80, "OIL-FRY", 2, 20, "backflush"), material(90, "PAPER-BAG", 100, 30, "backflush")]
    return recipe(
        product,
        "discrete",
        100,
        mats,
        [op(10, "PST-SHAPE"), op(20, "PST-FRY", "FRYER1"), op(30, "PST-PACK")],
        [
            step(
                10,
                10,
                "material_add",
                "Abaisser la pâte (lire le lot)",
                "Roll the dough (scan the lot)",
                iMaterialSeq=10,
            ),
            step(10, 20, "material_add", filling_title[0], filling_title[1], iMaterialSeq=20),
            step(10, 30, "check", "Pastels bien fermés", "Pastels well sealed", lRequired=True),
            step(
                20,
                10,
                "parameter",
                "Température de l'huile",
                "Oil temperature",
                cParam="TEMP_HUILE",
                cUOM="°C",
                dTarget="180",
                dMin="175",
                dMax="185",
                lRequired=True,
            ),
            step(20, 20, "timer", "Frire 3 minutes", "Fry for 3 minutes", dDurationMin="3"),
            step(30, 10, "output", "Déclarer la production", "Report the production"),
        ],
        "Une fournée = 100 pastels de 60 g de pâte et 80 g de garniture.",
    )


def recipes() -> list[dict]:
    core = {"cUOM": "°C", "lRequired": True, "lCritical": True, "cOnFail": "hold_lot", "cFrequency": "per_lot"}
    return [
        recipe(
            "DOUGH",
            "batch",
            10,
            [material(10, "FLOUR", 6, 10), material(20, "SALT", 0.12, 10), material(30, "OIL-FRY", 0.4, 10)],
            [op(10, "PST-WEIGH"), op(20, "PST-MIX", "MIXER1"), op(30, "PST-REST")],
            [
                step(
                    10,
                    10,
                    "material_add",
                    "Peser la farine (lire le lot)",
                    "Weigh the flour (scan the lot)",
                    iMaterialSeq=10,
                ),
                step(
                    20,
                    10,
                    "parameter",
                    "Ajouter l'eau tiède",
                    "Add warm water",
                    cParam="EAU",
                    cUOM="L",
                    dTarget="3.6",
                    dMin="3.4",
                    dMax="3.8",
                    lRequired=True,
                ),
                step(20, 20, "timer", "Pétrir 15 minutes", "Mix for 15 minutes", dDurationMin="15"),
                step(30, 10, "timer", "Repos de la pâte", "Rest the dough", dDurationMin="30"),
            ],
            "10 kg de pâte : 6 kg de farine et 3,6 L d'eau.",
        ),
        recipe(
            "GROUND-BEEF",
            "batch",
            10,
            [
                material(10, "BEEF-RAW", 12, 10),
                material(20, "ONION", 1.5, 20),
                material(30, "SEASONING", 0.15, 20),
                material(40, "SALT", 0.1, 20),
            ],
            [op(10, "PST-GRIND", "GRINDER1"), op(20, "PST-COOK", "STOVE1")],
            [
                step(
                    10,
                    10,
                    "material_add",
                    "Hacher le bœuf (lire le lot)",
                    "Grind the beef (scan the lot)",
                    iMaterialSeq=10,
                ),
                step(
                    20, 10, "measure", "Température à cœur", "Core temperature", cParam="TEMP_COEUR", dMin="71", **core
                ),
            ],
            "12 kg de bœuf cru donnent 10 kg de bœuf haché cuit.",
        ),
        recipe(
            "BOILED-EGG",
            "batch",
            60,
            [material(10, "EGG", 60, 10)],
            [op(10, "PST-BOIL", "STOVE1"), op(20, "PST-CHOP")],
            [step(10, 10, "timer", "Cuire 10 minutes", "Boil for 10 minutes", dDurationMin="10")],
        ),
        recipe(
            "FILL-BEEF-EGG",
            "batch",
            10,
            [material(10, "GROUND-BEEF", 8.5, 10), material(20, "BOILED-EGG", 25, 10)],
            [op(10, "PST-BLEND")],
            [],
        ),
        recipe(
            "CHICKEN-COOKED",
            "batch",
            10,
            [material(10, "CHICKEN-RAW", 16, 10), material(20, "SALT", 0.1, 10)],
            [op(10, "PST-COOK", "STOVE1")],
            [step(10, 10, "measure", "Température à cœur", "Core temperature", cParam="TEMP_COEUR", dMin="74", **core)],
            "16 kg de poulet entier donnent 10 kg de poulet cuit sans os.",
        ),
        recipe(
            "CHICKEN-SHRED",
            "batch",
            10,
            [
                material(10, "CHICKEN-COOKED", 9.5, 10),
                material(20, "ONION", 0.8, 20),
                material(30, "SEASONING", 0.1, 20),
            ],
            [op(10, "PST-SHRED"), op(20, "PST-COOK", "STOVE1")],
            [],
        ),
        pastel("PASTEL-BEEF", [("FILL-BEEF-EGG", 8)], ("Garnir : bœuf et œuf", "Fill: beef and egg")),
        pastel("PASTEL-CHICKEN", [("CHICKEN-SHRED", 8)], ("Garnir : poulet", "Fill: chicken")),
        pastel(
            "PASTEL-HAM-CHEESE",
            [("HAM", 4), ("CHEESE", 4)],
            ("Garnir : jambon et fromage", "Fill: ham and cheese"),
        ),
    ]


# ------------------------------------------------------------------ finished pastels (sales demo)

# The pastels made before the demo starts (there are no production orders yet: M3), so that the sales invoices of
# data/pastry/sales.json can be posted: one lot per day of production, at the shop's counter.
MADE_BEFORE = [  # (product, quantity, unit cost)
    ("PASTEL-BEEF", 120, "2.10"),
    ("PASTEL-CHICKEN", 120, "1.85"),
    ("PASTEL-HAM-CHEESE", 90, "1.95"),
]


def finished_goods() -> list[dict]:
    return [
        {
            "dDate": day,
            "cType": "IN",
            "cProduct": code,
            "dQty": num(qty // 2),
            "dUnitCost": cost,
            "cWarehouse": WH,
            "cLocation": "SHOP-01",
            "cWhTo": "",
            "cLocTo": "",
            "cLot": f"{code.split('-', 1)[1]}-{day.replace('-', '')}",
            "cSerial": "",
            "dExpiry": "",
            "cDocType": "PROD",
            "cDocNo": "",
            "cReason": "Production (stock initial)",
            "cComment": "",
        }
        for day in ("2026-11-18", "2026-11-19")
        for code, qty, cost in MADE_BEFORE
    ]


# ------------------------------------------------------------------ files


def main() -> None:
    prods = products()
    by_code = {p["cCode"]: p for p in prods}
    suppliers, pos, recs, invoices, movements = build_purchases(by_code)
    movements += finished_goods()
    inventory = {
        "_about": "Pastry shop demo (tools/make_pastry_data.py). Taxes and units come from data/inventory.json.",
        "categories": [
            {"cCode": c, "cDescFR": fr, "cDescEN": en, "cParent": parent, "lActive": True}
            for c, fr, en, parent in CATEGORIES
        ],
        "warehouses": [
            full(
                S.WAREHOUSE,
                {
                    "cCode": WH,
                    "cNameFR": "Cuisine centrale - Pâtisserie",
                    "cNameEN": "Central kitchen - Pastry shop",
                    "cType": "main",
                    "cAddress1": "4520, rue Saint-Denis",
                    "cCity": "Montréal",
                    "cProvince": "QC",
                    "cZipCode": "H2J 2L3",
                    "cCountry": "CA",
                    "cManager": BUYER,
                    "lUseLocations": True,
                    "cReceivingLoc": "REC",
                    "cShippingLoc": "SHOP-01",
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
                    "lMixLots": True,
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
                    "cDefaultLocation": BOUGHT[code][4],
                    "iLeadTimeDays": 1,
                    "lActive": True,
                },
            )
            for code, rp, mx in [
                ("BEEF-RAW", 15, 50),
                ("CHICKEN-RAW", 20, 60),
                ("EGG", 120, 480),
                ("FLOUR", 25, 125),
                ("OIL-FRY", 20, 80),
            ]
        ],
        "movements": movements,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    files = {
        "inventory.json": inventory,
        "production.json": production(by_code),
        "suppliers.json": suppliers,
        "purchase_orders.json": pos,
        "receptions.json": recs,
        "invoices.json": invoices,
    }
    for name, data in files.items():
        (OUT / name).write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{OUT}: {len(prods)} products, {len(movements)} movements, {len(invoices)} invoices")


if __name__ == "__main__":
    main()
