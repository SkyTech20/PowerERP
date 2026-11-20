"""Stock balances (phase R3): on hand and reserved quantity per product, warehouse, location, lot and serial.

Updated in the same transaction as each movement (stock_movements is the ledger, this table its running total),
so reading the stock no longer replays every movement. The texts keep the spelling of the first movement;
the key ignores case, like everywhere else in the ERP.
"""
from sqlalchemy import BigInteger, Column, Date, ForeignKey, Index, Numeric, Table, Text, text

from ..database import Base

stock_balances = Table(
    "stock_balances", Base.metadata,
    Column("id", BigInteger, primary_key=True, autoincrement=True),
    Column("company_id", BigInteger, ForeignKey("companies.id"), nullable=False),
    Column("product", Text, nullable=False),
    Column("warehouse", Text, nullable=False),
    Column("location", Text, nullable=False, server_default=""),
    Column("lot", Text, nullable=False, server_default=""),
    Column("serial", Text, nullable=False, server_default=""),
    Column("qty", Numeric, nullable=False, server_default="0"),
    Column("reserved", Numeric, nullable=False, server_default="0"),
    Column("expiry", Date, nullable=True),
    Index("uq_stock_balances_key", "company_id", text("lower(product)"), text("lower(warehouse)"),
          text("lower(location)"), text("lower(lot)"), text("lower(serial)"), unique=True),
)
