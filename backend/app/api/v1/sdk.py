"""
GetClearance - SDK API
======================
Public API endpoints for the embeddable Web SDK.

These endpoints use SDK tokens (not Auth0 JWTs) to allow end-user
verification flows on customer websites.

Flow:
1. Customer backend calls POST /sdk/access-token with their API key
2. Customer frontend initializes SDK with the access token
3. SDK makes calls to these endpoints to complete verification
"""

from datetime import datetime, timedelta
from typing import Annotated
from uuid import UUID, uuid4
import secrets
import hashlib
import hmac

from fastapi import APIRouter, Depends, HTTPException, Query, Header, Request, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.models import Applicant, Document, Tenant, ApiKey
from app.config import settings
from app.services.storage import storage_service, StorageConfigError, StorageServiceError

router = APIRouter()


# ===========================================
# SCHEMAS
# ===========================================

class SDKAccessTokenRequest(BaseModel):
    """Request to create an SDK access token."""
    external_user_id: str = Field(..., description="Your unique identifier for this user")
    email: EmailStr | None = Field(None, description="User's email (optional but recommended)")
    phone: str | None = Field(None, description="User's phone number (optional)")
    first_name: str | None = Field(None)
    last_name: str | None = Field(None)
    metadata: dict | None = Field(None, description="Custom metadata to attach to the applicant")
    flow_name: str = Field("default", description="Verification flow/workflow name")
    redirect_url: str | None = Field(None, description="URL to redirect after verification completes")
    expires_in: int = Field(3600, ge=300, le=86400, description="Token validity in seconds (5min - 24hr)")


class SDKAccessTokenResponse(BaseModel):
    """SDK access token for frontend initialization."""
    access_token: str
    applicant_id: UUID
    expires_at: datetime
    flow_name: str
    sdk_url: str  # URL to the hosted SDK or CDN


class SDKConfigResponse(BaseModel):
    """SDK configuration for the verification flow."""
    applicant_id: UUID
    flow_name: str
    steps: list[dict]
    branding: dict
    allowed_document_types: list[str]
    require_selfie: bool
    require_liveness: bool
    expires_at: datetime


class SDKDocumentUploadRequest(BaseModel):
    """Request to get an upload URL for document."""
    document_type: str = Field(..., description="Type: passport, driver_license, id_card, etc.")
    side: str = Field("front", description="Document side: front or back")
    file_name: str
    content_type: str = Field(..., description="MIME type: image/jpeg, image/png, application/pdf")


class SDKUploadUrlResponse(BaseModel):
    """Presigned URL for document upload."""
    document_id: UUID
    upload_url: str
    upload_method: str = "PUT"  # or "POST" with fields
    upload_fields: dict | None = None
    expires_in: int
    max_size_bytes: int


class SDKConfirmUploadRequest(BaseModel):
    """Confirm document upload completed."""
    document_id: UUID
    file_size: int


class SDKStepCompleteRequest(BaseModel):
    """Mark a verification step as complete."""
    step_name: str
    data: dict | None = None


class SDKStatusResponse(BaseModel):
    """Current verification status."""
    applicant_id: UUID
    status: str
    steps_completed: list[str]
    steps_remaining: list[str]
    documents: list[dict]
    redirect_url: str | None


# ===========================================
# SDK TOKEN MANAGEMENT
# ===========================================

# In-memory token store (use Redis in production)
_sdk_tokens: dict[str, dict] = {}


def _generate_sdk_token() -> str:
    """Generate a secure SDK token."""
    return f"sdk_{secrets.token_urlsafe(32)}"


def _hash_api_key(api_key: str) -> str:
    """Hash API key for lookup."""
    return hashlib.sha256(api_key.encode()).hexdigest()


async def verify_sdk_token(
    authorization: str = Header(..., description="Bearer sdk_xxx token"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Verify SDK access token and return session data.
    Used as a dependency for SDK endpoints.
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
        )

    token = authorization.replace("Bearer ", "")

    if token not in _sdk_tokens:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired SDK token",
        )

    session = _sdk_tokens[token]

    if datetime.utcnow() > session["expires_at"]:
        del _sdk_tokens[token]
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="SDK token expired",
        )

    # Verify applicant still exists
    query = select(Applicant).where(Applicant.id == session["applicant_id"])
    result = await db.execute(query)
    applicant = result.scalar_one_or_none()

    if not applicant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Applicant not found",
        )

    return {
        **session,
        "applicant": applicant,
        "db": db,
    }


async def verify_api_key(
    x_api_key: str = Header(..., alias="X-API-Key"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Verify API key for server-to-server calls.
    Returns tenant information.
    """
    # For now, use a simple approach - check if key exists in database
    # In production, use hashed keys with proper lookup

    key_hash = _hash_api_key(x_api_key)

    # Check for API key in database
    query = select(ApiKey).where(
        ApiKey.key_hash == key_hash,
        ApiKey.is_active == True,
    )
    result = await db.execute(query)
    api_key = result.scalar_one_or_none()

    if not api_key:
        # Fallback for development: accept any key starting with "test_"
        if settings.DEBUG and x_api_key.startswith("test_"):
            # Get first tenant for development
            tenant_query = select(Tenant).limit(1)
            tenant_result = await db.execute(tenant_query)
            tenant = tenant_result.scalar_one_or_none()

            if tenant:
                return {
                    "tenant_id": tenant.id,
                    "tenant_name": tenant.name,
                    "db": db,
                }

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    return {
        "tenant_id": api_key.tenant_id,
        "api_key_id": api_key.id,
        "db": db,
    }


# ===========================================
# SDK ACCESS TOKEN ENDPOINT (Server-to-Server)
# ===========================================

@router.post("/access-token", response_model=SDKAccessTokenResponse)
async def create_sdk_access_token(
    request: SDKAccessTokenRequest,
    auth: dict = Depends(verify_api_key),
):
    """
    Create an SDK access token for frontend initialization.

    This is called from your backend server with your API key.
    The returned access token is given to your frontend to initialize the SDK.

    Example flow:
    1. User clicks "Verify Identity" on your website
    2. Your backend calls this endpoint
    3. Your backend passes the access_token to your frontend
    4. Frontend loads the SDK with the access_token
    5. SDK guides user through verification
    6. SDK calls your redirect_url when done
    """
    db = auth["db"]
    tenant_id = auth["tenant_id"]

    # Check for existing applicant with this external_id
    query = select(Applicant).where(
        Applicant.tenant_id == tenant_id,
        Applicant.external_id == request.external_user_id,
    )
    result = await db.execute(query)
    applicant = result.scalar_one_or_none()

    if applicant:
        # Update existing applicant if needed
        if request.email and not applicant.email:
            applicant.email = request.email
        if request.first_name and not applicant.first_name:
            applicant.first_name = request.first_name
        if request.last_name and not applicant.last_name:
            applicant.last_name = request.last_name
        applicant.updated_at = datetime.utcnow()
    else:
        # Create new applicant
        applicant = Applicant(
            id=uuid4(),
            tenant_id=tenant_id,
            external_id=request.external_user_id,
            email=request.email,
            phone=request.phone,
            first_name=request.first_name,
            last_name=request.last_name,
            metadata=request.metadata or {},
            source="sdk",
            status="pending",
        )
        db.add(applicant)

    await db.flush()
    await db.refresh(applicant)

    # Generate SDK token
    token = _generate_sdk_token()
    expires_at = datetime.utcnow() + timedelta(seconds=request.expires_in)

    # Store token session
    _sdk_tokens[token] = {
        "token": token,
        "tenant_id": tenant_id,
        "applicant_id": applicant.id,
        "external_user_id": request.external_user_id,
        "flow_name": request.flow_name,
        "redirect_url": request.redirect_url,
        "expires_at": expires_at,
        "created_at": datetime.utcnow(),
    }

    # Construct SDK URL (frontend app or CDN)
    base_url = settings.FRONTEND_URL if hasattr(settings, 'FRONTEND_URL') else "https://app.getclearance.ai"
    sdk_url = f"{base_url}/sdk/verify?token={token}"

    return SDKAccessTokenResponse(
        access_token=token,
        applicant_id=applicant.id,
        expires_at=expires_at,
        flow_name=request.flow_name,
        sdk_url=sdk_url,
    )


# ===========================================
# SDK CONFIGURATION (Called by SDK frontend)
# ===========================================

@router.get("/config", response_model=SDKConfigResponse)
async def get_sdk_config(
    session: dict = Depends(verify_sdk_token),
):
    """
    Get SDK configuration for the verification flow.

    Called by the SDK after initialization to get the steps to display.
    """
    applicant = session["applicant"]

    # Default verification steps
    steps = [
        {
            "name": "consent",
            "title": "Data Processing Consent",
            "description": "We need your consent to process your personal data for identity verification.",
            "required": True,
        },
        {
            "name": "document",
            "title": "Upload ID Document",
            "description": "Upload a valid government-issued ID (passport, driver's license, or ID card).",
            "required": True,
            "options": {
                "document_types": ["passport", "driver_license", "id_card"],
            },
        },
        {
            "name": "selfie",
            "title": "Take a Selfie",
            "description": "Take a photo of yourself to verify you match your ID.",
            "required": True,
        },
        {
            "name": "review",
            "title": "Review & Submit",
            "description": "Review your information before submitting.",
            "required": True,
        },
    ]

    # Default branding (can be customized per tenant)
    branding = {
        "primary_color": "#6366f1",
        "logo_url": None,
        "company_name": "GetClearance",
    }

    return SDKConfigResponse(
        applicant_id=applicant.id,
        flow_name=session["flow_name"],
        steps=steps,
        branding=branding,
        allowed_document_types=["passport", "driver_license", "id_card"],
        require_selfie=True,
        require_liveness=False,  # Enable when liveness is implemented
        expires_at=session["expires_at"],
    )


# ===========================================
# DOCUMENT UPLOAD (Called by SDK)
# ===========================================

@router.post("/documents/upload-url", response_model=SDKUploadUrlResponse)
async def get_sdk_upload_url(
    request: SDKDocumentUploadRequest,
    session: dict = Depends(verify_sdk_token),
):
    """
    Get a presigned URL for document upload.

    The SDK calls this to get a URL where it can upload the document directly.
    """
    applicant = session["applicant"]
    db = session["db"]

    # Create document record
    document_id = uuid4()
    document_type = f"{request.document_type}_{request.side}" if request.side != "front" else request.document_type

    storage_key = storage_service.generate_storage_key(
        tenant_id=session["tenant_id"],
        entity_type="applicants",
        entity_id=applicant.id,
        filename=request.file_name,
    )

    document = Document(
        id=document_id,
        tenant_id=session["tenant_id"],
        applicant_id=applicant.id,
        type=document_type,
        file_name=request.file_name,
        mime_type=request.content_type,
        storage_path=storage_key,
        status="pending",
    )
    db.add(document)
    await db.flush()

    try:
        # Get presigned upload URL
        upload_data = await storage_service.create_presigned_upload(
            key=storage_key,
            content_type=request.content_type,
            max_size_mb=50,
            metadata={
                "document-id": str(document_id),
                "tenant-id": str(session["tenant_id"]),
                "document-type": document_type,
            },
        )

        return SDKUploadUrlResponse(
            document_id=document_id,
            upload_url=upload_data["upload_url"],
            upload_method="PUT",
            upload_fields=upload_data.get("fields"),
            expires_in=upload_data["expires_in"],
            max_size_bytes=upload_data["max_size_bytes"],
        )

    except StorageConfigError:
        # R2 not configured - return mock for development
        return SDKUploadUrlResponse(
            document_id=document_id,
            upload_url=f"https://storage.getclearance.dev/upload/{storage_key}?mock=true",
            upload_method="PUT",
            upload_fields=None,
            expires_in=3600,
            max_size_bytes=50 * 1024 * 1024,
        )


@router.post("/documents/confirm")
async def confirm_sdk_upload(
    request: SDKConfirmUploadRequest,
    session: dict = Depends(verify_sdk_token),
):
    """
    Confirm document upload completed.

    Called by SDK after successful upload to R2.
    """
    db = session["db"]

    query = select(Document).where(
        Document.id == request.document_id,
        Document.applicant_id == session["applicant_id"],
    )
    result = await db.execute(query)
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    document.file_size = request.file_size
    document.status = "processing"
    document.uploaded_at = datetime.utcnow()

    await db.flush()

    # TODO: Trigger document processing (OCR, verification)

    return {
        "status": "processing",
        "document_id": str(request.document_id),
        "message": "Upload confirmed, processing started",
    }


# ===========================================
# STEP COMPLETION (Called by SDK)
# ===========================================

@router.post("/steps/complete")
async def complete_sdk_step(
    request: SDKStepCompleteRequest,
    session: dict = Depends(verify_sdk_token),
):
    """
    Mark a verification step as complete.
    """
    applicant = session["applicant"]
    db = session["db"]

    # Record step completion in applicant metadata
    steps_completed = applicant.metadata.get("sdk_steps_completed", [])
    if request.step_name not in steps_completed:
        steps_completed.append(request.step_name)

    applicant.metadata = {
        **applicant.metadata,
        "sdk_steps_completed": steps_completed,
        f"step_{request.step_name}_data": request.data,
        f"step_{request.step_name}_completed_at": datetime.utcnow().isoformat(),
    }
    applicant.updated_at = datetime.utcnow()

    # Check if consent step was completed
    if request.step_name == "consent" and request.data:
        applicant.consent_given = request.data.get("consent", False)
        applicant.consent_given_at = datetime.utcnow()

    await db.flush()

    return {
        "status": "completed",
        "step_name": request.step_name,
        "steps_completed": steps_completed,
    }


# ===========================================
# VERIFICATION STATUS (Called by SDK)
# ===========================================

@router.get("/status", response_model=SDKStatusResponse)
async def get_sdk_status(
    session: dict = Depends(verify_sdk_token),
):
    """
    Get current verification status.

    Called by SDK to check progress and show appropriate screens.
    """
    applicant = session["applicant"]
    db = session["db"]

    # Get applicant's documents
    doc_query = select(Document).where(Document.applicant_id == applicant.id)
    doc_result = await db.execute(doc_query)
    documents = doc_result.scalars().all()

    # Determine completed and remaining steps
    steps_completed = applicant.metadata.get("sdk_steps_completed", [])

    all_steps = ["consent", "document", "selfie", "review"]
    steps_remaining = [s for s in all_steps if s not in steps_completed]

    # If all steps complete, update applicant status
    if not steps_remaining and applicant.status == "pending":
        applicant.status = "in_progress"
        applicant.updated_at = datetime.utcnow()
        await db.flush()

    return SDKStatusResponse(
        applicant_id=applicant.id,
        status=applicant.status,
        steps_completed=steps_completed,
        steps_remaining=steps_remaining,
        documents=[
            {
                "id": str(doc.id),
                "type": doc.type,
                "status": doc.status,
                "uploaded_at": doc.uploaded_at.isoformat() if doc.uploaded_at else None,
            }
            for doc in documents
        ],
        redirect_url=session.get("redirect_url"),
    )


# ===========================================
# SUBMIT VERIFICATION (Called by SDK)
# ===========================================

@router.post("/submit")
async def submit_verification(
    session: dict = Depends(verify_sdk_token),
):
    """
    Submit verification for review.

    Called when the user completes all SDK steps.
    """
    applicant = session["applicant"]
    db = session["db"]

    # Validate all required steps are complete
    steps_completed = applicant.metadata.get("sdk_steps_completed", [])
    required_steps = ["consent", "document"]

    missing_steps = [s for s in required_steps if s not in steps_completed]
    if missing_steps:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Missing required steps: {', '.join(missing_steps)}",
        )

    # Check for at least one document
    doc_query = select(Document).where(
        Document.applicant_id == applicant.id,
        Document.status.in_(["processing", "verified", "pending_review"]),
    )
    doc_result = await db.execute(doc_query)
    documents = doc_result.scalars().all()

    if not documents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No documents uploaded",
        )

    # Update applicant status
    applicant.status = "in_progress"
    applicant.submitted_at = datetime.utcnow()
    applicant.metadata = {
        **applicant.metadata,
        "sdk_submitted_at": datetime.utcnow().isoformat(),
    }
    applicant.updated_at = datetime.utcnow()

    await db.flush()

    # TODO: Trigger background verification:
    # - AML screening
    # - Document OCR
    # - AI analysis

    return {
        "status": "submitted",
        "applicant_id": str(applicant.id),
        "message": "Verification submitted for review",
        "redirect_url": session.get("redirect_url"),
    }
