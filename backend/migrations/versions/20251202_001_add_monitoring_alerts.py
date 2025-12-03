"""Add monitoring_alerts table for ongoing AML monitoring

Revision ID: 005
Revises: 004
Create Date: 2025-12-02

This migration adds:
1. monitoring_alerts table for tracking alerts from ongoing monitoring
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


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
    if not table_exists('monitoring_alerts'):
        op.create_table(
            'monitoring_alerts',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
            sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
            sa.Column('applicant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('applicants.id', ondelete='CASCADE'), nullable=False),
            sa.Column('alert_type', sa.String(50), nullable=False),
            sa.Column('severity', sa.String(20), server_default='medium', nullable=False),
            sa.Column('previous_screening_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('screening_checks.id', ondelete='SET NULL'), nullable=True),
            sa.Column('new_screening_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('screening_checks.id', ondelete='CASCADE'), nullable=False),
            sa.Column('new_hits', postgresql.JSONB, server_default='[]', nullable=False),
            sa.Column('hit_count', sa.Integer, server_default='0', nullable=False),
            sa.Column('hit_types', postgresql.JSONB, server_default='[]', nullable=False),
            sa.Column('status', sa.String(50), server_default='open', nullable=False),
            sa.Column('resolved_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
            sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('resolution_notes', sa.Text, nullable=True),
            sa.Column('resolution_action', sa.String(50), nullable=True),
            sa.Column('escalated_to', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
            sa.Column('escalated_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('escalation_reason', sa.Text, nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        )

    if not index_exists('monitoring_alerts', 'idx_monitoring_alerts_tenant_status'):
        op.create_index('idx_monitoring_alerts_tenant_status', 'monitoring_alerts', ['tenant_id', 'status'])
    if not index_exists('monitoring_alerts', 'idx_monitoring_alerts_applicant'):
        op.create_index('idx_monitoring_alerts_applicant', 'monitoring_alerts', ['applicant_id'])
    if not index_exists('monitoring_alerts', 'idx_monitoring_alerts_severity'):
        op.create_index('idx_monitoring_alerts_severity', 'monitoring_alerts', ['tenant_id', 'severity'])
    if not index_exists('monitoring_alerts', 'idx_monitoring_alerts_open'):
        op.create_index('idx_monitoring_alerts_open', 'monitoring_alerts', ['tenant_id', 'created_at'],
                       postgresql_where=sa.text("status IN ('open', 'reviewing')"))


def downgrade() -> None:
    if table_exists('monitoring_alerts'):
        op.drop_index('idx_monitoring_alerts_open', table_name='monitoring_alerts')
        op.drop_index('idx_monitoring_alerts_severity', table_name='monitoring_alerts')
        op.drop_index('idx_monitoring_alerts_applicant', table_name='monitoring_alerts')
        op.drop_index('idx_monitoring_alerts_tenant_status', table_name='monitoring_alerts')
        op.drop_table('monitoring_alerts')
