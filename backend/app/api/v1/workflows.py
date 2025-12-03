"""
Get Clearance - Workflows API
==============================
Risk-based workflow rule management and applicant risk assessment.

Endpoints:
    GET  /api/v1/workflows/rules              - List workflow rules
    POST /api/v1/workflows/rules              - Create rule
    GET  /api/v1/workflows/rules/{id}         - Get rule details
    PUT  /api/v1/workflows/rules/{id}         - Update rule
    DELETE /api/v1/workflows/rules/{id}       - Delete rule
    POST /api/v1/workflows/rules/{id}/test    - Test rule against applicant

    GET  /api/v1/applicants/{id}/risk         - Get risk assessment
    POST /api/v1/applicants/{id}/risk/recalculate - Recalculate risk
"""

from datetime import datetime
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.dependencies import TenantDB, AuthenticatedUser, AuditContext, require_permission
from app.models import Applicant
from app.models.workflow import WorkflowRule, RiskAssessmentLog, DEFAULT_WORKFLOW_RULES
from app.services.risk_engine import risk_engine, RiskAssessment
from app.services.audit import record_audit_log

router = APIRouter()


# ===========================================
# SCHEMAS
# ===========================================

class WorkflowRuleCreate(BaseModel):
    """Create a new workflow rule."""
    name: str = Field(..., max_length=255)
    description: str | None = None
    conditions: dict[str, Any] = Field(default_factory=dict)
    action: str = Field(..., pattern="^(auto_approve|manual_review|auto_reject|escalate|hold)$")
    assign_to_user_id: UUID | None = None
    assign_to_role: str | None = None
    notify_on_match: bool = False
    notification_channels: list[str] = Field(default_factory=list)
    priority: int = Field(default=0, ge=0, le=10000)
    is_active: bool = True


class WorkflowRuleUpdate(BaseModel):
    """Update an existing workflow rule."""
    name: str | None = Field(None, max_length=255)
    description: str | None = None
    conditions: dict[str, Any] | None = None
    action: str | None = Field(None, pattern="^(auto_approve|manual_review|auto_reject|escalate|hold)$")
    assign_to_user_id: UUID | None = None
    assign_to_role: str | None = None
    notify_on_match: bool | None = None
    notification_channels: list[str] | None = None
    priority: int | None = Field(None, ge=0, le=10000)
    is_active: bool | None = None


class WorkflowRuleResponse(BaseModel):
    """Workflow rule details."""
    id: UUID
    tenant_id: UUID
    name: str
    description: str | None
    conditions: dict[str, Any]
    condition_summary: str
    action: str
    assign_to_user_id: UUID | None
    assign_to_role: str | None
    notify_on_match: bool
    notification_channels: list[str]
    priority: int
    is_active: bool
    times_matched: int
    last_matched_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class WorkflowRuleListResponse(BaseModel):
    """List of workflow rules."""
    items: list[WorkflowRuleResponse]
    total: int


class RiskSignalResponse(BaseModel):
    """Individual risk signal."""
    category: str
    signal_name: str
    score: int
    weight: float
    description: str
    details: dict[str, Any]


class RiskAssessmentResponse(BaseModel):
    """Risk assessment result."""
    applicant_id: UUID
    overall_level: str
    overall_score: int
    recommended_action: str
    signals: list[RiskSignalResponse]
    assessment_time: datetime
    applied_rule_name: str | None = None
    final_action: str | None = None


class TestRuleRequest(BaseModel):
    """Test a rule against an applicant."""
    applicant_id: UUID


class TestRuleResponse(BaseModel):
    """Result of testing a rule."""
    rule_id: UUID
    rule_name: str
    applicant_id: UUID
    matches: bool
    condition_results: dict[str, Any]


# ===========================================
# WORKFLOW RULES CRUD
# ===========================================

@router.get("/rules", response_model=WorkflowRuleListResponse)
async def list_workflow_rules(
    db: TenantDB,
    user: AuthenticatedUser,
    is_active: bool | None = Query(None),
    action: str | None = Query(None),
    sort_by: str = Query("priority", description="Sort by: priority, name, created_at"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
):
    """List all workflow rules for the tenant."""
    query = select(WorkflowRule).where(WorkflowRule.tenant_id == user.tenant_id)

    if is_active is not None:
        query = query.where(WorkflowRule.is_active == is_active)
    if action:
        query = query.where(WorkflowRule.action == action)

    # Sort
    sort_column = getattr(WorkflowRule, sort_by, WorkflowRule.priority)
    if sort_order == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    result = await db.execute(query)
    rules = result.scalars().all()

    return WorkflowRuleListResponse(
        items=[WorkflowRuleResponse.model_validate(r) for r in rules],
        total=len(rules),
    )


@router.post("/rules", response_model=WorkflowRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_workflow_rule(
    data: WorkflowRuleCreate,
    db: TenantDB,
    user: Annotated[AuthenticatedUser, Depends(require_permission("admin:workflows"))],
    ctx: AuditContext,
):
    """Create a new workflow rule."""
    rule = WorkflowRule(
        tenant_id=user.tenant_id,
        name=data.name,
        description=data.description,
        conditions=data.conditions,
        action=data.action,
        assign_to_user_id=data.assign_to_user_id,
        assign_to_role=data.assign_to_role,
        notify_on_match=data.notify_on_match,
        notification_channels=data.notification_channels,
        priority=data.priority,
        is_active=data.is_active,
        created_by=UUID(user.id),
    )

    db.add(rule)
    await db.flush()

    # Audit log
    await record_audit_log(
        db=db,
        tenant_id=user.tenant_id,
        user_id=UUID(user.id),
        action="workflow_rule.created",
        resource_type="workflow_rule",
        resource_id=rule.id,
        new_values={
            "name": data.name,
            "action": data.action,
            "priority": data.priority,
        },
        user_email=user.email,
        ip_address=ctx.ip_address,
    )

    await db.refresh(rule)
    return WorkflowRuleResponse.model_validate(rule)


@router.get("/rules/{rule_id}", response_model=WorkflowRuleResponse)
async def get_workflow_rule(
    rule_id: UUID,
    db: TenantDB,
    user: AuthenticatedUser,
):
    """Get workflow rule details."""
    rule = await db.get(WorkflowRule, rule_id)

    if not rule or rule.tenant_id != user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow rule not found",
        )

    return WorkflowRuleResponse.model_validate(rule)


@router.put("/rules/{rule_id}", response_model=WorkflowRuleResponse)
async def update_workflow_rule(
    rule_id: UUID,
    data: WorkflowRuleUpdate,
    db: TenantDB,
    user: Annotated[AuthenticatedUser, Depends(require_permission("admin:workflows"))],
    ctx: AuditContext,
):
    """Update a workflow rule."""
    rule = await db.get(WorkflowRule, rule_id)

    if not rule or rule.tenant_id != user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow rule not found",
        )

    # Track changes for audit
    update_data = data.model_dump(exclude_unset=True)
    old_values = {}
    for field in update_data.keys():
        old_values[field] = getattr(rule, field, None)

    # Update fields
    for field, value in update_data.items():
        setattr(rule, field, value)

    rule.last_modified_by = UUID(user.id)
    rule.updated_at = datetime.utcnow()

    # Audit log
    await record_audit_log(
        db=db,
        tenant_id=user.tenant_id,
        user_id=UUID(user.id),
        action="workflow_rule.updated",
        resource_type="workflow_rule",
        resource_id=rule.id,
        old_values=old_values,
        new_values=update_data,
        user_email=user.email,
        ip_address=ctx.ip_address,
    )

    await db.flush()
    await db.refresh(rule)
    return WorkflowRuleResponse.model_validate(rule)


@router.delete("/rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workflow_rule(
    rule_id: UUID,
    db: TenantDB,
    user: Annotated[AuthenticatedUser, Depends(require_permission("admin:workflows"))],
    ctx: AuditContext,
):
    """Delete a workflow rule."""
    rule = await db.get(WorkflowRule, rule_id)

    if not rule or rule.tenant_id != user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow rule not found",
        )

    # Audit log before deletion
    await record_audit_log(
        db=db,
        tenant_id=user.tenant_id,
        user_id=UUID(user.id),
        action="workflow_rule.deleted",
        resource_type="workflow_rule",
        resource_id=rule.id,
        old_values={
            "name": rule.name,
            "action": rule.action,
        },
        user_email=user.email,
        ip_address=ctx.ip_address,
    )

    await db.delete(rule)
    await db.commit()


@router.post("/rules/{rule_id}/test", response_model=TestRuleResponse)
async def test_workflow_rule(
    rule_id: UUID,
    data: TestRuleRequest,
    db: TenantDB,
    user: AuthenticatedUser,
):
    """Test a workflow rule against a specific applicant."""
    rule = await db.get(WorkflowRule, rule_id)

    if not rule or rule.tenant_id != user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow rule not found",
        )

    applicant = await db.get(Applicant, data.applicant_id)

    if not applicant or applicant.tenant_id != user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Applicant not found",
        )

    # Calculate risk assessment
    assessment = await risk_engine.calculate_risk(db, applicant)

    # Test if rule matches
    matches = risk_engine._rule_matches(rule, applicant, assessment)

    # Build condition results
    condition_results = {}
    for key, expected in (rule.conditions or {}).items():
        actual = None
        if key == "risk_level":
            actual = assessment.overall_level.value
        elif key == "country":
            actual = applicant.nationality or applicant.country_of_residence
        elif key == "has_sanctions_hit":
            actual = any(s.signal_name == "sanctions_hit" for s in assessment.signals)
        elif key == "has_pep_hit":
            actual = any(s.signal_name == "pep_hit" for s in assessment.signals)
        else:
            actual = getattr(applicant, key, None)

        condition_results[key] = {
            "expected": expected,
            "actual": actual,
            "matches": actual in expected if isinstance(expected, list) else actual == expected,
        }

    return TestRuleResponse(
        rule_id=rule.id,
        rule_name=rule.name,
        applicant_id=applicant.id,
        matches=matches,
        condition_results=condition_results,
    )


@router.post("/rules/seed-defaults")
async def seed_default_rules(
    db: TenantDB,
    user: Annotated[AuthenticatedUser, Depends(require_permission("admin:workflows"))],
):
    """Seed default workflow rules for the tenant."""
    # Check if rules already exist
    existing = await db.execute(
        select(func.count(WorkflowRule.id)).where(
            WorkflowRule.tenant_id == user.tenant_id
        )
    )
    count = existing.scalar() or 0

    if count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tenant already has {count} workflow rules. Delete them first to re-seed.",
        )

    # Create default rules
    created = []
    for rule_data in DEFAULT_WORKFLOW_RULES:
        rule = WorkflowRule(
            tenant_id=user.tenant_id,
            name=rule_data["name"],
            description=rule_data.get("description"),
            conditions=rule_data.get("conditions", {}),
            action=rule_data["action"],
            assign_to_role=rule_data.get("assign_to_role"),
            notify_on_match=rule_data.get("notify_on_match", False),
            priority=rule_data.get("priority", 0),
            is_active=True,
            created_by=UUID(user.id),
        )
        db.add(rule)
        created.append(rule_data["name"])

    await db.commit()

    return {
        "status": "success",
        "rules_created": len(created),
        "rule_names": created,
    }


# ===========================================
# RISK ASSESSMENT ENDPOINTS
# ===========================================

@router.get("/risk/{applicant_id}", response_model=RiskAssessmentResponse)
async def get_risk_assessment(
    applicant_id: UUID,
    db: TenantDB,
    user: AuthenticatedUser,
):
    """
    Get risk assessment for an applicant.

    Returns the most recent risk assessment. If none exists,
    calculates a new one.
    """
    applicant = await db.get(Applicant, applicant_id)

    if not applicant or applicant.tenant_id != user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Applicant not found",
        )

    # Check for existing assessment
    existing_query = (
        select(RiskAssessmentLog)
        .where(RiskAssessmentLog.applicant_id == applicant_id)
        .order_by(RiskAssessmentLog.created_at.desc())
        .limit(1)
    )
    result = await db.execute(existing_query)
    existing = result.scalar_one_or_none()

    if existing:
        # Return existing assessment
        return RiskAssessmentResponse(
            applicant_id=applicant_id,
            overall_level=existing.overall_level,
            overall_score=existing.overall_score,
            recommended_action=existing.recommended_action,
            signals=[RiskSignalResponse(**s) for s in existing.signals],
            assessment_time=existing.created_at,
            applied_rule_name=existing.applied_rule.name if existing.applied_rule else None,
            final_action=existing.final_action,
        )

    # Calculate new assessment
    assessment = await risk_engine.calculate_risk(db, applicant)

    return RiskAssessmentResponse(
        applicant_id=applicant_id,
        overall_level=assessment.overall_level.value,
        overall_score=assessment.overall_score,
        recommended_action=assessment.recommended_action,
        signals=[
            RiskSignalResponse(
                category=s.category.value,
                signal_name=s.signal_name,
                score=s.score,
                weight=s.weight,
                description=s.description,
                details=s.details,
            )
            for s in assessment.signals
        ],
        assessment_time=assessment.assessment_time,
    )


@router.post("/risk/{applicant_id}/recalculate", response_model=RiskAssessmentResponse)
async def recalculate_risk(
    applicant_id: UUID,
    db: TenantDB,
    user: Annotated[AuthenticatedUser, Depends(require_permission("write:applicants"))],
    ctx: AuditContext,
    apply_workflow: bool = Query(True, description="Apply workflow rules after calculation"),
):
    """
    Recalculate risk assessment for an applicant.

    This performs a fresh risk calculation and optionally applies
    workflow rules to determine the final action.
    """
    query = (
        select(Applicant)
        .where(
            Applicant.id == applicant_id,
            Applicant.tenant_id == user.tenant_id,
        )
        .options(
            selectinload(Applicant.screening_checks),
            selectinload(Applicant.documents),
        )
    )
    result = await db.execute(query)
    applicant = result.scalar_one_or_none()

    if not applicant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Applicant not found",
        )

    # Calculate risk
    assessment = await risk_engine.calculate_risk(
        db=db,
        applicant=applicant,
        screening_checks=applicant.screening_checks,
        documents=applicant.documents,
    )

    # Apply workflow rules if requested
    final_action = assessment.recommended_action
    applied_rule: WorkflowRule | None = None

    if apply_workflow:
        final_action = await risk_engine.apply_workflow_rules(
            db=db,
            applicant=applicant,
            assessment=assessment,
            tenant_id=user.tenant_id,
        )

        # Find which rule was applied (if any)
        if final_action != assessment.recommended_action:
            rules_query = (
                select(WorkflowRule)
                .where(
                    WorkflowRule.tenant_id == user.tenant_id,
                    WorkflowRule.is_active == True,
                    WorkflowRule.action == final_action,
                )
                .order_by(WorkflowRule.priority.desc())
                .limit(1)
            )
            rules_result = await db.execute(rules_query)
            applied_rule = rules_result.scalar_one_or_none()

            # Update rule match statistics
            if applied_rule:
                applied_rule.times_matched += 1
                applied_rule.last_matched_at = datetime.utcnow()

    # Log the assessment
    log_entry = RiskAssessmentLog(
        tenant_id=user.tenant_id,
        applicant_id=applicant_id,
        overall_level=assessment.overall_level.value,
        overall_score=assessment.overall_score,
        signals=[
            {
                "category": s.category.value,
                "signal_name": s.signal_name,
                "score": s.score,
                "weight": s.weight,
                "description": s.description,
                "details": s.details,
            }
            for s in assessment.signals
        ],
        recommended_action=assessment.recommended_action,
        applied_rule_id=applied_rule.id if applied_rule else None,
        final_action=final_action,
    )
    db.add(log_entry)

    # Update applicant risk score
    applicant.risk_score = assessment.overall_score
    applicant.risk_factors = [
        {
            "category": s.category.value,
            "signal": s.signal_name,
            "score": s.score,
            "description": s.description,
        }
        for s in assessment.signals
        if s.score > 20  # Only include significant signals
    ]

    # Audit log
    await record_audit_log(
        db=db,
        tenant_id=user.tenant_id,
        user_id=UUID(user.id),
        action="risk.recalculated",
        resource_type="applicant",
        resource_id=applicant_id,
        new_values={
            "risk_score": assessment.overall_score,
            "risk_level": assessment.overall_level.value,
            "recommended_action": assessment.recommended_action,
            "final_action": final_action,
        },
        user_email=user.email,
        ip_address=ctx.ip_address,
    )

    await db.commit()

    return RiskAssessmentResponse(
        applicant_id=applicant_id,
        overall_level=assessment.overall_level.value,
        overall_score=assessment.overall_score,
        recommended_action=assessment.recommended_action,
        signals=[
            RiskSignalResponse(
                category=s.category.value,
                signal_name=s.signal_name,
                score=s.score,
                weight=s.weight,
                description=s.description,
                details=s.details,
            )
            for s in assessment.signals
        ],
        assessment_time=assessment.assessment_time,
        applied_rule_name=applied_rule.name if applied_rule else None,
        final_action=final_action,
    )


@router.get("/risk/{applicant_id}/history")
async def get_risk_history(
    applicant_id: UUID,
    db: TenantDB,
    user: AuthenticatedUser,
    limit: int = Query(10, ge=1, le=100),
):
    """Get risk assessment history for an applicant."""
    # Verify applicant exists and belongs to tenant
    applicant = await db.get(Applicant, applicant_id)
    if not applicant or applicant.tenant_id != user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Applicant not found",
        )

    query = (
        select(RiskAssessmentLog)
        .where(RiskAssessmentLog.applicant_id == applicant_id)
        .order_by(RiskAssessmentLog.created_at.desc())
        .limit(limit)
        .options(selectinload(RiskAssessmentLog.applied_rule))
    )
    result = await db.execute(query)
    logs = result.scalars().all()

    return {
        "applicant_id": str(applicant_id),
        "assessments": [
            {
                "id": str(log.id),
                "overall_level": log.overall_level,
                "overall_score": log.overall_score,
                "recommended_action": log.recommended_action,
                "final_action": log.final_action,
                "applied_rule": log.applied_rule.name if log.applied_rule else None,
                "created_at": log.created_at.isoformat(),
            }
            for log in logs
        ],
    }
