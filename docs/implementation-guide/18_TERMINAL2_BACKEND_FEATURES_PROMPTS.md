# Terminal 2: Backend Features Sprint Prompts
**Purpose:** Copy-paste prompts for backend feature sprints (F1-F6)
**Run in parallel with:** Terminal 1 (Security) or Terminal 3 (Frontend)

---

## ✅ ALL SPRINTS COMPLETE (December 2, 2025)

All Terminal 2 Backend Features (F1-F6) have been fully implemented.

## Sprint Overview

| Sprint | Feature | Duration | Status | Files Created |
|--------|---------|----------|--------|---------------|
| **F1** | Ongoing AML Monitoring | 3-4 days | ✅ COMPLETE | `models/monitoring_alert.py`, `services/monitoring.py`, `workers/monitoring_worker.py`, `api/v1/monitoring.py` |
| **F2** | KYB/Companies Module | 5-7 days | ✅ COMPLETE | `models/company.py`, `schemas/company.py`, `services/kyb_screening.py`, `api/v1/companies.py` |
| **F3** | Risk Workflows | 2-3 days | ✅ COMPLETE | `models/workflow.py`, `services/risk_engine.py`, `api/v1/workflows.py` |
| **F4** | Questionnaires | 3-4 days | ✅ COMPLETE | `models/questionnaire.py`, `api/v1/questionnaires.py`, 8 default templates |
| **F5** | Address Verification | 2-3 days | ✅ COMPLETE | `services/address_verification.py`, `api/v1/addresses.py` |
| **F6** | Liveness Detection | 2-3 days | ✅ COMPLETE | `services/biometrics.py`, `api/v1/biometrics.py`, biometrics fields on documents |

**Total: 17-24 days** - ALL COMPLETE

### Implementation Details

**F1 - Ongoing AML Monitoring:**
- MonitoringAlert model with status, severity, resolution tracking
- Batch re-screening service with comparison to previous results
- ARQ worker for daily/configurable monitoring runs
- API: enable/disable monitoring, list/resolve alerts, stats

**F2 - KYB/Companies Module:**
- Company model with legal info, addresses, screening status
- BeneficialOwner model with ownership %, roles, verification status
- CompanyDocument model for corporate docs
- KYB screening service for company + all UBOs
- Full CRUD API with UBO management

**F3 - Risk Workflows:**
- WorkflowRule model with conditions and actions (JSONB)
- Risk engine with weighted scoring (AML 40%, Document 20%, Country 15%, Address 10%, Identity 10%, Device 5%)
- Auto-approve/manual-review/auto-reject based on risk
- FATF grey/black list country detection
- Workflow CRUD API

**F4 - Questionnaires:**
- Questionnaire model with JSONB questions array
- QuestionnaireResponse model with answers and calculated risk
- 8 default templates: Source of Funds, PEP Declaration, Tax Residency, Crypto Source of Funds, Crypto Transaction Purpose, Fintech Account Purpose, Business Account - Fintech, Enhanced Due Diligence
- Risk score calculation from answer risk_scores
- Full CRUD API with response submission

**F5 - Address Verification:**
- AddressVerificationService with Smarty API (US + international)
- Basic fallback validation when API unavailable
- FATF high-risk countries list (Afghanistan, Belarus, Cuba, Iran, North Korea, etc.)
- Address risk scoring integrated into risk engine
- API: verify address, verify applicant address, list high-risk countries

**F6 - Liveness Detection:**
- BiometricsService placeholder for AWS Rekognition
- Face comparison (ID photo vs selfie) with similarity threshold
- Liveness detection (photo of photo detection)
- Face detection with quality metrics
- Biometric fields on documents table (face_match_score, liveness_score, biometrics_checked_at, verification_result)
- Migration for new fields

---

## Prompts Below (For Reference Only - All Implemented)

---

## Files to Upload for ALL Sprints

Before ANY sprint, upload these context files:

```
backend/app/models/applicant.py    # Model patterns
backend/app/services/screening.py  # Service patterns
backend/app/api/v1/applicants.py   # API patterns
backend/app/config.py              # Settings
README.md
```

---

## Sprint F1: Ongoing AML Monitoring (3-4 Days)

### Why This Sprint?
Sumsub offers continuous AML monitoring - daily re-screening of approved applicants against updated sanctions lists. Currently we only screen once at verification time.

### Files to Upload:
1. `backend/app/services/screening.py` - Existing screening service
2. `backend/app/models/screening.py` - Screening models
3. `backend/app/models/applicant.py` - Has `monitoring_enabled` field
4. `backend/app/workers/screening_worker.py` - Worker patterns
5. `backend/app/api/v1/screening.py` - Screening endpoints

### Prompt (Copy This):

```
# CHAT TITLE: Backend Sprint F1 - Ongoing AML Monitoring

## Context
I'm building GetClearance, an AI-native KYC/AML platform. We have AML screening working for initial verification, but we need ONGOING monitoring - daily re-screening of approved applicants against updated sanctions/PEP lists.

## What Exists (Read the uploaded files first)
1. **screening.py (service)** - OpenSanctions integration, fuzzy matching
2. **screening.py (models)** - ScreeningCheck, ScreeningHit models
3. **applicant.py** - Has `monitoring_enabled: bool` field (not used yet)
4. **screening_worker.py** - Background job patterns
5. **screening.py (api)** - Screening endpoints

**Current state:**
- One-time screening works via `screen_applicant()` function
- `monitoring_enabled` field exists but does nothing
- No re-screening or alert system

## What I Need You To Do

### Part 1: Create Monitoring Service

**File to create:** `backend/app/services/monitoring.py`

**Requirements:**
1. `enable_monitoring(applicant_id)` - Enable for approved applicant
2. `disable_monitoring(applicant_id)` - Disable monitoring
3. `run_monitoring_batch()` - Re-screen all enabled applicants
4. `check_for_new_hits(applicant_id)` - Compare current vs previous screening
5. `create_monitoring_alert(applicant_id, new_hits)` - Create alert record

**Pattern to follow from screening.py:**
```python
async def run_monitoring_batch(db: AsyncSession) -> dict:
    """
    Re-screen all applicants with monitoring_enabled=True.
    Called by scheduled worker (daily).

    Returns:
        {
            "screened": 150,
            "new_alerts": 3,
            "errors": 0
        }
    """
    # Get all applicants with monitoring enabled
    applicants = await db.execute(
        select(Applicant).where(
            Applicant.monitoring_enabled == True,
            Applicant.status == "approved"
        )
    )

    results = {"screened": 0, "new_alerts": 0, "errors": 0}

    for applicant in applicants.scalars():
        try:
            # Re-run screening
            new_results = await screen_person(
                full_name=f"{applicant.first_name} {applicant.last_name}",
                date_of_birth=applicant.date_of_birth,
                nationality=applicant.nationality
            )

            # Compare with previous screening
            # If new hits found, create alert
            ...

            results["screened"] += 1
        except Exception as e:
            results["errors"] += 1

    return results
```

### Part 2: Create Monitoring Alert Model

**File to create:** `backend/app/models/monitoring_alert.py`

```python
class MonitoringAlert(Base):
    __tablename__ = "monitoring_alerts"

    id: Mapped[UUID]
    tenant_id: Mapped[UUID]
    applicant_id: Mapped[UUID]  # FK to applicants

    alert_type: Mapped[str]  # 'new_hit', 'upgraded_risk', 'list_update'
    severity: Mapped[str]  # 'high', 'medium', 'low'

    previous_screening_id: Mapped[UUID | None]
    new_screening_id: Mapped[UUID]

    new_hits: Mapped[list]  # JSONB - list of new hit IDs

    status: Mapped[str]  # 'open', 'reviewing', 'resolved', 'dismissed'
    resolved_by: Mapped[UUID | None]
    resolved_at: Mapped[datetime | None]
    resolution_notes: Mapped[str | None]

    created_at: Mapped[datetime]
```

### Part 3: Create Monitoring Worker

**File to create:** `backend/app/workers/monitoring_worker.py`

**Requirements:**
1. Scheduled job that runs daily (configurable)
2. Calls `run_monitoring_batch()`
3. Sends webhook for new alerts
4. Logs results

### Part 4: Add API Endpoints

**File to update:** `backend/app/api/v1/screening.py`

**New endpoints:**
```
POST /api/v1/applicants/{id}/monitoring/enable   - Enable monitoring
POST /api/v1/applicants/{id}/monitoring/disable  - Disable monitoring
GET  /api/v1/monitoring/alerts                   - List all alerts
GET  /api/v1/monitoring/alerts/{id}              - Get alert details
POST /api/v1/monitoring/alerts/{id}/resolve      - Resolve alert
GET  /api/v1/monitoring/stats                    - Monitoring statistics
```

### Part 5: Create Migration

**File to create:** `backend/migrations/versions/YYYYMMDD_add_monitoring_alerts.py`

Add the monitoring_alerts table.

## Success Criteria
1. Can enable/disable monitoring per applicant
2. Batch re-screening finds new hits
3. Alerts created when new hits found
4. API endpoints work
5. Worker can be scheduled

## Do NOT:
- Modify the core screening logic (it works)
- Change existing models (add new ones)
- Remove any existing functionality
```

---

## Sprint F2: KYB/Companies Module (5-7 Days)

### Why This Sprint?
Sumsub offers business verification (KYB) - verifying companies, their beneficial owners (UBOs), and corporate structure. This is a core product feature.

### Files to Upload:
1. `backend/app/models/applicant.py` - Model patterns to follow
2. `backend/app/api/v1/applicants.py` - API patterns to follow
3. `backend/app/services/screening.py` - For company screening
4. `backend/app/schemas/applicant.py` - Schema patterns

### Prompt (Copy This):

```
# CHAT TITLE: Backend Sprint F2 - KYB/Companies Module

## Context
I'm building GetClearance, an AI-native KYC/AML platform. We have individual KYC working, but we need KYB (Know Your Business) - verifying companies and their beneficial owners.

## What Exists (Read the uploaded files first)
1. **applicant.py (model)** - Pattern for Company model
2. **applicants.py (api)** - Pattern for Company API
3. **screening.py** - Can screen company names too
4. **applicant.py (schema)** - Pattern for Company schemas

**Current state:**
- Individual verification works
- No company/business verification
- Placeholder CompaniesPage.jsx exists in frontend

## What I Need You To Do

### Part 1: Create Company Models

**File to create:** `backend/app/models/company.py`

```python
from sqlalchemy import String, Date, ForeignKey, Text, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

class CompanyStatus(str, enum.Enum):
    PENDING = "pending"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"

class Company(Base):
    __tablename__ = "companies"

    id: Mapped[UUID]
    tenant_id: Mapped[UUID]  # FK to tenants
    external_id: Mapped[str | None]  # Customer's reference

    # Company info
    legal_name: Mapped[str]
    trading_name: Mapped[str | None]
    registration_number: Mapped[str | None]
    tax_id: Mapped[str | None]
    incorporation_date: Mapped[date | None]
    incorporation_country: Mapped[str | None]  # ISO 3166-1 alpha-2
    legal_form: Mapped[str | None]  # LLC, Corp, Ltd, etc.

    # Address
    registered_address: Mapped[dict | None]  # JSONB
    business_address: Mapped[dict | None]  # JSONB

    # Contact
    website: Mapped[str | None]
    email: Mapped[str | None]
    phone: Mapped[str | None]

    # Status
    status: Mapped[CompanyStatus]
    risk_level: Mapped[str | None]  # low, medium, high

    # Screening
    screening_status: Mapped[str | None]
    last_screened_at: Mapped[datetime | None]

    # Relationships
    beneficial_owners: Mapped[list["BeneficialOwner"]] = relationship(back_populates="company")
    documents: Mapped[list["CompanyDocument"]] = relationship(back_populates="company")

    # Timestamps
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]
    reviewed_at: Mapped[datetime | None]
    reviewed_by: Mapped[UUID | None]


class BeneficialOwner(Base):
    __tablename__ = "beneficial_owners"

    id: Mapped[UUID]
    company_id: Mapped[UUID]  # FK to companies
    applicant_id: Mapped[UUID | None]  # FK to applicants (if linked to KYC)

    # Person info
    full_name: Mapped[str]
    date_of_birth: Mapped[date | None]
    nationality: Mapped[str | None]

    # Ownership
    ownership_percentage: Mapped[float | None]
    ownership_type: Mapped[str]  # 'direct', 'indirect', 'control'

    # Role
    is_director: Mapped[bool] = False
    is_shareholder: Mapped[bool] = False
    is_signatory: Mapped[bool] = False
    role_title: Mapped[str | None]

    # Verification
    verification_status: Mapped[str]  # 'pending', 'verified', 'failed'

    # Screening
    screening_status: Mapped[str | None]

    created_at: Mapped[datetime]


class CompanyDocument(Base):
    __tablename__ = "company_documents"

    id: Mapped[UUID]
    company_id: Mapped[UUID]

    document_type: Mapped[str]  # 'registration_cert', 'articles', 'shareholder_register', etc.
    file_name: Mapped[str]
    storage_key: Mapped[str]

    status: Mapped[str]  # 'pending', 'verified', 'rejected'

    created_at: Mapped[datetime]
```

### Part 2: Create Company Schemas

**File to create:** `backend/app/schemas/company.py`

Create Pydantic schemas for:
- CompanyCreate
- CompanyUpdate
- CompanyResponse
- CompanyListResponse
- BeneficialOwnerCreate
- BeneficialOwnerResponse
- CompanyDocumentResponse

### Part 3: Create Company API

**File to create:** `backend/app/api/v1/companies.py`

**Endpoints:**
```
POST   /api/v1/companies                        - Create company
GET    /api/v1/companies                        - List companies (paginated)
GET    /api/v1/companies/{id}                   - Get company details
PUT    /api/v1/companies/{id}                   - Update company
DELETE /api/v1/companies/{id}                   - Delete company

POST   /api/v1/companies/{id}/screen            - Screen company
POST   /api/v1/companies/{id}/review            - Approve/reject company

GET    /api/v1/companies/{id}/beneficial-owners - List UBOs
POST   /api/v1/companies/{id}/beneficial-owners - Add UBO
PUT    /api/v1/companies/{id}/beneficial-owners/{ubo_id} - Update UBO
DELETE /api/v1/companies/{id}/beneficial-owners/{ubo_id} - Remove UBO
POST   /api/v1/companies/{id}/beneficial-owners/{ubo_id}/link - Link UBO to applicant KYC

GET    /api/v1/companies/{id}/documents         - List company documents
POST   /api/v1/companies/{id}/documents/upload  - Upload document
```

### Part 4: Create Company Screening Service

**File to create:** `backend/app/services/kyb_screening.py`

**Requirements:**
1. Screen company name against sanctions lists
2. Screen all beneficial owners
3. Aggregate risk from company + UBOs
4. Return combined screening result

### Part 5: Create Migration

**File to create:** `backend/migrations/versions/YYYYMMDD_add_companies.py`

Add companies, beneficial_owners, company_documents tables.

### Part 6: Register Router

**Update:** `backend/app/api/router.py`

Add the companies router.

## Success Criteria
1. Can create/update/delete companies
2. Can add/remove beneficial owners
3. Company screening works
4. UBO screening works
5. Can link UBO to individual applicant KYC
6. Documents can be uploaded

## Do NOT:
- Modify existing applicant models
- Change existing screening logic
- Break any existing functionality
```

---

## Sprint F3: Risk Workflows (2-3 Days)

### Why This Sprint?
Sumsub offers risk-based workflows - automatically routing applicants based on risk score. High risk → manual review, low risk → auto-approve.

### Files to Upload:
1. `backend/app/models/applicant.py`
2. `backend/app/api/v1/applicants.py`
3. `backend/app/services/screening.py`

### Prompt (Copy This):

```
# CHAT TITLE: Backend Sprint F3 - Risk Workflows

## Context
I'm building GetClearance, an AI-native KYC/AML platform. We need risk-based workflows that automatically route applicants based on their risk score.

## What Exists
1. **applicant.py** - Has risk_level field
2. **applicants.py** - Has review endpoint
3. **screening.py** - Returns match scores

**Current state:**
- Risk level can be set manually
- No automatic risk calculation
- No workflow routing

## What I Need You To Do

### Part 1: Create Risk Engine Service

**File to create:** `backend/app/services/risk_engine.py`

```python
from enum import Enum
from dataclasses import dataclass

class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class RiskCategory(str, Enum):
    AML = "aml"              # Sanctions/PEP hits
    DOCUMENT = "document"    # Document issues
    IDENTITY = "identity"    # Identity mismatch
    DEVICE = "device"        # VPN, proxy, etc.
    BEHAVIOR = "behavior"    # Suspicious patterns

@dataclass
class RiskSignal:
    category: RiskCategory
    signal: str
    score: int  # 0-100
    details: dict

@dataclass
class RiskAssessment:
    overall_level: RiskLevel
    overall_score: int  # 0-100
    signals: list[RiskSignal]
    recommended_action: str  # 'auto_approve', 'manual_review', 'auto_reject'

async def calculate_risk(
    applicant: Applicant,
    screening_results: list[ScreeningCheck],
    documents: list[Document],
) -> RiskAssessment:
    """
    Calculate overall risk score based on multiple factors.

    Factors:
    - AML screening results (sanctions, PEP, adverse media)
    - Document verification results
    - Country risk
    - Age of documents
    """
    signals = []

    # AML Risk (weight: 40%)
    aml_score = calculate_aml_risk(screening_results)
    signals.append(RiskSignal(
        category=RiskCategory.AML,
        signal="screening_results",
        score=aml_score,
        details={"hits": len([h for s in screening_results for h in s.hits])}
    ))

    # Document Risk (weight: 30%)
    doc_score = calculate_document_risk(documents)
    signals.append(RiskSignal(
        category=RiskCategory.DOCUMENT,
        signal="document_quality",
        score=doc_score,
        details={}
    ))

    # Country Risk (weight: 20%)
    country_score = get_country_risk(applicant.nationality)
    signals.append(RiskSignal(
        category=RiskCategory.IDENTITY,
        signal="country_risk",
        score=country_score,
        details={"country": applicant.nationality}
    ))

    # Calculate weighted score
    overall_score = (
        aml_score * 0.4 +
        doc_score * 0.3 +
        country_score * 0.2 +
        10  # Base score
    )

    # Determine level and action
    if overall_score >= 80:
        level = RiskLevel.CRITICAL
        action = "auto_reject"
    elif overall_score >= 60:
        level = RiskLevel.HIGH
        action = "manual_review"
    elif overall_score >= 40:
        level = RiskLevel.MEDIUM
        action = "manual_review"
    else:
        level = RiskLevel.LOW
        action = "auto_approve"

    return RiskAssessment(
        overall_level=level,
        overall_score=overall_score,
        signals=signals,
        recommended_action=action
    )
```

### Part 2: Create Workflow Configuration

**File to create:** `backend/app/models/workflow.py`

```python
class WorkflowRule(Base):
    __tablename__ = "workflow_rules"

    id: Mapped[UUID]
    tenant_id: Mapped[UUID]

    name: Mapped[str]
    description: Mapped[str | None]

    # Conditions (JSONB)
    conditions: Mapped[dict]
    # Example: {"risk_level": ["high", "critical"], "country": ["IR", "KP"]}

    # Actions
    action: Mapped[str]  # 'auto_approve', 'manual_review', 'auto_reject', 'escalate'
    assign_to: Mapped[UUID | None]  # User ID to assign to

    priority: Mapped[int]  # Higher = evaluated first
    is_active: Mapped[bool]

    created_at: Mapped[datetime]
```

### Part 3: Integrate Risk Calculation

**Update:** `backend/app/api/v1/applicants.py`

After screening completes, automatically:
1. Calculate risk score
2. Apply workflow rules
3. Route accordingly

### Part 4: Add Risk Endpoints

**New endpoints:**
```
GET  /api/v1/applicants/{id}/risk          - Get risk assessment
POST /api/v1/applicants/{id}/risk/recalculate - Recalculate risk

GET  /api/v1/workflows/rules               - List workflow rules
POST /api/v1/workflows/rules               - Create rule
PUT  /api/v1/workflows/rules/{id}          - Update rule
DELETE /api/v1/workflows/rules/{id}        - Delete rule
```

## Success Criteria
1. Risk calculated automatically after screening
2. Applicants routed based on risk level
3. Workflow rules configurable per tenant
4. Risk breakdown visible in API response
```

---

## Sprint F4: Questionnaires (3-4 Days)

### Prompt (Copy This):

```
# CHAT TITLE: Backend Sprint F4 - Questionnaires

## Context
I'm building GetClearance, an AI-native KYC/AML platform. We need custom questionnaires that collect additional information and contribute to risk scoring.

## What I Need You To Do

### Part 1: Create Questionnaire Models

**File to create:** `backend/app/models/questionnaire.py`

```python
class Questionnaire(Base):
    __tablename__ = "questionnaires"

    id: Mapped[UUID]
    tenant_id: Mapped[UUID]

    name: Mapped[str]
    description: Mapped[str | None]

    # Questions stored as JSONB array
    questions: Mapped[list]
    # [
    #   {
    #     "id": "q1",
    #     "type": "select",  # text, select, multi_select, date, file
    #     "label": "Source of funds",
    #     "required": true,
    #     "options": ["Employment", "Business", "Investment", "Inheritance", "Other"],
    #     "risk_scores": {"Employment": 0, "Business": 10, "Other": 20}
    #   }
    # ]

    is_active: Mapped[bool]
    created_at: Mapped[datetime]


class QuestionnaireResponse(Base):
    __tablename__ = "questionnaire_responses"

    id: Mapped[UUID]
    questionnaire_id: Mapped[UUID]
    applicant_id: Mapped[UUID | None]
    company_id: Mapped[UUID | None]

    answers: Mapped[dict]  # JSONB: {"q1": "Employment", "q2": "..."}

    risk_score: Mapped[int | None]  # Calculated from answers

    submitted_at: Mapped[datetime]
```

### Part 2: Create API Endpoints

**File to create:** `backend/app/api/v1/questionnaires.py`

```
GET    /api/v1/questionnaires                    - List questionnaires
POST   /api/v1/questionnaires                    - Create questionnaire
GET    /api/v1/questionnaires/{id}               - Get questionnaire
PUT    /api/v1/questionnaires/{id}               - Update questionnaire
DELETE /api/v1/questionnaires/{id}               - Delete questionnaire

POST   /api/v1/applicants/{id}/questionnaire     - Submit answers
GET    /api/v1/applicants/{id}/questionnaire     - Get submitted answers
```

### Part 3: Risk Score Calculation

Calculate risk score from answers based on configured risk_scores in questions.

## Success Criteria
1. Can create questionnaires with multiple question types
2. Can submit answers for applicants
3. Risk score calculated from answers
4. Risk feeds into overall risk assessment
```

---

## Sprint F5: Address Verification (2-3 Days)

### Prompt (Copy This):

```
# CHAT TITLE: Backend Sprint F5 - Address Verification

## Context
I'm building GetClearance, an AI-native KYC/AML platform. We need address verification - validating and standardizing addresses.

## What I Need You To Do

### Part 1: Create Address Service

**File to create:** `backend/app/services/address_verification.py`

**If using Smarty API:**
```python
import httpx

class AddressVerificationService:
    def __init__(self, auth_id: str, auth_token: str):
        self.auth_id = auth_id
        self.auth_token = auth_token
        self.base_url = "https://us-street.api.smarty.com/street-address"

    async def verify_us_address(
        self,
        street: str,
        city: str,
        state: str,
        zipcode: str = None
    ) -> dict:
        """Verify and standardize US address."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.base_url,
                params={
                    'auth-id': self.auth_id,
                    'auth-token': self.auth_token,
                    'street': street,
                    'city': city,
                    'state': state,
                    'zipcode': zipcode or '',
                    'candidates': 1
                }
            )
            # Parse and return standardized address
```

**If no API key, create mock/basic validation.**

### Part 2: Add to Applicant Flow

Update applicant creation to:
1. Validate address if provided
2. Store standardized address
3. Store geocoding (lat/long) if available

### Part 3: API Endpoint

```
POST /api/v1/addresses/verify - Verify an address
```

## Success Criteria
1. Address validation works (or graceful fallback)
2. Standardized address stored
3. Address quality contributes to risk score
```

---

## Sprint F6: Liveness Detection Placeholder (2-3 Days)

### Prompt (Copy This):

```
# CHAT TITLE: Backend Sprint F6 - Liveness Detection (Placeholder)

## Context
I'm building GetClearance, an AI-native KYC/AML platform. We need liveness detection infrastructure that will integrate with AWS Rekognition later.

## What I Need You To Do

### Part 1: Create Biometrics Service (Placeholder)

**File to create:** `backend/app/services/biometrics.py`

```python
class BiometricsService:
    """
    Biometrics service for face matching and liveness detection.
    Currently a placeholder - will integrate AWS Rekognition in Terminal 5.
    """

    def __init__(self):
        self.is_configured = False  # Set True when AWS configured

    async def compare_faces(
        self,
        source_image: bytes,  # ID photo
        target_image: bytes,  # Selfie
        similarity_threshold: float = 90.0
    ) -> dict:
        """Compare two faces, return similarity score."""
        if not self.is_configured:
            # Return mock result for development
            return {
                'match': True,
                'similarity': 95.0,
                'confidence': 99.0,
                'mock': True
            }

        # TODO: AWS Rekognition integration in Terminal 5

    async def detect_liveness(self, image: bytes) -> dict:
        """Detect if image is live (not a photo of photo)."""
        if not self.is_configured:
            return {
                'is_live': True,
                'confidence': 95.0,
                'quality': {'brightness': 80, 'sharpness': 90},
                'mock': True
            }

        # TODO: AWS Rekognition integration in Terminal 5

biometrics_service = BiometricsService()
```

### Part 2: Create API Endpoints

**File to create:** `backend/app/api/v1/biometrics.py`

```
POST /api/v1/biometrics/compare   - Compare two faces
POST /api/v1/biometrics/liveness  - Check liveness
```

### Part 3: Database Fields

Add to documents table:
- `face_match_score: float`
- `liveness_score: float`
- `biometrics_checked_at: datetime`

## Success Criteria
1. Placeholder service exists
2. API endpoints work (return mock data)
3. Database ready for real data
4. Easy to swap in AWS Rekognition later
```

---

## Quick Start Commands

```bash
# Terminal 2 - Start with F1 (Ongoing AML)
cd ~/getclearance

# Upload these files to chat:
# - backend/app/services/screening.py
# - backend/app/models/screening.py
# - backend/app/models/applicant.py
# - backend/app/workers/screening_worker.py
# - backend/app/api/v1/screening.py

# Then paste the Sprint F1 prompt above
```

---

## Sprint Checklist

After each sprint, verify:

```
□ New files created in correct locations
□ Models have migrations
□ API endpoints registered in router.py
□ Tests written (basic coverage)
□ No breaking changes to existing code
□ Git commit with descriptive message
```

**Commit format:**
```bash
git commit -m "feat(F1): implement ongoing AML monitoring

- Add monitoring service with batch re-screening
- Add monitoring_alerts table
- Add monitoring worker for daily runs
- Add API endpoints for alert management"
```
