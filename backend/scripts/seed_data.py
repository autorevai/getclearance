#!/usr/bin/env python3
"""
Seed test data for development/staging environments.

Usage:
    cd backend
    python -m scripts.seed_data --tenant-id <uuid>
    python -m scripts.seed_data --create-tenant  # Creates new demo tenant first

Options:
    --tenant-id     UUID of existing tenant to seed data into
    --create-tenant Create a new demo tenant and seed data into it
    --count         Number of applicants to create (default: 10)
    --clear         Clear existing data before seeding (use with caution!)
"""

import argparse
import asyncio
import random
import secrets
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID, uuid4

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.models.tenant import Tenant, User
from app.models.applicant import Applicant, ApplicantStep
from app.models.document import Document
from app.models.screening import ScreeningList, ScreeningCheck, ScreeningHit
from app.models.case import Case, CaseNote


# Sample data for generating realistic test records
FIRST_NAMES = [
    "James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda",
    "William", "Elizabeth", "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica",
    "Thomas", "Sarah", "Charles", "Karen", "Christopher", "Lisa", "Daniel", "Nancy",
    "Ahmed", "Fatima", "Mohammed", "Aisha", "Wei", "Mei", "Raj", "Priya",
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
    "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson",
    "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker",
    "Chen", "Wang", "Singh", "Kumar", "Patel", "Kim", "Park", "Nguyen",
]

COUNTRIES = ["USA", "GBR", "CAN", "AUS", "DEU", "FRA", "JPN", "SGP", "UAE", "BRA"]

APPLICANT_STATUSES = ["pending", "in_progress", "review", "approved", "rejected"]
STATUS_WEIGHTS = [0.1, 0.15, 0.15, 0.45, 0.15]  # Most end up approved

DOCUMENT_TYPES = ["passport", "drivers_license", "national_id", "utility_bill", "bank_statement"]
DOCUMENT_STATUSES = ["pending", "processing", "verified", "rejected"]

CHECK_TYPES = ["sanctions", "pep", "adverse_media"]

HIT_TYPES = ["sanctions", "pep", "adverse_media"]

CASE_TYPES = ["sanctions_hit", "pep_hit", "fraud_suspected", "manual_review"]
CASE_PRIORITIES = ["low", "medium", "high", "critical"]


def random_date(start_year: int = 1960, end_year: int = 2000) -> date:
    """Generate a random date of birth."""
    year = random.randint(start_year, end_year)
    month = random.randint(1, 12)
    day = random.randint(1, 28)  # Safe for all months
    return date(year, month, day)


def random_datetime(days_ago_max: int = 30) -> datetime:
    """Generate a random datetime within the last N days."""
    days = random.randint(0, days_ago_max)
    hours = random.randint(0, 23)
    minutes = random.randint(0, 59)
    return datetime.now(timezone.utc) - timedelta(days=days, hours=hours, minutes=minutes)


def generate_applicant(tenant_id: UUID, index: int) -> Applicant:
    """Generate a realistic test applicant."""
    first_name = random.choice(FIRST_NAMES)
    last_name = random.choice(LAST_NAMES)
    status = random.choices(APPLICANT_STATUSES, weights=STATUS_WEIGHTS)[0]

    # Risk score based on status
    if status == "rejected":
        risk_score = random.randint(70, 100)
    elif status == "review":
        risk_score = random.randint(50, 80)
    elif status == "approved":
        risk_score = random.randint(0, 40)
    else:
        risk_score = random.randint(0, 60)

    # Flags based on risk
    flags = []
    if risk_score > 60:
        if random.random() > 0.5:
            flags.append("pep")
        if random.random() > 0.7:
            flags.append("sanctions")
        if random.random() > 0.6:
            flags.append("adverse_media")
    if random.random() > 0.9:
        flags.append("high_risk_country")

    created_at = random_datetime(days_ago_max=60)
    submitted_at = created_at + timedelta(hours=random.randint(0, 24)) if status != "pending" else None
    reviewed_at = submitted_at + timedelta(hours=random.randint(1, 48)) if status in ["approved", "rejected"] else None

    return Applicant(
        id=uuid4(),
        tenant_id=tenant_id,
        external_id=f"ext_{secrets.token_hex(8)}",
        email=f"{first_name.lower()}.{last_name.lower()}{random.randint(1, 99)}@example.com",
        phone=f"+1{random.randint(2000000000, 9999999999)}",
        first_name=first_name,
        last_name=last_name,
        date_of_birth=random_date(),
        nationality=random.choice(COUNTRIES),
        country_of_residence=random.choice(COUNTRIES),
        address={
            "street": f"{random.randint(1, 9999)} {random.choice(['Main', 'Oak', 'Pine', 'Elm', 'Market'])} Street",
            "city": random.choice(["New York", "Los Angeles", "London", "Toronto", "Sydney", "Berlin"]),
            "state": random.choice(["NY", "CA", "ON", "NSW", "BE"]),
            "postal_code": f"{random.randint(10000, 99999)}",
            "country": random.choice(COUNTRIES),
        },
        status=status,
        risk_score=risk_score,
        risk_factors=[
            {"factor": "country_risk", "impact": random.randint(1, 30), "source": "geo_analysis"},
            {"factor": "name_screening", "impact": random.randint(0, 20), "source": "aml_check"},
        ] if risk_score > 30 else [],
        flags=flags,
        source=random.choice(["api", "web", "mobile", "sdk"]),
        created_at=created_at,
        submitted_at=submitted_at,
        reviewed_at=reviewed_at,
        sla_due_at=created_at + timedelta(days=7) if status in ["pending", "in_progress", "review"] else None,
    )


def generate_document(tenant_id: UUID, applicant_id: UUID) -> Document:
    """Generate a test document for an applicant."""
    doc_type = random.choice(DOCUMENT_TYPES)
    status = random.choice(DOCUMENT_STATUSES)

    return Document(
        id=uuid4(),
        tenant_id=tenant_id,
        applicant_id=applicant_id,
        type=doc_type,
        file_name=f"{doc_type}_{secrets.token_hex(4)}.pdf",
        file_size=random.randint(100000, 5000000),
        mime_type="application/pdf",
        storage_path=f"{tenant_id}/applicants/{applicant_id}/{uuid4()}.pdf",
        status=status,
        ocr_text="[Sample OCR text for testing]" if status == "verified" else None,
        ocr_confidence=random.uniform(0.85, 0.99) if status == "verified" else None,
        extracted_data={
            "document_number": f"{secrets.token_hex(4).upper()}",
            "expiry_date": str(date.today() + timedelta(days=random.randint(365, 3650))),
            "issuing_country": random.choice(COUNTRIES),
        } if status == "verified" else None,
        verification_checks=[
            {"check": "mrz_validation", "passed": True, "confidence": 0.95},
            {"check": "face_match", "passed": True, "confidence": 0.92},
        ] if status == "verified" else [],
        fraud_signals=[
            {"signal": "digital_tampering_suspected", "severity": "medium", "details": "Metadata inconsistency"}
        ] if status == "rejected" else [],
        uploaded_at=random_datetime(days_ago_max=30),
        processed_at=random_datetime(days_ago_max=29) if status != "pending" else None,
    )


def generate_screening_list() -> ScreeningList:
    """Generate a screening list version record."""
    return ScreeningList(
        id=uuid4(),
        source="opensanctions",
        version_id=f"OS-{date.today().strftime('%Y%m%d')}-001",
        list_type="combined",
        entity_count=random.randint(50000, 100000),
        published_at=datetime.now(timezone.utc) - timedelta(days=1),
        fetched_at=datetime.now(timezone.utc),
        checksum=secrets.token_hex(32),
    )


def generate_screening_check(
    tenant_id: UUID,
    applicant: Applicant,
    screening_list: ScreeningList,
) -> tuple[ScreeningCheck, list[ScreeningHit]]:
    """Generate a screening check with potential hits."""
    has_hits = "pep" in applicant.flags or "sanctions" in applicant.flags or "adverse_media" in applicant.flags

    check = ScreeningCheck(
        id=uuid4(),
        tenant_id=tenant_id,
        applicant_id=applicant.id,
        entity_type="individual",
        screened_name=applicant.full_name,
        screened_dob=applicant.date_of_birth,
        screened_country=applicant.nationality,
        check_types=["sanctions", "pep", "adverse_media"],
        status="hit" if has_hits else "clear",
        hit_count=random.randint(1, 3) if has_hits else 0,
        started_at=random_datetime(days_ago_max=30),
        completed_at=random_datetime(days_ago_max=29),
    )

    hits = []
    if has_hits:
        for flag in applicant.flags:
            if flag in HIT_TYPES:
                hit = ScreeningHit(
                    id=uuid4(),
                    check_id=check.id,
                    list_id=screening_list.id,
                    list_source=screening_list.source,
                    list_version_id=screening_list.version_id,
                    hit_type=flag,
                    matched_entity_id=f"os-{secrets.token_hex(8)}",
                    matched_name=f"{random.choice(FIRST_NAMES)} {applicant.last_name}",  # Similar name
                    confidence=random.uniform(60, 95),
                    matched_fields=["name", "dob"] if random.random() > 0.5 else ["name"],
                    match_data={
                        "source_url": "https://opensanctions.org/entities/example",
                        "aliases": [f"{applicant.first_name} {applicant.last_name}"],
                    },
                    pep_tier=random.randint(1, 4) if flag == "pep" else None,
                    pep_position="Government Official" if flag == "pep" else None,
                    pep_relationship=random.choice(["direct", "family", "associate"]) if flag == "pep" else None,
                    match_type=random.choice(["true_positive", "potential_match", "false_positive"]),
                    resolution_status=random.choice(["pending", "confirmed_true", "confirmed_false"]),
                    created_at=check.completed_at,
                )
                hits.append(hit)

    return check, hits


def generate_case(
    tenant_id: UUID,
    applicant: Applicant,
    user_id: UUID | None,
    case_counter: int,
) -> tuple[Case, list[CaseNote]]:
    """Generate a case for investigation."""
    case_type = random.choice(CASE_TYPES)
    priority = random.choice(CASE_PRIORITIES)
    status = random.choice(["open", "in_progress", "resolved", "closed"])

    # Generate case number (e.g., CASE-2025-001)
    case_number = f"CASE-2025-{case_counter:03d}"
    created_at = random_datetime(days_ago_max=14)

    case = Case(
        id=uuid4(),
        tenant_id=tenant_id,
        applicant_id=applicant.id,
        case_number=case_number,
        type=case_type.replace("_hit", "").replace("_suspected", ""),  # Map to valid types: sanctions, pep, fraud, manual_review -> verification
        title=f"{case_type.replace('_', ' ').title()} - {applicant.full_name}",
        description=f"Auto-generated case for {case_type}",
        priority=priority,
        status=status,
        assignee_id=user_id if status in ["in_progress", "resolved"] else None,
        source="screening_hit" if "hit" in case_type else "manual",
        opened_at=created_at,
        resolved_at=random_datetime(days_ago_max=7) if status in ["resolved", "closed"] else None,
    )

    notes = []
    if status in ["in_progress", "resolved", "closed"]:
        note = CaseNote(
            id=uuid4(),
            case_id=case.id,
            author_id=user_id,
            content=f"Investigation note: Reviewed {case_type} alert. " +
                    ("Confirmed as legitimate concern." if status == "resolved" else "Monitoring situation."),
            created_at=created_at + timedelta(hours=random.randint(1, 24)),
        )
        notes.append(note)

    return case, notes


async def create_demo_tenant(session: AsyncSession) -> tuple[UUID, UUID]:
    """Create a demo tenant and return (tenant_id, user_id)."""
    tenant = Tenant(
        id=uuid4(),
        name="Demo Company",
        slug=f"demo-{secrets.token_hex(4)}",
        settings={
            "api_key": f"gc_live_{secrets.token_urlsafe(32)}",
            "webhook_url": None,
        },
        plan="growth",
        status="active",
    )
    session.add(tenant)

    user = User(
        id=uuid4(),
        tenant_id=tenant.id,
        email="demo@getclearance.ai",
        name="Demo Admin",
        role="admin",
        status="active",
    )
    session.add(user)

    await session.flush()
    return tenant.id, user.id


async def clear_tenant_data(session: AsyncSession, tenant_id: UUID) -> None:
    """Clear existing data for a tenant (except tenant and users)."""
    # Delete in correct order due to foreign keys
    await session.execute(delete(CaseNote).where(
        CaseNote.case_id.in_(select(Case.id).where(Case.tenant_id == tenant_id))
    ))
    await session.execute(delete(Case).where(Case.tenant_id == tenant_id))
    await session.execute(delete(ScreeningHit).where(
        ScreeningHit.check_id.in_(select(ScreeningCheck.id).where(ScreeningCheck.tenant_id == tenant_id))
    ))
    await session.execute(delete(ScreeningCheck).where(ScreeningCheck.tenant_id == tenant_id))
    await session.execute(delete(Document).where(Document.tenant_id == tenant_id))
    await session.execute(delete(ApplicantStep).where(
        ApplicantStep.applicant_id.in_(select(Applicant.id).where(Applicant.tenant_id == tenant_id))
    ))
    await session.execute(delete(Applicant).where(Applicant.tenant_id == tenant_id))


async def seed_data(
    tenant_id: UUID | None = None,
    create_tenant: bool = False,
    count: int = 10,
    clear: bool = False,
) -> dict:
    """
    Seed test data into the database.

    Args:
        tenant_id: UUID of existing tenant (if not creating new)
        create_tenant: Whether to create a new demo tenant
        count: Number of applicants to create
        clear: Whether to clear existing data first

    Returns:
        dict with counts of created records
    """
    engine = create_async_engine(settings.database_url_async)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        try:
            user_id = None

            # Create or verify tenant
            if create_tenant:
                tenant_id, user_id = await create_demo_tenant(session)
                print(f"Created demo tenant: {tenant_id}")
            else:
                # Verify tenant exists
                result = await session.execute(
                    select(Tenant).where(Tenant.id == tenant_id)
                )
                tenant = result.scalar_one_or_none()
                if not tenant:
                    raise ValueError(f"Tenant {tenant_id} not found")

                # Get a user for assignments
                result = await session.execute(
                    select(User).where(User.tenant_id == tenant_id).limit(1)
                )
                user = result.scalar_one_or_none()
                user_id = user.id if user else None

            # Clear existing data if requested
            if clear and tenant_id:
                print("Clearing existing data...")
                await clear_tenant_data(session, tenant_id)

            # Create screening list (shared)
            screening_list = generate_screening_list()
            session.add(screening_list)

            # Track counts
            counts = {
                "applicants": 0,
                "documents": 0,
                "screening_checks": 0,
                "screening_hits": 0,
                "cases": 0,
                "case_notes": 0,
            }
            case_counter = 1

            # Create applicants with related data
            for i in range(count):
                applicant = generate_applicant(tenant_id, i)
                session.add(applicant)
                counts["applicants"] += 1

                # Add 1-3 documents per applicant
                for _ in range(random.randint(1, 3)):
                    doc = generate_document(tenant_id, applicant.id)
                    session.add(doc)
                    counts["documents"] += 1

                # Add screening check
                check, hits = generate_screening_check(tenant_id, applicant, screening_list)
                session.add(check)
                counts["screening_checks"] += 1
                for hit in hits:
                    session.add(hit)
                    counts["screening_hits"] += 1

                # Add case for high-risk applicants (30% chance)
                if applicant.risk_score and applicant.risk_score > 50 and random.random() > 0.7:
                    case, notes = generate_case(tenant_id, applicant, user_id, case_counter)
                    case_counter += 1
                    session.add(case)
                    counts["cases"] += 1
                    for note in notes:
                        session.add(note)
                        counts["case_notes"] += 1

            await session.commit()

            return {
                "tenant_id": str(tenant_id),
                "counts": counts,
            }

        except Exception as e:
            await session.rollback()
            raise
        finally:
            await engine.dispose()


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Seed test data for development/staging",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python -m scripts.seed_data --create-tenant
    python -m scripts.seed_data --tenant-id 550e8400-e29b-41d4-a716-446655440000
    python -m scripts.seed_data --create-tenant --count 50
    python -m scripts.seed_data --tenant-id <uuid> --clear --count 20
        """
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--tenant-id",
        type=UUID,
        help="UUID of existing tenant to seed data into"
    )
    group.add_argument(
        "--create-tenant",
        action="store_true",
        help="Create a new demo tenant first"
    )

    parser.add_argument(
        "--count",
        type=int,
        default=10,
        help="Number of applicants to create (default: 10)"
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear existing data before seeding (use with caution!)"
    )

    args = parser.parse_args()

    if args.clear and not args.create_tenant:
        confirm = input("WARNING: This will delete existing data. Continue? [y/N] ")
        if confirm.lower() != 'y':
            print("Aborted.")
            sys.exit(0)

    try:
        result = asyncio.run(seed_data(
            tenant_id=args.tenant_id,
            create_tenant=args.create_tenant,
            count=args.count,
            clear=args.clear,
        ))

        print("\n" + "=" * 50)
        print("Test data seeded successfully!")
        print("=" * 50)
        print(f"Tenant ID: {result['tenant_id']}")
        print("\nRecords created:")
        for key, value in result["counts"].items():
            print(f"  {key}: {value}")
        print("=" * 50 + "\n")

    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error seeding data: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
