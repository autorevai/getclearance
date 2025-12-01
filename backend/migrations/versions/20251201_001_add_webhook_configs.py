"""Add webhook_configs table for tenant webhook settings

Revision ID: 003
Revises: 002
Create Date: 2025-12-01

This migration adds:
1. webhook_configs table for tenant webhook configuration
   - Allows tenants to configure webhook endpoints
   - Supports multiple webhook URLs per tenant with event subscriptions
   - Includes HMAC secret for signature verification
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ============================================
    # CREATE webhook_configs TABLE
    # ============================================
    # Stores tenant webhook configuration (URL, secret, subscribed events)
    # Different from webhook_deliveries which tracks individual delivery attempts

    op.create_table(
        'webhook_configs',
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

        # Webhook endpoint configuration
        sa.Column('name', sa.String(255), nullable=False),
        # Friendly name for the webhook (e.g., "Production", "Slack Alerts")
        sa.Column('url', sa.String(500), nullable=False),
        # Target URL to send webhook events to
        sa.Column('secret', sa.String(255), nullable=False),
        # HMAC secret for signature verification (auto-generated)

        # Event subscriptions
        sa.Column(
            'events',
            postgresql.JSONB,
            server_default='[]',
            nullable=False
        ),
        # Array of subscribed event types:
        # [
        #   "applicant.created",
        #   "applicant.approved",
        #   "applicant.rejected",
        #   "screening.completed",
        #   "screening.hit_found",
        #   "document.verified",
        #   "document.rejected",
        #   "case.created",
        #   "case.resolved"
        # ]

        # Configuration options
        sa.Column(
            'headers',
            postgresql.JSONB,
            server_default='{}',
            nullable=False
        ),
        # Custom headers to include in webhook requests
        # Example: {"X-Custom-Header": "value"}

        sa.Column('timeout_seconds', sa.Integer, server_default='30', nullable=False),
        # Request timeout in seconds

        sa.Column('max_retries', sa.Integer, server_default='3', nullable=False),
        # Maximum retry attempts for failed deliveries

        # Status
        sa.Column('is_active', sa.Boolean, server_default='true', nullable=False),
        # Whether this webhook config is active

        sa.Column('is_verified', sa.Boolean, server_default='false', nullable=False),
        # Whether the webhook URL has been verified (via test ping)

        sa.Column('last_verified_at', sa.DateTime(timezone=True)),
        # When the webhook was last successfully verified

        # Delivery stats (denormalized for quick access)
        sa.Column('total_deliveries', sa.Integer, server_default='0', nullable=False),
        sa.Column('successful_deliveries', sa.Integer, server_default='0', nullable=False),
        sa.Column('failed_deliveries', sa.Integer, server_default='0', nullable=False),
        sa.Column('last_delivery_at', sa.DateTime(timezone=True)),
        sa.Column('last_delivery_status', sa.String(50)),
        # Values: 'success', 'failed', 'pending'

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

    # Indexes for webhook_configs
    op.create_index(
        'idx_webhook_configs_tenant',
        'webhook_configs',
        ['tenant_id']
    )
    op.create_index(
        'idx_webhook_configs_active',
        'webhook_configs',
        ['tenant_id', 'is_active'],
        postgresql_where=sa.text("is_active = true")
    )


def downgrade() -> None:
    # Drop indexes first
    op.drop_index('idx_webhook_configs_active', table_name='webhook_configs')
    op.drop_index('idx_webhook_configs_tenant', table_name='webhook_configs')

    # Drop table
    op.drop_table('webhook_configs')
