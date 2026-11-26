"""Relational models. Import every module here so Alembic sees all the tables."""

from . import (
    production,  # noqa: F401  (production reference lists)
    purchasing,  # noqa: F401  (purchase orders, receptions, invoices)
    quality,  # noqa: F401  (lot status, nonconformances)
    sales,  # noqa: F401  (company profile, customers)
    stock,  # noqa: F401  (stock balances)
)
from .core import (  # noqa: F401
    AuditEvent,
    Company,
    DocSequence,
    LegacyDataset,
    Role,
    RoleHistory,
    RolePermission,
    Setting,
    User,
)
from .master import SPECS  # noqa: F401
