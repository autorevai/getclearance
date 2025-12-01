"""
Get Clearance - Screening Worker
=================================
Background worker for running AML/Sanctions/PEP screening.

This worker:
1. Runs screening checks against OpenSanctions
2. Stores hits in the database
3. Updates applicant status based on results
4. Creates timeline events for audit

Usage (from API):
    from arq import create_pool
    from app.workers.config import get_redis_settings

    redis = await create_pool(get_redis_settings())
    job = await redis.enqueue_job(
        'run_screening_check',
        applicant_id='uuid-here',
        check_types=['sanctions', 'pep']
    )
"""

import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from app.database import get_db_context
from app.models import Applicant, ScreeningCheck, ScreeningHit, ScreeningList
from app.services.screening import screening_service, ScreeningResult, ScreeningHitResult

logger = logging.getLogger(__name__)


async def run_screening_check(
    ctx: dict[str, Any],
    applicant_id: str,
    check_types: list[str] | None = None,
    threshold: float = 0.5,
) -> dict[str, Any]:
    """
    Run AML/Sanctions/PEP screening for an applicant.

    This is the main screening worker function. It:
    1. Fetches applicant data from database
    2. Runs screening via OpenSanctions
    3. Stores screening check and hits
    4. Updates applicant status

    Args:
        ctx: ARQ context with logger
        applicant_id: UUID of the applicant to screen
        check_types: Types of checks to run (defaults to all)
        threshold: Minimum match confidence (0-1)

    Returns:
        Dict with status, hit_count, and check_id

    Raises:
        Exception: If screening fails (ARQ will retry)
    """
    job_logger = ctx.get("logger", logger)
    job_logger.info(f"Starting screening check for applicant {applicant_id}")

    # Default check types
    if check_types is None:
        check_types = ["sanctions", "pep", "adverse_media"]

    async with get_db_context() as db:
        try:
            # Fetch applicant
            query = select(Applicant).where(Applicant.id == UUID(applicant_id))
            result = await db.execute(query)
            applicant = result.scalar_one_or_none()

            if not applicant:
                job_logger.error(f"Applicant not found: {applicant_id}")
                return {"status": "error", "error": "Applicant not found"}

            job_logger.info(
                f"Screening {applicant.full_name} "
                f"(DOB: {applicant.date_of_birth}, "
                f"Nationality: {applicant.nationality})"
            )

            # Create screening check record
            screening_check = ScreeningCheck(
                tenant_id=applicant.tenant_id,
                applicant_id=applicant.id,
                entity_type="individual",
                screened_name=applicant.full_name,
                screened_dob=applicant.date_of_birth,
                screened_country=applicant.nationality,
                check_types=check_types,
                status="pending",
                started_at=datetime.utcnow(),
            )
            db.add(screening_check)
            await db.flush()  # Get the ID

            # Run screening via service
            screening_result: ScreeningResult = await screening_service.check_individual(
                name=applicant.full_name,
                birth_date=applicant.date_of_birth,
                countries=[c for c in [applicant.nationality, applicant.country_of_residence] if c],
                threshold=threshold,
            )

            # Handle error status
            if screening_result.status == "error":
                screening_check.status = "error"
                screening_check.completed_at = datetime.utcnow()
                await db.commit()

                job_logger.error(
                    f"Screening error for {applicant_id}: "
                    f"{screening_result.error_message}"
                )
                # Re-raise to trigger ARQ retry
                raise Exception(f"Screening failed: {screening_result.error_message}")

            # Get or create screening list record
            list_version = screening_result.list_version_id
            list_record = await _get_or_create_screening_list(
                db, "opensanctions", list_version, check_types
            )

            # Process hits
            hit_count = 0
            for hit in screening_result.hits:
                screening_hit = _create_screening_hit(
                    check_id=screening_check.id,
                    list_id=list_record.id if list_record else None,
                    hit_data=hit,
                )
                db.add(screening_hit)
                hit_count += 1

            # Update screening check
            screening_check.status = "hit" if hit_count > 0 else "clear"
            screening_check.hit_count = hit_count
            screening_check.completed_at = datetime.utcnow()

            # Update applicant status and flags based on results
            await _update_applicant_from_screening(
                db, applicant, screening_result, hit_count
            )

            await db.commit()

            job_logger.info(
                f"Screening complete for {applicant_id}: "
                f"{screening_check.status} ({hit_count} hits)"
            )

            return {
                "status": "success",
                "screening_status": screening_check.status,
                "hit_count": hit_count,
                "check_id": str(screening_check.id),
                "list_version": list_version,
            }

        except Exception as e:
            job_logger.error(f"Screening worker error for {applicant_id}: {e}")
            await db.rollback()
            raise  # Re-raise for ARQ retry


async def _get_or_create_screening_list(
    db: Any,
    source: str,
    version_id: str,
    check_types: list[str],
) -> ScreeningList | None:
    """Get existing screening list or create new one."""
    # Check if list exists
    query = select(ScreeningList).where(
        ScreeningList.source == source,
        ScreeningList.version_id == version_id,
    )
    result = await db.execute(query)
    existing = result.scalar_one_or_none()

    if existing:
        return existing

    # Create new list record
    list_record = ScreeningList(
        source=source,
        version_id=version_id,
        list_type=check_types[0] if check_types else "sanctions",
        fetched_at=datetime.utcnow(),
    )
    db.add(list_record)
    await db.flush()

    return list_record


def _create_screening_hit(
    check_id: UUID,
    list_id: UUID | None,
    hit_data: ScreeningHitResult,
) -> ScreeningHit:
    """Create a ScreeningHit model from service result."""
    return ScreeningHit(
        check_id=check_id,
        list_id=list_id,
        list_source=hit_data.list_source,
        list_version_id=hit_data.list_version_id,
        hit_type=hit_data.hit_type,
        matched_entity_id=hit_data.matched_entity_id,
        matched_name=hit_data.matched_name,
        confidence=hit_data.confidence,
        matched_fields=hit_data.matched_fields,
        match_data=hit_data.match_data,
        pep_tier=hit_data.pep_tier,
        pep_position=hit_data.pep_position,
        pep_relationship=hit_data.pep_relationship,
        article_url=hit_data.article_url,
        article_title=hit_data.article_title,
        article_date=hit_data.article_date,
        categories=hit_data.categories,
        resolution_status="pending",
        created_at=datetime.utcnow(),
    )


async def _update_applicant_from_screening(
    db: Any,
    applicant: Applicant,
    result: ScreeningResult,
    hit_count: int,
) -> None:
    """
    Update applicant status and flags based on screening results.

    - If clear: Move to next step or mark for review
    - If hits: Flag applicant and create case for review
    """
    # Collect flags based on hits
    new_flags: list[str] = list(applicant.flags or [])

    for hit in result.hits:
        if hit.hit_type == "sanctions" and "sanctions" not in new_flags:
            new_flags.append("sanctions")
        elif hit.hit_type == "pep" and "pep" not in new_flags:
            new_flags.append("pep")
        elif hit.hit_type == "adverse_media" and "adverse_media" not in new_flags:
            new_flags.append("adverse_media")

    # Calculate risk score impact
    risk_score = applicant.risk_score or 0

    for hit in result.hits:
        if hit.hit_type == "sanctions":
            risk_score = min(100, risk_score + 50)  # Sanctions = high risk
        elif hit.hit_type == "pep":
            tier = hit.pep_tier or 2
            risk_score = min(100, risk_score + (40 - tier * 10))  # Tier 1 = +30, Tier 2 = +20, etc.
        elif hit.hit_type == "adverse_media":
            risk_score = min(100, risk_score + 20)

    # Update applicant
    update_stmt = (
        update(Applicant)
        .where(Applicant.id == applicant.id)
        .values(
            flags=new_flags,
            risk_score=risk_score,
            # Move to review if hits found, otherwise keep current status
            status="review" if hit_count > 0 else applicant.status,
        )
    )
    await db.execute(update_stmt)

    logger.info(
        f"Updated applicant {applicant.id}: "
        f"flags={new_flags}, risk_score={risk_score}"
    )
