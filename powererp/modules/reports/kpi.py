"""The supply chain indicators (step 7 of the SCOR / ISO plan: SCOR performance attributes, ISO 9001 9.1 monitoring,
measurement, analysis and evaluation).

Everything is read from the data the ERP already keeps, for a period (from / to, the last 90 days by default):

Reliability (RL)
- perfect_order: the posted sales invoices of the period that no credit note credits (SCOR RL.1.1, simplified: an
  invoice with a credit note had a wrong quantity, price, product or a return);
- prod_on_time: the production orders completed in the period on or before their due date (orders without a due date
  are left out);
- prod_yield: the quantity made / the quantity ordered, of the orders completed in the period;
- supplier_fill: the quantity received / the quantity ordered on the receptions of the period (each line counts at
  most what was ordered);
- supplier_quality: the receptions of the period without a nonconformance found at reception (its document);
- steps_first_time: the shop floor records of the period within their limits (M4).
Responsiveness (RS)
- prod_cycle: the days from release to completion, on average, of the orders completed in the period;
- nc_close_days: the days from the creation to the closing of the nonconformances closed in the period.
Cost (CO)
- cost_variance: the actual cost against the estimated cost of the quantity made, of the orders closed in the period;
- gross_margin: (sales - cost of the goods sold) / sales, of the invoices posted in the period (credit notes subtract).
Assets (AM)
- inventory_value: the value of the stock today (quantity x unit cost of the product);
- inventory_turns: the stock used in the period (value of the stock that went out for sales and production), per year,
  / the value of the stock today;
- days_supply: the value of the stock today / the value used per day in the period;
- held_value: the value of the lots in stock that are not released (quality);
- expiring_value: the value of the lots that expire within the horizon (30 days by default) or are already expired.

Each indicator is {key, value, unit, num, den}: value is None when there is nothing to measure (no data in the period).
The lists under it: the lots to expire, the lots held, the stock by product (days of supply, slow movers), the
nonconformances by source and severity and the deviations recorded on the shop floor.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import date, datetime, timedelta
from typing import Any

from powererp.core.errors import AppError
from powererp.core.values import number, text

Row = dict[str, Any]
Rows = list[Row]
DAYS = 90  # the default period
HORIZON = 30  # the default horizon of the lots to expire
TOP = 15  # the rows of the stock by product
USED_DOCS = ("SO", "INV", "PROD")  # the stock that goes out for a sale (invoice) or a production order
LOT_HELD = ("on_hold", "quarantine", "rejected")


def _day(value: object) -> str:
    return text(value)[:10]


def _date(value: str, field: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise AppError("invalid_date", field) from None


def _days_between(start: object, end: object) -> float | None:
    """Days (with a decimal) between two timestamps or dates; None when one is missing."""
    a, b = text(start), text(end)
    if not a or not b:
        return None
    try:
        return (datetime.fromisoformat(b[:19]) - datetime.fromisoformat(a[:19])).total_seconds() / 86400
    except ValueError:
        return None


def _ratio(num: float, den: float) -> float | None:
    return num / den if den > 1e-9 else None


def kpi(key: str, value: float | None, unit: str, num: float | None = None, den: float | None = None) -> Row:
    """unit: pct (0..1), days, money, ratio (times a year)."""
    rounded = None if value is None else round(value, 4 if unit == "pct" else 2)
    return {"key": key, "value": rounded, "unit": unit, "num": num, "den": den}


class KpiService:
    def __init__(self, deps: dict[str, Callable[..., Any]]):
        """deps (each a callable, read when asked): invoices() sales invoices, orders() production orders,
        receptions() receptions (with their lines), ncs() nonconformances, lot_statuses() {(PRODUCT, LOT): status},
        balances() stock balances, movements() stock movements, products() products, today() the date;
        unit_cost(product) the unit cost of a product (not called: a function)."""
        self.deps = deps

    def _get(self, name: str, default: Any) -> Any:
        dep = self.deps.get(name)
        return dep() if dep else default

    # ---------------------------------------------------------- the period
    def period(self, args: Row) -> Row:
        today = self._get("today", date.today())
        to = _date(text(args.get("to")) or today.isoformat(), "to")
        start = _date(text(args.get("from")) or (to - timedelta(days=DAYS - 1)).isoformat(), "from")
        if start > to:
            raise AppError("invalid_period", "from")
        horizon = int(number(args.get("horizon")) or HORIZON)
        if not 1 <= horizon <= 365:
            raise AppError("invalid_choice", "horizon")
        return {"from": start.isoformat(), "to": to.isoformat(), "days": (to - start).days + 1, "horizon": horizon}

    @staticmethod
    def _in(value: object, p: Row) -> bool:
        d = _day(value)
        return bool(d) and p["from"] <= d <= p["to"]

    # ---------------------------------------------------------- all
    def indicators(self, args: Row) -> Row:
        p = self.period(args)
        products = {r["cCode"].upper(): r for r in self._get("products", [])}
        cost_of = self.deps.get("unit_cost") or (lambda prod: number(prod.get("dAvgCost")))
        cost = {code: cost_of(r) for code, r in products.items()}
        stock = self._stock(p, cost)
        orders = self._get("orders", [])
        ncs = self._get("ncs", [])
        steps, deviations = self._steps(p, orders)
        return {
            "period": p,
            "reliability": [
                self._perfect_order(p),
                *self._production_reliability(p, orders),
                *self._suppliers(p, ncs),
                steps,
            ],
            "responsiveness": [self._cycle(p, orders), self._nc_close(p, ncs)],
            "cost": [self._variance(p, orders), self._margin(p)],
            "assets": stock["kpis"],
            "lots": stock["lots"],
            "products": stock["products"],
            "nonconformances": self._nc_counts(p, ncs),
            "deviations": deviations,
        }

    # ---------------------------------------------------------- reliability
    def _perfect_order(self, p: Row) -> Row:
        invoices = [i for i in self._get("invoices", []) if i.get("cStatus") == "posted"]
        credited = {text(i.get("cOrigInvoice")).upper() for i in invoices if i.get("cType") == "credit"}
        mine = [i for i in invoices if i.get("cType") != "credit" and self._in(i.get("dDate"), p)]
        good = sum(1 for i in mine if text(i.get("cInvoiceNo")).upper() not in credited)
        return kpi("perfect_order", _ratio(good, len(mine)), "pct", good, len(mine))

    def _production_reliability(self, p: Row, orders: Rows) -> list[Row]:
        done = [o for o in orders if o.get("cStatus") in ("completed", "closed") and self._in(o.get("dCompleted"), p)]
        due = [o for o in done if _day(o.get("dDue"))]
        on_time = sum(1 for o in due if _day(o["dCompleted"]) <= _day(o["dDue"]))
        made = sum(number(o.get("dQtyDone")) for o in done)
        asked = sum(number(o.get("dQty")) for o in done)
        return [
            kpi("prod_on_time", _ratio(on_time, len(due)), "pct", on_time, len(due)),
            kpi("prod_yield", _ratio(made, asked), "pct", round(made, 4), round(asked, 4)),
        ]

    def _suppliers(self, p: Row, ncs: Rows) -> list[Row]:
        recs = [r for r in self._get("receptions", []) if self._in(r.get("DateReception"), p)]
        ordered = received = 0.0
        for r in recs:
            for ln in r.get("lines", []):
                want = number(ln.get("QuantiteCommandee"))
                if want > 0:
                    ordered += want
                    received += min(number(ln.get("QuantiteRecue")), want)
        found = {text(n.get("cRef")).upper() for n in ncs if n.get("cSource") == "reception"}
        clean = sum(1 for r in recs if text(r.get("NoReception")).upper() not in found)
        return [
            kpi("supplier_fill", _ratio(received, ordered), "pct", round(received, 4), round(ordered, 4)),
            kpi("supplier_quality", _ratio(clean, len(recs)), "pct", clean, len(recs)),
        ]

    def _steps(self, p: Row, orders: Rows) -> tuple[Row, Rows]:
        records = [(o, r) for o in orders for r in o.get("records", []) if self._in(r.get("dAt"), p)]
        good = sum(1 for _o, r in records if r.get("lOk"))
        bad = [
            {
                "iOrder": o["iNo"],
                "cProduct": o.get("cProduct", ""),
                "dAt": r.get("dAt"),
                "cStep": f"{r.get('iOpSeq')}/{r.get('iStep')}",
                "cTitleFR": r.get("cTitleFR", ""),
                "cTitleEN": r.get("cTitleEN", ""),
                "cValue": r.get("cValue", ""),
                "cUOM": r.get("cUOM", ""),
                "cReason": r.get("cReason", ""),
                "cAction": r.get("cAction", ""),
                "cComment": r.get("cComment", ""),
                "cUser": r.get("cUser", ""),
            }
            for o, r in records
            if not r.get("lOk")
        ]
        bad.sort(key=lambda d: text(d["dAt"]), reverse=True)
        return kpi("steps_first_time", _ratio(good, len(records)), "pct", good, len(records)), bad

    # ---------------------------------------------------------- responsiveness
    def _cycle(self, p: Row, orders: Rows) -> Row:
        days = [
            d
            for o in orders
            if o.get("cStatus") in ("completed", "closed") and self._in(o.get("dCompleted"), p)
            if (d := _days_between(o.get("dReleased"), o.get("dCompleted"))) is not None
        ]
        return kpi("prod_cycle", _ratio(sum(days), len(days)), "days", round(sum(days), 2), len(days))

    def _nc_close(self, p: Row, ncs: Rows) -> Row:
        days = [
            d
            for n in ncs
            if n.get("cStatus") == "closed" and self._in(n.get("dClosed"), p)
            if (d := _days_between(n.get("dCreated") or n.get("dDate"), n.get("dClosed"))) is not None
        ]
        return kpi("nc_close_days", _ratio(sum(days), len(days)), "days", round(sum(days), 2), len(days))

    # ---------------------------------------------------------- cost
    def _variance(self, p: Row, orders: Rows) -> Row:
        closed = [o for o in orders if o.get("cStatus") == "closed" and self._in(o.get("dClosed"), p)]
        est = sum(number(o.get("dEstUnitCost")) * number(o.get("dQtyDone")) for o in closed)
        diff = sum(number(o.get("dVariance")) for o in closed)
        return kpi("cost_variance", _ratio(diff, est), "pct", round(diff, 2), round(est, 2))

    def _margin(self, p: Row) -> Row:
        sales = cogs = 0.0
        for i in self._get("invoices", []):
            if i.get("cStatus") != "posted" or not self._in(i.get("dDate"), p):
                continue
            sign = -1 if i.get("cType") == "credit" else 1
            sales += sign * number(i.get("dSubTotal"))
            cogs += sign * abs(number(i.get("dCost")))
        return kpi("gross_margin", _ratio(sales - cogs, sales), "pct", round(sales - cogs, 2), round(sales, 2))

    # ---------------------------------------------------------- assets: the stock today and what was used
    def _stock(self, p: Row, cost: dict[str, float]) -> Row:
        today = self._get("today", date.today()).isoformat()
        limit = (date.fromisoformat(today) + timedelta(days=p["horizon"])).isoformat()
        statuses = self._get("lot_statuses", {})
        products = {r["cCode"].upper(): r for r in self._get("products", [])}
        value_by: dict[str, float] = {}
        qty_by: dict[str, float] = {}
        lots: dict[tuple[str, str], Row] = {}
        for b in self._get("balances", {}).values():
            qty = number(b.get("qty"))
            if qty <= 1e-9:
                continue
            code = text(b.get("cProduct")).upper()
            value = qty * cost.get(code, 0.0)
            value_by[code] = value_by.get(code, 0.0) + value
            qty_by[code] = qty_by.get(code, 0.0) + qty
            lot = text(b.get("cLot"))
            if lot:
                row = lots.setdefault(
                    (code, lot.upper()),
                    {
                        "cProduct": b.get("cProduct"),
                        "cLot": lot,
                        "dExpiry": _day(b.get("dExpiry")),
                        "qty": 0.0,
                        "value": 0.0,
                    },
                )
                row["qty"] += qty
                row["value"] += value
                row["dExpiry"] = min((x for x in (row["dExpiry"], _day(b.get("dExpiry"))) if x), default="")
        used: dict[str, float] = {}
        last_out: dict[str, str] = {}
        for m in self._get("movements", []):
            if m.get("cType") != "OUT":
                continue
            code = text(m.get("cProduct")).upper()
            day = _day(m.get("dDate"))
            last_out[code] = max(last_out.get(code, ""), day)
            if m.get("cDocType") in USED_DOCS and p["from"] <= day <= p["to"]:
                used[code] = used.get(code, 0.0) + abs(number(m.get("dValue")))
        total = sum(value_by.values())
        per_day = sum(used.values()) / p["days"]

        def lot_row(r: Row) -> Row:
            prod = products.get(r["cProduct"].upper(), {})
            status = statuses.get((r["cProduct"].upper(), r["cLot"].upper()), "released")
            left = (date.fromisoformat(r["dExpiry"]) - date.fromisoformat(today)).days if r["dExpiry"] else None
            return {
                "cProduct": r["cProduct"],
                "cDescFR": prod.get("cDescFR", ""),
                "cDescEN": prod.get("cDescEN", ""),
                "cLot": r["cLot"],
                "dExpiry": r["dExpiry"],
                "iDaysLeft": left,
                "cStatus": status,
                "dQty": round(r["qty"], 4),
                "cUOM": prod.get("cStockUOM", ""),
                "dValue": round(r["value"], 2),
            }

        all_lots = [lot_row(r) for r in lots.values()]
        expiring = sorted((r for r in all_lots if r["dExpiry"] and r["dExpiry"] <= limit), key=lambda r: r["dExpiry"])
        held = sorted((r for r in all_lots if r["cStatus"] in LOT_HELD), key=lambda r: -r["dValue"])
        rows = []
        for code, value in value_by.items():
            prod = products.get(code, {})
            pace = used.get(code, 0.0) / p["days"]  # value used per day
            rows.append(
                {
                    "cProduct": prod.get("cCode", code),
                    "cDescFR": prod.get("cDescFR", ""),
                    "cDescEN": prod.get("cDescEN", ""),
                    "dQty": round(qty_by[code], 4),
                    "cUOM": prod.get("cStockUOM", ""),
                    "dValue": round(value, 2),
                    "dUsed": round(used.get(code, 0.0), 2),
                    "dDaysSupply": round(value / pace, 1) if pace > 1e-9 else None,
                    "dLastOut": last_out.get(code, ""),
                }
            )
        # the slow movers first (no use in the period, then the most days of supply), the largest values first
        rows.sort(key=lambda r: (r["dDaysSupply"] is not None, -(r["dDaysSupply"] or 0), -r["dValue"]))
        held_value = sum(r["dValue"] for r in held)
        expiring_value = sum(r["dValue"] for r in expiring)
        return {
            "kpis": [
                kpi("inventory_value", total, "money"),
                kpi(
                    "inventory_turns",
                    _ratio(per_day * 365, total),
                    "ratio",
                    round(sum(used.values()), 2),
                    round(total, 2),
                ),
                kpi("days_supply", _ratio(total, per_day), "days", round(total, 2), round(per_day, 2)),
                kpi("held_value", held_value, "money", len(held), None),
                kpi("expiring_value", expiring_value, "money", len(expiring), None),
            ],
            "lots": {"expiring": expiring, "held": held},
            "products": {
                "rows": rows[:TOP],
                "total": len(rows),
                "slow": sum(1 for r in rows if r["dDaysSupply"] is None),
            },
        }

    # ---------------------------------------------------------- nonconformances
    def _nc_counts(self, p: Row, ncs: Rows) -> Row:
        mine = [n for n in ncs if self._in(n.get("dDate"), p)]
        by_source: dict[str, int] = {}
        by_severity: dict[str, int] = {}
        for n in mine:
            by_source[n.get("cSource") or "internal"] = by_source.get(n.get("cSource") or "internal", 0) + 1
            by_severity[n.get("cSeverity") or "minor"] = by_severity.get(n.get("cSeverity") or "minor", 0) + 1
        return {
            "found": len(mine),
            "open": sum(1 for n in ncs if n.get("cStatus") == "open"),
            "bySource": by_source,
            "bySeverity": by_severity,
        }
