"""Add monitoring_alerts table for ongoing AML monitoring

Revision ID: 004
Revises: 003
Create Date: 2025-12-02

This migration adds:
1. monitoring_alerts table for tracking alerts from ongoing monitoring
   - Generated when re-screening finds new hits
   - Tracks severity, status, and resolution workflow
   - Links to previous and new screening checks
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ============================================
    # CREATE monitoring_alerts TABLE
    # ============================================
    # Stores alerts generated during ongoing AML monitoring
    # when new hits are found for approved applicants

    op.create_table(
        'monitoring_alerts',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text('gen_random_uuid()')
        ),

        # Ownership
        sa.Column(
            'tenant_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('tenants.id', ondelete='CASCADE'),
            nullable=False
        ),
        sa.Column(
            'applicant_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('applicants.id', ondelete='CASCADE'),
            nullable=False
        ),

        # Alert classification
        sa.Column('alert_type', sa.String(50), nullable=False),
        # Types: 'new_hit', 'upgraded_risk', 'list_update', 'reactivation'
        sa.Column('severity', sa.String(20), server_default='medium', nullable=False),
        # Severity: 'critical', 'high', 'medium', 'low'

        # Screening references
        sa.Column(
            'previous_screening_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('screening_checks.id', ondelete='SET NULL'),
            nullable=True
        ),
        sa.Column(
            'new_screening_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('screening_checks.id', ondelete='CASCADE'),
            nullable=False
        ),

        # New hits details (JSONB array)
        sa.Column(
            'new_hits',
            postgresql.JSONB,
            server_default='[]',
            nullable=False
        ),
        # Format: [{"hit_id": "uuid", "matched_name": "...", "hit_type": "...", "confidence": 85.5}]

        # Summary for quick display
        sa.Column('hit_count', sa.Integer, server_default='0', nullable=False),
        sa.Column(
            'hit_types',
            postgresql.JSONB,
            server_default='[]',
            nullable=False
        ),
        # e.g., ["sanctions", "pep"]

        # Resolution workflow
        sa.Column('status', sa.String(50), server_default='open', nullable=False),
        # Status: 'open', 'reviewing', 'resolved', 'dismissed', 'escalated'

        sa.Column(
            'resolved_by',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('users.id', ondelete='SET NULL'),
            nullable=True
        ),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolution_notes', sa.Text, nullable=True),
        sa.Column('resolution_action', sa.String(50), nullable=True),
        # Actions: 'confirmed_match', 'false_positive', 'requires_review', 'no_action'

        # Escalation
        sa.Column(
            'escalated_to',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('users.id', ondelete='SET NULL'),
            nullable=True
        ),
        sa.Column('escalated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('escalation_reason', sa.Text, nullable=True),

        # Timestamps
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False
        ),
    )

    # Create indexes for monitoring_alerts
    op.create_index(
        'idx_monitoring_alerts_tenant_status',
        'monitoring_alerts',
        ['tenant_id', 'status']
    )
    op.create_index(
        'idx_monitoring_alerts_applicant',
        'monitoring_alerts',
        ['applicant_id']
    )
    op.create_index(
        'idx_monitoring_alerts_severity',
        'monitoring_alerts',
        ['tenant_id', 'severity']
    )
    # Partial index for open alerts (most common query)
    op.create_index(
        'idx_monitoring_alerts_open',
        'monitoring_alerts',
        ['tenant_id', 'created_at'],
        postgresql_where=sa.text("status IN ('open', 'reviewing')")
    )


def downgrade() -> None:
    # Drop indexes first
    op.drop_index('idx_monitoring_alerts_open', table_name='monitoring_alerts')
    op.drop_index('idx_monitoring_alerts_severity', table_name='monitoring_alerts')
    op.drop_index('idx_monitoring_alerts_applicant', table_name='monitoring_alerts')
    op.drop_index('idx_monitoring_alerts_tenant_status', table_name='monitoring_alerts')

    # Drop table
    op.drop_table('monitoring_alerts')
