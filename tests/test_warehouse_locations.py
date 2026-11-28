"""Inventory > Warehouses: the Locations tab and Generate locations (aisle x rack x level x bin)."""

import pytest

from powererp.core.errors import AppError
from powererp.modules.inventory.masters import expand_range


def test_ranges():
    assert expand_range("A", "C", "f") == ["A", "B", "C"]
    assert expand_range("01", "10", "f") == ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10"]
    assert expand_range("1", "3", "f") == ["1", "2", "3"]
    assert expand_range("b", "", "f") == ["B"]
    assert expand_range("", "", "f") == [""]
    for bad in (("C", "A"), ("A", "3"), ("AA", "AC"), ("5", "2")):
        with pytest.raises(AppError) as e:
            expand_range(*bad, "cRackFrom")
        assert (e.value.code, e.value.field) == ("bad_range", "cRackFrom")


def wh(client, code="MP"):
    r = client.post("/api/warehouses", json={"cCode": code, "cNameFR": "Matières premières", "cType": "main"})
    assert r.status_code == 201, r.get_json()
    return code


def test_generate_preview_then_create(client):
    code = wh(client)
    body = {"cZone": "r", "cAisleFrom": "A", "cAisleTo": "C", "cRackFrom": "01", "cRackTo": "05"}
    body.update({"cLevelFrom": "1", "cLevelTo": "4", "cType": "reserve"})
    p = client.post(f"/api/warehouses/{code}/generate-locations?preview=1", json=body)
    assert p.status_code == 200
    p = p.get_json()
    assert (p["iToCreate"], p["iCreated"], p["iSkipped"]) == (60, 0, 0)
    assert p["codes"][:2] == ["R-A-01-1", "R-A-01-2"] and p["codes"][-1] == "R-C-05-4"
    assert client.get(f"/api/locations?f_cWarehouse={code}").get_json()["total"] == 0  # a preview saves nothing

    r = client.post(f"/api/warehouses/{code}/generate-locations", json=body)
    assert r.status_code == 201 and r.get_json()["iCreated"] == 60
    loc = client.get(f"/api/locations/{code}/R-B-03-2").get_json()
    assert (loc["cZone"], loc["cAisle"], loc["cRack"], loc["cLevel"], loc["cType"]) == ("R", "B", "03", "2", "reserve")
    assert loc["lActive"] is True and loc["lMixProducts"] is True

    # the same ranges with one more aisle: only the new aisle is created, in picking order after the others
    body["cAisleTo"] = "D"
    again = client.post(f"/api/warehouses/{code}/generate-locations", json=body).get_json()
    assert (again["iCreated"], again["iSkipped"]) == (20, 60)
    rows = client.get(f"/api/locations?f_cWarehouse={code}&sort=iPickSeq&size=500").get_json()["items"]
    assert len(rows) == 80 and rows[-1]["cCode"] == "R-D-05-4"
    assert rows[-1]["iPickSeq"] > rows[59]["iPickSeq"]


def test_generate_refusals(client):
    code = wh(client, "INT")
    url = f"/api/warehouses/{code}/generate-locations?preview=1"
    assert client.post(url, json={}).get_json()["field"] == "cAisleFrom"
    r = client.post(url, json={"cAisleFrom": "A", "cAisleTo": "C", "cRackFrom": "5", "cRackTo": "1"})
    assert r.status_code == 400 and r.get_json() == {**r.get_json(), "error": "bad_range", "field": "cRackFrom"}
    big = {"cAisleFrom": "1", "cAisleTo": "50", "cRackFrom": "1", "cRackTo": "50"}
    assert client.post(url, json=big).get_json()["error"] == "too_many_locations"
    assert client.post(url, json={"cAisleFrom": "A", "cType": "x"}).get_json()["error"] == "invalid_choice"
    assert client.post("/api/warehouses/NOPE/generate-locations", json={"cAisleFrom": "A"}).status_code == 404
