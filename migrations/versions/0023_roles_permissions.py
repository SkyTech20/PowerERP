"""Access control (A1): roles with permissions per screen and action, and the history of their changes.

The users' fixed role (admin / user) becomes a role of the new roles table: ADMIN (every permission, built in)
and USER, given what a plain user could do before (every screen except the administration ones; approving a
recipe stayed with the administrator), so nobody gains or loses access with this migration. The permissions are
listed here as they were on 2026-11-24 (powererp/core/permissions.py can grow later).

Revision ID: 0023
Revises: 0022
Create Date: 2026-11-24
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = '0023'
down_revision = '0022'
branch_labels = None
depends_on = None

USER_PERMISSIONS = """
    gl.accounts:view gl.accounts:create gl.accounts:edit gl.accounts:delete ap.suppliers:view ap.suppliers:create
    ap.suppliers:edit ap.suppliers:delete ap.invoices:view ap.invoices:create ap.invoices:edit ap.invoices:delete
    pur.po:view pur.po:create pur.po:edit pur.po:delete pur.receptions:view pur.receptions:create
    pur.receptions:edit pur.receptions:delete sales.customers:view sales.customers:create sales.customers:edit
    sales.customers:delete sales.priceLists:view sales.priceLists:create sales.priceLists:edit
    sales.priceLists:delete sales.invoices:view sales.invoices:create sales.invoices:edit sales.invoices:delete
    sales.invoices:post sales.invoices:credit sales.invoices:print inv.items:view inv.items:create inv.items:edit
    inv.items:delete inv.stock:view inv.movements:view inv.movements:create inv.movements:edit
    inv.movements:delete inv.replenishment:view inv.replenishment:create_po inv.count:view inv.count:create
    inv.count:edit inv.count:delete inv.count:post inv.valuation:view inv.warehouses:view inv.warehouses:create
    inv.warehouses:edit inv.warehouses:delete inv.params:view inv.params:create inv.params:edit inv.params:delete
    inv.setup:view inv.setup:create inv.setup:edit inv.setup:delete prod.recipes:view prod.recipes:create
    prod.recipes:edit prod.recipes:delete prod.items:view prod.items:create prod.items:edit prod.items:delete
    prod.operations:view prod.operations:create prod.operations:edit prod.operations:delete prod.resources:view
    prod.resources:create prod.resources:edit prod.resources:delete prod.workcenters:view prod.workcenters:create
    prod.workcenters:edit prod.workcenters:delete prod.setupmatrix:view prod.setupmatrix:create
    prod.setupmatrix:edit prod.setupmatrix:delete prod.calendars:view prod.calendars:create prod.calendars:edit
    prod.calendars:delete prod.setup:view prod.setup:create prod.setup:edit prod.setup:delete admin.taxes:view
    admin.taxes:create admin.taxes:edit admin.taxes:delete
""".split()


def upgrade():
    op.create_table('roles',
    sa.Column('code', sa.String(length=30), nullable=False),
    sa.Column('desc_fr', sa.Text(), server_default='', nullable=False),
    sa.Column('desc_en', sa.Text(), server_default='', nullable=False),
    sa.Column('is_admin', sa.Boolean(), server_default='false', nullable=False),
    sa.Column('active', sa.Boolean(), server_default='true', nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('code')
    )
    op.create_table('role_permissions',
    sa.Column('role_code', sa.String(length=30), nullable=False),
    sa.Column('permission', sa.String(length=80), nullable=False),
    sa.ForeignKeyConstraint(['role_code'], ['roles.code'], onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('role_code', 'permission')
    )
    op.create_table('role_history',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('role_code', sa.String(length=30), nullable=False),
    sa.Column('username', sa.String(length=80), server_default='', nullable=False),
    sa.Column('change', sa.String(length=20), nullable=False),
    sa.Column('details', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_role_history_role', 'role_history', ['role_code', 'at'], unique=False)

    bind = op.get_bind()
    bind.execute(sa.text(
        "INSERT INTO roles (code, desc_fr, desc_en, is_admin) VALUES "
        "('ADMIN', 'Administrateur', 'Administrator', true), ('USER', 'Utilisateur', 'User', false)"
    ))
    bind.execute(
        sa.text("INSERT INTO role_permissions (role_code, permission) VALUES ('USER', :p)"),
        [{"p": p} for p in USER_PERMISSIONS],
    )
    bind.execute(sa.text(
        "INSERT INTO role_history (role_code, username, change, details) VALUES "
        "('ADMIN', 'system', 'created', '{\"note\": \"migration 0023\"}'), "
        "('USER', 'system', 'created', '{\"note\": \"migration 0023: access of a plain user before roles\"}')"
    ))

    op.drop_constraint('ck_users_role', 'users', type_='check')
    op.alter_column('users', 'role', type_=sa.String(length=30), server_default='USER')
    bind.execute(sa.text("UPDATE users SET role = CASE WHEN role = 'admin' THEN 'ADMIN' ELSE 'USER' END"))
    op.create_foreign_key('fk_users_role', 'users', 'roles', ['role'], ['code'], onupdate='CASCADE')


def downgrade():
    op.drop_constraint('fk_users_role', 'users', type_='foreignkey')
    bind = op.get_bind()
    bind.execute(sa.text(
        "UPDATE users SET role = CASE WHEN role IN (SELECT code FROM roles WHERE is_admin) THEN 'admin' ELSE 'user' END"
    ))
    op.alter_column('users', 'role', type_=sa.String(length=20), server_default='user')
    op.create_check_constraint('ck_users_role', 'users', "role IN ('admin', 'user')")
    op.drop_index('ix_role_history_role', table_name='role_history')
    op.drop_table('role_history')
    op.drop_table('role_permissions')
    op.drop_table('roles')
