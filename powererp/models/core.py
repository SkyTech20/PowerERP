"""Core tables: companies, users, settings, document numbering and the transition table."""
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, CheckConstraint, DateTime, ForeignKey, Index, String, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base

ROLES = ("admin", "user")
LANGS = ("en", "fr")


class Company(Base):
    """A company (legal entity / plant). Master data and documents get a company_id as they move here."""
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(20), unique=True)
    name: Mapped[str] = mapped_column(String(200))
    active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        Index("uq_users_username_lower", text("lower(username)"), unique=True),
        CheckConstraint("role IN ('admin', 'user')", name="ck_users_role"),
        CheckConstraint("lang IN ('en', 'fr')", name="ck_users_lang"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(80))
    name: Mapped[str] = mapped_column(String(200), default="", server_default="")
    email: Mapped[str] = mapped_column(String(200), default="", server_default="")
    role: Mapped[str] = mapped_column(String(20), default="user", server_default="user")
    lang: Mapped[str] = mapped_column(String(5), default="en", server_default="en")
    active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    password_hash: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Setting(Base):
    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[str] = mapped_column(Text)


class DocSequence(Base):
    """Next number of each document type, per company (taken with SELECT ... FOR UPDATE)."""
    __tablename__ = "doc_sequences"

    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), primary_key=True)
    doc_type: Mapped[str] = mapped_column(String(20), primary_key=True)
    prefix: Mapped[str] = mapped_column(String(20), default="", server_default="")
    next_value: Mapped[int] = mapped_column(BigInteger, default=1, server_default="1")


class LegacyDataset(Base):
    """Transition only: the ERP tables not yet moved to relational tables, one JSON document each.

    Same role as the old SQLite "datasets" table; emptied area by area during R1 to R3 and dropped in R4.
    """
    __tablename__ = "legacy_datasets"

    name: Mapped[str] = mapped_column(String(100), primary_key=True)
    data: Mapped[list | dict] = mapped_column(JSONB)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
