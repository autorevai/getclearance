"""
Add Sumsub-inspired features to schema

Revision ID: 20251130_002
Revises: 20251130_001
Create Date: 2025-11-30

This migration adds:
1. Enhanced screening_hits fields (match_type, confidence, pep_relationship, sentiment)
2. Document fraud detection fields
3. Webhook delivery tracking table
4. Applicant events timeline table
5. KYC share tokens table (for future reusable KYC)
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20251130_002'
down_revision = '20251130_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ============================================
    # 1. UPDATE screening_hits FOR FUZZY MATCHING
    # ============================================
    
    # Change confidence from INTEGER to DECIMAL(5,2) for precision
    op.alter_column(
        'screening_hits',
        'confidence',
        existing_type=sa.Integer(),
        type_=sa.Numeric(5, 2),
        existing_nullable=True
    )
    
    # Add match classification field
    op.add_column(
        'screening_hits',
        sa.Column('match_type', sa.String(50), nullable=True)
        # Values: 'true_positive', 'potential_match', 'false_positive', 'unknown'
    )
    
    # Add PEP relationship field
    op.add_column(
        'screening_hits',
        sa.Column('pep_relationship', sa.String(50), nullable=True)
        # Values: 'direct', 'family', 'associate'
    )
    
    # Add adverse media sentiment fields
    op.add_column(
        'screening_hits',
        sa.Column('sentiment', sa.String(20), nullable=True)
        # Values: 'positive', 'neutral', 'negative'
    )
    
    op.add_column(
        'screening_hits',
        sa.Column('source_reputation', sa.String(20), nullable=True)
        # Values: 'high', 'medium', 'low'
    )
    
    # ============================================
    # 2. UPDATE documents FOR FRAUD DETECTION
    # ============================================
    
    # Add security features detected field
    op.add_column(
        'documents',
        sa.Column(
            'security_features_detected',
            postgresql.JSONB,
            server_default='[]',
            nullable=False
        )
        # Example: ["hologram", "mrz", "watermark", "microprint"]
    )
    
    # Add fraud analysis field
    op.add_column(
        'documents',
        sa.Column(
            'fraud_analysis',
            postgresql.JSONB,
            server_default='{}',
            nullable=False
        )
        # Example: {
        #   "signals": [
        #     {"signal": "pixel_analysis_anomaly", "severity": "high", "confidence": 85}
        #   ],
        #   "overall_risk": "medium",
        #   "recommendation": "manual_review"
        # }
    )
    
    # ============================================
    # 3. CREATE webhook_deliveries TABLE
    # ============================================
    
    op.create_table(
        'webhook_deliveries',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        
        # Webhook target
        sa.Column('webhook_url', sa.String(500), nullable=False),
        
        # Event details
        sa.Column('event_type', sa.String(100), nullable=False),
        # Examples: 'applicant.reviewed', 'screening.completed', 'document.verified'
        sa.Column('event_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('payload', postgresql.JSONB, nullable=False),
        
        # Delivery tracking
        sa.Column('attempt_count', sa.Integer, server_default='0', nullable=False),
        sa.Column('last_attempt_at', sa.DateTime(timezone=True)),
        sa.Column('next_retry_at', sa.DateTime(timezone=True)),
        
        # Status
        sa.Column('status', sa.String(50), server_default='pending', nullable=False),
        # Values: 'pending', 'delivered', 'failed', 'expired'
        sa.Column('http_status', sa.Integer),
        sa.Column('response_body', sa.Text),
        
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    
    # Indexes for webhook_deliveries
    op.create_index('idx_webhook_deliveries_tenant', 'webhook_deliveries', ['tenant_id'])
    op.create_index(
        'idx_webhook_deliveries_pending',
        'webhook_deliveries',
        ['status', 'next_retry_at'],
        postgresql_where=sa.text("status = 'pending'")
    )
    op.create_index('idx_webhook_deliveries_event', 'webhook_deliveries', ['event_type', 'event_id'])
    
    # ============================================
    # 4. CREATE applicant_events TABLE
    # ============================================
    
    op.create_table(
        'applicant_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('applicant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('applicants.id', ondelete='CASCADE'), nullable=False),
        
        # Event details
        sa.Column('event_type', sa.String(100), nullable=False),
        # Examples: 'document_uploaded', 'liveness_completed', 'screening_started',
        # 'status_changed', 'manual_review', 'case_created', etc.
        sa.Column('event_data', postgresql.JSONB),
        
        # Actor information
        sa.Column('actor_type', sa.String(50)),
        # Values: 'system', 'applicant', 'reviewer', 'api', 'worker'
        sa.Column('actor_id', postgresql.UUID(as_uuid=True)),
        # user_id if manual action, null if system
        
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    
    # Indexes for applicant_events
    op.create_index('idx_applicant_events_applicant', 'applicant_events', ['applicant_id', 'timestamp'])
    op.create_index('idx_applicant_events_tenant', 'applicant_events', ['tenant_id'])
    op.create_index('idx_applicant_events_type', 'applicant_events', ['event_type'])
    
    # ============================================
    # 5. CREATE kyc_share_tokens TABLE (FUTURE)
    # ============================================
    
    op.create_table(
        'kyc_share_tokens',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('applicant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('applicants.id', ondelete='CASCADE'), nullable=False),
        
        # Token
        sa.Column('token', sa.String(64), nullable=False, unique=True),
        
        # Scope definition
        sa.Column('scope', postgresql.JSONB, nullable=False),
        # Example: {"data": ["identity", "screening"], "documents": false}
        
        # User consent
        sa.Column('user_consent', postgresql.JSONB, nullable=False),
        # Example: {"timestamp": "2025-11-30T10:00:00Z", "ip": "203.0.113.45", "terms_version": "v1.2"}
        
        # Lifecycle
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('revoked_at', sa.DateTime(timezone=True)),
        
        # Usage tracking
        sa.Column('access_count', sa.Integer, server_default='0', nullable=False),
        sa.Column('last_accessed_at', sa.DateTime(timezone=True)),
        sa.Column('last_accessed_by', sa.String(255)),
        # Platform identifier or company name
    )
    
    # Indexes for kyc_share_tokens
    op.create_index('idx_kyc_tokens_applicant', 'kyc_share_tokens', ['applicant_id'])
    op.create_index('idx_kyc_tokens_token', 'kyc_share_tokens', ['token'], unique=True)
    op.create_index(
        'idx_kyc_tokens_active',
        'kyc_share_tokens',
        ['token', 'expires_at'],
        postgresql_where=sa.text("revoked_at IS NULL AND expires_at > now()")
    )


def downgrade() -> None:
    # Drop new tables
    op.drop_table('kyc_share_tokens')
    op.drop_table('applicant_events')
    op.drop_table('webhook_deliveries')
    
    # Remove document fraud detection columns
    op.drop_column('documents', 'fraud_analysis')
    op.drop_column('documents', 'security_features_detected')
    
    # Remove screening_hits enhancements
    op.drop_column('screening_hits', 'source_reputation')
    op.drop_column('screening_hits', 'sentiment')
    op.drop_column('screening_hits', 'pep_relationship')
    op.drop_column('screening_hits', 'match_type')
    
    # Revert confidence to INTEGER
    op.alter_column(
        'screening_hits',
        'confidence',
        existing_type=sa.Numeric(5, 2),
        type_=sa.Integer(),
        existing_nullable=True
    )
