"""System module: the screens' files, the dashboard, the lookups, and the demo data life cycle (reset / clear).

DataLifecycle replaces the old "hooks": each module registers the tables it seeds and what to do after a load
or a clear; /api/reset loads the demo data again, /api/clear empties everything.
"""

from __future__ import annotations

import copy
from collections.abc import Callable
from pathlib import Path
from typing import Any

from flask import Blueprint, Flask, jsonify, request, send_from_directory

from powererp.container import Container
from powererp.core.errors import NotFound
from powererp.modules.common.registry import LookupRegistry

STATIC_DIR = Path(__file__).resolve().parent.parent.parent.parent / "static"

Loader = Callable[[dict], None]


class DataLifecycle:
    """The tables seeded with the demo data. Two kinds:
    - a repository with one key and its seed rows (add): loaded with replace_all, emptied with clear;
    - a custom dataset (add_dataset): keys, a loader of those keys, a clearer and its seed (e.g. the purchase
      orders, rebuilt from two PowerWARE lists).
    after_load / on_clear: what follows a load (e.g. stock balances recalculated from the movements) or a clear.
    """

    def __init__(self) -> None:
        self._repos: list[tuple[Any, str]] = []
        self._datasets: list[tuple[tuple[str, ...], Loader, Callable[[], None]]] = []
        self._after_load: list[Loader] = []
        self._on_clear: list[Callable[[], None]] = []
        self._snapshot: dict[str, Any] = {}

    def add(self, repo: Any, key: str, rows: list) -> None:
        self._repos.append((repo, key))
        self._snapshot[key] = copy.deepcopy(rows)

    def add_stores(self, triples) -> None:
        """Compatibility with the modules not reorganized yet: [(repo, key, rows), ...]."""
        for repo, key, rows in triples:
            self.add(repo, key, rows)

    def add_dataset(self, seed: dict[str, Any], load: Loader, clear: Callable[[], None]) -> None:
        self._datasets.append((tuple(seed), load, clear))
        self._snapshot.update(copy.deepcopy(seed))

    def after_load(self, fn: Loader) -> None:
        self._after_load.append(fn)

    def on_clear(self, fn: Callable[[], None]) -> None:
        self._on_clear.append(fn)

    def keys(self) -> list[str]:
        return [key for _repo, key in self._repos] + [k for keys, _l, _c in self._datasets for k in keys]

    def load(self, data: dict[str, Any]) -> None:
        """Load the keys present in `data` (the demo snapshot, or the JSON of an older database)."""
        for repo, key in self._repos:
            if key in data:
                repo.replace_all(data[key])
        for keys, loader, _clear in self._datasets:
            if any(k in data for k in keys):
                loader(data)
        for fn in self._after_load:
            fn(data)

    def seed(self) -> None:
        self.load(copy.deepcopy(self._snapshot))

    def clear(self) -> None:
        for fn in self._on_clear:
            fn()
        for _keys, _loader, clear in reversed(self._datasets):
            clear()
        for repo, _key in reversed(self._repos):
            repo.clear()


class DashboardRegistry(list):
    """Functions returning the figures of a module for the dashboard (/api/summary)."""

    def register(self, fn: Callable[[], dict]) -> None:
        self.append(fn)

    def summary(self) -> dict:
        return {k: v for fn in self for k, v in fn().items()}


def _blueprint(lifecycle: DataLifecycle, dashboard: DashboardRegistry, lookups: LookupRegistry) -> Blueprint:
    bp = Blueprint("system", __name__)

    @bp.route("/")
    def index():
        return send_from_directory(STATIC_DIR, "index.html")

    @bp.route("/assets/<path:filename>")
    def assets(filename):
        # ES modules need a JavaScript MIME type (some Windows set-ups map .js to text/plain)
        mimetype = "text/javascript" if filename.endswith(".js") else None
        return send_from_directory(STATIC_DIR, filename, mimetype=mimetype)

    @bp.route("/api/summary")
    def summary():
        return jsonify(dashboard.summary())

    @bp.route("/api/lookups/<kind>")
    def lookup(kind):
        if kind not in lookups:
            raise NotFound()
        rows, limit = lookups[kind]()
        q = (request.args.get("q") or "").strip().lower()
        if q:
            rows = [r for r in rows if q in r["code"].lower() or q in (r["label"] or "").lower()]
        return jsonify(rows if request.args.get("all") else rows[:limit])

    @bp.route("/api/reset", methods=["POST"])
    def reset():
        lifecycle.seed()
        return jsonify({"ok": True})

    @bp.route("/api/clear", methods=["POST"])
    def clear():
        """Empty every table (for demos that start from a blank ERP). /api/reset brings the demo data back."""
        lifecycle.clear()
        return jsonify({"ok": True})

    return bp


def register(app: Flask, c: Container) -> None:
    lifecycle = c.register("lifecycle", DataLifecycle())
    dashboard = c.register("dashboard", DashboardRegistry())
    lookups = c.register("lookups", LookupRegistry())
    app.register_blueprint(_blueprint(lifecycle, dashboard, lookups))
