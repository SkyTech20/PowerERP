"""The demo data scenarios chosen in System settings: maple products (the default), SkyAI (purchasing) or
manufacturing. The maple products company: tests/test_demo_maple.py."""

from powererp import settings
from powererp.seed.demo import DemoData, scenario_or_default


def _count(client, path):
    return client.get(path + "?limit=1000").get_json()["total"]


def test_the_scenarios(monkeypatch):
    assert scenario_or_default("Purchasing") == "purchasing"
    assert scenario_or_default("bogus") == "manufacturing"  # ERP_SCENARIO of the tests
    monkeypatch.delenv("ERP_SCENARIO")
    assert scenario_or_default("bogus") == scenario_or_default(None) == "maple"  # the default
    purchasing = DemoData.load("demo", "purchasing")
    assert purchasing.production == {} and purchasing.name.endswith(":purchasing")
    codes = {p["cCode"] for p in purchasing.inventory["products"]}
    assert "LAP-14I7" in codes and "PAIN-BL-675" not in codes  # no item of the production demo


def test_reset_switches_the_scenario(admin):
    assert admin.get("/api/demo").get_json() == {
        "scenario": "manufacturing",
        "scenarios": ["maple", "purchasing", "manufacturing"],
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


def test_an_upgrade_keeps_the_scenario_the_database_was_seeded_with(app):
    """A database seeded before maple became the default (no scenario chosen in System settings) keeps its data:
    the scenario comes from the name of the dataset it was seeded with."""
    from powererp.factory import seeded_scenario

    before = settings.get_setting("dataset")
    try:
        settings.set_setting("dataset", "demo+history:manufacturing")
        assert seeded_scenario() == "manufacturing"
        settings.set_setting("dataset", "demo")  # older than the scenarios
        assert seeded_scenario() == ""
    finally:
        settings.set_setting("dataset", before)
