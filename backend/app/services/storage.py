"""
Get Clearance - Storage Service
================================
Cloudflare R2 integration for document storage.

Uses boto3/aioboto3 with S3-compatible API for:
- Presigned upload URLs (direct client upload)
- Presigned download URLs (secure document access)
- Object management (delete, copy, etc.)

R2 provides S3-compatible object storage with:
- Zero egress fees
- Global distribution via Cloudflare's network
- S3 API compatibility
"""

import logging
from datetime import datetime
from typing import Any
from uuid import UUID

import aioboto3
from botocore.config import Config
from botocore.exceptions import ClientError

from app.config import settings

logger = logging.getLogger(__name__)


class StorageServiceError(Exception):
    """Base exception for storage service errors."""
    pass


class StorageConfigError(StorageServiceError):
    """Configuration error (e.g., missing credentials)."""
    pass


class StorageUploadError(StorageServiceError):
    """Error during upload operation."""
    pass


class StorageDownloadError(StorageServiceError):
    """Error during download operation."""
    pass


class StorageService:
    """
    Service for document storage via Cloudflare R2.
    
    R2 is S3-compatible, so we use aioboto3 for async operations.
    All uploads go directly from client to R2 via presigned URLs,
    keeping large files off the API server.
    
    Usage:
        # Generate upload URL for client
        upload_url = await storage_service.create_presigned_upload(
            key="tenants/abc123/documents/passport.jpg",
            content_type="image/jpeg",
            max_size_mb=10
        )
        
        # Generate download URL
        download_url = await storage_service.create_presigned_download(
            key="tenants/abc123/documents/passport.jpg"
        )
    """
    
    def __init__(
        self,
        access_key_id: str | None = None,
        secret_access_key: str | None = None,
        endpoint: str | None = None,
        bucket: str | None = None,
        upload_expires: int | None = None,
        download_expires: int | None = None,
    ):
        self.access_key_id = access_key_id or settings.r2_access_key_id
        self.secret_access_key = secret_access_key or settings.r2_secret_access_key
        self.endpoint = endpoint or settings.r2_endpoint
        self.bucket = bucket or settings.r2_bucket
        self.upload_expires = upload_expires or settings.r2_upload_url_expires
        self.download_expires = download_expires or settings.r2_download_url_expires
        
        self._session: aioboto3.Session | None = None
    
    @property
    def is_configured(self) -> bool:
        """Check if service is properly configured."""
        return bool(
            self.access_key_id
            and self.secret_access_key
            and self.endpoint
            and self.bucket
        )
    
    def _get_session(self) -> aioboto3.Session:
        """Get or create aioboto3 session."""
        if self._session is None:
            self._session = aioboto3.Session(
                aws_access_key_id=self.access_key_id,
                aws_secret_access_key=self.secret_access_key,
            )
        return self._session
    
    def _get_client_config(self) -> Config:
        """Get boto3 client configuration."""
        return Config(
            signature_version="s3v4",
            s3={"addressing_style": "path"},
            retries={"max_attempts": 3, "mode": "adaptive"},
        )
    
    def generate_storage_key(
        self,
        tenant_id: UUID | str,
        entity_type: str,
        entity_id: UUID | str,
        filename: str,
    ) -> str:
        """
        Generate a storage key (path) for a document.
        
        Format: {tenant_id}/{entity_type}/{entity_id}/{timestamp}_{filename}
        
        Args:
            tenant_id: Tenant UUID
            entity_type: Type of entity (applicants, companies, cases)
            entity_id: Entity UUID
            filename: Original filename
            
        Returns:
            Storage key path
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        # Sanitize filename
        safe_filename = "".join(
            c for c in filename 
            if c.isalnum() or c in "._-"
        )
        return f"{tenant_id}/{entity_type}/{entity_id}/{timestamp}_{safe_filename}"
    
    async def create_presigned_upload(
        self,
        key: str,
        content_type: str = "application/octet-stream",
        max_size_mb: int = 50,
        metadata: dict[str, str] | None = None,
        expires_in: int | None = None,
    ) -> dict[str, Any]:
        """
        Generate a presigned URL for direct upload to R2.
        
        The client uploads directly to R2, bypassing the API server.
        This is efficient for large files and reduces server load.
        
        Args:
            key: Storage path/key for the object
            content_type: MIME type of the file
            max_size_mb: Maximum allowed file size in MB
            metadata: Optional metadata to attach to object
            expires_in: URL expiration in seconds (default from config)
            
        Returns:
            Dict with upload_url, fields (for multipart), and expires_in
            
        Raises:
            StorageConfigError: If R2 is not configured
            StorageUploadError: If presigned URL generation fails
        """
        if not self.is_configured:
            raise StorageConfigError("Cloudflare R2 not configured")
        
        expires = expires_in or self.upload_expires
        
        session = self._get_session()
        config = self._get_client_config()
        
        try:
            async with session.client(
                "s3",
                endpoint_url=self.endpoint,
                config=config,
            ) as s3:
                # Build conditions for POST policy
                conditions = [
                    {"bucket": self.bucket},
                    ["starts-with", "$key", key],
                    ["content-length-range", 1, max_size_mb * 1024 * 1024],
                    {"Content-Type": content_type},
                ]
                
                # Add metadata conditions
                fields = {"Content-Type": content_type}
                if metadata:
                    for meta_key, meta_value in metadata.items():
                        amz_key = f"x-amz-meta-{meta_key}"
                        conditions.append({amz_key: meta_value})
                        fields[amz_key] = meta_value
                
                # Generate presigned POST
                presigned = await s3.generate_presigned_post(
                    Bucket=self.bucket,
                    Key=key,
                    Fields=fields,
                    Conditions=conditions,
                    ExpiresIn=expires,
                )
                
                logger.info(f"Generated presigned upload URL for: {key}")
                
                return {
                    "upload_url": presigned["url"],
                    "fields": presigned["fields"],
                    "key": key,
                    "expires_in": expires,
                    "max_size_bytes": max_size_mb * 1024 * 1024,
                }
                
        except ClientError as e:
            logger.error(f"Failed to generate upload URL: {e}")
            raise StorageUploadError(f"Failed to generate upload URL: {e}")
    
    async def create_presigned_upload_put(
        self,
        key: str,
        content_type: str = "application/octet-stream",
        expires_in: int | None = None,
    ) -> str:
        """
        Generate a presigned PUT URL for simple upload.
        
        Simpler than POST but doesn't support size limits or policies.
        Use for trusted uploads where you've validated on the API side.
        
        Args:
            key: Storage path/key for the object
            content_type: MIME type of the file
            expires_in: URL expiration in seconds
            
        Returns:
            Presigned PUT URL string
        """
        if not self.is_configured:
            raise StorageConfigError("Cloudflare R2 not configured")
        
        expires = expires_in or self.upload_expires
        
        session = self._get_session()
        config = self._get_client_config()
        
        try:
            async with session.client(
                "s3",
                endpoint_url=self.endpoint,
                config=config,
            ) as s3:
                url = await s3.generate_presigned_url(
                    "put_object",
                    Params={
                        "Bucket": self.bucket,
                        "Key": key,
                        "ContentType": content_type,
                    },
                    ExpiresIn=expires,
                )
                
                logger.info(f"Generated presigned PUT URL for: {key}")
                return url
                
        except ClientError as e:
            logger.error(f"Failed to generate PUT URL: {e}")
            raise StorageUploadError(f"Failed to generate PUT URL: {e}")
    
    async def create_presigned_download(
        self,
        key: str,
        filename: str | None = None,
        expires_in: int | None = None,
    ) -> str:
        """
        Generate a presigned URL for downloading a document.
        
        Args:
            key: Storage path/key of the object
            filename: Optional filename for Content-Disposition header
            expires_in: URL expiration in seconds (default from config)
            
        Returns:
            Presigned download URL
            
        Raises:
            StorageConfigError: If R2 is not configured
            StorageDownloadError: If presigned URL generation fails
        """
        if not self.is_configured:
            raise StorageConfigError("Cloudflare R2 not configured")
        
        expires = expires_in or self.download_expires
        
        session = self._get_session()
        config = self._get_client_config()
        
        try:
            async with session.client(
                "s3",
                endpoint_url=self.endpoint,
                config=config,
            ) as s3:
                params: dict[str, Any] = {
                    "Bucket": self.bucket,
                    "Key": key,
                }
                
                # Add Content-Disposition for download filename
                if filename:
                    params["ResponseContentDisposition"] = (
                        f'attachment; filename="{filename}"'
                    )
                
                url = await s3.generate_presigned_url(
                    "get_object",
                    Params=params,
                    ExpiresIn=expires,
                )
                
                logger.info(f"Generated presigned download URL for: {key}")
                return url
                
        except ClientError as e:
            logger.error(f"Failed to generate download URL: {e}")
            raise StorageDownloadError(f"Failed to generate download URL: {e}")
    
    async def delete(self, key: str) -> bool:
        """
        Delete an object from storage.
        
        Args:
            key: Storage path/key of the object
            
        Returns:
            True if deleted, False if not found
        """
        if not self.is_configured:
            raise StorageConfigError("Cloudflare R2 not configured")
        
        session = self._get_session()
        config = self._get_client_config()
        
        try:
            async with session.client(
                "s3",
                endpoint_url=self.endpoint,
                config=config,
            ) as s3:
                await s3.delete_object(
                    Bucket=self.bucket,
                    Key=key,
                )
                
                logger.info(f"Deleted object: {key}")
                return True
                
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code")
            if error_code == "NoSuchKey":
                logger.warning(f"Object not found for deletion: {key}")
                return False
            logger.error(f"Failed to delete object: {e}")
            raise StorageServiceError(f"Failed to delete object: {e}")
    
    async def delete_prefix(self, prefix: str) -> int:
        """
        Delete all objects with a given prefix.
        
        Useful for cleaning up all documents for an entity.
        
        Args:
            prefix: Key prefix to match (e.g., "{tenant_id}/applicants/{id}/")
            
        Returns:
            Number of objects deleted
        """
        if not self.is_configured:
            raise StorageConfigError("Cloudflare R2 not configured")
        
        session = self._get_session()
        config = self._get_client_config()
        
        deleted_count = 0
        
        try:
            async with session.client(
                "s3",
                endpoint_url=self.endpoint,
                config=config,
            ) as s3:
                # List objects with prefix
                paginator = s3.get_paginator("list_objects_v2")
                
                async for page in paginator.paginate(
                    Bucket=self.bucket,
                    Prefix=prefix,
                ):
                    contents = page.get("Contents", [])
                    if not contents:
                        continue
                    
                    # Delete in batches of 1000 (S3 limit)
                    objects = [{"Key": obj["Key"]} for obj in contents]
                    
                    await s3.delete_objects(
                        Bucket=self.bucket,
                        Delete={"Objects": objects},
                    )
                    
                    deleted_count += len(objects)
                
                logger.info(f"Deleted {deleted_count} objects with prefix: {prefix}")
                return deleted_count
                
        except ClientError as e:
            logger.error(f"Failed to delete objects with prefix: {e}")
            raise StorageServiceError(f"Failed to delete objects: {e}")
    
    async def object_exists(self, key: str) -> bool:
        """
        Check if an object exists in storage.
        
        Args:
            key: Storage path/key of the object
            
        Returns:
            True if exists, False otherwise
        """
        if not self.is_configured:
            raise StorageConfigError("Cloudflare R2 not configured")
        
        session = self._get_session()
        config = self._get_client_config()
        
        try:
            async with session.client(
                "s3",
                endpoint_url=self.endpoint,
                config=config,
            ) as s3:
                await s3.head_object(
                    Bucket=self.bucket,
                    Key=key,
                )
                return True
                
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code")
            if error_code in ("404", "NoSuchKey"):
                return False
            raise StorageServiceError(f"Failed to check object: {e}")
    
    async def get_object_metadata(self, key: str) -> dict[str, Any] | None:
        """
        Get metadata for an object.
        
        Args:
            key: Storage path/key of the object
            
        Returns:
            Dict with size, content_type, last_modified, metadata
            or None if not found
        """
        if not self.is_configured:
            raise StorageConfigError("Cloudflare R2 not configured")
        
        session = self._get_session()
        config = self._get_client_config()
        
        try:
            async with session.client(
                "s3",
                endpoint_url=self.endpoint,
                config=config,
            ) as s3:
                response = await s3.head_object(
                    Bucket=self.bucket,
                    Key=key,
                )
                
                return {
                    "size": response.get("ContentLength"),
                    "content_type": response.get("ContentType"),
                    "last_modified": response.get("LastModified"),
                    "etag": response.get("ETag"),
                    "metadata": response.get("Metadata", {}),
                }
                
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code")
            if error_code in ("404", "NoSuchKey"):
                return None
            raise StorageServiceError(f"Failed to get object metadata: {e}")
    
    async def copy(
        self,
        source_key: str,
        dest_key: str,
        metadata: dict[str, str] | None = None,
    ) -> bool:
        """
        Copy an object within the bucket.
        
        Args:
            source_key: Source object key
            dest_key: Destination object key
            metadata: Optional new metadata (replaces existing)
            
        Returns:
            True if successful
        """
        if not self.is_configured:
            raise StorageConfigError("Cloudflare R2 not configured")
        
        session = self._get_session()
        config = self._get_client_config()
        
        try:
            async with session.client(
                "s3",
                endpoint_url=self.endpoint,
                config=config,
            ) as s3:
                copy_source = {"Bucket": self.bucket, "Key": source_key}
                
                params: dict[str, Any] = {
                    "Bucket": self.bucket,
                    "Key": dest_key,
                    "CopySource": copy_source,
                }
                
                if metadata:
                    params["Metadata"] = metadata
                    params["MetadataDirective"] = "REPLACE"
                
                await s3.copy_object(**params)
                
                logger.info(f"Copied object from {source_key} to {dest_key}")
                return True
                
        except ClientError as e:
            logger.error(f"Failed to copy object: {e}")
            raise StorageServiceError(f"Failed to copy object: {e}")


# ===========================================
# SINGLETON INSTANCE
# ===========================================

storage_service = StorageService()
