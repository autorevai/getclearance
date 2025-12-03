"""Add batch_jobs table for tracking background processing

Revision ID: 008
Revises: 007
Create Date: 2025-12-02

This migration adds the batch_jobs table for tracking:
- Batch AI risk analysis jobs
- Bulk applicant operations
- Data import/export jobs
- Report generation
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '008'
down_revision = '007'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ============================================
    # CREATE batch_jobs TABLE
    # ============================================
    op.create_table(
        'batch_jobs',
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

        # Job identification
        sa.Column('job_type', sa.String(50), nullable=False),
        # Types: risk_analysis, bulk_screening, data_export, report_generation

        # Status tracking
        sa.Column('status', sa.String(20), server_default='pending', nullable=False),
        # Status: pending, processing, completed, failed, cancelled

        # Progress tracking
        sa.Column('progress', sa.Integer, server_default='0', nullable=False),
        sa.Column('total_items', sa.Integer, server_default='0', nullable=False),
        sa.Column('processed_items', sa.Integer, server_default='0', nullable=False),
        sa.Column('failed_items', sa.Integer, server_default='0', nullable=False),

        # Input/output data
        sa.Column('input_data', postgresql.JSONB),
        sa.Column('results', postgresql.JSONB, server_default='[]'),
        sa.Column('errors', postgresql.JSONB, server_default='[]'),

        # Timing
        sa.Column('started_at', sa.DateTime(timezone=True)),
        sa.Column('completed_at', sa.DateTime(timezone=True)),

        # Who initiated the job
        sa.Column(
            'created_by',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('users.id', ondelete='SET NULL')
        ),

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

    # Indexes for batch_jobs
    op.create_index(
        'idx_batch_jobs_tenant',
        'batch_jobs',
        ['tenant_id']
    )
    op.create_index(
        'idx_batch_jobs_tenant_status',
        'batch_jobs',
        ['tenant_id', 'status']
    )
    op.create_index(
        'idx_batch_jobs_tenant_type',
        'batch_jobs',
        ['tenant_id', 'job_type']
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_batch_jobs_tenant_type', table_name='batch_jobs')
    op.drop_index('idx_batch_jobs_tenant_status', table_name='batch_jobs')
    op.drop_index('idx_batch_jobs_tenant', table_name='batch_jobs')

    # Drop table
    op.drop_table('batch_jobs')
