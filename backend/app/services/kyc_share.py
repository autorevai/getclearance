"""
Get Clearance - KYC Share Service
=================================
Service for managing portable identity / reusable KYC tokens.

Features:
- Generate secure share tokens with configurable permissions
- Verify tokens and return filtered applicant data
- Revoke tokens at any time
- Log all access attempts for audit
"""

import hashlib
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional, Any
from uuid import UUID
import logging

from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.applicant import Applicant
from app.models.kyc_share import KYCShareToken, KYCShareAccessLog
from app.models.document import Document
from app.models.screening import ScreeningCheck, ScreeningHit

logger = logging.getLogger(__name__)


class KYCShareError(Exception):
    """Custom exception for KYC share errors."""
    pass


class TokenExpiredError(KYCShareError):
    """Token has expired."""
    pass


class TokenRevokedError(KYCShareError):
    """Token has been revoked."""
    pass


class TokenExhaustedError(KYCShareError):
    """Token has reached max uses."""
    pass


class TokenInvalidError(KYCShareError):
    """Token is invalid or not found."""
    pass


class ApplicantNotApprovedError(KYCShareError):
    """Applicant must be approved to share KYC."""
    pass


# Available permissions
PERMISSIONS = {
    "basic_info": "Name and date of birth",
    "id_verification": "ID type, number, and verification status",
    "address": "Verified address",
    "screening": "AML/sanctions screening result",
    "documents": "Access to verified documents",
    "full": "All verification data",
}

# Max limits
MAX_EXPIRY_DAYS = 90
MAX_USES = 10
DEFAULT_EXPIRY_DAYS = 30
DEFAULT_MAX_USES = 1


@dataclass
class TokenGenerationResult:
    """Result of token generation."""
    token: str  # The actual token (shown once)
    token_id: UUID
    token_prefix: str
    expires_at: datetime
    max_uses: int
    permissions: dict[str, bool]
    shared_with: str


@dataclass
class SharedKYCData:
    """Filtered applicant data based on permissions."""
    applicant_id: UUID
    verification_status: str
    verified_at: Optional[datetime]

    # Basic info (if permitted)
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[str] = None

    # ID verification (if permitted)
    id_type: Optional[str] = None
    id_number: Optional[str] = None
    id_country: Optional[str] = None
    id_verified: Optional[bool] = None

    # Address (if permitted)
    address: Optional[dict] = None

    # Screening (if permitted)
    screening_clear: Optional[bool] = None
    screening_checked_at: Optional[datetime] = None
    has_pep: Optional[bool] = None
    has_sanctions: Optional[bool] = None

    # Documents (if permitted)
    documents: Optional[list[dict]] = None

    def to_dict(self) -> dict:
        """Convert to dictionary, excluding None values."""
        return {k: v for k, v in {
            "applicant_id": str(self.applicant_id),
            "verification_status": self.verification_status,
            "verified_at": self.verified_at.isoformat() if self.verified_at else None,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "date_of_birth": self.date_of_birth,
            "id_type": self.id_type,
            "id_number": self.id_number,
            "id_country": self.id_country,
            "id_verified": self.id_verified,
            "address": self.address,
            "screening_clear": self.screening_clear,
            "screening_checked_at": self.screening_checked_at.isoformat() if self.screening_checked_at else None,
            "has_pep": self.has_pep,
            "has_sanctions": self.has_sanctions,
            "documents": self.documents,
        }.items() if v is not None}


class KYCShareService:
    """Service for managing KYC share tokens."""

    def _hash_token(self, token: str) -> str:
        """Generate SHA-256 hash of token."""
        return hashlib.sha256(token.encode()).hexdigest()

    async def generate_share_token(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        applicant_id: UUID,
        shared_with: str,
        permissions: dict[str, bool],
        expires_days: int = DEFAULT_EXPIRY_DAYS,
        max_uses: int = DEFAULT_MAX_USES,
        purpose: Optional[str] = None,
        shared_with_email: Optional[str] = None,
        consent_ip_address: Optional[str] = None,
    ) -> TokenGenerationResult:
        """
        Generate a new KYC share token.

        Args:
            db: Database session
            tenant_id: Tenant UUID
            applicant_id: Applicant UUID whose KYC to share
            shared_with: Name of company/entity receiving the data
            permissions: Dict of permission keys to booleans
            expires_days: Days until token expires (max 90)
            max_uses: Maximum times token can be used (max 10)
            purpose: Optional purpose for sharing
            shared_with_email: Optional contact email
            consent_ip_address: IP address where consent was given

        Returns:
            TokenGenerationResult with the token (shown once)
        """
        # Validate applicant exists and is approved
        applicant = await db.get(Applicant, applicant_id)
        if not applicant:
            raise KYCShareError("Applicant not found")
        if applicant.tenant_id != tenant_id:
            raise KYCShareError("Applicant not found")
        if applicant.status != "approved":
            raise ApplicantNotApprovedError("Applicant must be approved to share KYC data")

        # Validate limits
        expires_days = min(expires_days, MAX_EXPIRY_DAYS)
        max_uses = min(max_uses, MAX_USES)

        # Validate permissions
        valid_permissions = {k: v for k, v in permissions.items() if k in PERMISSIONS and v}
        if not valid_permissions:
            raise KYCShareError("At least one permission must be granted")

        # Generate token
        token = secrets.token_urlsafe(32)
        token_hash = self._hash_token(token)
        token_prefix = token[:8]

        # Calculate expiry
        expires_at = datetime.now(timezone.utc) + timedelta(days=expires_days)

        # Create token record
        share_token = KYCShareToken(
            tenant_id=tenant_id,
            applicant_id=applicant_id,
            token_hash=token_hash,
            token_prefix=token_prefix,
            shared_with=shared_with,
            shared_with_email=shared_with_email,
            purpose=purpose,
            permissions=valid_permissions,
            expires_at=expires_at,
            max_uses=max_uses,
            use_count=0,
            consent_given_at=datetime.now(timezone.utc),
            consent_ip_address=consent_ip_address,
        )

        db.add(share_token)
        await db.flush()

        logger.info(f"Generated KYC share token {token_prefix}... for applicant {applicant_id}")

        return TokenGenerationResult(
            token=token,
            token_id=share_token.id,
            token_prefix=token_prefix,
            expires_at=expires_at,
            max_uses=max_uses,
            permissions=valid_permissions,
            shared_with=shared_with,
        )

    async def verify_share_token(
        self,
        db: AsyncSession,
        token: str,
        requester_ip: Optional[str] = None,
        requester_domain: Optional[str] = None,
        requester_user_agent: Optional[str] = None,
    ) -> SharedKYCData:
        """
        Verify a share token and return the shared KYC data.

        Args:
            db: Database session
            token: The share token to verify
            requester_ip: IP address of requester
            requester_domain: Domain of requester
            requester_user_agent: User agent of requester

        Returns:
            SharedKYCData filtered by token permissions
        """
        token_hash = self._hash_token(token)

        # Find token
        query = (
            select(KYCShareToken)
            .options(selectinload(KYCShareToken.applicant))
            .where(KYCShareToken.token_hash == token_hash)
        )
        result = await db.execute(query)
        share_token = result.scalar_one_or_none()

        if not share_token:
            # Log failed attempt
            logger.warning(f"Invalid token verification attempt from {requester_ip}")
            raise TokenInvalidError("Invalid or unknown token")

        # Check token status
        if share_token.is_revoked:
            await self._log_access(
                db, share_token.id, requester_ip, requester_domain,
                requester_user_agent, False, "Token revoked"
            )
            raise TokenRevokedError("Token has been revoked")

        if share_token.is_expired:
            await self._log_access(
                db, share_token.id, requester_ip, requester_domain,
                requester_user_agent, False, "Token expired"
            )
            raise TokenExpiredError("Token has expired")

        if share_token.use_count >= share_token.max_uses:
            await self._log_access(
                db, share_token.id, requester_ip, requester_domain,
                requester_user_agent, False, "Token exhausted"
            )
            raise TokenExhaustedError("Token has reached maximum uses")

        # Get applicant data
        applicant = share_token.applicant

        # Build filtered response based on permissions
        permissions = share_token.permissions
        accessed_permissions = list(permissions.keys())

        shared_data = SharedKYCData(
            applicant_id=applicant.id,
            verification_status=applicant.status,
            verified_at=applicant.reviewed_at,
        )

        # Add data based on permissions
        if permissions.get("basic_info") or permissions.get("full"):
            shared_data.first_name = applicant.first_name
            shared_data.last_name = applicant.last_name
            shared_data.date_of_birth = applicant.date_of_birth.isoformat() if applicant.date_of_birth else None

        if permissions.get("id_verification") or permissions.get("full"):
            # Get ID info from steps/documents
            id_step = next((s for s in applicant.steps if s.step_type == "document"), None)
            if id_step and id_step.data:
                shared_data.id_type = id_step.data.get("document_type")
                shared_data.id_number = id_step.data.get("document_number")
                shared_data.id_country = id_step.data.get("issuing_country")
                shared_data.id_verified = id_step.status == "complete"

        if permissions.get("address") or permissions.get("full"):
            shared_data.address = applicant.address

        if permissions.get("screening") or permissions.get("full"):
            # Get latest screening result
            screening_query = (
                select(ScreeningCheck)
                .where(ScreeningCheck.applicant_id == applicant.id)
                .order_by(ScreeningCheck.created_at.desc())
                .limit(1)
            )
            screening_result = await db.execute(screening_query)
            screening = screening_result.scalar_one_or_none()

            if screening:
                shared_data.screening_clear = screening.status == "clear"
                shared_data.screening_checked_at = screening.created_at
                shared_data.has_pep = "pep" in applicant.flags
                shared_data.has_sanctions = "sanctions" in applicant.flags

        if permissions.get("documents") or permissions.get("full"):
            # Get verified documents (metadata only, not actual files)
            doc_query = (
                select(Document)
                .where(
                    and_(
                        Document.applicant_id == applicant.id,
                        Document.verification_status == "verified",
                    )
                )
            )
            doc_result = await db.execute(doc_query)
            documents = doc_result.scalars().all()

            shared_data.documents = [
                {
                    "type": doc.document_type,
                    "verified_at": doc.verified_at.isoformat() if doc.verified_at else None,
                    "issuing_country": doc.issuing_country,
                }
                for doc in documents
            ]

        # Increment use count
        share_token.use_count += 1

        # Log successful access
        await self._log_access(
            db, share_token.id, requester_ip, requester_domain,
            requester_user_agent, True, None, accessed_permissions
        )

        await db.commit()

        logger.info(f"Token {share_token.token_prefix}... verified by {requester_ip}")

        return shared_data

    async def revoke_share_token(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        token_id: UUID,
        reason: Optional[str] = None,
    ) -> None:
        """
        Revoke a share token.

        Args:
            db: Database session
            tenant_id: Tenant UUID
            token_id: Token UUID to revoke
            reason: Optional reason for revocation
        """
        token = await db.get(KYCShareToken, token_id)
        if not token or token.tenant_id != tenant_id:
            raise KYCShareError("Token not found")

        if token.is_revoked:
            return  # Already revoked

        token.revoked_at = datetime.now(timezone.utc)
        token.revoked_reason = reason

        await db.commit()

        logger.info(f"Revoked KYC share token {token.token_prefix}...")

    async def get_applicant_tokens(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        applicant_id: UUID,
        include_expired: bool = False,
    ) -> list[KYCShareToken]:
        """
        Get all share tokens for an applicant.

        Args:
            db: Database session
            tenant_id: Tenant UUID
            applicant_id: Applicant UUID
            include_expired: Whether to include expired tokens

        Returns:
            List of KYCShareToken objects
        """
        query = (
            select(KYCShareToken)
            .where(
                and_(
                    KYCShareToken.tenant_id == tenant_id,
                    KYCShareToken.applicant_id == applicant_id,
                )
            )
            .order_by(KYCShareToken.created_at.desc())
        )

        if not include_expired:
            query = query.where(
                KYCShareToken.expires_at > datetime.now(timezone.utc)
            )

        result = await db.execute(query)
        return result.scalars().all()

    async def get_token_access_history(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        applicant_id: UUID,
        limit: int = 50,
    ) -> list[dict]:
        """
        Get access history for an applicant's shared tokens.

        Args:
            db: Database session
            tenant_id: Tenant UUID
            applicant_id: Applicant UUID
            limit: Maximum number of records

        Returns:
            List of access log entries
        """
        query = (
            select(KYCShareAccessLog, KYCShareToken)
            .join(KYCShareToken)
            .where(
                and_(
                    KYCShareToken.tenant_id == tenant_id,
                    KYCShareToken.applicant_id == applicant_id,
                )
            )
            .order_by(KYCShareAccessLog.accessed_at.desc())
            .limit(limit)
        )

        result = await db.execute(query)
        rows = result.all()

        return [
            {
                "id": str(log.id),
                "token_prefix": token.token_prefix,
                "shared_with": token.shared_with,
                "requester_ip": log.requester_ip,
                "requester_domain": log.requester_domain,
                "accessed_at": log.accessed_at.isoformat(),
                "success": log.success,
                "failure_reason": log.failure_reason,
                "accessed_permissions": log.accessed_permissions,
            }
            for log, token in rows
        ]

    async def _log_access(
        self,
        db: AsyncSession,
        token_id: UUID,
        requester_ip: Optional[str],
        requester_domain: Optional[str],
        requester_user_agent: Optional[str],
        success: bool,
        failure_reason: Optional[str],
        accessed_permissions: Optional[list[str]] = None,
    ) -> None:
        """Log an access attempt."""
        log = KYCShareAccessLog(
            token_id=token_id,
            requester_ip=requester_ip,
            requester_domain=requester_domain,
            requester_user_agent=requester_user_agent,
            accessed_at=datetime.now(timezone.utc),
            success=success,
            failure_reason=failure_reason,
            accessed_permissions=accessed_permissions or [],
        )
        db.add(log)

    def get_available_permissions(self) -> dict[str, str]:
        """Get list of available permissions."""
        return PERMISSIONS.copy()


# Singleton instance
kyc_share_service = KYCShareService()
