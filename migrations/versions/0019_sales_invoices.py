"""Sales (V3): the sales invoices (drafts) with their lines and their taxes by tax code.

Revision ID: 0019
Revises: 0018
Create Date: 2026-11-23
"""
from alembic import op
import sqlalchemy as sa


revision = '0019'
down_revision = '0018'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('sales_invoices',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('company_id', sa.BigInteger(), nullable=False),
    sa.Column('customer', sa.Text(), server_default='', nullable=False),
    sa.Column('ship_to', sa.Text(), server_default='', nullable=False),
    sa.Column('date', sa.Date(), nullable=True),
    sa.Column('warehouse', sa.Text(), server_default='', nullable=False),
    sa.Column('customer_po', sa.Text(), server_default='', nullable=False),
    sa.Column('lang', sa.Text(), server_default='', nullable=False),
    sa.Column('term_code', sa.Text(), server_default='', nullable=False),
    sa.Column('term_desc', sa.Text(), server_default='', nullable=False),
    sa.Column('notes', sa.Text(), server_default='', nullable=False),
    sa.Column('no', sa.Integer(), server_default='0', nullable=False),
    sa.Column('status', sa.String(length=30), server_default='draft', nullable=False),
    sa.Column('invoice_no', sa.Text(), server_default='', nullable=False),
    sa.Column('customer_name', sa.Text(), server_default='', nullable=False),
    sa.Column('tax_group', sa.Text(), server_default='', nullable=False),
    sa.Column('sub_total', sa.Numeric(), nullable=True),
    sa.Column('discount_total', sa.Numeric(), nullable=True),
    sa.Column('tax_total', sa.Numeric(), nullable=True),
    sa.Column('total', sa.Numeric(), nullable=True),
    sa.Column('user', sa.Text(), server_default='', nullable=False),
    sa.Column('created', sa.DateTime(), nullable=True),
    sa.CheckConstraint("status IN ('draft', 'posted')", name='ck_sales_invoices_status'),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
    sa.PrimaryKeyConstraint('id'),
    comment='business key: no'
    )
    op.create_index(op.f('ix_sales_invoices_company_id'), 'sales_invoices', ['company_id'], unique=False)
    op.create_index('uq_sales_invoices_key', 'sales_invoices', [sa.text('company_id'), sa.text('no')], unique=True)
    op.create_table('sales_invoices_lines',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('parent_id', sa.BigInteger(), nullable=False),
    sa.Column('line_no', sa.Integer(), nullable=False),
    sa.Column('product', sa.Text(), server_default='', nullable=False),
    sa.Column('description', sa.Text(), server_default='', nullable=False),
    sa.Column('qty', sa.Numeric(), nullable=True),
    sa.Column('uom', sa.Text(), server_default='', nullable=False),
    sa.Column('price', sa.Numeric(), nullable=True),
    sa.Column('discount_pct', sa.Numeric(), nullable=True),
    sa.Column('net_price', sa.Numeric(), nullable=True),
    sa.Column('amount', sa.Numeric(), nullable=True),
    sa.Column('tax_group', sa.Text(), server_default='', nullable=False),
    sa.Column('price_source', sa.Text(), server_default='', nullable=False),
    sa.ForeignKeyConstraint(['parent_id'], ['sales_invoices.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sales_invoices_lines_parent_id'), 'sales_invoices_lines', ['parent_id'], unique=False)
    op.create_table('sales_invoices_taxes',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('parent_id', sa.BigInteger(), nullable=False),
    sa.Column('line_no', sa.Integer(), nullable=False),
    sa.Column('tax_group', sa.Text(), server_default='', nullable=False),
    sa.Column('tax_code', sa.Text(), server_default='', nullable=False),
    sa.Column('kind', sa.Text(), server_default='', nullable=False),
    sa.Column('rate', sa.Numeric(), nullable=True),
    sa.Column('base', sa.Numeric(), nullable=True),
    sa.Column('tax', sa.Numeric(), nullable=True),
    sa.ForeignKeyConstraint(['parent_id'], ['sales_invoices.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sales_invoices_taxes_parent_id'), 'sales_invoices_taxes', ['parent_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_sales_invoices_taxes_parent_id'), table_name='sales_invoices_taxes')
    op.drop_table('sales_invoices_taxes')
    op.drop_index(op.f('ix_sales_invoices_lines_parent_id'), table_name='sales_invoices_lines')
    op.drop_table('sales_invoices_lines')
    op.drop_index('uq_sales_invoices_key', table_name='sales_invoices')
    op.drop_index(op.f('ix_sales_invoices_company_id'), table_name='sales_invoices')
    op.drop_table('sales_invoices')
