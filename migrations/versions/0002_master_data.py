"""Master data tables (R1): GL accounts, cost centers, suppliers, taxes, units, categories, products, warehouses, locations.

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-19
"""
from alembic import op
import sqlalchemy as sa


revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None


def upgrade():

    op.create_table('cost_centers',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('company_id', sa.BigInteger(), nullable=False),
    sa.Column('cc1', sa.Text(), server_default='', nullable=False),
    sa.Column('cc2', sa.Text(), server_default='', nullable=False),
    sa.Column('description', sa.Text(), server_default='', nullable=False),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
    sa.PrimaryKeyConstraint('id'),
    comment='business key: lower(cc1), lower(cc2)'
    )
    op.create_index(op.f('ix_cost_centers_company_id'), 'cost_centers', ['company_id'], unique=False)
    op.create_index('uq_cost_centers_key', 'cost_centers', [sa.text('company_id'), sa.text('lower(cc1)'), sa.text('lower(cc2)')], unique=True)
    op.create_table('gl_accounts',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('company_id', sa.BigInteger(), nullable=False),
    sa.Column('code', sa.Text(), server_default='', nullable=False),
    sa.Column('description', sa.Text(), server_default='', nullable=False),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
    sa.PrimaryKeyConstraint('id'),
    comment='business key: lower(code)'
    )
    op.create_index(op.f('ix_gl_accounts_company_id'), 'gl_accounts', ['company_id'], unique=False)
    op.create_index('uq_gl_accounts_key', 'gl_accounts', [sa.text('company_id'), sa.text('lower(code)')], unique=True)
    op.create_table('locations',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('company_id', sa.BigInteger(), nullable=False),
    sa.Column('warehouse', sa.Text(), server_default='', nullable=False),
    sa.Column('code', sa.Text(), server_default='', nullable=False),
    sa.Column('zone', sa.Text(), server_default='', nullable=False),
    sa.Column('aisle', sa.Text(), server_default='', nullable=False),
    sa.Column('rack', sa.Text(), server_default='', nullable=False),
    sa.Column('level', sa.Text(), server_default='', nullable=False),
    sa.Column('bin', sa.Text(), server_default='', nullable=False),
    sa.Column('description', sa.Text(), server_default='', nullable=False),
    sa.Column('type', sa.String(length=30), server_default='picking', nullable=False),
    sa.Column('max_weight', sa.Numeric(), nullable=True),
    sa.Column('max_volume', sa.Numeric(), nullable=True),
    sa.Column('max_pallets', sa.Integer(), server_default='0', nullable=False),
    sa.Column('mix_products', sa.Boolean(), server_default='false', nullable=False),
    sa.Column('mix_lots', sa.Boolean(), server_default='false', nullable=False),
    sa.Column('blocked', sa.Boolean(), server_default='false', nullable=False),
    sa.Column('pick_seq', sa.Integer(), server_default='0', nullable=False),
    sa.Column('active', sa.Boolean(), server_default='false', nullable=False),
    sa.CheckConstraint("type IN ('picking', 'reserve', 'receiving', 'shipping', 'quarantine', 'staging')", name='ck_locations_type'),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
    sa.PrimaryKeyConstraint('id'),
    comment='business key: lower(warehouse), lower(code)'
    )
    op.create_index(op.f('ix_locations_company_id'), 'locations', ['company_id'], unique=False)
    op.create_index('uq_locations_key', 'locations', [sa.text('company_id'), sa.text('lower(warehouse)'), sa.text('lower(code)')], unique=True)
    op.create_table('product_categories',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('company_id', sa.BigInteger(), nullable=False),
    sa.Column('code', sa.Text(), server_default='', nullable=False),
    sa.Column('desc_fr', sa.Text(), server_default='', nullable=False),
    sa.Column('desc_en', sa.Text(), server_default='', nullable=False),
    sa.Column('parent', sa.Text(), server_default='', nullable=False),
    sa.Column('active', sa.Boolean(), server_default='false', nullable=False),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
    sa.PrimaryKeyConstraint('id'),
    comment='business key: lower(code)'
    )
    op.create_index(op.f('ix_product_categories_company_id'), 'product_categories', ['company_id'], unique=False)
    op.create_index('uq_product_categories_key', 'product_categories', [sa.text('company_id'), sa.text('lower(code)')], unique=True)
    op.create_table('products',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('company_id', sa.BigInteger(), nullable=False),
    sa.Column('code', sa.Text(), server_default='', nullable=False),
    sa.Column('status', sa.String(length=30), server_default='active', nullable=False),
    sa.Column('type', sa.String(length=30), server_default='stock', nullable=False),
    sa.Column('desc_fr', sa.Text(), server_default='', nullable=False),
    sa.Column('desc_en', sa.Text(), server_default='', nullable=False),
    sa.Column('long_desc_fr', sa.Text(), server_default='', nullable=False),
    sa.Column('long_desc_en', sa.Text(), server_default='', nullable=False),
    sa.Column('category', sa.Text(), server_default='', nullable=False),
    sa.Column('brand', sa.Text(), server_default='', nullable=False),
    sa.Column('model', sa.Text(), server_default='', nullable=False),
    sa.Column('upc', sa.Text(), server_default='', nullable=False),
    sa.Column('manufacturer', sa.Text(), server_default='', nullable=False),
    sa.Column('mfr_part_no', sa.Text(), server_default='', nullable=False),
    sa.Column('image_url', sa.Text(), server_default='', nullable=False),
    sa.Column('spec_url', sa.Text(), server_default='', nullable=False),
    sa.Column('sds_url', sa.Text(), server_default='', nullable=False),
    sa.Column('stock_uom', sa.Text(), server_default='', nullable=False),
    sa.Column('purchase_uom', sa.Text(), server_default='', nullable=False),
    sa.Column('purchase_factor', sa.Numeric(), nullable=True),
    sa.Column('sales_uom', sa.Text(), server_default='', nullable=False),
    sa.Column('sales_factor', sa.Numeric(), nullable=True),
    sa.Column('weight', sa.Numeric(), nullable=True),
    sa.Column('weight_uom', sa.Text(), server_default='', nullable=False),
    sa.Column('length', sa.Numeric(), nullable=True),
    sa.Column('width', sa.Numeric(), nullable=True),
    sa.Column('height', sa.Numeric(), nullable=True),
    sa.Column('dim_uom', sa.Text(), server_default='', nullable=False),
    sa.Column('volume', sa.Numeric(), nullable=True),
    sa.Column('cost_method', sa.String(length=30), server_default='avg', nullable=False),
    sa.Column('std_cost', sa.Numeric(), nullable=True),
    sa.Column('currency', sa.Text(), server_default='', nullable=False),
    sa.Column('price1', sa.Numeric(), nullable=True),
    sa.Column('price2', sa.Numeric(), nullable=True),
    sa.Column('price3', sa.Numeric(), nullable=True),
    sa.Column('price4', sa.Numeric(), nullable=True),
    sa.Column('price5', sa.Numeric(), nullable=True),
    sa.Column('min_price', sa.Numeric(), nullable=True),
    sa.Column('sales_tax_group', sa.Text(), server_default='', nullable=False),
    sa.Column('purchase_tax_group', sa.Text(), server_default='', nullable=False),
    sa.Column('eco_fee', sa.Numeric(), nullable=True),
    sa.Column('eco_fee_code', sa.Text(), server_default='', nullable=False),
    sa.Column('gl_sales', sa.Text(), server_default='', nullable=False),
    sa.Column('gl_purchase', sa.Text(), server_default='', nullable=False),
    sa.Column('gl_inventory', sa.Text(), server_default='', nullable=False),
    sa.Column('gl_cogs', sa.Text(), server_default='', nullable=False),
    sa.Column('cost_center', sa.Text(), server_default='', nullable=False),
    sa.Column('project', sa.Text(), server_default='', nullable=False),
    sa.Column('stocked', sa.Boolean(), server_default='false', nullable=False),
    sa.Column('lot_control', sa.Boolean(), server_default='false', nullable=False),
    sa.Column('serial_control', sa.Boolean(), server_default='false', nullable=False),
    sa.Column('expiry_control', sa.Boolean(), server_default='false', nullable=False),
    sa.Column('shelf_life_days', sa.Integer(), server_default='0', nullable=False),
    sa.Column('default_warehouse', sa.Text(), server_default='', nullable=False),
    sa.Column('abc_class', sa.String(length=30), server_default='', nullable=False),
    sa.Column('sellable', sa.Boolean(), server_default='false', nullable=False),
    sa.Column('purchasable', sa.Boolean(), server_default='false', nullable=False),
    sa.Column('po_required', sa.Boolean(), server_default='false', nullable=False),
    sa.Column('warranty_months', sa.Integer(), server_default='0', nullable=False),
    sa.Column('country_origin', sa.Text(), server_default='', nullable=False),
    sa.Column('hs_code', sa.Text(), server_default='', nullable=False),
    sa.Column('freight_class', sa.Text(), server_default='', nullable=False),
    sa.Column('hazardous', sa.Boolean(), server_default='false', nullable=False),
    sa.Column('notes', sa.Text(), server_default='', nullable=False),
    sa.Column('avg_cost', sa.Numeric(), nullable=True),
    sa.Column('last_cost', sa.Numeric(), nullable=True),
    sa.CheckConstraint("abc_class IN ('', 'A', 'B', 'C')", name='ck_products_abc_class'),
    sa.CheckConstraint("cost_method IN ('avg', 'std')", name='ck_products_cost_method'),
    sa.CheckConstraint("status IN ('active', 'inactive', 'discontinued')", name='ck_products_status'),
    sa.CheckConstraint("type IN ('stock', 'nonstock', 'service', 'kit', 'raw')", name='ck_products_type'),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
    sa.PrimaryKeyConstraint('id'),
    comment='business key: lower(code)'
    )
    op.create_index(op.f('ix_products_company_id'), 'products', ['company_id'], unique=False)
    op.create_index('uq_products_key', 'products', [sa.text('company_id'), sa.text('lower(code)')], unique=True)
    op.create_table('suppliers',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('company_id', sa.BigInteger(), nullable=False),
    sa.Column('code', sa.Text(), server_default='', nullable=False),
    sa.Column('name', sa.Text(), server_default='', nullable=False),
    sa.Column('term_code', sa.Text(), server_default='', nullable=False),
    sa.Column('term_desc', sa.Text(), server_default='', nullable=False),
    sa.Column('address1', sa.Text(), server_default='', nullable=False),
    sa.Column('address2', sa.Text(), server_default='', nullable=False),
    sa.Column('city', sa.Text(), server_default='', nullable=False),
    sa.Column('province', sa.Text(), server_default='', nullable=False),
    sa.Column('country', sa.Text(), server_default='', nullable=False),
    sa.Column('zip_code', sa.Text(), server_default='', nullable=False),
    sa.Column('no_tps', sa.Text(), server_default='', nullable=False),
    sa.Column('no_tvq', sa.Text(), server_default='', nullable=False),
    sa.Column('code_ach', sa.Text(), server_default='', nullable=False),
    sa.Column('desc_ach', sa.Text(), server_default='', nullable=False),
    sa.Column('dept_sauv', sa.Text(), server_default='', nullable=False),
    sa.Column('type_po', sa.Integer(), server_default='0', nullable=False),
    sa.Column('statut_ach', sa.Integer(), server_default='0', nullable=False),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
    sa.PrimaryKeyConstraint('id'),
    comment='business key: lower(code)'
    )
    op.create_index(op.f('ix_suppliers_company_id'), 'suppliers', ['company_id'], unique=False)
    op.create_index('uq_suppliers_key', 'suppliers', [sa.text('company_id'), sa.text('lower(code)')], unique=True)
    op.create_table('tax_codes',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('company_id', sa.BigInteger(), nullable=False),
    sa.Column('code', sa.Text(), server_default='', nullable=False),
    sa.Column('desc_fr', sa.Text(), server_default='', nullable=False),
    sa.Column('desc_en', sa.Text(), server_default='', nullable=False),
    sa.Column('kind', sa.String(length=30), server_default='gst', nullable=False),
    sa.Column('jurisdiction', sa.Text(), server_default='', nullable=False),
    sa.Column('registration_no', sa.Text(), server_default='', nullable=False),
    sa.Column('gl_collected', sa.Text(), server_default='', nullable=False),
    sa.Column('gl_recoverable', sa.Text(), server_default='', nullable=False),
    sa.Column('recoverable_pct', sa.Numeric(), nullable=True),
    sa.Column('active', sa.Boolean(), server_default='false', nullable=False),
    sa.CheckConstraint("kind IN ('gst', 'pst', 'hst', 'other')", name='ck_tax_codes_kind'),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
    sa.PrimaryKeyConstraint('id'),
    comment='business key: lower(code)'
    )
    op.create_index(op.f('ix_tax_codes_company_id'), 'tax_codes', ['company_id'], unique=False)
    op.create_index('uq_tax_codes_key', 'tax_codes', [sa.text('company_id'), sa.text('lower(code)')], unique=True)
    op.create_table('tax_groups',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('company_id', sa.BigInteger(), nullable=False),
    sa.Column('code', sa.Text(), server_default='', nullable=False),
    sa.Column('desc_fr', sa.Text(), server_default='', nullable=False),
    sa.Column('desc_en', sa.Text(), server_default='', nullable=False),
    sa.Column('province', sa.Text(), server_default='', nullable=False),
    sa.Column('treatment', sa.String(length=30), server_default='taxable', nullable=False),
    sa.Column('active', sa.Boolean(), server_default='false', nullable=False),
    sa.CheckConstraint("treatment IN ('taxable', 'zero', 'exempt')", name='ck_tax_groups_treatment'),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
    sa.PrimaryKeyConstraint('id'),
    comment='business key: lower(code)'
    )
    op.create_index(op.f('ix_tax_groups_company_id'), 'tax_groups', ['company_id'], unique=False)
    op.create_index('uq_tax_groups_key', 'tax_groups', [sa.text('company_id'), sa.text('lower(code)')], unique=True)
    op.create_table('uoms',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('company_id', sa.BigInteger(), nullable=False),
    sa.Column('code', sa.Text(), server_default='', nullable=False),
    sa.Column('desc_fr', sa.Text(), server_default='', nullable=False),
    sa.Column('desc_en', sa.Text(), server_default='', nullable=False),
    sa.Column('type', sa.String(length=30), server_default='count', nullable=False),
    sa.Column('active', sa.Boolean(), server_default='false', nullable=False),
    sa.CheckConstraint("type IN ('count', 'weight', 'length', 'area', 'volume', 'time')", name='ck_uoms_type'),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
    sa.PrimaryKeyConstraint('id'),
    comment='business key: lower(code)'
    )
    op.create_index(op.f('ix_uoms_company_id'), 'uoms', ['company_id'], unique=False)
    op.create_index('uq_uoms_key', 'uoms', [sa.text('company_id'), sa.text('lower(code)')], unique=True)
    op.create_table('warehouses',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('company_id', sa.BigInteger(), nullable=False),
    sa.Column('code', sa.Text(), server_default='', nullable=False),
    sa.Column('name_fr', sa.Text(), server_default='', nullable=False),
    sa.Column('name_en', sa.Text(), server_default='', nullable=False),
    sa.Column('type', sa.String(length=30), server_default='main', nullable=False),
    sa.Column('address1', sa.Text(), server_default='', nullable=False),
    sa.Column('city', sa.Text(), server_default='', nullable=False),
    sa.Column('province', sa.Text(), server_default='', nullable=False),
    sa.Column('zip_code', sa.Text(), server_default='', nullable=False),
    sa.Column('country', sa.Text(), server_default='', nullable=False),
    sa.Column('manager', sa.Text(), server_default='', nullable=False),
    sa.Column('phone', sa.Text(), server_default='', nullable=False),
    sa.Column('email', sa.Text(), server_default='', nullable=False),
    sa.Column('use_locations', sa.Boolean(), server_default='false', nullable=False),
    sa.Column('allow_negative', sa.Boolean(), server_default='false', nullable=False),
    sa.Column('receiving_loc', sa.Text(), server_default='', nullable=False),
    sa.Column('shipping_loc', sa.Text(), server_default='', nullable=False),
    sa.Column('active', sa.Boolean(), server_default='false', nullable=False),
    sa.CheckConstraint("type IN ('main', 'transit', 'consignment', 'quarantine', 'virtual')", name='ck_warehouses_type'),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
    sa.PrimaryKeyConstraint('id'),
    comment='business key: lower(code)'
    )
    op.create_index(op.f('ix_warehouses_company_id'), 'warehouses', ['company_id'], unique=False)
    op.create_index('uq_warehouses_key', 'warehouses', [sa.text('company_id'), sa.text('lower(code)')], unique=True)
    op.create_table('products_lines',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('parent_id', sa.BigInteger(), nullable=False),
    sa.Column('line_no', sa.Integer(), nullable=False),
    sa.Column('supplier_code', sa.Text(), server_default='', nullable=False),
    sa.Column('supplier_item', sa.Text(), server_default='', nullable=False),
    sa.Column('purchase_price', sa.Numeric(), nullable=True),
    sa.Column('currency', sa.Text(), server_default='', nullable=False),
    sa.Column('lead_time_days', sa.Integer(), server_default='0', nullable=False),
    sa.Column('min_order_qty', sa.Numeric(), nullable=True),
    sa.Column('preferred', sa.Boolean(), server_default='false', nullable=False),
    sa.ForeignKeyConstraint(['parent_id'], ['products.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_products_lines_parent_id'), 'products_lines', ['parent_id'], unique=False)
    op.create_table('tax_codes_lines',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('parent_id', sa.BigInteger(), nullable=False),
    sa.Column('line_no', sa.Integer(), nullable=False),
    sa.Column('start_date', sa.Date(), nullable=True),
    sa.Column('end_date', sa.Date(), nullable=True),
    sa.Column('rate', sa.Numeric(), nullable=True),
    sa.ForeignKeyConstraint(['parent_id'], ['tax_codes.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tax_codes_lines_parent_id'), 'tax_codes_lines', ['parent_id'], unique=False)
    op.create_table('tax_groups_lines',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('parent_id', sa.BigInteger(), nullable=False),
    sa.Column('line_no', sa.Integer(), nullable=False),
    sa.Column('seq', sa.Integer(), server_default='0', nullable=False),
    sa.Column('tax_code', sa.Text(), server_default='', nullable=False),
    sa.Column('compound', sa.Boolean(), server_default='false', nullable=False),
    sa.ForeignKeyConstraint(['parent_id'], ['tax_groups.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tax_groups_lines_parent_id'), 'tax_groups_lines', ['parent_id'], unique=False)



def downgrade():

    op.drop_index(op.f('ix_tax_groups_lines_parent_id'), table_name='tax_groups_lines')
    op.drop_table('tax_groups_lines')
    op.drop_index(op.f('ix_tax_codes_lines_parent_id'), table_name='tax_codes_lines')
    op.drop_table('tax_codes_lines')
    op.drop_index(op.f('ix_products_lines_parent_id'), table_name='products_lines')
    op.drop_table('products_lines')
    op.drop_index('uq_warehouses_key', table_name='warehouses')
    op.drop_index(op.f('ix_warehouses_company_id'), table_name='warehouses')
    op.drop_table('warehouses')
    op.drop_index('uq_uoms_key', table_name='uoms')
    op.drop_index(op.f('ix_uoms_company_id'), table_name='uoms')
    op.drop_table('uoms')
    op.drop_index('uq_tax_groups_key', table_name='tax_groups')
    op.drop_index(op.f('ix_tax_groups_company_id'), table_name='tax_groups')
    op.drop_table('tax_groups')
    op.drop_index('uq_tax_codes_key', table_name='tax_codes')
    op.drop_index(op.f('ix_tax_codes_company_id'), table_name='tax_codes')
    op.drop_table('tax_codes')
    op.drop_index('uq_suppliers_key', table_name='suppliers')
    op.drop_index(op.f('ix_suppliers_company_id'), table_name='suppliers')
    op.drop_table('suppliers')
    op.drop_index('uq_products_key', table_name='products')
    op.drop_index(op.f('ix_products_company_id'), table_name='products')
    op.drop_table('products')
    op.drop_index('uq_product_categories_key', table_name='product_categories')
    op.drop_index(op.f('ix_product_categories_company_id'), table_name='product_categories')
    op.drop_table('product_categories')
    op.drop_index('uq_locations_key', table_name='locations')
    op.drop_index(op.f('ix_locations_company_id'), table_name='locations')
    op.drop_table('locations')
    op.drop_index('uq_gl_accounts_key', table_name='gl_accounts')
    op.drop_index(op.f('ix_gl_accounts_company_id'), table_name='gl_accounts')
    op.drop_table('gl_accounts')
    op.drop_index('uq_cost_centers_key', table_name='cost_centers')
    op.drop_index(op.f('ix_cost_centers_company_id'), table_name='cost_centers')
    op.drop_table('cost_centers')

