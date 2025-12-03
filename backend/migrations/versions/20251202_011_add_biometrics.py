"""Add biometrics fields to documents table

Revision ID: 008
Revises: 007
Create Date: 2025-12-02

This migration adds biometric verification fields to the documents table:
- face_match_score: Similarity score between ID photo and selfie
- liveness_score: Confidence that the selfie is a live person
- biometrics_checked_at: Timestamp of biometric verification
- verification_result: Full verification result JSON
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '014'
down_revision = '013'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add biometrics columns to documents table
    op.add_column(
        'documents',
        sa.Column('face_match_score', sa.Numeric(5, 2), nullable=True,
                  comment='Face similarity score 0-100 when compared to selfie')
    )
    op.add_column(
        'documents',
        sa.Column('liveness_score', sa.Numeric(5, 2), nullable=True,
                  comment='Liveness detection confidence 0-100')
    )
    op.add_column(
        'documents',
        sa.Column('biometrics_checked_at', sa.DateTime(timezone=True), nullable=True,
                  comment='When biometric verification was performed')
    )
    op.add_column(
        'documents',
        sa.Column('verification_result', postgresql.JSONB, nullable=True,
                  comment='Full biometric verification result including quality metrics')
    )

    # Create index for documents with biometrics
    op.create_index(
        'idx_documents_biometrics',
        'documents',
        ['applicant_id', 'biometrics_checked_at'],
        postgresql_where=sa.text('biometrics_checked_at IS NOT NULL')
    )


def downgrade() -> None:
    # Drop index
    op.drop_index('idx_documents_biometrics', table_name='documents')

    # Drop columns
    op.drop_column('documents', 'verification_result')
    op.drop_column('documents', 'biometrics_checked_at')
    op.drop_column('documents', 'liveness_score')
    op.drop_column('documents', 'face_match_score')
