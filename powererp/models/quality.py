"""Quality tables (step 5 of the SCOR / ISO plan).

lot_status: the status of a lot of a product (released, on hold, quarantine, rejected) and its history; a lot
without a row is released.
nonconformances: what was found wrong (product, lot, quantity), its cause, what is done with it (disposition) and
the corrective action, with its history.
"""

from .. import schemas as S
from .master import TableSpec, register_specs

register_specs(
    TableSpec(
        "lot_status",
        S.LOT_STATUS,
        keys=("cProduct", "cLot"),
        order=("cProduct", "cLot"),
        extra=S.LOT_STATUS_EXTRA,
        children={"history": S.LOT_STATUS_HISTORY},
    ),
    TableSpec(
        "nonconformances",
        S.NONCONFORMANCE,
        keys=("iNo",),
        order=("iNo",),
        extra=S.NONCONFORMANCE_EXTRA,
        sparse=("dClosed",),
        children={"history": S.NC_HISTORY},
    ),
)
