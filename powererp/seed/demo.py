"""The demonstration dataset: data/*.json (full) or data/demo/*.json (ERP_DATASET=demo, fictitious data).

Same shapes as the PowerWARE / SkyAI feeds. data/demo/history.json (tools/make_history_data.py) adds suppliers and
closed POs / receptions / invoices for the supplier selection of SkyAI requisitions.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

DATA_ROOT = Path(__file__).resolve().parent.parent.parent / "data"


@dataclass
class DemoData:
    folder: Path
    lists: dict
    inventory: (
        dict  # data/inventory.json: taxes, units, categories, warehouses, products, opening stock (both datasets)
    )
    production: dict  # data/production.json: shop floor reference lists of a paper, a food and a metal plant

    @property
    def name(self) -> str:
        """Name of the dataset, saved in the settings: the database is re-seeded when it changes."""
        return self.folder.name + ("+history" if (self.folder / "history.json").exists() else "")

    @classmethod
    def load(cls, dataset: str | None = None) -> DemoData:
        dataset = (dataset if dataset is not None else os.environ.get("ERP_DATASET", "")).strip().lower()
        demo = dataset == "demo"
        folder = DATA_ROOT / "demo" if demo else DATA_ROOT

        def read(name):
            with open(folder / name, encoding="utf-8") as f:
                return json.load(f)

        po, rec = read("purchase_orders.json"), read("receptions.json")
        lists = {
            "gl_ttGL_data": read("gl_accounts.json"),
            "gl_ttCC_data": read("cost_centers.json"),
            "supplier_terms_data": read("suppliers.json"),
            "po_details": po["po_details"],
            "unbilled_po": po["unbilled_po"],
            "receiving_details": rec["receiving_details"],
            "unbilled_receiving": rec["unbilled_receiving"],
            **({"seed_invoices": []} if demo else {}),
        }
        if (folder / "history.json").exists():
            hist = read("history.json")
            codes = {s["cCode"] for s in lists["supplier_terms_data"]}
            lists["supplier_terms_data"] += [s for s in hist["suppliers"] if s["cCode"] not in codes]
            lists["po_details"] = hist["po_details"] + lists["po_details"]
            lists["receiving_details"] = hist["receiving_details"] + lists["receiving_details"]
            lists["seed_invoices"] = hist["invoices"] + lists.get("seed_invoices", [])
        inv_file = DATA_ROOT / "inventory.json"
        inventory = json.loads(inv_file.read_text(encoding="utf-8")) if inv_file.exists() else {}
        prod_file = DATA_ROOT / "production.json"
        production = json.loads(prod_file.read_text(encoding="utf-8")) if prod_file.exists() else {}
        # the items of the production demo (paper, bakery, metal) join the item master
        for key, rows in production.get("inventory", {}).items():
            inventory[key] = inventory.get(key, []) + rows
        return cls(folder, lists, inventory, production)
