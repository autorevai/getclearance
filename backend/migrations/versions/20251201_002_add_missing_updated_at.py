"""Add missing updated_at column to tables using TimestampMixin

Revision ID: 004
Revises: 003
Create Date: 2025-12-01

Several tables were missing the updated_at column that their models expect
from the TimestampMixin (documents, screening_checks).
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add updated_at to screening_checks table
    op.add_column(
        'screening_checks',
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=True
        )
    )

    # Add updated_at to documents table
    op.add_column(
        'documents',
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=True
        )
    )


def downgrade() -> None:
    op.drop_column('screening_checks', 'updated_at')
    op.drop_column('documents', 'updated_at')
