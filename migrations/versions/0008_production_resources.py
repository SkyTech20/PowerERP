"""Production (P4): resources with their capabilities, attributes, subresources and planned downtime.

Revision ID: 0008
Revises: 0007
Create Date: 2026-11-20
"""
from alembic import op
import sqlalchemy as sa


revision = '0008'
down_revision = '0007'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('resources',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('company_id', sa.BigInteger(), nullable=False),
    sa.Column('code', sa.Text(), server_default='', nullable=False),
    sa.Column('desc_fr', sa.Text(), server_default='', nullable=False),
    sa.Column('desc_en', sa.Text(), server_default='', nullable=False),
    sa.Column('work_center', sa.Text(), server_default='', nullable=False),
    sa.Column('calendar', sa.Text(), server_default='', nullable=False),
    sa.Column('speed_factor', sa.Numeric(), nullable=True),
    sa.Column('parallel', sa.Integer(), server_default='0', nullable=False),
    sa.Column('manufacturer', sa.Text(), server_default='', nullable=False),
    sa.Column('model', sa.Text(), server_default='', nullable=False),
    sa.Column('serial_no', sa.Text(), server_default='', nullable=False),
    sa.Column('notes', sa.Text(), server_default='', nullable=False),
    sa.Column('active', sa.Boolean(), server_default='false', nullable=False),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
    sa.PrimaryKeyConstraint('id'),
    comment='business key: lower(code)'
    )
    op.create_index(op.f('ix_resources_company_id'), 'resources', ['company_id'], unique=False)
    op.create_index('uq_resources_key', 'resources', [sa.text('company_id'), sa.text('lower(code)')], unique=True)
    op.create_table('resources_attributes',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('parent_id', sa.BigInteger(), nullable=False),
    sa.Column('line_no', sa.Integer(), nullable=False),
    sa.Column('attribute', sa.Text(), server_default='', nullable=False),
    sa.Column('uom', sa.Text(), server_default='', nullable=False),
    sa.Column('min', sa.Numeric(), nullable=True),
    sa.Column('max', sa.Numeric(), nullable=True),
    sa.Column('value', sa.Text(), server_default='', nullable=False),
    sa.ForeignKeyConstraint(['parent_id'], ['resources.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_resources_attributes_parent_id'), 'resources_attributes', ['parent_id'], unique=False)
    op.create_table('resources_capabilities',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('parent_id', sa.BigInteger(), nullable=False),
    sa.Column('line_no', sa.Integer(), nullable=False),
    sa.Column('capability', sa.Text(), server_default='', nullable=False),
    sa.Column('preference', sa.Integer(), server_default='0', nullable=False),
    sa.ForeignKeyConstraint(['parent_id'], ['resources.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_resources_capabilities_parent_id'), 'resources_capabilities', ['parent_id'], unique=False)
    op.create_table('resources_downtime',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('parent_id', sa.BigInteger(), nullable=False),
    sa.Column('line_no', sa.Integer(), nullable=False),
    sa.Column('start', sa.Date(), nullable=True),
    sa.Column('start_time', sa.Text(), server_default='', nullable=False),
    sa.Column('end', sa.Date(), nullable=True),
    sa.Column('end_time', sa.Text(), server_default='', nullable=False),
    sa.Column('reason', sa.Text(), server_default='', nullable=False),
    sa.Column('notes', sa.Text(), server_default='', nullable=False),
    sa.ForeignKeyConstraint(['parent_id'], ['resources.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_resources_downtime_parent_id'), 'resources_downtime', ['parent_id'], unique=False)
    op.create_table('resources_subresources',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('parent_id', sa.BigInteger(), nullable=False),
    sa.Column('line_no', sa.Integer(), nullable=False),
    sa.Column('code', sa.Text(), server_default='', nullable=False),
    sa.Column('desc_fr', sa.Text(), server_default='', nullable=False),
    sa.Column('desc_en', sa.Text(), server_default='', nullable=False),
    sa.ForeignKeyConstraint(['parent_id'], ['resources.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_resources_subresources_parent_id'), 'resources_subresources', ['parent_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_resources_subresources_parent_id'), table_name='resources_subresources')
    op.drop_table('resources_subresources')
    op.drop_index(op.f('ix_resources_downtime_parent_id'), table_name='resources_downtime')
    op.drop_table('resources_downtime')
    op.drop_index(op.f('ix_resources_capabilities_parent_id'), table_name='resources_capabilities')
    op.drop_table('resources_capabilities')
    op.drop_index(op.f('ix_resources_attributes_parent_id'), table_name='resources_attributes')
    op.drop_table('resources_attributes')
    op.drop_index('uq_resources_key', table_name='resources')
    op.drop_index(op.f('ix_resources_company_id'), table_name='resources')
    op.drop_table('resources')
