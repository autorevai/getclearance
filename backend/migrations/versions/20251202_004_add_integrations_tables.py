"""Add API keys and webhooks tables

Revision ID: 008
Revises: 007
Create Date: 2025-12-02

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision: str = '008'
down_revision: Union[str, None] = '007'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def table_exists(table_name):
    bind = op.get_bind()
    inspector = inspect(bind)
    return table_name in inspector.get_table_names()


def index_exists(table_name, index_name):
    bind = op.get_bind()
    inspector = inspect(bind)
    if not table_exists(table_name):
        return False
    indexes = [idx['name'] for idx in inspector.get_indexes(table_name)]
    return index_name in indexes


def upgrade() -> None:
    # Create api_keys table
    if not table_exists('api_keys'):
        op.create_table(
            'api_keys',
            sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('name', sa.String(255), nullable=False),
            sa.Column('key_hash', sa.String(64), nullable=False),
            sa.Column('key_prefix', sa.String(12), nullable=False),
            sa.Column('permissions', postgresql.JSONB(), nullable=True, default=[]),
            sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('last_used_ip', sa.String(45), nullable=True),
            sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
            sa.PrimaryKeyConstraint('id'),
            sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
            sa.UniqueConstraint('key_hash'),
        )
    if not index_exists('api_keys', 'idx_api_keys_tenant'):
        op.create_index('idx_api_keys_tenant', 'api_keys', ['tenant_id'])
    if not index_exists('api_keys', 'idx_api_keys_key_hash'):
        op.create_index('idx_api_keys_key_hash', 'api_keys', ['key_hash'], unique=True)
    if not index_exists('api_keys', 'idx_api_keys_prefix'):
        op.create_index('idx_api_keys_prefix', 'api_keys', ['key_prefix'])

    # Create webhook_configs table
    if not table_exists('webhook_configs'):
        op.create_table(
            'webhook_configs',
            sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('name', sa.String(255), nullable=False),
            sa.Column('url', sa.String(2048), nullable=False),
            sa.Column('secret', sa.String(64), nullable=False),
            sa.Column('events', postgresql.JSONB(), nullable=True, default=[]),
            sa.Column('active', sa.Boolean(), nullable=False, default=True),
            sa.Column('failure_count', sa.Integer(), nullable=False, default=0),
            sa.Column('last_success_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('last_failure_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
            sa.PrimaryKeyConstraint('id'),
            sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        )
    if not index_exists('webhook_configs', 'idx_webhook_configs_tenant'):
        op.create_index('idx_webhook_configs_tenant', 'webhook_configs', ['tenant_id'])
    if not index_exists('webhook_configs', 'idx_webhook_configs_active'):
        op.create_index('idx_webhook_configs_active', 'webhook_configs', ['tenant_id', 'active'])

    # Create webhook_deliveries table
    if not table_exists('webhook_deliveries'):
        op.create_table(
            'webhook_deliveries',
            sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('webhook_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('event_type', sa.String(100), nullable=False),
            sa.Column('payload', postgresql.JSONB(), nullable=False),
            sa.Column('response_code', sa.Integer(), nullable=True),
            sa.Column('response_body', sa.Text(), nullable=True),
            sa.Column('response_time_ms', sa.Integer(), nullable=True),
            sa.Column('success', sa.Boolean(), nullable=False, default=False),
            sa.Column('error_message', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column('delivered_at', sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            sa.ForeignKeyConstraint(['webhook_id'], ['webhook_configs.id'], ondelete='CASCADE'),
        )
    if not index_exists('webhook_deliveries', 'idx_webhook_deliveries_webhook'):
        op.create_index('idx_webhook_deliveries_webhook', 'webhook_deliveries', ['webhook_id'])
    if not index_exists('webhook_deliveries', 'idx_webhook_deliveries_created'):
        op.create_index('idx_webhook_deliveries_created', 'webhook_deliveries', ['created_at'])


def downgrade() -> None:
    if table_exists('webhook_deliveries'):
        op.drop_table('webhook_deliveries')
    if table_exists('webhook_configs'):
        op.drop_table('webhook_configs')
    if table_exists('api_keys'):
        op.drop_table('api_keys')
