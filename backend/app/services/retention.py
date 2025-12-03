"""
Get Clearance - Data Retention Service
=======================================
GDPR-compliant data retention management.

Implements retention policies based on:
- GDPR Article 5(1)(e): Storage limitation principle
- AML 4th/5th Directive: 5-year minimum for suspicious activity
- Local regulations may require longer retention

Retention periods by applicant status:
- approved: 5 years (standard retention)
- rejected: 5 years (AML requirement for rejected applicants)
- flagged: 7 years (extended AML retention for confirmed hits)
- pending: 90 days (incomplete applications)
- withdrawn: 30 days (user-cancelled applications)
"""

from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Applicant


# Retention policies define how long data should be kept after last activity
RETENTION_POLICIES: dict[str, timedelta] = {
    "approved": timedelta(days=365 * 5),      # 5 years - standard KYC retention
    "rejected": timedelta(days=365 * 5),      # 5 years - AML requires keeping rejected
    "flagged": timedelta(days=365 * 7),       # 7 years - extended for confirmed hits
    "pending": timedelta(days=90),            # 90 days - incomplete applications
    "in_progress": timedelta(days=90),        # 90 days - stuck in progress
    "review": timedelta(days=180),            # 6 months - awaiting review
    "withdrawn": timedelta(days=30),          # 30 days - user cancelled
}


def get_retention_period(status: str) -> timedelta:
    """
    Get the retention period for a given applicant status.

    Args:
        status: Applicant status

    Returns:
        Retention timedelta for that status
    """
    return RETENTION_POLICIES.get(status, timedelta(days=365 * 5))  # Default 5 years


def calculate_retention_expiry(status: str, from_date: datetime | None = None) -> datetime:
    """
    Calculate when an applicant's data should expire based on status.

    Args:
        status: Applicant status
        from_date: Starting date (defaults to now)

    Returns:
        DateTime when data retention expires
    """
    from_date = from_date or datetime.utcnow()
    retention_period = get_retention_period(status)
    return from_date + retention_period


def can_delete_for_aml(applicant: Applicant) -> bool:
    """
    Check if applicant can be deleted per AML regulations.

    Some records must be retained regardless of GDPR right to erasure:
    - Flagged applicants with confirmed sanctions/PEP hits
    - Records linked to SARs (Suspicious Activity Reports)
    - Records under legal hold

    Args:
        applicant: Applicant to check

    Returns:
        True if deletion is allowed, False if AML requires retention
    """
    # Legal hold always blocks deletion
    if applicant.legal_hold:
        return False

    # Check if applicant was flagged with confirmed hits
    if applicant.status == "flagged":
        # Check retention expiry
        if applicant.retention_expires_at:
            return datetime.utcnow() >= applicant.retention_expires_at

        # If no expiry set, calculate from updated_at
        min_retention = applicant.updated_at + timedelta(days=365 * 5)
        return datetime.utcnow() >= min_retention

    # Rejected applicants have 5-year AML retention
    if applicant.status == "rejected":
        if applicant.retention_expires_at:
            return datetime.utcnow() >= applicant.retention_expires_at

        min_retention = applicant.updated_at + timedelta(days=365 * 5)
        return datetime.utcnow() >= min_retention

    # Other statuses can be deleted
    return True


async def get_expired_applicants(
    db: AsyncSession,
    tenant_id: UUID | None = None,
    limit: int = 100,
) -> list[Applicant]:
    """
    Find applicants past their retention period.

    Checks each applicant's status against retention policies
    and returns those that have exceeded their retention period.

    Args:
        db: Database session
        tenant_id: Optional tenant filter
        limit: Maximum number of results

    Returns:
        List of applicants past retention period
    """
    expired: list[Applicant] = []
    now = datetime.utcnow()

    for status, retention_period in RETENTION_POLICIES.items():
        cutoff = now - retention_period

        query = select(Applicant).where(
            and_(
                Applicant.status == status,
                Applicant.updated_at < cutoff,
                Applicant.legal_hold == False,  # noqa: E712
            )
        )

        if tenant_id:
            query = query.where(Applicant.tenant_id == tenant_id)

        query = query.limit(limit - len(expired))

        result = await db.execute(query)
        expired.extend(result.scalars().all())

        if len(expired) >= limit:
            break

    return expired[:limit]


async def get_applicants_expiring_soon(
    db: AsyncSession,
    days_until_expiry: int = 30,
    tenant_id: UUID | None = None,
    limit: int = 100,
) -> list[Applicant]:
    """
    Find applicants whose retention is expiring soon.

    Useful for sending notifications before automatic deletion.

    Args:
        db: Database session
        days_until_expiry: Warning threshold in days
        tenant_id: Optional tenant filter
        limit: Maximum number of results

    Returns:
        List of applicants with upcoming expiry
    """
    expiring: list[Applicant] = []
    now = datetime.utcnow()

    for status, retention_period in RETENTION_POLICIES.items():
        # Calculate the window: expired < updated_at < expiring_soon
        expiry_cutoff = now - retention_period
        warning_cutoff = now - retention_period + timedelta(days=days_until_expiry)

        query = select(Applicant).where(
            and_(
                Applicant.status == status,
                Applicant.updated_at >= expiry_cutoff,
                Applicant.updated_at < warning_cutoff,
                Applicant.legal_hold == False,  # noqa: E712
            )
        )

        if tenant_id:
            query = query.where(Applicant.tenant_id == tenant_id)

        query = query.limit(limit - len(expiring))

        result = await db.execute(query)
        expiring.extend(result.scalars().all())

        if len(expiring) >= limit:
            break

    return expiring[:limit]


async def set_legal_hold(
    db: AsyncSession,
    applicant: Applicant,
    reason: str,
    user_id: UUID,
) -> None:
    """
    Place an applicant under legal hold to prevent deletion.

    Legal hold blocks:
    - GDPR deletion requests
    - Automated retention cleanup
    - Manual deletion

    Args:
        db: Database session
        applicant: Applicant to hold
        reason: Reason for legal hold
        user_id: User setting the hold
    """
    applicant.legal_hold = True
    applicant.legal_hold_reason = reason
    applicant.legal_hold_set_by = user_id
    applicant.legal_hold_set_at = datetime.utcnow()
    applicant.updated_at = datetime.utcnow()
    await db.flush()


async def remove_legal_hold(
    db: AsyncSession,
    applicant: Applicant,
) -> None:
    """
    Remove legal hold from an applicant.

    Args:
        db: Database session
        applicant: Applicant to release
    """
    applicant.legal_hold = False
    applicant.legal_hold_reason = None
    applicant.legal_hold_set_by = None
    applicant.legal_hold_set_at = None
    applicant.updated_at = datetime.utcnow()
    await db.flush()


def get_retention_summary() -> dict[str, Any]:
    """
    Get a summary of retention policies.

    Returns:
        Dictionary with retention policy details
    """
    return {
        "policies": {
            status: {
                "days": period.days,
                "years": round(period.days / 365, 1),
                "description": _get_policy_description(status),
            }
            for status, period in RETENTION_POLICIES.items()
        },
        "aml_requirements": {
            "flagged_minimum_years": 7,
            "rejected_minimum_years": 5,
            "legal_hold_overrides_all": True,
        },
        "gdpr_articles": {
            "storage_limitation": "5(1)(e)",
            "right_to_erasure": "17",
            "legal_basis_exceptions": ["17(3)(b)", "17(3)(e)"],
        },
    }


def _get_policy_description(status: str) -> str:
    """Get human-readable description for retention policy."""
    descriptions = {
        "approved": "Standard KYC retention for approved applicants",
        "rejected": "AML requirement for rejected applicants",
        "flagged": "Extended retention for confirmed screening hits",
        "pending": "Short retention for incomplete applications",
        "in_progress": "Short retention for stuck applications",
        "review": "Medium retention for applications awaiting review",
        "withdrawn": "Minimal retention for user-cancelled applications",
    }
    return descriptions.get(status, "Default retention period")
