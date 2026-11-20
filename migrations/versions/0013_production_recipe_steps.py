"""Production (P9): the steps of the recipe operations.

Revision ID: 0013
Revises: 0012
Create Date: 2026-11-20
"""
from alembic import op
import sqlalchemy as sa


revision = '0013'
down_revision = '0012'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('recipes_steps',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('parent_id', sa.BigInteger(), nullable=False),
    sa.Column('line_no', sa.Integer(), nullable=False),
    sa.Column('op_seq', sa.Integer(), server_default='0', nullable=False),
    sa.Column('step', sa.Integer(), server_default='0', nullable=False),
    sa.Column('kind', sa.String(length=30), server_default='instruction', nullable=False),
    sa.Column('title_fr', sa.Text(), server_default='', nullable=False),
    sa.Column('title_en', sa.Text(), server_default='', nullable=False),
    sa.Column('instruction_fr', sa.Text(), server_default='', nullable=False),
    sa.Column('instruction_en', sa.Text(), server_default='', nullable=False),
    sa.Column('attachment_url', sa.Text(), server_default='', nullable=False),
    sa.Column('duration_min', sa.Numeric(), nullable=True),
    sa.Column('param', sa.Text(), server_default='', nullable=False),
    sa.Column('data_type', sa.String(length=30), server_default='number', nullable=False),
    sa.Column('uom', sa.Text(), server_default='', nullable=False),
    sa.Column('target', sa.Numeric(), nullable=True),
    sa.Column('min', sa.Numeric(), nullable=True),
    sa.Column('max', sa.Numeric(), nullable=True),
    sa.Column('options', sa.Text(), server_default='', nullable=False),
    sa.Column('required', sa.Boolean(), server_default='false', nullable=False),
    sa.Column('critical', sa.Boolean(), server_default='false', nullable=False),
    sa.Column('on_fail', sa.String(length=30), server_default='block', nullable=False),
    sa.Column('frequency', sa.String(length=30), server_default='once', nullable=False),
    sa.Column('frequency_value', sa.Numeric(), nullable=True),
    sa.Column('material_seq', sa.Integer(), server_default='0', nullable=False),
    sa.Column('required_role', sa.Text(), server_default='', nullable=False),
    sa.Column('second_signature', sa.Boolean(), server_default='false', nullable=False),
    sa.Column('condition', sa.Text(), server_default='', nullable=False),
    sa.CheckConstraint("data_type IN ('number', 'text', 'yes_no', 'list', 'photo')", name='ck_recipes_steps_data_type'),
    sa.CheckConstraint("frequency IN ('once', 'every_n_units', 'every_n_min', 'per_lot')", name='ck_recipes_steps_frequency'),
    sa.CheckConstraint("kind IN ('instruction', 'material_add', 'parameter', 'measure', 'check', 'timer', 'output', 'signature')", name='ck_recipes_steps_kind'),
    sa.CheckConstraint("on_fail IN ('block', 'warn', 'hold_lot')", name='ck_recipes_steps_on_fail'),
    sa.ForeignKeyConstraint(['parent_id'], ['recipes.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_recipes_steps_parent_id'), 'recipes_steps', ['parent_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_recipes_steps_parent_id'), table_name='recipes_steps')
    op.drop_table('recipes_steps')
