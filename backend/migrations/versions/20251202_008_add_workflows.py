"""Add workflow_rules and risk_assessment_logs tables

Revision ID: 006
Revises: 005
Create Date: 2025-12-02

This migration adds:
1. workflow_rules table - Configurable rules for applicant routing
2. risk_assessment_logs table - History of risk assessments
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '011'
down_revision = '010'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ============================================
    # CREATE workflow_rules TABLE
    # ============================================
    op.create_table(
        'workflow_rules',
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

        # Rule identification
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text),

        # Conditions (JSONB)
        sa.Column(
            'conditions',
            postgresql.JSONB,
            server_default='{}',
            nullable=False
        ),

        # Action
        sa.Column('action', sa.String(50), nullable=False),
        # Values: 'auto_approve', 'manual_review', 'auto_reject', 'escalate', 'hold'

        # Assignment
        sa.Column(
            'assign_to_user_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('users.id', ondelete='SET NULL')
        ),
        sa.Column('assign_to_role', sa.String(100)),

        # Notifications
        sa.Column('notify_on_match', sa.Boolean, server_default='false', nullable=False),
        sa.Column(
            'notification_channels',
            postgresql.JSONB,
            server_default='[]',
            nullable=False
        ),

        # Priority (higher = evaluated first)
        sa.Column('priority', sa.Integer, server_default='0', nullable=False),

        # Status
        sa.Column('is_active', sa.Boolean, server_default='true', nullable=False),

        # Metadata
        sa.Column(
            'created_by',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('users.id', ondelete='SET NULL')
        ),
        sa.Column(
            'last_modified_by',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('users.id', ondelete='SET NULL')
        ),

        # Statistics
        sa.Column('times_matched', sa.Integer, server_default='0', nullable=False),
        sa.Column('last_matched_at', sa.DateTime(timezone=True)),

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

    # Indexes for workflow_rules
    op.create_index(
        'idx_workflow_rules_tenant',
        'workflow_rules',
        ['tenant_id']
    )
    op.create_index(
        'idx_workflow_rules_tenant_active',
        'workflow_rules',
        ['tenant_id', 'is_active']
    )
    op.create_index(
        'idx_workflow_rules_priority',
        'workflow_rules',
        ['tenant_id', 'priority']
    )

    # ============================================
    # CREATE risk_assessment_logs TABLE
    # ============================================
    op.create_table(
        'risk_assessment_logs',
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
        sa.Column(
            'applicant_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('applicants.id', ondelete='CASCADE'),
            nullable=False
        ),

        # Assessment results
        sa.Column('overall_level', sa.String(20), nullable=False),
        # Values: 'low', 'medium', 'high', 'critical'
        sa.Column('overall_score', sa.Integer, nullable=False),
        # Score: 0-100

        # Signals (JSONB array)
        sa.Column(
            'signals',
            postgresql.JSONB,
            server_default='[]',
            nullable=False
        ),

        # Recommendation and final action
        sa.Column('recommended_action', sa.String(50), nullable=False),
        sa.Column(
            'applied_rule_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('workflow_rules.id', ondelete='SET NULL')
        ),
        sa.Column('final_action', sa.String(50)),

        # Timestamp
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False
        ),
    )

    # Indexes for risk_assessment_logs
    op.create_index(
        'idx_risk_logs_applicant',
        'risk_assessment_logs',
        ['applicant_id']
    )
    op.create_index(
        'idx_risk_logs_tenant_date',
        'risk_assessment_logs',
        ['tenant_id', 'created_at']
    )


def downgrade() -> None:
    # Drop risk_assessment_logs
    op.drop_index('idx_risk_logs_tenant_date', table_name='risk_assessment_logs')
    op.drop_index('idx_risk_logs_applicant', table_name='risk_assessment_logs')
    op.drop_table('risk_assessment_logs')

    # Drop workflow_rules
    op.drop_index('idx_workflow_rules_priority', table_name='workflow_rules')
    op.drop_index('idx_workflow_rules_tenant_active', table_name='workflow_rules')
    op.drop_index('idx_workflow_rules_tenant', table_name='workflow_rules')
    op.drop_table('workflow_rules')
