"""Add custom_data column to applicants table

Revision ID: 20251202_001
Revises: 20251201_002
Create Date: 2025-12-02

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20251202_001'
down_revision = '20251201_002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add custom_data column to applicants table for SDK data
    op.add_column(
        'applicants',
        sa.Column(
            'custom_data',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            server_default='{}',
        )
    )


def downgrade() -> None:
    op.drop_column('applicants', 'custom_data')
