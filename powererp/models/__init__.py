"""Relational models. Import every module here so Alembic sees all the tables."""
from .core import Company, DocSequence, LegacyDataset, Setting, User  # noqa: F401
from .master import SPECS  # noqa: F401
from . import purchasing  # noqa: F401  (purchase orders, receptions, invoices)
