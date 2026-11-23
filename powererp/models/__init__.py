"""Relational models. Import every module here so Alembic sees all the tables."""

from . import (
    production,  # noqa: F401  (production reference lists)
    purchasing,  # noqa: F401  (purchase orders, receptions, invoices)
    sales,  # noqa: F401  (company profile, customers)
    stock,  # noqa: F401  (stock balances)
)
from .core import Company, DocSequence, LegacyDataset, Setting, User  # noqa: F401
from .master import SPECS  # noqa: F401
