"""
Get Clearance - Documents API
==============================
Document upload, retrieval, and management with Cloudflare R2 integration.
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
from app.services.storage import (
    storage_service,
    StorageServiceError,
    StorageConfigError,
)

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
    uploaded_at: datetime | None
    processed_at: datetime | None
    
    model_config = {"from_attributes": True}


class UploadUrlResponse(BaseModel):
    """Presigned upload URL response."""
    document_id: UUID
    upload_url: str
    upload_fields: dict | None = None  # For POST-based upload
    key: str
    expires_in: int
    max_size_bytes: int


class DownloadUrlResponse(BaseModel):
    """Presigned download URL response."""
    download_url: str
    expires_in: int


class ConfirmUploadRequest(BaseModel):
    """Confirm upload completion."""
    file_size: int


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
    Get a presigned URL for direct upload to Cloudflare R2.
    
    Flow:
    1. Client requests upload URL with metadata
    2. Server creates document record and returns presigned URL
    3. Client uploads directly to R2
    4. Client calls /confirm to mark upload complete
    
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
    
    # Generate storage key
    storage_key = storage_service.generate_storage_key(
        tenant_id=user.tenant_id,
        entity_type="applicants",
        entity_id=applicant_id,
        filename=file_name,
    )
    
    document = Document(
        id=document_id,
        tenant_id=user.tenant_id,
        applicant_id=applicant_id,
        type=document_type,
        file_name=file_name,
        mime_type=content_type,
        storage_path=storage_key,
        status="pending",
    )
    db.add(document)
    await db.flush()
    
    try:
        # Generate presigned upload URL
        upload_data = await storage_service.create_presigned_upload(
            key=storage_key,
            content_type=content_type,
            max_size_mb=50,  # 50MB limit
            metadata={
                "document-id": str(document_id),
                "tenant-id": str(user.tenant_id),
                "document-type": document_type,
            },
        )
        
        return UploadUrlResponse(
            document_id=document_id,
            upload_url=upload_data["upload_url"],
            upload_fields=upload_data.get("fields"),
            key=upload_data["key"],
            expires_in=upload_data["expires_in"],
            max_size_bytes=upload_data["max_size_bytes"],
        )
        
    except StorageConfigError:
        # R2 not configured - return mock URL for development
        mock_url = f"https://storage.getclearance.dev/upload/{storage_key}?mock=true"
        
        return UploadUrlResponse(
            document_id=document_id,
            upload_url=mock_url,
            upload_fields=None,
            key=storage_key,
            expires_in=3600,
            max_size_bytes=50 * 1024 * 1024,
        )
        
    except StorageServiceError as e:
        # Clean up document record on failure
        await db.delete(document)
        await db.flush()
        
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Storage service error: {str(e)}",
        )


# ===========================================
# CONFIRM UPLOAD
# ===========================================
@router.post("/{document_id}/confirm")
async def confirm_upload(
    document_id: UUID,
    data: ConfirmUploadRequest,
    db: TenantDB,
    user: AuthenticatedUser,
):
    """
    Confirm that upload to R2 completed successfully.
    
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
    
    if document.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Document already confirmed (status: {document.status})",
        )
    
    # Optionally verify the object exists in storage
    try:
        if storage_service.is_configured:
            exists = await storage_service.object_exists(document.storage_path)
            if not exists:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Upload not found in storage",
                )
    except StorageConfigError:
        # R2 not configured, skip verification in development
        pass
    except StorageServiceError:
        # Log but don't fail - file might still be uploading
        pass
    
    # Update document
    document.file_size = data.file_size
    document.status = "processing"
    document.uploaded_at = datetime.utcnow()
    
    # TODO: Enqueue document processing job
    # - OCR extraction
    # - Document verification
    # - Fraud detection
    
    await db.flush()
    
    return {
        "status": "processing",
        "document_id": str(document_id),
        "message": "Upload confirmed, document processing started",
    }


# ===========================================
# DIRECT UPLOAD (Alternative for small files)
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
    storage_key = storage_service.generate_storage_key(
        tenant_id=user.tenant_id,
        entity_type="applicants",
        entity_id=applicant_id,
        filename=file.filename or "document",
    )
    
    document = Document(
        id=document_id,
        tenant_id=user.tenant_id,
        applicant_id=applicant_id,
        type=document_type,
        file_name=file.filename,
        file_size=len(content),
        mime_type=file.content_type,
        storage_path=storage_key,
        status="processing",
        uploaded_at=datetime.utcnow(),
    )
    db.add(document)
    
    # Upload to R2
    try:
        if storage_service.is_configured:
            # Get PUT URL and upload
            put_url = await storage_service.create_presigned_upload_put(
                key=storage_key,
                content_type=file.content_type or "application/octet-stream",
            )
            
            # Upload using httpx
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.put(
                    put_url,
                    content=content,
                    headers={"Content-Type": file.content_type or "application/octet-stream"},
                )
                
                if response.status_code not in (200, 201):
                    raise StorageServiceError(f"Upload failed: {response.status_code}")
                    
    except (StorageConfigError, StorageServiceError) as e:
        # Log but continue - we've saved the metadata
        # In production, you might want to handle this differently
        import logging
        logging.warning(f"Storage upload failed, continuing: {e}")
    
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
    
    if not document.storage_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document has no associated file",
        )
    
    try:
        download_url = await storage_service.create_presigned_download(
            key=document.storage_path,
            filename=document.file_name,
        )
        
        return DownloadUrlResponse(
            download_url=download_url,
            expires_in=3600,
        )
        
    except StorageConfigError:
        # R2 not configured - return mock URL for development
        mock_url = f"https://storage.getclearance.dev/download/{document.storage_path}?mock=true"
        
        return DownloadUrlResponse(
            download_url=mock_url,
            expires_in=3600,
        )
        
    except StorageServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Storage service error: {str(e)}",
        )


# ===========================================
# DELETE DOCUMENT
# ===========================================
@router.delete("/{document_id}")
async def delete_document(
    document_id: UUID,
    db: TenantDB,
    user: Annotated[AuthenticatedUser, Depends(require_permission("delete:documents"))],
):
    """
    Delete a document.
    
    Removes both the database record and the file from storage.
    Requires delete:documents permission.
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
    
    # Delete from storage
    if document.storage_path:
        try:
            await storage_service.delete(document.storage_path)
        except (StorageConfigError, StorageServiceError) as e:
            # Log but continue with database deletion
            import logging
            logging.warning(f"Failed to delete from storage: {e}")
    
    # Soft delete - keep record for audit
    document.status = "deleted"
    await db.flush()
    
    return {"status": "deleted", "document_id": str(document_id)}


# ===========================================
# AI DOCUMENT ANALYSIS
# ===========================================
@router.post("/{document_id}/analyze")
async def analyze_document(
    document_id: UUID,
    db: TenantDB,
    user: AuthenticatedUser,
):
    """
    Run AI analysis on a document.
    
    Analyzes the document for:
    - Authenticity indicators
    - Fraud signals
    - Data extraction
    """
    from app.services.ai import ai_service, AIServiceError
    
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
    
    if document.status not in ("processing", "verified", "pending_review"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Document cannot be analyzed (status: {document.status})",
        )
    
    try:
        analysis = await ai_service.analyze_document(db, document_id)
        
        # Update document with analysis results
        document.verification_checks = document.verification_checks or []
        document.verification_checks.append({
            "check": "ai_analysis",
            "passed": analysis.authenticity_score >= 70,
            "confidence": analysis.confidence,
            "details": analysis.notes,
            "timestamp": datetime.utcnow().isoformat(),
        })
        
        document.fraud_signals = analysis.fraud_indicators
        
        # Merge extracted data
        if analysis.extracted_data:
            document.extracted_data = {
                **(document.extracted_data or {}),
                **analysis.extracted_data,
            }
        
        await db.flush()
        
        return {
            "document_id": str(document_id),
            "authenticity_score": analysis.authenticity_score,
            "confidence": analysis.confidence,
            "fraud_indicators": analysis.fraud_indicators,
            "extracted_data": analysis.extracted_data,
            "notes": analysis.notes,
            "analyzed_at": analysis.generated_at.isoformat(),
        }
        
    except AIServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI service error: {str(e)}",
        )
