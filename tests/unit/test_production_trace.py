"""TraceService with fakes: a loop between two lots ends, a reception deleted since keeps the movement's data,
the lots reached go through several orders, the lookup of the lots."""

from powererp.core.errors import AppError
from powererp.modules.production.trace import TraceService


class Repo:
    def __init__(self, rows):
        self.rows = rows

    def all(self, **_):
        return self.rows


class Stock:
    def __init__(self, moves, balances):
        self.ledger = Repo(moves)
        self._b = balances

    def balances(self):
        return self._b


class Holder:
    def __init__(self, rows):
        self.repo = Repo(rows)


class Receptions:
    def get(self, no):
        raise LookupError(no)  # deleted since


def mv(no, prod, lot, kind, doc, qty, docno="", reason=""):
    return {
        "iNo": no,
        "cProduct": prod,
        "cLot": lot,
        "cType": kind,
        "cDocType": doc,
        "dQty": qty,
        "cDocNo": docno,
        "cReason": reason,
        "dDate": "2026-12-01",
        "cWarehouse": "W",
        "cLocation": "L",
        "dExpiry": "",
        "cUser": "u",
    }


def order(no, product, uses, makes, status="closed"):
    return {
        "iNo": no,
        "cProduct": product,
        "cStatus": status,
        "issues": [{"cComponent": c, "cLot": lot, "dQty": q} for c, lot, q in uses],
        "outputs": [{"cLot": lot, "dQty": q, "dDate": "2026-12-01"} for lot, q in makes],
    }


def service(moves, orders, balances=None):
    deps = {
        "stock": lambda: Stock(moves, balances or {}),
        "orders": lambda: Holder(orders),
        "receptions": lambda: Receptions(),
        "invoices": lambda: Holder([]),
        "products": lambda: (lambda code: {"cCode": code, "cStockUOM": "KG", "cDescFR": code.lower()}),
    }
    return TraceService(deps)


MOVES = [
    mv(1, "A", "A1", "IN", "REC", "10", "R1", "SUP"),
    mv(2, "A", "A1", "OUT", "PROD", "10", "1"),
    mv(3, "B", "B1", "IN", "PROD", "8", "1"),
    mv(4, "B", "B1", "OUT", "PROD", "8", "2"),
    mv(5, "C", "C1", "IN", "PROD", "5", "2"),
    mv(6, "C", "C1", "OUT", "SO", "2", "7", "CUST"),
]
ORDERS = [
    order(1, "B", [("A", "A1", "10")], [("B1", "8")]),
    order(2, "C", [("B", "B1", "8")], [("C1", "5")], "completed"),
]


def test_lots_reached_through_two_orders_and_the_recall():
    s = service(MOVES, ORDERS, {("C", "W", "L", "C1", ""): {"qty": 3.0}})
    t = s.trace("a", "a1")
    assert [(n["cProduct"], n["cLot"]) for n in t["recall"]["lots"]] == [("A", "A1"), ("B", "B1"), ("C", "C1")]
    assert [(c["cCustomer"], c["dQty"]) for c in t["recall"]["customers"]] == [("CUST", "2")]  # from the movement
    assert [(s["cLot"], s["dQty"]) for s in t["recall"]["stock"]] == [("C1", "3")]
    assert [o["iOrder"] for o in t["recall"]["orders"]] == [2]  # order 1 is closed
    [src] = t["origin"]["sources"]
    assert (src["cKind"], src["cDocNo"], src["cSupplier"], src["cSupplierLot"]) == ("reception", "R1", "SUP", "")
    deep = t["uses"]["orders"][0]["outputs"][0]["orders"][0]["outputs"][0]
    assert (deep["cProduct"], deep["cLot"]) == ("C", "C1")


def test_a_loop_between_lots_ends():
    loop = ORDERS + [order(3, "A", [("C", "C1", "1")], [("A1", "1")])]
    t = service(MOVES, loop).trace("C", "C1")

    def depth(n, d=0):
        return max([d] + [depth(i, d + 1) for i in n["inputs"]])

    assert depth(t["origin"]) < 10
    again = t["origin"]["inputs"][0]["inputs"][0]["inputs"][0]  # C1 <- B1 <- A1 <- C1 again
    assert (again["cLot"], again.get("lLoop")) == ("C1", True)


def test_unknown_lot_and_lots_lookup():
    s = service(MOVES, ORDERS, {("B", "W", "L", "B1", ""): {"qty": 2.0}})
    try:
        s.trace("A", "")
        raise AssertionError("no error")
    except AppError as e:
        assert (e.code, e.status) == ("unknown_lot", 404)
    assert s.lots("b") == [{"code": "B1", "label": "2"}]
    assert [p["code"] for p in s.products()] == ["A", "B", "C"]
