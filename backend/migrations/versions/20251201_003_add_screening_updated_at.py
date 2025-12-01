"""Add updated_at to screening_checks table

Revision ID: 005
Revises: 004
Create Date: 2025-12-01

The screening_checks table was missing updated_at column.
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'screening_checks',
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=True
        )
    )


def downgrade() -> None:
    op.drop_column('screening_checks', 'updated_at')
