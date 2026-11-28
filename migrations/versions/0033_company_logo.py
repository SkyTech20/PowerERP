"""company logo: Administration > System settings, printed on the invoices, the credit notes and the trace export

The logo is kept on the company profile as a PNG data URL ('' = no logo).

Revision ID: 0033
Revises: 0032
Create Date: 2026-11-28 06:00:00
"""
from alembic import op
import sqlalchemy as sa


revision = '0033'
down_revision = '0032'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('company_profile', sa.Column('logo', sa.Text(), server_default='', nullable=False))


def downgrade():
    op.drop_column('company_profile', 'logo')
