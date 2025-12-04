"""
Get Clearance - Document Worker
================================
Background worker for processing uploaded documents.

This worker handles:
1. Document download from R2 storage
2. OCR processing (placeholder for Textract/Vision integration)
3. Data extraction
4. Status updates

Note: Full OCR integration (AWS Textract/Google Vision) will be
added in a future phase. Currently handles document status updates
and prepares structure for OCR integration.

Usage (from API):
    from arq import create_pool
    from app.workers.config import get_redis_settings

    redis = await create_pool(get_redis_settings())
    job = await redis.enqueue_job(
        'process_document',
        document_id='uuid-here'
    )
"""

import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select, update

from app.database import get_db_context
from app.models import Document, Applicant
from app.services.storage import storage_service
from app.services.ocr import ocr_service, OCRServiceError, OCRConfigError
from app.services.mrz_parser import mrz_parser, MRZValidationError
from app.services.document_classifier import document_classifier, DocumentType

logger = logging.getLogger(__name__)


async def process_document(
    ctx: dict[str, Any],
    document_id: str,
    run_ocr: bool = True,
) -> dict[str, Any]:
    """
    Process an uploaded document.

    This worker:
    1. Fetches document metadata from database
    2. Verifies document exists in storage
    3. Runs OCR (when integrated)
    4. Extracts structured data
    5. Updates document status

    Args:
        ctx: ARQ context with logger
        document_id: UUID of the document to process
        run_ocr: Whether to run OCR processing

    Returns:
        Dict with status and extracted data

    Raises:
        Exception: If processing fails (ARQ will retry)
    """
    job_logger = ctx.get("logger", logger)
    job_logger.info(f"Starting document processing for {document_id}")

    async with get_db_context() as db:
        try:
            # Fetch document
            query = select(Document).where(Document.id == UUID(document_id))
            result = await db.execute(query)
            document = result.scalar_one_or_none()

            if not document:
                job_logger.error(f"Document not found: {document_id}")
                return {"status": "error", "error": "Document not found"}

            job_logger.info(
                f"Processing document: type={document.type}, "
                f"path={document.storage_path}"
            )

            # Update status to processing
            await db.execute(
                update(Document)
                .where(Document.id == document.id)
                .values(status="processing")
            )
            await db.flush()

            # Verify document exists in storage
            if storage_service.is_configured:
                exists = await storage_service.object_exists(document.storage_path)
                if not exists:
                    job_logger.error(
                        f"Document file not found in storage: {document.storage_path}"
                    )
                    await db.execute(
                        update(Document)
                        .where(Document.id == document.id)
                        .values(
                            status="rejected",
                            verification_checks=[{
                                "check": "storage_exists",
                                "passed": False,
                                "details": "File not found in storage",
                            }],
                        )
                    )
                    await db.commit()
                    return {"status": "error", "error": "File not found in storage"}

                # Get file metadata
                metadata = await storage_service.get_object_metadata(document.storage_path)
                if metadata:
                    job_logger.info(
                        f"Document file size: {metadata.get('size', 0)} bytes, "
                        f"type: {metadata.get('content_type', 'unknown')}"
                    )
            else:
                job_logger.warning("Storage service not configured, skipping file verification")

            # Run document classification first (Claude Vision)
            classification_result = None
            if storage_service.is_configured and document_classifier.is_configured:
                try:
                    # Download document for classification
                    image_bytes = await storage_service.download_object(document.storage_path)
                    if image_bytes:
                        classification_result = await document_classifier.classify(
                            image_bytes,
                            filename=document.original_filename,
                        )
                        job_logger.info(
                            f"Document classified: type={classification_result.document_type.value}, "
                            f"country={classification_result.country_code}, "
                            f"confidence={classification_result.confidence:.1f}"
                        )
                except Exception as e:
                    job_logger.warning(f"Document classification failed: {e}")

            # Run OCR processing (uses classification results to select template)
            ocr_result = None
            if run_ocr:
                ocr_result = await _run_ocr_processing(
                    document,
                    job_logger,
                    classification=classification_result,
                )

            # Build verification checks
            verification_checks = []

            # Storage verification
            verification_checks.append({
                "check": "storage_exists",
                "passed": True,
                "details": "Document file verified in storage",
            })

            # File type verification
            valid_types = [
                "image/jpeg", "image/png", "image/webp",
                "application/pdf",
            ]
            mime_valid = document.mime_type in valid_types if document.mime_type else False
            verification_checks.append({
                "check": "file_type",
                "passed": mime_valid,
                "details": f"MIME type: {document.mime_type}",
            })

            # File size verification (max 10MB)
            max_size = 10 * 1024 * 1024  # 10MB
            size_valid = (document.file_size or 0) <= max_size
            verification_checks.append({
                "check": "file_size",
                "passed": size_valid,
                "details": f"Size: {document.file_size or 0} bytes (max: {max_size})",
            })

            # If we have OCR results, add them
            extracted_data = document.extracted_data or {}
            ocr_text = document.ocr_text
            ocr_confidence = document.ocr_confidence
            fraud_signals = document.fraud_signals or []

            # Add classification results
            if classification_result:
                extracted_data["_classification"] = {
                    "document_type": classification_result.document_type.value,
                    "country_code": classification_result.country_code,
                    "side": classification_result.side.value,
                    "confidence": classification_result.confidence,
                    "detected_fields": classification_result.detected_fields,
                    "suggested_ocr_template": classification_result.suggested_ocr_template,
                    "is_identity_document": classification_result.is_identity_document,
                }

                # Add classification confidence check
                verification_checks.append({
                    "check": "document_classification",
                    "passed": classification_result.confidence >= 70,
                    "details": f"Classified as {classification_result.document_type.value} with {classification_result.confidence:.0f}% confidence",
                })

            if ocr_result:
                extracted_data.update(ocr_result.get("extracted_data", {}))
                ocr_text = ocr_result.get("ocr_text")
                ocr_confidence = ocr_result.get("confidence")
                # Add fraud signals from OCR processing
                fraud_signals.extend(ocr_result.get("fraud_signals", []))

            # Determine final status based on all checks
            final_status = _determine_document_status(
                verification_checks=verification_checks,
                ocr_confidence=ocr_confidence,
                fraud_signals=fraud_signals,
                extracted_data=extracted_data,
                document_type=document.type,
            )

            # Update document
            await db.execute(
                update(Document)
                .where(Document.id == document.id)
                .values(
                    status=final_status,
                    ocr_text=ocr_text,
                    ocr_confidence=ocr_confidence,
                    extracted_data=extracted_data,
                    verification_checks=verification_checks,
                    fraud_signals=fraud_signals,
                    processed_at=datetime.utcnow(),
                )
            )

            # Update applicant step if linked
            if document.step_id:
                await _update_applicant_step(db, document.step_id, final_status)

            await db.commit()

            job_logger.info(
                f"Document processing complete for {document_id}: {final_status}"
            )

            return {
                "status": "success",
                "document_status": final_status,
                "verification_checks": verification_checks,
                "extracted_data": extracted_data,
            }

        except Exception as e:
            job_logger.error(f"Document worker error for {document_id}: {e}")
            await db.rollback()
            raise  # Re-raise for ARQ retry


async def _run_ocr_processing(
    document: Document,
    job_logger: logging.Logger,
    classification: "ClassificationResult | None" = None,
) -> dict[str, Any] | None:
    """
    Run OCR processing on document using AWS Textract.

    Extracts text from documents, parses structured fields,
    and validates MRZ for passports.

    Args:
        document: Document model instance
        job_logger: Logger instance
        classification: Optional classification result from Claude Vision

    Returns:
        Dict with OCR results or None if OCR not configured
    """
    # Import here to avoid circular imports
    from app.services.document_classifier import ClassificationResult

    # Determine document type - use classification result if available
    doc_type = document.type
    if classification and classification.confidence >= 70:
        # Override document type with high-confidence classification
        doc_type = classification.document_type.value
        job_logger.info(f"Using classified document type: {doc_type} (was: {document.type})")

    # Check if OCR service is configured
    if not ocr_service.is_configured:
        job_logger.warning("OCR service not configured (missing AWS credentials)")
        return {
            "ocr_text": None,
            "confidence": None,
            "extracted_data": {
                "_ocr_pending": True,
                "_message": "OCR processing requires AWS Textract configuration",
            },
            "fraud_signals": [],
        }

    job_logger.info(f"Running OCR for document type: {doc_type}")

    try:
        # Run OCR via Textract
        ocr_result = await ocr_service.extract_text(
            storage_key=document.storage_path,
            document_type=doc_type,
            check_quality=True,
        )

        job_logger.info(
            f"OCR complete: confidence={ocr_result.get('ocr_confidence')}, "
            f"quality_issues={len(ocr_result.get('quality_issues', []))}"
        )

        # For passports, validate MRZ
        extracted_data = ocr_result.get("extracted_data", {})
        fraud_signals = ocr_result.get("quality_issues", [])

        if doc_type == "passport":
            mrz_lines = extracted_data.get("mrz_lines")
            if mrz_lines and len(mrz_lines) >= 2:
                try:
                    # Parse MRZ (non-strict to get all data even if checksum fails)
                    mrz_result = mrz_parser.parse_mrz(mrz_lines, strict=False)

                    # Merge MRZ data into extracted_data
                    extracted_data.update({
                        "document_number": mrz_result.get("document_number"),
                        "nationality": mrz_result.get("nationality"),
                        "date_of_birth": mrz_result.get("date_of_birth"),
                        "expiry_date": mrz_result.get("expiry_date"),
                        "sex": mrz_result.get("sex"),
                        "given_names": mrz_result.get("given_names"),
                        "surname": mrz_result.get("surname"),
                        "full_name": mrz_result.get("full_name"),
                        "mrz_checksum_valid": mrz_result.get("checksum_valid"),
                    })

                    # Add MRZ validation errors as fraud signals
                    if not mrz_result.get("checksum_valid"):
                        for error in mrz_result.get("validation_errors", []):
                            fraud_signals.append({
                                "issue": "mrz_checksum_failed",
                                "severity": "high",
                                "confidence": 100,
                                "details": error,
                            })

                    job_logger.info(
                        f"MRZ parsed: valid={mrz_result.get('checksum_valid')}, "
                        f"doc_number={mrz_result.get('document_number')}"
                    )

                except ValueError as e:
                    job_logger.warning(f"MRZ parse error: {e}")
                    fraud_signals.append({
                        "issue": "mrz_parse_error",
                        "severity": "medium",
                        "confidence": 80,
                        "details": str(e),
                    })

        return {
            "ocr_text": ocr_result.get("ocr_text"),
            "confidence": ocr_result.get("ocr_confidence"),
            "extracted_data": extracted_data,
            "fraud_signals": fraud_signals,
        }

    except OCRConfigError as e:
        job_logger.error(f"OCR configuration error: {e}")
        return {
            "ocr_text": None,
            "confidence": None,
            "extracted_data": {
                "_ocr_error": True,
                "_message": str(e),
            },
            "fraud_signals": [{
                "issue": "ocr_config_error",
                "severity": "high",
                "details": str(e),
            }],
        }

    except OCRServiceError as e:
        job_logger.error(f"OCR service error: {e}")
        return {
            "ocr_text": None,
            "confidence": None,
            "extracted_data": {
                "_ocr_error": True,
                "_message": str(e),
            },
            "fraud_signals": [{
                "issue": "ocr_api_error",
                "severity": "medium",
                "details": str(e),
            }],
        }


def _determine_document_status(
    verification_checks: list[dict[str, Any]],
    ocr_confidence: float | None,
    fraud_signals: list[dict[str, Any]],
    extracted_data: dict[str, Any],
    document_type: str,
) -> str:
    """
    Determine final document status based on all processing results.

    Status logic:
    - verified: All checks pass, high OCR confidence, no high-severity fraud signals
    - rejected: Critical failures (MRZ checksum, high-severity fraud signals)
    - review: Minor issues that need human review

    Args:
        verification_checks: File verification check results
        ocr_confidence: OCR confidence score (0-100)
        fraud_signals: List of detected fraud signals
        extracted_data: Extracted document data
        document_type: Type of document

    Returns:
        Status: 'verified', 'rejected', or 'review'
    """
    # Check basic verification
    all_basic_passed = all(check.get("passed", False) for check in verification_checks)
    if not all_basic_passed:
        return "rejected"

    # Count fraud signals by severity
    high_severity = [s for s in fraud_signals if s.get("severity") == "high"]
    medium_severity = [s for s in fraud_signals if s.get("severity") == "medium"]

    # MRZ validation failure is critical for passports
    if document_type == "passport":
        mrz_valid = extracted_data.get("mrz_checksum_valid")
        if mrz_valid is False:  # Explicitly False, not None
            return "rejected"

    # Multiple high-severity issues = reject
    if len(high_severity) >= 2:
        return "rejected"

    # Any high-severity issue = review
    if high_severity:
        return "review"

    # OCR confidence thresholds
    if ocr_confidence is not None:
        if ocr_confidence < 60:
            return "rejected"
        elif ocr_confidence < 85:
            return "review"

    # Medium-severity issues = review
    if len(medium_severity) >= 2:
        return "review"

    return "verified"


async def _update_applicant_step(
    db: Any,
    step_id: UUID,
    document_status: str,
) -> None:
    """
    Update applicant step status based on document processing result.

    Args:
        db: Database session
        step_id: ApplicantStep UUID
        document_status: Result of document processing
    """
    from app.models import ApplicantStep

    # Map document status to step status
    status_mapping = {
        "verified": "complete",
        "rejected": "failed",
        "processing": "in_progress",
    }
    step_status = status_mapping.get(document_status, "pending")

    await db.execute(
        update(ApplicantStep)
        .where(ApplicantStep.id == step_id)
        .values(
            status=step_status,
            completed_at=datetime.utcnow() if step_status in ["complete", "failed"] else None,
            verification_result={
                "document_status": document_status,
                "processed_at": datetime.utcnow().isoformat(),
            },
        )
    )

    logger.info(f"Updated applicant step {step_id}: status={step_status}")


async def validate_document_upload(
    ctx: dict[str, Any],
    document_id: str,
) -> dict[str, Any]:
    """
    Validate that a document was properly uploaded.

    This is a lighter-weight check that can be run immediately
    after upload confirmation to verify the file is accessible.

    Args:
        ctx: ARQ context with logger
        document_id: UUID of the document to validate

    Returns:
        Dict with validation status
    """
    job_logger = ctx.get("logger", logger)
    job_logger.info(f"Validating document upload: {document_id}")

    async with get_db_context() as db:
        try:
            # Fetch document
            query = select(Document).where(Document.id == UUID(document_id))
            result = await db.execute(query)
            document = result.scalar_one_or_none()

            if not document:
                return {"status": "error", "error": "Document not found"}

            # Quick storage check
            if storage_service.is_configured:
                exists = await storage_service.object_exists(document.storage_path)
                if not exists:
                    job_logger.warning(f"Document not found in storage: {document.storage_path}")
                    return {"status": "error", "error": "File not in storage"}

            return {"status": "success", "message": "Document upload validated"}

        except Exception as e:
            job_logger.error(f"Validation error for {document_id}: {e}")
            return {"status": "error", "error": str(e)}
