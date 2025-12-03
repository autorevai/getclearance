"""
Get Clearance - Monitoring Service
===================================
Ongoing AML monitoring for approved applicants.

This service handles:
1. Enabling/disabling monitoring for applicants
2. Running batch re-screening of monitored applicants
3. Comparing current vs previous screening results
4. Creating alerts for new hits

Usage:
    from app.services.monitoring import monitoring_service

    # Enable monitoring for approved applicant
    await monitoring_service.enable_monitoring(db, applicant_id)

    # Run daily batch monitoring
    results = await monitoring_service.run_monitoring_batch(db, tenant_id)
"""

import logging
from dataclasses import dataclass
from datetime import datetime, date
from typing import Any
from uuid import UUID

from sqlalchemy import select, update, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Applicant, ScreeningCheck, ScreeningHit
from app.models.monitoring_alert import MonitoringAlert
from app.services.screening import (
    screening_service,
    ScreeningResult,
    ScreeningConfigError,
)

logger = logging.getLogger(__name__)


@dataclass
class MonitoringBatchResult:
    """Result from a monitoring batch run."""
    screened: int
    new_alerts: int
    errors: int
    skipped: int
    details: list[dict[str, Any]]


@dataclass
class NewHitInfo:
    """Information about a new hit detected during monitoring."""
    hit_id: UUID
    matched_name: str
    hit_type: str
    confidence: float
    list_source: str
    matched_entity_id: str | None


class MonitoringService:
    """
    Service for ongoing AML monitoring of approved applicants.

    Handles enabling/disabling monitoring, running batch re-screening,
    and generating alerts for new hits.
    """

    async def enable_monitoring(
        self,
        db: AsyncSession,
        applicant_id: UUID,
        tenant_id: UUID | None = None,
    ) -> bool:
        """
        Enable ongoing monitoring for an applicant.

        Only approved applicants can have monitoring enabled.

        Args:
            db: Database session
            applicant_id: UUID of applicant
            tenant_id: Optional tenant ID for verification

        Returns:
            True if monitoring was enabled, False if not eligible

        Raises:
            ValueError: If applicant not found
        """
        query = select(Applicant).where(Applicant.id == applicant_id)
        if tenant_id:
            query = query.where(Applicant.tenant_id == tenant_id)

        result = await db.execute(query)
        applicant = result.scalar_one_or_none()

        if not applicant:
            raise ValueError(f"Applicant not found: {applicant_id}")

        # Only enable monitoring for approved applicants
        if applicant.status != "approved":
            logger.warning(
                f"Cannot enable monitoring for non-approved applicant "
                f"{applicant_id} (status: {applicant.status})"
            )
            return False

        # Update applicant - we need to add monitoring_enabled field
        # For now, store in flags
        flags = list(applicant.flags or [])
        if "monitoring_enabled" not in flags:
            flags.append("monitoring_enabled")
            applicant.flags = flags

            logger.info(f"Monitoring enabled for applicant {applicant_id}")

        return True

    async def disable_monitoring(
        self,
        db: AsyncSession,
        applicant_id: UUID,
        tenant_id: UUID | None = None,
    ) -> bool:
        """
        Disable ongoing monitoring for an applicant.

        Args:
            db: Database session
            applicant_id: UUID of applicant
            tenant_id: Optional tenant ID for verification

        Returns:
            True if monitoring was disabled
        """
        query = select(Applicant).where(Applicant.id == applicant_id)
        if tenant_id:
            query = query.where(Applicant.tenant_id == tenant_id)

        result = await db.execute(query)
        applicant = result.scalar_one_or_none()

        if not applicant:
            raise ValueError(f"Applicant not found: {applicant_id}")

        # Remove monitoring flag
        flags = list(applicant.flags or [])
        if "monitoring_enabled" in flags:
            flags.remove("monitoring_enabled")
            applicant.flags = flags
            logger.info(f"Monitoring disabled for applicant {applicant_id}")

        return True

    async def is_monitoring_enabled(
        self,
        db: AsyncSession,
        applicant_id: UUID,
    ) -> bool:
        """Check if monitoring is enabled for an applicant."""
        result = await db.execute(
            select(Applicant.flags).where(Applicant.id == applicant_id)
        )
        flags = result.scalar_one_or_none()

        if flags is None:
            return False

        return "monitoring_enabled" in (flags or [])

    async def get_monitored_applicants(
        self,
        db: AsyncSession,
        tenant_id: UUID | None = None,
        limit: int = 1000,
    ) -> list[Applicant]:
        """
        Get all applicants with monitoring enabled.

        Args:
            db: Database session
            tenant_id: Optional tenant filter
            limit: Maximum applicants to return

        Returns:
            List of applicants with monitoring enabled
        """
        # Query for applicants with monitoring_enabled in flags
        # and status = approved
        query = select(Applicant).where(
            Applicant.status == "approved",
            Applicant.flags.contains(["monitoring_enabled"]),
        )

        if tenant_id:
            query = query.where(Applicant.tenant_id == tenant_id)

        query = query.limit(limit)

        result = await db.execute(query)
        return list(result.scalars().all())

    async def run_monitoring_batch(
        self,
        db: AsyncSession,
        tenant_id: UUID | None = None,
    ) -> MonitoringBatchResult:
        """
        Re-screen all applicants with monitoring enabled.

        Called by scheduled worker (daily). For each monitored applicant:
        1. Run new screening check
        2. Compare against previous screening
        3. Create alerts for any new hits

        Args:
            db: Database session
            tenant_id: Optional tenant filter

        Returns:
            MonitoringBatchResult with counts and details
        """
        logger.info(
            f"Starting monitoring batch run"
            f"{' for tenant ' + str(tenant_id) if tenant_id else ''}"
        )

        result = MonitoringBatchResult(
            screened=0,
            new_alerts=0,
            errors=0,
            skipped=0,
            details=[],
        )

        # Get monitored applicants
        applicants = await self.get_monitored_applicants(db, tenant_id)
        logger.info(f"Found {len(applicants)} applicants to re-screen")

        for applicant in applicants:
            try:
                applicant_result = await self._screen_and_compare(db, applicant)

                if applicant_result.get("skipped"):
                    result.skipped += 1
                else:
                    result.screened += 1
                    if applicant_result.get("new_alert"):
                        result.new_alerts += 1

                result.details.append(applicant_result)

            except Exception as e:
                logger.error(
                    f"Error screening applicant {applicant.id}: {e}",
                    exc_info=True,
                )
                result.errors += 1
                result.details.append({
                    "applicant_id": str(applicant.id),
                    "error": str(e),
                })

        logger.info(
            f"Monitoring batch complete: "
            f"screened={result.screened}, "
            f"new_alerts={result.new_alerts}, "
            f"errors={result.errors}, "
            f"skipped={result.skipped}"
        )

        return result

    async def _screen_and_compare(
        self,
        db: AsyncSession,
        applicant: Applicant,
    ) -> dict[str, Any]:
        """
        Screen an applicant and compare with previous results.

        Args:
            db: Database session
            applicant: Applicant to screen

        Returns:
            Dict with screening results
        """
        # Get previous screening check
        prev_query = (
            select(ScreeningCheck)
            .where(
                ScreeningCheck.applicant_id == applicant.id,
                ScreeningCheck.status.in_(["clear", "hit"]),
            )
            .order_by(ScreeningCheck.created_at.desc())
            .limit(1)
            .options(selectinload(ScreeningCheck.hits))
        )
        prev_result = await db.execute(prev_query)
        previous_check = prev_result.scalar_one_or_none()

        # Run new screening
        try:
            full_name = applicant.full_name
            if not full_name or full_name == "Unknown":
                return {
                    "applicant_id": str(applicant.id),
                    "skipped": True,
                    "reason": "Missing name",
                }

            countries = [c for c in [applicant.nationality, applicant.country_of_residence] if c]

            screening_result = await screening_service.check_individual(
                name=full_name,
                birth_date=applicant.date_of_birth,
                countries=countries if countries else None,
            )

        except ScreeningConfigError:
            # OpenSanctions not configured - skip
            return {
                "applicant_id": str(applicant.id),
                "skipped": True,
                "reason": "Screening not configured",
            }

        # Create screening check record
        new_check = ScreeningCheck(
            tenant_id=applicant.tenant_id,
            applicant_id=applicant.id,
            entity_type="individual",
            screened_name=full_name,
            screened_dob=applicant.date_of_birth,
            screened_country=applicant.nationality,
            check_types=["sanctions", "pep", "adverse_media"],
            status=screening_result.status,
            hit_count=len(screening_result.hits),
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
        )
        db.add(new_check)
        await db.flush()

        # Create hit records
        new_hit_records = []
        for hit in screening_result.hits:
            hit_record = ScreeningHit(
                check_id=new_check.id,
                list_source=hit.list_source,
                list_version_id=hit.list_version_id,
                hit_type=hit.hit_type,
                matched_entity_id=hit.matched_entity_id,
                matched_name=hit.matched_name,
                confidence=hit.confidence,
                matched_fields=hit.matched_fields,
                match_data=hit.match_data,
                pep_tier=hit.pep_tier,
                pep_position=hit.pep_position,
                categories=hit.categories,
                resolution_status="pending",
            )
            db.add(hit_record)
            new_hit_records.append(hit_record)

        await db.flush()

        # Compare with previous screening
        new_hits = await self._find_new_hits(
            previous_check, new_hit_records
        )

        result_data = {
            "applicant_id": str(applicant.id),
            "screening_check_id": str(new_check.id),
            "status": screening_result.status,
            "total_hits": len(screening_result.hits),
            "new_hits": len(new_hits),
            "new_alert": False,
        }

        # Create alert if new hits found
        if new_hits:
            alert = await self.create_monitoring_alert(
                db=db,
                applicant=applicant,
                previous_check=previous_check,
                new_check=new_check,
                new_hits=new_hits,
            )
            result_data["new_alert"] = True
            result_data["alert_id"] = str(alert.id)

        return result_data

    async def _find_new_hits(
        self,
        previous_check: ScreeningCheck | None,
        new_hits: list[ScreeningHit],
    ) -> list[NewHitInfo]:
        """
        Find hits that are new compared to previous screening.

        A hit is considered "new" if:
        1. There was no previous screening, OR
        2. The matched_entity_id wasn't in the previous hits

        Args:
            previous_check: Previous screening check (may be None)
            new_hits: New hit records from current screening

        Returns:
            List of NewHitInfo for genuinely new hits
        """
        if not new_hits:
            return []

        # Get previous entity IDs
        previous_entity_ids: set[str] = set()
        if previous_check and previous_check.hits:
            for hit in previous_check.hits:
                if hit.matched_entity_id:
                    previous_entity_ids.add(hit.matched_entity_id)

        # Find new hits
        new_hit_infos = []
        for hit in new_hits:
            # Consider hit new if:
            # 1. No previous screening
            # 2. Entity ID not in previous hits
            # 3. Entity ID is None (can't compare, treat as new)
            is_new = (
                previous_check is None or
                not hit.matched_entity_id or
                hit.matched_entity_id not in previous_entity_ids
            )

            if is_new:
                new_hit_infos.append(NewHitInfo(
                    hit_id=hit.id,
                    matched_name=hit.matched_name,
                    hit_type=hit.hit_type,
                    confidence=float(hit.confidence),
                    list_source=hit.list_source,
                    matched_entity_id=hit.matched_entity_id,
                ))

        return new_hit_infos

    async def create_monitoring_alert(
        self,
        db: AsyncSession,
        applicant: Applicant,
        previous_check: ScreeningCheck | None,
        new_check: ScreeningCheck,
        new_hits: list[NewHitInfo],
    ) -> MonitoringAlert:
        """
        Create a monitoring alert for new hits.

        Args:
            db: Database session
            applicant: Applicant who was screened
            previous_check: Previous screening (may be None)
            new_check: New screening check
            new_hits: List of new hits found

        Returns:
            Created MonitoringAlert
        """
        # Determine severity based on hit types
        hit_types = list(set(h.hit_type for h in new_hits))
        severity = self._determine_severity(new_hits)

        # Determine alert type
        if previous_check is None:
            alert_type = "new_hit"  # First-time hit
        else:
            alert_type = "new_hit"  # New hit on re-screen

        # Build new_hits JSON
        new_hits_data = [
            {
                "hit_id": str(h.hit_id),
                "matched_name": h.matched_name,
                "hit_type": h.hit_type,
                "confidence": h.confidence,
                "list_source": h.list_source,
            }
            for h in new_hits
        ]

        alert = MonitoringAlert(
            tenant_id=applicant.tenant_id,
            applicant_id=applicant.id,
            alert_type=alert_type,
            severity=severity,
            previous_screening_id=previous_check.id if previous_check else None,
            new_screening_id=new_check.id,
            new_hits=new_hits_data,
            hit_count=len(new_hits),
            hit_types=hit_types,
            status="open",
        )

        db.add(alert)
        await db.flush()

        logger.info(
            f"Created monitoring alert {alert.id} for applicant {applicant.id}: "
            f"{len(new_hits)} new hits, severity={severity}"
        )

        return alert

    def _determine_severity(self, hits: list[NewHitInfo]) -> str:
        """Determine alert severity based on hits."""
        # Sanctions = critical/high
        # PEP tier 1 = high
        # PEP tier 2+ = medium
        # Adverse media = medium/low

        has_sanctions = any(h.hit_type == "sanctions" for h in hits)
        has_pep = any(h.hit_type == "pep" for h in hits)
        max_confidence = max((h.confidence for h in hits), default=0)

        if has_sanctions and max_confidence >= 90:
            return "critical"
        elif has_sanctions:
            return "high"
        elif has_pep and max_confidence >= 85:
            return "high"
        elif has_pep:
            return "medium"
        elif max_confidence >= 80:
            return "medium"
        else:
            return "low"

    async def get_monitoring_stats(
        self,
        db: AsyncSession,
        tenant_id: UUID,
    ) -> dict[str, Any]:
        """
        Get monitoring statistics for a tenant.

        Returns:
            Dict with monitoring statistics
        """
        from datetime import timedelta

        now = datetime.utcnow()
        thirty_days_ago = now - timedelta(days=30)

        # Count monitored applicants
        monitored_query = select(func.count(Applicant.id)).where(
            Applicant.tenant_id == tenant_id,
            Applicant.status == "approved",
            Applicant.flags.contains(["monitoring_enabled"]),
        )
        monitored_result = await db.execute(monitored_query)
        monitored_count = monitored_result.scalar() or 0

        # Count open alerts
        open_alerts_query = select(func.count(MonitoringAlert.id)).where(
            MonitoringAlert.tenant_id == tenant_id,
            MonitoringAlert.status.in_(["open", "reviewing"]),
        )
        open_alerts_result = await db.execute(open_alerts_query)
        open_alerts = open_alerts_result.scalar() or 0

        # Count alerts in last 30 days
        recent_alerts_query = select(func.count(MonitoringAlert.id)).where(
            MonitoringAlert.tenant_id == tenant_id,
            MonitoringAlert.created_at >= thirty_days_ago,
        )
        recent_alerts_result = await db.execute(recent_alerts_query)
        recent_alerts = recent_alerts_result.scalar() or 0

        # Count critical alerts
        critical_query = select(func.count(MonitoringAlert.id)).where(
            MonitoringAlert.tenant_id == tenant_id,
            MonitoringAlert.severity == "critical",
            MonitoringAlert.status.in_(["open", "reviewing"]),
        )
        critical_result = await db.execute(critical_query)
        critical_alerts = critical_result.scalar() or 0

        return {
            "monitored_applicants": monitored_count,
            "open_alerts": open_alerts,
            "critical_alerts": critical_alerts,
            "alerts_30d": recent_alerts,
        }


# Singleton instance
monitoring_service = MonitoringService()
