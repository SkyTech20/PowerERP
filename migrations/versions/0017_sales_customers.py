"""Sales (V1): the company profile (header of the invoices) and the customers, with their ship-to addresses
and contacts.

Revision ID: 0017
Revises: 0016
Create Date: 2026-11-23
"""
from alembic import op
import sqlalchemy as sa


revision = '0017'
down_revision = '0016'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('company_profile',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('company_id', sa.BigInteger(), nullable=False),
    sa.Column('code', sa.Text(), server_default='', nullable=False),
    sa.Column('name', sa.Text(), server_default='', nullable=False),
    sa.Column('legal_name', sa.Text(), server_default='', nullable=False),
    sa.Column('address1', sa.Text(), server_default='', nullable=False),
    sa.Column('address2', sa.Text(), server_default='', nullable=False),
    sa.Column('city', sa.Text(), server_default='', nullable=False),
    sa.Column('province', sa.Text(), server_default='', nullable=False),
    sa.Column('zip_code', sa.Text(), server_default='', nullable=False),
    sa.Column('country', sa.Text(), server_default='', nullable=False),
    sa.Column('phone', sa.Text(), server_default='', nullable=False),
    sa.Column('email', sa.Text(), server_default='', nullable=False),
    sa.Column('website', sa.Text(), server_default='', nullable=False),
    sa.Column('neq', sa.Text(), server_default='', nullable=False),
    sa.Column('invoice_note_fr', sa.Text(), server_default='', nullable=False),
    sa.Column('invoice_note_en', sa.Text(), server_default='', nullable=False),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
    sa.PrimaryKeyConstraint('id'),
    comment='business key: lower(code)'
    )
    op.create_index(op.f('ix_company_profile_company_id'), 'company_profile', ['company_id'], unique=False)
    op.create_index('uq_company_profile_key', 'company_profile', [sa.text('company_id'), sa.text('lower(code)')], unique=True)
    op.create_table('customers',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('company_id', sa.BigInteger(), nullable=False),
    sa.Column('code', sa.Text(), server_default='', nullable=False),
    sa.Column('name', sa.Text(), server_default='', nullable=False),
    sa.Column('legal_name', sa.Text(), server_default='', nullable=False),
    sa.Column('lang', sa.String(length=30), server_default='fr', nullable=False),
    sa.Column('address1', sa.Text(), server_default='', nullable=False),
    sa.Column('address2', sa.Text(), server_default='', nullable=False),
    sa.Column('city', sa.Text(), server_default='', nullable=False),
    sa.Column('province', sa.Text(), server_default='', nullable=False),
    sa.Column('zip_code', sa.Text(), server_default='', nullable=False),
    sa.Column('country', sa.Text(), server_default='', nullable=False),
    sa.Column('phone', sa.Text(), server_default='', nullable=False),
    sa.Column('email', sa.Text(), server_default='', nullable=False),
    sa.Column('tax_group', sa.Text(), server_default='', nullable=False),
    sa.Column('tax_exempt_no', sa.Text(), server_default='', nullable=False),
    sa.Column('term_code', sa.Text(), server_default='', nullable=False),
    sa.Column('term_desc', sa.Text(), server_default='', nullable=False),
    sa.Column('discount_pct', sa.Numeric(), nullable=True),
    sa.Column('warehouse', sa.Text(), server_default='', nullable=False),
    sa.Column('notes', sa.Text(), server_default='', nullable=False),
    sa.Column('active', sa.Boolean(), server_default='false', nullable=False),
    sa.CheckConstraint("lang IN ('fr', 'en')", name='ck_customers_lang'),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
    sa.PrimaryKeyConstraint('id'),
    comment='business key: lower(code)'
    )
    op.create_index(op.f('ix_customers_company_id'), 'customers', ['company_id'], unique=False)
    op.create_index('uq_customers_key', 'customers', [sa.text('company_id'), sa.text('lower(code)')], unique=True)
    op.create_table('customers_addresses',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('parent_id', sa.BigInteger(), nullable=False),
    sa.Column('line_no', sa.Integer(), nullable=False),
    sa.Column('code', sa.Text(), server_default='', nullable=False),
    sa.Column('name', sa.Text(), server_default='', nullable=False),
    sa.Column('address1', sa.Text(), server_default='', nullable=False),
    sa.Column('address2', sa.Text(), server_default='', nullable=False),
    sa.Column('city', sa.Text(), server_default='', nullable=False),
    sa.Column('province', sa.Text(), server_default='', nullable=False),
    sa.Column('zip_code', sa.Text(), server_default='', nullable=False),
    sa.Column('country', sa.Text(), server_default='', nullable=False),
    sa.Column('contact', sa.Text(), server_default='', nullable=False),
    sa.Column('phone', sa.Text(), server_default='', nullable=False),
    sa.Column('tax_group', sa.Text(), server_default='', nullable=False),
    sa.Column('is_default', sa.Boolean(), server_default='false', nullable=False),
    sa.ForeignKeyConstraint(['parent_id'], ['customers.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_customers_addresses_parent_id'), 'customers_addresses', ['parent_id'], unique=False)
    op.create_table('customers_contacts',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('parent_id', sa.BigInteger(), nullable=False),
    sa.Column('line_no', sa.Integer(), nullable=False),
    sa.Column('name', sa.Text(), server_default='', nullable=False),
    sa.Column('title', sa.Text(), server_default='', nullable=False),
    sa.Column('phone', sa.Text(), server_default='', nullable=False),
    sa.Column('email', sa.Text(), server_default='', nullable=False),
    sa.Column('invoices', sa.Boolean(), server_default='false', nullable=False),
    sa.ForeignKeyConstraint(['parent_id'], ['customers.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_customers_contacts_parent_id'), 'customers_contacts', ['parent_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_customers_contacts_parent_id'), table_name='customers_contacts')
    op.drop_table('customers_contacts')
    op.drop_index(op.f('ix_customers_addresses_parent_id'), table_name='customers_addresses')
    op.drop_table('customers_addresses')
    op.drop_index('uq_customers_key', table_name='customers')
    op.drop_index(op.f('ix_customers_company_id'), table_name='customers')
    op.drop_table('customers')
    op.drop_index('uq_company_profile_key', table_name='company_profile')
    op.drop_index(op.f('ix_company_profile_company_id'), table_name='company_profile')
    op.drop_table('company_profile')
