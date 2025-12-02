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

from app.api.v1 import applicants, documents, screening, cases, ai, auth

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

# TODO: Add remaining routers as they're built
# api_router.include_router(companies.router, prefix="/companies", tags=["Companies"])
# api_router.include_router(workflows.router, prefix="/workflows", tags=["Workflows"])
# api_router.include_router(evidence.router, prefix="/evidence", tags=["Evidence"])
# api_router.include_router(webhooks.router, prefix="/webhooks", tags=["Webhooks"])
