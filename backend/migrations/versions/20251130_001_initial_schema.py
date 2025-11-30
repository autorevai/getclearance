"""Initial schema - tenants applicants documents screening cases

Revision ID: 001
Revises: 
Create Date: 2025-11-30
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ===========================================
    # TENANTS
    # ===========================================
    op.create_table(
        'tenants',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('slug', sa.String(63), nullable=False, unique=True, index=True),
        sa.Column('settings', postgresql.JSONB, server_default='{}'),
        sa.Column('billing_customer_id', sa.String(255)),
        sa.Column('plan', sa.String(50), server_default='starter'),
        sa.Column('status', sa.String(20), server_default='active'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # ===========================================
    # USERS
    # ===========================================
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('auth0_id', sa.String(255), unique=True),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('name', sa.String(255)),
        sa.Column('avatar_url', sa.String(1000)),
        sa.Column('role', sa.String(50), server_default='analyst'),
        sa.Column('permissions', postgresql.JSONB, server_default='[]'),
        sa.Column('last_login_at', sa.DateTime(timezone=True)),
        sa.Column('status', sa.String(20), server_default='active'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )
    op.create_index('idx_users_tenant', 'users', ['tenant_id'])
    op.create_index('idx_users_tenant_email', 'users', ['tenant_id', 'email'], unique=True)

    # ===========================================
    # APPLICANTS
    # ===========================================
    op.create_table(
        'applicants',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('external_id', sa.String(255)),
        sa.Column('email', sa.String(255)),
        sa.Column('phone', sa.String(50)),
        sa.Column('first_name', sa.String(255)),
        sa.Column('last_name', sa.String(255)),
        sa.Column('date_of_birth', sa.Date),
        sa.Column('nationality', sa.String(3)),
        sa.Column('country_of_residence', sa.String(3)),
        sa.Column('address', postgresql.JSONB),
        sa.Column('workflow_id', postgresql.UUID(as_uuid=True)),
        sa.Column('workflow_version', sa.Integer),
        sa.Column('status', sa.String(50), server_default='pending'),
        sa.Column('risk_score', sa.Integer),
        sa.Column('risk_factors', postgresql.JSONB, server_default='[]'),
        sa.Column('flags', postgresql.ARRAY(sa.String(50)), server_default='{}'),
        sa.Column('source', sa.String(50)),
        sa.Column('ip_address', postgresql.INET),
        sa.Column('device_info', postgresql.JSONB),
        sa.Column('submitted_at', sa.DateTime(timezone=True)),
        sa.Column('reviewed_at', sa.DateTime(timezone=True)),
        sa.Column('reviewed_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL')),
        sa.Column('sla_due_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )
    op.create_index('idx_applicants_tenant', 'applicants', ['tenant_id'])
    op.create_index('idx_applicants_tenant_external', 'applicants', ['tenant_id', 'external_id'], unique=True)
    op.create_index('idx_applicants_tenant_status', 'applicants', ['tenant_id', 'status'])
    op.create_index('idx_applicants_tenant_email', 'applicants', ['tenant_id', 'email'])
    op.create_index('idx_applicants_tenant_risk', 'applicants', ['tenant_id', 'risk_score'])

    # ===========================================
    # APPLICANT STEPS
    # ===========================================
    op.create_table(
        'applicant_steps',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('applicant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('applicants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('step_id', sa.String(100), nullable=False),
        sa.Column('step_type', sa.String(50), nullable=False),
        sa.Column('status', sa.String(50), server_default='pending'),
        sa.Column('data', postgresql.JSONB, server_default='{}'),
        sa.Column('verification_result', postgresql.JSONB),
        sa.Column('failure_reasons', postgresql.ARRAY(sa.String(255)), server_default='{}'),
        sa.Column('resubmission_count', sa.Integer, server_default='0'),
        sa.Column('resubmission_requested_at', sa.DateTime(timezone=True)),
        sa.Column('resubmission_message', sa.Text),
        sa.Column('completed_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )
    op.create_index('idx_applicant_steps_applicant', 'applicant_steps', ['applicant_id'])
    op.create_index('idx_applicant_steps_applicant_step', 'applicant_steps', ['applicant_id', 'step_id'], unique=True)

    # ===========================================
    # DOCUMENTS
    # ===========================================
    op.create_table(
        'documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('applicant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('applicants.id', ondelete='CASCADE')),
        sa.Column('company_id', postgresql.UUID(as_uuid=True)),
        sa.Column('step_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('applicant_steps.id', ondelete='SET NULL')),
        sa.Column('type', sa.String(100), nullable=False),
        sa.Column('file_name', sa.String(500)),
        sa.Column('file_size', sa.Integer),
        sa.Column('mime_type', sa.String(100)),
        sa.Column('storage_path', sa.String(1000), nullable=False),
        sa.Column('status', sa.String(50), server_default='pending'),
        sa.Column('ocr_text', sa.Text),
        sa.Column('ocr_confidence', sa.Numeric(5, 2)),
        sa.Column('extracted_data', postgresql.JSONB),
        sa.Column('verification_checks', postgresql.JSONB, server_default='[]'),
        sa.Column('fraud_signals', postgresql.JSONB, server_default='[]'),
        sa.Column('original_language', sa.String(10)),
        sa.Column('translated_text', sa.Text),
        sa.Column('uploaded_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('processed_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )
    op.create_index('idx_documents_tenant', 'documents', ['tenant_id'])
    op.create_index('idx_documents_applicant', 'documents', ['applicant_id'])
    op.create_index('idx_documents_tenant_type', 'documents', ['tenant_id', 'type'])

    # ===========================================
    # SCREENING LISTS
    # ===========================================
    op.create_table(
        'screening_lists',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('source', sa.String(100), nullable=False),
        sa.Column('version_id', sa.String(100), nullable=False),
        sa.Column('list_type', sa.String(50), nullable=False),
        sa.Column('entity_count', sa.Integer),
        sa.Column('published_at', sa.DateTime(timezone=True)),
        sa.Column('fetched_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('checksum', sa.String(64)),
    )
    op.create_index('idx_screening_lists_source_version', 'screening_lists', ['source', 'version_id'], unique=True)

    # ===========================================
    # SCREENING CHECKS
    # ===========================================
    op.create_table(
        'screening_checks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('applicant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('applicants.id', ondelete='CASCADE')),
        sa.Column('company_id', postgresql.UUID(as_uuid=True)),
        sa.Column('entity_type', sa.String(20), nullable=False),
        sa.Column('screened_name', sa.String(500), nullable=False),
        sa.Column('screened_dob', sa.Date),
        sa.Column('screened_country', sa.String(3)),
        sa.Column('check_types', postgresql.ARRAY(sa.String(50)), nullable=False),
        sa.Column('status', sa.String(50), server_default='pending'),
        sa.Column('hit_count', sa.Integer, server_default='0'),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('completed_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )
    op.create_index('idx_screening_checks_tenant', 'screening_checks', ['tenant_id'])
    op.create_index('idx_screening_checks_applicant', 'screening_checks', ['applicant_id'])
    op.create_index('idx_screening_checks_tenant_status', 'screening_checks', ['tenant_id', 'status'])

    # ===========================================
    # SCREENING HITS
    # ===========================================
    op.create_table(
        'screening_hits',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('check_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('screening_checks.id', ondelete='CASCADE'), nullable=False),
        sa.Column('list_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('screening_lists.id', ondelete='SET NULL')),
        sa.Column('list_source', sa.String(100), nullable=False),
        sa.Column('list_version_id', sa.String(100), nullable=False),
        sa.Column('hit_type', sa.String(50), nullable=False),
        sa.Column('matched_entity_id', sa.String(255)),
        sa.Column('matched_name', sa.String(500), nullable=False),
        sa.Column('confidence', sa.Numeric(5, 2), nullable=False),
        sa.Column('matched_fields', postgresql.ARRAY(sa.String(100)), server_default='{}'),
        sa.Column('match_data', postgresql.JSONB, server_default='{}'),
        sa.Column('pep_tier', sa.Integer),
        sa.Column('pep_position', sa.Text),
        sa.Column('pep_relationship', sa.String(100)),
        sa.Column('article_url', sa.Text),
        sa.Column('article_title', sa.Text),
        sa.Column('article_date', sa.Date),
        sa.Column('categories', postgresql.ARRAY(sa.String(100)), server_default='{}'),
        sa.Column('resolution_status', sa.String(50), server_default='pending'),
        sa.Column('resolution_notes', sa.Text),
        sa.Column('resolved_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL')),
        sa.Column('resolved_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )
    op.create_index('idx_screening_hits_check', 'screening_hits', ['check_id'])
    op.create_index('idx_screening_hits_resolution', 'screening_hits', ['resolution_status'])

    # ===========================================
    # CASES
    # ===========================================
    op.create_table(
        'cases',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('case_number', sa.String(50), nullable=False),
        sa.Column('applicant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('applicants.id', ondelete='SET NULL')),
        sa.Column('company_id', postgresql.UUID(as_uuid=True)),
        sa.Column('screening_hit_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('screening_hits.id', ondelete='SET NULL')),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('type', sa.String(50), nullable=False),
        sa.Column('priority', sa.String(20), server_default='medium'),
        sa.Column('status', sa.String(50), server_default='open'),
        sa.Column('assignee_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL')),
        sa.Column('escalated_to', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL')),
        sa.Column('resolution', sa.String(50)),
        sa.Column('resolution_notes', sa.Text),
        sa.Column('source', sa.String(100)),
        sa.Column('source_reference', sa.String(255)),
        sa.Column('due_at', sa.DateTime(timezone=True)),
        sa.Column('opened_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('resolved_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )
    op.create_index('idx_cases_tenant', 'cases', ['tenant_id'])
    op.create_index('idx_cases_tenant_number', 'cases', ['tenant_id', 'case_number'], unique=True)
    op.create_index('idx_cases_tenant_status', 'cases', ['tenant_id', 'status'])
    op.create_index('idx_cases_assignee', 'cases', ['assignee_id'])
    op.create_index('idx_cases_applicant', 'cases', ['applicant_id'])

    # ===========================================
    # CASE NOTES
    # ===========================================
    op.create_table(
        'case_notes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('case_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('cases.id', ondelete='CASCADE'), nullable=False),
        sa.Column('author_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL')),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('is_ai_generated', sa.Boolean, server_default='false'),
        sa.Column('ai_model', sa.String(100)),
        sa.Column('ai_citations', postgresql.JSONB, server_default='[]'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )
    op.create_index('idx_case_notes_case', 'case_notes', ['case_id'])

    # ===========================================
    # CASE ATTACHMENTS
    # ===========================================
    op.create_table(
        'case_attachments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('case_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('cases.id', ondelete='CASCADE'), nullable=False),
        sa.Column('document_id', postgresql.UUID(as_uuid=True)),
        sa.Column('file_name', sa.String(500), nullable=False),
        sa.Column('storage_path', sa.String(1000), nullable=False),
        sa.Column('file_size', sa.Integer),
        sa.Column('mime_type', sa.String(100)),
        sa.Column('uploaded_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )
    op.create_index('idx_case_attachments_case', 'case_attachments', ['case_id'])

    # ===========================================
    # AUDIT LOG
    # ===========================================
    op.create_table(
        'audit_log',
        sa.Column('id', sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True)),
        sa.Column('user_email', sa.String(255)),
        sa.Column('ip_address', postgresql.INET),
        sa.Column('user_agent', sa.Text),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('resource_type', sa.String(50), nullable=False),
        sa.Column('resource_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('old_values', postgresql.JSONB),
        sa.Column('new_values', postgresql.JSONB),
        sa.Column('metadata', postgresql.JSONB, server_default='{}'),
        sa.Column('checksum', sa.String(64), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )
    op.create_index('idx_audit_log_tenant_time', 'audit_log', ['tenant_id', 'created_at'])
    op.create_index('idx_audit_log_resource', 'audit_log', ['resource_type', 'resource_id'])
    op.create_index('idx_audit_log_user', 'audit_log', ['user_id'])
    op.create_index('idx_audit_log_action', 'audit_log', ['action'])


def downgrade() -> None:
    op.drop_table('audit_log')
    op.drop_table('case_attachments')
    op.drop_table('case_notes')
    op.drop_table('cases')
    op.drop_table('screening_hits')
    op.drop_table('screening_checks')
    op.drop_table('screening_lists')
    op.drop_table('documents')
    op.drop_table('applicant_steps')
    op.drop_table('applicants')
    op.drop_table('users')
    op.drop_table('tenants')
