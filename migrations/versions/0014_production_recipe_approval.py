"""Production (P10): approval of the recipes (who / when, validity, default version) and their history.

Revision ID: 0014
Revises: 0013
Create Date: 2026-11-20
"""
from alembic import op
import sqlalchemy as sa


revision = '0014'
down_revision = '0013'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('recipes_history',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('parent_id', sa.BigInteger(), nullable=False),
    sa.Column('line_no', sa.Integer(), nullable=False),
    sa.Column('at', sa.DateTime(), nullable=True),
    sa.Column('user', sa.Text(), server_default='', nullable=False),
    sa.Column('action', sa.Text(), server_default='', nullable=False),
    sa.Column('from', sa.Text(), server_default='', nullable=False),
    sa.Column('to', sa.Text(), server_default='', nullable=False),
    sa.Column('comment', sa.Text(), server_default='', nullable=False),
    sa.ForeignKeyConstraint(['parent_id'], ['recipes.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_recipes_history_parent_id'), 'recipes_history', ['parent_id'], unique=False)
    op.add_column('recipes', sa.Column('change_reason', sa.Text(), server_default='', nullable=False))
    op.add_column('recipes', sa.Column('effective_from', sa.Date(), nullable=True))
    op.add_column('recipes', sa.Column('effective_to', sa.Date(), nullable=True))
    op.add_column('recipes', sa.Column('is_default', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('recipes', sa.Column('submitted_by', sa.Text(), server_default='', nullable=False))
    op.add_column('recipes', sa.Column('approved_by', sa.Text(), server_default='', nullable=False))
    op.add_column('recipes', sa.Column('approved_at', sa.DateTime(), nullable=True))


def downgrade():
    op.drop_column('recipes', 'approved_at')
    op.drop_column('recipes', 'approved_by')
    op.drop_column('recipes', 'submitted_by')
    op.drop_column('recipes', 'is_default')
    op.drop_column('recipes', 'effective_to')
    op.drop_column('recipes', 'effective_from')
    op.drop_column('recipes', 'change_reason')
    op.drop_index(op.f('ix_recipes_history_parent_id'), table_name='recipes_history')
    op.drop_table('recipes_history')
