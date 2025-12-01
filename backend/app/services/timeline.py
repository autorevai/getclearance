"""
Get Clearance - Timeline Service
=================================
Event aggregation service for applicant timeline generation.

Provides chronological event history for compliance audits and
evidence pack generation.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


# ===========================================
# DATA CLASSES
# ===========================================

@dataclass
class TimelineEvent:
    """A single event in the applicant timeline."""
    id: str
    timestamp: datetime
    event_type: str
    actor_type: str | None
    actor_id: str | None
    actor_name: str | None
    details: dict[str, Any]
    description: str


@dataclass
class TimelineGroup:
    """Events grouped by date."""
    date: str  # ISO date format (YYYY-MM-DD)
    events: list[TimelineEvent] = field(default_factory=list)


@dataclass
class ApplicantTimeline:
    """Complete timeline for an applicant."""
    applicant_id: str
    applicant_name: str
    total_events: int
    groups: list[TimelineGroup]
    generated_at: datetime = field(default_factory=datetime.utcnow)


class TimelineServiceError(Exception):
    """Base exception for timeline service errors."""
    pass


# ===========================================
# EVENT TYPE DESCRIPTIONS
# ===========================================

EVENT_DESCRIPTIONS = {
    # Application lifecycle
    "applicant_created": "Application created",
    "applicant_submitted": "Application submitted for review",
    "status_changed": "Application status changed",
    "applicant_approved": "Application approved",
    "applicant_rejected": "Application rejected",

    # Document events
    "document_uploaded": "Document uploaded",
    "document_verified": "Document verified",
    "document_rejected": "Document rejected",
    "document_analyzed": "Document analyzed by AI",
    "ocr_completed": "OCR processing completed",
    "fraud_detected": "Potential fraud signal detected",

    # Screening events
    "screening_started": "Screening check initiated",
    "screening_completed": "Screening check completed",
    "screening_hit_found": "Screening hit found",
    "screening_hit_resolved": "Screening hit resolved",
    "screening_cleared": "Screening cleared - no hits",

    # Case events
    "case_created": "Investigation case created",
    "case_assigned": "Case assigned to reviewer",
    "case_note_added": "Note added to case",
    "case_resolved": "Case resolved",
    "case_escalated": "Case escalated",

    # Review events
    "manual_review": "Manual review performed",
    "risk_score_updated": "Risk score updated",
    "risk_override": "Risk score manually overridden",

    # Verification events
    "liveness_completed": "Liveness check completed",
    "selfie_verified": "Selfie verification completed",
    "address_verified": "Address verification completed",

    # System events
    "workflow_started": "Verification workflow started",
    "step_completed": "Workflow step completed",
    "resubmission_requested": "Document resubmission requested",
    "evidence_exported": "Evidence pack exported",
}


def _get_event_description(event_type: str, event_data: dict[str, Any] | None) -> str:
    """
    Generate human-readable description for an event.

    Args:
        event_type: The type of event
        event_data: Additional event data

    Returns:
        Human-readable description
    """
    base_description = EVENT_DESCRIPTIONS.get(event_type, f"Event: {event_type}")

    if not event_data:
        return base_description

    # Add context from event data
    if event_type == "status_changed":
        old_status = event_data.get("old_status", "unknown")
        new_status = event_data.get("new_status", "unknown")
        return f"Status changed from '{old_status}' to '{new_status}'"

    elif event_type == "document_uploaded":
        doc_type = event_data.get("document_type", "document")
        return f"{doc_type.replace('_', ' ').title()} uploaded"

    elif event_type == "screening_hit_found":
        hit_type = event_data.get("hit_type", "screening")
        confidence = event_data.get("confidence", 0)
        return f"{hit_type.upper()} hit found ({confidence:.0f}% confidence)"

    elif event_type == "screening_hit_resolved":
        resolution = event_data.get("resolution", "resolved")
        return f"Screening hit marked as {resolution.replace('_', ' ')}"

    elif event_type == "case_created":
        case_type = event_data.get("case_type", "investigation")
        return f"{case_type.replace('_', ' ').title()} case created"

    elif event_type == "risk_score_updated":
        score = event_data.get("risk_score", "unknown")
        return f"Risk score updated to {score}"

    return base_description


def _get_actor_name(actor_type: str | None, actor_id: str | None, event_data: dict[str, Any] | None) -> str | None:
    """
    Get human-readable actor name.

    Args:
        actor_type: Type of actor (system, applicant, reviewer, etc.)
        actor_id: UUID of actor (if applicable)
        event_data: Additional event data that may contain actor info

    Returns:
        Actor name or None
    """
    if not actor_type:
        return None

    if actor_type == "system":
        return "System"
    elif actor_type == "applicant":
        return "Applicant"
    elif actor_type == "api":
        return "API Integration"
    elif actor_type == "worker":
        return "Background Worker"
    elif actor_type == "reviewer":
        # Try to get reviewer name from event_data
        if event_data and "reviewer_email" in event_data:
            return event_data["reviewer_email"]
        return "Reviewer"

    return actor_type.title()


# ===========================================
# TIMELINE SERVICE
# ===========================================

class TimelineService:
    """
    Service for aggregating and formatting applicant timeline events.

    Retrieves events from the applicant_events table and formats them
    into a chronological timeline suitable for evidence packs and
    compliance audits.

    Usage:
        timeline = await timeline_service.get_applicant_timeline(
            db=session,
            applicant_id=uuid
        )

        for group in timeline.groups:
            print(f"Date: {group.date}")
            for event in group.events:
                print(f"  {event.timestamp}: {event.description}")
    """

    async def get_applicant_timeline(
        self,
        db: AsyncSession,
        applicant_id: UUID,
        limit: int | None = None,
        event_types: list[str] | None = None,
    ) -> ApplicantTimeline:
        """
        Get chronological event timeline for an applicant.

        Args:
            db: Database session
            applicant_id: Applicant UUID
            limit: Maximum number of events to return
            event_types: Filter to specific event types

        Returns:
            ApplicantTimeline with grouped events
        """
        from app.models import Applicant

        # First get applicant info
        applicant_query = select(Applicant).where(Applicant.id == applicant_id)
        result = await db.execute(applicant_query)
        applicant = result.scalar_one_or_none()

        if not applicant:
            raise TimelineServiceError(f"Applicant not found: {applicant_id}")

        applicant_name = f"{applicant.first_name or ''} {applicant.last_name or ''}".strip() or "Unknown"

        # Build events query
        # Note: Using raw SQL since ApplicantEvent model may not exist yet
        query = text("""
            SELECT
                id,
                event_type,
                event_data,
                actor_type,
                actor_id,
                timestamp
            FROM applicant_events
            WHERE applicant_id = :applicant_id
            ORDER BY timestamp DESC
        """)

        params: dict[str, Any] = {"applicant_id": applicant_id}

        try:
            result = await db.execute(query, params)
            rows = result.fetchall()
        except Exception as e:
            # Table might not exist yet - return empty timeline
            logger.warning(f"Could not fetch applicant events: {e}")
            rows = []

        # Process events and group by date
        events: list[TimelineEvent] = []

        for row in rows:
            event_data = row.event_data or {}

            event = TimelineEvent(
                id=str(row.id),
                timestamp=row.timestamp,
                event_type=row.event_type,
                actor_type=row.actor_type,
                actor_id=str(row.actor_id) if row.actor_id else None,
                actor_name=_get_actor_name(row.actor_type, row.actor_id, event_data),
                details=event_data,
                description=_get_event_description(row.event_type, event_data),
            )
            events.append(event)

            if limit and len(events) >= limit:
                break

        # Apply event type filter if specified
        if event_types:
            events = [e for e in events if e.event_type in event_types]

        # Group events by date
        groups_dict: dict[str, list[TimelineEvent]] = {}
        for event in events:
            date_key = event.timestamp.strftime("%Y-%m-%d")
            if date_key not in groups_dict:
                groups_dict[date_key] = []
            groups_dict[date_key].append(event)

        # Convert to sorted list of groups
        groups = [
            TimelineGroup(date=date, events=evts)
            for date, evts in sorted(groups_dict.items(), reverse=True)
        ]

        return ApplicantTimeline(
            applicant_id=str(applicant_id),
            applicant_name=applicant_name,
            total_events=len(events),
            groups=groups,
        )

    async def get_events_for_date_range(
        self,
        db: AsyncSession,
        applicant_id: UUID,
        start_date: datetime,
        end_date: datetime,
    ) -> list[TimelineEvent]:
        """
        Get events within a specific date range.

        Args:
            db: Database session
            applicant_id: Applicant UUID
            start_date: Start of date range
            end_date: End of date range

        Returns:
            List of TimelineEvent objects
        """
        query = text("""
            SELECT
                id,
                event_type,
                event_data,
                actor_type,
                actor_id,
                timestamp
            FROM applicant_events
            WHERE applicant_id = :applicant_id
              AND timestamp >= :start_date
              AND timestamp <= :end_date
            ORDER BY timestamp DESC
        """)

        try:
            result = await db.execute(query, {
                "applicant_id": applicant_id,
                "start_date": start_date,
                "end_date": end_date,
            })
            rows = result.fetchall()
        except Exception as e:
            logger.warning(f"Could not fetch events for date range: {e}")
            return []

        events = []
        for row in rows:
            event_data = row.event_data or {}
            events.append(TimelineEvent(
                id=str(row.id),
                timestamp=row.timestamp,
                event_type=row.event_type,
                actor_type=row.actor_type,
                actor_id=str(row.actor_id) if row.actor_id else None,
                actor_name=_get_actor_name(row.actor_type, row.actor_id, event_data),
                details=event_data,
                description=_get_event_description(row.event_type, event_data),
            ))

        return events

    async def record_event(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        applicant_id: UUID,
        event_type: str,
        event_data: dict[str, Any] | None = None,
        actor_type: str | None = None,
        actor_id: UUID | None = None,
    ) -> str:
        """
        Record a new event in the applicant timeline.

        Args:
            db: Database session
            tenant_id: Tenant UUID
            applicant_id: Applicant UUID
            event_type: Type of event
            event_data: Additional event data
            actor_type: Type of actor (system, applicant, reviewer, etc.)
            actor_id: UUID of actor (if applicable)

        Returns:
            UUID of created event
        """
        import json

        query = text("""
            INSERT INTO applicant_events (
                tenant_id, applicant_id, event_type, event_data, actor_type, actor_id
            ) VALUES (
                :tenant_id, :applicant_id, :event_type, :event_data, :actor_type, :actor_id
            )
            RETURNING id
        """)

        try:
            result = await db.execute(query, {
                "tenant_id": tenant_id,
                "applicant_id": applicant_id,
                "event_type": event_type,
                "event_data": json.dumps(event_data) if event_data else None,
                "actor_type": actor_type,
                "actor_id": actor_id,
            })
            row = result.fetchone()
            event_id = str(row.id) if row else ""

            logger.info(f"Recorded event {event_type} for applicant {applicant_id}")
            return event_id

        except Exception as e:
            logger.error(f"Failed to record event: {e}")
            raise TimelineServiceError(f"Failed to record event: {e}")


# ===========================================
# SINGLETON INSTANCE
# ===========================================

timeline_service = TimelineService()
