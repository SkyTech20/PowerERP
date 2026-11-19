"""Relational models. Import every module here so Alembic sees all the tables."""
from .core import Company, DocSequence, LegacyDataset, Setting, User  # noqa: F401
