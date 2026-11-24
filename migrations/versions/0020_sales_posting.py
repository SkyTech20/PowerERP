"""Sales (V4): posting the invoices: the stock taken per line (allocations), the posting fields, the first
invoice number (company profile) and the pick policy of the products (FEFO / FIFO / LIFO).

Revision ID: 0020
Revises: 0019
Create Date: 2026-11-24
"""
from alembic import op
import sqlalchemy as sa


revision = '0020'
down_revision = '0019'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('sales_invoices_allocations',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('parent_id', sa.BigInteger(), nullable=False),
    sa.Column('line_no', sa.Integer(), nullable=False),
    sa.Column('line', sa.Integer(), server_default='0', nullable=False),
    sa.Column('product', sa.Text(), server_default='', nullable=False),
    sa.Column('warehouse', sa.Text(), server_default='', nullable=False),
    sa.Column('location', sa.Text(), server_default='', nullable=False),
    sa.Column('lot', sa.Text(), server_default='', nullable=False),
    sa.Column('serial', sa.Text(), server_default='', nullable=False),
    sa.Column('expiry', sa.Date(), nullable=True),
    sa.Column('qty', sa.Numeric(), nullable=True),
    sa.Column('uom', sa.Text(), server_default='', nullable=False),
    sa.Column('movement', sa.Integer(), server_default='0', nullable=False),
    sa.Column('value', sa.Numeric(), nullable=True),
    sa.ForeignKeyConstraint(['parent_id'], ['sales_invoices.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sales_invoices_allocations_parent_id'), 'sales_invoices_allocations', ['parent_id'], unique=False)
    op.add_column('company_profile', sa.Column('invoice_start', sa.Integer(), server_default='0', nullable=False))
    op.add_column('products', sa.Column('pick_policy', sa.String(length=30), server_default='', nullable=False))
    op.add_column('sales_invoices', sa.Column('posted', sa.DateTime(), nullable=True))
    op.add_column('sales_invoices', sa.Column('posted_by', sa.Text(), server_default='', nullable=False))
    op.add_column('sales_invoices', sa.Column('cost', sa.Numeric(), nullable=True))


def downgrade():
    op.drop_column('sales_invoices', 'cost')
    op.drop_column('sales_invoices', 'posted_by')
    op.drop_column('sales_invoices', 'posted')
    op.drop_column('products', 'pick_policy')
    op.drop_column('company_profile', 'invoice_start')
    op.drop_index(op.f('ix_sales_invoices_allocations_parent_id'), table_name='sales_invoices_allocations')
    op.drop_table('sales_invoices_allocations')
