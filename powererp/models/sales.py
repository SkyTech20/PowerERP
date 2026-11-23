"""Sales tables, step by step (V1 to V6).

V1: the company profile (one row: the header of the invoices) and the customers, with their ship-to addresses and
contacts (child tables customers_addresses, customers_contacts).
V2: the price lists, with their prices by product and quantity (price_lists_lines) and their discounts by
product category (price_lists_discounts); a customer points to its price list.
V3: the sales invoices (drafts), with their lines and their taxes by tax code (sales_invoices_taxes).
"""

from .. import schemas as S
from .master import TableSpec, register_specs

register_specs(
    TableSpec("company_profile", S.COMPANY_PROFILE),
    TableSpec(
        "price_lists",
        S.PRICE_LIST,
        order=("cCode",),
        line_schema=S.PRICE_LIST_LINE,
        children={"discounts": S.PRICE_LIST_DISCOUNT},
    ),
    TableSpec(
        "sales_invoices",
        S.SALES_INVOICE,
        keys=("iNo",),
        order=("iNo",),
        extra=S.SALES_INVOICE_EXTRA,
        line_schema=S.SALES_INVOICE_LINE,
        children={"taxes": S.SALES_INVOICE_TAX},
    ),
    TableSpec(
        "customers",
        S.CUSTOMER,
        order=("cCode",),
        children={"addresses": S.CUSTOMER_ADDRESS, "contacts": S.CUSTOMER_CONTACT},
    ),
)
