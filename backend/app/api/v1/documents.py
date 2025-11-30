"""
Get Clearance - Documents API
==============================
Document upload, retrieval, and management.
"""

from datetime import datetime
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import TenantDB, AuthenticatedUser, require_permission
from app.models import Document, Applicant

router = APIRouter()


# ===========================================
# SCHEMAS
# ===========================================

class DocumentResponse(BaseModel):
    """Document metadata response."""
    id: UUID
    type: str
    file_name: str | None
    file_size: int | None
    mime_type: str | None
    status: str
    ocr_confidence: float | None
    extracted_data: dict | None
    uploaded_at: datetime
    processed_at: datetime | None
    
    model_config = {"from_attributes": True}


class UploadUrlResponse(BaseModel):
    """Presigned upload URL response."""
    document_id: UUID
    upload_url: str
    expires_in: int


class DownloadUrlResponse(BaseModel):
    """Presigned download URL response."""
    download_url: str
    expires_in: int


# ===========================================
# GET PRESIGNED UPLOAD URL
# ===========================================
@router.post("/upload-url", response_model=UploadUrlResponse)
async def get_upload_url(
    db: TenantDB,
    user: AuthenticatedUser,
    applicant_id: UUID = Form(...),
    document_type: str = Form(...),
    file_name: str = Form(...),
    content_type: str = Form(...),
):
    """
    Get a presigned URL for direct upload to R2/S3.
    
    Flow:
    1. Client requests upload URL with metadata
    2. Server creates document record and returns presigned URL
    3. Client uploads directly to R2/S3
    4. Client confirms upload complete
    
    This approach keeps large files off the API server.
    """
    # Verify applicant exists and belongs to tenant
    query = select(Applicant).where(
        Applicant.id == applicant_id,
        Applicant.tenant_id == user.tenant_id,
    )
    result = await db.execute(query)
    applicant = result.scalar_one_or_none()
    
    if not applicant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Applicant not found",
        )
    
    # Create document record
    document_id = uuid4()
    storage_path = f"{user.tenant_id}/applicants/{applicant_id}/{document_id}"
    
    document = Document(
        id=document_id,
        tenant_id=user.tenant_id,
        applicant_id=applicant_id,
        type=document_type,
        file_name=file_name,
        mime_type=content_type,
        storage_path=storage_path,
        status="pending",
    )
    db.add(document)
    await db.flush()
    
    # TODO: Generate actual presigned URL from R2/S3
    # For now, return placeholder
    upload_url = f"https://storage.getclearance.com/upload/{storage_path}?token=PLACEHOLDER"
    
    return UploadUrlResponse(
        document_id=document_id,
        upload_url=upload_url,
        expires_in=3600,
    )


# ===========================================
# CONFIRM UPLOAD
# ===========================================
@router.post("/{document_id}/confirm")
async def confirm_upload(
    document_id: UUID,
    db: TenantDB,
    user: AuthenticatedUser,
    file_size: int = Form(...),
):
    """
    Confirm that upload to R2/S3 completed successfully.
    
    This triggers document processing (OCR, verification, etc.).
    """
    query = select(Document).where(
        Document.id == document_id,
        Document.tenant_id == user.tenant_id,
    )
    result = await db.execute(query)
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    
    # Update document
    document.file_size = file_size
    document.status = "processing"
    document.uploaded_at = datetime.utcnow()
    
    # TODO: Enqueue document processing job
    # - OCR extraction
    # - Document verification
    # - Fraud detection
    
    await db.flush()
    
    return {"status": "processing", "document_id": str(document_id)}


# ===========================================
# DIRECT UPLOAD (Alternative)
# ===========================================
@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    db: TenantDB,
    user: AuthenticatedUser,
    file: UploadFile = File(...),
    applicant_id: UUID = Form(...),
    document_type: str = Form(...),
):
    """
    Direct upload endpoint for smaller files (< 10MB).
    
    For larger files, use the presigned URL flow.
    """
    # Validate file size (10MB limit)
    max_size = 10 * 1024 * 1024
    content = await file.read()
    if len(content) > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File too large. Use presigned URL for files > 10MB",
        )
    
    # Verify applicant
    query = select(Applicant).where(
        Applicant.id == applicant_id,
        Applicant.tenant_id == user.tenant_id,
    )
    result = await db.execute(query)
    applicant = result.scalar_one_or_none()
    
    if not applicant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Applicant not found",
        )
    
    # Create document record
    document_id = uuid4()
    storage_path = f"{user.tenant_id}/applicants/{applicant_id}/{document_id}"
    
    document = Document(
        id=document_id,
        tenant_id=user.tenant_id,
        applicant_id=applicant_id,
        type=document_type,
        file_name=file.filename,
        file_size=len(content),
        mime_type=file.content_type,
        storage_path=storage_path,
        status="processing",
        uploaded_at=datetime.utcnow(),
    )
    db.add(document)
    
    # TODO: Upload to R2/S3
    # TODO: Enqueue processing job
    
    await db.flush()
    await db.refresh(document)
    
    return DocumentResponse.model_validate(document)


# ===========================================
# GET DOCUMENT
# ===========================================
@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: UUID,
    db: TenantDB,
    user: AuthenticatedUser,
):
    """
    Get document metadata.
    """
    query = select(Document).where(
        Document.id == document_id,
        Document.tenant_id == user.tenant_id,
    )
    result = await db.execute(query)
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    
    return DocumentResponse.model_validate(document)


# ===========================================
# GET DOWNLOAD URL
# ===========================================
@router.get("/{document_id}/download", response_model=DownloadUrlResponse)
async def get_download_url(
    document_id: UUID,
    db: TenantDB,
    user: AuthenticatedUser,
):
    """
    Get a presigned download URL for a document.
    """
    query = select(Document).where(
        Document.id == document_id,
        Document.tenant_id == user.tenant_id,
    )
    result = await db.execute(query)
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    
    # TODO: Generate actual presigned URL from R2/S3
    download_url = f"https://storage.getclearance.com/download/{document.storage_path}?token=PLACEHOLDER"
    
    return DownloadUrlResponse(
        download_url=download_url,
        expires_in=3600,
    )
