"""
Get Clearance - KYC Share API Routes
=====================================
API endpoints for Reusable KYC / Portable Identity feature.

Allows verified applicants to share their KYC data with third parties
using secure, time-limited, revocable tokens.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import TenantDB, AuthenticatedUser
from app.schemas.kyc_share import (
    ShareTokenCreate,
    ShareTokenResponse,
    ShareTokenRevoke,
    ShareTokenListItem,
    ShareTokenListResponse,
    SharedKYCDataResponse,
    VerifyTokenRequest,
    AccessLogEntry,
    AccessHistoryResponse,
    AvailablePermissionsResponse,
    PermissionInfo,
)
from app.services.kyc_share import (
    kyc_share_service,
    KYCShareError,
    TokenExpiredError,
    TokenRevokedError,
    TokenExhaustedError,
    TokenInvalidError,
    ApplicantNotApprovedError,
    PERMISSIONS,
)

router = APIRouter(prefix="/kyc-share", tags=["KYC Share"])


# ===========================================
# TOKEN MANAGEMENT ENDPOINTS
# ===========================================

@router.post("/token", response_model=ShareTokenResponse, status_code=status.HTTP_201_CREATED)
async def generate_share_token(
    data: ShareTokenCreate,
    request: Request,
    db: TenantDB,
    user: AuthenticatedUser,
):
    """
    Generate a new KYC share token for an applicant.

    The token is returned ONCE in the response - store it securely.
    The applicant must be in 'approved' status to share their KYC.

    **Permissions:**
    - `basic_info`: Name and date of birth
    - `id_verification`: ID type, number, and verification status
    - `address`: Verified address
    - `screening`: AML/sanctions screening result
    - `documents`: Access to verified documents
    - `full`: All verification data
    """
    try:
        # Get client IP for consent tracking
        client_ip = request.client.host if request.client else None

        result = await kyc_share_service.generate_share_token(
            db=db,
            tenant_id=user.tenant_id,
            applicant_id=data.applicant_id,
            shared_with=data.shared_with,
            permissions=data.permissions,
            expires_days=data.expires_days,
            max_uses=data.max_uses,
            purpose=data.purpose,
            shared_with_email=data.shared_with_email,
            consent_ip_address=client_ip,
        )

        return ShareTokenResponse(
            token=result.token,
            token_id=result.token_id,
            token_prefix=result.token_prefix,
            expires_at=result.expires_at,
            max_uses=result.max_uses,
            permissions=result.permissions,
            shared_with=result.shared_with,
        )

    except ApplicantNotApprovedError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except KYCShareError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/tokens/{applicant_id}", response_model=ShareTokenListResponse)
async def list_share_tokens(
    applicant_id: UUID,
    db: TenantDB,
    user: AuthenticatedUser,
    include_expired: bool = False,
):
    """
    List all share tokens for an applicant.

    By default, only active (non-expired) tokens are returned.
    Set `include_expired=true` to include expired tokens.
    """
    tokens = await kyc_share_service.get_applicant_tokens(
        db=db,
        tenant_id=user.tenant_id,
        applicant_id=applicant_id,
        include_expired=include_expired,
    )

    token_list = [
        ShareTokenListItem(
            id=t.id,
            token_prefix=t.token_prefix,
            shared_with=t.shared_with,
            shared_with_email=t.shared_with_email,
            purpose=t.purpose,
            permissions=t.permissions,
            expires_at=t.expires_at,
            max_uses=t.max_uses,
            use_count=t.use_count,
            uses_remaining=t.uses_remaining,
            status=t.status,
            revoked_at=t.revoked_at,
            revoked_reason=t.revoked_reason,
            created_at=t.created_at,
        )
        for t in tokens
    ]

    return ShareTokenListResponse(
        tokens=token_list,
        total=len(token_list),
    )


@router.post("/revoke/{token_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_share_token(
    token_id: UUID,
    db: TenantDB,
    user: AuthenticatedUser,
    data: Optional[ShareTokenRevoke] = None,
):
    """
    Revoke a share token immediately.

    Once revoked, the token can no longer be used to access KYC data.
    This action cannot be undone.
    """
    try:
        reason = data.reason if data else None
        await kyc_share_service.revoke_share_token(
            db=db,
            tenant_id=user.tenant_id,
            token_id=token_id,
            reason=reason,
        )
    except KYCShareError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


# ===========================================
# TOKEN VERIFICATION ENDPOINT (PUBLIC)
# ===========================================

@router.post("/verify", response_model=SharedKYCDataResponse)
async def verify_share_token(
    data: VerifyTokenRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Verify a share token and retrieve the shared KYC data.

    This endpoint is PUBLIC (no authentication required).
    The token itself serves as the authentication.

    Each successful verification counts against the token's max_uses.
    The returned data is filtered based on the token's permissions.
    """
    # Get requester info for logging
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    # Try to get domain from referer or origin
    referer = request.headers.get("referer") or request.headers.get("origin")
    requester_domain = None
    if referer:
        from urllib.parse import urlparse
        parsed = urlparse(referer)
        requester_domain = parsed.netloc

    try:
        shared_data = await kyc_share_service.verify_share_token(
            db=db,
            token=data.token,
            requester_ip=client_ip,
            requester_domain=requester_domain,
            requester_user_agent=user_agent,
        )

        # Get token for metadata
        token_hash = kyc_share_service._hash_token(data.token)
        from sqlalchemy import select
        from app.models.kyc_share import KYCShareToken
        query = select(KYCShareToken).where(KYCShareToken.token_hash == token_hash)
        result = await db.execute(query)
        token = result.scalar_one_or_none()

        return SharedKYCDataResponse(
            applicant_id=shared_data.applicant_id,
            verification_status=shared_data.verification_status,
            verified_at=shared_data.verified_at,
            first_name=shared_data.first_name,
            last_name=shared_data.last_name,
            date_of_birth=shared_data.date_of_birth,
            id_type=shared_data.id_type,
            id_number=shared_data.id_number,
            id_country=shared_data.id_country,
            id_verified=shared_data.id_verified,
            address=shared_data.address,
            screening_clear=shared_data.screening_clear,
            screening_checked_at=shared_data.screening_checked_at,
            has_pep=shared_data.has_pep,
            has_sanctions=shared_data.has_sanctions,
            documents=shared_data.documents,
            token_permissions=token.permissions if token else {},
            uses_remaining=token.uses_remaining if token else 0,
        )

    except TokenInvalidError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid or unknown token"
        )
    except TokenExpiredError:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Token has expired"
        )
    except TokenRevokedError:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Token has been revoked"
        )
    except TokenExhaustedError:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Token has reached maximum uses"
        )


# ===========================================
# ACCESS HISTORY ENDPOINT
# ===========================================

@router.get("/history/{applicant_id}", response_model=AccessHistoryResponse)
async def get_access_history(
    applicant_id: UUID,
    db: TenantDB,
    user: AuthenticatedUser,
    limit: int = 50,
):
    """
    Get access history for an applicant's shared tokens.

    Returns a log of all verification attempts, both successful and failed.
    Useful for audit and compliance purposes.
    """
    logs = await kyc_share_service.get_token_access_history(
        db=db,
        tenant_id=user.tenant_id,
        applicant_id=applicant_id,
        limit=limit,
    )

    log_entries = [
        AccessLogEntry(
            id=UUID(log["id"]),
            token_prefix=log["token_prefix"],
            shared_with=log["shared_with"],
            requester_ip=log["requester_ip"],
            requester_domain=log["requester_domain"],
            accessed_at=log["accessed_at"],
            success=log["success"],
            failure_reason=log["failure_reason"],
            accessed_permissions=log["accessed_permissions"],
        )
        for log in logs
    ]

    return AccessHistoryResponse(
        logs=log_entries,
        total=len(log_entries),
    )


# ===========================================
# UTILITY ENDPOINTS
# ===========================================

@router.get("/permissions", response_model=AvailablePermissionsResponse)
async def get_available_permissions():
    """
    Get list of available permissions for KYC sharing.

    Use these keys when creating a new share token.
    """
    permission_list = [
        PermissionInfo(
            key=key,
            name=key.replace("_", " ").title(),
            description=desc,
        )
        for key, desc in PERMISSIONS.items()
    ]

    return AvailablePermissionsResponse(permissions=permission_list)
