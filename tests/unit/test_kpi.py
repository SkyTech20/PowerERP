"""Unit tests of the supply chain indicators (step 7): each indicator from a small set of documents."""

from datetime import date

import pytest

from powererp.core.errors import AppError
from powererp.modules.reports.kpi import KpiService

TODAY = date(2026, 11, 26)


def service(**data):
    deps = {name: (lambda v=v: v) for name, v in data.items()}
    deps["today"] = lambda: TODAY
    deps["unit_cost"] = lambda prod: float(prod.get("dAvgCost") or 0)
    return KpiService(deps)


def by_key(out, group):
    return {k["key"]: k for k in out[group]}


def test_the_period_defaults_to_the_last_90_days_and_is_checked():
    s = service()
    assert s.period({}) == {"from": "2026-08-29", "to": "2026-11-26", "days": 90, "horizon": 30}
    assert s.period({"from": "2026-11-01", "to": "2026-11-30", "horizon": "7"})["days"] == 30
    for args, code in (({"from": "2026-12-01", "to": "2026-11-01"}, "invalid_period"), ({"from": "x"}, "invalid_date")):
        with pytest.raises(AppError) as e:
            s.period(args)
        assert e.value.code == code
    with pytest.raises(AppError):
        s.period({"horizon": "400"})


def test_nothing_to_measure_gives_no_value():
    out = service().indicators({})
    assert all(k["value"] is None for k in out["reliability"] + out["responsiveness"] + out["cost"])
    assets = by_key(out, "assets")
    assert assets["inventory_value"]["value"] == 0 and assets["days_supply"]["value"] is None


def test_sales_perfect_orders_and_gross_margin():
    invoices = [
        {
            "cType": "invoice",
            "cStatus": "posted",
            "cInvoiceNo": "1",
            "dDate": "2026-11-10",
            "dSubTotal": "100",
            "dCost": "40",
        },
        {
            "cType": "invoice",
            "cStatus": "posted",
            "cInvoiceNo": "2",
            "dDate": "2026-11-11",
            "dSubTotal": "200",
            "dCost": "80",
        },
        {
            "cType": "invoice",
            "cStatus": "draft",
            "cInvoiceNo": "",
            "dDate": "2026-11-11",
            "dSubTotal": "999",
            "dCost": "0",
        },
        {
            "cType": "invoice",
            "cStatus": "posted",
            "cInvoiceNo": "3",
            "dDate": "2025-01-01",
            "dSubTotal": "50",
            "dCost": "1",
        },
        {
            "cType": "credit",
            "cStatus": "posted",
            "cOrigInvoice": "2",
            "dDate": "2026-11-12",
            "dSubTotal": "50",
            "dCost": "20",
        },
    ]
    out = service(invoices=invoices).indicators({})
    rl, co = by_key(out, "reliability"), by_key(out, "cost")
    assert (rl["perfect_order"]["num"], rl["perfect_order"]["den"], rl["perfect_order"]["value"]) == (1, 2, 0.5)
    # sales 100 + 200 - 50 = 250, cost 40 + 80 - 20 = 100
    assert co["gross_margin"]["value"] == pytest.approx(0.6) and co["gross_margin"]["den"] == 250


def test_production_on_time_yield_cycle_variance_and_steps():
    orders = [
        {
            "iNo": 1,
            "cProduct": "BREAD",
            "cStatus": "closed",
            "dQty": "100",
            "dQtyDone": "95",
            "dDue": "2026-11-10",
            "dReleased": "2026-11-08T08:00:00",
            "dCompleted": "2026-11-10T08:00:00",
            "dClosed": "2026-11-11T08:00:00",
            "dEstUnitCost": "2",
            "dVariance": "19",
            "records": [
                {"dAt": "2026-11-09T10:00:00", "lOk": True},
                {
                    "dAt": "2026-11-09T11:00:00",
                    "lOk": False,
                    "cAction": "block",
                    "cReason": "below_min",
                    "iOpSeq": 20,
                    "iStep": 10,
                },
            ],
        },
        {
            "iNo": 2,
            "cProduct": "BREAD",
            "cStatus": "completed",
            "dQty": "50",
            "dQtyDone": "50",
            "dDue": "2026-11-12",
            "dReleased": "2026-11-12T08:00:00",
            "dCompleted": "2026-11-13T20:00:00",
        },
        {"iNo": 3, "cStatus": "in_progress", "dQty": "10", "dQtyDone": "5", "records": []},
    ]
    out = service(orders=orders).indicators({})
    rl, rs, co = by_key(out, "reliability"), by_key(out, "responsiveness"), by_key(out, "cost")
    assert (rl["prod_on_time"]["num"], rl["prod_on_time"]["den"]) == (1, 2)
    assert rl["prod_yield"]["value"] == pytest.approx(145 / 150, abs=1e-4)
    assert rs["prod_cycle"]["value"] == pytest.approx((2 + 1.5) / 2)
    assert co["cost_variance"]["value"] == pytest.approx(19 / 190, abs=1e-4)  # estimated 2 x 95
    assert (rl["steps_first_time"]["num"], rl["steps_first_time"]["den"]) == (1, 2)
    assert [(d["iOrder"], d["cStep"], d["cAction"]) for d in out["deviations"]] == [(1, "20/10", "block")]


def test_suppliers_fill_rate_and_receptions_without_a_problem():
    receptions = [
        {
            "NoReception": "R1",
            "DateReception": "2026-11-01",
            "lines": [{"QuantiteCommandee": "10", "QuantiteRecue": "8"}],
        },
        {
            "NoReception": "R2",
            "DateReception": "2026-11-02",
            "lines": [{"QuantiteCommandee": "10", "QuantiteRecue": "12"}],
        },
    ]
    ncs = [
        {
            "cSource": "reception",
            "cRef": "r1",
            "dDate": "2026-11-01",
            "cSeverity": "major",
            "cStatus": "closed",
            "dCreated": "2026-11-01T10:00:00",
            "dClosed": "2026-11-04T10:00:00",
        },
        {"cSource": "production", "cRef": "", "dDate": "2026-11-20", "cSeverity": "minor", "cStatus": "open"},
    ]
    out = service(receptions=receptions, ncs=ncs).indicators({})
    rl, rs = by_key(out, "reliability"), by_key(out, "responsiveness")
    assert rl["supplier_fill"]["value"] == pytest.approx(18 / 20)  # the 12 received count as the 10 ordered
    assert (rl["supplier_quality"]["num"], rl["supplier_quality"]["den"]) == (1, 2)
    assert rs["nc_close_days"]["value"] == 3
    nc = out["nonconformances"]
    assert (nc["found"], nc["open"], nc["bySource"], nc["bySeverity"]) == (
        2,
        1,
        {"reception": 1, "production": 1},
        {"major": 1, "minor": 1},
    )


def test_stock_turns_days_of_supply_and_the_lots_to_watch():
    products = [
        {"cCode": "FLOUR", "dAvgCost": "1", "cStockUOM": "KG"},
        {"cCode": "MILK", "dAvgCost": "2", "cStockUOM": "L"},
        {"cCode": "BOX", "dAvgCost": "0.5", "cStockUOM": "UN"},
    ]
    balances = {
        1: {"cProduct": "FLOUR", "cLot": "F1", "dExpiry": "2027-06-01", "qty": 900},
        2: {"cProduct": "MILK", "cLot": "M1", "dExpiry": "2026-12-01", "qty": 30},  # 5 days left
        3: {"cProduct": "MILK", "cLot": "M0", "dExpiry": "2026-11-20", "qty": 10},  # expired
        4: {"cProduct": "BOX", "cLot": "", "dExpiry": "", "qty": 200},
    }
    movements = [
        {"cType": "OUT", "cDocType": "PROD", "cProduct": "FLOUR", "dDate": "2026-11-10", "dValue": "-90"},
        {"cType": "OUT", "cDocType": "SO", "cProduct": "MILK", "dDate": "2026-11-11", "dValue": "-90"},
        {"cType": "OUT", "cDocType": "MAN", "cProduct": "BOX", "dDate": "2026-11-11", "dValue": "-5"},  # not a use
    ]
    statuses = {("FLOUR", "F1"): "on_hold"}
    out = service(products=products, balances=balances, movements=movements, lot_statuses=statuses).indicators(
        {"from": "2026-11-01", "to": "2026-11-30", "horizon": "7"}
    )
    am = by_key(out, "assets")
    assert am["inventory_value"]["value"] == 1080  # 900 + 80 + 100
    assert am["inventory_turns"]["value"] == pytest.approx(180 / 30 * 365 / 1080, abs=0.01)
    assert am["days_supply"]["value"] == pytest.approx(1080 / 6, abs=0.01)
    assert (am["held_value"]["value"], am["held_value"]["num"]) == (900, 1)
    assert (am["expiring_value"]["value"], am["expiring_value"]["num"]) == (80, 2)
    assert [(r["cLot"], r["iDaysLeft"]) for r in out["lots"]["expiring"]] == [("M0", -6), ("M1", 5)]
    rows = out["products"]["rows"]
    assert [r["cProduct"] for r in rows] == ["BOX", "FLOUR", "MILK"]  # not used first, then the most days of supply
    assert rows[0]["dDaysSupply"] is None and rows[0]["dLastOut"] == "2026-11-11"
    assert out["products"]["slow"] == 1
