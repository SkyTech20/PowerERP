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
