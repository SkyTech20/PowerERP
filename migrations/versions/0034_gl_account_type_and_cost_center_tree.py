"""GL accounts: type, English description, requires a cost center, active; cost centers: English description, active

The type of the existing accounts is guessed from the first digit of their code (1 asset, 2 liability,
3 equity, 4 revenue, the others expense); every existing account and cost center stays active.

Revision ID: 0034
Revises: 0033
Create Date: 2026-11-28 07:00:00
"""
from alembic import op
import sqlalchemy as sa


revision = '0034'
down_revision = '0033'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('gl_accounts', sa.Column('desc_en', sa.Text(), server_default='', nullable=False))
    op.add_column('gl_accounts', sa.Column('type', sa.String(length=30), server_default='asset', nullable=False))
    op.add_column('gl_accounts', sa.Column('requires_cc', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('gl_accounts', sa.Column('active', sa.Boolean(), server_default='false', nullable=False))
    op.create_check_constraint(
        'ck_gl_accounts_type', 'gl_accounts', "type IN ('asset', 'liability', 'equity', 'revenue', 'expense')"
    )
    op.add_column('cost_centers', sa.Column('desc_en', sa.Text(), server_default='', nullable=False))
    op.add_column('cost_centers', sa.Column('active', sa.Boolean(), server_default='false', nullable=False))
    op.get_bind().execute(
        sa.text(
            "UPDATE gl_accounts SET active = true, type = CASE left(code, 1) WHEN '1' THEN 'asset' "
            "WHEN '2' THEN 'liability' WHEN '3' THEN 'equity' WHEN '4' THEN 'revenue' ELSE 'expense' END"
        )
    )
    op.get_bind().execute(sa.text("UPDATE cost_centers SET active = true"))


def downgrade():
    op.drop_column('cost_centers', 'active')
    op.drop_column('cost_centers', 'desc_en')
    op.drop_constraint('ck_gl_accounts_type', 'gl_accounts', type_='check')
    op.drop_column('gl_accounts', 'active')
    op.drop_column('gl_accounts', 'requires_cc')
    op.drop_column('gl_accounts', 'type')
    op.drop_column('gl_accounts', 'desc_en')
