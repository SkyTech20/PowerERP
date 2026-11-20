"""Production tables. M0: the reference lists of the shop floor (capabilities, setup families, stop and scrap
reasons). The resources, recipes and production orders follow in the next milestones (Docs/PowerERP-Producao-Plano.md).
"""

from .. import schemas as S
from .master import TableSpec, register_specs

register_specs(
    TableSpec("capabilities", S.CAPABILITY, order=("cCode",)),
    TableSpec("setup_families", S.SETUP_FAMILY, order=("cCode",)),
    TableSpec("downtime_reasons", S.DOWNTIME_REASON, order=("cCode",)),
    TableSpec("scrap_reasons", S.SCRAP_REASON, order=("cCode",)),
)
