"""Production (M0): the reference lists of the shop floor: capabilities, setup families, stop and scrap reasons.

Revision ID: 0005
Revises: 0004
Create Date: 2026-11-20
"""
from alembic import op
import sqlalchemy as sa


revision = '0005'
down_revision = '0004'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('capabilities',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('company_id', sa.BigInteger(), nullable=False),
    sa.Column('code', sa.Text(), server_default='', nullable=False),
    sa.Column('desc_fr', sa.Text(), server_default='', nullable=False),
    sa.Column('desc_en', sa.Text(), server_default='', nullable=False),
    sa.Column('active', sa.Boolean(), server_default='false', nullable=False),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
    sa.PrimaryKeyConstraint('id'),
    comment='business key: lower(code)'
    )
    op.create_index(op.f('ix_capabilities_company_id'), 'capabilities', ['company_id'], unique=False)
    op.create_index('uq_capabilities_key', 'capabilities', [sa.text('company_id'), sa.text('lower(code)')], unique=True)
    op.create_table('downtime_reasons',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('company_id', sa.BigInteger(), nullable=False),
    sa.Column('code', sa.Text(), server_default='', nullable=False),
    sa.Column('desc_fr', sa.Text(), server_default='', nullable=False),
    sa.Column('desc_en', sa.Text(), server_default='', nullable=False),
    sa.Column('reason_group', sa.String(length=30), server_default='breakdown', nullable=False),
    sa.Column('affects_oee', sa.Boolean(), server_default='false', nullable=False),
    sa.Column('active', sa.Boolean(), server_default='false', nullable=False),
    sa.CheckConstraint("reason_group IN ('breakdown', 'setup', 'minor_stop', 'reduced_speed', 'no_material', 'no_operator', 'quality', 'planned', 'other')", name='ck_downtime_reasons_reason_group'),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
    sa.PrimaryKeyConstraint('id'),
    comment='business key: lower(code)'
    )
    op.create_index(op.f('ix_downtime_reasons_company_id'), 'downtime_reasons', ['company_id'], unique=False)
    op.create_index('uq_downtime_reasons_key', 'downtime_reasons', [sa.text('company_id'), sa.text('lower(code)')], unique=True)
    op.create_table('scrap_reasons',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('company_id', sa.BigInteger(), nullable=False),
    sa.Column('code', sa.Text(), server_default='', nullable=False),
    sa.Column('desc_fr', sa.Text(), server_default='', nullable=False),
    sa.Column('desc_en', sa.Text(), server_default='', nullable=False),
    sa.Column('reason_group', sa.String(length=30), server_default='material', nullable=False),
    sa.Column('active', sa.Boolean(), server_default='false', nullable=False),
    sa.CheckConstraint("reason_group IN ('material', 'process', 'machine', 'operator', 'startup', 'other')", name='ck_scrap_reasons_reason_group'),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
    sa.PrimaryKeyConstraint('id'),
    comment='business key: lower(code)'
    )
    op.create_index(op.f('ix_scrap_reasons_company_id'), 'scrap_reasons', ['company_id'], unique=False)
    op.create_index('uq_scrap_reasons_key', 'scrap_reasons', [sa.text('company_id'), sa.text('lower(code)')], unique=True)
    op.create_table('setup_families',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('company_id', sa.BigInteger(), nullable=False),
    sa.Column('code', sa.Text(), server_default='', nullable=False),
    sa.Column('desc_fr', sa.Text(), server_default='', nullable=False),
    sa.Column('desc_en', sa.Text(), server_default='', nullable=False),
    sa.Column('active', sa.Boolean(), server_default='false', nullable=False),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
    sa.PrimaryKeyConstraint('id'),
    comment='business key: lower(code)'
    )
    op.create_index(op.f('ix_setup_families_company_id'), 'setup_families', ['company_id'], unique=False)
    op.create_index('uq_setup_families_key', 'setup_families', [sa.text('company_id'), sa.text('lower(code)')], unique=True)


def downgrade():
    op.drop_index('uq_setup_families_key', table_name='setup_families')
    op.drop_index(op.f('ix_setup_families_company_id'), table_name='setup_families')
    op.drop_table('setup_families')
    op.drop_index('uq_scrap_reasons_key', table_name='scrap_reasons')
    op.drop_index(op.f('ix_scrap_reasons_company_id'), table_name='scrap_reasons')
    op.drop_table('scrap_reasons')
    op.drop_index('uq_downtime_reasons_key', table_name='downtime_reasons')
    op.drop_index(op.f('ix_downtime_reasons_company_id'), table_name='downtime_reasons')
    op.drop_table('downtime_reasons')
    op.drop_index('uq_capabilities_key', table_name='capabilities')
    op.drop_index(op.f('ix_capabilities_company_id'), table_name='capabilities')
    op.drop_table('capabilities')
