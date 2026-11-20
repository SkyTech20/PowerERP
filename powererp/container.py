"""A small dependency container: the factory registers the services once, the modules ask for them.

It replaces module-level globals: two apps in the same process (tests) each have their own container.
    container.register("purchase_orders", PurchaseOrderService(...))
    container.get("purchase_orders")
"""

from __future__ import annotations

from typing import Any


class Container:
    def __init__(self) -> None:
        self._items: dict[str, Any] = {}

    def register(self, name: str, item: Any) -> Any:
        if name in self._items:
            raise KeyError(f"{name} already registered")
        self._items[name] = item
        return item

    def get(self, name: str) -> Any:
        try:
            return self._items[name]
        except KeyError:
            raise KeyError(f"{name} is not registered") from None

    def __contains__(self, name: str) -> bool:
        return name in self._items


def container_of(app) -> Container:
    """The container of a Flask app (created by powererp.factory.create_app)."""
    return app.extensions["powererp"]
