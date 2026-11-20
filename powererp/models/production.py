"""Production tables, step by step (Docs/PowerERP-Cadastros-Plano.md).

P1: the reference lists of the shop floor (capabilities, setup families, stop and scrap reasons).
P2: working calendars (shifts by weekday as lines) and their exceptions by date.
P3: work centers.
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
)
