"""
Get Clearance - Biometrics Service
===================================
Service for face matching and liveness detection using AWS Rekognition.

Features:
- Face comparison between ID photo and selfie
- Liveness detection (anti-spoofing via quality analysis)
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

AWS Configuration:
    Requires these environment variables:
    - AWS_ACCESS_KEY_ID
    - AWS_SECRET_ACCESS_KEY
    - AWS_REGION (default: us-east-1)

    IAM permissions needed:
    - rekognition:CompareFaces
    - rekognition:DetectFaces
"""

import base64
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

import boto3
from botocore.exceptions import ClientError, BotoCoreError

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

    Uses AWS Rekognition for production biometrics:
    - CompareFaces: Compare ID photo to selfie
    - DetectFaces: Quality analysis and passive liveness

    Configuration:
        AWS credentials in environment:
        - AWS_ACCESS_KEY_ID
        - AWS_SECRET_ACCESS_KEY
        - AWS_REGION

    Mock mode:
        When AWS is not configured, returns mock data for development.
    """

    # Similarity threshold for face match
    DEFAULT_SIMILARITY_THRESHOLD = 90.0

    # Liveness quality thresholds
    MIN_BRIGHTNESS = 40.0
    MIN_SHARPNESS = 40.0
    MAX_POSE_ANGLE = 30.0  # degrees

    def __init__(self):
        """Initialize biometrics service."""
        self._aws_configured = self._check_aws_config()
        self._rekognition_client = None

        if self._aws_configured:
            self._init_rekognition()

    def _check_aws_config(self) -> bool:
        """Check if AWS credentials are configured."""
        has_creds = bool(
            getattr(settings, 'aws_access_key_id', None) and
            getattr(settings, 'aws_secret_access_key', None) and
            getattr(settings, 'aws_region', None)
        )
        logger.info(f"AWS Rekognition configured: {has_creds}")
        return has_creds

    def _init_rekognition(self) -> None:
        """Initialize AWS Rekognition client."""
        try:
            self._rekognition_client = boto3.client(
                'rekognition',
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
                region_name=settings.aws_region,
            )
            logger.info(f"AWS Rekognition client initialized (region: {settings.aws_region})")
        except Exception as e:
            logger.error(f"Failed to initialize Rekognition client: {e}")
            self._rekognition_client = None
            self._aws_configured = False

    @property
    def is_configured(self) -> bool:
        """Check if biometrics service is configured for production use."""
        return self._aws_configured and self._rekognition_client is not None

    def _extract_quality_from_face(self, face_detail: dict) -> FaceQuality:
        """Extract FaceQuality from AWS DetectFaces response."""
        quality = face_detail.get('Quality', {})
        pose = face_detail.get('Pose', {})
        eyes_open = face_detail.get('EyesOpen', {})
        mouth_open = face_detail.get('MouthOpen', {})
        sunglasses = face_detail.get('Sunglasses', {})

        brightness = quality.get('Brightness', 50.0)
        sharpness = quality.get('Sharpness', 50.0)
        pitch = pose.get('Pitch', 0.0)
        yaw = pose.get('Yaw', 0.0)
        roll = pose.get('Roll', 0.0)

        # Determine if quality is acceptable
        is_acceptable = (
            brightness >= self.MIN_BRIGHTNESS and
            sharpness >= self.MIN_SHARPNESS and
            abs(pitch) <= self.MAX_POSE_ANGLE and
            abs(yaw) <= self.MAX_POSE_ANGLE and
            abs(roll) <= self.MAX_POSE_ANGLE and
            eyes_open.get('Value', True) and
            not sunglasses.get('Value', False)
        )

        return FaceQuality(
            brightness=round(brightness, 1),
            sharpness=round(sharpness, 1),
            contrast=round((brightness + sharpness) / 2, 1),  # AWS doesn't provide contrast
            pose_pitch=round(pitch, 1),
            pose_yaw=round(yaw, 1),
            pose_roll=round(roll, 1),
            eyes_open=eyes_open.get('Value', True),
            mouth_open=mouth_open.get('Value', False),
            sunglasses=sunglasses.get('Value', False),
            is_acceptable=is_acceptable,
        )

    def _extract_emotions(self, face_detail: dict) -> dict[str, float]:
        """Extract emotions from AWS face details."""
        emotions = face_detail.get('Emotions', [])
        return {
            e['Type'].lower(): round(e['Confidence'] / 100, 2)
            for e in emotions
        }

    async def compare_faces(
        self,
        source_image: bytes,
        target_image: bytes,
        similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
    ) -> FaceComparisonResult:
        """
        Compare two faces for matching using AWS Rekognition.

        Args:
            source_image: Source face image (e.g., ID photo) as bytes
            target_image: Target face image (e.g., selfie) as bytes
            similarity_threshold: Minimum similarity score for match (0-100)

        Returns:
            FaceComparisonResult with match status and similarity score
        """
        start_time = time.time()

        if not self.is_configured:
            logger.warning("AWS not configured, using mock face comparison")
            return self._mock_compare_faces(source_image, target_image, similarity_threshold)

        try:
            logger.info(f"Comparing faces with AWS Rekognition (threshold: {similarity_threshold})")

            response = self._rekognition_client.compare_faces(
                SourceImage={'Bytes': source_image},
                TargetImage={'Bytes': target_image},
                SimilarityThreshold=float(similarity_threshold),
                QualityFilter='AUTO',
            )

            processing_time = int((time.time() - start_time) * 1000)

            # Check if we got a match
            face_matches = response.get('FaceMatches', [])

            if face_matches:
                # Use the best match
                best_match = face_matches[0]
                similarity = best_match.get('Similarity', 0.0)
                face = best_match.get('Face', {})
                confidence = face.get('Confidence', 0.0)

                # Extract quality from source and target
                source_face = response.get('SourceImageFace', {})
                source_quality = self._extract_quality_from_face(source_face) if source_face else None

                match = similarity >= similarity_threshold
                result = FaceMatchResult.MATCH if match else FaceMatchResult.NO_MATCH

                logger.info(f"Face comparison result: similarity={similarity:.1f}, match={match}")

                return FaceComparisonResult(
                    match=match,
                    result=result,
                    similarity=round(similarity, 2),
                    confidence=round(confidence, 2),
                    source_face_quality=source_quality,
                    target_face_quality=None,  # Would need separate DetectFaces call
                    processing_time_ms=processing_time,
                    is_mock=False,
                    raw_response=response,
                )
            else:
                # No face match found
                unmatched = response.get('UnmatchedFaces', [])
                logger.info(f"No face match found. Unmatched faces: {len(unmatched)}")

                return FaceComparisonResult(
                    match=False,
                    result=FaceMatchResult.NO_MATCH,
                    similarity=0.0,
                    confidence=0.0,
                    processing_time_ms=processing_time,
                    is_mock=False,
                    raw_response=response,
                )

        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"AWS Rekognition error: {error_code} - {error_message}")

            # Handle specific errors
            if error_code in ['InvalidParameterException', 'InvalidImageFormatException']:
                return FaceComparisonResult(
                    match=False,
                    result=FaceMatchResult.ERROR,
                    similarity=0.0,
                    confidence=0.0,
                    processing_time_ms=int((time.time() - start_time) * 1000),
                    is_mock=False,
                    error_message=f"Invalid image: {error_message}",
                )
            elif error_code == 'ImageTooLargeException':
                return FaceComparisonResult(
                    match=False,
                    result=FaceMatchResult.ERROR,
                    similarity=0.0,
                    confidence=0.0,
                    processing_time_ms=int((time.time() - start_time) * 1000),
                    is_mock=False,
                    error_message="Image too large (max 5MB)",
                )
            else:
                return FaceComparisonResult(
                    match=False,
                    result=FaceMatchResult.ERROR,
                    similarity=0.0,
                    confidence=0.0,
                    processing_time_ms=int((time.time() - start_time) * 1000),
                    is_mock=False,
                    error_message=f"AWS error: {error_code}",
                )

        except Exception as e:
            logger.exception(f"Unexpected error in face comparison: {e}")
            return FaceComparisonResult(
                match=False,
                result=FaceMatchResult.ERROR,
                similarity=0.0,
                confidence=0.0,
                processing_time_ms=int((time.time() - start_time) * 1000),
                is_mock=False,
                error_message=str(e),
            )

    async def detect_liveness(
        self,
        image: bytes,
        session_id: str | None = None,
    ) -> LivenessResult:
        """
        Detect if the image contains a live person using quality analysis.

        Uses AWS Rekognition DetectFaces with quality metrics as a proxy for liveness:
        - Good brightness and sharpness
        - Eyes open
        - Reasonable head pose
        - No sunglasses

        For production-grade liveness, consider AWS Rekognition Face Liveness
        which requires interactive session management.

        Args:
            image: Face image as bytes
            session_id: Optional session ID (unused in passive mode)

        Returns:
            LivenessResult with liveness status and confidence
        """
        start_time = time.time()

        if not self.is_configured:
            logger.warning("AWS not configured, using mock liveness detection")
            return self._mock_detect_liveness(image)

        try:
            logger.info("Detecting liveness with AWS Rekognition")

            response = self._rekognition_client.detect_faces(
                Image={'Bytes': image},
                Attributes=['ALL'],
            )

            processing_time = int((time.time() - start_time) * 1000)

            face_details = response.get('FaceDetails', [])

            if not face_details:
                logger.info("No face detected in liveness check")
                return LivenessResult(
                    is_live=False,
                    confidence=0.0,
                    confidence_level=LivenessConfidence.UNKNOWN,
                    processing_time_ms=processing_time,
                    is_mock=False,
                    error_message="No face detected",
                )

            # Use the primary (largest) face
            face = face_details[0]
            quality = self._extract_quality_from_face(face)

            # Calculate liveness score based on quality metrics
            # Higher quality = more likely to be a real live face
            quality_score = (quality.brightness + quality.sharpness) / 2

            # Pose penalty - extreme angles suggest photo manipulation
            pose_penalty = (
                abs(quality.pose_pitch) + abs(quality.pose_yaw) + abs(quality.pose_roll)
            ) / 3
            pose_multiplier = max(0.5, 1.0 - (pose_penalty / 60))

            # Eyes/sunglasses factor
            eyes_factor = 1.0 if quality.eyes_open and not quality.sunglasses else 0.7

            # Calculate final liveness confidence
            liveness_confidence = min(100.0, quality_score * pose_multiplier * eyes_factor)

            # Determine if live
            is_live = quality.is_acceptable and liveness_confidence >= 70

            # Confidence level
            if liveness_confidence >= 90:
                level = LivenessConfidence.HIGH
            elif liveness_confidence >= 75:
                level = LivenessConfidence.MEDIUM
            elif liveness_confidence >= 50:
                level = LivenessConfidence.LOW
            else:
                level = LivenessConfidence.UNKNOWN

            # Extract age range
            age_range_data = face.get('AgeRange', {})
            age_range = None
            if age_range_data:
                age_range = (age_range_data.get('Low', 0), age_range_data.get('High', 100))

            # Determine which "challenges" passed
            challenges_passed = []
            if quality.eyes_open:
                challenges_passed.append("eyes_open")
            if not quality.sunglasses:
                challenges_passed.append("no_sunglasses")
            if abs(quality.pose_pitch) <= 15:
                challenges_passed.append("good_pose")
            if quality.brightness >= 50:
                challenges_passed.append("good_lighting")

            logger.info(f"Liveness result: is_live={is_live}, confidence={liveness_confidence:.1f}")

            return LivenessResult(
                is_live=is_live,
                confidence=round(liveness_confidence, 2),
                confidence_level=level,
                quality=quality,
                age_range=age_range,
                challenges_passed=challenges_passed,
                anti_spoofing_score=round(liveness_confidence, 2),
                processing_time_ms=processing_time,
                is_mock=False,
                raw_response=response,
            )

        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"AWS Rekognition error in liveness: {error_code} - {error_message}")

            return LivenessResult(
                is_live=False,
                confidence=0.0,
                confidence_level=LivenessConfidence.UNKNOWN,
                processing_time_ms=int((time.time() - start_time) * 1000),
                is_mock=False,
                error_message=f"AWS error: {error_code}",
            )

        except Exception as e:
            logger.exception(f"Unexpected error in liveness detection: {e}")
            return LivenessResult(
                is_live=False,
                confidence=0.0,
                confidence_level=LivenessConfidence.UNKNOWN,
                processing_time_ms=int((time.time() - start_time) * 1000),
                is_mock=False,
                error_message=str(e),
            )

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
        start_time = time.time()

        if not self.is_configured:
            logger.warning("AWS not configured, using mock face detection")
            return self._mock_detect_faces(image)

        try:
            logger.info("Detecting faces with AWS Rekognition")

            response = self._rekognition_client.detect_faces(
                Image={'Bytes': image},
                Attributes=['ALL'],
            )

            face_details = response.get('FaceDetails', [])
            faces_detected = len(face_details)

            if faces_detected == 0:
                return FaceDetectionResult(
                    faces_detected=0,
                    is_mock=False,
                    error_message="No faces detected",
                )

            # Use the primary face
            face = face_details[0]
            bounding_box = face.get('BoundingBox', {})
            quality = self._extract_quality_from_face(face)
            emotions = self._extract_emotions(face)

            # Gender (if available)
            gender_data = face.get('Gender', {})
            gender = gender_data.get('Value', '').lower() if gender_data.get('Confidence', 0) > 90 else None

            # Age range
            age_range_data = face.get('AgeRange', {})
            age_range = None
            if age_range_data:
                age_range = (age_range_data.get('Low', 0), age_range_data.get('High', 100))

            # Landmarks
            landmarks = [
                {"type": lm['Type'], "x": lm['X'], "y": lm['Y']}
                for lm in face.get('Landmarks', [])
            ]

            logger.info(f"Detected {faces_detected} face(s)")

            return FaceDetectionResult(
                faces_detected=faces_detected,
                primary_face_bounds={
                    "left": bounding_box.get('Left', 0),
                    "top": bounding_box.get('Top', 0),
                    "width": bounding_box.get('Width', 0),
                    "height": bounding_box.get('Height', 0),
                },
                quality=quality,
                landmarks=landmarks,
                emotions=emotions,
                gender=gender,
                age_range=age_range,
                is_mock=False,
            )

        except ClientError as e:
            error_code = e.response['Error']['Code']
            logger.error(f"AWS Rekognition error in face detection: {error_code}")
            return FaceDetectionResult(
                faces_detected=0,
                is_mock=False,
                error_message=f"AWS error: {error_code}",
            )

        except Exception as e:
            logger.exception(f"Unexpected error in face detection: {e}")
            return FaceDetectionResult(
                faces_detected=0,
                is_mock=False,
                error_message=str(e),
            )

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

        result = await self.detect_faces(image)
        if result.quality:
            return result.quality
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

        if face_match.error_message:
            result["failure_reasons"].append(f"face_match_error: {face_match.error_message}")

        # Step 2: Liveness detection
        liveness = None
        if check_liveness:
            liveness = await self.detect_liveness(selfie)
            result["liveness"] = liveness.to_dict()

            if not liveness.is_live:
                result["failure_reasons"].append("liveness_failed")

        # Calculate overall result
        if face_match.match and (not check_liveness or (liveness and liveness.is_live)):
            result["verified"] = True
            result["overall_confidence"] = (
                face_match.confidence * 0.6 +
                (liveness.confidence if liveness else 100) * 0.4
            )
        else:
            result["overall_confidence"] = min(
                face_match.confidence,
                liveness.confidence if liveness else 100
            )

        result["processing_time_ms"] = int((time.time() - start) * 1000)

        logger.info(
            f"Biometric verification for applicant {applicant_id}: "
            f"verified={result['verified']}, confidence={result['overall_confidence']:.1f}, "
            f"is_mock={result['is_mock']}"
        )

        return result

    # ===========================================
    # MOCK IMPLEMENTATIONS (fallback when AWS not configured)
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
            challenges_passed=["eyes_open", "no_sunglasses", "good_pose", "good_lighting"] if is_live else [],
            anti_spoofing_score=round(random.uniform(85.0, 99.0), 2),
            processing_time_ms=random.randint(150, 400),
            is_mock=True,
        )

    def _mock_detect_faces(self, image: bytes) -> FaceDetectionResult:
        """Generate mock face detection result."""
        return FaceDetectionResult(
            faces_detected=1,
            primary_face_bounds={"left": 0.2, "top": 0.1, "width": 0.6, "height": 0.8},
            quality=self._mock_face_quality(),
            emotions={"neutral": 0.7, "happy": 0.2, "calm": 0.1},
            gender=None,  # Not assuming
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
