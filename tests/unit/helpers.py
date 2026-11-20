"""Helpers of the unit tests: memory repositories and stand-ins (no Flask, no database)."""

import copy

from powererp.modules.common.memory import MemoryRepository


def memory(rows=(), keys=("cCode",)):
    """A MemoryRepository holding copies of `rows` (the test constants stay untouched)."""
    return MemoryRepository(copy.deepcopy(list(rows)), keys=keys)


class Numbering:
    """Stand-in of the document numbering: 1, 2, 3... per kind."""

    def __init__(self):
        self.last = {}

    def next(self, kind):
        self.last[kind] = self.last.get(kind, 0) + 1
        return self.last[kind]


def receive(stock, product="P1", qty="10", location="A-1", cost="2"):
    return stock.add(
        {"cType": "IN", "cProduct": product, "dQty": qty, "cWarehouse": "W1", "cLocation": location, "dUnitCost": cost}
    )
