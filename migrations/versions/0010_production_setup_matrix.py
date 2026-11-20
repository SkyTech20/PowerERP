"""Production (P6): setup matrices, one per work center or resource, with the family pairs as lines.

Revision ID: 0010
Revises: 0009
Create Date: 2026-11-20
"""
from alembic import op
import sqlalchemy as sa


revision = '0010'
down_revision = '0009'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('setup_matrices',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('company_id', sa.BigInteger(), nullable=False),
    sa.Column('scope', sa.String(length=30), server_default='work_center', nullable=False),
    sa.Column('scope_code', sa.Text(), server_default='', nullable=False),
    sa.Column('notes', sa.Text(), server_default='', nullable=False),
    sa.Column('active', sa.Boolean(), server_default='false', nullable=False),
    sa.CheckConstraint("scope IN ('work_center', 'resource')", name='ck_setup_matrices_scope'),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
    sa.PrimaryKeyConstraint('id'),
    comment='business key: scope, lower(scope_code)'
    )
    op.create_index(op.f('ix_setup_matrices_company_id'), 'setup_matrices', ['company_id'], unique=False)
    op.create_index('uq_setup_matrices_key', 'setup_matrices', [sa.text('company_id'), sa.text('scope'), sa.text('lower(scope_code)')], unique=True)
    op.create_table('setup_matrices_lines',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('parent_id', sa.BigInteger(), nullable=False),
    sa.Column('line_no', sa.Integer(), nullable=False),
    sa.Column('from_family', sa.Text(), server_default='', nullable=False),
    sa.Column('to_family', sa.Text(), server_default='', nullable=False),
    sa.Column('setup_min', sa.Numeric(), nullable=True),
    sa.Column('setup_cost', sa.Numeric(), nullable=True),
    sa.Column('scrap_qty', sa.Numeric(), nullable=True),
    sa.ForeignKeyConstraint(['parent_id'], ['setup_matrices.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_setup_matrices_lines_parent_id'), 'setup_matrices_lines', ['parent_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_setup_matrices_lines_parent_id'), table_name='setup_matrices_lines')
    op.drop_table('setup_matrices_lines')
    op.drop_index('uq_setup_matrices_key', table_name='setup_matrices')
    op.drop_index(op.f('ix_setup_matrices_company_id'), table_name='setup_matrices')
    op.drop_table('setup_matrices')
