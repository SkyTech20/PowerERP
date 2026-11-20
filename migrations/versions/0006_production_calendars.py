"""Production (P2): working calendars, their shifts by weekday and their exceptions by date.

Revision ID: 0006
Revises: 0005
Create Date: 2026-11-20
"""
from alembic import op
import sqlalchemy as sa


revision = '0006'
down_revision = '0005'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('calendar_exceptions',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('company_id', sa.BigInteger(), nullable=False),
    sa.Column('calendar', sa.Text(), server_default='', nullable=False),
    sa.Column('date', sa.Date(), nullable=True),
    sa.Column('desc_fr', sa.Text(), server_default='', nullable=False),
    sa.Column('desc_en', sa.Text(), server_default='', nullable=False),
    sa.Column('closed', sa.Boolean(), server_default='false', nullable=False),
    sa.Column('start', sa.Text(), server_default='', nullable=False),
    sa.Column('end', sa.Text(), server_default='', nullable=False),
    sa.Column('break_min', sa.Integer(), server_default='0', nullable=False),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
    sa.PrimaryKeyConstraint('id'),
    comment='business key: lower(calendar), date'
    )
    op.create_index(op.f('ix_calendar_exceptions_company_id'), 'calendar_exceptions', ['company_id'], unique=False)
    op.create_index('uq_calendar_exceptions_key', 'calendar_exceptions', [sa.text('company_id'), sa.text('lower(calendar)'), sa.text('date')], unique=True)
    op.create_table('calendars',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('company_id', sa.BigInteger(), nullable=False),
    sa.Column('code', sa.Text(), server_default='', nullable=False),
    sa.Column('desc_fr', sa.Text(), server_default='', nullable=False),
    sa.Column('desc_en', sa.Text(), server_default='', nullable=False),
    sa.Column('active', sa.Boolean(), server_default='false', nullable=False),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
    sa.PrimaryKeyConstraint('id'),
    comment='business key: lower(code)'
    )
    op.create_index(op.f('ix_calendars_company_id'), 'calendars', ['company_id'], unique=False)
    op.create_index('uq_calendars_key', 'calendars', [sa.text('company_id'), sa.text('lower(code)')], unique=True)
    op.create_table('calendars_lines',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('parent_id', sa.BigInteger(), nullable=False),
    sa.Column('line_no', sa.Integer(), nullable=False),
    sa.Column('weekday', sa.Integer(), server_default='0', nullable=False),
    sa.Column('shift', sa.Text(), server_default='', nullable=False),
    sa.Column('start', sa.Text(), server_default='', nullable=False),
    sa.Column('end', sa.Text(), server_default='', nullable=False),
    sa.Column('break_min', sa.Integer(), server_default='0', nullable=False),
    sa.ForeignKeyConstraint(['parent_id'], ['calendars.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_calendars_lines_parent_id'), 'calendars_lines', ['parent_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_calendars_lines_parent_id'), table_name='calendars_lines')
    op.drop_table('calendars_lines')
    op.drop_index('uq_calendars_key', table_name='calendars')
    op.drop_index(op.f('ix_calendars_company_id'), table_name='calendars')
    op.drop_table('calendars')
    op.drop_index('uq_calendar_exceptions_key', table_name='calendar_exceptions')
    op.drop_index(op.f('ix_calendar_exceptions_company_id'), table_name='calendar_exceptions')
    op.drop_table('calendar_exceptions')
