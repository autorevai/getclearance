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
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = '014'
down_revision = '013'
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
    # Add biometrics columns to documents table
    if not column_exists('documents', 'face_match_score'):
        op.add_column(
            'documents',
            sa.Column('face_match_score', sa.Numeric(5, 2), nullable=True,
                      comment='Face similarity score 0-100 when compared to selfie')
        )
    if not column_exists('documents', 'liveness_score'):
        op.add_column(
            'documents',
            sa.Column('liveness_score', sa.Numeric(5, 2), nullable=True,
                      comment='Liveness detection confidence 0-100')
        )
    if not column_exists('documents', 'biometrics_checked_at'):
        op.add_column(
            'documents',
            sa.Column('biometrics_checked_at', sa.DateTime(timezone=True), nullable=True,
                      comment='When biometric verification was performed')
        )
    if not column_exists('documents', 'verification_result'):
        op.add_column(
            'documents',
            sa.Column('verification_result', postgresql.JSONB, nullable=True,
                      comment='Full biometric verification result including quality metrics')
        )

    # Create index for documents with biometrics
    if not index_exists('documents', 'idx_documents_biometrics'):
        op.create_index(
            'idx_documents_biometrics',
            'documents',
            ['applicant_id', 'biometrics_checked_at'],
            postgresql_where=sa.text('biometrics_checked_at IS NOT NULL')
        )


def downgrade() -> None:
    # Drop index
    if index_exists('documents', 'idx_documents_biometrics'):
        op.drop_index('idx_documents_biometrics', table_name='documents')

    # Drop columns
    if column_exists('documents', 'verification_result'):
        op.drop_column('documents', 'verification_result')
    if column_exists('documents', 'biometrics_checked_at'):
        op.drop_column('documents', 'biometrics_checked_at')
    if column_exists('documents', 'liveness_score'):
        op.drop_column('documents', 'liveness_score')
    if column_exists('documents', 'face_match_score'):
        op.drop_column('documents', 'face_match_score')
