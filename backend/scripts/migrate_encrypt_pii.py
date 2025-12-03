#!/usr/bin/env python3
"""
PII Encryption Migration Script
===============================
One-time migration to encrypt existing plaintext PII data.

Run ONCE after deploying the encryption feature and running the schema migration.

Usage:
    # From backend directory
    python -m scripts.migrate_encrypt_pii

    # Dry run (no changes)
    python -m scripts.migrate_encrypt_pii --dry-run

    # Batch size
    python -m scripts.migrate_encrypt_pii --batch-size 100

What this script does:
1. Finds all applicants with plaintext (unencrypted) PII
2. Encrypts email, phone, first_name, last_name
3. Generates email_hash for searchable lookups
4. Commits in batches for large datasets

Safety features:
- Detects already-encrypted data (Fernet tokens start with 'gAAAAA')
- Commits in batches to avoid long transactions
- Dry-run mode for testing
- Progress reporting
"""

import argparse
import asyncio
import hashlib
import sys
from pathlib import Path

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_maker
from app.services.encryption import encrypt_pii, is_encrypted


FERNET_PREFIX = "gAAAAA"


async def count_applicants(db: AsyncSession) -> tuple[int, int]:
    """Count total applicants and those needing migration."""
    # Import here to avoid circular imports
    from app.models.applicant import Applicant

    total_result = await db.execute(select(func.count(Applicant.id)))
    total = total_result.scalar() or 0

    # Count those with plaintext email (not starting with Fernet prefix)
    # This is an approximation - we check more thoroughly per-record
    plaintext_result = await db.execute(
        select(func.count(Applicant.id)).where(
            Applicant.email.isnot(None),
            ~Applicant.email.startswith(FERNET_PREFIX)
        )
    )
    plaintext = plaintext_result.scalar() or 0

    return total, plaintext


async def migrate_batch(
    db: AsyncSession,
    offset: int,
    batch_size: int,
    dry_run: bool = False
) -> tuple[int, int]:
    """
    Migrate a batch of applicants.

    Returns:
        Tuple of (processed, migrated) counts
    """
    from app.models.applicant import Applicant

    # Fetch batch
    result = await db.execute(
        select(Applicant)
        .order_by(Applicant.created_at)
        .offset(offset)
        .limit(batch_size)
    )
    applicants = result.scalars().all()

    processed = 0
    migrated = 0

    for applicant in applicants:
        processed += 1
        needs_migration = False

        # Check and encrypt each PII field
        if applicant.email and not is_encrypted(applicant.email):
            if not dry_run:
                # Set email and hash together
                applicant.set_email(applicant.email)
            needs_migration = True

        if applicant.phone and not is_encrypted(applicant.phone):
            if not dry_run:
                applicant.phone = encrypt_pii(applicant.phone)
            needs_migration = True

        if applicant.first_name and not is_encrypted(applicant.first_name):
            if not dry_run:
                applicant.first_name = encrypt_pii(applicant.first_name)
            needs_migration = True

        if applicant.last_name and not is_encrypted(applicant.last_name):
            if not dry_run:
                applicant.last_name = encrypt_pii(applicant.last_name)
            needs_migration = True

        # Populate email_hash if missing but email exists
        if applicant.email and not applicant.email_hash and not dry_run:
            # Decrypt to get plaintext for hashing (might already be encrypted now)
            from app.services.encryption import decrypt_pii
            plaintext_email = decrypt_pii(applicant.email)
            if plaintext_email:
                applicant.email_hash = hashlib.sha256(
                    plaintext_email.lower().encode()
                ).hexdigest()
            needs_migration = True

        if needs_migration:
            migrated += 1

    if not dry_run:
        await db.commit()

    return processed, migrated


async def migrate_all_pii(batch_size: int = 100, dry_run: bool = False) -> None:
    """
    Migrate all plaintext PII to encrypted format.

    Args:
        batch_size: Number of records to process per batch
        dry_run: If True, don't make any changes
    """
    print("PII Encryption Migration")
    print("=" * 50)

    if dry_run:
        print("DRY RUN MODE - No changes will be made")
        print()

    async with async_session_maker() as db:
        # Get counts
        total, estimated_plaintext = await count_applicants(db)
        print(f"Total applicants: {total}")
        print(f"Estimated needing migration: {estimated_plaintext}")
        print()

        if total == 0:
            print("No applicants to migrate.")
            return

        # Process in batches
        offset = 0
        total_processed = 0
        total_migrated = 0

        while offset < total:
            processed, migrated = await migrate_batch(
                db, offset, batch_size, dry_run
            )

            total_processed += processed
            total_migrated += migrated

            progress = (offset + processed) / total * 100
            print(f"Progress: {offset + processed}/{total} ({progress:.1f}%) - "
                  f"Migrated this batch: {migrated}")

            offset += batch_size

            if processed == 0:
                break

    print()
    print("=" * 50)
    print(f"Migration {'simulation' if dry_run else 'complete'}!")
    print(f"Total processed: {total_processed}")
    print(f"Total migrated: {total_migrated}")

    if dry_run:
        print()
        print("Run without --dry-run to apply changes.")


def main():
    parser = argparse.ArgumentParser(
        description="Migrate existing plaintext PII to encrypted format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate migration without making changes",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Number of records to process per batch (default: 100)",
    )

    args = parser.parse_args()

    asyncio.run(migrate_all_pii(
        batch_size=args.batch_size,
        dry_run=args.dry_run,
    ))


if __name__ == "__main__":
    main()
