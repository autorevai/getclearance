"""Add settings and team invitation tables

Revision ID: 006
Revises: 005
Create Date: 2025-12-02

This migration adds:
1. tenant_settings table for key-value settings storage
2. team_invitations table for team member invitations
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ============================================
    # CREATE tenant_settings TABLE
    # ============================================
    op.create_table(
        'tenant_settings',
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

        # Setting identification
        sa.Column('category', sa.String(50), nullable=False, server_default='general'),
        # Categories: general, notifications, branding, security

        sa.Column('key', sa.String(100), nullable=False),
        # Setting key (e.g., 'company_name', 'timezone', 'email_notifications')

        # Setting value
        sa.Column(
            'value',
            postgresql.JSONB,
            server_default='{}',
            nullable=False
        ),
        # JSONB value for flexibility (can store any JSON-serializable data)

        # Audit trail
        sa.Column('updated_by', postgresql.UUID(as_uuid=True)),
        # UUID of user who last updated this setting

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

    # Unique index for tenant + category + key
    op.create_index(
        'idx_tenant_settings_lookup',
        'tenant_settings',
        ['tenant_id', 'category', 'key'],
        unique=True
    )
    op.create_index(
        'idx_tenant_settings_tenant',
        'tenant_settings',
        ['tenant_id']
    )

    # ============================================
    # CREATE team_invitations TABLE
    # ============================================
    op.create_table(
        'team_invitations',
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

        # Invitation details
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('role', sa.String(50), nullable=False, server_default='analyst'),
        # Role to assign: admin, reviewer, analyst, viewer

        # Invitation lifecycle
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        # Status: pending, accepted, expired, cancelled

        sa.Column(
            'invited_by',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('users.id', ondelete='SET NULL'),
            nullable=True
        ),
        sa.Column(
            'invited_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False
        ),
        sa.Column('accepted_at', sa.DateTime(timezone=True)),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),

        # Token for invitation link
        sa.Column('token_hash', sa.String(255)),
        # SHA256 hash of the invitation token

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

    # Indexes for team_invitations
    op.create_index(
        'idx_team_invitations_tenant_email',
        'team_invitations',
        ['tenant_id', 'email']
    )
    op.create_index(
        'idx_team_invitations_tenant',
        'team_invitations',
        ['tenant_id']
    )
    op.create_index(
        'idx_team_invitations_status',
        'team_invitations',
        ['tenant_id', 'status']
    )


def downgrade() -> None:
    # Drop team_invitations indexes and table
    op.drop_index('idx_team_invitations_status', table_name='team_invitations')
    op.drop_index('idx_team_invitations_tenant', table_name='team_invitations')
    op.drop_index('idx_team_invitations_tenant_email', table_name='team_invitations')
    op.drop_table('team_invitations')

    # Drop tenant_settings indexes and table
    op.drop_index('idx_tenant_settings_tenant', table_name='tenant_settings')
    op.drop_index('idx_tenant_settings_lookup', table_name='tenant_settings')
    op.drop_table('tenant_settings')
