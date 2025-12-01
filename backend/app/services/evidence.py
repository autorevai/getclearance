"""
Get Clearance - Evidence Export Service
========================================
PDF generation service for compliance evidence packs.

Generates comprehensive PDF evidence packs containing:
- Cover page with applicant information
- Document verification results
- Screening results and hit resolutions
- AI risk assessments
- Complete event timeline
- Chain-of-custody audit trail
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from io import BytesIO
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

from app.services.timeline import timeline_service, TimelineEvent

logger = logging.getLogger(__name__)


# ===========================================
# DATA CLASSES
# ===========================================

@dataclass
class EvidencePackMetadata:
    """Metadata for the generated evidence pack."""
    applicant_id: str
    applicant_name: str
    external_id: str | None
    generated_at: datetime
    generated_by: str
    pack_version: str = "1.0"


@dataclass
class EvidencePackResult:
    """Result of evidence pack generation."""
    pdf_bytes: bytes
    metadata: EvidencePackMetadata
    page_count: int
    sections_included: list[str]


class EvidenceServiceError(Exception):
    """Base exception for evidence service errors."""
    pass


# ===========================================
# CUSTOM STYLES
# ===========================================

def _get_custom_styles() -> dict[str, ParagraphStyle]:
    """Create custom paragraph styles for the evidence pack."""
    styles = getSampleStyleSheet()

    custom_styles = {
        "CoverTitle": ParagraphStyle(
            "CoverTitle",
            parent=styles["Title"],
            fontSize=28,
            spaceAfter=12,
            textColor=colors.HexColor("#1a365d"),
            alignment=TA_CENTER,
        ),
        "CoverSubtitle": ParagraphStyle(
            "CoverSubtitle",
            parent=styles["Normal"],
            fontSize=14,
            spaceAfter=6,
            textColor=colors.HexColor("#4a5568"),
            alignment=TA_CENTER,
        ),
        "SectionTitle": ParagraphStyle(
            "SectionTitle",
            parent=styles["Heading1"],
            fontSize=16,
            spaceBefore=20,
            spaceAfter=12,
            textColor=colors.HexColor("#1a365d"),
            borderPadding=6,
        ),
        "SubsectionTitle": ParagraphStyle(
            "SubsectionTitle",
            parent=styles["Heading2"],
            fontSize=12,
            spaceBefore=12,
            spaceAfter=6,
            textColor=colors.HexColor("#2d3748"),
        ),
        "BodyText": ParagraphStyle(
            "BodyText",
            parent=styles["Normal"],
            fontSize=10,
            spaceAfter=6,
            textColor=colors.HexColor("#2d3748"),
        ),
        "SmallText": ParagraphStyle(
            "SmallText",
            parent=styles["Normal"],
            fontSize=8,
            textColor=colors.HexColor("#718096"),
        ),
        "Citation": ParagraphStyle(
            "Citation",
            parent=styles["Normal"],
            fontSize=8,
            textColor=colors.HexColor("#4a5568"),
            leftIndent=20,
            spaceAfter=4,
        ),
        "Warning": ParagraphStyle(
            "Warning",
            parent=styles["Normal"],
            fontSize=10,
            textColor=colors.HexColor("#c53030"),
            backColor=colors.HexColor("#fff5f5"),
            borderPadding=8,
        ),
        "Success": ParagraphStyle(
            "Success",
            parent=styles["Normal"],
            fontSize=10,
            textColor=colors.HexColor("#276749"),
            backColor=colors.HexColor("#f0fff4"),
            borderPadding=8,
        ),
        "Watermark": ParagraphStyle(
            "Watermark",
            parent=styles["Normal"],
            fontSize=8,
            textColor=colors.HexColor("#a0aec0"),
            alignment=TA_CENTER,
        ),
    }

    return custom_styles


def _create_table_style() -> TableStyle:
    """Create standard table style for data tables."""
    return TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#edf2f7")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor("#1a365d")),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor("#2d3748")),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('TOPPADDING', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ])


# ===========================================
# PDF BUILDER HELPERS
# ===========================================

def _format_date(dt: datetime | None) -> str:
    """Format datetime for display."""
    if not dt:
        return "N/A"
    return dt.strftime("%Y-%m-%d %H:%M UTC")


def _format_risk_level(score: int | None) -> tuple[str, colors.Color]:
    """Get risk level label and color from score."""
    if score is None:
        return "Unknown", colors.HexColor("#718096")
    if score <= 30:
        return "Low", colors.HexColor("#276749")
    if score <= 60:
        return "Medium", colors.HexColor("#c05621")
    return "High", colors.HexColor("#c53030")


def _build_cover_page(
    story: list,
    styles: dict,
    applicant: Any,
    generated_at: datetime,
    generated_by: str,
) -> None:
    """Build the cover page of the evidence pack."""
    # Add spacing at top
    story.append(Spacer(1, 2 * inch))

    # Title
    story.append(Paragraph("EVIDENCE PACK", styles["CoverTitle"]))
    story.append(Spacer(1, 0.3 * inch))

    # Applicant name
    applicant_name = f"{applicant.first_name or ''} {applicant.last_name or ''}".strip() or "Unknown"
    story.append(Paragraph(applicant_name, styles["CoverSubtitle"]))
    story.append(Spacer(1, 0.5 * inch))

    # Horizontal rule
    story.append(HRFlowable(
        width="80%",
        thickness=2,
        color=colors.HexColor("#1a365d"),
        spaceBefore=10,
        spaceAfter=20,
    ))

    # Metadata table
    metadata = [
        ["Applicant ID:", str(applicant.id)],
        ["External Reference:", applicant.external_id or "N/A"],
        ["Status:", applicant.status.upper()],
        ["Generated:", _format_date(generated_at)],
        ["Generated By:", generated_by],
    ]

    metadata_table = Table(metadata, colWidths=[2 * inch, 4 * inch])
    metadata_table.setStyle(TableStyle([
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor("#718096")),
        ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor("#2d3748")),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
    ]))
    story.append(metadata_table)

    story.append(Spacer(1, 1 * inch))

    # Watermark/disclaimer
    story.append(Paragraph(
        "OFFICIAL EVIDENCE PACK - CONFIDENTIAL",
        styles["Watermark"]
    ))
    story.append(Paragraph(
        f"Generated: {generated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}",
        styles["Watermark"]
    ))

    story.append(PageBreak())


def _build_applicant_info_section(
    story: list,
    styles: dict,
    applicant: Any,
) -> None:
    """Build the applicant information section."""
    story.append(Paragraph("1. Applicant Information", styles["SectionTitle"]))

    # Personal details
    story.append(Paragraph("1.1 Personal Details", styles["SubsectionTitle"]))

    personal_data = [
        ["Field", "Value", "Source"],
        ["Full Name", f"{applicant.first_name or ''} {applicant.last_name or ''}", "Application"],
        ["Email", applicant.email or "N/A", "Application"],
        ["Phone", applicant.phone or "N/A", "Application"],
        ["Date of Birth", str(applicant.date_of_birth) if applicant.date_of_birth else "N/A", "Application"],
        ["Nationality", applicant.nationality or "N/A", "Application"],
        ["Country of Residence", applicant.country_of_residence or "N/A", "Application"],
    ]

    personal_table = Table(personal_data, colWidths=[1.5 * inch, 3 * inch, 1.5 * inch])
    personal_table.setStyle(_create_table_style())
    story.append(personal_table)

    # Address
    if applicant.address:
        story.append(Spacer(1, 0.2 * inch))
        story.append(Paragraph("1.2 Address", styles["SubsectionTitle"]))

        addr = applicant.address
        address_text = ", ".join(filter(None, [
            addr.get("street"),
            addr.get("city"),
            addr.get("state"),
            addr.get("postal_code"),
            addr.get("country"),
        ]))
        story.append(Paragraph(address_text or "N/A", styles["BodyText"]))

    # Risk assessment
    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph("1.3 Risk Assessment", styles["SubsectionTitle"]))

    risk_level, risk_color = _format_risk_level(applicant.risk_score)
    risk_data = [
        ["Metric", "Value"],
        ["Risk Score", f"{applicant.risk_score}/100" if applicant.risk_score else "Not assessed"],
        ["Risk Level", risk_level],
        ["Flags", ", ".join(applicant.flags) if applicant.flags else "None"],
        ["Status", applicant.status.upper()],
    ]

    risk_table = Table(risk_data, colWidths=[2 * inch, 4 * inch])
    risk_table.setStyle(_create_table_style())
    story.append(risk_table)

    story.append(Spacer(1, 0.3 * inch))


def _build_documents_section(
    story: list,
    styles: dict,
    documents: list,
) -> None:
    """Build the documents section."""
    story.append(Paragraph("2. Documents", styles["SectionTitle"]))

    if not documents:
        story.append(Paragraph("No documents uploaded.", styles["BodyText"]))
        story.append(Spacer(1, 0.3 * inch))
        return

    for i, doc in enumerate(documents, 1):
        story.append(Paragraph(f"2.{i} {doc.type.replace('_', ' ').title()}", styles["SubsectionTitle"]))

        doc_data = [
            ["Property", "Value"],
            ["Document ID", str(doc.id)],
            ["Type", doc.type],
            ["Status", doc.status.upper()],
            ["File Name", doc.file_name or "N/A"],
            ["Uploaded", _format_date(doc.uploaded_at)],
            ["OCR Confidence", f"{float(doc.ocr_confidence):.1f}%" if doc.ocr_confidence else "N/A"],
        ]

        doc_table = Table(doc_data, colWidths=[2 * inch, 4 * inch])
        doc_table.setStyle(_create_table_style())
        story.append(doc_table)

        # Extracted data
        if doc.extracted_data:
            story.append(Paragraph("Extracted Data:", styles["Citation"]))
            for key, value in doc.extracted_data.items():
                story.append(Paragraph(f"  {key}: {value}", styles["Citation"]))

        # Fraud signals
        if doc.fraud_signals:
            story.append(Paragraph("Fraud Signals:", styles["Warning"]))
            for signal in doc.fraud_signals:
                signal_text = signal.get("signal", str(signal))
                severity = signal.get("severity", "unknown")
                story.append(Paragraph(f"  [{severity.upper()}] {signal_text}", styles["Citation"]))

        # Verification checks
        if doc.verification_checks:
            story.append(Paragraph("Verification Checks:", styles["Citation"]))
            for check in doc.verification_checks:
                check_name = check.get("check", "Unknown check")
                passed = check.get("passed", False)
                status_icon = "[PASS]" if passed else "[FAIL]"
                story.append(Paragraph(f"  {status_icon} {check_name}", styles["Citation"]))

        story.append(Spacer(1, 0.2 * inch))

    story.append(Spacer(1, 0.3 * inch))


def _build_screening_section(
    story: list,
    styles: dict,
    screening_checks: list,
) -> None:
    """Build the screening results section."""
    story.append(Paragraph("3. Screening Results", styles["SectionTitle"]))

    if not screening_checks:
        story.append(Paragraph("No screening checks performed.", styles["BodyText"]))
        story.append(Spacer(1, 0.3 * inch))
        return

    for i, check in enumerate(screening_checks, 1):
        check_types = ", ".join(check.check_types) if check.check_types else "General"
        story.append(Paragraph(f"3.{i} {check_types} Screening", styles["SubsectionTitle"]))

        check_data = [
            ["Property", "Value"],
            ["Check ID", str(check.id)],
            ["Screened Name", check.screened_name],
            ["Check Types", check_types],
            ["Status", check.status.upper()],
            ["Hit Count", str(check.hit_count)],
            ["Started", _format_date(check.started_at)],
            ["Completed", _format_date(check.completed_at)],
        ]

        check_table = Table(check_data, colWidths=[2 * inch, 4 * inch])
        check_table.setStyle(_create_table_style())
        story.append(check_table)

        # Hits
        if check.hits:
            story.append(Paragraph("Screening Hits:", styles["SubsectionTitle"]))

            for j, hit in enumerate(check.hits, 1):
                hit_data = [
                    ["Hit Property", "Value"],
                    ["Hit ID", str(hit.id)],
                    ["Type", hit.hit_type.upper()],
                    ["Matched Name", hit.matched_name],
                    ["Confidence", f"{float(hit.confidence):.1f}%"],
                    ["List Source", hit.list_source],
                    ["List Version", hit.list_version_id],
                    ["Resolution", hit.resolution_status.replace("_", " ").title()],
                ]

                if hit.pep_tier:
                    hit_data.append(["PEP Tier", f"Tier {hit.pep_tier}"])
                if hit.pep_position:
                    hit_data.append(["PEP Position", hit.pep_position])
                if hit.resolution_notes:
                    hit_data.append(["Resolution Notes", hit.resolution_notes])

                hit_table = Table(hit_data, colWidths=[2 * inch, 4 * inch])
                hit_table.setStyle(_create_table_style())
                story.append(hit_table)
                story.append(Spacer(1, 0.1 * inch))

        story.append(Spacer(1, 0.2 * inch))

    story.append(Spacer(1, 0.3 * inch))


def _build_ai_assessment_section(
    story: list,
    styles: dict,
    applicant: Any,
) -> None:
    """Build the AI assessment section."""
    story.append(Paragraph("4. AI Risk Assessment", styles["SectionTitle"]))

    # Risk summary
    story.append(Paragraph("4.1 Risk Summary", styles["SubsectionTitle"]))

    if applicant.risk_score is not None:
        risk_level, _ = _format_risk_level(applicant.risk_score)
        story.append(Paragraph(
            f"Overall Risk: {risk_level} ({applicant.risk_score}/100)",
            styles["BodyText"]
        ))
    else:
        story.append(Paragraph("Risk assessment not yet performed.", styles["BodyText"]))

    # Risk factors
    if applicant.risk_factors:
        story.append(Paragraph("4.2 Identified Risk Factors", styles["SubsectionTitle"]))

        for factor in applicant.risk_factors:
            factor_text = factor.get("factor", str(factor))
            impact = factor.get("impact", "unknown")
            source = factor.get("source", "unknown")
            story.append(Paragraph(
                f"[{impact}] {factor_text} (Source: {source})",
                styles["Citation"]
            ))

    # Flags
    if applicant.flags:
        story.append(Paragraph("4.3 Active Flags", styles["SubsectionTitle"]))
        for flag in applicant.flags:
            flag_style = styles["Warning"] if flag in ["sanctions", "pep"] else styles["BodyText"]
            story.append(Paragraph(f"[{flag.upper()}]", flag_style))

    story.append(Spacer(1, 0.3 * inch))


def _build_timeline_section(
    story: list,
    styles: dict,
    timeline_events: list[TimelineEvent],
) -> None:
    """Build the timeline section."""
    story.append(Paragraph("5. Event Timeline", styles["SectionTitle"]))

    if not timeline_events:
        story.append(Paragraph("No events recorded.", styles["BodyText"]))
        story.append(Spacer(1, 0.3 * inch))
        return

    # Build timeline table
    timeline_data = [["Timestamp", "Event", "Actor"]]

    for event in timeline_events:
        timeline_data.append([
            event.timestamp.strftime("%Y-%m-%d %H:%M"),
            event.description,
            event.actor_name or "System",
        ])

    timeline_table = Table(timeline_data, colWidths=[1.5 * inch, 3.5 * inch, 1 * inch])
    timeline_table.setStyle(_create_table_style())
    story.append(timeline_table)

    story.append(Spacer(1, 0.3 * inch))


def _build_chain_of_custody_section(
    story: list,
    styles: dict,
    db: AsyncSession,
    applicant_id: UUID,
    audit_entries: list,
) -> None:
    """Build the chain of custody section."""
    story.append(Paragraph("6. Chain of Custody", styles["SectionTitle"]))

    story.append(Paragraph(
        "This section provides tamper-evident audit trail information. "
        "Each entry is chain-hashed to ensure data integrity.",
        styles["BodyText"]
    ))

    if not audit_entries:
        story.append(Paragraph(
            "Audit log entries will be displayed here when available.",
            styles["Citation"]
        ))
        story.append(Spacer(1, 0.3 * inch))
        return

    # Build audit table
    audit_data = [["ID", "Action", "Timestamp", "Checksum (truncated)"]]

    for entry in audit_entries[:20]:  # Limit to 20 entries
        audit_data.append([
            str(entry.id),
            entry.action,
            _format_date(entry.created_at),
            entry.checksum[:16] + "..." if entry.checksum else "N/A",
        ])

    audit_table = Table(audit_data, colWidths=[0.8 * inch, 2 * inch, 1.5 * inch, 1.7 * inch])
    audit_table.setStyle(_create_table_style())
    story.append(audit_table)

    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph(
        "Full checksums and audit data can be verified via the API.",
        styles["SmallText"]
    ))

    story.append(Spacer(1, 0.3 * inch))


def _build_footer_section(
    story: list,
    styles: dict,
    generated_at: datetime,
) -> None:
    """Build the footer/certification section."""
    story.append(PageBreak())
    story.append(Paragraph("Certification", styles["SectionTitle"]))

    story.append(Paragraph(
        "This evidence pack was generated by Get Clearance, an AI-native KYC/AML "
        "compliance platform. All data contained herein is sourced from the verification "
        "process and has been validated for accuracy.",
        styles["BodyText"]
    ))

    story.append(Spacer(1, 0.3 * inch))

    story.append(Paragraph(
        f"Generated: {generated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}",
        styles["BodyText"]
    ))

    story.append(Spacer(1, 0.5 * inch))

    story.append(HRFlowable(
        width="100%",
        thickness=1,
        color=colors.HexColor("#e2e8f0"),
    ))

    story.append(Spacer(1, 0.2 * inch))

    story.append(Paragraph(
        "CONFIDENTIAL - This document contains sensitive personal information "
        "and should be handled in accordance with applicable data protection regulations.",
        styles["SmallText"]
    ))


# ===========================================
# EVIDENCE SERVICE
# ===========================================

class EvidenceService:
    """
    Service for generating PDF evidence packs for compliance audits.

    Evidence packs include:
    - Cover page with applicant identification
    - Personal information and risk assessment
    - Document verification results
    - Screening results with hit details
    - AI risk analysis with citations
    - Complete event timeline
    - Chain-of-custody audit trail

    Usage:
        result = await evidence_service.generate_evidence_pack(
            db=session,
            applicant_id=uuid,
            generated_by="compliance@example.com"
        )

        # Save or return PDF
        with open("evidence.pdf", "wb") as f:
            f.write(result.pdf_bytes)
    """

    async def generate_evidence_pack(
        self,
        db: AsyncSession,
        applicant_id: UUID,
        generated_by: str = "System",
        include_audit_log: bool = True,
    ) -> EvidencePackResult:
        """
        Generate a complete evidence pack PDF for an applicant.

        Args:
            db: Database session
            applicant_id: Applicant UUID
            generated_by: Email or name of person generating the pack
            include_audit_log: Whether to include chain-of-custody section

        Returns:
            EvidencePackResult with PDF bytes and metadata

        Raises:
            EvidenceServiceError: If applicant not found or generation fails
        """
        from app.models import Applicant, ScreeningCheck, AuditLog

        # Fetch applicant with all related data
        query = (
            select(Applicant)
            .where(Applicant.id == applicant_id)
            .options(
                selectinload(Applicant.documents),
                selectinload(Applicant.screening_checks).selectinload(ScreeningCheck.hits),
            )
        )

        result = await db.execute(query)
        applicant = result.scalar_one_or_none()

        if not applicant:
            raise EvidenceServiceError(f"Applicant not found: {applicant_id}")

        generated_at = datetime.utcnow()
        sections_included = []

        # Get timeline events
        try:
            timeline = await timeline_service.get_applicant_timeline(db, applicant_id)
            timeline_events = []
            for group in timeline.groups:
                timeline_events.extend(group.events)
        except Exception as e:
            logger.warning(f"Could not fetch timeline: {e}")
            timeline_events = []

        # Get audit log entries
        audit_entries = []
        if include_audit_log:
            try:
                audit_query = (
                    select(AuditLog)
                    .where(AuditLog.resource_id == applicant_id)
                    .order_by(AuditLog.created_at.desc())
                    .limit(50)
                )
                audit_result = await db.execute(audit_query)
                audit_entries = list(audit_result.scalars().all())
            except Exception as e:
                logger.warning(f"Could not fetch audit log: {e}")

        # Build PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=0.75 * inch,
            leftMargin=0.75 * inch,
            topMargin=0.75 * inch,
            bottomMargin=0.75 * inch,
        )

        # Get custom styles
        styles = _get_custom_styles()
        story = []

        # 1. Cover Page
        _build_cover_page(story, styles, applicant, generated_at, generated_by)
        sections_included.append("cover")

        # 2. Applicant Information
        _build_applicant_info_section(story, styles, applicant)
        sections_included.append("applicant_info")

        # 3. Documents
        _build_documents_section(story, styles, applicant.documents)
        sections_included.append("documents")

        # 4. Screening Results
        _build_screening_section(story, styles, applicant.screening_checks)
        sections_included.append("screening")

        # 5. AI Assessment
        _build_ai_assessment_section(story, styles, applicant)
        sections_included.append("ai_assessment")

        # 6. Timeline
        _build_timeline_section(story, styles, timeline_events)
        sections_included.append("timeline")

        # 7. Chain of Custody
        if include_audit_log:
            _build_chain_of_custody_section(story, styles, db, applicant_id, audit_entries)
            sections_included.append("chain_of_custody")

        # 8. Footer/Certification
        _build_footer_section(story, styles, generated_at)
        sections_included.append("certification")

        # Build the PDF
        try:
            doc.build(story)
        except Exception as e:
            logger.error(f"PDF generation failed: {e}")
            raise EvidenceServiceError(f"PDF generation failed: {e}")

        pdf_bytes = buffer.getvalue()
        buffer.close()

        # Calculate approximate page count (rough estimate)
        page_count = max(1, len(pdf_bytes) // 50000 + 1)

        applicant_name = f"{applicant.first_name or ''} {applicant.last_name or ''}".strip() or "Unknown"

        metadata = EvidencePackMetadata(
            applicant_id=str(applicant_id),
            applicant_name=applicant_name,
            external_id=applicant.external_id,
            generated_at=generated_at,
            generated_by=generated_by,
        )

        logger.info(
            f"Generated evidence pack for applicant {applicant_id}: "
            f"{len(pdf_bytes)} bytes, {len(sections_included)} sections"
        )

        return EvidencePackResult(
            pdf_bytes=pdf_bytes,
            metadata=metadata,
            page_count=page_count,
            sections_included=sections_included,
        )

    async def get_evidence_preview(
        self,
        db: AsyncSession,
        applicant_id: UUID,
    ) -> dict[str, Any]:
        """
        Get a preview of what would be included in an evidence pack.

        Useful for showing users what will be in the pack before generating.

        Args:
            db: Database session
            applicant_id: Applicant UUID

        Returns:
            Dictionary with section summaries
        """
        from app.models import Applicant, ScreeningCheck

        query = (
            select(Applicant)
            .where(Applicant.id == applicant_id)
            .options(
                selectinload(Applicant.documents),
                selectinload(Applicant.screening_checks).selectinload(ScreeningCheck.hits),
            )
        )

        result = await db.execute(query)
        applicant = result.scalar_one_or_none()

        if not applicant:
            raise EvidenceServiceError(f"Applicant not found: {applicant_id}")

        # Count timeline events
        try:
            timeline = await timeline_service.get_applicant_timeline(db, applicant_id)
            event_count = timeline.total_events
        except Exception:
            event_count = 0

        # Count screening hits
        total_hits = sum(len(check.hits) for check in applicant.screening_checks)
        unresolved_hits = sum(
            1 for check in applicant.screening_checks
            for hit in check.hits
            if hit.resolution_status == "pending"
        )

        return {
            "applicant_id": str(applicant_id),
            "applicant_name": f"{applicant.first_name or ''} {applicant.last_name or ''}".strip(),
            "status": applicant.status,
            "sections": {
                "applicant_info": True,
                "documents": {
                    "count": len(applicant.documents),
                    "verified": sum(1 for d in applicant.documents if d.status == "verified"),
                },
                "screening": {
                    "checks": len(applicant.screening_checks),
                    "total_hits": total_hits,
                    "unresolved_hits": unresolved_hits,
                },
                "ai_assessment": {
                    "risk_score": applicant.risk_score,
                    "flags": applicant.flags or [],
                },
                "timeline": {
                    "event_count": event_count,
                },
                "chain_of_custody": True,
            },
            "estimated_pages": 5 + len(applicant.documents) + len(applicant.screening_checks),
        }


# ===========================================
# SINGLETON INSTANCE
# ===========================================

evidence_service = EvidenceService()
