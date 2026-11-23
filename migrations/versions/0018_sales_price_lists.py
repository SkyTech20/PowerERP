"""Sales (V2): price lists with their prices by product and quantity and their discounts by category; the price
list of each customer.

Revision ID: 0018
Revises: 0017
Create Date: 2026-11-23
"""
from alembic import op
import sqlalchemy as sa


revision = '0018'
down_revision = '0017'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('price_lists',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('company_id', sa.BigInteger(), nullable=False),
    sa.Column('code', sa.Text(), server_default='', nullable=False),
    sa.Column('desc_fr', sa.Text(), server_default='', nullable=False),
    sa.Column('desc_en', sa.Text(), server_default='', nullable=False),
    sa.Column('start_date', sa.Date(), nullable=True),
    sa.Column('end_date', sa.Date(), nullable=True),
    sa.Column('notes', sa.Text(), server_default='', nullable=False),
    sa.Column('active', sa.Boolean(), server_default='false', nullable=False),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
    sa.PrimaryKeyConstraint('id'),
    comment='business key: lower(code)'
    )
    op.create_index(op.f('ix_price_lists_company_id'), 'price_lists', ['company_id'], unique=False)
    op.create_index('uq_price_lists_key', 'price_lists', [sa.text('company_id'), sa.text('lower(code)')], unique=True)
    op.create_table('price_lists_discounts',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('parent_id', sa.BigInteger(), nullable=False),
    sa.Column('line_no', sa.Integer(), nullable=False),
    sa.Column('category', sa.Text(), server_default='', nullable=False),
    sa.Column('discount_pct', sa.Numeric(), nullable=True),
    sa.ForeignKeyConstraint(['parent_id'], ['price_lists.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_price_lists_discounts_parent_id'), 'price_lists_discounts', ['parent_id'], unique=False)
    op.create_table('price_lists_lines',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('parent_id', sa.BigInteger(), nullable=False),
    sa.Column('line_no', sa.Integer(), nullable=False),
    sa.Column('product', sa.Text(), server_default='', nullable=False),
    sa.Column('uom', sa.Text(), server_default='', nullable=False),
    sa.Column('min_qty', sa.Numeric(), nullable=True),
    sa.Column('price', sa.Numeric(), nullable=True),
    sa.Column('discount_pct', sa.Numeric(), nullable=True),
    sa.ForeignKeyConstraint(['parent_id'], ['price_lists.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_price_lists_lines_parent_id'), 'price_lists_lines', ['parent_id'], unique=False)
    op.add_column('customers', sa.Column('price_list', sa.Text(), server_default='', nullable=False))


def downgrade():
    op.drop_column('customers', 'price_list')
    op.drop_index(op.f('ix_price_lists_lines_parent_id'), table_name='price_lists_lines')
    op.drop_table('price_lists_lines')
    op.drop_index(op.f('ix_price_lists_discounts_parent_id'), table_name='price_lists_discounts')
    op.drop_table('price_lists_discounts')
    op.drop_index('uq_price_lists_key', table_name='price_lists')
    op.drop_index(op.f('ix_price_lists_company_id'), table_name='price_lists')
    op.drop_table('price_lists')
