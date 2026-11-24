"""Access control: the screens a role can be given, their actions, and the permission each API route needs.

A permission is "<screen>:<action>", e.g. "sales.invoices:post". The screens are the entries of the menu
(static/js/menu.js, same keys); the tabs of a screen share its permissions. Every screen has "view"; most also
have "create", "edit" and "delete"; some have their own actions (post, print, credit, approve, create_po).

Each API route (Flask endpoint) is classified here:
  OPEN_ENDPOINTS   any logged-in user (own account, lookups, dashboard, company header)
  ADMIN_ENDPOINTS  the administrator role only (users, roles, backups, system settings, demo data)
  a screen route   the permission of that screen; CRUD routes take the action from the HTTP method
                   (GET view, POST create, PUT edit, DELETE delete)
  a screen "read"  a GET another screen needs (the PO form reads the supplier): allowed with the view of
                   either screen
A route that is in none of these is refused (tests/test_permissions.py fails when one is added unclassified).
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field

CRUD = ("view", "create", "edit", "delete")
METHOD_ACTION = {"GET": "view", "HEAD": "view", "POST": "create", "PUT": "edit", "PATCH": "edit", "DELETE": "delete"}

# The routes of register_crud_routes and the hand-written CRUD routes: "<name>_collection" / "<name>_item".
ActionRule = str | Callable[[Mapping[str, str]], str]


@dataclass(frozen=True)
class Screen:
    key: str  # menu key, e.g. "sales.invoices"
    module: str  # menu group, e.g. "sales"
    actions: tuple[str, ...] = CRUD
    crud: tuple[str, ...] = ()  # endpoint prefixes with _collection / _item routes
    routes: Mapping[str, ActionRule] = field(default_factory=dict)  # endpoint -> action ("crud": by method)
    reads: tuple[str, ...] = ()  # GET endpoints of other screens this screen needs


def _recipe_action(args: Mapping[str, str]) -> str:
    action = args.get("action", "")
    if action == "copy":
        return "create"
    if action == "submit":
        return "edit"
    return "approve"  # approve, reject, obsolete, default (and unknown ones: 404 for whoever may approve)


SCREENS: tuple[Screen, ...] = (
    # General ledger
    Screen("gl.accounts", "gl", crud=("ledger.gl", "ledger.cc")),
    # Accounts payable
    Screen("ap.suppliers", "ap", crud=("suppliers.supplier",)),
    Screen(
        "ap.invoices",
        "ap",
        crud=("purchasing.inv",),
        reads=("suppliers.supplier_item", "purchasing.po_item"),
    ),
    # Purchasing
    Screen("pur.po", "pur", crud=("purchasing.po",), reads=("suppliers.supplier_item",)),
    Screen(
        "pur.receptions",
        "pur",
        crud=("purchasing.rec",),
        reads=("suppliers.supplier_item", "purchasing.po_item"),
    ),
    # Sales
    Screen("sales.customers", "sales", crud=("sales.customers",)),
    Screen("sales.priceLists", "sales", crud=("sales.price_lists",), routes={"sales.price_of": "view"}),
    Screen(
        "sales.invoices",
        "sales",
        actions=(*CRUD, "post", "credit", "print"),
        routes={
            "sales.sales_invoices": "crud",
            "sales.sales_invoice": "crud",
            "sales.sales_invoice_calc": "view",
            "sales.sales_invoice_check": "view",
            "sales.sales_invoice_post": "post",
            "sales.sales_invoice_credit": "credit",
            "sales.sales_invoice_print": "print",
        },
        reads=("sales.price_of",),
    ),
    # Inventory
    Screen("inv.items", "inv", crud=("inventory.products",), routes={"inventory.products_unit_check": "view"}),
    Screen("inv.stock", "inv", actions=("view",), routes={"inventory.inventory_stock": "view"}),
    Screen("inv.movements", "inv", crud=("inventory.movements",)),
    Screen(
        "inv.replenishment",
        "inv",
        actions=("view", "create_po"),
        routes={"inventory.inventory_replenishment": "view", "inventory.replenishment_po": "create_po"},
    ),
    Screen(
        "inv.count",
        "inv",
        actions=(*CRUD, "post"),
        crud=("inventory.counts",),
        routes={"inventory.counts_generate": "edit", "inventory.counts_post": "post"},
    ),
    Screen("inv.valuation", "inv", actions=("view",), routes={"inventory.inventory_valuation": "view"}),
    Screen("inv.warehouses", "inv", crud=("inventory.warehouses", "inventory.locations")),
    Screen("inv.params", "inv", crud=("inventory.stock_params",)),
    Screen(
        "inv.setup",
        "inv",
        crud=("catalog.categories", "catalog.uom", "catalog.uom_conversions"),
        routes={"catalog.conversion_factor": "view", "catalog.add_standard_conversions": "create"},
    ),
    # Production
    Screen(
        "prod.recipes",
        "prod",
        actions=(*CRUD, "approve"),
        crud=("production.recipes",),
        routes={
            "production.recipe_action": _recipe_action,
            "production.recipe_explode": "view",
            "production.recipe_step_check": "view",
            "production.recipe_compare": "view",
            "production.product_current_recipe": "view",
        },
    ),
    Screen("prod.items", "prod", crud=("production.product_mfg",)),
    Screen(
        "prod.operations",
        "prod",
        crud=("production.operations",),
        routes={"production.operation_time": "view"},
        reads=("production.capability_resources", "production.resources_collection"),
    ),
    Screen(
        "prod.resources",
        "prod",
        crud=("production.resources",),
        routes={"production.resource_availability": "view"},
    ),
    Screen(
        "prod.workcenters",
        "prod",
        crud=("production.work_centers",),
        routes={"production.work_center_availability": "view"},
        reads=("production.resources_collection",),
    ),
    Screen(
        "prod.setupmatrix",
        "prod",
        crud=("production.setup_matrices",),
        routes={"production.setup_matrix_grid": "view", "production.setup_changeover": "view"},
    ),
    Screen(
        "prod.calendars",
        "prod",
        crud=("production.calendars", "production.calendar_exceptions"),
        routes={"production.calendar_availability": "view"},
    ),
    Screen(
        "prod.setup",
        "prod",
        crud=(
            "production.capabilities",
            "production.setup_families",
            "production.downtime_reasons",
            "production.scrap_reasons",
        ),
        routes={"production.capability_resources": "view"},
    ),
    # Administration (the screens any role can be given; users, roles, backups and settings: ADMIN_ENDPOINTS)
    Screen(
        "admin.taxes", "admin", crud=("taxes.tax_codes", "taxes.tax_groups"), routes={"taxes.tax_group_calc": "view"}
    ),
)

SCREEN_BY_KEY = {s.key: s for s in SCREENS}

# Any logged-in user.
OPEN_ENDPOINTS = frozenset(
    {
        "auth.health",
        "auth.login",
        "auth.logout",
        "auth.me",
        "auth.change_password",
        "auth.set_lang",
        "system.index",
        "system.assets",
        "system.lookup",  # code + description lists of the form fields
        "system.summary",  # dashboard
        "sales.company_profile",  # header of the documents
        "static",
    }
)

# The administrator role only.
ADMIN_ENDPOINTS = frozenset(
    {
        "auth.users_collection",
        "auth.users_item",
        "auth.permission_catalog",
        "auth.roles_collection",
        "auth.roles_item",
        "auth.role_history",
        "backup.backup_settings",
        "backup.backup_file",
        "backup.backup_run",
        "sales.company_save",
        "system.demo",
        "system.reset",
        "system.clear",
    }
)


# The figures of the dashboard (/api/summary): the screen whose view shows each one.
DASHBOARD_KEYS = {
    "glAccounts": "gl.accounts",
    "costCenters": "gl.accounts",
    "suppliers": "ap.suppliers",
    "activeSuppliers": "ap.suppliers",
    "invoices": "ap.invoices",
    "openInvoices": "ap.invoices",
    "openInvoicesAmount": "ap.invoices",
    "recentInvoices": "ap.invoices",
    "purchaseOrders": "pur.po",
    "unbilledPOs": "pur.po",
    "receptions": "pur.receptions",
    "unbilledReceptions": "pur.receptions",
    "products": "inv.valuation",
    "warehouses": "inv.valuation",
    "stockValue": "inv.valuation",
    "reorderItems": "inv.valuation",
}


def dashboard_for(summary: Mapping[str, object], can: Callable[[str], bool]) -> dict[str, object]:
    """The figures of the dashboard the user may see (a figure no screen claims is left out)."""
    return {k: v for k, v in summary.items() if k in DASHBOARD_KEYS and can(DASHBOARD_KEYS[k] + ":view")}


def all_permissions() -> list[str]:
    """Every permission a role can be given, in menu order."""
    return [f"{s.key}:{a}" for s in SCREENS for a in s.actions]


def _index() -> tuple[dict[str, list[tuple[str, ActionRule]]], dict[str, list[str]]]:
    rules: dict[str, list[tuple[str, ActionRule]]] = {}
    reads: dict[str, list[str]] = {}
    for s in SCREENS:
        for prefix in s.crud:
            for suffix in ("_collection", "_item"):
                rules.setdefault(prefix + suffix, []).append((s.key, "crud"))
        for endpoint, rule in s.routes.items():
            rules.setdefault(endpoint, []).append((s.key, rule))
        for endpoint in s.reads:
            reads.setdefault(endpoint, []).append(s.key)
    return rules, reads


_RULES, _READS = _index()


def classified(endpoint: str) -> bool:
    """True when the endpoint has an access rule (used by the coverage test)."""
    return endpoint in OPEN_ENDPOINTS or endpoint in ADMIN_ENDPOINTS or endpoint in _RULES


def required(endpoint: str, method: str, args: Mapping[str, str]) -> list[str] | None:
    """The permissions that each allow the call (any one is enough); None for an unclassified endpoint."""
    if endpoint not in _RULES:
        return None
    needed = []
    for screen, rule in _RULES[endpoint]:
        action = rule(args) if callable(rule) else rule
        if action == "crud":
            action = METHOD_ACTION.get(method.upper(), "edit")
        needed.append(f"{screen}:{action}")
    if method.upper() in ("GET", "HEAD"):
        needed += [f"{screen}:view" for screen in _READS.get(endpoint, [])]
    return needed


def allowed(endpoint: str | None, method: str, args: Mapping[str, str], perms: Iterable[str], admin: bool) -> bool:
    """May a user with these permissions (or the administrator role) call this endpoint?"""
    if endpoint is None or endpoint in OPEN_ENDPOINTS:
        return True  # no route (404) or open to every logged-in user
    if admin:
        return True
    if endpoint in ADMIN_ENDPOINTS:
        return False
    needed = required(endpoint, method, args)
    if needed is None:
        return False  # unclassified: refused until it gets a rule
    have = set(perms)
    return any(p in have for p in needed)


def clean(perms: Iterable[str]) -> list[str]:
    """Known permissions only, without duplicates, in menu order."""
    wanted = set(perms)
    return [p for p in all_permissions() if p in wanted]
