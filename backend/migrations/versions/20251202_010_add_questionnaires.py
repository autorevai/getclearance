"""Add questionnaires and questionnaire_responses tables

Revision ID: 007
Revises: 006
Create Date: 2025-12-02

This migration adds:
1. questionnaires table - Configurable questionnaire templates
2. questionnaire_responses table - Submitted answers with risk scoring
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = '013'
down_revision = '012'
branch_labels = None
depends_on = None


def table_exists(table_name):
    """Check if a table exists in the database."""
    bind = op.get_bind()
    inspector = inspect(bind)
    return table_name in inspector.get_table_names()


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
    # CREATE questionnaires TABLE
    # ============================================
    if not table_exists('questionnaires'):
        op.create_table(
            'questionnaires',
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

            # Identification
            sa.Column('name', sa.String(255), nullable=False),
            sa.Column('description', sa.Text),
            sa.Column('internal_notes', sa.Text),

            # Type/purpose
            sa.Column('questionnaire_type', sa.String(50), server_default='general', nullable=False),

            # Questions configuration (JSONB array)
            sa.Column(
                'questions',
                postgresql.JSONB,
                server_default='[]',
                nullable=False
            ),

            # Scoring
            sa.Column('max_risk_score', sa.Integer),

            # Status
            sa.Column('is_active', sa.Boolean, server_default='true', nullable=False),
            sa.Column('is_required', sa.Boolean, server_default='false', nullable=False),

            # Versioning
            sa.Column('version', sa.Integer, server_default='1', nullable=False),

            # Metadata
            sa.Column(
                'created_by',
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey('users.id', ondelete='SET NULL')
            ),

            # Statistics
            sa.Column('times_completed', sa.Integer, server_default='0', nullable=False),
            sa.Column('average_risk_score', sa.Integer),

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

    # Indexes for questionnaires
    if not index_exists('questionnaires', 'idx_questionnaires_tenant'):
        op.create_index(
            'idx_questionnaires_tenant',
            'questionnaires',
            ['tenant_id']
        )
    if not index_exists('questionnaires', 'idx_questionnaires_tenant_active'):
        op.create_index(
            'idx_questionnaires_tenant_active',
            'questionnaires',
            ['tenant_id', 'is_active']
        )
    if not index_exists('questionnaires', 'idx_questionnaires_type'):
        op.create_index(
            'idx_questionnaires_type',
            'questionnaires',
            ['tenant_id', 'questionnaire_type']
        )

    # ============================================
    # CREATE questionnaire_responses TABLE
    # ============================================
    if not table_exists('questionnaire_responses'):
        op.create_table(
            'questionnaire_responses',
            sa.Column(
                'id',
                postgresql.UUID(as_uuid=True),
                primary_key=True,
                server_default=sa.text('gen_random_uuid()')
            ),

            # Parent questionnaire
            sa.Column(
                'questionnaire_id',
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey('questionnaires.id', ondelete='CASCADE'),
                nullable=False
            ),

            # Link to applicant or company (one must be set)
            sa.Column(
                'applicant_id',
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey('applicants.id', ondelete='CASCADE')
            ),
            sa.Column(
                'company_id',
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey('companies.id', ondelete='CASCADE')
            ),

            # Submitted answers (JSONB)
            sa.Column(
                'answers',
                postgresql.JSONB,
                server_default='{}',
                nullable=False
            ),

            # Calculated risk score
            sa.Column('risk_score', sa.Integer),
            sa.Column('risk_breakdown', postgresql.JSONB),

            # Status
            sa.Column('status', sa.String(50), server_default='submitted', nullable=False),

            # Submission details
            sa.Column('submitted_at', sa.DateTime(timezone=True)),
            sa.Column(
                'submitted_by',
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey('users.id', ondelete='SET NULL')
            ),

            # Review
            sa.Column('reviewed_at', sa.DateTime(timezone=True)),
            sa.Column(
                'reviewed_by',
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey('users.id', ondelete='SET NULL')
            ),
            sa.Column('review_notes', sa.Text),

            # IP/device tracking for fraud prevention
            sa.Column('ip_address', sa.String(45)),
            sa.Column('user_agent', sa.Text),

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

    # Indexes for questionnaire_responses
    if not index_exists('questionnaire_responses', 'idx_questionnaire_responses_questionnaire'):
        op.create_index(
            'idx_questionnaire_responses_questionnaire',
            'questionnaire_responses',
            ['questionnaire_id']
        )
    if not index_exists('questionnaire_responses', 'idx_questionnaire_responses_applicant'):
        op.create_index(
            'idx_questionnaire_responses_applicant',
            'questionnaire_responses',
            ['applicant_id']
        )
    if not index_exists('questionnaire_responses', 'idx_questionnaire_responses_company'):
        op.create_index(
            'idx_questionnaire_responses_company',
            'questionnaire_responses',
            ['company_id']
        )


def downgrade() -> None:
    # Drop questionnaire_responses
    if table_exists('questionnaire_responses'):
        if index_exists('questionnaire_responses', 'idx_questionnaire_responses_company'):
            op.drop_index('idx_questionnaire_responses_company', table_name='questionnaire_responses')
        if index_exists('questionnaire_responses', 'idx_questionnaire_responses_applicant'):
            op.drop_index('idx_questionnaire_responses_applicant', table_name='questionnaire_responses')
        if index_exists('questionnaire_responses', 'idx_questionnaire_responses_questionnaire'):
            op.drop_index('idx_questionnaire_responses_questionnaire', table_name='questionnaire_responses')
        op.drop_table('questionnaire_responses')

    # Drop questionnaires
    if table_exists('questionnaires'):
        if index_exists('questionnaires', 'idx_questionnaires_type'):
            op.drop_index('idx_questionnaires_type', table_name='questionnaires')
        if index_exists('questionnaires', 'idx_questionnaires_tenant_active'):
            op.drop_index('idx_questionnaires_tenant_active', table_name='questionnaires')
        if index_exists('questionnaires', 'idx_questionnaires_tenant'):
            op.drop_index('idx_questionnaires_tenant', table_name='questionnaires')
        op.drop_table('questionnaires')
