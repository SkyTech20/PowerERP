"""Units: general conversions between units (1 KG = 1000 G) and the units of each product (1 BAG = 25 KG).

Revision ID: 0015
Revises: 0014
Create Date: 2026-11-23
"""
from alembic import op
import sqlalchemy as sa


revision = '0015'
down_revision = '0014'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('uom_conversions',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('company_id', sa.BigInteger(), nullable=False),
    sa.Column('from_uom', sa.Text(), server_default='', nullable=False),
    sa.Column('to_uom', sa.Text(), server_default='', nullable=False),
    sa.Column('factor', sa.Numeric(), nullable=True),
    sa.Column('notes', sa.Text(), server_default='', nullable=False),
    sa.Column('active', sa.Boolean(), server_default='false', nullable=False),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
    sa.PrimaryKeyConstraint('id'),
    comment='business key: lower(from_uom), lower(to_uom)'
    )
    op.create_index(op.f('ix_uom_conversions_company_id'), 'uom_conversions', ['company_id'], unique=False)
    op.create_index('uq_uom_conversions_key', 'uom_conversions', [sa.text('company_id'), sa.text('lower(from_uom)'), sa.text('lower(to_uom)')], unique=True)
    op.create_table('products_conversions',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('parent_id', sa.BigInteger(), nullable=False),
    sa.Column('line_no', sa.Integer(), nullable=False),
    sa.Column('uom', sa.Text(), server_default='', nullable=False),
    sa.Column('factor', sa.Numeric(), nullable=True),
    sa.Column('notes', sa.Text(), server_default='', nullable=False),
    sa.ForeignKeyConstraint(['parent_id'], ['products.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_products_conversions_parent_id'), 'products_conversions', ['parent_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_products_conversions_parent_id'), table_name='products_conversions')
    op.drop_table('products_conversions')
    op.drop_index('uq_uom_conversions_key', table_name='uom_conversions')
    op.drop_index(op.f('ix_uom_conversions_company_id'), table_name='uom_conversions')
    op.drop_table('uom_conversions')
