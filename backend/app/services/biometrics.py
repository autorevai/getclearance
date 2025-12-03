"""
Get Clearance - Biometrics Service
===================================
Service for face matching and liveness detection.

This is a placeholder implementation that returns mock data for development.
Production integration with AWS Rekognition will be implemented in Terminal 5.

Features:
- Face comparison between ID photo and selfie
- Liveness detection (anti-spoofing)
- Face quality assessment
- Age estimation

Usage:
    from app.services.biometrics import biometrics_service

    # Compare faces
    result = await biometrics_service.compare_faces(id_photo, selfie)
    if result.match and result.confidence >= 90:
        print("Face match confirmed")

    # Check liveness
    liveness = await biometrics_service.detect_liveness(selfie)
    if liveness.is_live:
        print("Live face detected")
"""

import base64
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from app.config import settings

logger = logging.getLogger(__name__)


# ===========================================
# ENUMS AND DATA CLASSES
# ===========================================

class LivenessConfidence(str, Enum):
    """Liveness detection confidence level."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


class FaceMatchResult(str, Enum):
    """Face matching result."""
    MATCH = "match"
    NO_MATCH = "no_match"
    INCONCLUSIVE = "inconclusive"
    ERROR = "error"


@dataclass
class FaceQuality:
    """Face image quality metrics."""
    brightness: float  # 0-100
    sharpness: float   # 0-100
    contrast: float    # 0-100
    pose_pitch: float  # Face tilt up/down in degrees
    pose_yaw: float    # Face tilt left/right in degrees
    pose_roll: float   # Face rotation in degrees
    eyes_open: bool
    mouth_open: bool
    sunglasses: bool
    is_acceptable: bool  # Overall quality acceptable for matching

    def to_dict(self) -> dict[str, Any]:
        return {
            "brightness": self.brightness,
            "sharpness": self.sharpness,
            "contrast": self.contrast,
            "pose": {
                "pitch": self.pose_pitch,
                "yaw": self.pose_yaw,
                "roll": self.pose_roll,
            },
            "eyes_open": self.eyes_open,
            "mouth_open": self.mouth_open,
            "sunglasses": self.sunglasses,
            "is_acceptable": self.is_acceptable,
        }


@dataclass
class FaceComparisonResult:
    """Result of face comparison between two images."""
    match: bool
    result: FaceMatchResult
    similarity: float  # 0-100 similarity score
    confidence: float  # 0-100 confidence in the comparison
    source_face_quality: FaceQuality | None = None
    target_face_quality: FaceQuality | None = None
    processing_time_ms: int = 0
    is_mock: bool = False
    error_message: str | None = None
    raw_response: dict = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "match": self.match,
            "result": self.result.value,
            "similarity": self.similarity,
            "confidence": self.confidence,
            "source_face_quality": self.source_face_quality.to_dict() if self.source_face_quality else None,
            "target_face_quality": self.target_face_quality.to_dict() if self.target_face_quality else None,
            "processing_time_ms": self.processing_time_ms,
            "is_mock": self.is_mock,
            "error_message": self.error_message,
        }


@dataclass
class LivenessResult:
    """Result of liveness detection."""
    is_live: bool
    confidence: float  # 0-100
    confidence_level: LivenessConfidence
    quality: FaceQuality | None = None
    age_range: tuple[int, int] | None = None  # (min_age, max_age)
    challenges_passed: list[str] = field(default_factory=list)
    # Challenges: 'blink', 'smile', 'turn_left', 'turn_right', 'nod'
    anti_spoofing_score: float = 0.0  # 0-100, higher = more likely real
    processing_time_ms: int = 0
    is_mock: bool = False
    error_message: str | None = None
    raw_response: dict = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "is_live": self.is_live,
            "confidence": self.confidence,
            "confidence_level": self.confidence_level.value,
            "quality": self.quality.to_dict() if self.quality else None,
            "age_range": {"min": self.age_range[0], "max": self.age_range[1]} if self.age_range else None,
            "challenges_passed": self.challenges_passed,
            "anti_spoofing_score": self.anti_spoofing_score,
            "processing_time_ms": self.processing_time_ms,
            "is_mock": self.is_mock,
            "error_message": self.error_message,
        }


@dataclass
class FaceDetectionResult:
    """Result of face detection in an image."""
    faces_detected: int
    primary_face_bounds: dict | None = None  # {"left": x, "top": y, "width": w, "height": h}
    quality: FaceQuality | None = None
    landmarks: list[dict] | None = None  # Facial landmark positions
    emotions: dict[str, float] | None = None  # {"happy": 0.8, "neutral": 0.2, ...}
    gender: str | None = None
    age_range: tuple[int, int] | None = None
    is_mock: bool = False
    error_message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "faces_detected": self.faces_detected,
            "primary_face_bounds": self.primary_face_bounds,
            "quality": self.quality.to_dict() if self.quality else None,
            "emotions": self.emotions,
            "gender": self.gender,
            "age_range": {"min": self.age_range[0], "max": self.age_range[1]} if self.age_range else None,
            "is_mock": self.is_mock,
            "error_message": self.error_message,
        }


# ===========================================
# BIOMETRICS SERVICE
# ===========================================

class BiometricsService:
    """
    Biometrics service for face matching and liveness detection.

    Currently a placeholder implementation returning mock data.
    Will integrate with AWS Rekognition in Terminal 5.

    Configuration:
        AWS credentials in config.py:
        - AWS_ACCESS_KEY_ID
        - AWS_SECRET_ACCESS_KEY
        - AWS_REGION

    Mock mode:
        When AWS is not configured, returns realistic mock data for development.
    """

    # Similarity threshold for face match
    DEFAULT_SIMILARITY_THRESHOLD = 90.0

    def __init__(self):
        """Initialize biometrics service."""
        self._aws_configured = self._check_aws_config()
        self._rekognition_client = None

        if self._aws_configured:
            self._init_rekognition()

    def _check_aws_config(self) -> bool:
        """Check if AWS credentials are configured."""
        return bool(
            getattr(settings, 'aws_access_key_id', None) and
            getattr(settings, 'aws_secret_access_key', None) and
            getattr(settings, 'aws_region', None)
        )

    def _init_rekognition(self) -> None:
        """Initialize AWS Rekognition client."""
        # TODO: Initialize boto3 Rekognition client in Terminal 5
        # import boto3
        # self._rekognition_client = boto3.client(
        #     'rekognition',
        #     aws_access_key_id=settings.aws_access_key_id,
        #     aws_secret_access_key=settings.aws_secret_access_key,
        #     region_name=settings.aws_region,
        # )
        pass

    @property
    def is_configured(self) -> bool:
        """Check if biometrics service is configured for production use."""
        return self._aws_configured

    async def compare_faces(
        self,
        source_image: bytes,
        target_image: bytes,
        similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
    ) -> FaceComparisonResult:
        """
        Compare two faces for matching.

        Args:
            source_image: Source face image (e.g., ID photo) as bytes
            target_image: Target face image (e.g., selfie) as bytes
            similarity_threshold: Minimum similarity score for match (0-100)

        Returns:
            FaceComparisonResult with match status and similarity score
        """
        if not self.is_configured:
            return self._mock_compare_faces(source_image, target_image, similarity_threshold)

        # TODO: AWS Rekognition integration in Terminal 5
        # try:
        #     response = self._rekognition_client.compare_faces(
        #         SourceImage={'Bytes': source_image},
        #         TargetImage={'Bytes': target_image},
        #         SimilarityThreshold=similarity_threshold,
        #         QualityFilter='AUTO',
        #     )
        #     ...
        # except ClientError as e:
        #     ...

        return self._mock_compare_faces(source_image, target_image, similarity_threshold)

    async def detect_liveness(
        self,
        image: bytes,
        session_id: str | None = None,
    ) -> LivenessResult:
        """
        Detect if the image contains a live person (not a photo/screen).

        Args:
            image: Face image as bytes
            session_id: Optional session ID for multi-frame liveness check

        Returns:
            LivenessResult with liveness status and confidence
        """
        if not self.is_configured:
            return self._mock_detect_liveness(image)

        # TODO: AWS Rekognition Liveness integration in Terminal 5
        # AWS offers two approaches:
        # 1. FaceLivenessSession (interactive, requires SDK)
        # 2. DetectFaces with quality analysis (passive)

        return self._mock_detect_liveness(image)

    async def detect_faces(
        self,
        image: bytes,
    ) -> FaceDetectionResult:
        """
        Detect faces in an image and return metadata.

        Args:
            image: Image as bytes

        Returns:
            FaceDetectionResult with face count and details
        """
        if not self.is_configured:
            return self._mock_detect_faces(image)

        # TODO: AWS Rekognition DetectFaces in Terminal 5

        return self._mock_detect_faces(image)

    async def assess_face_quality(
        self,
        image: bytes,
    ) -> FaceQuality:
        """
        Assess the quality of a face image for biometric matching.

        Args:
            image: Face image as bytes

        Returns:
            FaceQuality with quality metrics
        """
        if not self.is_configured:
            return self._mock_face_quality()

        # TODO: Extract quality from DetectFaces response

        return self._mock_face_quality()

    async def verify_applicant_selfie(
        self,
        id_photo: bytes,
        selfie: bytes,
        applicant_id: UUID,
        check_liveness: bool = True,
    ) -> dict[str, Any]:
        """
        Complete biometric verification for an applicant.

        Performs:
        1. Face comparison between ID photo and selfie
        2. Liveness detection on selfie
        3. Quality assessment

        Args:
            id_photo: ID document photo as bytes
            selfie: Live selfie as bytes
            applicant_id: Applicant UUID
            check_liveness: Whether to perform liveness check

        Returns:
            Complete verification result dict
        """
        import time
        start = time.time()

        result = {
            "applicant_id": str(applicant_id),
            "verified": False,
            "face_match": None,
            "liveness": None,
            "overall_confidence": 0.0,
            "failure_reasons": [],
            "verified_at": datetime.utcnow().isoformat(),
            "is_mock": not self.is_configured,
        }

        # Step 1: Compare faces
        face_match = await self.compare_faces(id_photo, selfie)
        result["face_match"] = face_match.to_dict()

        if not face_match.match:
            result["failure_reasons"].append("face_mismatch")

        # Step 2: Liveness detection
        if check_liveness:
            liveness = await self.detect_liveness(selfie)
            result["liveness"] = liveness.to_dict()

            if not liveness.is_live:
                result["failure_reasons"].append("liveness_failed")

        # Calculate overall result
        if face_match.match and (not check_liveness or liveness.is_live):
            result["verified"] = True
            result["overall_confidence"] = (
                face_match.confidence * 0.6 +
                (liveness.confidence if check_liveness else 100) * 0.4
            )
        else:
            result["overall_confidence"] = min(
                face_match.confidence,
                liveness.confidence if check_liveness else 100
            )

        result["processing_time_ms"] = int((time.time() - start) * 1000)

        logger.info(
            f"Biometric verification for applicant {applicant_id}: "
            f"verified={result['verified']}, confidence={result['overall_confidence']:.1f}"
        )

        return result

    # ===========================================
    # MOCK IMPLEMENTATIONS
    # ===========================================

    def _mock_compare_faces(
        self,
        source_image: bytes,
        target_image: bytes,
        threshold: float,
    ) -> FaceComparisonResult:
        """Generate mock face comparison result."""
        import random

        # Generate realistic mock data
        similarity = random.uniform(85.0, 99.0)
        confidence = random.uniform(92.0, 99.5)

        # Determine match based on threshold
        match = similarity >= threshold
        result = FaceMatchResult.MATCH if match else FaceMatchResult.NO_MATCH

        return FaceComparisonResult(
            match=match,
            result=result,
            similarity=round(similarity, 2),
            confidence=round(confidence, 2),
            source_face_quality=self._mock_face_quality(),
            target_face_quality=self._mock_face_quality(),
            processing_time_ms=random.randint(200, 500),
            is_mock=True,
        )

    def _mock_detect_liveness(self, image: bytes) -> LivenessResult:
        """Generate mock liveness detection result."""
        import random

        confidence = random.uniform(88.0, 99.0)
        is_live = confidence >= 80.0

        if confidence >= 95:
            level = LivenessConfidence.HIGH
        elif confidence >= 85:
            level = LivenessConfidence.MEDIUM
        else:
            level = LivenessConfidence.LOW

        return LivenessResult(
            is_live=is_live,
            confidence=round(confidence, 2),
            confidence_level=level,
            quality=self._mock_face_quality(),
            age_range=(25, 35),  # Mock age range
            challenges_passed=["blink", "smile"] if is_live else [],
            anti_spoofing_score=round(random.uniform(85.0, 99.0), 2),
            processing_time_ms=random.randint(150, 400),
            is_mock=True,
        )

    def _mock_detect_faces(self, image: bytes) -> FaceDetectionResult:
        """Generate mock face detection result."""
        return FaceDetectionResult(
            faces_detected=1,
            primary_face_bounds={"left": 100, "top": 80, "width": 200, "height": 250},
            quality=self._mock_face_quality(),
            emotions={"neutral": 0.7, "happy": 0.2, "calm": 0.1},
            gender="unknown",  # Not assuming
            age_range=(25, 35),
            is_mock=True,
        )

    def _mock_face_quality(self) -> FaceQuality:
        """Generate mock face quality metrics."""
        import random

        return FaceQuality(
            brightness=round(random.uniform(75.0, 95.0), 1),
            sharpness=round(random.uniform(80.0, 98.0), 1),
            contrast=round(random.uniform(70.0, 90.0), 1),
            pose_pitch=round(random.uniform(-5.0, 5.0), 1),
            pose_yaw=round(random.uniform(-8.0, 8.0), 1),
            pose_roll=round(random.uniform(-3.0, 3.0), 1),
            eyes_open=True,
            mouth_open=False,
            sunglasses=False,
            is_acceptable=True,
        )


# ===========================================
# SINGLETON INSTANCE
# ===========================================

biometrics_service = BiometricsService()


# ===========================================
# CONVENIENCE FUNCTIONS
# ===========================================

async def compare_faces(
    source_image: bytes,
    target_image: bytes,
    similarity_threshold: float = 90.0,
) -> FaceComparisonResult:
    """Compare two faces for matching."""
    return await biometrics_service.compare_faces(
        source_image, target_image, similarity_threshold
    )


async def detect_liveness(image: bytes) -> LivenessResult:
    """Detect if image contains a live person."""
    return await biometrics_service.detect_liveness(image)


async def verify_applicant(
    id_photo: bytes,
    selfie: bytes,
    applicant_id: UUID,
) -> dict[str, Any]:
    """Complete biometric verification for an applicant."""
    return await biometrics_service.verify_applicant_selfie(
        id_photo, selfie, applicant_id
    )
