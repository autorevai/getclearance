"""
Get Clearance - Settings API
=============================
API endpoints for tenant settings and team management.
"""

from datetime import datetime, timedelta
from typing import Annotated
from uuid import UUID
import secrets
import hashlib

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import TenantDB, AuthenticatedUser, AuditContext, require_permission, require_role
from app.models.tenant import User, Tenant
from app.models.settings import TenantSettings, TeamInvitation, TeamInvitationStatus
from app.schemas.settings import (
    SettingsResponse,
    GeneralSettingsUpdate,
    NotificationPreferences,
    NotificationSettingsUpdate,
    SecuritySettingsUpdate,
    SecuritySettingsResponse,
    BrandingSettingsUpdate,
    BrandingSettingsResponse,
    TeamMemberResponse,
    TeamMemberListResponse,
    TeamMemberRoleUpdate,
    TeamInviteRequest,
    TeamInvitationResponse,
    TeamInvitationListResponse,
)
from app.services.audit import record_audit_log

router = APIRouter()


# ===========================================
# HELPER FUNCTIONS
# ===========================================

async def get_settings_dict(db: AsyncSession, tenant_id: UUID, category: str) -> dict:
    """Get all settings for a tenant and category as a dict."""
    query = select(TenantSettings).where(
        TenantSettings.tenant_id == tenant_id,
        TenantSettings.category == category,
    )
    result = await db.execute(query)
    settings = result.scalars().all()
    return {s.key: s.value for s in settings}


async def upsert_setting(
    db: AsyncSession,
    tenant_id: UUID,
    category: str,
    key: str,
    value: dict,
    user_id: UUID,
) -> TenantSettings:
    """Create or update a setting."""
    query = select(TenantSettings).where(
        TenantSettings.tenant_id == tenant_id,
        TenantSettings.category == category,
        TenantSettings.key == key,
    )
    result = await db.execute(query)
    setting = result.scalar_one_or_none()

    if setting:
        setting.value = value
        setting.updated_by = user_id
        setting.updated_at = datetime.utcnow()
    else:
        setting = TenantSettings(
            tenant_id=tenant_id,
            category=category,
            key=key,
            value=value,
            updated_by=user_id,
        )
        db.add(setting)

    return setting


# ===========================================
# GET ALL SETTINGS
# ===========================================

@router.get("", response_model=SettingsResponse)
async def get_settings(
    db: TenantDB,
    user: Annotated[AuthenticatedUser, Depends(require_permission("read:settings"))],
):
    """
    Get all tenant settings grouped by category.
    """
    # Get settings for each category
    general = await get_settings_dict(db, user.tenant_id, "general")
    notifications = await get_settings_dict(db, user.tenant_id, "notifications")
    branding = await get_settings_dict(db, user.tenant_id, "branding")
    security = await get_settings_dict(db, user.tenant_id, "security")

    # Also get tenant info for general settings
    tenant_query = select(Tenant).where(Tenant.id == user.tenant_id)
    tenant_result = await db.execute(tenant_query)
    tenant = tenant_result.scalar_one_or_none()

    if tenant:
        general["company_name"] = general.get("company_name", tenant.name)

    return SettingsResponse(
        general=general,
        notifications=notifications,
        branding=branding,
        security=security,
    )


# ===========================================
# GENERAL SETTINGS
# ===========================================

@router.put("/general")
async def update_general_settings(
    data: GeneralSettingsUpdate,
    db: TenantDB,
    user: Annotated[AuthenticatedUser, Depends(require_permission("write:settings"))],
    ctx: AuditContext,
):
    """
    Update general settings (company name, timezone, etc.).
    """
    update_data = data.model_dump(exclude_unset=True)

    # Update company name on tenant if provided
    if "company_name" in update_data:
        tenant_query = select(Tenant).where(Tenant.id == user.tenant_id)
        tenant_result = await db.execute(tenant_query)
        tenant = tenant_result.scalar_one_or_none()
        if tenant:
            tenant.name = update_data["company_name"]

    # Store other settings
    for key, value in update_data.items():
        if value is not None:
            await upsert_setting(
                db, user.tenant_id, "general", key, {"value": value}, UUID(user.id)
            )

    # Audit log
    await record_audit_log(
        db=db,
        tenant_id=user.tenant_id,
        user_id=UUID(user.id),
        action="settings.general_updated",
        resource_type="settings",
        resource_id=user.tenant_id,
        new_values=update_data,
        user_email=user.email,
        ip_address=ctx.ip_address,
    )

    await db.commit()

    return {"status": "success", "message": "General settings updated"}


# ===========================================
# NOTIFICATION SETTINGS
# ===========================================

@router.get("/notifications", response_model=NotificationPreferences)
async def get_notification_preferences(
    db: TenantDB,
    user: Annotated[AuthenticatedUser, Depends(require_permission("read:settings"))],
):
    """
    Get notification preferences.
    """
    settings = await get_settings_dict(db, user.tenant_id, "notifications")

    # Build preferences with defaults
    return NotificationPreferences(
        email_new_applicant=settings.get("email_new_applicant", {}).get("value", True),
        email_review_required=settings.get("email_review_required", {}).get("value", True),
        email_high_risk_alert=settings.get("email_high_risk_alert", {}).get("value", True),
        email_screening_hit=settings.get("email_screening_hit", {}).get("value", True),
        email_case_assigned=settings.get("email_case_assigned", {}).get("value", True),
        email_daily_digest=settings.get("email_daily_digest", {}).get("value", False),
        email_weekly_report=settings.get("email_weekly_report", {}).get("value", True),
    )


@router.put("/notifications")
async def update_notification_preferences(
    data: NotificationSettingsUpdate,
    db: TenantDB,
    user: Annotated[AuthenticatedUser, Depends(require_permission("write:settings"))],
    ctx: AuditContext,
):
    """
    Update notification preferences.
    """
    prefs = data.preferences.model_dump()

    for key, value in prefs.items():
        await upsert_setting(
            db, user.tenant_id, "notifications", key, {"value": value}, UUID(user.id)
        )

    # Audit log
    await record_audit_log(
        db=db,
        tenant_id=user.tenant_id,
        user_id=UUID(user.id),
        action="settings.notifications_updated",
        resource_type="settings",
        resource_id=user.tenant_id,
        new_values=prefs,
        user_email=user.email,
        ip_address=ctx.ip_address,
    )

    await db.commit()

    return {"status": "success", "message": "Notification preferences updated"}


# ===========================================
# SECURITY SETTINGS
# ===========================================

@router.get("/security", response_model=SecuritySettingsResponse)
async def get_security_settings(
    db: TenantDB,
    user: Annotated[AuthenticatedUser, Depends(require_role("admin"))],
):
    """
    Get security settings. Admin only.
    """
    settings = await get_settings_dict(db, user.tenant_id, "security")

    return SecuritySettingsResponse(
        session_timeout_minutes=settings.get("session_timeout_minutes", {}).get("value", 60),
        require_2fa=settings.get("require_2fa", {}).get("value", False),
        password_min_length=settings.get("password_min_length", {}).get("value", 12),
        password_require_uppercase=settings.get("password_require_uppercase", {}).get("value", True),
        password_require_number=settings.get("password_require_number", {}).get("value", True),
        password_require_special=settings.get("password_require_special", {}).get("value", True),
        allowed_ip_ranges=settings.get("allowed_ip_ranges", {}).get("value", []),
    )


@router.put("/security")
async def update_security_settings(
    data: SecuritySettingsUpdate,
    db: TenantDB,
    user: Annotated[AuthenticatedUser, Depends(require_role("admin"))],
    ctx: AuditContext,
):
    """
    Update security settings. Admin only.
    """
    update_data = data.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        if value is not None:
            await upsert_setting(
                db, user.tenant_id, "security", key, {"value": value}, UUID(user.id)
            )

    # Audit log
    await record_audit_log(
        db=db,
        tenant_id=user.tenant_id,
        user_id=UUID(user.id),
        action="settings.security_updated",
        resource_type="settings",
        resource_id=user.tenant_id,
        new_values=update_data,
        user_email=user.email,
        ip_address=ctx.ip_address,
    )

    await db.commit()

    return {"status": "success", "message": "Security settings updated"}


# ===========================================
# BRANDING SETTINGS
# ===========================================

@router.get("/branding", response_model=BrandingSettingsResponse)
async def get_branding_settings(
    db: TenantDB,
    user: Annotated[AuthenticatedUser, Depends(require_permission("read:settings"))],
):
    """
    Get branding settings.
    """
    settings = await get_settings_dict(db, user.tenant_id, "branding")

    return BrandingSettingsResponse(
        logo_url=settings.get("logo_url", {}).get("value"),
        primary_color=settings.get("primary_color", {}).get("value", "#6366f1"),
        accent_color=settings.get("accent_color", {}).get("value", "#818cf8"),
        favicon_url=settings.get("favicon_url", {}).get("value"),
        custom_css=settings.get("custom_css", {}).get("value"),
    )


@router.put("/branding")
async def update_branding_settings(
    data: BrandingSettingsUpdate,
    db: TenantDB,
    user: Annotated[AuthenticatedUser, Depends(require_role("admin"))],
    ctx: AuditContext,
):
    """
    Update branding settings. Admin only.
    """
    update_data = data.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        if value is not None:
            await upsert_setting(
                db, user.tenant_id, "branding", key, {"value": value}, UUID(user.id)
            )

    # Audit log
    await record_audit_log(
        db=db,
        tenant_id=user.tenant_id,
        user_id=UUID(user.id),
        action="settings.branding_updated",
        resource_type="settings",
        resource_id=user.tenant_id,
        new_values=update_data,
        user_email=user.email,
        ip_address=ctx.ip_address,
    )

    await db.commit()

    return {"status": "success", "message": "Branding settings updated"}


# ===========================================
# TEAM MEMBER MANAGEMENT
# ===========================================

@router.get("/team", response_model=TeamMemberListResponse)
async def list_team_members(
    db: TenantDB,
    user: Annotated[AuthenticatedUser, Depends(require_permission("read:settings"))],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    """
    List all team members in the tenant.
    """
    # Count query
    count_query = select(func.count(User.id)).where(User.tenant_id == user.tenant_id)
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    # List query
    query = (
        select(User)
        .where(User.tenant_id == user.tenant_id)
        .order_by(User.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(query)
    members = result.scalars().all()

    return TeamMemberListResponse(
        items=[TeamMemberResponse.model_validate(m) for m in members],
        total=total,
    )


@router.put("/team/{member_id}/role")
async def update_team_member_role(
    member_id: UUID,
    data: TeamMemberRoleUpdate,
    db: TenantDB,
    user: Annotated[AuthenticatedUser, Depends(require_role("admin"))],
    ctx: AuditContext,
):
    """
    Update a team member's role. Admin only.
    """
    # Get the member
    query = select(User).where(
        User.id == member_id,
        User.tenant_id == user.tenant_id,
    )
    result = await db.execute(query)
    member = result.scalar_one_or_none()

    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team member not found",
        )

    # Don't allow changing own role
    if str(member_id) == user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change your own role",
        )

    old_role = member.role
    member.role = data.role

    # Audit log
    await record_audit_log(
        db=db,
        tenant_id=user.tenant_id,
        user_id=UUID(user.id),
        action="team.role_changed",
        resource_type="user",
        resource_id=member_id,
        old_values={"role": old_role},
        new_values={"role": data.role},
        user_email=user.email,
        ip_address=ctx.ip_address,
    )

    await db.commit()

    return {"status": "success", "message": f"Role updated to {data.role}"}


@router.delete("/team/{member_id}")
async def remove_team_member(
    member_id: UUID,
    db: TenantDB,
    user: Annotated[AuthenticatedUser, Depends(require_role("admin"))],
    ctx: AuditContext,
):
    """
    Remove a team member. Admin only.
    """
    # Get the member
    query = select(User).where(
        User.id == member_id,
        User.tenant_id == user.tenant_id,
    )
    result = await db.execute(query)
    member = result.scalar_one_or_none()

    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team member not found",
        )

    # Don't allow removing self
    if str(member_id) == user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove yourself",
        )

    member_email = member.email

    # Soft delete by setting status to inactive
    member.status = "inactive"

    # Audit log
    await record_audit_log(
        db=db,
        tenant_id=user.tenant_id,
        user_id=UUID(user.id),
        action="team.member_removed",
        resource_type="user",
        resource_id=member_id,
        old_values={"email": member_email, "status": "active"},
        new_values={"status": "inactive"},
        user_email=user.email,
        ip_address=ctx.ip_address,
    )

    await db.commit()

    return {"status": "success", "message": "Team member removed"}


# ===========================================
# TEAM INVITATIONS
# ===========================================

@router.get("/team/invitations", response_model=TeamInvitationListResponse)
async def list_invitations(
    db: TenantDB,
    user: Annotated[AuthenticatedUser, Depends(require_role("admin"))],
    status_filter: Annotated[str | None, Query(alias="status")] = None,
):
    """
    List pending team invitations. Admin only.
    """
    query = select(TeamInvitation).where(TeamInvitation.tenant_id == user.tenant_id)

    if status_filter:
        query = query.where(TeamInvitation.status == status_filter)
    else:
        # Default to pending invitations
        query = query.where(TeamInvitation.status == TeamInvitationStatus.PENDING.value)

    query = query.order_by(TeamInvitation.invited_at.desc())

    result = await db.execute(query)
    invitations = result.scalars().all()

    # Filter out expired ones
    valid_invitations = [inv for inv in invitations if not inv.is_expired or inv.status != "pending"]

    return TeamInvitationListResponse(
        items=[TeamInvitationResponse.model_validate(inv) for inv in valid_invitations],
        total=len(valid_invitations),
    )


@router.post("/team/invite", response_model=TeamInvitationResponse, status_code=status.HTTP_201_CREATED)
async def invite_team_member(
    data: TeamInviteRequest,
    db: TenantDB,
    user: Annotated[AuthenticatedUser, Depends(require_role("admin"))],
    ctx: AuditContext,
):
    """
    Invite a new team member. Admin only.
    """
    # Check if user already exists
    existing_user = await db.execute(
        select(User).where(
            User.tenant_id == user.tenant_id,
            User.email == data.email,
        )
    )
    if existing_user.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists in your team",
        )

    # Check for existing pending invitation
    existing_invite = await db.execute(
        select(TeamInvitation).where(
            TeamInvitation.tenant_id == user.tenant_id,
            TeamInvitation.email == data.email,
            TeamInvitation.status == TeamInvitationStatus.PENDING.value,
        )
    )
    existing = existing_invite.scalar_one_or_none()
    if existing and existing.is_valid:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A pending invitation already exists for this email",
        )

    # Generate invitation token
    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode()).hexdigest()

    # Create invitation
    invitation = TeamInvitation(
        tenant_id=user.tenant_id,
        email=data.email,
        role=data.role,
        invited_by=UUID(user.id),
        expires_at=datetime.utcnow() + timedelta(days=7),
        token_hash=token_hash,
    )
    db.add(invitation)

    # Audit log
    await record_audit_log(
        db=db,
        tenant_id=user.tenant_id,
        user_id=UUID(user.id),
        action="team.invitation_sent",
        resource_type="team_invitation",
        resource_id=invitation.id,
        new_values={"email": data.email, "role": data.role},
        user_email=user.email,
        ip_address=ctx.ip_address,
    )

    await db.commit()
    await db.refresh(invitation)

    # TODO: Send invitation email with token

    return TeamInvitationResponse.model_validate(invitation)


@router.delete("/team/invitations/{invitation_id}")
async def cancel_invitation(
    invitation_id: UUID,
    db: TenantDB,
    user: Annotated[AuthenticatedUser, Depends(require_role("admin"))],
    ctx: AuditContext,
):
    """
    Cancel a pending invitation. Admin only.
    """
    query = select(TeamInvitation).where(
        TeamInvitation.id == invitation_id,
        TeamInvitation.tenant_id == user.tenant_id,
    )
    result = await db.execute(query)
    invitation = result.scalar_one_or_none()

    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found",
        )

    if invitation.status != TeamInvitationStatus.PENDING.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only cancel pending invitations",
        )

    invitation.status = TeamInvitationStatus.CANCELLED.value

    # Audit log
    await record_audit_log(
        db=db,
        tenant_id=user.tenant_id,
        user_id=UUID(user.id),
        action="team.invitation_cancelled",
        resource_type="team_invitation",
        resource_id=invitation_id,
        new_values={"email": invitation.email, "status": "cancelled"},
        user_email=user.email,
        ip_address=ctx.ip_address,
    )

    await db.commit()

    return {"status": "success", "message": "Invitation cancelled"}


@router.post("/team/invitations/{invitation_id}/resend")
async def resend_invitation(
    invitation_id: UUID,
    db: TenantDB,
    user: Annotated[AuthenticatedUser, Depends(require_role("admin"))],
    ctx: AuditContext,
):
    """
    Resend an invitation with a new expiration. Admin only.
    """
    query = select(TeamInvitation).where(
        TeamInvitation.id == invitation_id,
        TeamInvitation.tenant_id == user.tenant_id,
    )
    result = await db.execute(query)
    invitation = result.scalar_one_or_none()

    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found",
        )

    if invitation.status != TeamInvitationStatus.PENDING.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only resend pending invitations",
        )

    # Generate new token and extend expiration
    token = secrets.token_urlsafe(32)
    invitation.token_hash = hashlib.sha256(token.encode()).hexdigest()
    invitation.expires_at = datetime.utcnow() + timedelta(days=7)
    invitation.invited_at = datetime.utcnow()

    # Audit log
    await record_audit_log(
        db=db,
        tenant_id=user.tenant_id,
        user_id=UUID(user.id),
        action="team.invitation_resent",
        resource_type="team_invitation",
        resource_id=invitation_id,
        new_values={"email": invitation.email},
        user_email=user.email,
        ip_address=ctx.ip_address,
    )

    await db.commit()

    # TODO: Send invitation email with new token

    return {"status": "success", "message": "Invitation resent"}
