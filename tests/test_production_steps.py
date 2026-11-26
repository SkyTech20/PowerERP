"""The records of the recipe steps on the shop floor (M4, step 6 of the SCOR / ISO plan): the value and the limits
kept, the corrective action of a deviation, a critical "block" step that stops the report and the completion, a
"hold the lot" step that holds the lot made, the second signature and the required role, the conditions."""

import pytest
from conftest import ADMIN_PASSWORD
from test_production_floor import _stock

URL = "/api/production-orders"
CLEAN = (20, 10)  # check, critical, block, second signature
WATER = (20, 20)  # parameter EAU 48-52
DOUGH = (20, 40)  # measure TEMP_PATE 24-26, critical, warn
COLD = (20, 50)  # instruction, only when TEMP_PATE < 24
CORE = (40, 20)  # measure TEMP_COEUR >= 92, critical, hold the lot, per lot


@pytest.fixture
def order(client):
    _stock(client)
    o = client.post(URL, json={"cProduct": "PAIN-BL-675", "dQty": "400", "dStart": "2026-12-01"}).get_json()
    assert client.post(f"{URL}/{o['iNo']}/release", json={}).status_code == 200
    return o["iNo"]


def _record(client, no, step, value="", **more):
    return client.post(f"{URL}/{no}/steps/record", json={"iOpSeq": step[0], "iStep": step[1], "cValue": value, **more})


def _step(board, step):
    return next(s for s in board["steps"] if (s["iOpSeq"], s["iStep"]) == step)


def _sign(**more):
    return {"cSecondUser": "admin", "cSecondPassword": ADMIN_PASSWORD, **more}


def test_the_board_lists_the_recipe_steps_and_a_draft_has_none(client, order):
    board = client.get(f"{URL}/{order}/steps").get_json()
    assert len(board["steps"]) == 15
    assert _step(board, WATER)["cState"] == "todo" and _step(board, COLD)["cState"] == "skipped"
    assert board["iRequired"] == 6 and board["iRequiredDone"] == 0 and board["blocking"] == []
    assert client.get(f"{URL}/{order}").get_json()["shopSteps"]["iRequired"] == 6
    draft = client.post(URL, json={"cProduct": "PAIN-BL-675", "dQty": "10", "dStart": "2026-12-01"}).get_json()
    assert "shopSteps" not in draft
    r = _record(client, draft["iNo"], WATER, "50")
    assert r.status_code == 409 and r.get_json()["error"] == "invalid_status"
    assert "records" not in client.get(URL).get_json()["items"][0]


def test_a_value_within_its_limits_is_kept_with_who_and_the_limits(client, order):
    assert _record(client, order, (99, 10), "1").status_code == 404
    assert _record(client, order, WATER).get_json()["error"] == "required"
    assert _record(client, order, WATER, "abc").get_json()["error"] == "numeric"
    o = _record(client, order, WATER, "50,5").get_json()
    rec = o["records"][0]
    assert (rec["cUser"], rec["cValue"], rec["cParam"], rec["cUOM"], rec["lOk"]) == ("api", "50,5", "EAU", "L", True)
    assert float(rec["dMin"]) == 48 and float(rec["dMax"]) == 52 and rec["dAt"]
    assert _step(o["shopSteps"], WATER)["cState"] == "done"
    # a step that records nothing (instruction, timer) is "done"
    o = _record(client, order, (10, 10)).get_json()
    assert o["records"][-1]["cValue"] == "done"


def test_a_deviation_needs_a_corrective_action_and_opens_the_conditional_step(client, order):
    r = _record(client, order, DOUGH, "22")
    assert r.status_code == 400 and r.get_json()["error"] == "corrective_action"
    assert _record(client, order, COLD).get_json()["error"] == "step_not_applicable"
    o = _record(client, order, DOUGH, "22", cComment="warm water added").get_json()
    rec = o["records"][-1]
    assert (rec["lOk"], rec["cReason"], rec["cAction"], rec["cComment"]) == (
        False,
        "below_min",
        "warn",
        "warm water added",
    )
    board = o["shopSteps"]
    assert _step(board, DOUGH)["cState"] == "deviation" and board["iDeviations"] == 1 and board["blocking"] == []
    assert _step(board, COLD)["cState"] == "todo"
    assert o["history"][-1]["cAction"] == "deviation" and "warm water added" in o["history"][-1]["cComment"]
    # a warning stops nothing; the step is done once recorded again within its limits
    assert _record(client, order, COLD).status_code == 200
    o = _record(client, order, DOUGH, "24.5").get_json()
    assert _step(o["shopSteps"], DOUGH)["cState"] == "done" and o["shopSteps"]["iDeviations"] == 1


def test_a_second_signature_needs_another_user_and_their_password(client, admin, order):
    assert _record(client, order, CLEAN, "yes").get_json()["error"] == "required"
    r = _record(client, order, CLEAN, "yes", cSecondUser="admin", cSecondPassword="wrong")
    assert r.status_code == 400 and (r.get_json()["error"], r.get_json()["field"]) == (
        "bad_signature",
        "cSecondPassword",
    )
    failed = admin.get("/api/audit?kind=security&size=50").get_json()["items"]
    assert any(e["event"] == "signature_failed" and e["username"] == "admin" for e in failed)
    # the administrator cannot sign their own record
    r = _record(admin, order, CLEAN, "yes", **_sign())
    assert r.get_json()["error"] == "same_signer"
    o = _record(client, order, CLEAN, "yes", **_sign()).get_json()
    assert o["records"][-1]["cSecondUser"] == "admin" and o["records"][-1]["cUser"] == "api"
    rows = admin.get("/api/audit?size=50").get_json()["items"]
    assert any(e["event"] == "signature_ok" and e["username"] == "admin" for e in rows)
    change = next(e for e in rows if e["kind"] == "change" and e["path"].endswith("/steps/record"))
    assert change["details"]["sent"]["cSecondPassword"] == "***"  # the password is never kept


def test_a_critical_block_step_stops_the_report_and_the_completion(client, order):
    o = _record(client, order, CLEAN, "no", **_sign(cComment="allergen residue: cleaned again")).get_json()
    assert o["shopSteps"]["blocking"] == ["20/10 Mixer clean (cleaning checked)"]
    r = client.post(f"{URL}/{order}/report", json={"dQty": "100", "dDate": "2026-12-01"})
    assert r.status_code == 409 and r.get_json()["error"] == "step_blocked"
    # recorded again within its limits: the order goes on
    _record(client, order, CLEAN, "yes", **_sign())
    assert client.post(f"{URL}/{order}/report", json={"dQty": "100", "dDate": "2026-12-01"}).status_code == 200
    _record(client, order, CLEAN, "no", **_sign(cComment="checked again: not clean"))
    r = client.post(f"{URL}/{order}/complete", json={})
    assert r.status_code == 409 and r.get_json()["error"] == "step_blocked"


def _lot_status(client, lot):
    return client.get(f"/api/lot-status/PAIN-BL-675/{lot}").get_json()["cStatus"]


def test_a_hold_the_lot_deviation_holds_the_lot_made_even_later(client, order):
    # recorded before the lot exists: the lot reported afterwards is held
    o = _record(client, order, CORE, "85", cComment="oven door open, trays baked again").get_json()
    assert o["records"][-1]["cAction"] == "hold_lot"
    client.post(f"{URL}/{order}/report", json={"dQty": "100", "dDate": "2026-12-01"})
    assert _lot_status(client, "MO1") == "on_hold"
    held = client.get("/api/lot-status/PAIN-BL-675/MO1").get_json()
    assert "Core temperature" in held["cReason"]
    # quality releases it; a second report of the same lot does not hold it again
    assert (
        client.post("/api/lot-status/PAIN-BL-675/MO1", json={"cStatus": "released", "cReason": "lab ok"}).status_code
        == 200
    )
    client.post(f"{URL}/{order}/report", json={"dQty": "50", "dDate": "2026-12-01"})
    assert _lot_status(client, "MO1") == "released"
    # recorded once the lot exists: that lot is held at once; per lot, one good record per lot made
    o = _record(client, order, CORE, "80", cLot="MO1", cComment="probe again").get_json()
    assert o["records"][-1]["cLot"] == "MO1" and _lot_status(client, "MO1") == "on_hold"
    o = _record(client, order, CORE, "94", cLot="MO1").get_json()
    step = _step(o["shopSteps"], CORE)
    assert (step["cState"], step["iNeeded"], step["iGood"]) == ("done", 1, 1)


def test_a_step_with_a_required_role(client, admin):
    o = client.post(URL, json={"cProduct": "SUPP-ALU-01", "dQty": "100", "dStart": "2026-12-01"}).get_json()
    assert client.post(f"{URL}/{o['iNo']}/release", json={}).status_code == 200, "release"
    no = o["iNo"]
    r = admin.post("/api/users", json={"username": "op1", "name": "Operator", "role": "USER", "password": "Secret-123"})
    assert r.status_code == 201, r.get_json()
    sign = (20, 20)  # signature step, role "quality"
    r = _record(client, no, sign, cSecondUser="op1", cSecondPassword="Secret-123")
    assert r.status_code == 400 and r.get_json()["error"] == "role_required" and r.get_json()["detail"] == "quality"
    assert _record(client, no, sign, **_sign()).status_code == 200  # an administrator may always
    # every 50 units: one record for each 50 made (at least one)
    board = client.get(f"{URL}/{no}/steps").get_json()
    assert _step(board, (10, 40))["iNeeded"] == 1
