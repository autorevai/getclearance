#!/usr/bin/env python3
"""
Create Pax Markets tenant and seed data.

Usage:
    cd backend
    python -m scripts.create_pax_tenant

    # For Railway production:
    DATABASE_URL="postgresql+asyncpg://postgres:PASSWORD@HOST:PORT/railway" python -m scripts.create_pax_tenant
"""

import asyncio
import os
import secrets
import sys
from pathlib import Path
from uuid import uuid4

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Allow DATABASE_URL override for production
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    from app.config import settings
    DATABASE_URL = settings.database_url_async
elif "+asyncpg" not in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

from app.models.tenant import Tenant, User


async def create_pax_tenant():
    """Create Pax Markets tenant with admin user."""
    print(f"Connecting to database...")
    engine = create_async_engine(DATABASE_URL)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        try:
            # Check if tenant already exists
            result = await session.execute(
                select(Tenant).where(Tenant.slug == "pax-markets")
            )
            existing = result.scalar_one_or_none()

            if existing:
                print(f"Tenant 'pax-markets' already exists with ID: {existing.id}")

                # Check for user
                result = await session.execute(
                    select(User).where(
                        User.tenant_id == existing.id,
                        User.email == "chris.diyanni@gmail.com"
                    )
                )
                user = result.scalar_one_or_none()
                if user:
                    print(f"User already exists with ID: {user.id}")
                    return str(existing.id), str(user.id)

                # Create user if not exists
                user = User(
                    id=uuid4(),
                    tenant_id=existing.id,
                    auth0_id="auth0|6839a5c4cc91adc9a5757f1b",  # Chris's Auth0 ID
                    email="chris.diyanni@gmail.com",
                    name="Chris DiYanni",
                    role="admin",
                    permissions=[
                        "read:applicants",
                        "write:applicants",
                        "delete:applicants",
                        "read:documents",
                        "write:documents",
                        "read:screening",
                        "write:screening",
                        "read:cases",
                        "write:cases",
                        "read:settings",
                        "write:settings",
                        "admin:*",
                    ],
                    status="active",
                )
                session.add(user)
                await session.commit()
                print(f"Created user: {user.id}")
                return str(existing.id), str(user.id)

            # Create Pax Markets tenant
            tenant = Tenant(
                id=uuid4(),
                name="Pax Markets",
                slug="pax-markets",
                settings={
                    "api_key": f"gc_live_{secrets.token_urlsafe(32)}",
                    "webhook_url": None,
                    "domain": "https://pax.markets",
                },
                plan="growth",
                status="active",
            )
            session.add(tenant)

            # Create admin user
            user = User(
                id=uuid4(),
                tenant_id=tenant.id,
                auth0_id="auth0|6839a5c4cc91adc9a5757f1b",  # Chris's Auth0 ID - update if needed
                email="chris.diyanni@gmail.com",
                name="Chris DiYanni",
                role="admin",
                permissions=[
                    "read:applicants",
                    "write:applicants",
                    "delete:applicants",
                    "read:documents",
                    "write:documents",
                    "read:screening",
                    "write:screening",
                    "read:cases",
                    "write:cases",
                    "read:settings",
                    "write:settings",
                    "admin:*",
                ],
                status="active",
            )
            session.add(user)

            await session.commit()

            print("=" * 60)
            print("Pax Markets Tenant Created!")
            print("=" * 60)
            print(f"Tenant ID: {tenant.id}")
            print(f"Tenant Slug: {tenant.slug}")
            print(f"User ID: {user.id}")
            print(f"User Email: {user.email}")
            print("=" * 60)

            return str(tenant.id), str(user.id)

        except Exception as e:
            await session.rollback()
            print(f"Error: {e}")
            raise
        finally:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(create_pax_tenant())
