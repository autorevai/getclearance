"""Add GDPR compliance fields to applicants table

Revision ID: 009
Revises: 008
Create Date: 2025-12-02

This migration adds GDPR compliance fields:
- Legal hold support (blocks deletion per GDPR Article 17(3))
- Consent tracking (GDPR Articles 6 & 7)
- Data retention tracking
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = '009'
down_revision = '008'
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
    # ADD GDPR COMPLIANCE FIELDS TO applicants
    # ============================================

    # Legal hold fields
    if not column_exists('applicants', 'legal_hold'):
        op.add_column(
            'applicants',
            sa.Column('legal_hold', sa.Boolean(), server_default='false', nullable=False)
        )
    if not column_exists('applicants', 'legal_hold_reason'):
        op.add_column(
            'applicants',
            sa.Column('legal_hold_reason', sa.String(500), nullable=True)
        )
    if not column_exists('applicants', 'legal_hold_set_by'):
        op.add_column(
            'applicants',
            sa.Column(
                'legal_hold_set_by',
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey('users.id', ondelete='SET NULL'),
                nullable=True
            )
        )
    if not column_exists('applicants', 'legal_hold_set_at'):
        op.add_column(
            'applicants',
            sa.Column('legal_hold_set_at', sa.DateTime(timezone=True), nullable=True)
        )

    # Consent tracking fields (GDPR Article 6/7)
    if not column_exists('applicants', 'consent_given'):
        op.add_column(
            'applicants',
            sa.Column('consent_given', sa.Boolean(), server_default='false', nullable=False)
        )
    if not column_exists('applicants', 'consent_given_at'):
        op.add_column(
            'applicants',
            sa.Column('consent_given_at', sa.DateTime(timezone=True), nullable=True)
        )
    if not column_exists('applicants', 'consent_ip_address'):
        op.add_column(
            'applicants',
            sa.Column('consent_ip_address', sa.String(45), nullable=True)
        )
    if not column_exists('applicants', 'consent_withdrawn_at'):
        op.add_column(
            'applicants',
            sa.Column('consent_withdrawn_at', sa.DateTime(timezone=True), nullable=True)
        )

    # Data retention tracking
    if not column_exists('applicants', 'retention_expires_at'):
        op.add_column(
            'applicants',
            sa.Column('retention_expires_at', sa.DateTime(timezone=True), nullable=True)
        )

    # ============================================
    # CREATE INDEXES
    # ============================================

    # Index for finding applicants under legal hold
    if not index_exists('applicants', 'idx_applicants_legal_hold'):
        op.create_index(
            'idx_applicants_legal_hold',
            'applicants',
            ['tenant_id', 'legal_hold'],
            postgresql_where=sa.text("legal_hold = true")
        )

    # Index for retention expiry lookups
    if not index_exists('applicants', 'idx_applicants_retention_expires'):
        op.create_index(
            'idx_applicants_retention_expires',
            'applicants',
            ['tenant_id', 'retention_expires_at'],
            postgresql_where=sa.text("retention_expires_at IS NOT NULL")
        )


def downgrade() -> None:
    # Drop indexes
    if index_exists('applicants', 'idx_applicants_retention_expires'):
        op.drop_index('idx_applicants_retention_expires', table_name='applicants')
    if index_exists('applicants', 'idx_applicants_legal_hold'):
        op.drop_index('idx_applicants_legal_hold', table_name='applicants')

    # Drop retention tracking
    if column_exists('applicants', 'retention_expires_at'):
        op.drop_column('applicants', 'retention_expires_at')

    # Drop consent fields
    if column_exists('applicants', 'consent_withdrawn_at'):
        op.drop_column('applicants', 'consent_withdrawn_at')
    if column_exists('applicants', 'consent_ip_address'):
        op.drop_column('applicants', 'consent_ip_address')
    if column_exists('applicants', 'consent_given_at'):
        op.drop_column('applicants', 'consent_given_at')
    if column_exists('applicants', 'consent_given'):
        op.drop_column('applicants', 'consent_given')

    # Drop legal hold fields
    if column_exists('applicants', 'legal_hold_set_at'):
        op.drop_column('applicants', 'legal_hold_set_at')
    if column_exists('applicants', 'legal_hold_set_by'):
        op.drop_column('applicants', 'legal_hold_set_by')
    if column_exists('applicants', 'legal_hold_reason'):
        op.drop_column('applicants', 'legal_hold_reason')
    if column_exists('applicants', 'legal_hold'):
        op.drop_column('applicants', 'legal_hold')
