# SignalWeave Engineering Context & Standards

**Purpose:** This document provides essential context for engineers and AI assistants working on SignalWeave, an AI-native KYC/AML compliance platform competing with Sumsub and Persona.

**Core Differentiator:** Deep AI integration throughout the compliance workflow (not AI as an add-on), enabling faster approvals, intelligent document processing, automated risk assessment, and superior UX.

---

## Table of Contents

1. [Platform Overview](#platform-overview)
2. [Core Technical Stack](#core-technical-stack)
3. [Required Knowledge Areas](#required-knowledge-areas)
4. [Reference Documentation](#reference-documentation)
5. [Internal Standards](#internal-standards)
6. [Code Generation Guidelines](#code-generation-guidelines)

---

## Platform Overview

### Architecture Principles

- **Multi-tenant from day one**: All data tables use Row Level Security (RLS) with `current_setting('app.current_tenant_id')`
- **AI-first design**: Claude API integration for document fraud detection, natural language risk assessments, and intelligent matching
- **Audit-everything**: Append-only `audit_log` with chain hashing for regulatory compliance
- **Async by default**: Long-running tasks (OCR, screening, AI analysis) run in background workers
- **US-market specialization**: Initial focus on US regulations before global expansion

### Core Data Model

```
Tenant
  └─ Workflow (versioned)
      └─ Applicant
          ├─ Applicant Steps
          ├─ Documents
          │   ├─ OCR data
          │   └─ Fraud signals
          ├─ Screening Checks
          │   └─ Screening Hits
          ├─ Cases (when issues found)
          │   ├─ AI Assessments
          │   └─ Case Actions
          └─ Evidence Exports
```

**Key Tables:**
- `applicants` - Individual KYC subjects
- `companies` - KYB business entities
- `company_persons` - UBOs/officers linked to companies
- `applicant_steps` - Workflow progression tracking
- `documents` - ID docs, proof of address, etc.
- `screening_checks` - Sanctions, PEP, adverse media checks
- `screening_hits` - Potential matches requiring review
- `cases` - Items requiring compliance review
- `ai_assessments` - AI-generated risk summaries with citations
- `evidence_exports` - Audit trail PDFs with provenance
- `audit_log` - Immutable event log with chain hashing

---

## Core Technical Stack

### Backend: FastAPI + PostgreSQL + Redis

**FastAPI Requirements:**
- Modular router design: separate routers for `applicants`, `screening`, `cases`, `workflows`, `evidence`
- Dependency injection for tenant context and auth
- Pydantic models for all request/response validation
- Automatic OpenAPI schema generation
- Background tasks via ARQ/Celery for long-running operations

**PostgreSQL Requirements:**
- Row Level Security (RLS) on ALL tenant tables using `current_setting('app.current_tenant_id')`
- JSONB for flexible configs: `workflow_versions.config`, `risk_factors`, `verification_checks`
- Full-text search indexes on names, addresses, document text
- Indexes for SLA queues: `sla_due_at`, `status`
- Trigram indexes for fuzzy name matching in screening

**Redis + Task Queue (ARQ):**
- Pub/sub for real-time updates
- Task queues for: OCR processing, AI analysis, screening, evidence export
- Scheduled jobs: sanctions list syncs, ongoing monitoring
- Retry logic with exponential backoff and dead-letter queues

### Frontend: React + Claude API Integration

**React Component Library:**
- `AppShell` - Main layout with navigation
- `Dashboard` - Metrics and SLA overview
- `ApplicantsList` - Searchable, filterable table
- `ApplicantDetail` - Full applicant view with timeline
- `ScreeningChecks` - Results visualization
- `CaseManagement` - Review queue and case details
- `ApplicantAssistant` - AI-powered onboarding helper

**Claude API Integration Points:**
- Document fraud detection and translation
- Natural language risk assessments
- Sanctions matching disambiguation
- Evidence pack generation with citations
- Batch review intelligence

### Storage & External Services

- **R2/S3**: Document storage with presigned URLs
- **OpenSanctions API**: Primary sanctions/PEP screening data source
- **AWS Textract / Google Vision**: OCR for document extraction
- **Liveness Provider**: (Facetec/Onfido) for selfie verification
- **Crypto Providers**: TRM/Chainalysis for blockchain risk

---

## Required Knowledge Areas

### 1. Identity Verification Platform Behavior

**Study these platforms to understand end-to-end flows:**

**Sumsub Documentation:**
- [API Overview & Get Started](https://docs.sumsub.com/reference/about-sumsub-api) - Core verification flow, applicants, document upload, statuses, callbacks
- [ID Verification](https://docs.sumsub.com/docs/identity-verification) - Document fraud vectors, liveness checks, verification types
- [Reusable KYC](https://docs.sumsub.com/docs/reusable-kyc) - Share tokens, list versions, ongoing monitoring
- [Add Verification Documents](https://docs.sumsub.com/reference/add-verification-documents) - Multipart upload patterns, metadata schemas

**Persona Documentation:**
- [API Introduction](https://docs.withpersona.com/api-introduction) - Inquiry lifecycle, templates, webhooks, evidence
- [Government ID Verification via API](https://docs.withpersona.com/integration-guide-gov-id-via-api) - Field requirements, error patterns, edge cases

**Engineers Must Know:**
- How to sketch the complete "Applicant Journey" from memory
- State transitions: `pending → in_progress → needs_resubmission → approved/rejected`
- How these concepts map to our tables: `applicants`, `applicant_steps`, `documents`, `screening_checks`, etc.

### 2. Backend Stack Expertise

**FastAPI:**
- [Official Docs](https://fastapi.tiangolo.com/) - Complete tutorial series
- **Critical Skills:**
  - Dependency injection for tenant + auth context
  - Pydantic models for validation
  - Background tasks vs external workers
  - OpenAPI schema versioning

**PostgreSQL Multi-Tenancy:**
- [Row Security Policies](https://www.postgresql.org/docs/current/ddl-rowsecurity.html) - Official RLS documentation
- [Neon RLS Guide](https://neon.com/postgresql/postgresql-administration/postgresql-row-level-security) - Practical multi-tenant patterns
- [Supabase RLS Docs](https://supabase.com/docs/guides/database/postgres/row-level-security) - Examples and gotchas

**Critical Skills:**
- Implementing RLS with `current_setting('app.current_tenant_id')`
- Debugging RLS issues and join leakage
- JSONB indexing strategies
- Full-text search configuration

**Task Queues:**
- ARQ or Celery documentation
- **Critical Skills:**
  - Designing idempotent tasks
  - Retry strategies with backoff
  - Monitoring queue health

### 3. Screening & Data Providers

**OpenSanctions:**
- [Public API](https://publicapi.dev/open-sanctions-api) - Query patterns, matching, filters
- [GitHub Repository](https://github.com/opensanctions/opensanctions) - Entity normalization, deduplication, versioning

**Critical Skills:**
- Syncing list versions into `screening_lists` table
- Maintaining `list_version_id` + `checksum` integrity
- Designing local matching engine (Postgres trigram)
- Scoring and disambiguation logic

**Crypto/Blockchain Providers:**
- TRM/Chainalysis REST APIs
- Address risk checks, wallet entity risk
- Transaction monitoring webhooks
- Mapping alerts to `screening_checks` and `cases`

### 4. Document Processing & Liveness

**OCR & Vision:**
- AWS Textract and Google Vision documentation
- **Focus Areas:**
  - ID document extraction (blocks, lines, bounding boxes)
  - Rate limits and async job patterns
  - Multi-language and low-quality scan handling
- **Schema Mapping:** `documents.extracted_data`, `ocr_text`, `ocr_confidence`, `fraud_signals`

**Face Match & Liveness:**
- Passive vs active liveness concepts
- Face embedding similarity (cosine distance, thresholds)
- Presentation attack detection (screens, masks, printouts)
- **Implementation:** Video/selfie capture → worker processing → minimal biometric storage

### 5. Audit & Compliance

**Critical Understanding:**
- `audit_log` design: append-only, chain-hashed
- `evidence_exports` and `ai_assessments`: decision reconstruction
- Immutability, time synchronization, idempotency
- Chain hashing implementation and tamper detection

---

## Reference Documentation

### API Design Standards

- Use Sumsub/Persona API structures as inspiration
- Well-typed, versioned APIs with clear error semantics
- Comprehensive OpenAPI documentation
- Consistent error response format

### Storage & Lifecycle

**S3/R2 Patterns:**
- Presigned URLs for secure uploads
- Bucket policies and KMS/SSE encryption
- Lifecycle rules (e.g., archive to Glacier after N years)

**Billing:**
- Stripe integration for per-verification metering
- Usage tracking and reporting

---

## Internal Standards

### 1. Platform Concept Model

**Object Relationships:**
```
Tenant → Workflow → Applicant → Steps → Documents → Screening Checks → Screening Hits → Case → AI Assessments → Evidence Export
```

**Applicant State Machine:**
```
pending
  ↓
in_progress
  ↓
[screening/checks running]
  ↓
needs_resubmission ←──┐
  ↓                   │
under_review          │
  ↓                   │
approved/rejected     │
  │                   │
  └───────────────────┘ (if issues found)
```

**Workflow Version Handling:**
- New applicants use latest workflow version
- In-flight applicants continue on their original version
- Version upgrades require explicit migration

### 2. End-to-End Flow Documentation

**KYC Individual Flow:**
1. Client creates applicant via API
2. Mobile/Web SDK captures documents + selfie
3. Background jobs triggered:
   - OCR extraction (Textract/Vision)
   - Liveness check (Facetec/Onfido)
   - Screening checks (OpenSanctions)
   - AI risk summary (Claude API)
4. Results stored in respective tables
5. Workflow step updated
6. SLA monitoring initiated
7. Webhook callbacks to client
8. If issues → create case
9. If approved → evidence export available

**KYB Business Flow:**
1. Company record created
2. UBOs/officers added to `company_persons`
3. Each officer linked to individual `applicant`
4. Parallel screening of company + all persons
5. Aggregate risk assessment
6. Case creation if any hits/issues
7. Approval requires all persons cleared

**Screening & Ongoing Monitoring:**
1. Initial screening at application submission
2. Scheduled list syncs (daily/weekly)
3. Ongoing monitoring for existing approved applicants
4. New hits create/update cases
5. Automatic re-screening on workflow triggers

### 3. Security & Privacy Guidelines

**Never Log:**
- Full document images in application logs
- Biometric templates or face embeddings
- Raw OCR text containing PII in debug logs
- API keys or authentication tokens

**Data Retention:**
- ID documents: 7 years (configurable per tenant/jurisdiction)
- Biometric data: Minimum necessary, 90 days default
- Audit logs: Permanent
- Evidence exports: Permanent

**Encryption Requirements:**
- Database: Encryption at rest for all PII columns
- Object storage: SSE-KMS for R2/S3 buckets
- In transit: TLS 1.3 minimum
- API keys: Hashed with bcrypt/argon2

**Data Residency:**
- Respect tenant `data_residency_region` flag
- Route to appropriate R2/S3 bucket
- Log storage region in audit trail

### 4. AI Integration Standards

**Claude API Call Structure:**

```python
# Standard pattern for AI assessments
ai_request = {
    "model": "claude-sonnet-4-20250514",
    "max_tokens": 2000,
    "messages": [
        {
            "role": "user",
            "content": f"""
Analyze this applicant data for KYC risk:

Name: {applicant.full_name}
DOB: {applicant.date_of_birth}
Screening Results: {screening_summary}
Document Analysis: {document_fraud_signals}

Provide:
1. Risk level (Low/Medium/High)
2. Key risk factors with specific citations
3. Recommended next actions

Format as JSON.
"""
        }
    ]
}
```

**Required Fields in `ai_assessments`:**
```python
{
    "model_name": "claude-sonnet-4-20250514",
    "prompt_hash": "sha256(prompt_text)",
    "input_hash": "sha256(applicant_data)",
    "assessment_type": "risk_summary",
    "risk_level": "medium",
    "risk_factors": [...],  # JSONB with citations
    "recommendations": [...],
    "confidence_score": 0.87,
    "created_at": "timestamp"
}
```

**Guardrails:**
- Maximum 4000 tokens per call
- Timeout: 30 seconds
- Retry: 3 attempts with exponential backoff
- Redaction: Remove PII before logging prompts
- Rate limiting: 100 requests/minute per tenant
- Cost tracking: Log token usage per assessment

**Citation Requirements:**
- All risk factors must cite specific data points
- Include source document IDs
- Timestamp when data was captured
- Track which screening list version was used

---

## Code Generation Guidelines

When generating code for SignalWeave, **always**:

### Database Operations

1. **Include tenant context:**
```python
# Good
await db.execute(
    "SET LOCAL app.current_tenant_id = :tenant_id",
    {"tenant_id": tenant_id}
)
result = await db.fetch_all("SELECT * FROM applicants")

# Bad - missing tenant context
result = await db.fetch_all("SELECT * FROM applicants")
```

2. **Use JSONB appropriately:**
```python
# Good - structured JSONB
verification_checks = {
    "document_check": {
        "status": "passed",
        "confidence": 0.95,
        "fraud_signals": []
    },
    "liveness_check": {
        "status": "passed",
        "confidence": 0.89
    }
}

# Good - JSONB query
await db.fetch_all(
    """
    SELECT * FROM applicants 
    WHERE verification_checks->>'document_check'->>'status' = 'passed'
    """
)
```

3. **Always create audit log entries:**
```python
# Good
await create_audit_log_entry(
    tenant_id=tenant_id,
    entity_type="applicant",
    entity_id=applicant_id,
    action="status_change",
    actor_id=user_id,
    old_value=old_status,
    new_value=new_status,
    metadata={"reason": "screening_completed"}
)
```

### API Endpoints

1. **Use dependency injection:**
```python
# Good
@router.post("/applicants")
async def create_applicant(
    request: ApplicantCreate,
    tenant: Tenant = Depends(get_current_tenant),
    db: Database = Depends(get_db)
):
    # Implementation
```

2. **Return consistent error format:**
```python
# Good
from fastapi import HTTPException

raise HTTPException(
    status_code=422,
    detail={
        "error_code": "INVALID_DOCUMENT",
        "message": "Document quality too low for OCR",
        "field": "document_image",
        "applicant_id": applicant_id
    }
)
```

3. **Version your APIs:**
```python
# Good
@router.post("/v1/applicants")
async def create_applicant_v1(...):
    pass

@router.post("/v2/applicants")
async def create_applicant_v2(...):
    pass
```

### Background Tasks

1. **Make tasks idempotent:**
```python
# Good
async def process_document(document_id: str):
    # Check if already processed
    existing = await db.fetch_one(
        "SELECT * FROM documents WHERE id = :id AND ocr_status = 'completed'",
        {"id": document_id}
    )
    if existing:
        return existing
    
    # Process...
```

2. **Include comprehensive error handling:**
```python
# Good
from arq import Retry

async def run_screening(applicant_id: str) -> None:
    try:
        await opensanctions_check(applicant_id)
    except RateLimitError:
        raise Retry(defer=timedelta(seconds=60))
    except TemporaryError as e:
        raise Retry(defer=timedelta(seconds=30))
    except PermanentError as e:
        await mark_screening_failed(applicant_id, str(e))
```

### React Components

1. **Follow established component patterns:**
```jsx
// Good - matches existing component library
import { Card, Badge, Timeline } from '@/components/ui';

export function ApplicantDetail({ applicantId }) {
  const { data, isLoading } = useApplicant(applicantId);
  
  if (isLoading) return <LoadingSpinner />;
  
  return (
    <div className="space-y-6">
      <Card>
        <ApplicantHeader applicant={data} />
      </Card>
      <Card>
        <Timeline steps={data.steps} />
      </Card>
    </div>
  );
}
```

2. **Use Claude API integration pattern:**
```jsx
// Good - standard pattern for AI features
const handleAIAnalysis = async () => {
  const response = await fetch('/api/v1/ai/analyze-document', {
    method: 'POST',
    body: JSON.stringify({
      document_id: documentId,
      analysis_type: 'fraud_detection'
    })
  });
  
  const { assessment_id } = await response.json();
  // Poll or subscribe for results
};
```

### Testing Requirements

1. **Test RLS isolation:**
```python
# Good
async def test_tenant_isolation():
    tenant_a_id = "tenant-a"
    tenant_b_id = "tenant-b"
    
    # Create applicants for both tenants
    await create_applicant(tenant_a_id, "Alice")
    await create_applicant(tenant_b_id, "Bob")
    
    # Verify tenant A can't see tenant B's data
    await db.execute("SET LOCAL app.current_tenant_id = :id", {"id": tenant_a_id})
    results = await db.fetch_all("SELECT * FROM applicants")
    assert len(results) == 1
    assert results[0]['full_name'] == "Alice"
```

2. **Test idempotency:**
```python
# Good
async def test_duplicate_screening():
    applicant_id = "test-applicant"
    
    # Run screening twice
    result1 = await run_screening(applicant_id)
    result2 = await run_screening(applicant_id)
    
    # Should return same result, not create duplicates
    assert result1['screening_id'] == result2['screening_id']
    
    # Verify only one screening record exists
    count = await db.fetch_val(
        "SELECT COUNT(*) FROM screening_checks WHERE applicant_id = :id",
        {"id": applicant_id}
    )
    assert count == 1
```

---

## Quick Reference Checklist

When implementing any feature, ensure:

- [ ] RLS context is set for all DB queries
- [ ] Audit log entry is created for state changes
- [ ] Background tasks are idempotent
- [ ] API responses match OpenAPI schema
- [ ] Error responses follow standard format
- [ ] PII is encrypted at rest
- [ ] Document retention policies are respected
- [ ] AI assessments include required fields
- [ ] Tenant isolation is tested
- [ ] Webhook callbacks are queued
- [ ] SLA monitoring is triggered
- [ ] Evidence trail is maintained

---

## Key Architecture References

Throughout this document, items marked **ARCHITECTURE** refer to detailed specifications in the main architecture document. When implementing features:

1. Check the architecture doc for exact table schemas
2. Verify index requirements
3. Confirm JSONB structure expectations
4. Review RLS policy definitions
5. Validate workflow state machine logic

---

## Document Updates

This document should be updated when:
- New external APIs are integrated
- Internal standards change
- New workflow types are added
- Security/privacy requirements evolve
- AI integration patterns are enhanced

**Last Updated:** [Current Date]
**Maintainer:** Engineering Lead
**Review Cycle:** Quarterly
