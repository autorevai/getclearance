# Get Clearance - System Architecture

## Overview

A multi-tenant, AI-native compliance platform designed to scale from startup to enterprise workloads. The architecture prioritizes auditability, AI integration at every layer, and horizontal scalability.

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENTS                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│  Web Dashboard    │   Mobile SDK    │   REST API    │   Webhooks (inbound)  │
│  (React SPA)      │   (React Native)│   (Customers) │   (TRM, Chainalysis)  │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           API GATEWAY / LOAD BALANCER                        │
│                    (AWS ALB / Cloudflare / Kong)                            │
│         - Rate limiting, SSL termination, request routing                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    ▼                 ▼                 ▼
┌──────────────────────┐ ┌──────────────────────┐ ┌──────────────────────┐
│   API SERVICE        │ │   WORKER SERVICE     │ │   AI SERVICE         │
│   (FastAPI)          │ │   (Celery/ARQ)       │ │   (FastAPI)          │
│                      │ │                      │ │                      │
│ - REST endpoints     │ │ - Async jobs         │ │ - Claude API proxy   │
│ - Auth/AuthZ         │ │ - Screening runs     │ │ - Document analysis  │
│ - Request validation │ │ - List syncs         │ │ - Risk scoring       │
│ - Business logic     │ │ - Evidence export    │ │ - Summary generation │
│                      │ │ - Webhook dispatch   │ │ - Batch review       │
└──────────────────────┘ └──────────────────────┘ └──────────────────────┘
          │                       │                        │
          └───────────────────────┼────────────────────────┘
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DATA LAYER                                         │
├─────────────────┬─────────────────┬─────────────────┬───────────────────────┤
│   PostgreSQL    │     Redis       │   S3 / Minio    │   Elasticsearch      │
│   (Primary DB)  │   (Cache/Queue) │   (Documents)   │   (Search/Analytics) │
│                 │                 │                 │                       │
│ - Tenants       │ - Session cache │ - ID docs       │ - Full-text search   │
│ - Applicants    │ - Rate limits   │ - Selfies       │ - Audit log search   │
│ - Companies     │ - Job queues    │ - Evidence PDFs │ - Applicant search   │
│ - Workflows     │ - API cache     │ - OCR results   │ - Screening results  │
│ - Cases         │ - Pub/sub       │                 │                       │
│ - Screening     │                 │                 │                       │
│ - Audit logs    │                 │                 │                       │
└─────────────────┴─────────────────┴─────────────────┴───────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        EXTERNAL INTEGRATIONS                                 │
├─────────────────┬─────────────────┬─────────────────┬───────────────────────┤
│  OpenSanctions  │  TRM Labs       │  Chainalysis    │   Claude API         │
│  (Sanctions/PEP)│  (Crypto TM)    │  (Crypto TM)    │   (AI Engine)        │
├─────────────────┼─────────────────┼─────────────────┼───────────────────────┤
│  Twilio         │  AWS Textract   │  Google Vision  │   Stripe             │
│  (SMS/Phone)    │  (OCR)          │  (OCR backup)   │   (Billing)          │
└─────────────────┴─────────────────┴─────────────────┴───────────────────────┘
```

---

## Database Schema (PostgreSQL)

### Design Principles

1. **Multi-tenant by default** - Every table has `tenant_id`, row-level security
2. **Immutable audit trail** - Soft deletes, append-only audit log
3. **Version everything** - Workflows, screening lists, decisions all versioned
4. **JSONB for flexibility** - Extensible fields without migrations
5. **UUID primary keys** - No sequential IDs exposed externally

### Core Tables

```sql
-- ============================================
-- TENANT & AUTH
-- ============================================

CREATE TABLE tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(63) UNIQUE NOT NULL,
    settings JSONB DEFAULT '{}',
    billing_customer_id VARCHAR(255), -- Stripe customer ID
    plan VARCHAR(50) DEFAULT 'starter',
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id),
    email VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255),
    name VARCHAR(255),
    role VARCHAR(50) DEFAULT 'analyst', -- admin, reviewer, analyst, viewer
    permissions JSONB DEFAULT '[]',
    last_login_at TIMESTAMPTZ,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(tenant_id, email)
);

CREATE INDEX idx_users_tenant ON users(tenant_id);
CREATE INDEX idx_users_email ON users(email);

-- ============================================
-- WORKFLOWS (Versioned)
-- ============================================

CREATE TABLE workflows (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id),
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL, -- 'kyc', 'kyb'
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE workflow_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID REFERENCES workflows(id),
    version INTEGER NOT NULL,
    config JSONB NOT NULL, -- steps, conditions, SLAs, EDD branches
    published_at TIMESTAMPTZ,
    published_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(workflow_id, version)
);

-- Config JSONB structure:
-- {
--   "steps": [
--     {"id": "id_document", "type": "document", "required": true, "doc_types": ["passport", "drivers_license"]},
--     {"id": "liveness", "type": "liveness", "required": true},
--     {"id": "poa", "type": "document", "required": false, "condition": "risk_score > 50"}
--   ],
--   "sla": {"review_hours": 24, "escalation_hours": 48},
--   "auto_approve": {"enabled": true, "max_risk_score": 30}
-- }

CREATE INDEX idx_workflow_versions_workflow ON workflow_versions(workflow_id);

-- ============================================
-- APPLICANTS (Individuals)
-- ============================================

CREATE TABLE applicants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id),
    external_id VARCHAR(255), -- Customer's reference ID
    
    -- Personal info (encrypted at rest)
    email VARCHAR(255),
    phone VARCHAR(50),
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    date_of_birth DATE,
    nationality VARCHAR(3), -- ISO 3166-1 alpha-3
    country_of_residence VARCHAR(3),
    address JSONB, -- {street, city, state, postal_code, country}
    
    -- Workflow state
    workflow_id UUID REFERENCES workflows(id),
    workflow_version INTEGER,
    status VARCHAR(50) DEFAULT 'pending', -- pending, in_progress, review, approved, rejected, withdrawn
    
    -- Risk assessment
    risk_score INTEGER, -- 0-100
    risk_factors JSONB DEFAULT '[]', -- [{factor, impact, source}]
    flags VARCHAR(50)[] DEFAULT '{}', -- ['pep', 'sanctions', 'adverse_media', 'high_risk_country']
    
    -- Metadata
    source VARCHAR(50), -- 'api', 'web', 'mobile', 'sdk'
    ip_address INET,
    device_info JSONB,
    
    -- Timestamps
    submitted_at TIMESTAMPTZ,
    reviewed_at TIMESTAMPTZ,
    reviewed_by UUID REFERENCES users(id),
    sla_due_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(tenant_id, external_id)
);

CREATE INDEX idx_applicants_tenant ON applicants(tenant_id);
CREATE INDEX idx_applicants_status ON applicants(tenant_id, status);
CREATE INDEX idx_applicants_email ON applicants(tenant_id, email);
CREATE INDEX idx_applicants_risk ON applicants(tenant_id, risk_score);
CREATE INDEX idx_applicants_sla ON applicants(tenant_id, sla_due_at) WHERE status IN ('pending', 'in_progress', 'review');
CREATE INDEX idx_applicants_flags ON applicants USING GIN(flags);

-- ============================================
-- APPLICANT KYC STEPS
-- ============================================

CREATE TABLE applicant_steps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    applicant_id UUID REFERENCES applicants(id),
    step_id VARCHAR(100) NOT NULL, -- matches workflow config step id
    status VARCHAR(50) DEFAULT 'pending', -- pending, in_progress, complete, failed, skipped
    
    -- Step-specific data
    data JSONB DEFAULT '{}', -- varies by step type
    
    -- Verification results
    verification_result JSONB, -- {passed, confidence, checks: [...]}
    failure_reasons VARCHAR(255)[],
    
    -- Resubmission
    resubmission_count INTEGER DEFAULT 0,
    resubmission_requested_at TIMESTAMPTZ,
    resubmission_message TEXT,
    
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(applicant_id, step_id)
);

CREATE INDEX idx_applicant_steps_applicant ON applicant_steps(applicant_id);

-- ============================================
-- COMPANIES (KYB)
-- ============================================

CREATE TABLE companies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id),
    external_id VARCHAR(255),
    
    -- Company info
    legal_name VARCHAR(500) NOT NULL,
    trading_name VARCHAR(500),
    registration_number VARCHAR(100),
    tax_id VARCHAR(100),
    jurisdiction VARCHAR(3), -- ISO country code
    incorporation_date DATE,
    company_type VARCHAR(100), -- LLC, Corp, GmbH, etc.
    industry_codes VARCHAR(20)[], -- NAICS/SIC codes
    
    -- Address
    registered_address JSONB,
    business_address JSONB,
    
    -- Workflow state
    workflow_id UUID REFERENCES workflows(id),
    workflow_version INTEGER,
    status VARCHAR(50) DEFAULT 'pending',
    
    -- Risk
    risk_score INTEGER,
    risk_factors JSONB DEFAULT '[]',
    flags VARCHAR(50)[] DEFAULT '{}',
    
    -- Timestamps
    submitted_at TIMESTAMPTZ,
    reviewed_at TIMESTAMPTZ,
    reviewed_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(tenant_id, external_id)
);

CREATE INDEX idx_companies_tenant ON companies(tenant_id);
CREATE INDEX idx_companies_status ON companies(tenant_id, status);
CREATE INDEX idx_companies_jurisdiction ON companies(tenant_id, jurisdiction);

-- ============================================
-- BENEFICIAL OWNERS / OFFICERS
-- ============================================

CREATE TABLE company_persons (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id),
    applicant_id UUID REFERENCES applicants(id), -- Link to full KYC if available
    
    -- Role
    role VARCHAR(50) NOT NULL, -- 'ubo', 'director', 'officer', 'shareholder'
    title VARCHAR(255),
    ownership_percentage DECIMAL(5,2),
    
    -- Basic info (if no linked applicant)
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    date_of_birth DATE,
    nationality VARCHAR(3),
    
    -- Verification
    verified BOOLEAN DEFAULT false,
    verified_at TIMESTAMPTZ,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_company_persons_company ON company_persons(company_id);
CREATE INDEX idx_company_persons_applicant ON company_persons(applicant_id);

-- ============================================
-- DOCUMENTS
-- ============================================

CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id),
    applicant_id UUID REFERENCES applicants(id),
    company_id UUID REFERENCES companies(id),
    step_id UUID REFERENCES applicant_steps(id),
    
    -- Document info
    type VARCHAR(100) NOT NULL, -- 'passport', 'drivers_license', 'utility_bill', etc.
    file_name VARCHAR(500),
    file_size INTEGER,
    mime_type VARCHAR(100),
    storage_path VARCHAR(1000), -- S3 key
    
    -- Processing
    status VARCHAR(50) DEFAULT 'pending', -- pending, processing, verified, rejected
    
    -- OCR & extraction
    ocr_text TEXT,
    ocr_confidence DECIMAL(5,2),
    extracted_data JSONB, -- {document_number, expiry_date, issuing_country, etc.}
    
    -- Verification
    verification_checks JSONB, -- [{check, passed, confidence, details}]
    fraud_signals JSONB, -- [{signal, severity, details}]
    
    -- Translation
    original_language VARCHAR(10),
    translated_text TEXT,
    
    uploaded_at TIMESTAMPTZ DEFAULT NOW(),
    processed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_documents_applicant ON documents(applicant_id);
CREATE INDEX idx_documents_company ON documents(company_id);
CREATE INDEX idx_documents_type ON documents(tenant_id, type);

-- ============================================
-- SCREENING
-- ============================================

CREATE TABLE screening_lists (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source VARCHAR(100) NOT NULL, -- 'ofac_sdn', 'eu_consolidated', 'un_sc', 'opensanctions'
    version_id VARCHAR(100) NOT NULL, -- e.g., 'OFAC-2025-11-27'
    list_type VARCHAR(50) NOT NULL, -- 'sanctions', 'pep', 'adverse_media'
    entity_count INTEGER,
    published_at TIMESTAMPTZ,
    fetched_at TIMESTAMPTZ DEFAULT NOW(),
    checksum VARCHAR(64),
    UNIQUE(source, version_id)
);

CREATE TABLE screening_checks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id),
    applicant_id UUID REFERENCES applicants(id),
    company_id UUID REFERENCES companies(id),
    
    -- What was screened
    entity_type VARCHAR(20) NOT NULL, -- 'individual', 'company'
    screened_name VARCHAR(500),
    screened_dob DATE,
    screened_country VARCHAR(3),
    
    -- Check configuration
    check_types VARCHAR(50)[] NOT NULL, -- ['sanctions', 'pep', 'adverse_media']
    
    -- Results summary
    status VARCHAR(50) DEFAULT 'pending', -- pending, clear, hit, error
    hit_count INTEGER DEFAULT 0,
    
    -- Timestamps
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_screening_checks_applicant ON screening_checks(applicant_id);
CREATE INDEX idx_screening_checks_company ON screening_checks(company_id);
CREATE INDEX idx_screening_checks_status ON screening_checks(tenant_id, status);

CREATE TABLE screening_hits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    check_id UUID REFERENCES screening_checks(id),
    
    -- Source tracking (CRITICAL for compliance)
    list_id UUID REFERENCES screening_lists(id),
    list_source VARCHAR(100) NOT NULL,
    list_version_id VARCHAR(100) NOT NULL, -- Denormalized for query speed
    
    -- Match details
    hit_type VARCHAR(50) NOT NULL, -- 'sanctions', 'pep', 'adverse_media'
    matched_entity_id VARCHAR(255), -- ID in source list
    matched_name VARCHAR(500),
    confidence DECIMAL(5,2), -- 0-100
    matched_fields VARCHAR(100)[], -- ['name', 'dob', 'country']
    
    -- PEP-specific
    pep_tier INTEGER, -- 1, 2, 3, 4
    pep_position TEXT,
    pep_relationship VARCHAR(100), -- 'direct', 'family', 'associate'
    
    -- Adverse media specific
    article_url TEXT,
    article_title TEXT,
    article_date DATE,
    categories VARCHAR(100)[], -- ['fraud', 'bribery', 'money_laundering']
    
    -- Resolution
    resolution_status VARCHAR(50) DEFAULT 'pending', -- pending, confirmed_true, confirmed_false
    resolution_notes TEXT,
    resolved_by UUID REFERENCES users(id),
    resolved_at TIMESTAMPTZ,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_screening_hits_check ON screening_hits(check_id);
CREATE INDEX idx_screening_hits_resolution ON screening_hits(resolution_status);

-- ============================================
-- CASES
-- ============================================

CREATE TABLE cases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id),
    case_number VARCHAR(50) NOT NULL, -- Human-readable: CASE-2025-001
    
    -- Subject
    applicant_id UUID REFERENCES applicants(id),
    company_id UUID REFERENCES companies(id),
    screening_hit_id UUID REFERENCES screening_hits(id),
    
    -- Case info
    title VARCHAR(500) NOT NULL,
    type VARCHAR(50) NOT NULL, -- 'sanctions', 'pep', 'fraud', 'aml', 'verification'
    priority VARCHAR(20) DEFAULT 'medium', -- critical, high, medium, low
    status VARCHAR(50) DEFAULT 'open', -- open, in_progress, pending_info, resolved, escalated
    
    -- Assignment
    assignee_id UUID REFERENCES users(id),
    escalated_to UUID REFERENCES users(id),
    
    -- Resolution
    resolution VARCHAR(50), -- 'cleared', 'confirmed', 'reported'
    resolution_notes TEXT,
    
    -- Source
    source VARCHAR(100), -- 'screening_hit', 'manual', 'tm_alert'
    source_reference VARCHAR(255),
    
    -- SLA
    due_at TIMESTAMPTZ,
    
    -- Timestamps
    opened_at TIMESTAMPTZ DEFAULT NOW(),
    resolved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(tenant_id, case_number)
);

CREATE INDEX idx_cases_tenant ON cases(tenant_id);
CREATE INDEX idx_cases_status ON cases(tenant_id, status);
CREATE INDEX idx_cases_assignee ON cases(assignee_id);
CREATE INDEX idx_cases_applicant ON cases(applicant_id);
CREATE INDEX idx_cases_due ON cases(tenant_id, due_at) WHERE status IN ('open', 'in_progress');

CREATE TABLE case_notes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID REFERENCES cases(id),
    author_id UUID REFERENCES users(id),
    content TEXT NOT NULL,
    is_ai_generated BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_case_notes_case ON case_notes(case_id);

CREATE TABLE case_attachments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID REFERENCES cases(id),
    document_id UUID REFERENCES documents(id),
    file_name VARCHAR(500),
    storage_path VARCHAR(1000),
    uploaded_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- AI ASSESSMENTS
-- ============================================

CREATE TABLE ai_assessments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id),
    applicant_id UUID REFERENCES applicants(id),
    company_id UUID REFERENCES companies(id),
    case_id UUID REFERENCES cases(id),
    
    -- Assessment type
    type VARCHAR(50) NOT NULL, -- 'risk_summary', 'document_analysis', 'screening_review', 'batch_review'
    
    -- AI output
    model VARCHAR(100) NOT NULL, -- 'claude-sonnet-4-20250514'
    prompt_hash VARCHAR(64), -- For reproducibility
    
    summary TEXT NOT NULL,
    confidence DECIMAL(5,2),
    recommendation VARCHAR(50), -- 'approve', 'reject', 'review', 'escalate'
    
    -- Citations (CRITICAL)
    citations JSONB NOT NULL, -- [{type, source, detail}]
    
    -- Input snapshot (for audit)
    input_data_hash VARCHAR(64),
    
    generated_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_ai_assessments_applicant ON ai_assessments(applicant_id);
CREATE INDEX idx_ai_assessments_case ON ai_assessments(case_id);

-- ============================================
-- AUDIT LOG (Append-only)
-- ============================================

CREATE TABLE audit_log (
    id BIGSERIAL PRIMARY KEY, -- Sequential for ordering
    tenant_id UUID NOT NULL,
    
    -- Actor
    user_id UUID,
    user_email VARCHAR(255),
    ip_address INET,
    user_agent TEXT,
    
    -- Action
    action VARCHAR(100) NOT NULL, -- 'applicant.approved', 'case.created', 'document.uploaded'
    resource_type VARCHAR(50) NOT NULL, -- 'applicant', 'company', 'case', 'document'
    resource_id UUID NOT NULL,
    
    -- Change details
    old_values JSONB,
    new_values JSONB,
    metadata JSONB, -- Additional context
    
    -- Integrity
    checksum VARCHAR(64), -- SHA-256 of (previous_checksum + record)
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Partitioned by month for performance
CREATE INDEX idx_audit_log_tenant_time ON audit_log(tenant_id, created_at DESC);
CREATE INDEX idx_audit_log_resource ON audit_log(resource_type, resource_id);
CREATE INDEX idx_audit_log_user ON audit_log(user_id);

-- ============================================
-- INTEGRATIONS
-- ============================================

CREATE TABLE integrations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id),
    provider VARCHAR(100) NOT NULL, -- 'opensanctions', 'trm', 'chainalysis', 'sumsub'
    
    -- Credentials (encrypted)
    credentials_encrypted BYTEA,
    
    -- Configuration
    config JSONB DEFAULT '{}', -- Provider-specific settings
    field_mappings JSONB DEFAULT '{}',
    
    -- Status
    status VARCHAR(50) DEFAULT 'active', -- active, inactive, error
    last_sync_at TIMESTAMPTZ,
    last_error TEXT,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(tenant_id, provider)
);

-- ============================================
-- EVIDENCE EXPORTS
-- ============================================

CREATE TABLE evidence_exports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id),
    applicant_id UUID REFERENCES applicants(id),
    company_id UUID REFERENCES companies(id),
    case_id UUID REFERENCES cases(id),
    
    -- Export details
    format VARCHAR(20) NOT NULL, -- 'pdf', 'json'
    storage_path VARCHAR(1000),
    file_hash VARCHAR(64), -- SHA-256 for integrity
    
    -- Contents snapshot
    included_items JSONB, -- [{type, id, version}]
    
    -- Metadata
    generated_by UUID REFERENCES users(id),
    generated_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ, -- Optional expiry
    download_count INTEGER DEFAULT 0,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_evidence_exports_applicant ON evidence_exports(applicant_id);
```

---

## Scaling Strategy

### Phase 0: Local Development & MVP (Now)

```
┌─────────────────────────────────────────┐
│           Local / Railway / Render      │
├─────────────────────────────────────────┤
│  Docker Compose (local) OR Railway      │
│  ├── FastAPI (API + Workers combined)   │
│  ├── PostgreSQL                         │
│  ├── Redis                              │
│  └── Local filesystem / Cloudflare R2   │
├─────────────────────────────────────────┤
│  Cloudflare (DNS + CDN + proxy)         │
│  Vercel or Netlify (React frontend)     │
└─────────────────────────────────────────┘
```

**Estimated cost:** $0-50/month
**Why:** Get to market fast. Railway/Render handle SSL, deploys, scaling automatically. No DevOps overhead.

**V1 Simplifications:**
- Skip Elasticsearch → Use PostgreSQL full-text search (`pg_trgm` + `tsvector`)
- Skip Celery → Use `ARQ` (lighter) or FastAPI `BackgroundTasks`
- Skip S3 → Use Cloudflare R2 (S3-compatible, cheaper, no egress fees)
- Skip Kong → FastAPI handles routing fine at this scale

### Phase 1: 0-1000 Tenants (Single Region)

```
┌─────────────────────────────────────────┐
│     Railway Pro / Render Pro / AWS      │
├─────────────────────────────────────────┤
│  Services:                              │
│  ├── API Service (2-4 replicas)         │
│  ├── Worker Service (ARQ workers)       │
│  └── (AI calls are just API requests)   │
├─────────────────────────────────────────┤
│  PostgreSQL (managed)                   │
│  Redis (managed)                        │
│  Cloudflare R2 (documents)              │
│  Cloudflare (CDN + DNS + DDoS)          │
└─────────────────────────────────────────┘
```

**Estimated cost:** $100-500/month
**When to move here:** First paying customers, need reliability guarantees

### Phase 2: 1000-10,000 Tenants (AWS/GCP)

```
┌─────────────────────────────────────────┐
│           Single Cloud Region           │
├─────────────────────────────────────────┤
│  ECS/Cloud Run                          │
│  ├── API Service (2-4 replicas)         │
│  ├── Worker Service (2-4 replicas)      │
│  └── AI Service (2 replicas)            │
├─────────────────────────────────────────┤
│  RDS/Cloud SQL PostgreSQL               │
│  ElastiCache/Memorystore Redis          │
│  S3 (documents)                         │
│  OpenSearch (if needed for search)      │
└─────────────────────────────────────────┘
```

**Estimated cost:** $2-4k/month
**When to move here:** Enterprise customers, SOC 2 requirements, need fine-grained control

**Key optimizations:**
- Database partitioning (audit_log by month, applicants by tenant)
- Connection pooling (PgBouncer)
- Aggressive caching (screening results, workflow configs)
- Async everything possible

### Phase 3: 10,000+ Tenants (Multi-Region)

- Multi-region active-passive (or active-active for reads)
- Tenant sharding if needed
- Dedicated infrastructure for large enterprise tenants
- Consider tenant isolation (separate databases) for enterprise
- Kong or similar API gateway for multi-tenant API management

---

## Key Architectural Decisions

### 1. Multi-Tenancy Approach

**Row-level security (RLS) in PostgreSQL:**

```sql
-- Enable RLS
ALTER TABLE applicants ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see their tenant's data
CREATE POLICY tenant_isolation ON applicants
    USING (tenant_id = current_setting('app.current_tenant_id')::UUID);
```

Every API request sets `app.current_tenant_id` before queries run.

### 2. Document Storage

- **S3** with server-side encryption (SSE-S3 or SSE-KMS)
- Path structure: `/{tenant_id}/{resource_type}/{resource_id}/{document_id}`
- Presigned URLs for uploads/downloads (never expose raw S3)
- Lifecycle policies: move to Glacier after 7 years

### 3. AI Integration Pattern

```python
# AI calls are always async jobs
class AIAssessmentJob:
    def run(self, applicant_id: UUID, assessment_type: str):
        # 1. Gather context
        applicant = get_applicant(applicant_id)
        documents = get_documents(applicant_id)
        screening = get_screening_results(applicant_id)
        
        # 2. Build prompt with citations
        prompt = build_assessment_prompt(
            applicant=applicant,
            documents=documents,
            screening=screening,
            assessment_type=assessment_type
        )
        
        # 3. Call Claude
        response = claude_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        # 4. Store with full provenance
        ai_assessment = AIAssessment(
            applicant_id=applicant_id,
            type=assessment_type,
            model="claude-sonnet-4-20250514",
            prompt_hash=hash(prompt),
            summary=response.content,
            citations=extract_citations(response),
            input_data_hash=hash(json.dumps(context))
        )
        save(ai_assessment)
```

### 4. Screening Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    SCREENING FLOW                            │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ List Sync    │    │ On-Demand    │    │ Ongoing      │
│ (Scheduled)  │    │ Check        │    │ Monitoring   │
└──────────────┘    └──────────────┘    └──────────────┘
        │                     │                     │
        ▼                     ▼                     ▼
┌─────────────────────────────────────────────────────────────┐
│               SCREENING ENGINE                               │
│                                                              │
│  1. Normalize input (name variants, transliteration)        │
│  2. Query local list cache (PostgreSQL + trigram index)     │
│  3. Score matches (fuzzy matching, field weights)           │
│  4. Return hits with confidence + list_version_id           │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│               AI DISAMBIGUATION                              │
│                                                              │
│  For hits > 60% confidence, AI reviews:                     │
│  - Name similarity analysis                                  │
│  - DOB/country correlation                                   │
│  - Recommends: confirm/clear/human review                   │
└─────────────────────────────────────────────────────────────┘
```

### 5. Audit Log Integrity

Chain hashing for tamper evidence:

```python
def create_audit_entry(entry: AuditLogEntry) -> AuditLogEntry:
    # Get previous entry's checksum
    previous = get_latest_audit_entry(entry.tenant_id)
    previous_checksum = previous.checksum if previous else "GENESIS"
    
    # Create chain
    payload = f"{previous_checksum}|{entry.to_json()}"
    entry.checksum = sha256(payload)
    
    save(entry)
    return entry
```

---

## API Service Structure

```
getclearance-api/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app
│   ├── config.py               # Settings (pydantic-settings)
│   ├── dependencies.py         # Dependency injection
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── applicants.py
│   │   │   ├── companies.py
│   │   │   ├── screening.py
│   │   │   ├── cases.py
│   │   │   ├── workflows.py
│   │   │   ├── evidence.py
│   │   │   ├── integrations.py
│   │   │   └── webhooks.py
│   │   └── router.py
│   │
│   ├── models/                 # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── tenant.py
│   │   ├── applicant.py
│   │   ├── company.py
│   │   ├── document.py
│   │   ├── screening.py
│   │   ├── case.py
│   │   └── audit.py
│   │
│   ├── schemas/                # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── applicant.py
│   │   ├── company.py
│   │   └── ...
│   │
│   ├── services/               # Business logic
│   │   ├── __init__.py
│   │   ├── applicant_service.py
│   │   ├── screening_service.py
│   │   ├── ai_service.py
│   │   ├── evidence_service.py
│   │   └── notification_service.py
│   │
│   ├── workers/                # Async jobs
│   │   ├── __init__.py
│   │   ├── screening_worker.py
│   │   ├── list_sync_worker.py
│   │   ├── ai_assessment_worker.py
│   │   └── evidence_export_worker.py
│   │
│   └── utils/
│       ├── __init__.py
│       ├── auth.py
│       ├── encryption.py
│       └── audit.py
│
├── migrations/                 # Alembic
├── tests/
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

---

## Recommended Tech Stack Summary

### V1 (MVP) Stack - Start Here

| Layer | Technology | Why |
|-------|------------|-----|
| **Frontend** | React + Vite | Already built, fast dev experience |
| **Frontend Hosting** | Vercel or Netlify | Free tier, auto deploys from GitHub |
| **API** | FastAPI | Async, fast, great typing, auto OpenAPI |
| **Database** | PostgreSQL 15+ | JSONB, RLS, full-text search built-in |
| **Cache/Queue** | Redis | Session cache, rate limiting, job queues |
| **Task Queue** | ARQ | Lighter than Celery, Redis-native, async |
| **Search** | PostgreSQL pg_trgm | Skip Elasticsearch for V1, Postgres handles it |
| **Object Storage** | Cloudflare R2 | S3-compatible, no egress fees, cheap |
| **AI** | Claude API | Risk summaries, document analysis |
| **OCR** | AWS Textract or Google Vision | Pay-per-use, no infrastructure |
| **Backend Hosting** | Railway or Render | One-click Postgres + Redis, auto SSL |
| **DNS/CDN** | Cloudflare | Free tier, DDoS protection, fast |

### Production Stack (When You Scale)

| Layer | Technology | Why |
|-------|------------|-----|
| **API** | FastAPI | Same as V1 |
| **Database** | PostgreSQL (RDS/Cloud SQL) | Managed, backups, read replicas |
| **Cache/Queue** | Redis (ElastiCache) | Managed, clustered |
| **Task Queue** | ARQ or Celery | Scale workers independently |
| **Search** | OpenSearch (if needed) | Full-text search at scale |
| **Object Storage** | S3 | Enterprise, lifecycle policies |
| **Monitoring** | Datadog or Grafana Cloud | Metrics, logs, traces |
| **Infrastructure** | AWS ECS or GCP Cloud Run | Containers, auto-scaling |
| **API Gateway** | Kong (if needed) | Multi-tenant API key management |

---

## Security Considerations

1. **Encryption at rest** - Managed DB encryption, R2/S3 SSE, encrypted credentials
2. **Encryption in transit** - TLS everywhere (Railway/Render handle this)
3. **PII handling** - Consider field-level encryption for sensitive data
4. **Access control** - RBAC with row-level security
5. **Audit everything** - Immutable, chain-hashed audit log
6. **SOC 2 readiness** - Design with compliance in mind from day 1
7. **Data residency** - Plan for regional data storage requirements

---

*Architecture document created: November 28, 2025*
*Updated: Added Phase 0 (MVP) deployment path with Railway/Render*
