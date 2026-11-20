"""Production (P7): manufacturing data of the products, with their attributes.

Revision ID: 0011
Revises: 0010
Create Date: 2026-11-20
"""
from alembic import op
import sqlalchemy as sa


revision = '0011'
down_revision = '0010'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('product_mfg',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('company_id', sa.BigInteger(), nullable=False),
    sa.Column('product', sa.Text(), server_default='', nullable=False),
    sa.Column('make_buy', sa.String(length=30), server_default='make', nullable=False),
    sa.Column('setup_family', sa.Text(), server_default='', nullable=False),
    sa.Column('mfg_lot_min', sa.Numeric(), nullable=True),
    sa.Column('mfg_lot_multiple', sa.Numeric(), nullable=True),
    sa.Column('mfg_lead_days', sa.Integer(), server_default='0', nullable=False),
    sa.Column('phantom', sa.Boolean(), server_default='false', nullable=False),
    sa.Column('trace_level', sa.String(length=30), server_default='none', nullable=False),
    sa.Column('notes', sa.Text(), server_default='', nullable=False),
    sa.CheckConstraint("make_buy IN ('make', 'buy', 'both')", name='ck_product_mfg_make_buy'),
    sa.CheckConstraint("trace_level IN ('none', 'lot', 'serial')", name='ck_product_mfg_trace_level'),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
    sa.PrimaryKeyConstraint('id'),
    comment='business key: lower(product)'
    )
    op.create_index(op.f('ix_product_mfg_company_id'), 'product_mfg', ['company_id'], unique=False)
    op.create_index('uq_product_mfg_key', 'product_mfg', [sa.text('company_id'), sa.text('lower(product)')], unique=True)
    op.create_table('product_mfg_attributes',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('parent_id', sa.BigInteger(), nullable=False),
    sa.Column('line_no', sa.Integer(), nullable=False),
    sa.Column('attribute', sa.Text(), server_default='', nullable=False),
    sa.Column('uom', sa.Text(), server_default='', nullable=False),
    sa.Column('number', sa.Numeric(), nullable=True),
    sa.Column('value', sa.Text(), server_default='', nullable=False),
    sa.ForeignKeyConstraint(['parent_id'], ['product_mfg.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_product_mfg_attributes_parent_id'), 'product_mfg_attributes', ['parent_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_product_mfg_attributes_parent_id'), table_name='product_mfg_attributes')
    op.drop_table('product_mfg_attributes')
    op.drop_index('uq_product_mfg_key', table_name='product_mfg')
    op.drop_index(op.f('ix_product_mfg_company_id'), table_name='product_mfg')
    op.drop_table('product_mfg')
