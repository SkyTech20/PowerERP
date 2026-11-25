"""Core tables: companies, users, settings, document numbering and the transition table."""

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base

ADMIN_ROLE = "ADMIN"  # built-in: every permission, cannot be changed
USER_ROLE = "USER"  # built-in at the migration: what a plain user could do before roles existed
LANGS = ("en", "fr")


class Company(Base):
    """A company (legal entity / plant). Master data and documents get a company_id as they move here."""

    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(20), unique=True)
    name: Mapped[str] = mapped_column(String(200))
    active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Role(Base):
    """A role (profile): what its users may open and do. A user has one role."""

    __tablename__ = "roles"

    code: Mapped[str] = mapped_column(String(30), primary_key=True)
    desc_fr: Mapped[str] = mapped_column(Text, default="", server_default="")
    desc_en: Mapped[str] = mapped_column(Text, default="", server_default="")
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class RolePermission(Base):
    """One permission of a role: "<screen>:<action>" (powererp/core/permissions.py)."""

    __tablename__ = "role_permissions"

    role_code: Mapped[str] = mapped_column(
        String(30), ForeignKey("roles.code", onupdate="CASCADE", ondelete="CASCADE"), primary_key=True
    )
    permission: Mapped[str] = mapped_column(String(80), primary_key=True)


class RoleHistory(Base):
    """Who changed a role and when (kept after the role is deleted)."""

    __tablename__ = "role_history"
    __table_args__ = (Index("ix_role_history_role", "role_code", "at"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    role_code: Mapped[str] = mapped_column(String(30))
    username: Mapped[str] = mapped_column(String(80), default="", server_default="")
    change: Mapped[str] = mapped_column(String(20))  # created, updated, permissions, deleted
    details: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}")


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        Index("uq_users_username_lower", text("lower(username)"), unique=True),
        CheckConstraint("lang IN ('en', 'fr')", name="ck_users_lang"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(80))
    name: Mapped[str] = mapped_column(String(200), default="", server_default="")
    email: Mapped[str] = mapped_column(String(200), default="", server_default="")
    role: Mapped[str] = mapped_column(
        String(30), ForeignKey("roles.code", onupdate="CASCADE"), default=USER_ROLE, server_default=USER_ROLE
    )
    lang: Mapped[str] = mapped_column(String(5), default="en", server_default="en")
    active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    password_hash: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # lockout: failed logins in a row, and the account refused until locked_until (Administration > Users unlocks)
    failed_logins: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AuditEvent(Base):
    """The audit trail: security events (logins, lockouts, passwords, refusals) and every change made through the
    API (who, when, which screen, which record, what was sent). Written in its own transaction; never changed."""

    __tablename__ = "audit_log"
    __table_args__ = (Index("ix_audit_log_at", "at"), Index("ix_audit_log_user_at", "username", "at"))

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    username: Mapped[str] = mapped_column(String(80), default="", server_default="")
    kind: Mapped[str] = mapped_column(String(10))  # security, change
    event: Mapped[str] = mapped_column(String(40))  # login_ok, login_failed, locked, ... / create, edit, post, ...
    screen: Mapped[str] = mapped_column(String(60), default="", server_default="")
    method: Mapped[str] = mapped_column(String(10), default="", server_default="")
    path: Mapped[str] = mapped_column(Text, default="", server_default="")
    record: Mapped[str] = mapped_column(Text, default="", server_default="")
    status: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    ip: Mapped[str] = mapped_column(String(64), default="", server_default="")
    details: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}")


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
