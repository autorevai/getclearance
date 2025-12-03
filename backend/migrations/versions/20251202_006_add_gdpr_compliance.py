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


# revision identifiers, used by Alembic.
revision = '009'
down_revision = '008'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ============================================
    # ADD GDPR COMPLIANCE FIELDS TO applicants
    # ============================================

    # Legal hold fields
    op.add_column(
        'applicants',
        sa.Column('legal_hold', sa.Boolean(), server_default='false', nullable=False)
    )
    op.add_column(
        'applicants',
        sa.Column('legal_hold_reason', sa.String(500), nullable=True)
    )
    op.add_column(
        'applicants',
        sa.Column(
            'legal_hold_set_by',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('users.id', ondelete='SET NULL'),
            nullable=True
        )
    )
    op.add_column(
        'applicants',
        sa.Column('legal_hold_set_at', sa.DateTime(timezone=True), nullable=True)
    )

    # Consent tracking fields (GDPR Article 6/7)
    op.add_column(
        'applicants',
        sa.Column('consent_given', sa.Boolean(), server_default='false', nullable=False)
    )
    op.add_column(
        'applicants',
        sa.Column('consent_given_at', sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        'applicants',
        sa.Column('consent_ip_address', sa.String(45), nullable=True)
    )
    op.add_column(
        'applicants',
        sa.Column('consent_withdrawn_at', sa.DateTime(timezone=True), nullable=True)
    )

    # Data retention tracking
    op.add_column(
        'applicants',
        sa.Column('retention_expires_at', sa.DateTime(timezone=True), nullable=True)
    )

    # ============================================
    # CREATE INDEXES
    # ============================================

    # Index for finding applicants under legal hold
    op.create_index(
        'idx_applicants_legal_hold',
        'applicants',
        ['tenant_id', 'legal_hold'],
        postgresql_where=sa.text("legal_hold = true")
    )

    # Index for retention expiry lookups
    op.create_index(
        'idx_applicants_retention_expires',
        'applicants',
        ['tenant_id', 'retention_expires_at'],
        postgresql_where=sa.text("retention_expires_at IS NOT NULL")
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_applicants_retention_expires', table_name='applicants')
    op.drop_index('idx_applicants_legal_hold', table_name='applicants')

    # Drop retention tracking
    op.drop_column('applicants', 'retention_expires_at')

    # Drop consent fields
    op.drop_column('applicants', 'consent_withdrawn_at')
    op.drop_column('applicants', 'consent_ip_address')
    op.drop_column('applicants', 'consent_given_at')
    op.drop_column('applicants', 'consent_given')

    # Drop legal hold fields
    op.drop_column('applicants', 'legal_hold_set_at')
    op.drop_column('applicants', 'legal_hold_set_by')
    op.drop_column('applicants', 'legal_hold_reason')
    op.drop_column('applicants', 'legal_hold')
