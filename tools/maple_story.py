"""The story of the maple products demo (tools/make_maple_data.py): October and November 2026 played through the ERP.

Every step goes through the API, as on the screens, at the date and time of the story (time-machine moves the
clock), on an empty scratch database seeded with the master data and the purchases of data/maple. What the ERP
then holds in the tables of STORY_KEYS is returned: make_maple_data.py writes it to data/maple/story.json.

The story:
- the syrup of the barrels is standardized (filtered, Brix checked) into tanks, then made into cans, bottles,
  butter, candy and fudge, lot by lot (each lot to a free place: a location holds one lot of a product);
- the barrel T-140 of Sucrerie Tremblay tastes of "bourgeon" (end of season): a nonconformance at reception holds
  it, it is returned to the sugar bush (rejected: never used);
- one candy batch is cooked at 118.5 °C (115 ± 1): the step holds the lot, a nonconformance asks for a decision;
  the order is completed a day late;
- the barrel T-140 leaves the plant (a stock movement OUT of its lot);
- the invoices of the four customers are posted (the stock goes out by lot, FEFO), one complaint (six fudge trays
  crushed) gets a credit note, two invoices are still drafts; one order is released for next week, one is a draft.
"""

from __future__ import annotations

import os
import sys
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any

import time_machine
from sqlalchemy import create_engine, text

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

PASSWORD = "maple-story"
URL = "/api/production-orders"
INV = "/api/sales-invoices"
NC = "/api/nonconformances"


def _scratch_database() -> str:
    url = os.environ.get("MAPLE_DATABASE_URL", "postgresql+psycopg://powererp:powererp@127.0.0.1:5432/powererp_scratch")
    name = url.rsplit("/", 1)[-1]
    if "scratch" not in name and "test" not in name:
        sys.exit("MAPLE_DATABASE_URL must point to a database whose name contains 'scratch' or 'test': it is emptied.")
    from powererp.config import database_url

    engine = create_engine(database_url(url))
    with engine.begin() as con:
        con.execute(text("DROP SCHEMA public CASCADE"))
        con.execute(text("CREATE SCHEMA public"))
    engine.dispose()
    return url


class Story:
    def __init__(self, app):
        self.app = app
        self.client = app.test_client()
        self.now = ""

    @contextmanager
    def at(self, when: str):
        """The clock of the ERP at this date and time ("2026-10-01 07:30"), logged in as the administrator."""
        with time_machine.travel(datetime.fromisoformat(when), tick=False):
            self.now = when
            r = self.client.post("/api/auth/login", json={"username": "admin", "password": PASSWORD})
            assert r.status_code == 200, r.get_json()
            yield self

    def call(self, method: str, path: str, body: Any = None, ok: tuple[int, ...] = (200, 201)) -> Any:
        r = self.client.open(path, method=method, json=body)
        if r.status_code not in ok:
            raise RuntimeError(f"{self.now} {method} {path} {body}: {r.status_code} {r.get_json()}")
        return r.get_json()

    def post(self, path: str, body: Any = None) -> Any:
        return self.call("POST", path, body or {})

    # ---------------------------------------------------------- production
    def order(
        self,
        product: str,
        qty: float,
        start: str,
        due: str,
        location: str,
        *,
        made: float | None = None,
        values: dict[str, str] | None = None,
        comments: dict[str, str] | None = None,
        completed: str = "",
        closed: str = "",
        notes: str = "",
    ) -> dict:
        """An order made on its start day: released, issued by lot, its steps recorded, reported, then completed
        (the same day unless `completed`) and closed (`closed`, else left completed)."""
        with self.at(f"{start} 07:05"):
            o = self.post(
                URL,
                {
                    "cProduct": product,
                    "dQty": str(qty),
                    "dStart": start,
                    "dDue": due,
                    "cWarehouse": "PLANT",
                    "cNotes": notes,
                },
            )
            no = o["iNo"]
        with self.at(f"{start} 07:20"):
            self.post(f"{URL}/{no}/release", {"cComment": ""})
        with self.at(f"{start} 07:45"):
            self.post(f"{URL}/{no}/issue", {"dDate": start})
        with self.at(f"{start} 07:50"):
            board = self.call("GET", f"{URL}/{no}/steps")
        for i, s in enumerate(board["steps"]):
            body: dict[str, Any] = {"iOpSeq": s["iOpSeq"], "iStep": s["iStep"]}
            param = (s.get("cParam") or "").upper()
            if s["cKind"] in ("measure", "parameter"):
                body["cValue"] = (values or {}).get(param) or s.get("dTarget") or s.get("dMin")
            elif s["cKind"] == "check":
                body["cValue"] = "yes"
            if comments and param in comments:
                body["cComment"] = comments[param]
            minute = 8 * 60 + 20 * i
            with self.at(f"{start} {minute // 60:02}:{minute % 60:02}"):
                self.post(f"{URL}/{no}/steps/record", body)
        with self.at(f"{start} 14:10"):
            self.post(
                f"{URL}/{no}/report",
                {"dQty": str(made if made is not None else qty), "dDate": start, "cLocation": location},
            )
        with self.at(f"{completed or start} 15:10"):
            self.post(f"{URL}/{no}/complete", {"cComment": ""})
        if closed:
            with self.at(f"{closed} 10:00"):
                self.post(f"{URL}/{no}/close", {"cComment": "Coûts vérifiés."})
        return {"iNo": no, "cLot": f"MO{no}"}

    def planned(self, product: str, qty: float, start: str, due: str, when: str, release: bool) -> int:
        with self.at(when):
            no = self.post(
                URL, {"cProduct": product, "dQty": str(qty), "dStart": start, "dDue": due, "cWarehouse": "PLANT"}
            )["iNo"]
            if release:
                self.post(f"{URL}/{no}/release", {"cComment": ""})
        return no

    # ---------------------------------------------------------- sales
    def invoice(self, customer: str, day: str, lines: list[tuple[str, float]], post: bool = True, po: str = "") -> dict:
        with self.at(f"{day} 09:00"):
            inv = self.post(
                INV,
                {
                    "cCustomer": customer,
                    "dDate": day,
                    "cCustomerPO": po,
                    "lines": [{"cProduct": p, "dQty": str(q)} for p, q in lines],
                },
            )
        if post:
            with self.at(f"{day} 10:30"):
                inv = self.post(f"{INV}/{inv['iNo']}/post")
        return inv

    # ---------------------------------------------------------- quality
    def nonconformance(self, day: str, **body) -> int:
        with self.at(f"{day} 11:00"):
            return self.post(NC, {"dDate": day, "lHoldLot": True, **body})["iNo"]

    def close_nc(self, no: int, day: str, **body) -> None:
        with self.at(f"{day} 16:00"):
            self.post(f"{NC}/{no}/close", body)


def story(s: Story) -> None:
    std = "SYRUP-STD"
    # ---- October: the first standardized syrup (barrels of Érablière Gagnon), then every product
    s.order(std, 1000, "2026-10-01", "2026-10-01", "TANK-01", values={"BRIX": "67.3"}, closed="2026-10-02")
    s.order(
        "MAPLE-SYRUP-540",
        800,
        "2026-10-02",
        "2026-10-02",
        "FG-01",
        made=796,
        closed="2026-10-05",
        notes="4 cannes mal scellées retirées de la ligne.",
    )
    s.order(
        "MAPLE-BUTTER-200",
        300,
        "2026-10-05",
        "2026-10-05",
        "FG-02",
        values={"TEMP_CUISSON": "112.2", "TEMP_REFROID": "7.5"},
        closed="2026-10-06",
    )
    s.invoice("EPICERIE-STDENIS", "2026-10-06", [("MAPLE-SYRUP-540", 240), ("MAPLE-BUTTER-200", 60)], po="ESD-1007")
    s.order(
        "MAPLE-CANDY-12",
        400,
        "2026-10-07",
        "2026-10-07",
        "FG-03",
        made=388,
        values={"TEMP_CUISSON": "115.1"},
        closed="2026-10-08",
        notes="12 boîtes de bonbons cassés au démoulage.",
    )
    s.order(
        "MAPLE-FUDGE-250",
        300,
        "2026-10-08",
        "2026-10-08",
        "FG-04",
        values={"TEMP_CUISSON": "113.2"},
        closed="2026-10-09",
    )
    s.invoice("BOUTIQUE-VQ", "2026-10-09", [("MAPLE-SYRUP-540", 120), ("MAPLE-CANDY-12", 96), ("MAPLE-FUDGE-250", 60)])
    s.invoice(
        "DISTRIB-CHAUDIERE",
        "2026-10-13",
        [("MAPLE-SYRUP-540", 300), ("MAPLE-CANDY-12", 150), ("MAPLE-FUDGE-250", 120), ("MAPLE-BUTTER-200", 100)],
        po="DAC-55102",
    )
    s.order("MAPLE-SYRUP-250", 600, "2026-10-14", "2026-10-14", "FG-05", values={"BRIX": "67.8"}, closed="2026-10-15")
    s.invoice("LAURENTIAN-HOTELS", "2026-10-20", [("MAPLE-SYRUP-250", 200), ("MAPLE-SYRUP-540", 100)], po="LHG-3381")
    s.invoice("EPICERIE-STDENIS", "2026-10-27", [("MAPLE-SYRUP-250", 120), ("MAPLE-FUDGE-250", 60)], po="ESD-1028")

    # ---- the barrels of Sucrerie Tremblay (received 2026-10-28): T-140 tastes of "bourgeon"
    nc = s.nonconformance(
        "2026-10-28",
        cSource="reception",
        cRef="900106",
        cProduct="SYRUP-BULK-AMB",
        cLot="900106-3",
        dQty="278",
        cSeverity="major",
        cDescription="Baril T-140 (récolte du 2026-04-26) : goût de bourgeon à la dégustation de réception.",
    )
    s.close_nc(
        nc,
        "2026-10-30",
        cDisposition="return_supplier",
        cCause="Sirop de fin de saison (bourgeonnement des érables).",
        cAction="Baril retourné à Sucrerie Tremblay et crédité. Dégustation de chaque baril récolté après le 20 avril.",
    )
    with s.at("2026-10-30 16:30"):  # the barrel leaves the plant
        s.post(
            "/api/stock-movements",
            {
                "dDate": "2026-10-30",
                "cType": "OUT",
                "cProduct": "SYRUP-BULK-AMB",
                "dQty": "278",
                "cWarehouse": "PLANT",
                "cLocation": "BAR-11",
                "cLot": "900106-3",
                "cDocType": "REC",
                "cDocNo": "900106",
                "cReason": "Retour au fournisseur (non-conformité 1)",
                "cComment": "Baril T-140",
            },
        )
    # ---- a customer complaint: 6 trays of fudge crushed in the delivery of 2026-10-27
    complaint = s.nonconformance(
        "2026-10-29",
        cSource="customer",
        cRef="Facture 5",
        cProduct="MAPLE-FUDGE-250",
        cLot="MO5",
        dQty="6",
        cSeverity="minor",
        lHoldLot=False,
        cDescription="Épicerie fine Saint-Denis : 6 barquettes écrasées à la livraison.",
    )
    with s.at("2026-10-29 14:00"):
        posted = [i for i in s.call("GET", f"{INV}?size=100")["items"] if i.get("cInvoiceNo") == "5"]
        assert posted, "invoice 5"
        cn = s.post(f"{INV}/{posted[0]['iNo']}/credit")
        lines = [ln for ln in cn["lines"] if ln["cProduct"] == "MAPLE-FUDGE-250"]
        s.call(
            "PUT",
            f"{INV}/{cn['iNo']}",
            {
                "cNotes": "6 barquettes écrasées (non retournées).",
                "lines": [{**lines[0], "dQty": "6", "lReturn": False}],
            },
        )
        s.post(f"{INV}/{cn['iNo']}/post")
    s.close_nc(
        complaint,
        "2026-11-02",
        cDisposition="use_as_is",
        cCause="Caisses empilées trop haut dans le camion (le lot en stock est conforme).",
        cAction="Note de crédit NC-1. Maximum 4 caisses de sucre à la crème par pile, indiqué sur les caisses.",
    )

    # ---- November: the second standardized syrup (Cantons and Tremblay barrels; T-140 is never used)
    s.order(std, 800, "2026-11-02", "2026-11-02", "TANK-02", values={"BRIX": "66.9"}, closed="2026-11-03")
    s.order("MAPLE-SYRUP-540", 1000, "2026-11-03", "2026-11-03", "FG-06", closed="2026-11-04")
    candy = s.order(
        "MAPLE-CANDY-12",
        400,
        "2026-11-05",
        "2026-11-05",
        "FG-07",
        values={"TEMP_CUISSON": "118.5"},
        comments={"TEMP_CUISSON": "Sonde du cuiseur 2 décalée; sirop trop cuit. Lot retenu, texture à vérifier."},
        completed="2026-11-06",
    )
    s.nonconformance(
        "2026-11-06",
        cSource="production",
        cRef=f"Ordre {candy['iNo']}",
        cProduct="MAPLE-CANDY-12",
        cLot=candy["cLot"],
        dQty="400",
        cSeverity="major",
        cDescription="Cuisson à 118,5 °C (limite 116 °C) : bonbons durs et granuleux possibles. Décision à prendre.",
    )
    s.invoice("DISTRIB-CHAUDIERE", "2026-11-06", [("MAPLE-SYRUP-540", 400), ("MAPLE-BUTTER-200", 100)], po="DAC-55240")
    s.order(
        "MAPLE-FUDGE-250",
        300,
        "2026-11-12",
        "2026-11-12",
        "FG-08",
        values={"TEMP_CUISSON": "112.8"},
        closed="2026-11-13",
    )
    s.invoice("BOUTIQUE-VQ", "2026-11-13", [("MAPLE-CANDY-12", 120), ("MAPLE-FUDGE-250", 80), ("MAPLE-SYRUP-250", 60)])
    s.order(
        "MAPLE-BUTTER-200",
        300,
        "2026-11-16",
        "2026-11-17",
        "FG-09",
        values={"TEMP_CUISSON": "111.8", "TEMP_REFROID": "8.2"},
        completed="2026-11-17",
        closed="2026-11-18",
    )
    s.invoice("LAURENTIAN-HOTELS", "2026-11-18", [("MAPLE-SYRUP-250", 150), ("MAPLE-SYRUP-540", 200)], po="LHG-3502")
    s.invoice("EPICERIE-STDENIS", "2026-11-20", [("MAPLE-SYRUP-540", 200), ("MAPLE-BUTTER-200", 80)], po="ESD-1121")
    # ---- still to do: two drafts (one would take the held candy), an order released, one draft
    s.invoice(
        "DISTRIB-CHAUDIERE",
        "2026-11-24",
        [("MAPLE-SYRUP-540", 200), ("MAPLE-FUDGE-250", 60)],
        post=False,
        po="DAC-55377",
    )
    s.invoice("LAURENTIAN-HOTELS", "2026-11-25", [("MAPLE-CANDY-12", 48)], post=False, po="LHG-3560")
    s.planned("MAPLE-SYRUP-540", 600, "2026-11-30", "2026-11-30", "2026-11-25 15:00", release=True)
    s.planned("MAPLE-CANDY-12", 300, "2026-12-01", "2026-12-02", "2026-11-25 15:20", release=False)


def play(keys: tuple[str, ...]) -> dict:
    """Run the story on an empty scratch database; the rows of these tables afterwards."""
    url = _scratch_database()
    (ROOT / "data" / "maple" / "story.json").unlink(missing_ok=True)  # the story starts from the bare seed
    os.environ.update(
        {
            "DATABASE_URL": url,
            "ERP_SCENARIO": "maple",
            "ERP_DATASET": os.environ.get("ERP_DATASET", "demo"),
            "ERP_ADMIN_USER": "admin",
            "ERP_ADMIN_PASSWORD": PASSWORD,
            "ERP_SECRET_KEY": "maple-story",
            "ERP_API_KEY": "maple-story",
            "BACKUP_SCHEDULER": "0",
        }
    )
    from powererp import database
    from powererp.factory import create_app

    with time_machine.travel(datetime(2026, 9, 30, 18, 0), tick=False):
        app = create_app(url)
    story(Story(app))
    with app.app_context(), database.unit_of_work():
        rows = app.extensions["powererp"].get("lifecycle").export(keys)
    return {
        "_about": "The tables after the story of tools/maple_story.py (October and November 2026 played through the "
        "ERP); they replace the seed of these tables. Generated: do not edit, run tools/make_maple_data.py.",
        **rows,
    }
