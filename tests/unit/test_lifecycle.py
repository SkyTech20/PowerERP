"""DataLifecycle: the seed of a table replaced (the story of a demo scenario) and the rows of tables exported."""

import pytest

from powererp.modules.system import DataLifecycle


class Repo:
    def __init__(self):
        self.rows = []

    def replace_all(self, rows):
        self.rows = list(rows)

    def all(self):
        return list(self.rows)

    def clear(self):
        self.rows = []


def test_use_seed_replaces_the_seed_and_export_gives_it_back():
    life, orders, stock = DataLifecycle(), Repo(), Repo()
    life.add(orders, "prod_orders", [])
    life.add(stock, "inv_movements", [{"iNo": 1}])
    life.use_seed({"prod_orders": [{"iNo": 7}]})
    life.seed()
    assert orders.rows == [{"iNo": 7}] and stock.rows == [{"iNo": 1}]  # the other tables keep their seed
    orders.rows.append({"iNo": 8})
    assert life.export(("prod_orders",)) == {"prod_orders": [{"iNo": 7}, {"iNo": 8}]}
    life.seed()  # a reset goes back to the replaced seed, not to the rows of the moment
    assert orders.rows == [{"iNo": 7}]


def test_unknown_tables_are_refused():
    life = DataLifecycle()
    life.add(Repo(), "prod_orders", [])
    with pytest.raises(KeyError):
        life.use_seed({"nope": []})
    with pytest.raises(KeyError):
        life.export(("prod_orders", "nope"))
