"""supply chain indicators (step 7 of the SCOR / ISO plan): Reports > Supply chain indicators

No table: the indicators are read from the data the ERP keeps. The roles that release production orders get the
view of the new screen (rep.scor:view).

Revision ID: 0032
Revises: 0031
Create Date: 2026-11-26 02:30:00
"""
from alembic import op
import sqlalchemy as sa


revision = '0032'
down_revision = '0031'
branch_labels = None
depends_on = None


def upgrade():
    op.get_bind().execute(
        sa.text(
            "INSERT INTO role_permissions (role_code, permission) "
            "SELECT role_code, 'rep.scor:view' FROM role_permissions WHERE permission = 'prod.orders:release' "
            "ON CONFLICT DO NOTHING"
        )
    )


def downgrade():
    op.get_bind().execute(sa.text("DELETE FROM role_permissions WHERE permission = 'rep.scor:view'"))
