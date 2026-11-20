"""Production API (M0): the reference lists of the shop floor, their lookups and the demo data life cycle."""

import pytest

LISTS = [
    ("capabilities", "CNC", 10),
    ("setup-families", "FOOD-ALLERG", 6),
    ("downtime-reasons", "BRK-MECH", 11),
    ("scrap-reasons", "WEB-BREAK", 7),
]


@pytest.mark.parametrize("url, code, count", LISTS)
def test_demo_lists(client, url, code, count):
    page = client.get(f"/api/{url}?sort=cCode").get_json()
    assert page["total"] == count
    assert client.get(f"/api/{url}/{code}").get_json()["cCode"] == code


@pytest.mark.parametrize("url, code, count", LISTS)
def test_crud(client, url, code, count):
    r = client.post(f"/api/{url}", json={"cCode": "new-1", "cDescFR": "Nouveau", "cDescEN": "New"})
    assert r.status_code == 201 and r.get_json()["cCode"] == "NEW-1"  # codes in capitals
    assert client.post(f"/api/{url}", json={"cCode": "new-1", "cDescFR": "x"}).status_code == 409
    r = client.post(f"/api/{url}", json={"cCode": "X"})
    assert r.status_code == 400 and r.get_json()["field"] == "cDescFR"
    r = client.put(f"/api/{url}/NEW-1", json={"cDescFR": "Renommé", "lActive": False})
    assert r.get_json()["cDescFR"] == "Renommé" and r.get_json()["lActive"] is False
    assert client.delete(f"/api/{url}/NEW-1").status_code == 200
    assert client.get(f"/api/{url}/NEW-1").status_code == 404


def test_downtime_reason_groups(client):
    r = client.post("/api/downtime-reasons", json={"cCode": "LUNCH", "cDescFR": "Dîner", "cGroup": "planned"})
    assert r.get_json()["lAffectsOEE"] is False  # a planned stop is not lost time
    r = client.post("/api/downtime-reasons", json={"cCode": "Z", "cDescFR": "z", "cGroup": "coffee"})
    assert r.status_code == 400 and r.get_json() == {"error": "invalid_choice", "field": "cGroup"}
    planned = client.get("/api/downtime-reasons?f_cGroup=planned").get_json()["items"]
    assert {r["cCode"] for r in planned} == {"BREAK", "LUNCH", "PM"}


def test_lookups_follow_the_language_and_skip_inactive(client):
    client.put("/api/capabilities/PAINT", json={"lActive": False})
    fr = {r["code"]: r["label"] for r in client.get("/api/lookups/capabilities").get_json()}
    en = {r["code"]: r["label"] for r in client.get("/api/lookups/capabilities?lang=en").get_json()}
    assert fr["BAKE"] == "Cuisson" and en["BAKE"].startswith("Baking") and "PAINT" not in fr


def test_reset_and_clear(client):
    client.delete("/api/scrap-reasons/DIM")
    client.post("/api/clear")
    assert client.get("/api/capabilities").get_json()["total"] == 0
    client.post("/api/reset")
    assert client.get("/api/scrap-reasons/DIM").status_code == 200


def test_production_uses_the_stock_service(app):
    """The plan's rule: production posts stock movements (cDocType PROD) through the stock service."""
    from powererp import database

    stock = app.extensions["powererp"].get("stock")
    with app.test_request_context(), database.unit_of_work():
        m = stock.add(
            {
                "cType": "IN",
                "cProduct": "CLAV-SF",
                "dQty": "2",
                "cWarehouse": "ENT-01",
                "cLocation": "A-01-02-A",
                "cDocType": "PROD",
                "cDocNo": "1",
            },
            user="test",
        )
    assert m["cDocType"] == "PROD"


# ------------------------------------------------------------------ P2: calendars

WEEK = "from=2026-11-23&to=2026-11-29"  # Monday to Sunday


def test_demo_calendars_available_minutes(client):
    """3 x 450 min x 7 days; 2 x 450 x 6 days; 5 x 480 + Saturday overtime 300."""
    mins = {
        c: client.get(f"/api/calendars/{c}/availability?{WEEK}").get_json() for c in ("PAP-24-7", "BAK-2X6", "MET-1X5")
    }
    assert {c: m["iMinutes"] for c, m in mins.items()} == {"PAP-24-7": 9450, "BAK-2X6": 5400, "MET-1X5": 2700}
    sat = mins["MET-1X5"]["days"][5]
    assert sat["cException"].startswith("Heures supp") and sat["shifts"] == [
        {"cShift": "*", "cStart": "07:00", "cEnd": "12:00", "iMinutes": 300}
    ]
    xmas = client.get("/api/calendars/PAP-24-7/availability?from=2026-12-25&to=2026-12-25").get_json()
    assert xmas["iMinutes"] == 0 and xmas["days"][0]["lClosed"]  # "*" closes every calendar


def test_calendar_list_and_crud(client):
    rows = client.get("/api/calendars").get_json()["items"]
    assert {r["cCode"]: r["iWeekMinutes"] for r in rows}["MET-1X5"] == 2400 and "lines" not in rows[0]
    body = {
        "cCode": "nuit",
        "cDescFR": "Nuit",
        "lines": [{"iWeekday": 5, "cStart": "22:00", "cEnd": "6:00", "iBreakMin": 30}],
    }
    r = client.post("/api/calendars", json=body)
    assert r.status_code == 201 and r.get_json()["lines"][0]["cEnd"] == "06:00"
    bad = {**body, "cCode": "X", "lines": body["lines"] + [{"iWeekday": 6, "cStart": "05:00", "cEnd": "08:00"}]}
    r = client.post("/api/calendars", json=bad)
    assert r.status_code == 400 and r.get_json()["error"] == "shift_overlap"
    r = client.get("/api/calendars/NUIT/availability?from=2026-11-27&to=2026-11-27").get_json()
    assert r["iMinutes"] == 450
    client.post("/api/calendar-exceptions", json={"cCalendar": "NUIT", "dDate": "2026-11-27", "cDescFR": "Fermé"})
    assert client.delete("/api/calendars/NUIT").status_code == 200
    assert client.get("/api/calendar-exceptions/NUIT/2026-11-27").status_code == 404  # gone with the calendar


def test_calendar_exceptions_api(client):
    r = client.post(
        "/api/calendar-exceptions",
        json={
            "cCalendar": "MET-1X5",
            "dDate": "2026-12-31",
            "cDescFR": "Court",
            "lClosed": False,
            "cStart": "07:00",
            "cEnd": "11:00",
        },
    )
    assert r.status_code == 201
    assert (
        client.post(
            "/api/calendar-exceptions", json={"cCalendar": "met-1x5", "dDate": "2026-12-31", "cDescFR": "x"}
        ).status_code
        == 409
    )
    r = client.get("/api/calendar-exceptions?f_cCalendar=*").get_json()
    assert [e["dDate"] for e in r["items"]] == ["2026-12-25"]
    assert client.get("/api/calendars/MET-1X5/availability?from=2026-12-31&to=2026-12-31").get_json()["iMinutes"] == 240
    r = client.get("/api/calendars/MET-1X5/availability?from=nope")
    assert r.status_code == 400 and r.get_json()["field"] == "from"
    assert client.get("/api/calendars/NOPE/availability").status_code == 404
    assert any(x["code"] == "PAP-24-7" for x in client.get("/api/lookups/calendars").get_json())


# ------------------------------------------------------------------ P3: work centers


def test_demo_work_centers(client):
    page = client.get("/api/work-centers?sort=cCode&size=50").get_json()
    assert page["total"] == 11
    cnc = client.get("/api/work-centers/MET-CNC").get_json()
    assert (cnc["cCalendar"], cnc["dUtilizationPct"], cnc["cInLocation"]) == ("MET-1X5", "85", "A-01-01-A")
    crews = client.get("/api/work-centers?f_cType=labor").get_json()["items"]
    assert {w["cCode"] for w in crews} == {"BAK-EQUIPE", "MET-SOUD", "MET-CQ"}


def test_work_center_capacity(client):
    """MET-1X5 gives 2,700 min that week (2,400 + 300 of overtime); the CNC centers are 85 % utilized."""
    r = client.get(f"/api/work-centers/MET-CNC/availability?{WEEK}").get_json()
    assert (r["cWorkCenter"], r["iMinutes"], r["iCapacityMinutes"]) == ("MET-CNC", 2700, 2295)


def test_work_center_crud_and_calendar_in_use(client):
    body = {
        "cCode": "met-laser",
        "cDescFR": "Découpe laser",
        "cCalendar": "MET-1X5",
        "cWarehouse": "ENT-01",
        "cOutLocation": "exp-01",
    }
    r = client.post("/api/work-centers", json=body)
    assert r.status_code == 201 and (r.get_json()["cCode"], r.get_json()["cOutLocation"]) == ("MET-LASER", "EXP-01")
    r = client.post("/api/work-centers", json={**body, "cCode": "X", "cCalendar": "NOPE"})
    assert r.status_code == 400 and r.get_json() == {"error": "unknown_ref", "field": "cCalendar"}
    # a calendar used by a work center cannot be deleted
    assert client.delete("/api/calendars/MET-1X5").status_code == 409
    assert client.delete("/api/work-centers/MET-LASER").status_code == 200
    assert any(x["code"] == "MET-CNC" for x in client.get("/api/lookups/work_centers").get_json())


def test_subcontract_work_center(client):
    sup = client.get("/api/suppliers?size=1").get_json()["items"][0]["cCode"]
    r = client.post(
        "/api/work-centers",
        json={"cCode": "TRT", "cDescFR": "Traitement thermique", "cType": "subcontract", "cSupplier": sup},
    )
    assert r.status_code == 201 and r.get_json()["lFinite"] is False
    r = client.get("/api/work-centers/TRT/availability")
    assert r.status_code == 400 and r.get_json()["error"] == "no_calendar"


# ------------------------------------------------------------------ P4: resources


def test_demo_resources_and_child_lists(client):
    page = client.get("/api/resources?size=50").get_json()
    assert page["total"] == 14 and "capabilities" not in page["items"][0]
    reb1 = next(r for r in page["items"] if r["cCode"] == "REB1")
    assert reb1["cCapabilities"] == "WIND, CUT"
    cnc1 = client.get("/api/resources/CNC1").get_json()
    assert [a["cAttribute"] for a in cnc1["attributes"]] == ["Course X", "Course Y", "Outils"]
    assert [s["cCode"] for s in cnc1["subresources"]] == ["BROCHE", "ATC"]
    assert cnc1["downtime"][0]["cReason"] == "PM"


def test_resource_available_time(client):
    """CNC1: 2,700 min of MET-1X5 that week, minus 4 h of preventive maintenance on Wednesday; 85 % utilization."""
    r = client.get(f"/api/resources/CNC1/availability?{WEEK}").get_json()
    assert (r["iCalendarMinutes"], r["iDowntimeMinutes"], r["iMinutes"], r["iCapacityMinutes"]) == (
        2700,
        240,
        2460,
        2091,
    )
    oven = client.get(f"/api/resources/FOUR1/availability?{WEEK}").get_json()
    assert (oven["iMinutes"], oven["iCapacityMinutes"]) == (5400 - 240, round(5160 * 0.95 * 3))  # 3 trays at once


def test_resource_crud_and_references(client):
    body = {
        "cCode": "cnc3",
        "cDescFR": "Tour CNC",
        "cWorkCenter": "MET-CNC",
        "capabilities": [{"cCapability": "cnc", "iPreference": 3}],
        "subresources": [{"cCode": "mandrin", "cDescFR": "Mandrin"}],
    }
    r = client.post("/api/resources", json=body)
    assert r.status_code == 201 and r.get_json()["capabilities"] == [{"cCapability": "CNC", "iPreference": 3}]
    r = client.put("/api/resources/CNC3", json={"capabilities": [{"cCapability": "WELD"}, {"cCapability": "PAINT"}]})
    assert [c["cCapability"] for c in r.get_json()["capabilities"]] == ["WELD", "PAINT"]
    assert client.get("/api/resources/CNC3").get_json()["subresources"][0]["cCode"] == "MANDRIN"  # left as it was
    r = client.post("/api/resources", json={**body, "cCode": "X", "cWorkCenter": "NOPE"})
    assert r.status_code == 400 and r.get_json() == {"error": "unknown_ref", "field": "cWorkCenter"}
    # what the resources use cannot be deleted
    assert client.delete("/api/work-centers/MET-CNC").status_code == 409
    assert client.delete("/api/capabilities/CNC").status_code == 409
    assert client.delete("/api/downtime-reasons/PM").status_code == 409
    assert client.delete("/api/resources/CNC3").status_code == 200


def test_resources_of_a_capability(client):
    r = client.get("/api/capabilities/WIND/resources").get_json()
    assert [x["cCode"] for x in r] == ["REB1", "REB2"]  # preferred first
    assert client.get("/api/capabilities/NOPE/resources").status_code == 404


# ------------------------------------------------------------------ P5: standard operations


def test_demo_operations(client):
    page = client.get("/api/operations?size=50").get_json()
    assert page["total"] == 12
    usin = client.get("/api/operations/MET-USIN").get_json()
    assert (usin["cCapability"], usin["cRunFormat"], usin["dRunValue"]) == ("CNC", "min_per_unit", "6.5")


def test_operation_time(client):
    """MET-USIN: 45 min setup + 6.5 min per part; on CNC2 (speed 0.85, work center at 100 %)."""
    r = client.get("/api/operations/MET-USIN/time?qty=100").get_json()
    assert (r["dSetupMin"], r["dRunMin"], r["dTotalMin"]) == (45, 650, 695)
    r = client.get("/api/operations/MET-USIN/time?qty=100&resource=CNC2").get_json()
    assert r["dRunMin"] == round(650 / 0.85, 2)
    r = client.get("/api/operations/BAK-CUISS/time?qty=600&lot=200").get_json()
    assert r["dRunMin"] == 75  # 3 batches of 25 min
    assert client.get("/api/operations/MET-USIN/time?qty=abc").status_code == 400
    assert client.get("/api/operations/MET-USIN/time?resource=NOPE").status_code == 404


def test_operation_crud_and_references(client):
    r = client.post(
        "/api/operations", json={"cCode": "met-ebav", "cDescFR": "Ébavurage", "cCapability": "cnc", "dRunValue": "1.5"}
    )
    assert r.status_code == 201 and r.get_json()["cCapability"] == "CNC"
    r = client.post("/api/operations", json={"cCode": "X", "cDescFR": "x"})
    assert r.status_code == 400 and r.get_json()["error"] == "work_center_or_capability"
    assert client.delete("/api/work-centers/MET-PEINT").status_code == 409  # MET-PEINT runs there
    assert client.delete("/api/operations/MET-EBAV").status_code == 200
    assert any(x["code"] == "MET-USIN" for x in client.get("/api/lookups/operations").get_json())


# ------------------------------------------------------------------ P6: setup matrix


def test_demo_setup_matrices(client):
    page = client.get("/api/setup-matrices").get_json()
    assert page["total"] == 5 and {r["cScopeCode"]: r["iPairs"] for r in page["items"]}["PAP-MP"] == 4


def test_changeover_lookup(client):
    r = client.get("/api/setup-changeover?from=PAP-COLOR&to=PAP-WHITE&workCenter=PAP-MP").get_json()
    assert (r["dSetupMin"], r["dScrapQty"], r["cRule"]) == (45, 1200, "matrix")
    # REB2 has its own matrix; REB1 uses the work center's
    assert client.get("/api/setup-changeover?from=PAP-WHITE&to=PAP-COLOR&resource=REB2").get_json()["dSetupMin"] == 45
    assert client.get("/api/setup-changeover?from=PAP-WHITE&to=PAP-COLOR&resource=REB1").get_json()["dSetupMin"] == 30
    # allergens: the cleaning goes one way only
    r = client.get("/api/setup-changeover?from=FOOD-ALLERG&to=FOOD-PLAIN&resource=PET1").get_json()
    assert (r["dSetupMin"], r["cScope"]) == (60, "work_center")
    r = client.get("/api/setup-changeover?from=MET-STEEL&to=MET-STEEL&resource=CNC1&default=45").get_json()
    assert (r["dSetupMin"], r["cRule"]) == (0, "same_family")


def test_setup_matrix_crud_grid_and_references(client):
    r = client.post(
        "/api/setup-matrices",
        json={
            "cScope": "resource",
            "cScopeCode": "cnc2",
            "lines": [{"cFromFamily": "met-steel", "cToFamily": "met-alu", "dSetupMin": "15"}],
        },
    )
    assert r.status_code == 201 and r.get_json()["lines"][0]["cToFamily"] == "MET-ALU"
    assert client.post("/api/setup-matrices", json={"cScope": "resource", "cScopeCode": "CNC2"}).status_code == 409
    g = client.get("/api/setup-matrices/resource/CNC2/grid?default=45").get_json()
    i, j = g["families"].index("MET-STEEL"), g["families"].index("MET-ALU")
    assert g["cells"][i][j]["dSetupMin"] == 15 and g["cells"][j][i]["dSetupMin"] == 45
    assert client.delete("/api/setup-families/MET-ALU").status_code == 409  # used by a matrix
    assert client.delete("/api/setup-matrices/resource/CNC2").status_code == 200


# ------------------------------------------------------------------ P7: manufacturing data of the products


def test_demo_items_join_the_item_master(client):
    assert client.get("/api/products/PAIN-BL-675").get_json()["cCategory"] == "BOUL"
    assert client.get("/api/products/LAP-14I7").status_code == 200  # the inventory demo is still there
    page = client.get("/api/product-mfg?size=50").get_json()
    assert page["total"] == 8 and "attributes" not in page["items"][0]
    bread = client.get("/api/product-mfg/PAIN-GR-600").get_json()
    assert (bread["cSetupFamily"], bread["cDescFR"], bread["cTraceLevel"]) == (
        "FOOD-ALLERG",
        "Pain aux graines 600 g (sésame)",
        "lot",
    )
    assert [a["cAttribute"] for a in bread["attributes"]] == ["Poids", "Allergènes"]


def test_product_mfg_crud_and_rules(client):
    r = client.post("/api/product-mfg", json={"cProduct": "LAP-14I7", "cMakeBuy": "buy", "cTraceLevel": "lot"})
    assert r.status_code == 400 and r.get_json() == {"error": "lot_control_required", "field": "cTraceLevel"}
    r = client.post("/api/product-mfg", json={"cProduct": "lap-14i7", "cMakeBuy": "buy", "cTraceLevel": "none"})
    assert r.status_code == 201 and r.get_json()["cProduct"] == "LAP-14I7"
    assert client.post("/api/product-mfg", json={"cProduct": "LAP-14I7", "cTraceLevel": "none"}).status_code == 409
    assert client.delete("/api/setup-families/FOOD-ALLERG").status_code == 409  # a product uses it


def test_manufacturing_data_go_with_the_product(client):
    client.post("/api/products", json={"cCode": "TEST-MFG", "cDescFR": "Test", "cStockUOM": "UN", "lLotControl": True})
    client.post("/api/product-mfg", json={"cProduct": "TEST-MFG"})
    assert client.delete("/api/products/TEST-MFG").status_code == 200
    assert client.get("/api/product-mfg/TEST-MFG").status_code == 404


# ------------------------------------------------------------------ P8: recipes


def test_demo_recipes(client):
    page = client.get("/api/recipes?size=50").get_json()
    assert page["total"] == 6 and "materials" not in page["items"][0]
    bread = client.get("/api/recipes/PAIN-BL-675/A").get_json()
    assert [op["cOperation"] for op in bread["operations"]] == [
        "BAK-PESEE",
        "BAK-PETRIS",
        "BAK-FERM",
        "BAK-CUISS",
        "BAK-EMB",
    ]
    # the empty fields of the demo took the standard operation's values
    assert (bread["operations"][1]["cDescFR"], bread["operations"][1]["cWorkCenter"]) == ("Pétrissage", "BAK-PETRIN")
    assert bread["operations"][2]["dMinWaitMin"] == "60" and bread["materials"][0]["cUOM"] == "KG"


def test_recipe_explosion(client):
    """400 white breads = 2 batches of 200, 98 % yield: flour 85 x 400 / 200 / 0.98."""
    e = client.get("/api/recipes/PAIN-BL-675/A/explode?qty=400").get_json()
    assert e["iBatches"] == 2
    assert e["materials"][0]["dQty"] == round(85 * 2 / 0.98, 4)
    mix = e["operations"][1]
    assert (mix["cWhere"], mix["dSetupMin"], mix["dRunMin"]) == ("PET1", 10, 24)  # 2 batches x 12 min
    proof = e["operations"][2]
    assert proof["dCost"] == 0  # unattended (crew 0)
    assert e["dTotalCost"] == round(e["dMaterialCost"] + e["dOperationCost"], 2)
    base = client.get("/api/recipes/SUPP-ALU-01/A/explode").get_json()  # the base quantity by default
    assert base["dQty"] == 1 and base["operations"][0]["cWhere"] == "CNC (CNC1)"  # the preferred resource
    assert base["operations"][0]["dCost"] > 0


def test_recipe_crud_and_rules(client):
    body = {
        "cProduct": "supp-alu-01",
        "cRevision": "b",
        "materials": [{"cComponent": "al6061-f125-48", "dQtyPer": "0.04"}],
        "operations": [{"iOpSeq": 10, "cOperation": "met-usin", "cResource": "cnc2"}],
    }
    r = client.post("/api/recipes", json=body)
    assert r.status_code == 201
    row = r.get_json()
    assert (row["cProduct"], row["cRevision"], row["cStatus"]) == ("SUPP-ALU-01", "B", "draft")
    assert (row["operations"][0]["cWorkCenter"], row["operations"][0]["dRunValue"]) == ("MET-CNC", "6.5")
    assert client.post("/api/recipes", json=body).status_code == 409
    r = client.post("/api/recipes", json={**body, "cRevision": "C", "cProduct": "LAP-14I7"})
    assert r.status_code == 400 and r.get_json() == {"error": "not_made", "field": "cProduct"}
    r = client.put("/api/recipes/SUPP-ALU-01/B", json={"cStatus": "approved", "cNotes": "ok"})
    assert r.get_json()["cStatus"] == "draft"  # the status is not edited (approval flow, P10)
    # what a recipe uses cannot be deleted
    assert client.delete("/api/products/AL6061-F125-48").status_code == 409
    assert client.delete("/api/operations/MET-USIN").status_code == 409
    assert client.delete("/api/resources/CNC2").status_code == 409
    assert client.delete("/api/recipes/SUPP-ALU-01/B").status_code == 200
    assert client.get("/api/recipes/NOPE/A/explode").status_code == 404


# ------------------------------------------------------------------ P9: steps of the recipe operations


def test_demo_steps(client):
    bread = client.get("/api/recipes/PAIN-BL-675/A").get_json()
    assert len(bread["steps"]) == 15
    mixing = [s for s in bread["steps"] if s["iOpSeq"] == 20]
    assert [s["cKind"] for s in mixing] == ["check", "parameter", "timer", "measure", "instruction"]
    assert mixing[0]["lSecondSignature"] and mixing[4]["cCondition"] == "TEMP_PATE < 24"
    row = next(r for r in client.get("/api/recipes?size=50").get_json()["items"] if r["cProduct"] == "PAIN-BL-675")
    assert row["iSteps"] == 15 and "steps" not in row


def test_step_value_check(client):
    url = "/api/recipes/PAIN-BL-675/A/steps/check"
    r = client.post(url, json={"iOpSeq": 40, "iStep": 20, "value": "89"}).get_json()
    assert r == {"ok": False, "reason": "below_min", "action": "hold_lot"}  # core temperature: hold the lot
    assert client.post(url, json={"iOpSeq": 20, "iStep": 40, "value": "25,5"}).get_json()["ok"] is True
    assert client.post(url, json={"iOpSeq": 20, "iStep": 99, "value": "1"}).status_code == 400


def test_steps_are_saved_with_the_recipe(client):
    recipe = client.get("/api/recipes/SUPP-ALU-01/A").get_json()
    steps = recipe["steps"] + [
        {"iOpSeq": 20, "iStep": 30, "cKind": "instruction", "cTitleFR": "Retouche", "cCondition": "ASPECT = Retouche"}
    ]
    r = client.put("/api/recipes/SUPP-ALU-01/A", json={"steps": steps})
    assert r.status_code == 200 and r.get_json()["steps"][-1]["cCondition"] == "ASPECT = Retouche"
    bad = steps + [
        {"iOpSeq": 20, "iStep": 40, "cKind": "measure", "cTitleFR": "X", "cParam": "X", "dMin": "5", "dMax": "1"}
    ]
    r = client.put("/api/recipes/SUPP-ALU-01/A", json={"steps": bad})
    assert r.status_code == 400 and r.get_json()["error"] == "max_below_min"
