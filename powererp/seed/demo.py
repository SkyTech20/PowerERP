"""The demonstration dataset: data/*.json (full) or data/demo/*.json (ERP_DATASET=demo, fictitious data).

Scenario (chosen on the dashboard when the demo data is reset, ERP_SCENARIO for the first start):
    purchasing      SkyAI: GL, suppliers, products, POs, receptions, invoices and stock, nothing of production
    manufacturing   the same, plus the shop floor of a paper, a food and a metal plant (data/production.json)
    maple           the default: a maple products company (data/maple, tools/make_maple_data.py): its own
                    suppliers, items, recipes, shop floor, customers and price lists; story.json adds two months
                    played through the ERP (production orders, posted sales invoices, lot status, nonconformances)

Every scenario has a company profile, customers, price lists and sales invoices (data/sales.json; the maple
products company: data/maple/sales.json and story.json).

Same shapes as the PowerWARE / SkyAI feeds. data/demo/history.json (tools/make_history_data.py) adds suppliers and
closed POs / receptions / invoices for the supplier selection of SkyAI requisitions.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path

DATA_ROOT = Path(__file__).resolve().parent.parent.parent / "data"
SCENARIOS = ("maple", "purchasing", "manufacturing")
MAPLE = DATA_ROOT / "maple"
# what the maple products company keeps from data/inventory.json: taxes and units
SHARED_INVENTORY = ("tax_codes", "tax_groups", "uom", "uom_conversions")
DEFAULT_SCENARIO = "maple"


def scenario_or_default(scenario: str | None) -> str:
    """The scenario asked for, else ERP_SCENARIO, else maple (an unknown value falls back too)."""
    for value in (scenario, os.environ.get("ERP_SCENARIO")):
        value = (value or "").strip().lower()
        if value in SCENARIOS:
            return value
    return DEFAULT_SCENARIO


@dataclass
class DemoData:
    folder: Path
    lists: dict
    inventory: (
        dict  # data/inventory.json: taxes, units, categories, warehouses, products, opening stock (both datasets)
    )
    production: dict  # data/production.json: shop floor reference lists of a paper, a food and a metal plant
    sales: dict  # data/sales.json (data/maple/sales.json): company profile and customers
    scenario: str = DEFAULT_SCENARIO
    # tables as they are after the story of the scenario (data/maple/story.json): they replace their seed
    story: dict = field(default_factory=dict)

    @property
    def name(self) -> str:
        """Name of the dataset, saved in the settings: the database is re-seeded when it changes."""
        history = "+history" if (self.folder / "history.json").exists() else ""
        return f"{self.folder.name}{history}:{self.scenario}"

    @classmethod
    def load(cls, dataset: str | None = None, scenario: str | None = None) -> DemoData:
        scenario = scenario_or_default(scenario)
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
        production = {}
        if scenario == "manufacturing" and prod_file.exists():
            production = json.loads(prod_file.read_text(encoding="utf-8"))
        # the items of the production demo (paper, bakery, metal) join the item master
        for key, rows in production.get("inventory", {}).items():
            inventory[key] = inventory.get(key, []) + rows
        sales_file = (MAPLE if scenario == "maple" else DATA_ROOT) / "sales.json"
        sales = json.loads(sales_file.read_text(encoding="utf-8")) if sales_file.exists() else {}
        story: dict = {}
        if scenario == "maple":
            lists, inventory, production = cls._maple(lists, inventory)
            story_file = MAPLE / "story.json"
            if story_file.exists():
                story = {k: v for k, v in json.loads(story_file.read_text(encoding="utf-8")).items() if k[0] != "_"}
        return cls(folder, lists, inventory, production, sales, scenario, story)

    @staticmethod
    def _maple(lists: dict, inventory: dict) -> tuple[dict, dict, dict]:
        """GL and cost centres of the dataset; suppliers, purchases, items, stock and shop floor of the maple
        products company."""

        def read(name):
            return json.loads((MAPLE / name).read_text(encoding="utf-8"))

        po, rec = read("purchase_orders.json"), read("receptions.json")
        lists = {
            "gl_ttGL_data": lists["gl_ttGL_data"],
            "gl_ttCC_data": lists["gl_ttCC_data"],
            "supplier_terms_data": read("suppliers.json"),
            "po_details": po["po_details"],
            "unbilled_po": po["unbilled_po"],
            "receiving_details": rec["receiving_details"],
            "unbilled_receiving": rec["unbilled_receiving"],
            "seed_invoices": read("invoices.json"),
        }
        own = read("inventory.json")
        inventory = {k: v for k, v in inventory.items() if k in SHARED_INVENTORY} | own
        return lists, inventory, read("production.json")
