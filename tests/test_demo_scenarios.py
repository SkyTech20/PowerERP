"""The demo data scenarios chosen in System settings: SkyAI (purchasing), manufacturing or the pastry shop."""

from powererp import settings
from powererp.seed.demo import DemoData, scenario_or_default


def _count(client, path):
    return client.get(path + "?limit=1000").get_json()["total"]


def test_the_scenarios():
    assert scenario_or_default("Purchasing") == "purchasing"
    assert scenario_or_default("bogus") == "manufacturing"
    purchasing = DemoData.load("demo", "purchasing")
    assert purchasing.production == {} and purchasing.name.endswith(":purchasing")
    codes = {p["cCode"] for p in purchasing.inventory["products"]}
    assert "LAP-14I7" in codes and "PAIN-BL-675" not in codes  # no item of the production demo


def test_reset_switches_the_scenario(admin):
    assert admin.get("/api/demo").get_json() == {
        "scenario": "manufacturing",
        "scenarios": ["purchasing", "manufacturing", "pastry"],
    }
    products, recipes = _count(admin, "/api/products"), _count(admin, "/api/recipes")
    assert recipes > 0
    try:
        r = admin.post("/api/reset", json={"scenario": "purchasing"})
        assert r.get_json() == {"ok": True, "scenario": "purchasing"}
        assert _count(admin, "/api/recipes") == 0 and _count(admin, "/api/work-centers") == 0
        assert _count(admin, "/api/products") < products
        assert _count(admin, "/api/purchase-orders") > 0
        assert settings.get_setting("demo_scenario") == "purchasing"  # kept for the next starts
        admin.post("/api/reset")  # a reset without a scenario keeps the current one
        assert admin.get("/api/demo").get_json()["scenario"] == "purchasing"
        assert _count(admin, "/api/recipes") == 0
        assert admin.post("/api/reset", json={"scenario": "bogus"}).get_json() == {
            "error": "invalid_choice",
            "field": "scenario",
        }
    finally:
        admin.post("/api/reset", json={"scenario": "manufacturing"})
    assert _count(admin, "/api/recipes") == recipes and _count(admin, "/api/products") == products


def test_only_administrators(app, admin):
    """Administration > System settings: a user cannot reset nor clear the data."""
    admin.post("/api/users", json={"username": "ann", "name": "Ann", "password": "secret1", "role": "user"})
    c = app.test_client()
    assert c.post("/api/auth/login", json={"username": "ann", "password": "secret1"}).status_code == 200
    assert c.get("/api/demo").status_code == 403
    assert c.post("/api/reset").status_code == 403
    assert c.post("/api/clear").status_code == 403
    assert c.get("/api/summary").status_code == 200  # the dashboard stays open to every user


def test_pastry_shop(admin):
    """3 pastels; dough and fillings made from raw meat, chicken and eggs; ham and cheese bought; stock = invoices."""
    try:
        assert admin.post("/api/reset", json={"scenario": "pastry"}).get_json() == {"ok": True, "scenario": "pastry"}
        products = {p["cCode"]: p for p in admin.get("/api/products?limit=1000").get_json()["items"]}
        finished = {c for c, p in products.items() if p["cClass"] == "finished"}
        assert finished == {"PASTEL-BEEF", "PASTEL-CHICKEN", "PASTEL-HAM-CHEESE"}
        assert all(products[c]["lSellable"] for c in finished)
        for bought in ("HAM", "CHEESE", "BEEF-RAW", "CHICKEN-RAW", "EGG"):
            assert products[bought]["cClass"] == "raw" and products[bought]["lPurchasable"]
        assert products["GLOVES"]["cClass"] == "consumable" and products["FRYER-2T"]["cClass"] == "asset"
        assert "LAP-14I7" not in products  # nothing of SkyAI

        recipes = admin.get("/api/recipes?limit=1000").get_json()["items"]
        made = {r["cProduct"] for r in recipes if r["cStatus"] == "approved" and r["lDefault"]}
        assert made == finished | {
            "DOUGH",
            "GROUND-BEEF",
            "BOILED-EGG",
            "FILL-BEEF-EGG",
            "CHICKEN-COOKED",
            "CHICKEN-SHRED",
        }
        uses = {
            m["cComponent"]
            for r in recipes
            for m in admin.get(f"/api/recipes/{r['cProduct']}/{r['cRevision']}").get_json()["materials"]
        }
        assert {"BEEF-RAW", "CHICKEN-RAW", "EGG", "HAM", "CHEESE", "GROUND-BEEF", "BOILED-EGG"} <= uses

        # the stock on hand is the raw material received and invoiced (the fryer is a fixed asset, not stocked)
        invoiced = 0.0
        for inv in admin.get("/api/invoices?limit=1000").get_json()["items"]:
            assert inv["cStatut"] == "Posted"
            for line in admin.get(f"/api/invoices/{inv['id']}").get_json()["lines"]:
                if products[line["cCodeProduit"]]["lStocked"]:
                    invoiced += float(line["dQuantite"]) * float(line["dCoutUnitaire"])
        valuation = admin.get("/api/inventory/valuation?limit=1000").get_json()
        assert invoiced > 0 and float(valuation["totalValue"]) == round(invoiced, 2)
        assert _count(admin, "/api/purchase-orders") == 7  # the last meat order is still open
    finally:
        admin.post("/api/reset", json={"scenario": "manufacturing"})
