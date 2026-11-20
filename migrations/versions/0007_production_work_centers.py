"""Production (P3): work centers.

Revision ID: 0007
Revises: 0006
Create Date: 2026-11-20
"""
from alembic import op
import sqlalchemy as sa


revision = '0007'
down_revision = '0006'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('work_centers',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('company_id', sa.BigInteger(), nullable=False),
    sa.Column('code', sa.Text(), server_default='', nullable=False),
    sa.Column('desc_fr', sa.Text(), server_default='', nullable=False),
    sa.Column('desc_en', sa.Text(), server_default='', nullable=False),
    sa.Column('type', sa.String(length=30), server_default='machine', nullable=False),
    sa.Column('calendar', sa.Text(), server_default='', nullable=False),
    sa.Column('finite', sa.Boolean(), server_default='false', nullable=False),
    sa.Column('efficiency_pct', sa.Numeric(), nullable=True),
    sa.Column('utilization_pct', sa.Numeric(), nullable=True),
    sa.Column('setup_rate_hr', sa.Numeric(), nullable=True),
    sa.Column('run_rate_hr', sa.Numeric(), nullable=True),
    sa.Column('burden_rate_hr', sa.Numeric(), nullable=True),
    sa.Column('cost_center', sa.Text(), server_default='', nullable=False),
    sa.Column('warehouse', sa.Text(), server_default='', nullable=False),
    sa.Column('in_location', sa.Text(), server_default='', nullable=False),
    sa.Column('out_location', sa.Text(), server_default='', nullable=False),
    sa.Column('queue_min', sa.Integer(), server_default='0', nullable=False),
    sa.Column('move_min', sa.Integer(), server_default='0', nullable=False),
    sa.Column('supplier', sa.Text(), server_default='', nullable=False),
    sa.Column('notes', sa.Text(), server_default='', nullable=False),
    sa.Column('active', sa.Boolean(), server_default='false', nullable=False),
    sa.CheckConstraint("type IN ('machine', 'line', 'labor', 'subcontract')", name='ck_work_centers_type'),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
    sa.PrimaryKeyConstraint('id'),
    comment='business key: lower(code)'
    )
    op.create_index(op.f('ix_work_centers_company_id'), 'work_centers', ['company_id'], unique=False)
    op.create_index('uq_work_centers_key', 'work_centers', [sa.text('company_id'), sa.text('lower(code)')], unique=True)


def downgrade():
    op.drop_index('uq_work_centers_key', table_name='work_centers')
    op.drop_index(op.f('ix_work_centers_company_id'), table_name='work_centers')
    op.drop_table('work_centers')
