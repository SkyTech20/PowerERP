"""Sales (V6): the credit notes: sales invoices of type "credit" crediting a posted invoice (cOrigInvoice); their
lines credit a line of it (iOrigLine) and can bring the goods back to the stock (lReturn).

Revision ID: 0021
Revises: 0020
Create Date: 2026-11-24
"""
from alembic import op
import sqlalchemy as sa


revision = '0021'
down_revision = '0020'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('sales_invoices', sa.Column('type', sa.String(length=30), server_default='invoice', nullable=False))
    op.add_column('sales_invoices', sa.Column('orig_invoice', sa.Text(), server_default='', nullable=False))
    op.add_column('sales_invoices_lines', sa.Column('orig_line', sa.Integer(), server_default='0', nullable=False))
    op.add_column('sales_invoices_lines', sa.Column('return', sa.Boolean(), server_default='false', nullable=False))


def downgrade():
    op.drop_column('sales_invoices_lines', 'return')
    op.drop_column('sales_invoices_lines', 'orig_line')
    op.drop_column('sales_invoices', 'orig_invoice')
    op.drop_column('sales_invoices', 'type')
