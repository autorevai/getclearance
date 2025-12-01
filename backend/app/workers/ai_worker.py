"""
Get Clearance - AI Worker
==========================
Background worker for AI-powered risk analysis.

This worker handles:
1. Risk summary generation using Claude AI
2. Applicant status updates based on AI assessment
3. Storage of AI assessment results

Usage (from API):
    from arq import create_pool
    from app.workers.config import get_redis_settings

    redis = await create_pool(get_redis_settings())
    job = await redis.enqueue_job(
        'generate_risk_summary',
        applicant_id='uuid-here'
    )
"""

import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select, update

from app.database import get_db_context
from app.models import Applicant
from app.services.ai import ai_service, RiskSummary

logger = logging.getLogger(__name__)


async def generate_risk_summary(
    ctx: dict[str, Any],
    applicant_id: str,
    update_applicant: bool = True,
) -> dict[str, Any]:
    """
    Generate AI-powered risk summary for an applicant.

    This worker:
    1. Fetches applicant with related data
    2. Generates risk summary via Claude AI
    3. Updates applicant risk score and factors
    4. Returns summary for storage/display

    Args:
        ctx: ARQ context with logger
        applicant_id: UUID of the applicant to analyze
        update_applicant: Whether to update applicant record

    Returns:
        Dict with summary, risk factors, and recommendations

    Raises:
        Exception: If AI processing fails (ARQ will retry)
    """
    job_logger = ctx.get("logger", logger)
    job_logger.info(f"Starting AI risk summary for applicant {applicant_id}")

    async with get_db_context() as db:
        try:
            # Verify applicant exists before AI call
            query = select(Applicant).where(Applicant.id == UUID(applicant_id))
            result = await db.execute(query)
            applicant = result.scalar_one_or_none()

            if not applicant:
                job_logger.error(f"Applicant not found: {applicant_id}")
                return {"status": "error", "error": "Applicant not found"}

            job_logger.info(f"Generating risk summary for {applicant.full_name}")

            # Check if AI service is configured
            if not ai_service.is_configured:
                job_logger.warning("AI service not configured, returning default assessment")
                return {
                    "status": "skipped",
                    "reason": "AI service not configured",
                    "overall_risk": "unknown",
                    "risk_score": None,
                }

            # Generate risk summary via AI service
            summary: RiskSummary = await ai_service.generate_risk_summary(
                db=db,
                applicant_id=UUID(applicant_id),
            )

            job_logger.info(
                f"AI assessment complete: risk={summary.overall_risk}, "
                f"score={summary.risk_score}"
            )

            # Update applicant if requested
            if update_applicant:
                await _update_applicant_from_summary(db, applicant, summary)

            await db.commit()

            # Format response
            response = {
                "status": "success",
                "overall_risk": summary.overall_risk,
                "risk_score": summary.risk_score,
                "summary": summary.summary,
                "risk_factors": [
                    {
                        "category": rf.category,
                        "severity": rf.severity,
                        "description": rf.description,
                        "citations": [
                            {
                                "source_type": c.source_type,
                                "source_id": c.source_id,
                                "source_name": c.source_name,
                                "excerpt": c.excerpt,
                            }
                            for c in rf.citations
                        ],
                    }
                    for rf in summary.risk_factors
                ],
                "recommendations": summary.recommendations,
                "model_version": summary.model_version,
                "generated_at": summary.generated_at.isoformat(),
            }

            job_logger.info(f"Risk summary complete for {applicant_id}")

            return response

        except Exception as e:
            job_logger.error(f"AI worker error for {applicant_id}: {e}")
            await db.rollback()
            raise  # Re-raise for ARQ retry


async def _update_applicant_from_summary(
    db: Any,
    applicant: Applicant,
    summary: RiskSummary,
) -> None:
    """
    Update applicant record with AI assessment results.

    Args:
        db: Database session
        applicant: Applicant model instance
        summary: RiskSummary from AI service
    """
    # Convert risk factors to storage format
    risk_factors = [
        {
            "factor": rf.description,
            "impact": rf.severity,
            "source": "ai_assessment",
            "category": rf.category,
            "citations": [
                {
                    "type": c.source_type,
                    "id": c.source_id,
                    "name": c.source_name,
                }
                for c in rf.citations
            ],
        }
        for rf in summary.risk_factors
    ]

    # Merge with existing risk factors (keep manual ones)
    existing_factors = applicant.risk_factors or []
    manual_factors = [f for f in existing_factors if f.get("source") != "ai_assessment"]
    merged_factors = manual_factors + risk_factors

    # Determine if status should change based on risk
    new_status = applicant.status
    if summary.risk_score >= 75 and applicant.status not in ["rejected", "approved"]:
        new_status = "review"  # High risk needs review

    # Update applicant
    await db.execute(
        update(Applicant)
        .where(Applicant.id == applicant.id)
        .values(
            risk_score=summary.risk_score,
            risk_factors=merged_factors,
            status=new_status,
        )
    )

    logger.info(
        f"Updated applicant {applicant.id}: "
        f"risk_score={summary.risk_score}, status={new_status}"
    )


async def batch_generate_summaries(
    ctx: dict[str, Any],
    applicant_ids: list[str],
    update_applicants: bool = True,
) -> dict[str, Any]:
    """
    Generate risk summaries for multiple applicants.

    This is a batch job for processing multiple applicants
    in sequence. Useful for backfilling or periodic re-assessment.

    Args:
        ctx: ARQ context with logger
        applicant_ids: List of applicant UUIDs to process
        update_applicants: Whether to update applicant records

    Returns:
        Dict with success/failure counts and details
    """
    job_logger = ctx.get("logger", logger)
    job_logger.info(f"Starting batch AI processing for {len(applicant_ids)} applicants")

    results = {
        "total": len(applicant_ids),
        "success": 0,
        "failed": 0,
        "skipped": 0,
        "details": [],
    }

    for applicant_id in applicant_ids:
        try:
            result = await generate_risk_summary(
                ctx=ctx,
                applicant_id=applicant_id,
                update_applicant=update_applicants,
            )

            if result.get("status") == "success":
                results["success"] += 1
            elif result.get("status") == "skipped":
                results["skipped"] += 1
            else:
                results["failed"] += 1

            results["details"].append({
                "applicant_id": applicant_id,
                "status": result.get("status"),
                "risk_score": result.get("risk_score"),
            })

        except Exception as e:
            job_logger.error(f"Batch processing error for {applicant_id}: {e}")
            results["failed"] += 1
            results["details"].append({
                "applicant_id": applicant_id,
                "status": "error",
                "error": str(e),
            })

    job_logger.info(
        f"Batch complete: {results['success']} success, "
        f"{results['failed']} failed, {results['skipped']} skipped"
    )

    return results


async def analyze_screening_hit(
    ctx: dict[str, Any],
    hit_id: str,
) -> dict[str, Any]:
    """
    Generate AI suggestion for resolving a screening hit.

    This worker analyzes a screening hit and provides a
    recommendation on whether it's a true match or false positive.

    Args:
        ctx: ARQ context with logger
        hit_id: UUID of the screening hit to analyze

    Returns:
        Dict with suggested resolution and reasoning
    """
    job_logger = ctx.get("logger", logger)
    job_logger.info(f"Starting AI hit analysis for {hit_id}")

    async with get_db_context() as db:
        try:
            # Check if AI service is configured
            if not ai_service.is_configured:
                job_logger.warning("AI service not configured")
                return {
                    "status": "skipped",
                    "reason": "AI service not configured",
                }

            # Generate resolution suggestion
            suggestion = await ai_service.suggest_hit_resolution(
                db=db,
                hit_id=UUID(hit_id),
            )

            job_logger.info(
                f"Hit analysis complete: "
                f"suggestion={suggestion.suggested_resolution}, "
                f"confidence={suggestion.confidence}"
            )

            return {
                "status": "success",
                "hit_id": hit_id,
                "suggested_resolution": suggestion.suggested_resolution,
                "confidence": suggestion.confidence,
                "reasoning": suggestion.reasoning,
                "evidence": [
                    {
                        "source_type": e.source_type,
                        "source_name": e.source_name,
                        "excerpt": e.excerpt,
                    }
                    for e in suggestion.evidence
                ],
                "generated_at": suggestion.generated_at.isoformat(),
            }

        except Exception as e:
            job_logger.error(f"AI hit analysis error for {hit_id}: {e}")
            raise  # Re-raise for ARQ retry
