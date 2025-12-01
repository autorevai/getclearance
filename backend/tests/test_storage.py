"""
Get Clearance - Storage Service Tests
======================================
Unit tests for Cloudflare R2 document storage service.

Tests:
- Presigned URL generation (upload and download)
- Storage key generation and sanitization
- Object operations (exists, metadata, delete)
- Error handling
- Configuration validation
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4, UUID

from botocore.exceptions import ClientError

from app.services.storage import (
    StorageService,
    StorageServiceError,
    StorageConfigError,
    StorageUploadError,
    StorageDownloadError,
)


# ===========================================
# STORAGE SERVICE INITIALIZATION
# ===========================================

class TestStorageServiceInit:
    """Test storage service initialization and configuration."""

    def test_is_configured_with_all_credentials(self):
        """Service is configured when all credentials provided."""
        service = StorageService(
            access_key_id="test-key",
            secret_access_key="test-secret",
            endpoint="https://test.r2.cloudflarestorage.com",
            bucket="test-bucket",
        )
        assert service.is_configured is True

    def test_is_not_configured_missing_key(self):
        """Service is not configured without access key."""
        service = StorageService(
            access_key_id="",
            secret_access_key="test-secret",
            endpoint="https://test.r2.cloudflarestorage.com",
            bucket="test-bucket",
        )
        assert service.is_configured is False

    def test_is_not_configured_missing_secret(self):
        """Service is not configured without secret key."""
        service = StorageService(
            access_key_id="test-key",
            secret_access_key="",
            endpoint="https://test.r2.cloudflarestorage.com",
            bucket="test-bucket",
        )
        assert service.is_configured is False

    def test_is_not_configured_missing_endpoint(self):
        """Service is not configured without endpoint."""
        service = StorageService(
            access_key_id="test-key",
            secret_access_key="test-secret",
            endpoint="",
            bucket="test-bucket",
        )
        assert service.is_configured is False

    def test_is_not_configured_missing_bucket(self):
        """Service is not configured without bucket."""
        service = StorageService(
            access_key_id="test-key",
            secret_access_key="test-secret",
            endpoint="https://test.r2.cloudflarestorage.com",
            bucket="",
        )
        assert service.is_configured is False

    def test_default_expiration_times(self):
        """Service has sensible default expiration times."""
        service = StorageService(
            access_key_id="test",
            secret_access_key="test",
            endpoint="test",
            bucket="test",
        )
        assert service.upload_expires == 3600  # 1 hour
        assert service.download_expires == 3600  # 1 hour

    def test_custom_expiration_times(self):
        """Service accepts custom expiration times."""
        service = StorageService(
            access_key_id="test",
            secret_access_key="test",
            endpoint="test",
            bucket="test",
            upload_expires=7200,
            download_expires=1800,
        )
        assert service.upload_expires == 7200
        assert service.download_expires == 1800


# ===========================================
# STORAGE KEY GENERATION
# ===========================================

class TestStorageKeyGeneration:
    """Test storage key/path generation."""

    def test_generate_key_basic(self, storage_service):
        """Generate basic storage key."""
        tenant_id = uuid4()
        entity_id = uuid4()

        key = storage_service.generate_storage_key(
            tenant_id=tenant_id,
            entity_type="applicants",
            entity_id=entity_id,
            filename="passport.jpg",
        )

        assert str(tenant_id) in key
        assert "applicants" in key
        assert str(entity_id) in key
        assert "passport.jpg" in key

    def test_generate_key_with_timestamp(self, storage_service):
        """Generated key includes timestamp."""
        tenant_id = uuid4()
        entity_id = uuid4()

        key = storage_service.generate_storage_key(
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

    def test_generate_key_sanitizes_filename(self, storage_service):
        """Filename is sanitized to remove unsafe characters."""
        tenant_id = uuid4()
        entity_id = uuid4()

        key = storage_service.generate_storage_key(
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

    def test_generate_key_preserves_extension(self, storage_service):
        """File extension is preserved."""
        tenant_id = uuid4()
        entity_id = uuid4()

        key = storage_service.generate_storage_key(
            tenant_id=tenant_id,
            entity_type="applicants",
            entity_id=entity_id,
            filename="document.pdf",
        )

        assert key.endswith(".pdf")

    def test_generate_key_with_uuid_strings(self, storage_service):
        """UUIDs can be passed as strings."""
        tenant_id = "12345678-1234-5678-1234-567812345678"
        entity_id = "87654321-4321-8765-4321-876543218765"

        key = storage_service.generate_storage_key(
            tenant_id=tenant_id,
            entity_type="applicants",
            entity_id=entity_id,
            filename="test.jpg",
        )

        assert tenant_id in key
        assert entity_id in key


# ===========================================
# PRESIGNED UPLOAD URL
# ===========================================

class TestPresignedUpload:
    """Test presigned upload URL generation."""

    @pytest.mark.asyncio
    async def test_create_presigned_upload_success(self, mock_storage, storage_service):
        """Successfully generate presigned upload URL."""
        result = await storage_service.create_presigned_upload(
            key="test/path/file.jpg",
            content_type="image/jpeg",
        )

        assert "upload_url" in result
        assert "fields" in result
        assert "key" in result
        assert "expires_in" in result
        assert "max_size_bytes" in result

    @pytest.mark.asyncio
    async def test_create_presigned_upload_with_metadata(self, mock_storage, storage_service):
        """Generate upload URL with custom metadata."""
        result = await storage_service.create_presigned_upload(
            key="test/path/file.jpg",
            content_type="image/jpeg",
            metadata={"document-type": "passport", "applicant-id": "123"},
        )

        assert "upload_url" in result

    @pytest.mark.asyncio
    async def test_create_presigned_upload_with_size_limit(self, mock_storage, storage_service):
        """Generate upload URL with size limit."""
        result = await storage_service.create_presigned_upload(
            key="test/path/file.jpg",
            content_type="image/jpeg",
            max_size_mb=10,
        )

        assert result["max_size_bytes"] == 10 * 1024 * 1024

    @pytest.mark.asyncio
    async def test_create_presigned_upload_with_custom_expiry(self, mock_storage, storage_service):
        """Generate upload URL with custom expiration."""
        result = await storage_service.create_presigned_upload(
            key="test/path/file.jpg",
            content_type="image/jpeg",
            expires_in=1800,  # 30 minutes
        )

        assert result["expires_in"] == 1800

    @pytest.mark.asyncio
    async def test_create_presigned_upload_not_configured(self):
        """Upload fails when not configured."""
        service = StorageService(
            access_key_id="",
            secret_access_key="",
            endpoint="",
            bucket="",
        )

        with pytest.raises(StorageConfigError) as exc_info:
            await service.create_presigned_upload(key="test", content_type="image/jpeg")

        assert "not configured" in str(exc_info.value)


# ===========================================
# PRESIGNED PUT URL
# ===========================================

class TestPresignedPutUpload:
    """Test presigned PUT URL generation."""

    @pytest.mark.asyncio
    async def test_create_presigned_put_success(self, mock_storage, storage_service):
        """Successfully generate presigned PUT URL."""
        url = await storage_service.create_presigned_upload_put(
            key="test/path/file.jpg",
            content_type="image/jpeg",
        )

        assert isinstance(url, str)
        assert "test-bucket" in url or "signature" in url.lower() or url.startswith("https://")

    @pytest.mark.asyncio
    async def test_create_presigned_put_not_configured(self):
        """PUT upload fails when not configured."""
        service = StorageService(
            access_key_id="",
            secret_access_key="",
            endpoint="",
            bucket="",
        )

        with pytest.raises(StorageConfigError):
            await service.create_presigned_upload_put(key="test", content_type="image/jpeg")


# ===========================================
# PRESIGNED DOWNLOAD URL
# ===========================================

class TestPresignedDownload:
    """Test presigned download URL generation."""

    @pytest.mark.asyncio
    async def test_create_presigned_download_success(self, mock_storage, storage_service):
        """Successfully generate presigned download URL."""
        url = await storage_service.create_presigned_download(key="test/path/file.jpg")

        assert isinstance(url, str)
        assert "signature" in url.lower() or "test" in url

    @pytest.mark.asyncio
    async def test_create_presigned_download_with_filename(self, mock_storage, storage_service):
        """Generate download URL with custom download filename."""
        url = await storage_service.create_presigned_download(
            key="test/path/abc123.jpg",
            filename="passport_john_doe.jpg",
        )

        assert isinstance(url, str)

    @pytest.mark.asyncio
    async def test_create_presigned_download_with_custom_expiry(self, mock_storage, storage_service):
        """Generate download URL with custom expiration."""
        url = await storage_service.create_presigned_download(
            key="test/path/file.jpg",
            expires_in=600,  # 10 minutes
        )

        assert isinstance(url, str)

    @pytest.mark.asyncio
    async def test_create_presigned_download_not_configured(self):
        """Download fails when not configured."""
        service = StorageService(
            access_key_id="",
            secret_access_key="",
            endpoint="",
            bucket="",
        )

        with pytest.raises(StorageConfigError):
            await service.create_presigned_download(key="test")


# ===========================================
# OBJECT EXISTS CHECK
# ===========================================

class TestObjectExists:
    """Test object existence checks."""

    @pytest.mark.asyncio
    async def test_object_exists_true(self, mock_storage, storage_service):
        """Check returns True when object exists."""
        exists = await storage_service.object_exists(key="test/existing-file.jpg")
        assert exists is True

    @pytest.mark.asyncio
    async def test_object_exists_false(self, storage_service):
        """Check returns False when object doesn't exist."""
        with patch("aioboto3.Session") as mock_session:
            mock_client = AsyncMock()

            # Simulate 404 response
            error_response = {"Error": {"Code": "404"}}
            mock_client.head_object = AsyncMock(
                side_effect=ClientError(error_response, "HeadObject")
            )

            mock_session_instance = MagicMock()
            mock_session_instance.client = MagicMock(return_value=AsyncMock(
                __aenter__=AsyncMock(return_value=mock_client),
                __aexit__=AsyncMock(return_value=None),
            ))
            mock_session.return_value = mock_session_instance

            exists = await storage_service.object_exists(key="test/nonexistent.jpg")

        assert exists is False

    @pytest.mark.asyncio
    async def test_object_exists_not_configured(self):
        """Exists check fails when not configured."""
        service = StorageService(
            access_key_id="",
            secret_access_key="",
            endpoint="",
            bucket="",
        )

        with pytest.raises(StorageConfigError):
            await service.object_exists(key="test")


# ===========================================
# OBJECT METADATA
# ===========================================

class TestObjectMetadata:
    """Test object metadata retrieval."""

    @pytest.mark.asyncio
    async def test_get_object_metadata_success(self, mock_storage, storage_service):
        """Successfully retrieve object metadata."""
        metadata = await storage_service.get_object_metadata(key="test/file.jpg")

        assert metadata is not None
        assert "size" in metadata
        assert "content_type" in metadata
        assert "last_modified" in metadata
        assert "etag" in metadata
        assert "metadata" in metadata

    @pytest.mark.asyncio
    async def test_get_object_metadata_not_found(self, storage_service):
        """Return None for non-existent object."""
        with patch("aioboto3.Session") as mock_session:
            mock_client = AsyncMock()

            error_response = {"Error": {"Code": "404"}}
            mock_client.head_object = AsyncMock(
                side_effect=ClientError(error_response, "HeadObject")
            )

            mock_session_instance = MagicMock()
            mock_session_instance.client = MagicMock(return_value=AsyncMock(
                __aenter__=AsyncMock(return_value=mock_client),
                __aexit__=AsyncMock(return_value=None),
            ))
            mock_session.return_value = mock_session_instance

            metadata = await storage_service.get_object_metadata(key="test/nonexistent.jpg")

        assert metadata is None

    @pytest.mark.asyncio
    async def test_get_object_metadata_not_configured(self):
        """Metadata retrieval fails when not configured."""
        service = StorageService(
            access_key_id="",
            secret_access_key="",
            endpoint="",
            bucket="",
        )

        with pytest.raises(StorageConfigError):
            await service.get_object_metadata(key="test")


# ===========================================
# DELETE OPERATIONS
# ===========================================

class TestDeleteOperations:
    """Test object deletion operations."""

    @pytest.mark.asyncio
    async def test_delete_success(self, mock_storage, storage_service):
        """Successfully delete an object."""
        result = await storage_service.delete(key="test/file-to-delete.jpg")
        assert result is True

    @pytest.mark.asyncio
    async def test_delete_not_found(self, storage_service):
        """Delete returns False for non-existent object."""
        with patch("aioboto3.Session") as mock_session:
            mock_client = AsyncMock()

            error_response = {"Error": {"Code": "NoSuchKey"}}
            mock_client.delete_object = AsyncMock(
                side_effect=ClientError(error_response, "DeleteObject")
            )

            mock_session_instance = MagicMock()
            mock_session_instance.client = MagicMock(return_value=AsyncMock(
                __aenter__=AsyncMock(return_value=mock_client),
                __aexit__=AsyncMock(return_value=None),
            ))
            mock_session.return_value = mock_session_instance

            result = await storage_service.delete(key="test/nonexistent.jpg")

        assert result is False

    @pytest.mark.asyncio
    async def test_delete_not_configured(self):
        """Delete fails when not configured."""
        service = StorageService(
            access_key_id="",
            secret_access_key="",
            endpoint="",
            bucket="",
        )

        with pytest.raises(StorageConfigError):
            await service.delete(key="test")


# ===========================================
# DELETE BY PREFIX
# ===========================================

class TestDeleteByPrefix:
    """Test deletion of objects by prefix."""

    @pytest.mark.asyncio
    async def test_delete_prefix_success(self, storage_service):
        """Successfully delete objects by prefix."""
        with patch("aioboto3.Session") as mock_session:
            mock_client = AsyncMock()

            # Mock paginator
            mock_paginator = MagicMock()
            mock_paginator.paginate = MagicMock(return_value=AsyncIterator([
                {
                    "Contents": [
                        {"Key": "test/prefix/file1.jpg"},
                        {"Key": "test/prefix/file2.jpg"},
                    ]
                }
            ]))
            mock_client.get_paginator = MagicMock(return_value=mock_paginator)
            mock_client.delete_objects = AsyncMock(return_value={})

            mock_session_instance = MagicMock()
            mock_session_instance.client = MagicMock(return_value=AsyncMock(
                __aenter__=AsyncMock(return_value=mock_client),
                __aexit__=AsyncMock(return_value=None),
            ))
            mock_session.return_value = mock_session_instance

            count = await storage_service.delete_prefix(prefix="test/prefix/")

        assert count == 2

    @pytest.mark.asyncio
    async def test_delete_prefix_empty(self, storage_service):
        """Delete prefix returns 0 when no objects found."""
        with patch("aioboto3.Session") as mock_session:
            mock_client = AsyncMock()

            # Mock paginator with no contents
            mock_paginator = MagicMock()
            mock_paginator.paginate = MagicMock(return_value=AsyncIterator([
                {"Contents": []}
            ]))
            mock_client.get_paginator = MagicMock(return_value=mock_paginator)

            mock_session_instance = MagicMock()
            mock_session_instance.client = MagicMock(return_value=AsyncMock(
                __aenter__=AsyncMock(return_value=mock_client),
                __aexit__=AsyncMock(return_value=None),
            ))
            mock_session.return_value = mock_session_instance

            count = await storage_service.delete_prefix(prefix="empty/prefix/")

        assert count == 0

    @pytest.mark.asyncio
    async def test_delete_prefix_not_configured(self):
        """Delete prefix fails when not configured."""
        service = StorageService(
            access_key_id="",
            secret_access_key="",
            endpoint="",
            bucket="",
        )

        with pytest.raises(StorageConfigError):
            await service.delete_prefix(prefix="test/")


# ===========================================
# COPY OPERATIONS
# ===========================================

class TestCopyOperations:
    """Test object copy operations."""

    @pytest.mark.asyncio
    async def test_copy_success(self, mock_storage, storage_service):
        """Successfully copy an object."""
        with patch("aioboto3.Session") as mock_session:
            mock_client = AsyncMock()
            mock_client.copy_object = AsyncMock(return_value={})

            mock_session_instance = MagicMock()
            mock_session_instance.client = MagicMock(return_value=AsyncMock(
                __aenter__=AsyncMock(return_value=mock_client),
                __aexit__=AsyncMock(return_value=None),
            ))
            mock_session.return_value = mock_session_instance

            result = await storage_service.copy(
                source_key="original/file.jpg",
                dest_key="copy/file.jpg",
            )

        assert result is True

    @pytest.mark.asyncio
    async def test_copy_with_metadata(self, storage_service):
        """Copy object with new metadata."""
        with patch("aioboto3.Session") as mock_session:
            mock_client = AsyncMock()
            mock_client.copy_object = AsyncMock(return_value={})

            mock_session_instance = MagicMock()
            mock_session_instance.client = MagicMock(return_value=AsyncMock(
                __aenter__=AsyncMock(return_value=mock_client),
                __aexit__=AsyncMock(return_value=None),
            ))
            mock_session.return_value = mock_session_instance

            result = await storage_service.copy(
                source_key="original/file.jpg",
                dest_key="copy/file.jpg",
                metadata={"new-key": "new-value"},
            )

        assert result is True

    @pytest.mark.asyncio
    async def test_copy_not_configured(self):
        """Copy fails when not configured."""
        service = StorageService(
            access_key_id="",
            secret_access_key="",
            endpoint="",
            bucket="",
        )

        with pytest.raises(StorageConfigError):
            await service.copy(source_key="a", dest_key="b")


# ===========================================
# ERROR HANDLING
# ===========================================

class TestStorageErrorHandling:
    """Test error handling for storage operations."""

    @pytest.mark.asyncio
    async def test_upload_error_wrapped(self, storage_service):
        """Upload errors are wrapped in StorageUploadError."""
        with patch("aioboto3.Session") as mock_session:
            mock_client = AsyncMock()

            error_response = {"Error": {"Code": "500", "Message": "Internal Error"}}
            mock_client.generate_presigned_post = AsyncMock(
                side_effect=ClientError(error_response, "GeneratePresignedPost")
            )

            mock_session_instance = MagicMock()
            mock_session_instance.client = MagicMock(return_value=AsyncMock(
                __aenter__=AsyncMock(return_value=mock_client),
                __aexit__=AsyncMock(return_value=None),
            ))
            mock_session.return_value = mock_session_instance

            with pytest.raises(StorageUploadError):
                await storage_service.create_presigned_upload(
                    key="test",
                    content_type="image/jpeg"
                )

    @pytest.mark.asyncio
    async def test_download_error_wrapped(self, storage_service):
        """Download errors are wrapped in StorageDownloadError."""
        with patch("aioboto3.Session") as mock_session:
            mock_client = AsyncMock()

            error_response = {"Error": {"Code": "500", "Message": "Internal Error"}}
            mock_client.generate_presigned_url = AsyncMock(
                side_effect=ClientError(error_response, "GeneratePresignedUrl")
            )

            mock_session_instance = MagicMock()
            mock_session_instance.client = MagicMock(return_value=AsyncMock(
                __aenter__=AsyncMock(return_value=mock_client),
                __aexit__=AsyncMock(return_value=None),
            ))
            mock_session.return_value = mock_session_instance

            with pytest.raises(StorageDownloadError):
                await storage_service.create_presigned_download(key="test")


# ===========================================
# HELPER CLASS FOR ASYNC ITERATOR
# ===========================================

class AsyncIterator:
    """Helper class to create async iterator for tests."""

    def __init__(self, items):
        self.items = items
        self.index = 0

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self.index >= len(self.items):
            raise StopAsyncIteration
        item = self.items[self.index]
        self.index += 1
        return item
