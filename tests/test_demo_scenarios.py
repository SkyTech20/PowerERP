"""The demo data scenarios chosen on the dashboard: SkyAI (purchasing, no production) or manufacturing."""

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
        "scenarios": ["purchasing", "manufacturing"],
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
