"""Sales tables, step by step (V1 to V6).

V1: the company profile (one row: the header of the invoices) and the customers, with their ship-to addresses and
contacts (child tables customers_addresses, customers_contacts).
"""

from .. import schemas as S
from .master import TableSpec, register_specs

register_specs(
    TableSpec("company_profile", S.COMPANY_PROFILE),
    TableSpec(
        "customers",
        S.CUSTOMER,
        order=("cCode",),
        children={"addresses": S.CUSTOMER_ADDRESS, "contacts": S.CUSTOMER_CONTACT},
    ),
)
