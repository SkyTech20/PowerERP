"""Core tables: companies, users, settings, document sequences, legacy datasets (transition).

Revision ID: 0001
Revises:
Create Date: 2026-11-19
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "companies",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("code", sa.String(20), nullable=False, unique=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.execute("INSERT INTO companies (code, name) VALUES ('MAIN', 'Main company')")

    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("username", sa.String(80), nullable=False),
        sa.Column("name", sa.String(200), nullable=False, server_default=""),
        sa.Column("email", sa.String(200), nullable=False, server_default=""),
        sa.Column("role", sa.String(20), nullable=False, server_default="user"),
        sa.Column("lang", sa.String(5), nullable=False, server_default="en"),
        sa.Column("active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("password_hash", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("last_login", sa.DateTime(timezone=True)),
        sa.CheckConstraint("role IN ('admin', 'user')", name="ck_users_role"),
        sa.CheckConstraint("lang IN ('en', 'fr')", name="ck_users_lang"),
    )
    op.create_index("uq_users_username_lower", "users", [sa.text("lower(username)")], unique=True)

    op.create_table(
        "settings",
        sa.Column("key", sa.String(100), primary_key=True),
        sa.Column("value", sa.Text, nullable=False),
    )

    op.create_table(
        "doc_sequences",
        sa.Column("company_id", sa.BigInteger, sa.ForeignKey("companies.id"), primary_key=True),
        sa.Column("doc_type", sa.String(20), primary_key=True),
        sa.Column("prefix", sa.String(20), nullable=False, server_default=""),
        sa.Column("next_value", sa.BigInteger, nullable=False, server_default="1"),
    )

    op.create_table(
        "legacy_datasets",
        sa.Column("name", sa.String(100), primary_key=True),
        sa.Column("data", postgresql.JSONB, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade():
    op.drop_table("legacy_datasets")
    op.drop_table("doc_sequences")
    op.drop_table("settings")
    op.drop_index("uq_users_username_lower", table_name="users")
    op.drop_table("users")
    op.drop_table("companies")
