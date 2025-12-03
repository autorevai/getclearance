"""
Get Clearance - Questionnaires API
===================================
API endpoints for managing custom questionnaires and responses.

Endpoints:
    GET    /api/v1/questionnaires                    - List questionnaires
    POST   /api/v1/questionnaires                    - Create questionnaire
    GET    /api/v1/questionnaires/{id}               - Get questionnaire
    PUT    /api/v1/questionnaires/{id}               - Update questionnaire
    DELETE /api/v1/questionnaires/{id}               - Delete questionnaire

    POST   /api/v1/applicants/{id}/questionnaire     - Submit answers
    GET    /api/v1/applicants/{id}/questionnaire     - Get submitted answers
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.dependencies import require_permission
from app.models.questionnaire import Questionnaire, QuestionnaireResponse, DEFAULT_QUESTIONNAIRES
from app.models.applicant import Applicant
from app.models.company import Company
from app.models.tenant import User


router = APIRouter()


# ============================================
# PYDANTIC SCHEMAS
# ============================================

class QuestionSchema(BaseModel):
    """Schema for a single question."""
    id: str = Field(..., description="Unique question identifier")
    type: str = Field(..., description="Question type: text, textarea, select, multi_select, date, number, file, boolean")
    label: str = Field(..., description="Question label/text")
    description: str | None = Field(None, description="Additional help text")
    required: bool = Field(False, description="Whether answer is required")
    options: list[str] | None = Field(None, description="Options for select/multi_select")
    risk_scores: dict[str, int] | None = Field(None, description="Risk scores per option")
    order: int = Field(0, description="Display order")
    conditional: dict[str, Any] | None = Field(None, description="Conditional display logic")


class QuestionnaireCreate(BaseModel):
    """Schema for creating a questionnaire."""
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    internal_notes: str | None = None
    questionnaire_type: str = Field("general", description="Type: general, source_of_funds, pep_declaration, etc.")
    questions: list[QuestionSchema] = Field(default_factory=list)
    is_required: bool = False
    is_active: bool = True


class QuestionnaireUpdate(BaseModel):
    """Schema for updating a questionnaire."""
    name: str | None = None
    description: str | None = None
    internal_notes: str | None = None
    questionnaire_type: str | None = None
    questions: list[QuestionSchema] | None = None
    is_required: bool | None = None
    is_active: bool | None = None


class QuestionnaireResponse_Out(BaseModel):
    """Schema for questionnaire output."""
    id: UUID
    name: str
    description: str | None
    questionnaire_type: str
    questions: list[dict[str, Any]]
    is_required: bool
    is_active: bool
    version: int
    question_count: int
    times_completed: int
    average_risk_score: int | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class QuestionnaireListResponse(BaseModel):
    """Paginated list of questionnaires."""
    items: list[QuestionnaireResponse_Out]
    total: int
    page: int
    page_size: int
    pages: int


class AnswerSubmission(BaseModel):
    """Schema for submitting questionnaire answers."""
    questionnaire_id: UUID
    answers: dict[str, Any] = Field(..., description="Answers keyed by question ID")


class ResponseOut(BaseModel):
    """Schema for questionnaire response output."""
    id: UUID
    questionnaire_id: UUID
    questionnaire_name: str | None = None
    applicant_id: UUID | None
    company_id: UUID | None
    answers: dict[str, Any]
    risk_score: int | None
    risk_breakdown: dict[str, Any] | None
    status: str
    is_complete: bool
    submitted_at: datetime | None
    reviewed_at: datetime | None
    review_notes: str | None
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================
# HELPER FUNCTIONS
# ============================================

def calculate_risk_score(questionnaire: Questionnaire, answers: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    """
    Calculate risk score based on answers.

    Returns:
        Tuple of (total_score, breakdown_dict)
    """
    total_score = 0
    breakdown = {}

    if not questionnaire.questions:
        return 0, {}

    for question in questionnaire.questions:
        q_id = question.get("id")
        if q_id not in answers:
            continue

        answer = answers[q_id]
        risk_scores = question.get("risk_scores", {})

        if not risk_scores:
            continue

        q_score = 0

        # Handle different question types
        q_type = question.get("type", "text")

        if q_type == "boolean":
            # Boolean answers: convert to string for lookup
            answer_key = str(answer).lower()
            q_score = risk_scores.get(answer_key, 0)
        elif q_type == "multi_select" and isinstance(answer, list):
            # Multi-select: sum scores for all selected options
            for selected in answer:
                q_score += risk_scores.get(selected, 0)
        else:
            # Single value (text, select, etc.)
            q_score = risk_scores.get(str(answer), 0)

        total_score += q_score
        breakdown[q_id] = {
            "answer": answer,
            "score": q_score,
            "label": question.get("label", q_id)
        }

    return total_score, breakdown


# ============================================
# QUESTIONNAIRE CRUD ENDPOINTS
# ============================================

@router.get("", response_model=QuestionnaireListResponse)
async def list_questionnaires(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    questionnaire_type: str | None = None,
    is_active: bool | None = None,
    search: str | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("questionnaires:read")),
):
    """
    List questionnaires for the tenant.

    Supports filtering by type, active status, and search.
    """
    query = select(Questionnaire).where(Questionnaire.tenant_id == user.tenant_id)
    count_query = select(func.count(Questionnaire.id)).where(Questionnaire.tenant_id == user.tenant_id)

    # Apply filters
    if questionnaire_type:
        query = query.where(Questionnaire.questionnaire_type == questionnaire_type)
        count_query = count_query.where(Questionnaire.questionnaire_type == questionnaire_type)

    if is_active is not None:
        query = query.where(Questionnaire.is_active == is_active)
        count_query = count_query.where(Questionnaire.is_active == is_active)

    if search:
        search_filter = Questionnaire.name.ilike(f"%{search}%")
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)

    # Get total count
    total = (await db.execute(count_query)).scalar() or 0

    # Apply pagination and ordering
    query = query.order_by(Questionnaire.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    questionnaires = result.scalars().all()

    return QuestionnaireListResponse(
        items=[
            QuestionnaireResponse_Out(
                id=q.id,
                name=q.name,
                description=q.description,
                questionnaire_type=q.questionnaire_type,
                questions=q.questions or [],
                is_required=q.is_required,
                is_active=q.is_active,
                version=q.version,
                question_count=q.question_count,
                times_completed=q.times_completed,
                average_risk_score=q.average_risk_score,
                created_at=q.created_at,
                updated_at=q.updated_at,
            )
            for q in questionnaires
        ],
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size if total > 0 else 0,
    )


@router.post("", response_model=QuestionnaireResponse_Out, status_code=status.HTTP_201_CREATED)
async def create_questionnaire(
    data: QuestionnaireCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("questionnaires:write")),
):
    """
    Create a new questionnaire.
    """
    # Calculate max possible risk score
    max_risk = 0
    for question in data.questions:
        risk_scores = question.risk_scores or {}
        if risk_scores:
            # For multi_select, assume all could be selected
            if question.type == "multi_select":
                max_risk += sum(risk_scores.values())
            else:
                max_risk += max(risk_scores.values()) if risk_scores else 0

    questionnaire = Questionnaire(
        tenant_id=user.tenant_id,
        name=data.name,
        description=data.description,
        internal_notes=data.internal_notes,
        questionnaire_type=data.questionnaire_type,
        questions=[q.model_dump() for q in data.questions],
        is_required=data.is_required,
        is_active=data.is_active,
        max_risk_score=max_risk if max_risk > 0 else None,
        created_by=user.id,
    )

    db.add(questionnaire)
    await db.commit()
    await db.refresh(questionnaire)

    return QuestionnaireResponse_Out(
        id=questionnaire.id,
        name=questionnaire.name,
        description=questionnaire.description,
        questionnaire_type=questionnaire.questionnaire_type,
        questions=questionnaire.questions or [],
        is_required=questionnaire.is_required,
        is_active=questionnaire.is_active,
        version=questionnaire.version,
        question_count=questionnaire.question_count,
        times_completed=questionnaire.times_completed,
        average_risk_score=questionnaire.average_risk_score,
        created_at=questionnaire.created_at,
        updated_at=questionnaire.updated_at,
    )


@router.get("/templates", response_model=list[dict])
async def list_templates(
    user: User = Depends(require_permission("questionnaires:read")),
):
    """
    Get default questionnaire templates that can be used as starting points.
    """
    return DEFAULT_QUESTIONNAIRES


@router.post("/initialize-defaults", status_code=status.HTTP_201_CREATED)
async def initialize_default_questionnaires(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("questionnaires:write")),
):
    """
    Initialize default questionnaire templates for the tenant.

    Creates Source of Funds, PEP Declaration, and Tax Residency questionnaires
    if they don't already exist.
    """
    created = []

    for template in DEFAULT_QUESTIONNAIRES:
        # Check if already exists
        existing = await db.execute(
            select(Questionnaire).where(
                and_(
                    Questionnaire.tenant_id == user.tenant_id,
                    Questionnaire.questionnaire_type == template["questionnaire_type"]
                )
            )
        )
        if existing.scalar_one_or_none():
            continue

        # Calculate max risk
        max_risk = 0
        for question in template["questions"]:
            risk_scores = question.get("risk_scores", {})
            if risk_scores:
                max_risk += max(risk_scores.values())

        questionnaire = Questionnaire(
            tenant_id=user.tenant_id,
            name=template["name"],
            description=template["description"],
            questionnaire_type=template["questionnaire_type"],
            questions=template["questions"],
            is_required=template["is_required"],
            max_risk_score=max_risk if max_risk > 0 else None,
            created_by=user.id,
        )
        db.add(questionnaire)
        created.append(template["name"])

    await db.commit()

    return {
        "message": f"Created {len(created)} questionnaires",
        "created": created
    }


@router.get("/{questionnaire_id}", response_model=QuestionnaireResponse_Out)
async def get_questionnaire(
    questionnaire_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("questionnaires:read")),
):
    """
    Get a specific questionnaire by ID.
    """
    result = await db.execute(
        select(Questionnaire).where(
            and_(
                Questionnaire.id == questionnaire_id,
                Questionnaire.tenant_id == user.tenant_id,
            )
        )
    )
    questionnaire = result.scalar_one_or_none()

    if not questionnaire:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Questionnaire not found"
        )

    return QuestionnaireResponse_Out(
        id=questionnaire.id,
        name=questionnaire.name,
        description=questionnaire.description,
        questionnaire_type=questionnaire.questionnaire_type,
        questions=questionnaire.questions or [],
        is_required=questionnaire.is_required,
        is_active=questionnaire.is_active,
        version=questionnaire.version,
        question_count=questionnaire.question_count,
        times_completed=questionnaire.times_completed,
        average_risk_score=questionnaire.average_risk_score,
        created_at=questionnaire.created_at,
        updated_at=questionnaire.updated_at,
    )


@router.put("/{questionnaire_id}", response_model=QuestionnaireResponse_Out)
async def update_questionnaire(
    questionnaire_id: UUID,
    data: QuestionnaireUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("questionnaires:write")),
):
    """
    Update a questionnaire.

    Increments version if questions are modified.
    """
    result = await db.execute(
        select(Questionnaire).where(
            and_(
                Questionnaire.id == questionnaire_id,
                Questionnaire.tenant_id == user.tenant_id,
            )
        )
    )
    questionnaire = result.scalar_one_or_none()

    if not questionnaire:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Questionnaire not found"
        )

    # Track if questions changed for versioning
    questions_changed = False

    # Update fields
    if data.name is not None:
        questionnaire.name = data.name
    if data.description is not None:
        questionnaire.description = data.description
    if data.internal_notes is not None:
        questionnaire.internal_notes = data.internal_notes
    if data.questionnaire_type is not None:
        questionnaire.questionnaire_type = data.questionnaire_type
    if data.is_required is not None:
        questionnaire.is_required = data.is_required
    if data.is_active is not None:
        questionnaire.is_active = data.is_active

    if data.questions is not None:
        questions_changed = True
        questionnaire.questions = [q.model_dump() for q in data.questions]

        # Recalculate max risk
        max_risk = 0
        for question in data.questions:
            risk_scores = question.risk_scores or {}
            if risk_scores:
                if question.type == "multi_select":
                    max_risk += sum(risk_scores.values())
                else:
                    max_risk += max(risk_scores.values()) if risk_scores else 0
        questionnaire.max_risk_score = max_risk if max_risk > 0 else None

    # Increment version if questions changed
    if questions_changed:
        questionnaire.version += 1

    await db.commit()
    await db.refresh(questionnaire)

    return QuestionnaireResponse_Out(
        id=questionnaire.id,
        name=questionnaire.name,
        description=questionnaire.description,
        questionnaire_type=questionnaire.questionnaire_type,
        questions=questionnaire.questions or [],
        is_required=questionnaire.is_required,
        is_active=questionnaire.is_active,
        version=questionnaire.version,
        question_count=questionnaire.question_count,
        times_completed=questionnaire.times_completed,
        average_risk_score=questionnaire.average_risk_score,
        created_at=questionnaire.created_at,
        updated_at=questionnaire.updated_at,
    )


@router.delete("/{questionnaire_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_questionnaire(
    questionnaire_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("questionnaires:write")),
):
    """
    Delete a questionnaire.

    Note: This will also delete all associated responses.
    """
    result = await db.execute(
        select(Questionnaire).where(
            and_(
                Questionnaire.id == questionnaire_id,
                Questionnaire.tenant_id == user.tenant_id,
            )
        )
    )
    questionnaire = result.scalar_one_or_none()

    if not questionnaire:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Questionnaire not found"
        )

    await db.delete(questionnaire)
    await db.commit()


# ============================================
# RESPONSE SUBMISSION ENDPOINTS
# ============================================

@router.post("/responses/applicant/{applicant_id}", response_model=ResponseOut, status_code=status.HTTP_201_CREATED)
async def submit_applicant_questionnaire(
    applicant_id: UUID,
    data: AnswerSubmission,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("applicants:write")),
):
    """
    Submit questionnaire answers for an applicant.

    Calculates risk score based on answers and updates questionnaire statistics.
    """
    # Verify applicant exists and belongs to tenant
    applicant_result = await db.execute(
        select(Applicant).where(
            and_(
                Applicant.id == applicant_id,
                Applicant.tenant_id == user.tenant_id,
            )
        )
    )
    applicant = applicant_result.scalar_one_or_none()

    if not applicant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Applicant not found"
        )

    # Get questionnaire
    questionnaire_result = await db.execute(
        select(Questionnaire).where(
            and_(
                Questionnaire.id == data.questionnaire_id,
                Questionnaire.tenant_id == user.tenant_id,
            )
        )
    )
    questionnaire = questionnaire_result.scalar_one_or_none()

    if not questionnaire:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Questionnaire not found"
        )

    if not questionnaire.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Questionnaire is not active"
        )

    # Check for existing response
    existing_result = await db.execute(
        select(QuestionnaireResponse).where(
            and_(
                QuestionnaireResponse.questionnaire_id == data.questionnaire_id,
                QuestionnaireResponse.applicant_id == applicant_id,
            )
        )
    )
    existing = existing_result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Questionnaire already submitted for this applicant. Use PUT to update."
        )

    # Calculate risk score
    risk_score, risk_breakdown = calculate_risk_score(questionnaire, data.answers)

    # Get IP and user agent for audit
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    # Create response
    response = QuestionnaireResponse(
        questionnaire_id=data.questionnaire_id,
        applicant_id=applicant_id,
        answers=data.answers,
        risk_score=risk_score,
        risk_breakdown=risk_breakdown,
        status="submitted",
        submitted_at=datetime.utcnow(),
        submitted_by=user.id,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    db.add(response)

    # Update questionnaire statistics
    questionnaire.times_completed += 1
    if questionnaire.average_risk_score is None:
        questionnaire.average_risk_score = risk_score
    else:
        # Running average calculation
        total = questionnaire.average_risk_score * (questionnaire.times_completed - 1) + risk_score
        questionnaire.average_risk_score = total // questionnaire.times_completed

    await db.commit()
    await db.refresh(response)

    return ResponseOut(
        id=response.id,
        questionnaire_id=response.questionnaire_id,
        questionnaire_name=questionnaire.name,
        applicant_id=response.applicant_id,
        company_id=response.company_id,
        answers=response.answers,
        risk_score=response.risk_score,
        risk_breakdown=response.risk_breakdown,
        status=response.status,
        is_complete=response.is_complete,
        submitted_at=response.submitted_at,
        reviewed_at=response.reviewed_at,
        review_notes=response.review_notes,
        created_at=response.created_at,
    )


@router.get("/responses/applicant/{applicant_id}", response_model=list[ResponseOut])
async def get_applicant_questionnaires(
    applicant_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("applicants:read")),
):
    """
    Get all questionnaire responses for an applicant.
    """
    # Verify applicant exists and belongs to tenant
    applicant_result = await db.execute(
        select(Applicant).where(
            and_(
                Applicant.id == applicant_id,
                Applicant.tenant_id == user.tenant_id,
            )
        )
    )
    applicant = applicant_result.scalar_one_or_none()

    if not applicant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Applicant not found"
        )

    # Get responses with questionnaire data
    result = await db.execute(
        select(QuestionnaireResponse)
        .options(selectinload(QuestionnaireResponse.questionnaire))
        .where(QuestionnaireResponse.applicant_id == applicant_id)
        .order_by(QuestionnaireResponse.created_at.desc())
    )
    responses = result.scalars().all()

    return [
        ResponseOut(
            id=r.id,
            questionnaire_id=r.questionnaire_id,
            questionnaire_name=r.questionnaire.name if r.questionnaire else None,
            applicant_id=r.applicant_id,
            company_id=r.company_id,
            answers=r.answers,
            risk_score=r.risk_score,
            risk_breakdown=r.risk_breakdown,
            status=r.status,
            is_complete=r.is_complete,
            submitted_at=r.submitted_at,
            reviewed_at=r.reviewed_at,
            review_notes=r.review_notes,
            created_at=r.created_at,
        )
        for r in responses
    ]


@router.put("/responses/{response_id}", response_model=ResponseOut)
async def update_questionnaire_response(
    response_id: UUID,
    data: AnswerSubmission,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("applicants:write")),
):
    """
    Update a questionnaire response (resubmit answers).
    """
    # Get response with questionnaire
    result = await db.execute(
        select(QuestionnaireResponse)
        .options(selectinload(QuestionnaireResponse.questionnaire))
        .where(QuestionnaireResponse.id == response_id)
    )
    response = result.scalar_one_or_none()

    if not response:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Response not found"
        )

    # Verify tenant access
    if response.questionnaire.tenant_id != user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Response not found"
        )

    # Recalculate risk score
    risk_score, risk_breakdown = calculate_risk_score(response.questionnaire, data.answers)

    # Update response
    response.answers = data.answers
    response.risk_score = risk_score
    response.risk_breakdown = risk_breakdown
    response.status = "submitted"
    response.submitted_at = datetime.utcnow()
    response.submitted_by = user.id

    await db.commit()
    await db.refresh(response)

    return ResponseOut(
        id=response.id,
        questionnaire_id=response.questionnaire_id,
        questionnaire_name=response.questionnaire.name,
        applicant_id=response.applicant_id,
        company_id=response.company_id,
        answers=response.answers,
        risk_score=response.risk_score,
        risk_breakdown=response.risk_breakdown,
        status=response.status,
        is_complete=response.is_complete,
        submitted_at=response.submitted_at,
        reviewed_at=response.reviewed_at,
        review_notes=response.review_notes,
        created_at=response.created_at,
    )


@router.post("/responses/{response_id}/review", response_model=ResponseOut)
async def review_questionnaire_response(
    response_id: UUID,
    status_update: str = Query(..., description="New status: reviewed, flagged"),
    review_notes: str | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("applicants:write")),
):
    """
    Review a questionnaire response.
    """
    # Get response with questionnaire
    result = await db.execute(
        select(QuestionnaireResponse)
        .options(selectinload(QuestionnaireResponse.questionnaire))
        .where(QuestionnaireResponse.id == response_id)
    )
    response = result.scalar_one_or_none()

    if not response:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Response not found"
        )

    # Verify tenant access
    if response.questionnaire.tenant_id != user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Response not found"
        )

    if status_update not in ["reviewed", "flagged"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid status. Must be 'reviewed' or 'flagged'"
        )

    # Update response
    response.status = status_update
    response.reviewed_at = datetime.utcnow()
    response.reviewed_by = user.id
    if review_notes:
        response.review_notes = review_notes

    await db.commit()
    await db.refresh(response)

    return ResponseOut(
        id=response.id,
        questionnaire_id=response.questionnaire_id,
        questionnaire_name=response.questionnaire.name,
        applicant_id=response.applicant_id,
        company_id=response.company_id,
        answers=response.answers,
        risk_score=response.risk_score,
        risk_breakdown=response.risk_breakdown,
        status=response.status,
        is_complete=response.is_complete,
        submitted_at=response.submitted_at,
        reviewed_at=response.reviewed_at,
        review_notes=response.review_notes,
        created_at=response.created_at,
    )


# ============================================
# COMPANY QUESTIONNAIRE ENDPOINTS (KYB)
# ============================================

@router.post("/responses/company/{company_id}", response_model=ResponseOut, status_code=status.HTTP_201_CREATED)
async def submit_company_questionnaire(
    company_id: UUID,
    data: AnswerSubmission,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("companies:write")),
):
    """
    Submit questionnaire answers for a company (KYB).
    """
    # Verify company exists and belongs to tenant
    company_result = await db.execute(
        select(Company).where(
            and_(
                Company.id == company_id,
                Company.tenant_id == user.tenant_id,
            )
        )
    )
    company = company_result.scalar_one_or_none()

    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )

    # Get questionnaire
    questionnaire_result = await db.execute(
        select(Questionnaire).where(
            and_(
                Questionnaire.id == data.questionnaire_id,
                Questionnaire.tenant_id == user.tenant_id,
            )
        )
    )
    questionnaire = questionnaire_result.scalar_one_or_none()

    if not questionnaire:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Questionnaire not found"
        )

    if not questionnaire.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Questionnaire is not active"
        )

    # Check for existing response
    existing_result = await db.execute(
        select(QuestionnaireResponse).where(
            and_(
                QuestionnaireResponse.questionnaire_id == data.questionnaire_id,
                QuestionnaireResponse.company_id == company_id,
            )
        )
    )
    existing = existing_result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Questionnaire already submitted for this company. Use PUT to update."
        )

    # Calculate risk score
    risk_score, risk_breakdown = calculate_risk_score(questionnaire, data.answers)

    # Get IP and user agent for audit
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    # Create response
    response = QuestionnaireResponse(
        questionnaire_id=data.questionnaire_id,
        company_id=company_id,
        answers=data.answers,
        risk_score=risk_score,
        risk_breakdown=risk_breakdown,
        status="submitted",
        submitted_at=datetime.utcnow(),
        submitted_by=user.id,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    db.add(response)

    # Update questionnaire statistics
    questionnaire.times_completed += 1
    if questionnaire.average_risk_score is None:
        questionnaire.average_risk_score = risk_score
    else:
        total = questionnaire.average_risk_score * (questionnaire.times_completed - 1) + risk_score
        questionnaire.average_risk_score = total // questionnaire.times_completed

    await db.commit()
    await db.refresh(response)

    return ResponseOut(
        id=response.id,
        questionnaire_id=response.questionnaire_id,
        questionnaire_name=questionnaire.name,
        applicant_id=response.applicant_id,
        company_id=response.company_id,
        answers=response.answers,
        risk_score=response.risk_score,
        risk_breakdown=response.risk_breakdown,
        status=response.status,
        is_complete=response.is_complete,
        submitted_at=response.submitted_at,
        reviewed_at=response.reviewed_at,
        review_notes=response.review_notes,
        created_at=response.created_at,
    )


@router.get("/responses/company/{company_id}", response_model=list[ResponseOut])
async def get_company_questionnaires(
    company_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("companies:read")),
):
    """
    Get all questionnaire responses for a company.
    """
    # Verify company exists and belongs to tenant
    company_result = await db.execute(
        select(Company).where(
            and_(
                Company.id == company_id,
                Company.tenant_id == user.tenant_id,
            )
        )
    )
    company = company_result.scalar_one_or_none()

    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )

    # Get responses with questionnaire data
    result = await db.execute(
        select(QuestionnaireResponse)
        .options(selectinload(QuestionnaireResponse.questionnaire))
        .where(QuestionnaireResponse.company_id == company_id)
        .order_by(QuestionnaireResponse.created_at.desc())
    )
    responses = result.scalars().all()

    return [
        ResponseOut(
            id=r.id,
            questionnaire_id=r.questionnaire_id,
            questionnaire_name=r.questionnaire.name if r.questionnaire else None,
            applicant_id=r.applicant_id,
            company_id=r.company_id,
            answers=r.answers,
            risk_score=r.risk_score,
            risk_breakdown=r.risk_breakdown,
            status=r.status,
            is_complete=r.is_complete,
            submitted_at=r.submitted_at,
            reviewed_at=r.reviewed_at,
            review_notes=r.review_notes,
            created_at=r.created_at,
        )
        for r in responses
    ]
