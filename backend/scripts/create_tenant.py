#!/usr/bin/env python3
"""
Create a new tenant with admin user.

Usage:
    cd backend
    python -m scripts.create_tenant --name "Acme Corp" --admin-email "admin@acme.com"

Options:
    --name          Tenant organization name (required)
    --admin-email   Admin user email address (required)
    --slug          URL-friendly slug (auto-generated from name if not provided)
    --plan          Subscription plan: starter, growth, enterprise (default: starter)
"""

import argparse
import asyncio
import re
import secrets
import sys
from pathlib import Path
from uuid import uuid4

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.models.tenant import Tenant, User


def generate_api_key() -> str:
    """Generate a secure API key with gc_live_ prefix."""
    return f"gc_live_{secrets.token_urlsafe(32)}"


def slugify(text: str) -> str:
    """Convert text to URL-friendly slug."""
    # Convert to lowercase and replace spaces with hyphens
    slug = text.lower().strip()
    slug = re.sub(r'[^\w\s-]', '', slug)  # Remove non-alphanumeric chars
    slug = re.sub(r'[-\s]+', '-', slug)   # Replace spaces/multiple hyphens with single hyphen
    slug = slug[:63]  # Max length 63 chars
    return slug


async def check_slug_exists(session: AsyncSession, slug: str) -> bool:
    """Check if a tenant with this slug already exists."""
    result = await session.execute(
        select(Tenant).where(Tenant.slug == slug)
    )
    return result.scalar_one_or_none() is not None


async def create_tenant(
    name: str,
    admin_email: str,
    slug: str | None = None,
    plan: str = "starter",
) -> dict:
    """
    Create a new tenant with an admin user.

    Args:
        name: Organization name
        admin_email: Email for the admin user
        slug: URL-friendly identifier (auto-generated if not provided)
        plan: Subscription plan (starter, growth, enterprise)

    Returns:
        dict with tenant_id, api_key, and admin_email

    Raises:
        ValueError: If slug already exists or email is invalid
    """
    # Generate slug if not provided
    if not slug:
        slug = slugify(name)

    # Create async engine and session
    engine = create_async_engine(settings.database_url_async)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        try:
            # Check if slug exists
            if await check_slug_exists(session, slug):
                # Try adding a random suffix
                original_slug = slug
                for _ in range(5):
                    slug = f"{original_slug}-{secrets.token_hex(2)}"
                    if not await check_slug_exists(session, slug):
                        break
                else:
                    raise ValueError(f"Slug '{original_slug}' already exists and couldn't generate unique alternative")

            # Create tenant
            api_key = generate_api_key()
            tenant = Tenant(
                id=uuid4(),
                name=name,
                slug=slug,
                settings={
                    "api_key": api_key,
                    "webhook_url": None,
                    "webhook_secret": None,
                },
                plan=plan,
                status="active",
            )
            session.add(tenant)

            # Create admin user
            user = User(
                id=uuid4(),
                tenant_id=tenant.id,
                email=admin_email,
                name=f"Admin ({admin_email.split('@')[0]})",
                role="admin",
                permissions=[],
                status="active",
            )
            session.add(user)

            await session.commit()

            return {
                "tenant_id": str(tenant.id),
                "slug": tenant.slug,
                "api_key": api_key,
                "admin_email": admin_email,
                "plan": plan,
            }

        except Exception as e:
            await session.rollback()
            raise
        finally:
            await engine.dispose()


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Create a new tenant with admin user",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python -m scripts.create_tenant --name "Acme Corp" --admin-email "admin@acme.com"
    python -m scripts.create_tenant --name "Test Inc" --admin-email "test@test.com" --plan growth
    python -m scripts.create_tenant --name "My Company" --admin-email "me@co.com" --slug my-company
        """
    )
    parser.add_argument(
        "--name",
        required=True,
        help="Tenant organization name"
    )
    parser.add_argument(
        "--admin-email",
        required=True,
        help="Admin user email address"
    )
    parser.add_argument(
        "--slug",
        help="URL-friendly slug (auto-generated from name if not provided)"
    )
    parser.add_argument(
        "--plan",
        choices=["starter", "growth", "enterprise"],
        default="starter",
        help="Subscription plan (default: starter)"
    )

    args = parser.parse_args()

    # Basic email validation
    if "@" not in args.admin_email or "." not in args.admin_email:
        print("Error: Invalid email address format")
        sys.exit(1)

    try:
        result = asyncio.run(create_tenant(
            name=args.name,
            admin_email=args.admin_email,
            slug=args.slug,
            plan=args.plan,
        ))

        print("\n" + "=" * 50)
        print("Tenant created successfully!")
        print("=" * 50)
        print(f"Tenant ID:  {result['tenant_id']}")
        print(f"Slug:       {result['slug']}")
        print(f"API Key:    {result['api_key']}")
        print(f"Admin User: {result['admin_email']}")
        print(f"Plan:       {result['plan']}")
        print("=" * 50)
        print("\nSave the API key - it cannot be retrieved later!")
        print()

    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error creating tenant: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
