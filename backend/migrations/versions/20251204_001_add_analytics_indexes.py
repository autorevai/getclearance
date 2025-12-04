"""Add indexes for analytics queries

This migration adds indexes to speed up analytics queries that filter
by tenant_id, status, and date columns.

Revision ID: 20251204_001
Revises: 20251202_013
Create Date: 2025-12-04

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251204_001'
down_revision = '20251202_013_add_batch_jobs'
branch_labels = None
depends_on = None


def upgrade():
    # Indexes for applicants table - used in analytics queries
    # These are partial indexes that only include relevant statuses

    # Index for counting approved/rejected by reviewed_at date
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_applicants_tenant_reviewed_status
        ON applicants (tenant_id, reviewed_at, status)
        WHERE status IN ('approved', 'rejected')
    """)

    # Index for counting by created_at date (funnel queries)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_applicants_tenant_created
        ON applicants (tenant_id, created_at)
    """)

    # Index for risk score queries
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_applicants_tenant_risk_created
        ON applicants (tenant_id, created_at, risk_score)
        WHERE risk_score IS NOT NULL
    """)

    # Index for geographic distribution
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_applicants_tenant_country_created
        ON applicants (tenant_id, country_of_residence, created_at)
        WHERE country_of_residence IS NOT NULL
    """)

    # Index for SLA queries
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_applicants_tenant_sla_status
        ON applicants (tenant_id, sla_due_at, status)
        WHERE sla_due_at IS NOT NULL
    """)

    # Indexes for screening_checks table
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_screening_checks_tenant_created_status
        ON screening_checks (tenant_id, created_at, status)
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_screening_checks_tenant_applicant_completed
        ON screening_checks (tenant_id, applicant_id, completed_at)
    """)

    # Indexes for documents table (funnel query)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_documents_tenant_applicant_uploaded
        ON documents (tenant_id, applicant_id, uploaded_at)
    """)


def downgrade():
    # Drop all the indexes we created
    op.execute("DROP INDEX IF EXISTS ix_applicants_tenant_reviewed_status")
    op.execute("DROP INDEX IF EXISTS ix_applicants_tenant_created")
    op.execute("DROP INDEX IF EXISTS ix_applicants_tenant_risk_created")
    op.execute("DROP INDEX IF EXISTS ix_applicants_tenant_country_created")
    op.execute("DROP INDEX IF EXISTS ix_applicants_tenant_sla_status")
    op.execute("DROP INDEX IF EXISTS ix_screening_checks_tenant_created_status")
    op.execute("DROP INDEX IF EXISTS ix_screening_checks_tenant_applicant_completed")
    op.execute("DROP INDEX IF EXISTS ix_documents_tenant_applicant_uploaded")
