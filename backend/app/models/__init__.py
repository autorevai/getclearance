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

# Monitoring (Ongoing AML)
from app.models.monitoring_alert import MonitoringAlert

# Cases (Investigation)
from app.models.case import Case, CaseNote, CaseAttachment

# Audit
from app.models.audit import AuditLog

# Companies (KYB)
from app.models.company import Company, BeneficialOwner, CompanyDocument

# Workflows (Risk-based routing)
from app.models.workflow import WorkflowRule, RiskAssessmentLog

# Questionnaires
from app.models.questionnaire import Questionnaire, QuestionnaireResponse

# Batch Jobs (Background processing)
from app.models.batch_job import BatchJob

# Device Intelligence
from app.models.device import DeviceFingerprint

# KYC Share (Reusable KYC)
from app.models.kyc_share import KYCShareToken, KYCShareAccessLog

# API Keys & Webhooks (Integrations)
from app.models.api_key import ApiKey
from app.models.webhook import WebhookConfig, WebhookDelivery

# Settings & Team
from app.models.settings import TenantSettings, TeamInvitation, SettingsCategory, TeamInvitationStatus

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
    # Monitoring
    "MonitoringAlert",
    # Cases
    "Case",
    "CaseNote",
    "CaseAttachment",
    # Audit
    "AuditLog",
    # Companies (KYB)
    "Company",
    "BeneficialOwner",
    "CompanyDocument",
    # Workflows
    "WorkflowRule",
    "RiskAssessmentLog",
    # Questionnaires
    "Questionnaire",
    "QuestionnaireResponse",
    # Batch Jobs
    "BatchJob",
    # Device Intelligence
    "DeviceFingerprint",
    # KYC Share
    "KYCShareToken",
    "KYCShareAccessLog",
    # API Keys & Webhooks
    "ApiKey",
    "WebhookConfig",
    "WebhookDelivery",
    # Settings & Team
    "TenantSettings",
    "TeamInvitation",
    "SettingsCategory",
    "TeamInvitationStatus",
]
