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
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = '012'
down_revision = '011'
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


def get_column_type(table_name, column_name):
    """Get the type of a column."""
    bind = op.get_bind()
    inspector = inspect(bind)
    if not table_exists(table_name):
        return None
    for col in inspector.get_columns(table_name):
        if col['name'] == column_name:
            return col['type']
    return None


def upgrade() -> None:
    # ============================================
    # ADD email_hash COLUMN
    # ============================================
    if not column_exists('applicants', 'email_hash'):
        op.add_column(
            'applicants',
            sa.Column('email_hash', sa.String(64), nullable=True)
        )

    # ============================================
    # MODIFY PII COLUMNS FOR ENCRYPTION
    # ============================================
    # Encrypted values are longer than plaintext (~1.4x + overhead)
    # Increase column sizes to accommodate encrypted data
    # Only alter if the column exists and needs resizing

    if column_exists('applicants', 'email'):
        col_type = get_column_type('applicants', 'email')
        # Check if column needs resizing (is less than 512)
        if col_type and hasattr(col_type, 'length') and col_type.length and col_type.length < 512:
            op.alter_column(
                'applicants',
                'email',
                type_=sa.String(512),
                existing_type=sa.String(255),
                existing_nullable=True
            )

    if column_exists('applicants', 'phone'):
        col_type = get_column_type('applicants', 'phone')
        if col_type and hasattr(col_type, 'length') and col_type.length and col_type.length < 256:
            op.alter_column(
                'applicants',
                'phone',
                type_=sa.String(256),
                existing_type=sa.String(50),
                existing_nullable=True
            )

    if column_exists('applicants', 'first_name'):
        col_type = get_column_type('applicants', 'first_name')
        if col_type and hasattr(col_type, 'length') and col_type.length and col_type.length < 512:
            op.alter_column(
                'applicants',
                'first_name',
                type_=sa.String(512),
                existing_type=sa.String(255),
                existing_nullable=True
            )

    if column_exists('applicants', 'last_name'):
        col_type = get_column_type('applicants', 'last_name')
        if col_type and hasattr(col_type, 'length') and col_type.length and col_type.length < 512:
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
    if index_exists('applicants', 'idx_applicants_tenant_email'):
        op.drop_index('idx_applicants_tenant_email', table_name='applicants')

    # Create new email_hash index for lookups
    if not index_exists('applicants', 'idx_applicants_tenant_email_hash'):
        op.create_index(
            'idx_applicants_tenant_email_hash',
            'applicants',
            ['tenant_id', 'email_hash']
        )


def downgrade() -> None:
    # Drop email_hash index
    if index_exists('applicants', 'idx_applicants_tenant_email_hash'):
        op.drop_index('idx_applicants_tenant_email_hash', table_name='applicants')

    # Recreate original email index
    if not index_exists('applicants', 'idx_applicants_tenant_email'):
        op.create_index(
            'idx_applicants_tenant_email',
            'applicants',
            ['tenant_id', 'email']
        )

    # Revert column sizes (WARNING: This may truncate encrypted data!)
    if column_exists('applicants', 'last_name'):
        op.alter_column(
            'applicants',
            'last_name',
            type_=sa.String(255),
            existing_type=sa.String(512),
            existing_nullable=True
        )

    if column_exists('applicants', 'first_name'):
        op.alter_column(
            'applicants',
            'first_name',
            type_=sa.String(255),
            existing_type=sa.String(512),
            existing_nullable=True
        )

    if column_exists('applicants', 'phone'):
        op.alter_column(
            'applicants',
            'phone',
            type_=sa.String(50),
            existing_type=sa.String(256),
            existing_nullable=True
        )

    if column_exists('applicants', 'email'):
        op.alter_column(
            'applicants',
            'email',
            type_=sa.String(255),
            existing_type=sa.String(512),
            existing_nullable=True
        )

    # Drop email_hash column
    if column_exists('applicants', 'email_hash'):
        op.drop_column('applicants', 'email_hash')
