"""Unit tests of the pick order of the stock (sales invoices and production orders): FEFO, FIFO, LIFO."""

from powererp.modules.inventory.picking import pick_order, pick_policy


def bal(lot, loc, qty, expiry="", reserved=0.0):
    return (
        ("P1", "W1", loc, lot, ""),
        {"cLocation": loc, "cLot": lot, "cSerial": "", "qty": qty, "reserved": reserved, "dExpiry": expiry},
    )


BAL = dict(
    [
        bal("L-NEW", "A", 5, "2027-02-01"),
        bal("L-OLD", "B", 5, "2026-12-01"),
        bal("L-GONE", "C", 5, "2026-11-01"),  # expired on the day
        bal("L-RES", "D", 5, "2026-12-15", reserved=5),  # all reserved
        bal("L-BLK", "X", 5, "2026-11-30"),  # blocked location
    ]
)
RECEIVED = {  # first received, movement, last received, movement
    ("P1", "W1", "A", "L-NEW", ""): ("2026-10-01", 1, "2026-10-01", 1),
    ("P1", "W1", "B", "L-OLD", ""): ("2026-11-01", 2, "2026-11-01", 2),
}


def lots(prod, day="2026-11-25"):
    return [b["cLot"] for b, _free in pick_order(prod, "w1", BAL, day, RECEIVED, lambda loc: loc != "X")]


def test_policy_of_a_product():
    assert pick_policy({"lExpiryControl": True}) == "FEFO"
    assert pick_policy({}) == "FIFO"
    assert pick_policy({"cPickPolicy": "LIFO", "lExpiryControl": True}) == "LIFO"


def test_fefo_fifo_lifo():
    assert lots({"cCode": "p1", "lExpiryControl": True}) == ["L-OLD", "L-NEW"]  # no expired, reserved or blocked
    assert lots({"cCode": "P1", "cPickPolicy": "FIFO", "lExpiryControl": True}) == ["L-NEW", "L-OLD"]
    assert lots({"cCode": "P1", "cPickPolicy": "LIFO", "lExpiryControl": True}) == ["L-OLD", "L-NEW"]
    # without expiry control, an expired date does not stop the stock
    assert "L-GONE" in lots({"cCode": "P1", "cPickPolicy": "FIFO"})
