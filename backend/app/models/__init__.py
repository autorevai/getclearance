"""
Get Clearance - SQLAlchemy Models
==================================
All database models for the compliance platform.

Import all models here to ensure they're registered with SQLAlchemy
before Alembic runs migrations.
"""

# Base class
from app.database import Base

# Tenant & Users
from app.models.tenant import Tenant, User

# Applicants (KYC)
from app.models.applicant import Applicant, ApplicantStep

# Documents
from app.models.document import Document

# Screening (AML/Sanctions/PEP)
from app.models.screening import ScreeningList, ScreeningCheck, ScreeningHit

# Cases (Investigation)
from app.models.case import Case, CaseNote, CaseAttachment

# Audit
from app.models.audit import AuditLog

# Export all for convenience
__all__ = [
    # Base
    "Base",
    # Tenant
    "Tenant",
    "User",
    # Applicants
    "Applicant",
    "ApplicantStep",
    # Documents
    "Document",
    # Screening
    "ScreeningList",
    "ScreeningCheck",
    "ScreeningHit",
    # Cases
    "Case",
    "CaseNote",
    "CaseAttachment",
    # Audit
    "AuditLog",
]
