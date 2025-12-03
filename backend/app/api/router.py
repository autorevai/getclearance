"""
Get Clearance - API Router
===========================
Aggregates all API v1 routers into a single router.

Router structure:
    /api/v1/
    ├── /applicants     - KYC applicant management
    ├── /companies      - KYB company verification
    ├── /documents      - Document upload and management
    ├── /screening      - AML/sanctions screening
    ├── /cases          - Investigation case management
    ├── /workflows      - Workflow configuration
    ├── /evidence       - Evidence pack export
    └── /webhooks       - Inbound webhook handling
"""

from fastapi import APIRouter

from app.api.v1 import applicants, companies, documents, screening, cases, ai, auth, dashboard, monitoring, settings, workflows, audit, questionnaires, addresses, analytics, biometrics, integrations, device_intel, billing, kyc_share, sdk

# Main API router
api_router = APIRouter()

# Include all v1 routers
api_router.include_router(
    applicants.router,
    prefix="/applicants",
    tags=["Applicants"],
)

api_router.include_router(
    documents.router,
    prefix="/documents",
    tags=["Documents"],
)

api_router.include_router(
    screening.router,
    prefix="/screening",
    tags=["Screening"],
)

api_router.include_router(
    cases.router,
    prefix="/cases",
    tags=["Cases"],
)

api_router.include_router(
    ai.router,
    prefix="/ai",
    tags=["AI"],
)

api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Auth"],
)

api_router.include_router(
    dashboard.router,
    prefix="/dashboard",
    tags=["Dashboard"],
)

api_router.include_router(
    monitoring.router,
    prefix="/monitoring",
    tags=["Monitoring"],
)

api_router.include_router(
    companies.router,
    prefix="/companies",
    tags=["Companies"],
)

api_router.include_router(
    settings.router,
    prefix="/settings",
    tags=["Settings"],
)

api_router.include_router(
    workflows.router,
    prefix="/workflows",
    tags=["Workflows"],
)

api_router.include_router(
    audit.router,
    prefix="/audit-log",
    tags=["Audit Log"],
)

api_router.include_router(
    questionnaires.router,
    prefix="/questionnaires",
    tags=["Questionnaires"],
)

api_router.include_router(
    addresses.router,
    prefix="/addresses",
    tags=["Addresses"],
)

api_router.include_router(
    analytics.router,
    prefix="/analytics",
    tags=["Analytics"],
)

api_router.include_router(
    biometrics.router,
    prefix="/biometrics",
    tags=["Biometrics"],
)

api_router.include_router(
    integrations.router,
    prefix="/integrations",
    tags=["Integrations"],
)

api_router.include_router(
    device_intel.router,
    prefix="/device-intel",
    tags=["Device Intelligence"],
)

api_router.include_router(
    billing.router,
    prefix="/billing",
    tags=["Billing"],
)

api_router.include_router(
    kyc_share.router,
    tags=["KYC Share"],
)

api_router.include_router(
    sdk.router,
    prefix="/sdk",
    tags=["SDK"],
)

# TODO: Add remaining routers as they're built
# api_router.include_router(evidence.router, prefix="/evidence", tags=["Evidence"])
# api_router.include_router(webhooks.router, prefix="/webhooks", tags=["Webhooks"])
