"""
Get Clearance - Storage Service Tests
======================================
Unit tests for Cloudflare R2 document storage service.

Tests:
- Service configuration validation
- Storage key generation and sanitization
- Error handling for unconfigured service
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.services.storage import (
    StorageService,
    StorageConfigError,
)


# Helper to create a configured storage service for tests
def create_storage_service(**kwargs):
    """Create a StorageService with test credentials."""
    defaults = {
        "access_key_id": "test-key",
        "secret_access_key": "test-secret",
        "endpoint": "https://test.r2.cloudflarestorage.com",
        "bucket": "test-bucket",
        "upload_expires": 3600,
        "download_expires": 3600,
    }
    defaults.update(kwargs)
    return StorageService(**defaults)


def create_unconfigured_storage_service(**overrides):
    """Create a StorageService that is explicitly not configured.

    We bypass the constructor's 'or' fallback logic by directly setting attributes.
    """
    service = StorageService.__new__(StorageService)
    service.access_key_id = overrides.get("access_key_id", "")
    service.secret_access_key = overrides.get("secret_access_key", "test-secret")
    service.endpoint = overrides.get("endpoint", "https://test.r2.cloudflarestorage.com")
    service.bucket = overrides.get("bucket", "test-bucket")
    service.upload_expires = 3600
    service.download_expires = 3600
    service._session = None
    return service


# ===========================================
# STORAGE SERVICE INITIALIZATION
# ===========================================

class TestStorageServiceInit:
    """Test storage service initialization and configuration."""

    def test_is_configured_with_all_credentials(self):
        """Service is configured when all credentials provided."""
        service = create_storage_service()
        assert service.is_configured is True

    def test_is_not_configured_missing_key(self):
        """Service is not configured without access key."""
        service = create_unconfigured_storage_service(access_key_id="")
        assert service.is_configured is False

    def test_is_not_configured_missing_secret(self):
        """Service is not configured without secret key."""
        service = create_unconfigured_storage_service(secret_access_key="")
        assert service.is_configured is False

    def test_is_not_configured_missing_endpoint(self):
        """Service is not configured without endpoint."""
        service = create_unconfigured_storage_service(
            access_key_id="test-key",
            endpoint=""
        )
        assert service.is_configured is False

    def test_is_not_configured_missing_bucket(self):
        """Service is not configured without bucket."""
        service = create_unconfigured_storage_service(
            access_key_id="test-key",
            bucket=""
        )
        assert service.is_configured is False

    def test_custom_expiration_times(self):
        """Service accepts custom expiration times."""
        service = create_storage_service(upload_expires=7200, download_expires=1800)
        assert service.upload_expires == 7200
        assert service.download_expires == 1800


# ===========================================
# STORAGE KEY GENERATION
# ===========================================

class TestStorageKeyGeneration:
    """Test storage key/path generation."""

    def test_generate_key_basic(self):
        """Generate basic storage key."""
        service = create_storage_service()
        tenant_id = uuid4()
        entity_id = uuid4()

        key = service.generate_storage_key(
            tenant_id=tenant_id,
            entity_type="applicants",
            entity_id=entity_id,
            filename="passport.jpg",
        )

        assert str(tenant_id) in key
        assert "applicants" in key
        assert str(entity_id) in key
        assert "passport.jpg" in key

    def test_generate_key_with_timestamp(self):
        """Generated key includes timestamp."""
        service = create_storage_service()
        tenant_id = uuid4()
        entity_id = uuid4()

        key = service.generate_storage_key(
            tenant_id=tenant_id,
            entity_type="documents",
            entity_id=entity_id,
            filename="test.pdf",
        )

        # Should have format: {tenant}/{type}/{entity}/{timestamp}_{filename}
        parts = key.split("/")
        assert len(parts) == 4
        # Last part should have timestamp prefix
        assert "_test.pdf" in parts[-1]

    def test_generate_key_sanitizes_filename(self):
        """Filename is sanitized to remove unsafe characters."""
        service = create_storage_service()
        tenant_id = uuid4()
        entity_id = uuid4()

        key = service.generate_storage_key(
            tenant_id=tenant_id,
            entity_type="applicants",
            entity_id=entity_id,
            filename="passport (1) copy!@#$.jpg",
        )

        # Should only contain alphanumeric, dots, underscores, hyphens
        filename_part = key.split("/")[-1]
        assert "!" not in filename_part
        assert "@" not in filename_part
        assert "#" not in filename_part
        assert "$" not in filename_part
        assert "(" not in filename_part
        assert ")" not in filename_part
        assert " " not in filename_part

    def test_generate_key_preserves_extension(self):
        """File extension is preserved."""
        service = create_storage_service()
        tenant_id = uuid4()
        entity_id = uuid4()

        key = service.generate_storage_key(
            tenant_id=tenant_id,
            entity_type="applicants",
            entity_id=entity_id,
            filename="document.pdf",
        )

        assert key.endswith(".pdf")

    def test_generate_key_with_uuid_strings(self):
        """UUIDs can be passed as strings."""
        service = create_storage_service()
        tenant_id = "12345678-1234-5678-1234-567812345678"
        entity_id = "87654321-4321-8765-4321-876543218765"

        key = service.generate_storage_key(
            tenant_id=tenant_id,
            entity_type="applicants",
            entity_id=entity_id,
            filename="test.jpg",
        )

        assert tenant_id in key
        assert entity_id in key


# ===========================================
# UNCONFIGURED SERVICE ERRORS
# ===========================================

class TestUnconfiguredServiceErrors:
    """Test that unconfigured service raises appropriate errors."""

    @pytest.mark.asyncio
    async def test_create_presigned_upload_not_configured(self):
        """Upload fails when not configured."""
        service = create_unconfigured_storage_service(access_key_id="")

        with pytest.raises(StorageConfigError) as exc_info:
            await service.create_presigned_upload(key="test", content_type="image/jpeg")

        assert "not configured" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_presigned_download_not_configured(self):
        """Download fails when not configured."""
        service = create_unconfigured_storage_service(access_key_id="")

        with pytest.raises(StorageConfigError):
            await service.create_presigned_download(key="test")

    @pytest.mark.asyncio
    async def test_object_exists_not_configured(self):
        """Exists check fails when not configured."""
        service = create_unconfigured_storage_service(access_key_id="")

        with pytest.raises(StorageConfigError):
            await service.object_exists(key="test")

    @pytest.mark.asyncio
    async def test_delete_not_configured(self):
        """Delete fails when not configured."""
        service = create_unconfigured_storage_service(access_key_id="")

        with pytest.raises(StorageConfigError):
            await service.delete(key="test")

    @pytest.mark.asyncio
    async def test_get_object_metadata_not_configured(self):
        """Metadata retrieval fails when not configured."""
        service = create_unconfigured_storage_service(access_key_id="")

        with pytest.raises(StorageConfigError):
            await service.get_object_metadata(key="test")

    @pytest.mark.asyncio
    async def test_copy_not_configured(self):
        """Copy fails when not configured."""
        service = create_unconfigured_storage_service(access_key_id="")

        with pytest.raises(StorageConfigError):
            await service.copy(source_key="a", dest_key="b")

    @pytest.mark.asyncio
    async def test_delete_prefix_not_configured(self):
        """Delete prefix fails when not configured."""
        service = create_unconfigured_storage_service(access_key_id="")

        with pytest.raises(StorageConfigError):
            await service.delete_prefix(prefix="test/")

    @pytest.mark.asyncio
    async def test_create_presigned_upload_put_not_configured(self):
        """PUT upload fails when not configured."""
        service = create_unconfigured_storage_service(access_key_id="")

        with pytest.raises(StorageConfigError):
            await service.create_presigned_upload_put(key="test", content_type="image/jpeg")
