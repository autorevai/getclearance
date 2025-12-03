"""Add PII encryption support with larger column sizes and email_hash

Revision ID: 007
Revises: 006
Create Date: 2025-12-02

This migration:
1. Increases column sizes for encrypted PII fields (email, phone, first_name, last_name)
2. Adds email_hash column for searchable lookups
3. Updates index from email to email_hash

NOTE: After running this migration, run the PII migration script to:
1. Encrypt existing plaintext PII data
2. Populate email_hash for existing records

Run: python -m scripts.migrate_encrypt_pii
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '012'
down_revision = '011'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ============================================
    # ADD email_hash COLUMN
    # ============================================
    op.add_column(
        'applicants',
        sa.Column('email_hash', sa.String(64), nullable=True)
    )

    # ============================================
    # MODIFY PII COLUMNS FOR ENCRYPTION
    # ============================================
    # Encrypted values are longer than plaintext (~1.4x + overhead)
    # Increase column sizes to accommodate encrypted data

    # email: 255 -> 512
    op.alter_column(
        'applicants',
        'email',
        type_=sa.String(512),
        existing_type=sa.String(255),
        existing_nullable=True
    )

    # phone: 50 -> 256
    op.alter_column(
        'applicants',
        'phone',
        type_=sa.String(256),
        existing_type=sa.String(50),
        existing_nullable=True
    )

    # first_name: 255 -> 512
    op.alter_column(
        'applicants',
        'first_name',
        type_=sa.String(512),
        existing_type=sa.String(255),
        existing_nullable=True
    )

    # last_name: 255 -> 512
    op.alter_column(
        'applicants',
        'last_name',
        type_=sa.String(512),
        existing_type=sa.String(255),
        existing_nullable=True
    )

    # ============================================
    # UPDATE INDEXES
    # ============================================
    # Drop old email index (can't search encrypted data)
    op.drop_index('idx_applicants_tenant_email', table_name='applicants')

    # Create new email_hash index for lookups
    op.create_index(
        'idx_applicants_tenant_email_hash',
        'applicants',
        ['tenant_id', 'email_hash']
    )


def downgrade() -> None:
    # Drop email_hash index
    op.drop_index('idx_applicants_tenant_email_hash', table_name='applicants')

    # Recreate original email index
    op.create_index(
        'idx_applicants_tenant_email',
        'applicants',
        ['tenant_id', 'email']
    )

    # Revert column sizes (WARNING: This may truncate encrypted data!)
    op.alter_column(
        'applicants',
        'last_name',
        type_=sa.String(255),
        existing_type=sa.String(512),
        existing_nullable=True
    )

    op.alter_column(
        'applicants',
        'first_name',
        type_=sa.String(255),
        existing_type=sa.String(512),
        existing_nullable=True
    )

    op.alter_column(
        'applicants',
        'phone',
        type_=sa.String(50),
        existing_type=sa.String(256),
        existing_nullable=True
    )

    op.alter_column(
        'applicants',
        'email',
        type_=sa.String(255),
        existing_type=sa.String(512),
        existing_nullable=True
    )

    # Drop email_hash column
    op.drop_column('applicants', 'email_hash')
