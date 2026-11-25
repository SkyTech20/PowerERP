"""Locations: one lot of a product per location, always (the client's rule). The location's "Several lots" option
(mix_lots) is dropped: the stock movements refuse a second lot of a product in a location that still has the first.

Stock that is already mixed stays as it is (a migration does not move stock); the locations where it is are listed
in the migration's log, and such a location refuses any other lot of that product until it is empty.

Revision ID: 0024
Revises: 0023
Create Date: 2026-11-25
"""
import logging

from alembic import op
import sqlalchemy as sa


revision = '0024'
down_revision = '0023'
branch_labels = None
depends_on = None

log = logging.getLogger("alembic.runtime.migration")


def upgrade():
    mixed = op.get_bind().execute(
        sa.text(
            "SELECT company_id, upper(warehouse), upper(location), upper(product), count(DISTINCT lower(lot)) FROM stock_balances "
            "WHERE qty > 0 AND location <> '' GROUP BY 1, 2, 3, 4 HAVING count(DISTINCT lower(lot)) > 1 ORDER BY 1, 2, 3, 4"
        )
    ).fetchall()
    for company, warehouse, location, product, lots in mixed:
        log.warning("company %s: %s / %s holds %s lots of %s", company, warehouse, location, lots, product)
    op.drop_column('locations', 'mix_lots')


def downgrade():
    # Before this migration, a location took several lots unless the option was unchecked
    op.add_column('locations', sa.Column('mix_lots', sa.Boolean(), server_default='false', nullable=False))
    op.execute("UPDATE locations SET mix_lots = true")
