"""
Get Clearance - Model Base Classes
===================================
Common mixins and base classes for all SQLAlchemy models.
"""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, declared_attr


class TimestampMixin:
    """Mixin that adds created_at and updated_at timestamps."""
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class UUIDMixin:
    """Mixin that adds UUID primary key."""
    
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )


class TenantMixin:
    """Mixin that adds tenant_id for multi-tenancy."""
    
    tenant_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=False,
        index=True,
    )


class SoftDeleteMixin:
    """Mixin for soft delete pattern."""
    
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )
    
    @property
    def is_deleted(self) -> bool:
        """Check if record is soft-deleted."""
        return self.deleted_at is not None


def generate_table_name(cls: type) -> str:
    """
    Generate table name from class name.
    
    Converts CamelCase to snake_case and pluralizes.
    Example: ApplicantStep -> applicant_steps
    """
    import re
    name = re.sub(r'(?<!^)(?=[A-Z])', '_', cls.__name__).lower()
    # Simple pluralization
    if name.endswith('y'):
        return name[:-1] + 'ies'
    elif name.endswith('s'):
        return name + 'es'
    else:
        return name + 's'
