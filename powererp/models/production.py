"""Production tables, step by step (Docs/PowerERP-Cadastros-Plano.md).

P1: the reference lists of the shop floor (capabilities, setup families, stop and scrap reasons).
P2: working calendars (shifts by weekday as lines) and their exceptions by date.
P3: work centers.
P4: resources, with their capabilities, attributes, subresources and planned downtime (child tables).
P5: standard operations.
P6: setup matrices (one per work center or resource, the family pairs as lines).
P7: manufacturing data of the products (1 to 1 with the item master), with their attributes.
P8: recipes (product + revision) with their materials, outputs (co / by-products) and operations.
P9: the steps of the recipe operations (child list recipes_steps, by operation).
P10: approval of the recipes: who / when, validity, default version, history (recipes_history).
M3: production orders, with the materials and operations of their recipe and the history of their status.
"""

from .. import schemas as S
from .master import TableSpec, register_specs

register_specs(
    TableSpec("capabilities", S.CAPABILITY, order=("cCode",)),
    TableSpec("setup_families", S.SETUP_FAMILY, order=("cCode",)),
    TableSpec("downtime_reasons", S.DOWNTIME_REASON, order=("cCode",)),
    TableSpec("scrap_reasons", S.SCRAP_REASON, order=("cCode",)),
    TableSpec("calendars", S.CALENDAR, order=("cCode",), line_schema=S.CALENDAR_SHIFT),
    TableSpec("calendar_exceptions", S.CALENDAR_EXCEPTION, keys=("cCalendar", "dDate"), order=("dDate", "cCalendar")),
    TableSpec("work_centers", S.WORK_CENTER, order=("cCode",)),
    TableSpec(
        "resources",
        S.RESOURCE,
        order=("cCode",),
        children={
            "capabilities": S.RESOURCE_CAPABILITY,
            "attributes": S.RESOURCE_ATTRIBUTE,
            "subresources": S.RESOURCE_SUBRESOURCE,
            "downtime": S.RESOURCE_DOWNTIME,
        },
    ),
    TableSpec("operations", S.OPERATION, order=("cCode",)),
    TableSpec(
        "setup_matrices",
        S.SETUP_MATRIX,
        keys=("cScope", "cScopeCode"),
        order=("cScope", "cScopeCode"),
        line_schema=S.SETUP_MATRIX_LINE,
    ),
    TableSpec(
        "product_mfg",
        S.PRODUCT_MFG,
        keys=("cProduct",),
        order=("cProduct",),
        children={"attributes": S.PRODUCT_ATTRIBUTE},
    ),
    TableSpec(
        "recipes",
        S.RECIPE,
        keys=("cProduct", "cRevision"),
        order=("cProduct", "cRevision"),
        extra=S.RECIPE_EXTRA,
        sparse=("dApprovedAt",),
        children={
            "materials": S.RECIPE_MATERIAL,
            "outputs": S.RECIPE_OUTPUT,
            "operations": S.RECIPE_OPERATION,
            "steps": S.RECIPE_STEP,
            "history": S.RECIPE_HISTORY,
        },
    ),
    TableSpec(
        "production_orders",
        S.PRODUCTION_ORDER,
        keys=("iNo",),
        order=("iNo",),
        extra=S.PRODUCTION_ORDER_EXTRA,
        sparse=("dReleased",),
        children={"materials": S.ORDER_MATERIAL, "operations": S.ORDER_OPERATION, "history": S.ORDER_HISTORY},
    ),
)
