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
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = '011'
down_revision = '010'
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
    # CREATE workflow_rules TABLE
    # ============================================
    if not table_exists('workflow_rules'):
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

    # Indexes for workflow_rules (only if columns exist)
    if column_exists('workflow_rules', 'tenant_id'):
        if not index_exists('workflow_rules', 'idx_workflow_rules_tenant'):
            op.create_index(
                'idx_workflow_rules_tenant',
                'workflow_rules',
                ['tenant_id']
            )
        if column_exists('workflow_rules', 'is_active'):
            if not index_exists('workflow_rules', 'idx_workflow_rules_tenant_active'):
                op.create_index(
                    'idx_workflow_rules_tenant_active',
                    'workflow_rules',
                    ['tenant_id', 'is_active']
                )
        if column_exists('workflow_rules', 'priority'):
            if not index_exists('workflow_rules', 'idx_workflow_rules_priority'):
                op.create_index(
                    'idx_workflow_rules_priority',
                    'workflow_rules',
                    ['tenant_id', 'priority']
                )

    # ============================================
    # CREATE risk_assessment_logs TABLE
    # ============================================
    if table_exists('risk_assessment_logs'):
        if not column_exists('risk_assessment_logs', 'applicant_id'):
            # Table exists but is malformed - drop and recreate
            op.drop_table('risk_assessment_logs')
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
                sa.Column('overall_level', sa.String(20), nullable=False),
                sa.Column('overall_score', sa.Integer, nullable=False),
                sa.Column(
                    'signals',
                    postgresql.JSONB,
                    server_default='[]',
                    nullable=False
                ),
                sa.Column('recommended_action', sa.String(50), nullable=False),
                sa.Column(
                    'applied_rule_id',
                    postgresql.UUID(as_uuid=True),
                    sa.ForeignKey('workflow_rules.id', ondelete='SET NULL')
                ),
                sa.Column('final_action', sa.String(50)),
                sa.Column(
                    'created_at',
                    sa.DateTime(timezone=True),
                    server_default=sa.text('now()'),
                    nullable=False
                ),
            )
    else:
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
            sa.Column('overall_level', sa.String(20), nullable=False),
            sa.Column('overall_score', sa.Integer, nullable=False),
            sa.Column(
                'signals',
                postgresql.JSONB,
                server_default='[]',
                nullable=False
            ),
            sa.Column('recommended_action', sa.String(50), nullable=False),
            sa.Column(
                'applied_rule_id',
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey('workflow_rules.id', ondelete='SET NULL')
            ),
            sa.Column('final_action', sa.String(50)),
            sa.Column(
                'created_at',
                sa.DateTime(timezone=True),
                server_default=sa.text('now()'),
                nullable=False
            ),
        )

    # Indexes for risk_assessment_logs (only if columns exist)
    if column_exists('risk_assessment_logs', 'applicant_id'):
        if not index_exists('risk_assessment_logs', 'idx_risk_logs_applicant'):
            op.create_index(
                'idx_risk_logs_applicant',
                'risk_assessment_logs',
                ['applicant_id']
            )
    if column_exists('risk_assessment_logs', 'tenant_id') and column_exists('risk_assessment_logs', 'created_at'):
        if not index_exists('risk_assessment_logs', 'idx_risk_logs_tenant_date'):
            op.create_index(
                'idx_risk_logs_tenant_date',
                'risk_assessment_logs',
                ['tenant_id', 'created_at']
            )


def downgrade() -> None:
    # Drop risk_assessment_logs
    if table_exists('risk_assessment_logs'):
        if index_exists('risk_assessment_logs', 'idx_risk_logs_tenant_date'):
            op.drop_index('idx_risk_logs_tenant_date', table_name='risk_assessment_logs')
        if index_exists('risk_assessment_logs', 'idx_risk_logs_applicant'):
            op.drop_index('idx_risk_logs_applicant', table_name='risk_assessment_logs')
        op.drop_table('risk_assessment_logs')

    # Drop workflow_rules
    if table_exists('workflow_rules'):
        if index_exists('workflow_rules', 'idx_workflow_rules_priority'):
            op.drop_index('idx_workflow_rules_priority', table_name='workflow_rules')
        if index_exists('workflow_rules', 'idx_workflow_rules_tenant_active'):
            op.drop_index('idx_workflow_rules_tenant_active', table_name='workflow_rules')
        if index_exists('workflow_rules', 'idx_workflow_rules_tenant'):
            op.drop_index('idx_workflow_rules_tenant', table_name='workflow_rules')
        op.drop_table('workflow_rules')
