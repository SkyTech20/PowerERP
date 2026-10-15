"""
PowerERP — a small demo ERP.

All ERP menus are visible; only GL Accounts / Cost Centers, Suppliers,
Invoices, Purchase orders and Receptions have working maintenance screens.
English / French UI. The ERP also answers the PowerWARE web services used by
SkyAI (getSupplierTerm.p, getPODetails.p, apInvoiceNoPO.p, ...), so SkyAI can
read the ERP data and create its invoices here.

Run:  pip install -r requirements.txt && python app.py
Open: http://localhost:5050/
"""
import json
import os
from pathlib import Path

from flask import Flask, jsonify

from erp_api import register_erp
from powerware_api import register_powerware

DATA_DIR = Path(__file__).resolve().parent / "data"
# ERP_DATASET=demo loads the fictitious demo data in data/demo/ (rebuild.ps1 -DemoData).
DEMO = os.environ.get("ERP_DATASET", "").strip().lower() == "demo"
if DEMO:
    DATA_DIR = DATA_DIR / "demo"


def _read(name):
    with open(DATA_DIR / name, encoding="utf-8") as f:
        return json.load(f)


def load_data():
    """Load the demo data (same shapes as the PowerWARE / SkyAI feeds)."""
    po = _read("purchase_orders.json")
    rec = _read("receptions.json")
    return {
        "gl_ttGL_data": _read("gl_accounts.json"),
        "gl_ttCC_data": _read("cost_centers.json"),
        "supplier_terms_data": _read("suppliers.json"),
        "po_details": po["po_details"],
        "unbilled_po": po["unbilled_po"],
        "receiving_details": rec["receiving_details"],
        "unbilled_receiving": rec["unbilled_receiving"],
        **({"seed_invoices": []} if DEMO else {}),
    }


app = Flask(__name__)
data = load_data()
hooks = register_erp(app, data)
# PowerWARE-compatible web services, so SkyAI can read from and write to this ERP
register_powerware(app, data, hooks["invoice_exists"], hooks["record_invoice"])


@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "not_found"}), 404


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5050"))
    print(f"PowerERP: http://localhost:{port}/ (data: {DATA_DIR.name})")
    app.run(host="0.0.0.0", port=port, debug=os.environ.get("FLASK_DEBUG") == "1")
