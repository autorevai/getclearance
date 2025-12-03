"""Add KYC share tables for reusable KYC

Revision ID: 20251202_007
Revises: 20251202_006
Create Date: 2025-12-02

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '010'
down_revision: Union[str, None] = '009'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create kyc_share_tokens table
    op.create_table(
        'kyc_share_tokens',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),

        # Tenant and Applicant
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('applicant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('applicants.id', ondelete='CASCADE'), nullable=False),

        # Token identification
        sa.Column('token_hash', sa.String(64), nullable=False, unique=True),
        sa.Column('token_prefix', sa.String(8), nullable=False),

        # Recipient information
        sa.Column('shared_with', sa.String(255), nullable=False),
        sa.Column('shared_with_email', sa.String(255), nullable=True),
        sa.Column('purpose', sa.Text, nullable=True),

        # Permissions
        sa.Column('permissions', postgresql.JSONB, nullable=False, server_default='{}'),

        # Limits
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('max_uses', sa.Integer, default=1, nullable=False),
        sa.Column('use_count', sa.Integer, default=0, nullable=False),

        # Status
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('revoked_reason', sa.String(255), nullable=True),

        # Consent
        sa.Column('consent_given_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('consent_ip_address', sa.String(45), nullable=True),
    )

    # Create indexes for kyc_share_tokens
    op.create_index('idx_share_tokens_tenant', 'kyc_share_tokens', ['tenant_id'])
    op.create_index('idx_share_tokens_applicant', 'kyc_share_tokens', ['applicant_id'])
    op.create_index('idx_share_tokens_hash', 'kyc_share_tokens', ['token_hash'], unique=True)
    op.create_index('idx_share_tokens_prefix', 'kyc_share_tokens', ['token_prefix'])

    # Create kyc_share_access_logs table
    op.create_table(
        'kyc_share_access_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),

        # Token reference
        sa.Column('token_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('kyc_share_tokens.id', ondelete='CASCADE'), nullable=False),

        # Requester information
        sa.Column('requester_ip', sa.String(45), nullable=True),
        sa.Column('requester_domain', sa.String(255), nullable=True),
        sa.Column('requester_user_agent', sa.Text, nullable=True),

        # Access details
        sa.Column('accessed_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('success', sa.Boolean, default=True, nullable=False),
        sa.Column('failure_reason', sa.String(255), nullable=True),

        # What data was accessed
        sa.Column('accessed_permissions', postgresql.JSONB, nullable=False, server_default='[]'),
    )

    # Create indexes for kyc_share_access_logs
    op.create_index('idx_share_access_token', 'kyc_share_access_logs', ['token_id'])
    op.create_index('idx_share_access_date', 'kyc_share_access_logs', ['accessed_at'])


def downgrade() -> None:
    op.drop_table('kyc_share_access_logs')
    op.drop_table('kyc_share_tokens')
