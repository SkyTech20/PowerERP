"""traceability screen: prod.traceability:view for the roles that see the production orders

Revision ID: 0028
Revises: 0027
Create Date: 2026-11-25 20:00:00

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0028"
down_revision = "0027"
branch_labels = None
depends_on = None


def upgrade():
    op.get_bind().execute(
        sa.text(
            "INSERT INTO role_permissions (role_code, permission) "
            "SELECT role_code, 'prod.traceability:view' FROM role_permissions WHERE permission = 'prod.orders:view' "
            "ON CONFLICT DO NOTHING"
        )
    )


def downgrade():
    op.get_bind().execute(sa.text("DELETE FROM role_permissions WHERE permission = 'prod.traceability:view'"))
