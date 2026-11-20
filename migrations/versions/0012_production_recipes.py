"""Production (P8): recipes with their materials, outputs (co / by-products) and operations.

Revision ID: 0012
Revises: 0011
Create Date: 2026-11-20
"""
from alembic import op
import sqlalchemy as sa


revision = '0012'
down_revision = '0011'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('recipes',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('company_id', sa.BigInteger(), nullable=False),
    sa.Column('product', sa.Text(), server_default='', nullable=False),
    sa.Column('revision', sa.Text(), server_default='', nullable=False),
    sa.Column('desc_fr', sa.Text(), server_default='', nullable=False),
    sa.Column('desc_en', sa.Text(), server_default='', nullable=False),
    sa.Column('process_type', sa.String(length=30), server_default='discrete', nullable=False),
    sa.Column('base_qty', sa.Numeric(), nullable=True),
    sa.Column('uom', sa.Text(), server_default='', nullable=False),
    sa.Column('min_batch', sa.Numeric(), nullable=True),
    sa.Column('max_batch', sa.Numeric(), nullable=True),
    sa.Column('yield_pct', sa.Numeric(), nullable=True),
    sa.Column('notes', sa.Text(), server_default='', nullable=False),
    sa.Column('status', sa.String(length=30), server_default='draft', nullable=False),
    sa.CheckConstraint("process_type IN ('discrete', 'batch', 'continuous')", name='ck_recipes_process_type'),
    sa.CheckConstraint("status IN ('draft', 'in_review', 'approved', 'obsolete')", name='ck_recipes_status'),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
    sa.PrimaryKeyConstraint('id'),
    comment='business key: lower(product), lower(revision)'
    )
    op.create_index(op.f('ix_recipes_company_id'), 'recipes', ['company_id'], unique=False)
    op.create_index('uq_recipes_key', 'recipes', [sa.text('company_id'), sa.text('lower(product)'), sa.text('lower(revision)')], unique=True)
    op.create_table('recipes_materials',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('parent_id', sa.BigInteger(), nullable=False),
    sa.Column('line_no', sa.Integer(), nullable=False),
    sa.Column('seq', sa.Integer(), server_default='0', nullable=False),
    sa.Column('component', sa.Text(), server_default='', nullable=False),
    sa.Column('qty_per', sa.Numeric(), nullable=True),
    sa.Column('uom', sa.Text(), server_default='', nullable=False),
    sa.Column('fixed_qty', sa.Boolean(), server_default='false', nullable=False),
    sa.Column('scrap_pct', sa.Numeric(), nullable=True),
    sa.Column('op_seq', sa.Integer(), server_default='0', nullable=False),
    sa.Column('issue_method', sa.String(length=30), server_default='manual', nullable=False),
    sa.Column('warehouse', sa.Text(), server_default='', nullable=False),
    sa.Column('notes', sa.Text(), server_default='', nullable=False),
    sa.CheckConstraint("issue_method IN ('manual', 'backflush', 'pick')", name='ck_recipes_materials_issue_method'),
    sa.ForeignKeyConstraint(['parent_id'], ['recipes.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_recipes_materials_parent_id'), 'recipes_materials', ['parent_id'], unique=False)
    op.create_table('recipes_operations',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('parent_id', sa.BigInteger(), nullable=False),
    sa.Column('line_no', sa.Integer(), nullable=False),
    sa.Column('op_seq', sa.Integer(), server_default='0', nullable=False),
    sa.Column('operation', sa.Text(), server_default='', nullable=False),
    sa.Column('desc_fr', sa.Text(), server_default='', nullable=False),
    sa.Column('desc_en', sa.Text(), server_default='', nullable=False),
    sa.Column('work_center', sa.Text(), server_default='', nullable=False),
    sa.Column('resource', sa.Text(), server_default='', nullable=False),
    sa.Column('capability', sa.Text(), server_default='', nullable=False),
    sa.Column('setup_min', sa.Numeric(), nullable=True),
    sa.Column('run_format', sa.String(length=30), server_default='min_per_unit', nullable=False),
    sa.Column('run_value', sa.Numeric(), nullable=True),
    sa.Column('crew', sa.Integer(), server_default='0', nullable=False),
    sa.Column('queue_min', sa.Integer(), server_default='0', nullable=False),
    sa.Column('move_min', sa.Integer(), server_default='0', nullable=False),
    sa.Column('min_wait_min', sa.Numeric(), nullable=True),
    sa.Column('max_wait_min', sa.Numeric(), nullable=True),
    sa.Column('yield_pct', sa.Numeric(), nullable=True),
    sa.Column('reporting_point', sa.Boolean(), server_default='false', nullable=False),
    sa.Column('subcontract', sa.Boolean(), server_default='false', nullable=False),
    sa.Column('supplier', sa.Text(), server_default='', nullable=False),
    sa.Column('subcontract_cost', sa.Numeric(), nullable=True),
    sa.Column('subcontract_days', sa.Integer(), server_default='0', nullable=False),
    sa.Column('predecessors', sa.Text(), server_default='', nullable=False),
    sa.Column('instruction_fr', sa.Text(), server_default='', nullable=False),
    sa.Column('instruction_en', sa.Text(), server_default='', nullable=False),
    sa.CheckConstraint("run_format IN ('min_per_unit', 'units_per_hour', 'min_per_lot')", name='ck_recipes_operations_run_format'),
    sa.ForeignKeyConstraint(['parent_id'], ['recipes.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_recipes_operations_parent_id'), 'recipes_operations', ['parent_id'], unique=False)
    op.create_table('recipes_outputs',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('parent_id', sa.BigInteger(), nullable=False),
    sa.Column('line_no', sa.Integer(), nullable=False),
    sa.Column('product', sa.Text(), server_default='', nullable=False),
    sa.Column('kind', sa.String(length=30), server_default='coproduct', nullable=False),
    sa.Column('qty_per', sa.Numeric(), nullable=True),
    sa.Column('uom', sa.Text(), server_default='', nullable=False),
    sa.Column('cost_pct', sa.Numeric(), nullable=True),
    sa.CheckConstraint("kind IN ('coproduct', 'byproduct')", name='ck_recipes_outputs_kind'),
    sa.ForeignKeyConstraint(['parent_id'], ['recipes.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_recipes_outputs_parent_id'), 'recipes_outputs', ['parent_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_recipes_outputs_parent_id'), table_name='recipes_outputs')
    op.drop_table('recipes_outputs')
    op.drop_index(op.f('ix_recipes_operations_parent_id'), table_name='recipes_operations')
    op.drop_table('recipes_operations')
    op.drop_index(op.f('ix_recipes_materials_parent_id'), table_name='recipes_materials')
    op.drop_table('recipes_materials')
    op.drop_index('uq_recipes_key', table_name='recipes')
    op.drop_index(op.f('ix_recipes_company_id'), table_name='recipes')
    op.drop_table('recipes')
