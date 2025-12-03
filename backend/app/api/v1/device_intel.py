"""
Get Clearance - Device Intelligence API
========================================
Device fingerprinting and fraud detection endpoints.

Provides:
- Device fingerprint submission and analysis
- Applicant device history
- Fraud statistics dashboard
"""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import TenantDB, AuthenticatedUser, AuditContext, require_permission
from app.models.device import DeviceFingerprint
from app.models.applicant import Applicant
from app.services.device_intel import device_intel_service, DeviceIntelError
from app.services.audit import record_audit_log
from app.schemas.device import (
    DeviceSubmission,
    DeviceAnalysisResult,
    DeviceSummary,
    DeviceListResponse,
    DeviceStats,
    ApplicantDevicesResponse,
    IPCheckResponse,
    EmailCheckResponse,
    PhoneCheckResponse,
)

router = APIRouter()


# ===========================================
# DEVICE ANALYSIS
# ===========================================

@router.post("/analyze", response_model=DeviceAnalysisResult, status_code=status.HTTP_201_CREATED)
async def analyze_device(
    data: DeviceSubmission,
    db: TenantDB,
    user: Annotated[AuthenticatedUser, Depends(require_permission("write:applicants"))],
    ctx: AuditContext,
):
    """
    Submit device fingerprint for analysis.

    Performs IP reputation check, and optionally email/phone validation.
    Returns combined risk assessment.
    """
    # Verify applicant if provided
    if data.applicant_id:
        applicant = await db.get(Applicant, data.applicant_id)
        if not applicant or applicant.tenant_id != user.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Applicant not found",
            )

    try:
        # Run device analysis
        result = await device_intel_service.analyze_device(
            ip_address=data.ip_address,
            email=data.email,
            phone=data.phone,
            user_agent=data.user_agent,
            phone_country=data.phone_country,
        )

        # Create device fingerprint record
        device = DeviceFingerprint(
            tenant_id=user.tenant_id,
            applicant_id=data.applicant_id,
            session_id=data.session_id,
            fingerprint_hash=data.fingerprint_hash,
            ip_address=data.ip_address,
            user_agent=data.user_agent,
            browser=data.browser,
            browser_version=data.browser_version,
            operating_system=data.operating_system,
            os_version=data.os_version,
            device_type=data.device_type,
            device_brand=data.device_brand,
            device_model=data.device_model,
            screen_resolution=data.screen_resolution,
            timezone=data.timezone,
            language=data.language,
            # IP check results
            fraud_score=result.fraud_score,
            risk_score=result.risk_score,
            risk_level=result.risk_level,
            risk_signals=result.risk_signals,
            status="completed",
        )

        # Populate from IP check
        if result.ip_check:
            ip = result.ip_check
            device.country_code = ip.country_code
            device.city = ip.city
            device.region = ip.region
            device.isp = ip.isp
            device.asn = ip.asn
            device.organization = ip.organization
            device.is_vpn = ip.is_vpn
            device.is_proxy = ip.is_proxy
            device.is_tor = ip.is_tor
            device.is_bot = ip.is_bot
            device.is_crawler = ip.is_crawler
            device.is_datacenter = ip.is_datacenter
            device.is_mobile = ip.is_mobile
            device.active_vpn = ip.active_vpn
            device.active_tor = ip.active_tor
            device.recent_abuse = ip.recent_abuse
            device.connection_type = ip.connection_type
            device.ip_check_response = ip.raw_response

        # Populate from email check
        if result.email_check:
            email = result.email_check
            device.email_valid = email.valid
            device.email_disposable = email.disposable
            device.email_fraud_score = email.fraud_score
            device.email_check_response = email.raw_response

        # Populate from phone check
        if result.phone_check:
            phone = result.phone_check
            device.phone_valid = phone.valid
            device.phone_fraud_score = phone.fraud_score
            device.phone_line_type = phone.line_type
            device.phone_check_response = phone.raw_response

        db.add(device)
        await db.flush()

        # Audit log
        await record_audit_log(
            db=db,
            tenant_id=user.tenant_id,
            user_id=UUID(user.id),
            action="device.analyzed",
            resource_type="device_fingerprint",
            resource_id=device.id,
            new_values={
                "session_id": data.session_id,
                "ip_address": data.ip_address,
                "risk_level": result.risk_level,
                "fraud_score": result.fraud_score,
                "flags": result.flags,
            },
            user_email=user.email,
            ip_address=ctx.ip_address,
        )

        await db.commit()
        await db.refresh(device)

        # Build response
        return DeviceAnalysisResult(
            id=device.id,
            session_id=device.session_id,
            risk_score=device.risk_score or 0,
            risk_level=device.risk_level or "low",
            fraud_score=device.fraud_score or 0,
            risk_signals=device.risk_signals or {},
            flags=result.flags,
            ip_address=device.ip_address,
            country_code=device.country_code,
            city=device.city,
            isp=device.isp,
            is_vpn=device.is_vpn,
            is_proxy=device.is_proxy,
            is_tor=device.is_tor,
            is_bot=device.is_bot,
            is_datacenter=device.is_datacenter,
            is_mobile=device.is_mobile,
            device_type=device.device_type,
            browser=device.browser,
            operating_system=device.operating_system,
            ip_check=IPCheckResponse(
                ip_address=result.ip_check.ip_address,
                fraud_score=result.ip_check.fraud_score,
                is_proxy=result.ip_check.is_proxy,
                is_vpn=result.ip_check.is_vpn,
                is_tor=result.ip_check.is_tor,
                is_bot=result.ip_check.is_bot,
                is_datacenter=result.ip_check.is_datacenter,
                is_mobile=result.ip_check.is_mobile,
                active_vpn=result.ip_check.active_vpn,
                active_tor=result.ip_check.active_tor,
                recent_abuse=result.ip_check.recent_abuse,
                connection_type=result.ip_check.connection_type,
                country_code=result.ip_check.country_code,
                city=result.ip_check.city,
                region=result.ip_check.region,
                isp=result.ip_check.isp,
                asn=result.ip_check.asn,
            ) if result.ip_check else None,
            email_check=EmailCheckResponse(
                email=result.email_check.email,
                valid=result.email_check.valid,
                disposable=result.email_check.disposable,
                fraud_score=result.email_check.fraud_score,
                recent_abuse=result.email_check.recent_abuse,
                deliverability=result.email_check.deliverability,
            ) if result.email_check else None,
            phone_check=PhoneCheckResponse(
                phone=result.phone_check.phone,
                valid=result.phone_check.valid,
                fraud_score=result.phone_check.fraud_score,
                line_type=result.phone_check.line_type,
                carrier=result.phone_check.carrier,
                active=result.phone_check.active,
                risky=result.phone_check.risky,
            ) if result.phone_check else None,
            created_at=device.created_at,
        )

    except DeviceIntelError as e:
        # Store failed attempt
        device = DeviceFingerprint(
            tenant_id=user.tenant_id,
            applicant_id=data.applicant_id,
            session_id=data.session_id,
            fingerprint_hash=data.fingerprint_hash,
            ip_address=data.ip_address,
            user_agent=data.user_agent,
            status="error",
            error_message=str(e),
        )
        db.add(device)
        await db.commit()

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Device analysis failed: {str(e)}",
        )


# ===========================================
# DEVICE HISTORY
# ===========================================

@router.get("/applicant/{applicant_id}", response_model=ApplicantDevicesResponse)
async def get_applicant_devices(
    applicant_id: UUID,
    db: TenantDB,
    user: Annotated[AuthenticatedUser, Depends(require_permission("read:applicants"))],
):
    """Get device fingerprint history for an applicant."""
    # Verify applicant
    applicant = await db.get(Applicant, applicant_id)
    if not applicant or applicant.tenant_id != user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Applicant not found",
        )

    # Get devices
    query = (
        select(DeviceFingerprint)
        .where(
            DeviceFingerprint.applicant_id == applicant_id,
            DeviceFingerprint.tenant_id == user.tenant_id,
        )
        .order_by(DeviceFingerprint.created_at.desc())
    )
    result = await db.execute(query)
    devices = result.scalars().all()

    # Check for high-risk indicators
    has_high_risk = any(d.risk_level == "high" for d in devices)
    has_vpn = any(d.is_vpn for d in devices)
    has_tor = any(d.is_tor for d in devices)

    return ApplicantDevicesResponse(
        applicant_id=applicant_id,
        devices=[
            DeviceSummary(
                id=d.id,
                session_id=d.session_id,
                applicant_id=d.applicant_id,
                risk_score=d.risk_score,
                risk_level=d.risk_level,
                fraud_score=d.fraud_score,
                flags=d.risk_flags,
                ip_address=d.ip_address,
                country_code=d.country_code,
                city=d.city,
                is_vpn=d.is_vpn,
                is_proxy=d.is_proxy,
                is_tor=d.is_tor,
                is_bot=d.is_bot,
                device_type=d.device_type,
                browser=d.browser,
                operating_system=d.operating_system,
                created_at=d.created_at,
            )
            for d in devices
        ],
        total=len(devices),
        has_high_risk=has_high_risk,
        has_vpn=has_vpn,
        has_tor=has_tor,
    )


@router.get("/session/{session_id}", response_model=DeviceSummary)
async def get_session_device(
    session_id: str,
    db: TenantDB,
    user: Annotated[AuthenticatedUser, Depends(require_permission("read:applicants"))],
):
    """Get device fingerprint for a specific session."""
    query = select(DeviceFingerprint).where(
        DeviceFingerprint.session_id == session_id,
        DeviceFingerprint.tenant_id == user.tenant_id,
    )
    result = await db.execute(query)
    device = result.scalar_one_or_none()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session device not found",
        )

    return DeviceSummary(
        id=device.id,
        session_id=device.session_id,
        applicant_id=device.applicant_id,
        risk_score=device.risk_score,
        risk_level=device.risk_level,
        fraud_score=device.fraud_score,
        flags=device.risk_flags,
        ip_address=device.ip_address,
        country_code=device.country_code,
        city=device.city,
        is_vpn=device.is_vpn,
        is_proxy=device.is_proxy,
        is_tor=device.is_tor,
        is_bot=device.is_bot,
        device_type=device.device_type,
        browser=device.browser,
        operating_system=device.operating_system,
        created_at=device.created_at,
    )


# ===========================================
# DEVICE LIST
# ===========================================

@router.get("", response_model=DeviceListResponse)
async def list_devices(
    db: TenantDB,
    user: Annotated[AuthenticatedUser, Depends(require_permission("read:applicants"))],
    risk_level: str | None = None,
    ip_address: str | None = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """List device fingerprints with optional filtering."""
    query = select(DeviceFingerprint).where(
        DeviceFingerprint.tenant_id == user.tenant_id
    )

    if risk_level:
        query = query.where(DeviceFingerprint.risk_level == risk_level)
    if ip_address:
        query = query.where(DeviceFingerprint.ip_address == ip_address)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query) or 0

    # Get paginated results
    query = query.order_by(DeviceFingerprint.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(query)
    devices = result.scalars().all()

    return DeviceListResponse(
        items=[
            DeviceSummary(
                id=d.id,
                session_id=d.session_id,
                applicant_id=d.applicant_id,
                risk_score=d.risk_score,
                risk_level=d.risk_level,
                fraud_score=d.fraud_score,
                flags=d.risk_flags,
                ip_address=d.ip_address,
                country_code=d.country_code,
                city=d.city,
                is_vpn=d.is_vpn,
                is_proxy=d.is_proxy,
                is_tor=d.is_tor,
                is_bot=d.is_bot,
                device_type=d.device_type,
                browser=d.browser,
                operating_system=d.operating_system,
                created_at=d.created_at,
            )
            for d in devices
        ],
        total=total,
        limit=limit,
        offset=offset,
    )


# ===========================================
# STATISTICS
# ===========================================

@router.get("/stats", response_model=DeviceStats)
async def get_device_stats(
    db: TenantDB,
    user: Annotated[AuthenticatedUser, Depends(require_permission("read:applicants"))],
    days: int = Query(30, ge=1, le=365),
):
    """Get fraud detection statistics for the tenant."""
    stats = await device_intel_service.get_stats(
        db=db,
        tenant_id=user.tenant_id,
        days=days,
    )

    return DeviceStats(**stats)


# ===========================================
# QUICK IP CHECK (No storage)
# ===========================================

@router.get("/check-ip/{ip_address}", response_model=IPCheckResponse)
async def quick_ip_check(
    ip_address: str,
    user: Annotated[AuthenticatedUser, Depends(require_permission("read:applicants"))],
):
    """
    Quick IP reputation check without storing results.

    Useful for ad-hoc lookups and testing.
    """
    try:
        result = await device_intel_service.check_ip(ip_address)

        return IPCheckResponse(
            ip_address=result.ip_address,
            fraud_score=result.fraud_score,
            is_proxy=result.is_proxy,
            is_vpn=result.is_vpn,
            is_tor=result.is_tor,
            is_bot=result.is_bot,
            is_datacenter=result.is_datacenter,
            is_mobile=result.is_mobile,
            active_vpn=result.active_vpn,
            active_tor=result.active_tor,
            recent_abuse=result.recent_abuse,
            connection_type=result.connection_type,
            country_code=result.country_code,
            city=result.city,
            region=result.region,
            isp=result.isp,
            asn=result.asn,
        )

    except DeviceIntelError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"IP check failed: {str(e)}",
        )
