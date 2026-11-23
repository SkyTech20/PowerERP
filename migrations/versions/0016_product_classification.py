"""Products: the type (stock / nonstock / service / kit / raw) becomes three fields: stock type (physical or not),
nature (product or service) and class (raw material, kit / assembly, finished product, consumable, fixed asset).

The values are not converted: the demo data is seeded again with the new fields.

Revision ID: 0016
Revises: 0015
Create Date: 2026-11-23
"""
from alembic import op
import sqlalchemy as sa


revision = '0016'
down_revision = '0015'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('products', sa.Column('stock_type', sa.String(length=30), server_default='physical', nullable=False))
    op.add_column('products', sa.Column('nature', sa.String(length=30), server_default='product', nullable=False))
    op.add_column('products', sa.Column('item_class', sa.String(length=30), server_default='', nullable=False))
    op.create_check_constraint('ck_products_stock_type', 'products', "stock_type IN ('physical', 'nonphysical')")
    op.create_check_constraint('ck_products_nature', 'products', "nature IN ('product', 'service')")
    op.create_check_constraint(
        'ck_products_item_class', 'products', "item_class IN ('', 'raw', 'kit', 'finished', 'consumable', 'asset')"
    )
    op.drop_constraint('ck_products_type', 'products', type_='check')
    op.drop_column('products', 'type')


def downgrade():
    op.add_column('products', sa.Column('type', sa.String(length=30), server_default='stock', nullable=False))
    op.create_check_constraint('ck_products_type', 'products', "type IN ('stock', 'nonstock', 'service', 'kit', 'raw')")
    op.drop_constraint('ck_products_item_class', 'products', type_='check')
    op.drop_constraint('ck_products_nature', 'products', type_='check')
    op.drop_constraint('ck_products_stock_type', 'products', type_='check')
    op.drop_column('products', 'item_class')
    op.drop_column('products', 'nature')
    op.drop_column('products', 'stock_type')
