"""Add device fingerprints table for device intelligence

Revision ID: 20251202_005
Revises: 20251202_004
Create Date: 2025-12-02

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision: str = '015'
down_revision: Union[str, None] = '014'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def table_exists(table_name):
    """Check if a table exists in the database."""
    bind = op.get_bind()
    inspector = inspect(bind)
    return table_name in inspector.get_table_names()


def index_exists(table_name, index_name):
    """Check if an index exists on a table."""
    bind = op.get_bind()
    inspector = inspect(bind)
    if not table_exists(table_name):
        return False
    indexes = [idx['name'] for idx in inspector.get_indexes(table_name)]
    return index_name in indexes


def upgrade() -> None:
    # Create device_fingerprints table
    if not table_exists('device_fingerprints'):
        op.create_table(
            'device_fingerprints',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),

            # Relations
            sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
            sa.Column('applicant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('applicants.id', ondelete='SET NULL'), nullable=True),

            # Session tracking
            sa.Column('session_id', sa.String(255), nullable=False),
            sa.Column('fingerprint_hash', sa.String(255), nullable=True),

            # Device/Browser Info
            sa.Column('ip_address', sa.String(45), nullable=False),
            sa.Column('user_agent', sa.Text, nullable=True),
            sa.Column('browser', sa.String(100), nullable=True),
            sa.Column('browser_version', sa.String(50), nullable=True),
            sa.Column('operating_system', sa.String(100), nullable=True),
            sa.Column('os_version', sa.String(50), nullable=True),
            sa.Column('device_type', sa.String(50), nullable=True),
            sa.Column('device_brand', sa.String(100), nullable=True),
            sa.Column('device_model', sa.String(100), nullable=True),
            sa.Column('screen_resolution', sa.String(20), nullable=True),
            sa.Column('timezone', sa.String(100), nullable=True),
            sa.Column('language', sa.String(20), nullable=True),

            # Location
            sa.Column('country_code', sa.String(2), nullable=True),
            sa.Column('city', sa.String(255), nullable=True),
            sa.Column('region', sa.String(255), nullable=True),
            sa.Column('isp', sa.String(255), nullable=True),
            sa.Column('asn', sa.Integer, nullable=True),
            sa.Column('organization', sa.String(255), nullable=True),

            # Network flags
            sa.Column('is_vpn', sa.Boolean, default=False),
            sa.Column('is_proxy', sa.Boolean, default=False),
            sa.Column('is_tor', sa.Boolean, default=False),
            sa.Column('is_bot', sa.Boolean, default=False),
            sa.Column('is_crawler', sa.Boolean, default=False),
            sa.Column('is_mobile', sa.Boolean, default=False),
            sa.Column('is_datacenter', sa.Boolean, default=False),
            sa.Column('active_vpn', sa.Boolean, default=False),
            sa.Column('active_tor', sa.Boolean, default=False),
            sa.Column('recent_abuse', sa.Boolean, default=False),
            sa.Column('connection_type', sa.String(50), nullable=True),

            # Risk scoring
            sa.Column('fraud_score', sa.Integer, nullable=True),
            sa.Column('risk_score', sa.Integer, nullable=True),
            sa.Column('risk_level', sa.String(20), nullable=True),
            sa.Column('risk_signals', postgresql.JSONB, nullable=True),

            # Raw API responses
            sa.Column('ip_check_response', postgresql.JSONB, nullable=True),
            sa.Column('email_check_response', postgresql.JSONB, nullable=True),
            sa.Column('phone_check_response', postgresql.JSONB, nullable=True),
            sa.Column('device_check_response', postgresql.JSONB, nullable=True),

            # Email/Phone validation
            sa.Column('email_valid', sa.Boolean, nullable=True),
            sa.Column('email_disposable', sa.Boolean, nullable=True),
            sa.Column('email_fraud_score', sa.Integer, nullable=True),
            sa.Column('phone_valid', sa.Boolean, nullable=True),
            sa.Column('phone_fraud_score', sa.Integer, nullable=True),
            sa.Column('phone_line_type', sa.String(50), nullable=True),

            # Status
            sa.Column('status', sa.String(50), default='completed'),
            sa.Column('error_message', sa.Text, nullable=True),
        )

    # Create indexes
    if not index_exists('device_fingerprints', 'idx_device_tenant'):
        op.create_index('idx_device_tenant', 'device_fingerprints', ['tenant_id'])
    if not index_exists('device_fingerprints', 'idx_device_applicant'):
        op.create_index('idx_device_applicant', 'device_fingerprints', ['applicant_id'])
    if not index_exists('device_fingerprints', 'idx_device_session'):
        op.create_index('idx_device_session', 'device_fingerprints', ['session_id'])
    if not index_exists('device_fingerprints', 'idx_device_ip'):
        op.create_index('idx_device_ip', 'device_fingerprints', ['ip_address'])
    if not index_exists('device_fingerprints', 'idx_device_fingerprint'):
        op.create_index('idx_device_fingerprint', 'device_fingerprints', ['fingerprint_hash'])
    if not index_exists('device_fingerprints', 'idx_device_risk'):
        op.create_index('idx_device_risk', 'device_fingerprints', ['risk_level'])


def downgrade() -> None:
    if table_exists('device_fingerprints'):
        if index_exists('device_fingerprints', 'idx_device_risk'):
            op.drop_index('idx_device_risk', table_name='device_fingerprints')
        if index_exists('device_fingerprints', 'idx_device_fingerprint'):
            op.drop_index('idx_device_fingerprint', table_name='device_fingerprints')
        if index_exists('device_fingerprints', 'idx_device_ip'):
            op.drop_index('idx_device_ip', table_name='device_fingerprints')
        if index_exists('device_fingerprints', 'idx_device_session'):
            op.drop_index('idx_device_session', table_name='device_fingerprints')
        if index_exists('device_fingerprints', 'idx_device_applicant'):
            op.drop_index('idx_device_applicant', table_name='device_fingerprints')
        if index_exists('device_fingerprints', 'idx_device_tenant'):
            op.drop_index('idx_device_tenant', table_name='device_fingerprints')
        op.drop_table('device_fingerprints')
