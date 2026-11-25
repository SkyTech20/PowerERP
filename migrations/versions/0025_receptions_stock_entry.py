"""Purchasing: a reception goes into the stock (posted once, IN movements REC <number>); each line keeps where
and how: location, lot, the supplier's lot, serial number and expiry date. The new action "pur.receptions:post"
is given to the roles that could edit the receptions.

Revision ID: 0025
Revises: 0024
Create Date: 2026-11-25
"""
from alembic import op
import sqlalchemy as sa


revision = '0025'
down_revision = '0024'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('receptions', sa.Column('stock_posted', sa.Boolean(), nullable=True))
    op.add_column('receptions', sa.Column('stock_posted_at', sa.DateTime(), nullable=True))
    op.add_column('receptions', sa.Column('stock_posted_by', sa.Text(), nullable=True))
    for col, kind in (
        ('location', sa.Text()),
        ('lot', sa.Text()),
        ('supplier_lot', sa.Text()),
        ('serial', sa.Text()),
        ('expiry', sa.Date()),
    ):
        op.add_column('reception_lines', sa.Column(col, kind, nullable=True))
    bind = op.get_bind()
    bind.execute(sa.text(
        "INSERT INTO role_permissions (role_code, permission) "
        "SELECT role_code, 'pur.receptions:post' FROM role_permissions WHERE permission = 'pur.receptions:edit' "
        "ON CONFLICT DO NOTHING"
    ))


def downgrade():
    op.get_bind().execute(sa.text("DELETE FROM role_permissions WHERE permission = 'pur.receptions:post'"))
    for col in ('expiry', 'serial', 'supplier_lot', 'lot', 'location'):
        op.drop_column('reception_lines', col)
    op.drop_column('receptions', 'stock_posted_by')
    op.drop_column('receptions', 'stock_posted_at')
    op.drop_column('receptions', 'stock_posted')
