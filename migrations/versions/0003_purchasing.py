"""Purchasing tables (R2): purchase orders, receptions, supplier invoices and their lines.

Revision ID: 0003
Revises: 0002
Create Date: 2026-11-19
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0003'
down_revision = '0002'
branch_labels = None
depends_on = None


def upgrade():

    op.create_table('ap_invoices',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('company_id', sa.BigInteger(), nullable=False),
    sa.Column('invoice_no', sa.Integer(), nullable=False),
    sa.Column('supplier_code', sa.Text(), nullable=True),
    sa.Column('supplier_name', sa.Text(), nullable=True),
    sa.Column('invoice_number', sa.Text(), nullable=True),
    sa.Column('invoice_date', sa.Date(), nullable=True),
    sa.Column('po_no', sa.Text(), nullable=True),
    sa.Column('currency', sa.Text(), nullable=True),
    sa.Column('status', sa.Text(), nullable=True),
    sa.Column('source', sa.Text(), nullable=True),
    sa.Column('freight', sa.Numeric(), nullable=True),
    sa.Column('gst', sa.Numeric(), nullable=True),
    sa.Column('pst', sa.Numeric(), nullable=True),
    sa.Column('sub_total', sa.Numeric(), nullable=True),
    sa.Column('total', sa.Numeric(), nullable=True),
    sa.Column('extra', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ap_invoices_company_id'), 'ap_invoices', ['company_id'], unique=False)
    op.create_index('ix_ap_invoices_supplier_number', 'ap_invoices', ['company_id', sa.text('lower(supplier_code)'), sa.text('lower(invoice_number)')], unique=False)
    op.create_index('uq_ap_invoices_no', 'ap_invoices', ['company_id', 'invoice_no'], unique=True)
    op.create_table('purchase_orders',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('company_id', sa.BigInteger(), nullable=False),
    sa.Column('po_no', sa.Text(), nullable=False),
    sa.Column('has_detail', sa.Boolean(), server_default='false', nullable=False),
    sa.Column('unbilled', sa.Boolean(), server_default='false', nullable=False),
    sa.Column('unbilled_order', sa.BigInteger(), nullable=True),
    sa.Column('pw_company', sa.Text(), nullable=True),
    sa.Column('supplier_code', sa.Text(), nullable=True),
    sa.Column('supplier_name', sa.Text(), nullable=True),
    sa.Column('buyer_code', sa.Text(), nullable=True),
    sa.Column('buyer_name', sa.Text(), nullable=True),
    sa.Column('applicant_code', sa.Text(), nullable=True),
    sa.Column('order_date', sa.Date(), nullable=True),
    sa.Column('due_date', sa.Date(), nullable=True),
    sa.Column('reference', sa.Text(), nullable=True),
    sa.Column('source', sa.Text(), nullable=True),
    sa.Column('sub_total', sa.Numeric(), nullable=True),
    sa.Column('freight', sa.Numeric(), nullable=True),
    sa.Column('gst', sa.Numeric(), nullable=True),
    sa.Column('pst', sa.Numeric(), nullable=True),
    sa.Column('total_amount', sa.Numeric(), nullable=True),
    sa.Column('unb_pw_company', sa.Text(), nullable=True),
    sa.Column('creation_date', sa.Date(), nullable=True),
    sa.Column('unb_supplier_code', sa.Text(), nullable=True),
    sa.Column('unb_supplier_name', sa.Text(), nullable=True),
    sa.Column('blanket_order', sa.Boolean(), nullable=True),
    sa.Column('extra', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_purchase_orders_company_id'), 'purchase_orders', ['company_id'], unique=False)
    op.create_index('uq_purchase_orders_key', 'purchase_orders', ['company_id', 'po_no'], unique=True)
    op.create_table('receptions',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('company_id', sa.BigInteger(), nullable=False),
    sa.Column('reception_no', sa.Text(), nullable=False),
    sa.Column('has_detail', sa.Boolean(), server_default='false', nullable=False),
    sa.Column('unbilled', sa.Boolean(), server_default='false', nullable=False),
    sa.Column('unbilled_order', sa.BigInteger(), nullable=True),
    sa.Column('pw_company', sa.Text(), nullable=True),
    sa.Column('reception_date', sa.Date(), nullable=True),
    sa.Column('supplier_name', sa.Text(), nullable=True),
    sa.Column('supplier_code', sa.Text(), nullable=True),
    sa.Column('po_no', sa.Text(), nullable=True),
    sa.Column('status', sa.Text(), nullable=True),
    sa.Column('warehouse', sa.Text(), nullable=True),
    sa.Column('total_amount', sa.Numeric(), nullable=True),
    sa.Column('received_by', sa.Text(), nullable=True),
    sa.Column('comments', sa.Text(), nullable=True),
    sa.Column('sub_total', sa.Numeric(), nullable=True),
    sa.Column('freight', sa.Numeric(), nullable=True),
    sa.Column('gst', sa.Numeric(), nullable=True),
    sa.Column('pst', sa.Numeric(), nullable=True),
    sa.Column('unb_pw_company', sa.Text(), nullable=True),
    sa.Column('unb_reception_date', sa.Date(), nullable=True),
    sa.Column('unb_po_no', sa.Text(), nullable=True),
    sa.Column('unb_supplier_name', sa.Text(), nullable=True),
    sa.Column('unb_supplier_code', sa.Text(), nullable=True),
    sa.Column('amount_received', sa.Numeric(), nullable=True),
    sa.Column('billing_status', sa.Text(), nullable=True),
    sa.Column('days_waiting', sa.Text(), nullable=True),
    sa.Column('billing_owner', sa.Text(), nullable=True),
    sa.Column('billing_priority', sa.Text(), nullable=True),
    sa.Column('currency', sa.Text(), nullable=True),
    sa.Column('unb_warehouse', sa.Text(), nullable=True),
    sa.Column('reception_type', sa.Text(), nullable=True),
    sa.Column('extra', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_receptions_company_id'), 'receptions', ['company_id'], unique=False)
    op.create_index('uq_receptions_key', 'receptions', ['company_id', 'reception_no'], unique=True)
    op.create_table('ap_invoice_lines',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('parent_id', sa.BigInteger(), nullable=False),
    sa.Column('line_no', sa.Integer(), nullable=False),
    sa.Column('product_code', sa.Text(), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('quantity', sa.Numeric(), nullable=True),
    sa.Column('unit_cost', sa.Numeric(), nullable=True),
    sa.Column('amount', sa.Numeric(), nullable=True),
    sa.Column('gl_account', sa.Text(), nullable=True),
    sa.Column('cc1', sa.Text(), nullable=True),
    sa.Column('cc2', sa.Text(), nullable=True),
    sa.Column('reception_no', sa.Text(), nullable=True),
    sa.Column('extra', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
    sa.ForeignKeyConstraint(['parent_id'], ['ap_invoices.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ap_invoice_lines_parent_id'), 'ap_invoice_lines', ['parent_id'], unique=False)
    op.create_table('purchase_order_lines',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('parent_id', sa.BigInteger(), nullable=False),
    sa.Column('line_no', sa.Integer(), nullable=False),
    sa.Column('line_ref', sa.Text(), nullable=True),
    sa.Column('product_code', sa.Text(), nullable=True),
    sa.Column('product_desc', sa.Text(), nullable=True),
    sa.Column('quantity', sa.Numeric(), nullable=True),
    sa.Column('unit_cost', sa.Numeric(), nullable=True),
    sa.Column('sub_total', sa.Numeric(), nullable=True),
    sa.Column('total_amount', sa.Numeric(), nullable=True),
    sa.Column('freight', sa.Numeric(), nullable=True),
    sa.Column('gst', sa.Numeric(), nullable=True),
    sa.Column('pst', sa.Numeric(), nullable=True),
    sa.Column('extra', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
    sa.ForeignKeyConstraint(['parent_id'], ['purchase_orders.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_purchase_order_lines_parent_id'), 'purchase_order_lines', ['parent_id'], unique=False)
    op.create_table('reception_lines',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('parent_id', sa.BigInteger(), nullable=False),
    sa.Column('line_no', sa.Integer(), nullable=False),
    sa.Column('item_code', sa.Text(), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('qty_ordered', sa.Numeric(), nullable=True),
    sa.Column('qty_received', sa.Numeric(), nullable=True),
    sa.Column('unit_price', sa.Numeric(), nullable=True),
    sa.Column('currency', sa.Text(), nullable=True),
    sa.Column('total_amount', sa.Numeric(), nullable=True),
    sa.Column('unit_cost', sa.Numeric(), nullable=True),
    sa.Column('sub_total', sa.Numeric(), nullable=True),
    sa.Column('freight', sa.Numeric(), nullable=True),
    sa.Column('gst', sa.Numeric(), nullable=True),
    sa.Column('pst', sa.Numeric(), nullable=True),
    sa.Column('gl_account', sa.Text(), nullable=True),
    sa.Column('cc1', sa.Text(), nullable=True),
    sa.Column('cc2', sa.Text(), nullable=True),
    sa.Column('extra', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
    sa.ForeignKeyConstraint(['parent_id'], ['receptions.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_reception_lines_parent_id'), 'reception_lines', ['parent_id'], unique=False)



def downgrade():

    op.drop_index(op.f('ix_reception_lines_parent_id'), table_name='reception_lines')
    op.drop_table('reception_lines')
    op.drop_index(op.f('ix_purchase_order_lines_parent_id'), table_name='purchase_order_lines')
    op.drop_table('purchase_order_lines')
    op.drop_index(op.f('ix_ap_invoice_lines_parent_id'), table_name='ap_invoice_lines')
    op.drop_table('ap_invoice_lines')
    op.drop_index('uq_receptions_key', table_name='receptions')
    op.drop_index(op.f('ix_receptions_company_id'), table_name='receptions')
    op.drop_table('receptions')
    op.drop_index('uq_purchase_orders_key', table_name='purchase_orders')
    op.drop_index(op.f('ix_purchase_orders_company_id'), table_name='purchase_orders')
    op.drop_table('purchase_orders')
    op.drop_index('uq_ap_invoices_no', table_name='ap_invoices')
    op.drop_index('ix_ap_invoices_supplier_number', table_name='ap_invoices')
    op.drop_index(op.f('ix_ap_invoices_company_id'), table_name='ap_invoices')
    op.drop_table('ap_invoices')

