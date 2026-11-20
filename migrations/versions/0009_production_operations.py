"""Production (P5): standard operations.

Revision ID: 0009
Revises: 0008
Create Date: 2026-11-20
"""
from alembic import op
import sqlalchemy as sa


revision = '0009'
down_revision = '0008'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('operations',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('company_id', sa.BigInteger(), nullable=False),
    sa.Column('code', sa.Text(), server_default='', nullable=False),
    sa.Column('desc_fr', sa.Text(), server_default='', nullable=False),
    sa.Column('desc_en', sa.Text(), server_default='', nullable=False),
    sa.Column('work_center', sa.Text(), server_default='', nullable=False),
    sa.Column('capability', sa.Text(), server_default='', nullable=False),
    sa.Column('run_format', sa.String(length=30), server_default='min_per_unit', nullable=False),
    sa.Column('setup_min', sa.Numeric(), nullable=True),
    sa.Column('run_value', sa.Numeric(), nullable=True),
    sa.Column('crew', sa.Integer(), server_default='0', nullable=False),
    sa.Column('reporting_point', sa.Boolean(), server_default='false', nullable=False),
    sa.Column('subcontract', sa.Boolean(), server_default='false', nullable=False),
    sa.Column('supplier', sa.Text(), server_default='', nullable=False),
    sa.Column('subcontract_cost', sa.Numeric(), nullable=True),
    sa.Column('subcontract_days', sa.Integer(), server_default='0', nullable=False),
    sa.Column('instruction_fr', sa.Text(), server_default='', nullable=False),
    sa.Column('instruction_en', sa.Text(), server_default='', nullable=False),
    sa.Column('active', sa.Boolean(), server_default='false', nullable=False),
    sa.CheckConstraint("run_format IN ('min_per_unit', 'units_per_hour', 'min_per_lot')", name='ck_operations_run_format'),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
    sa.PrimaryKeyConstraint('id'),
    comment='business key: lower(code)'
    )
    op.create_index(op.f('ix_operations_company_id'), 'operations', ['company_id'], unique=False)
    op.create_index('uq_operations_key', 'operations', [sa.text('company_id'), sa.text('lower(code)')], unique=True)


def downgrade():
    op.drop_index('uq_operations_key', table_name='operations')
    op.drop_index(op.f('ix_operations_company_id'), table_name='operations')
    op.drop_table('operations')
