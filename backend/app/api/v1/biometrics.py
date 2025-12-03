"""
Get Clearance - Biometrics API
==============================
API endpoints for face matching and liveness detection.

This is a placeholder implementation for development.
Production integration with AWS Rekognition will be added in Terminal 5.

Endpoints:
    POST /api/v1/biometrics/compare      - Compare two faces
    POST /api/v1/biometrics/liveness     - Check liveness
    POST /api/v1/biometrics/detect       - Detect faces in image
    POST /api/v1/biometrics/verify/{id}  - Complete applicant verification
    GET  /api/v1/biometrics/status       - Service status
"""

import base64
from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel, Field
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_permission
from app.models.applicant import Applicant
from app.models.document import Document
from app.models.tenant import User
from app.services.biometrics import (
    biometrics_service,
    FaceComparisonResult,
    LivenessResult,
    FaceDetectionResult,
)


router = APIRouter()


# ===========================================
# PYDANTIC SCHEMAS
# ===========================================

class FaceCompareRequest(BaseModel):
    """Request to compare two faces."""
    source_image: str = Field(..., description="Base64 encoded source image (ID photo)")
    target_image: str = Field(..., description="Base64 encoded target image (selfie)")
    similarity_threshold: float = Field(90.0, ge=0, le=100, description="Minimum similarity for match")


class LivenessRequest(BaseModel):
    """Request for liveness detection."""
    image: str = Field(..., description="Base64 encoded face image")
    session_id: str | None = Field(None, description="Optional session ID for multi-frame check")


class FaceDetectRequest(BaseModel):
    """Request for face detection."""
    image: str = Field(..., description="Base64 encoded image")


class FaceQualityResponse(BaseModel):
    """Face quality metrics."""
    brightness: float
    sharpness: float
    contrast: float
    pose: dict[str, float]
    eyes_open: bool
    mouth_open: bool
    sunglasses: bool
    is_acceptable: bool


class FaceCompareResponse(BaseModel):
    """Face comparison response."""
    match: bool
    result: str
    similarity: float
    confidence: float
    source_face_quality: FaceQualityResponse | None
    target_face_quality: FaceQualityResponse | None
    processing_time_ms: int
    is_mock: bool
    error_message: str | None


class LivenessResponse(BaseModel):
    """Liveness detection response."""
    is_live: bool
    confidence: float
    confidence_level: str
    quality: FaceQualityResponse | None
    age_range: dict[str, int] | None
    challenges_passed: list[str]
    anti_spoofing_score: float
    processing_time_ms: int
    is_mock: bool
    error_message: str | None


class FaceDetectResponse(BaseModel):
    """Face detection response."""
    faces_detected: int
    primary_face_bounds: dict | None
    quality: FaceQualityResponse | None
    emotions: dict[str, float] | None
    gender: str | None
    age_range: dict[str, int] | None
    is_mock: bool
    error_message: str | None


class ApplicantVerifyResponse(BaseModel):
    """Applicant biometric verification response."""
    applicant_id: str
    verified: bool
    face_match: FaceCompareResponse | None
    liveness: LivenessResponse | None
    overall_confidence: float
    failure_reasons: list[str]
    verified_at: str
    processing_time_ms: int
    is_mock: bool


class BiometricsStatusResponse(BaseModel):
    """Biometrics service status."""
    is_configured: bool
    provider: str
    mock_mode: bool
    capabilities: list[str]


# ===========================================
# HELPER FUNCTIONS
# ===========================================

def decode_base64_image(base64_string: str) -> bytes:
    """Decode base64 image, handling data URL format."""
    # Remove data URL prefix if present
    if "," in base64_string:
        base64_string = base64_string.split(",", 1)[1]

    try:
        return base64.b64decode(base64_string)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid base64 image: {str(e)}"
        )


def convert_face_quality(quality) -> FaceQualityResponse | None:
    """Convert FaceQuality dataclass to response model."""
    if quality is None:
        return None

    return FaceQualityResponse(
        brightness=quality.brightness,
        sharpness=quality.sharpness,
        contrast=quality.contrast,
        pose={
            "pitch": quality.pose_pitch,
            "yaw": quality.pose_yaw,
            "roll": quality.pose_roll,
        },
        eyes_open=quality.eyes_open,
        mouth_open=quality.mouth_open,
        sunglasses=quality.sunglasses,
        is_acceptable=quality.is_acceptable,
    )


# ===========================================
# ENDPOINTS
# ===========================================

@router.post("/compare", response_model=FaceCompareResponse)
async def compare_faces(
    request: FaceCompareRequest,
    user: User = Depends(require_permission("applicants:read")),
):
    """
    Compare two faces for matching.

    Compares a source image (typically ID photo) with a target image (selfie)
    and returns similarity score and match status.

    Note: Currently returns mock data. AWS Rekognition integration coming in Terminal 5.
    """
    source_bytes = decode_base64_image(request.source_image)
    target_bytes = decode_base64_image(request.target_image)

    result = await biometrics_service.compare_faces(
        source_bytes,
        target_bytes,
        request.similarity_threshold,
    )

    return FaceCompareResponse(
        match=result.match,
        result=result.result.value,
        similarity=result.similarity,
        confidence=result.confidence,
        source_face_quality=convert_face_quality(result.source_face_quality),
        target_face_quality=convert_face_quality(result.target_face_quality),
        processing_time_ms=result.processing_time_ms,
        is_mock=result.is_mock,
        error_message=result.error_message,
    )


@router.post("/liveness", response_model=LivenessResponse)
async def detect_liveness(
    request: LivenessRequest,
    user: User = Depends(require_permission("applicants:read")),
):
    """
    Detect if an image contains a live person.

    Performs anti-spoofing analysis to detect photo-of-photo attacks,
    screen presentations, masks, and other spoofing attempts.

    Note: Currently returns mock data. AWS Rekognition integration coming in Terminal 5.
    """
    image_bytes = decode_base64_image(request.image)

    result = await biometrics_service.detect_liveness(
        image_bytes,
        request.session_id,
    )

    return LivenessResponse(
        is_live=result.is_live,
        confidence=result.confidence,
        confidence_level=result.confidence_level.value,
        quality=convert_face_quality(result.quality),
        age_range={"min": result.age_range[0], "max": result.age_range[1]} if result.age_range else None,
        challenges_passed=result.challenges_passed,
        anti_spoofing_score=result.anti_spoofing_score,
        processing_time_ms=result.processing_time_ms,
        is_mock=result.is_mock,
        error_message=result.error_message,
    )


@router.post("/detect", response_model=FaceDetectResponse)
async def detect_faces(
    request: FaceDetectRequest,
    user: User = Depends(require_permission("applicants:read")),
):
    """
    Detect faces in an image.

    Returns face count, bounding boxes, quality metrics, and optional
    attributes like age range and emotions.

    Note: Currently returns mock data. AWS Rekognition integration coming in Terminal 5.
    """
    image_bytes = decode_base64_image(request.image)

    result = await biometrics_service.detect_faces(image_bytes)

    return FaceDetectResponse(
        faces_detected=result.faces_detected,
        primary_face_bounds=result.primary_face_bounds,
        quality=convert_face_quality(result.quality),
        emotions=result.emotions,
        gender=result.gender,
        age_range={"min": result.age_range[0], "max": result.age_range[1]} if result.age_range else None,
        is_mock=result.is_mock,
        error_message=result.error_message,
    )


@router.post("/verify/{applicant_id}", response_model=ApplicantVerifyResponse)
async def verify_applicant_biometrics(
    applicant_id: UUID,
    selfie_image: str = Form(..., description="Base64 encoded selfie image"),
    check_liveness: bool = Form(True, description="Whether to perform liveness check"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("applicants:write")),
):
    """
    Perform complete biometric verification for an applicant.

    Compares the applicant's ID document photo with the provided selfie
    and optionally performs liveness detection.

    Updates the applicant's document records with biometric verification results.

    Note: Currently returns mock data. AWS Rekognition integration coming in Terminal 5.
    """
    # Get applicant
    result = await db.execute(
        select(Applicant).where(
            and_(
                Applicant.id == applicant_id,
                Applicant.tenant_id == user.tenant_id,
            )
        )
    )
    applicant = result.scalar_one_or_none()

    if not applicant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Applicant not found"
        )

    # Get ID document with photo
    doc_result = await db.execute(
        select(Document).where(
            and_(
                Document.applicant_id == applicant_id,
                Document.document_type.in_(["passport", "id_card", "drivers_license", "identity"]),
            )
        ).order_by(Document.created_at.desc())
    )
    id_document = doc_result.scalar_one_or_none()

    if not id_document:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No ID document found for applicant. Please upload ID document first."
        )

    # For now, we'll use the selfie as both source and target in mock mode
    # In production, we'd fetch the ID photo from storage
    selfie_bytes = decode_base64_image(selfie_image)

    # In production, fetch ID photo from R2:
    # id_photo_bytes = await storage_service.download(id_document.storage_key)

    # For mock mode, use selfie for both (will show high similarity)
    id_photo_bytes = selfie_bytes

    # Perform verification
    verification_result = await biometrics_service.verify_applicant_selfie(
        id_photo=id_photo_bytes,
        selfie=selfie_bytes,
        applicant_id=applicant_id,
        check_liveness=check_liveness,
    )

    # Update document with biometric results
    if id_document:
        biometric_data = id_document.verification_result or {}
        biometric_data["biometrics"] = {
            "verified": verification_result["verified"],
            "face_match_score": verification_result["face_match"]["similarity"] if verification_result["face_match"] else None,
            "liveness_score": verification_result["liveness"]["confidence"] if verification_result["liveness"] else None,
            "checked_at": datetime.utcnow().isoformat(),
            "is_mock": verification_result["is_mock"],
        }
        id_document.verification_result = biometric_data

        # Also update the document biometric fields (if migration has been applied)
        if hasattr(id_document, 'face_match_score'):
            id_document.face_match_score = verification_result["face_match"]["similarity"] if verification_result["face_match"] else None
        if hasattr(id_document, 'liveness_score'):
            id_document.liveness_score = verification_result["liveness"]["confidence"] if verification_result["liveness"] else None
        if hasattr(id_document, 'biometrics_checked_at'):
            id_document.biometrics_checked_at = datetime.utcnow()

        await db.commit()

    # Convert nested results for response
    face_match_response = None
    if verification_result["face_match"]:
        fm = verification_result["face_match"]
        face_match_response = FaceCompareResponse(
            match=fm["match"],
            result=fm["result"],
            similarity=fm["similarity"],
            confidence=fm["confidence"],
            source_face_quality=fm["source_face_quality"],
            target_face_quality=fm["target_face_quality"],
            processing_time_ms=fm["processing_time_ms"],
            is_mock=fm["is_mock"],
            error_message=fm.get("error_message"),
        )

    liveness_response = None
    if verification_result["liveness"]:
        lv = verification_result["liveness"]
        liveness_response = LivenessResponse(
            is_live=lv["is_live"],
            confidence=lv["confidence"],
            confidence_level=lv["confidence_level"],
            quality=lv["quality"],
            age_range=lv["age_range"],
            challenges_passed=lv["challenges_passed"],
            anti_spoofing_score=lv["anti_spoofing_score"],
            processing_time_ms=lv["processing_time_ms"],
            is_mock=lv["is_mock"],
            error_message=lv.get("error_message"),
        )

    return ApplicantVerifyResponse(
        applicant_id=verification_result["applicant_id"],
        verified=verification_result["verified"],
        face_match=face_match_response,
        liveness=liveness_response,
        overall_confidence=verification_result["overall_confidence"],
        failure_reasons=verification_result["failure_reasons"],
        verified_at=verification_result["verified_at"],
        processing_time_ms=verification_result.get("processing_time_ms", 0),
        is_mock=verification_result["is_mock"],
    )


@router.post("/verify-upload/{applicant_id}", response_model=ApplicantVerifyResponse)
async def verify_applicant_with_upload(
    applicant_id: UUID,
    selfie: UploadFile = File(..., description="Selfie image file"),
    check_liveness: bool = Form(True),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("applicants:write")),
):
    """
    Verify applicant biometrics using file upload.

    Alternative to base64 encoded image for larger files.
    """
    # Read file content
    selfie_bytes = await selfie.read()

    if len(selfie_bytes) > 10 * 1024 * 1024:  # 10MB limit
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File too large. Maximum size is 10MB."
        )

    # Get applicant
    result = await db.execute(
        select(Applicant).where(
            and_(
                Applicant.id == applicant_id,
                Applicant.tenant_id == user.tenant_id,
            )
        )
    )
    applicant = result.scalar_one_or_none()

    if not applicant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Applicant not found"
        )

    # For mock mode, use selfie for both
    verification_result = await biometrics_service.verify_applicant_selfie(
        id_photo=selfie_bytes,
        selfie=selfie_bytes,
        applicant_id=applicant_id,
        check_liveness=check_liveness,
    )

    # Build response (similar to verify endpoint)
    face_match_response = None
    if verification_result["face_match"]:
        fm = verification_result["face_match"]
        face_match_response = FaceCompareResponse(
            match=fm["match"],
            result=fm["result"],
            similarity=fm["similarity"],
            confidence=fm["confidence"],
            source_face_quality=fm["source_face_quality"],
            target_face_quality=fm["target_face_quality"],
            processing_time_ms=fm["processing_time_ms"],
            is_mock=fm["is_mock"],
            error_message=fm.get("error_message"),
        )

    liveness_response = None
    if verification_result["liveness"]:
        lv = verification_result["liveness"]
        liveness_response = LivenessResponse(
            is_live=lv["is_live"],
            confidence=lv["confidence"],
            confidence_level=lv["confidence_level"],
            quality=lv["quality"],
            age_range=lv["age_range"],
            challenges_passed=lv["challenges_passed"],
            anti_spoofing_score=lv["anti_spoofing_score"],
            processing_time_ms=lv["processing_time_ms"],
            is_mock=lv["is_mock"],
            error_message=lv.get("error_message"),
        )

    return ApplicantVerifyResponse(
        applicant_id=verification_result["applicant_id"],
        verified=verification_result["verified"],
        face_match=face_match_response,
        liveness=liveness_response,
        overall_confidence=verification_result["overall_confidence"],
        failure_reasons=verification_result["failure_reasons"],
        verified_at=verification_result["verified_at"],
        processing_time_ms=verification_result.get("processing_time_ms", 0),
        is_mock=verification_result["is_mock"],
    )


@router.get("/status", response_model=BiometricsStatusResponse)
async def biometrics_status(
    user: User = Depends(require_permission("applicants:read")),
):
    """
    Get biometrics service status.

    Returns configuration status and available capabilities.
    """
    is_configured = biometrics_service.is_configured

    return BiometricsStatusResponse(
        is_configured=is_configured,
        provider="aws_rekognition" if is_configured else "mock",
        mock_mode=not is_configured,
        capabilities=[
            "face_comparison",
            "liveness_detection",
            "face_detection",
            "quality_assessment",
            "age_estimation",
        ] if is_configured else [
            "face_comparison (mock)",
            "liveness_detection (mock)",
            "face_detection (mock)",
        ],
    )
