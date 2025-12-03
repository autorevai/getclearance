"""Add companies, beneficial_owners, company_documents tables for KYB

Revision ID: 006
Revises: 005
Create Date: 2025-12-02

This migration adds:
1. companies table - Business entities for KYB verification
2. beneficial_owners table - Ultimate beneficial owners (UBOs)
3. company_documents table - Corporate documents

Also adds company_id foreign key to screening_checks table.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def table_exists(table_name):
    """Check if a table exists in the database."""
    bind = op.get_bind()
    inspector = inspect(bind)
    return table_name in inspector.get_table_names()


def column_exists(table_name, column_name):
    """Check if a column exists in a table."""
    bind = op.get_bind()
    inspector = inspect(bind)
    if not table_exists(table_name):
        return False
    columns = [c['name'] for c in inspector.get_columns(table_name)]
    return column_name in columns


def index_exists(table_name, index_name):
    """Check if an index exists on a table."""
    bind = op.get_bind()
    inspector = inspect(bind)
    if not table_exists(table_name):
        return False
    indexes = [idx['name'] for idx in inspector.get_indexes(table_name)]
    return index_name in indexes


def upgrade() -> None:
    # ============================================
    # CREATE companies TABLE
    # ============================================
    if not table_exists('companies'):
        op.create_table(
            'companies',
            sa.Column(
                'id',
                postgresql.UUID(as_uuid=True),
                primary_key=True,
                server_default=sa.text('gen_random_uuid()')
            ),
            sa.Column(
                'tenant_id',
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey('tenants.id', ondelete='CASCADE'),
                nullable=False
            ),
            sa.Column('external_id', sa.String(255)),
            sa.Column('legal_name', sa.String(500), nullable=False),
            sa.Column('trading_name', sa.String(500)),
            sa.Column('registration_number', sa.String(100)),
            sa.Column('tax_id', sa.String(100)),
            sa.Column('incorporation_date', sa.Date),
            sa.Column('incorporation_country', sa.String(2)),
            sa.Column('legal_form', sa.String(100)),
            sa.Column('registered_address', postgresql.JSONB),
            sa.Column('business_address', postgresql.JSONB),
            sa.Column('website', sa.String(500)),
            sa.Column('email', sa.String(255)),
            sa.Column('phone', sa.String(50)),
            sa.Column('industry', sa.String(255)),
            sa.Column('description', sa.Text),
            sa.Column('employee_count', sa.String(50)),
            sa.Column('annual_revenue', sa.String(50)),
            sa.Column('status', sa.String(50), server_default='pending', nullable=False),
            sa.Column('risk_level', sa.String(20)),
            sa.Column('risk_score', sa.Integer),
            sa.Column('screening_status', sa.String(50)),
            sa.Column('last_screened_at', sa.DateTime(timezone=True)),
            sa.Column('flags', postgresql.ARRAY(sa.String(50)), server_default='{}'),
            sa.Column('reviewed_at', sa.DateTime(timezone=True)),
            sa.Column(
                'reviewed_by',
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey('users.id', ondelete='SET NULL')
            ),
            sa.Column('review_notes', sa.Text),
            sa.Column('source', sa.String(50)),
            sa.Column('extra_data', postgresql.JSONB),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        )

    # Indexes for companies
    if not index_exists('companies', 'idx_companies_tenant'):
        op.create_index('idx_companies_tenant', 'companies', ['tenant_id'])
    if not index_exists('companies', 'idx_companies_tenant_external'):
        op.create_index('idx_companies_tenant_external', 'companies', ['tenant_id', 'external_id'], unique=True)
    if not index_exists('companies', 'idx_companies_tenant_status'):
        op.create_index('idx_companies_tenant_status', 'companies', ['tenant_id', 'status'])
    if not index_exists('companies', 'idx_companies_registration'):
        op.create_index('idx_companies_registration', 'companies', ['tenant_id', 'registration_number'])
    if not index_exists('companies', 'idx_companies_tax_id'):
        op.create_index('idx_companies_tax_id', 'companies', ['tenant_id', 'tax_id'])

    # ============================================
    # CREATE beneficial_owners TABLE
    # ============================================
    if not table_exists('beneficial_owners'):
        op.create_table(
            'beneficial_owners',
            sa.Column(
                'id',
                postgresql.UUID(as_uuid=True),
                primary_key=True,
                server_default=sa.text('gen_random_uuid()')
            ),
            sa.Column(
                'company_id',
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey('companies.id', ondelete='CASCADE'),
                nullable=False
            ),
            sa.Column(
                'applicant_id',
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey('applicants.id', ondelete='SET NULL')
            ),
            sa.Column('full_name', sa.String(500), nullable=False),
            sa.Column('date_of_birth', sa.Date),
            sa.Column('nationality', sa.String(2)),
            sa.Column('country_of_residence', sa.String(2)),
            sa.Column('id_type', sa.String(50)),
            sa.Column('id_number', sa.String(100)),
            sa.Column('id_country', sa.String(2)),
            sa.Column('ownership_percentage', sa.Float),
            sa.Column('ownership_type', sa.String(50), server_default='direct', nullable=False),
            sa.Column('voting_rights_percentage', sa.Float),
            sa.Column('is_director', sa.Boolean, server_default='false', nullable=False),
            sa.Column('is_shareholder', sa.Boolean, server_default='false', nullable=False),
            sa.Column('is_signatory', sa.Boolean, server_default='false', nullable=False),
            sa.Column('is_legal_representative', sa.Boolean, server_default='false', nullable=False),
            sa.Column('role_title', sa.String(255)),
            sa.Column('verification_status', sa.String(50), server_default='pending', nullable=False),
            sa.Column('verified_at', sa.DateTime(timezone=True)),
            sa.Column('screening_status', sa.String(50)),
            sa.Column('last_screened_at', sa.DateTime(timezone=True)),
            sa.Column('flags', postgresql.ARRAY(sa.String(50)), server_default='{}'),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.CheckConstraint(
                'ownership_percentage >= 0 AND ownership_percentage <= 100',
                name='ck_ownership_percentage_range'
            ),
        )

    # Indexes for beneficial_owners
    if not index_exists('beneficial_owners', 'idx_ubos_company'):
        op.create_index('idx_ubos_company', 'beneficial_owners', ['company_id'])
    if not index_exists('beneficial_owners', 'idx_ubos_applicant'):
        op.create_index('idx_ubos_applicant', 'beneficial_owners', ['applicant_id'])

    # ============================================
    # CREATE company_documents TABLE
    # ============================================
    if not table_exists('company_documents'):
        op.create_table(
            'company_documents',
            sa.Column(
                'id',
                postgresql.UUID(as_uuid=True),
                primary_key=True,
                server_default=sa.text('gen_random_uuid()')
            ),
            sa.Column(
                'company_id',
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey('companies.id', ondelete='CASCADE'),
                nullable=False
            ),
            sa.Column('document_type', sa.String(100), nullable=False),
            sa.Column('document_subtype', sa.String(100)),
            sa.Column('file_name', sa.String(500), nullable=False),
            sa.Column('file_type', sa.String(100)),
            sa.Column('file_size', sa.Integer),
            sa.Column('storage_key', sa.String(1000), nullable=False),
            sa.Column('issue_date', sa.Date),
            sa.Column('expiry_date', sa.Date),
            sa.Column('issuing_authority', sa.String(255)),
            sa.Column('document_number', sa.String(100)),
            sa.Column('status', sa.String(50), server_default='pending', nullable=False),
            sa.Column('verification_notes', sa.Text),
            sa.Column('verified_at', sa.DateTime(timezone=True)),
            sa.Column(
                'verified_by',
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey('users.id', ondelete='SET NULL')
            ),
            sa.Column('extracted_data', postgresql.JSONB),
            sa.Column('confidence_score', sa.Float),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        )

    # Indexes for company_documents
    if not index_exists('company_documents', 'idx_company_docs_company'):
        op.create_index('idx_company_docs_company', 'company_documents', ['company_id'])
    if not index_exists('company_documents', 'idx_company_docs_type'):
        op.create_index('idx_company_docs_type', 'company_documents', ['company_id', 'document_type'])

    # ============================================
    # ADD company_id to screening_checks
    # ============================================
    if not column_exists('screening_checks', 'company_id'):
        op.add_column(
            'screening_checks',
            sa.Column(
                'company_id',
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey('companies.id', ondelete='CASCADE'),
                nullable=True
            )
        )
    if not index_exists('screening_checks', 'idx_screening_checks_company'):
        op.create_index('idx_screening_checks_company', 'screening_checks', ['company_id'])


def downgrade() -> None:
    # Drop company_id from screening_checks
    if index_exists('screening_checks', 'idx_screening_checks_company'):
        op.drop_index('idx_screening_checks_company', table_name='screening_checks')
    if column_exists('screening_checks', 'company_id'):
        op.drop_column('screening_checks', 'company_id')

    # Drop company_documents
    if table_exists('company_documents'):
        op.drop_index('idx_company_docs_type', table_name='company_documents')
        op.drop_index('idx_company_docs_company', table_name='company_documents')
        op.drop_table('company_documents')

    # Drop beneficial_owners
    if table_exists('beneficial_owners'):
        op.drop_index('idx_ubos_applicant', table_name='beneficial_owners')
        op.drop_index('idx_ubos_company', table_name='beneficial_owners')
        op.drop_table('beneficial_owners')

    # Drop companies
    if table_exists('companies'):
        op.drop_index('idx_companies_tax_id', table_name='companies')
        op.drop_index('idx_companies_registration', table_name='companies')
        op.drop_index('idx_companies_tenant_status', table_name='companies')
        op.drop_index('idx_companies_tenant_external', table_name='companies')
        op.drop_index('idx_companies_tenant', table_name='companies')
        op.drop_table('companies')
