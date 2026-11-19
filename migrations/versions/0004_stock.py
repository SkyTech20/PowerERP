"""Stock tables (R3): replenishment parameters, movement ledger, balances, physical counts.

Revision ID: 0004
Revises: 0003
Create Date: 2026-11-19
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0004'
down_revision = '0003'
branch_labels = None
depends_on = None


def upgrade():

    op.create_table('stock_balances',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('company_id', sa.BigInteger(), nullable=False),
    sa.Column('product', sa.Text(), nullable=False),
    sa.Column('warehouse', sa.Text(), nullable=False),
    sa.Column('location', sa.Text(), server_default='', nullable=False),
    sa.Column('lot', sa.Text(), server_default='', nullable=False),
    sa.Column('serial', sa.Text(), server_default='', nullable=False),
    sa.Column('qty', sa.Numeric(), server_default='0', nullable=False),
    sa.Column('reserved', sa.Numeric(), server_default='0', nullable=False),
    sa.Column('expiry', sa.Date(), nullable=True),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('uq_stock_balances_key', 'stock_balances', ['company_id', sa.text('lower(product)'), sa.text('lower(warehouse)'), sa.text('lower(location)'), sa.text('lower(lot)'), sa.text('lower(serial)')], unique=True)
    op.create_table('stock_counts',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('company_id', sa.BigInteger(), nullable=False),
    sa.Column('warehouse', sa.Text(), server_default='', nullable=False),
    sa.Column('date', sa.Date(), nullable=True),
    sa.Column('description', sa.Text(), server_default='', nullable=False),
    sa.Column('location_prefix', sa.Text(), server_default='', nullable=False),
    sa.Column('product_prefix', sa.Text(), server_default='', nullable=False),
    sa.Column('no', sa.Integer(), server_default='0', nullable=False),
    sa.Column('status', sa.String(length=30), server_default='Draft', nullable=False),
    sa.Column('user', sa.Text(), server_default='', nullable=False),
    sa.Column('posted', sa.DateTime(), nullable=True),
    sa.Column('value_diff', sa.Numeric(), nullable=True),
    sa.Column('movements', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.CheckConstraint("status IN ('Draft', 'Posted')", name='ck_stock_counts_status'),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
    sa.PrimaryKeyConstraint('id'),
    comment='business key: no'
    )
    op.create_index(op.f('ix_stock_counts_company_id'), 'stock_counts', ['company_id'], unique=False)
    op.create_index('uq_stock_counts_key', 'stock_counts', [sa.text('company_id'), sa.text('no')], unique=True)
    op.create_table('stock_movements',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('company_id', sa.BigInteger(), nullable=False),
    sa.Column('date', sa.Date(), nullable=True),
    sa.Column('type', sa.String(length=30), server_default='IN', nullable=False),
    sa.Column('product', sa.Text(), server_default='', nullable=False),
    sa.Column('qty', sa.Numeric(), nullable=True),
    sa.Column('unit_cost', sa.Numeric(), nullable=True),
    sa.Column('warehouse', sa.Text(), server_default='', nullable=False),
    sa.Column('location', sa.Text(), server_default='', nullable=False),
    sa.Column('wh_to', sa.Text(), server_default='', nullable=False),
    sa.Column('loc_to', sa.Text(), server_default='', nullable=False),
    sa.Column('lot', sa.Text(), server_default='', nullable=False),
    sa.Column('serial', sa.Text(), server_default='', nullable=False),
    sa.Column('expiry', sa.Date(), nullable=True),
    sa.Column('doc_type', sa.String(length=30), server_default='MAN', nullable=False),
    sa.Column('doc_no', sa.Text(), server_default='', nullable=False),
    sa.Column('reason', sa.Text(), server_default='', nullable=False),
    sa.Column('comment', sa.Text(), server_default='', nullable=False),
    sa.Column('no', sa.Integer(), server_default='0', nullable=False),
    sa.Column('value', sa.Numeric(), nullable=True),
    sa.Column('avg_cost_after', sa.Numeric(), nullable=True),
    sa.Column('user', sa.Text(), server_default='', nullable=False),
    sa.Column('created', sa.DateTime(), nullable=True),
    sa.CheckConstraint("doc_type IN ('MAN', 'PO', 'REC', 'INV', 'SO', 'CNT', 'PROD')", name='ck_stock_movements_doc_type'),
    sa.CheckConstraint("type IN ('IN', 'OUT', 'TRF', 'ADJ', 'CNT', 'RSV')", name='ck_stock_movements_type'),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
    sa.PrimaryKeyConstraint('id'),
    comment='business key: no'
    )
    op.create_index(op.f('ix_stock_movements_company_id'), 'stock_movements', ['company_id'], unique=False)
    op.create_index('uq_stock_movements_key', 'stock_movements', [sa.text('company_id'), sa.text('no')], unique=True)
    op.create_table('stock_params',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('company_id', sa.BigInteger(), nullable=False),
    sa.Column('product', sa.Text(), server_default='', nullable=False),
    sa.Column('warehouse', sa.Text(), server_default='', nullable=False),
    sa.Column('reorder_point', sa.Numeric(), nullable=True),
    sa.Column('min_qty', sa.Numeric(), nullable=True),
    sa.Column('max_qty', sa.Numeric(), nullable=True),
    sa.Column('order_qty', sa.Numeric(), nullable=True),
    sa.Column('default_location', sa.Text(), server_default='', nullable=False),
    sa.Column('lead_time_days', sa.Integer(), server_default='0', nullable=False),
    sa.Column('active', sa.Boolean(), server_default='false', nullable=False),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
    sa.PrimaryKeyConstraint('id'),
    comment='business key: lower(product), lower(warehouse)'
    )
    op.create_index(op.f('ix_stock_params_company_id'), 'stock_params', ['company_id'], unique=False)
    op.create_index('uq_stock_params_key', 'stock_params', [sa.text('company_id'), sa.text('lower(product)'), sa.text('lower(warehouse)')], unique=True)
    op.create_table('stock_counts_lines',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('parent_id', sa.BigInteger(), nullable=False),
    sa.Column('line_no', sa.Integer(), nullable=False),
    sa.Column('product', sa.Text(), server_default='', nullable=False),
    sa.Column('location', sa.Text(), server_default='', nullable=False),
    sa.Column('lot', sa.Text(), server_default='', nullable=False),
    sa.Column('serial', sa.Text(), server_default='', nullable=False),
    sa.Column('qty_expected', sa.Numeric(), nullable=True),
    sa.Column('qty_counted', sa.Numeric(), nullable=True),
    sa.Column('desc_fr', sa.Text(), server_default='', nullable=False),
    sa.Column('diff', sa.Numeric(), nullable=True),
    sa.ForeignKeyConstraint(['parent_id'], ['stock_counts.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_stock_counts_lines_parent_id'), 'stock_counts_lines', ['parent_id'], unique=False)



def downgrade():

    op.drop_index(op.f('ix_stock_counts_lines_parent_id'), table_name='stock_counts_lines')
    op.drop_table('stock_counts_lines')
    op.drop_index('uq_stock_params_key', table_name='stock_params')
    op.drop_index(op.f('ix_stock_params_company_id'), table_name='stock_params')
    op.drop_table('stock_params')
    op.drop_index('uq_stock_movements_key', table_name='stock_movements')
    op.drop_index(op.f('ix_stock_movements_company_id'), table_name='stock_movements')
    op.drop_table('stock_movements')
    op.drop_index('uq_stock_counts_key', table_name='stock_counts')
    op.drop_index(op.f('ix_stock_counts_company_id'), table_name='stock_counts')
    op.drop_table('stock_counts')
    op.drop_index('uq_stock_balances_key', table_name='stock_balances')
    op.drop_table('stock_balances')

