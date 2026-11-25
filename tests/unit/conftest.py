"""Fixtures of the unit tests: services on memory repositories (no Flask, no database)."""

import pytest

from tests.unit.helpers import memory


@pytest.fixture
def inventory():
    """The inventory services on one warehouse W1 (locations A-1, A-2), products P1 / P2 and a service SVC."""
    from powererp.modules.inventory import build_services
    from powererp.modules.inventory.ledger import MemoryLedger

    repos = {
        "warehouses": memory(
            [
                {
                    "cCode": "W1",
                    "cNameFR": "Entrepôt",
                    "cReceivingLoc": "",
                    "cShippingLoc": "",
                    "lUseLocations": True,
                    "lAllowNegative": False,
                }
            ]
        ),
        "locations": memory(
            [
                {"cWarehouse": "W1", "cCode": "A-1", "lActive": True, "lMixProducts": True},
                {"cWarehouse": "W1", "cCode": "A-2", "lActive": True, "lMixProducts": True},
            ],
            keys=("cWarehouse", "cCode"),
        ),
        "products": memory(
            [
                {"cCode": "P1", "cDescFR": "Vis", "lStocked": True, "cCostMethod": "avg", "dAvgCost": "", "lines": []},
                {
                    "cCode": "P2",
                    "cDescFR": "Écrou",
                    "lStocked": True,
                    "cCostMethod": "avg",
                    "dAvgCost": "",
                    "lines": [],
                },
                {"cCode": "SVC", "cDescFR": "Service", "lStocked": False, "lines": []},
            ]
        ),
        "stock_params": memory([], keys=("cProduct", "cWarehouse")),
    }
    services = build_services(repos, MemoryLedger(), {}, username=lambda: "tester")
    services["repos"] = repos
    return services
