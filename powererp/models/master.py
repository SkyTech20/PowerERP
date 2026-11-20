"""Master data tables (phase R1): general ledger, suppliers, taxes, units, categories, products, warehouses, locations.

Each table is built from its field schema (powererp/schemas.py), the same one the API validates with, so the
API field (cDescFR) and the column (desc_fr) cannot drift apart. Kinds: s -> TEXT NOT NULL DEFAULT '',
d -> NUMERIC (unconstrained: keeps the scale that was typed, "12.50" stays 12.50; empty = NULL),
i -> INTEGER, b -> BOOLEAN, date -> DATE, (choices) -> VARCHAR with a CHECK.
Documents with lines (tax rate history, tax group taxes, product suppliers) get a child table <name>_lines.
Every table has id (primary key) and company_id; codes are unique per company, ignoring case.
"""

import re
from dataclasses import dataclass, field

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Table,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB

from .. import schemas as S
from ..database import Base

_OVERRIDES = {
    "cDesc": "description",
    "cGLCOGS": "gl_cogs",
    "cGLSales": "gl_sales",
    "cGLPurchase": "gl_purchase",
    "cGLInventory": "gl_inventory",
    "cGLCollected": "gl_collected",
    "cGLRecoverable": "gl_recoverable",
    "cGroup": "reason_group",  # "group" is an SQL keyword
    "lDefault": "is_default",  # "default" too
}


def column_name(api_name):
    """cDescFR -> desc_fr, dPurchaseFactor -> purchase_factor, lPORequired -> po_required, iTypePO -> type_po."""
    if api_name in _OVERRIDES:
        return _OVERRIDES[api_name]
    name = api_name[1:] if len(api_name) > 1 and api_name[0] in "cdilb" and api_name[1].isupper() else api_name
    name = re.sub(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])", "_", name)
    return name.lower()


def _column(api_name, kind, table):
    col = column_name(api_name)
    if isinstance(kind, tuple):
        allowed = ", ".join("'" + k + "'" for k in kind)
        return Column(
            col,
            String(30),
            nullable=False,
            server_default=kind[0],
            info={"check": CheckConstraint(f"{col} IN ({allowed})", name=f"ck_{table}_{col}")},
        )
    if kind == "d":
        return Column(col, Numeric, nullable=True)
    if kind == "i":
        return Column(col, Integer, nullable=False, server_default="0")
    if kind == "b":
        return Column(col, Boolean, nullable=False, server_default="false")
    if kind == "date":
        return Column(col, Date, nullable=True)
    if kind == "ts":
        return Column(col, DateTime, nullable=True)
    if kind == "json":
        return Column(col, JSONB, nullable=True)
    return Column(col, Text, nullable=False, server_default="")


def _key_expr(api_name, kind):
    """Text keys are unique ignoring case; other keys (numbers) as they are."""
    col = column_name(api_name)
    return f"lower({col})" if kind == "s" else col


@dataclass
class TableSpec:
    name: str  # table name
    schema: dict  # API fields -> kind
    keys: tuple = ("cCode",)  # business key (unique per company, case-insensitive)
    order: tuple = ()  # default order of lists (API fields); () = insertion order
    extra: dict = field(default_factory=dict)  # stored fields outside the input schema (read-only in the API)
    line_schema: dict | None = None  # the child list "lines" (table <name>_lines)
    children: dict = field(default_factory=dict)  # other child lists: key -> schema (table <name>_<key>)
    sparse: tuple = ()  # fields left out of a record while they are empty (NULL)
    table: Table | None = None
    lines: Table | None = None
    child_tables: dict = field(default_factory=dict)  # key -> Table, "lines" included

    @property
    def fields(self):
        return {**self.schema, **self.extra}

    def child_schemas(self) -> dict:
        """Every child list of a record: key in the API ("lines", "capabilities"...) -> field schema."""
        return {**({"lines": self.line_schema} if self.line_schema else {}), **self.children}


def _build(spec):
    cols = [_column(f, k, spec.name) for f, k in spec.fields.items()]
    checks = [c.info.pop("check") for c in cols if "check" in c.info]
    key_expr = ", ".join(_key_expr(k, spec.fields[k]) for k in spec.keys)
    spec.table = Table(
        spec.name,
        Base.metadata,
        Column("id", BigInteger, primary_key=True, autoincrement=True),
        Column("company_id", BigInteger, ForeignKey("companies.id"), nullable=False, index=True),
        *cols,
        *checks,
        Index(
            f"uq_{spec.name}_key",
            text("company_id"),
            *[text(_key_expr(k, spec.fields[k])) for k in spec.keys],
            unique=True,
        ),
        comment=f"business key: {key_expr}",
    )
    for key, schema in spec.child_schemas().items():
        name = f"{spec.name}_{key}"
        lcols = [_column(f, k, name) for f, k in schema.items()]
        lchecks = [c.info.pop("check") for c in lcols if "check" in c.info]
        spec.child_tables[key] = Table(
            name,
            Base.metadata,
            Column("id", BigInteger, primary_key=True, autoincrement=True),
            Column(
                "parent_id", BigInteger, ForeignKey(f"{spec.name}.id", ondelete="CASCADE"), nullable=False, index=True
            ),
            Column("line_no", Integer, nullable=False),
            *lcols,
            *lchecks,
        )
    spec.lines = spec.child_tables.get("lines")
    return spec


SPECS = {
    s.name: _build(s)
    for s in (
        TableSpec("gl_accounts", S.GL_ACCOUNT, order=("cCode",)),
        TableSpec("cost_centers", S.COST_CENTER, keys=("cCC1", "cCC2"), order=("cCC1", "cCC2")),
        TableSpec("suppliers", S.SUPPLIER),
        TableSpec("tax_codes", S.TAX_CODE, order=("cCode",), line_schema=S.TAX_RATE),
        TableSpec("tax_groups", S.TAX_GROUP, order=("cCode",), line_schema=S.TAX_GROUP_LINE),
        TableSpec("uoms", S.UOM, order=("cCode",)),
        TableSpec("product_categories", S.CATEGORY, order=("cCode",)),
        TableSpec(
            "products",
            S.PRODUCT,
            order=("cCode",),
            extra={"dAvgCost": "d", "dLastCost": "d"},
            line_schema=S.PRODUCT_SUPPLIER,
        ),
        TableSpec("warehouses", S.WAREHOUSE, order=("cCode",)),
        TableSpec("locations", S.LOCATION, keys=("cWarehouse", "cCode"), order=("cWarehouse", "iPickSeq", "cCode")),
        # ---- stock (R3)
        TableSpec("stock_params", S.STOCK_PARAM, keys=("cProduct", "cWarehouse")),
        # The movement ledger: rows are only ever inserted (a movement is corrected by another movement)
        TableSpec(
            "stock_movements",
            S.MOVEMENT,
            keys=("iNo",),
            order=("iNo",),
            extra={"iNo": "i", "dValue": "d", "dAvgCostAfter": "d", "cUser": "s", "dCreated": "ts"},
        ),
        TableSpec(
            "stock_counts",
            S.COUNT,
            keys=("iNo",),
            order=("iNo",),
            extra={
                "iNo": "i",
                "cStatus": S.COUNT_STATUS,
                "cUser": "s",
                "dPosted": "ts",
                "dValueDiff": "d",
                "movements": "json",
            },
            line_schema={**S.COUNT_LINE, "cDescFR": "s", "dDiff": "d"},
            sparse=("dPosted", "dValueDiff", "movements"),
        ),
    )
}


def register_specs(*specs: TableSpec) -> None:
    """Tables of a module defined outside this file (e.g. models/production.py), reachable through store(name)."""
    for spec in specs:
        if spec.name in SPECS:
            raise ValueError(f"table {spec.name} defined twice")
        SPECS[spec.name] = _build(spec)
