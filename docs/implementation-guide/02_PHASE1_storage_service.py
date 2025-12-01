"""
Storage Service - Cloudflare R2 / AWS S3 Integration
=====================================================

Provides secure document storage with presigned URLs for direct uploads/downloads.
Keeps large files off the API server (Sumsub pattern).

Features:
- Presigned upload URLs (client uploads directly to R2)
- Presigned download URLs (temporary access)
- Automatic file organization by tenant/applicant
- Lifecycle policies (future: auto-delete after N years)
"""

from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID
import logging

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from app.config import settings

logger = logging.getLogger(__name__)


class StorageService:
    """
    Manages document storage in Cloudflare R2 (S3-compatible).
    
    Usage:
        storage = StorageService()
        upload_url = await storage.create_presigned_upload(...)
        download_url = await storage.create_presigned_download(...)
    """
    
    def __init__(self):
        """Initialize S3 client for R2."""
        self.s3_client = boto3.client(
            's3',
            endpoint_url=settings.r2_endpoint,
            aws_access_key_id=settings.r2_access_key_id,
            aws_secret_access_key=settings.r2_secret_access_key,
            config=Config(
                signature_version='s3v4',
                region_name='auto',  # R2 uses 'auto' region
            ),
        )
        self.bucket = settings.r2_bucket
    
    def _generate_key(
        self,
        tenant_id: UUID,
        applicant_id: UUID,
        document_id: UUID,
        file_name: str,
    ) -> str:
        """
        Generate S3 key for document storage.
        
        Pattern: {tenant_id}/{applicant_id}/documents/{document_id}/{timestamp}_{filename}
        
        This organization allows for:
        - Easy tenant isolation
        - Simple applicant-level queries
        - Chronological ordering
        - Original filename preservation
        """
        timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        safe_filename = file_name.replace(' ', '_').replace('/', '_')
        
        return f"{tenant_id}/{applicant_id}/documents/{document_id}/{timestamp}_{safe_filename}"
    
    async def create_presigned_upload(
        self,
        tenant_id: UUID,
        applicant_id: UUID,
        document_id: UUID,
        file_name: str,
        content_type: str,
        expires_in: int = 3600,  # 1 hour
    ) -> dict:
        """
        Generate presigned POST URL for direct client upload.
        
        Flow:
        1. API receives upload request with metadata
        2. API creates document record in DB
        3. API returns presigned URL to client
        4. Client uploads directly to R2 (doesn't hit API)
        5. Client confirms upload complete
        6. API triggers background processing
        
        Args:
            tenant_id: Tenant UUID
            applicant_id: Applicant UUID
            document_id: Document UUID (must be created first)
            file_name: Original filename
            content_type: MIME type (e.g., 'image/jpeg', 'application/pdf')
            expires_in: URL expiration in seconds (default: 1 hour)
        
        Returns:
            dict with 'url', 'key', and 'fields' for POST upload
        """
        key = self._generate_key(tenant_id, applicant_id, document_id, file_name)
        
        try:
            # Generate presigned POST URL
            # This allows the client to upload directly without credentials
            presigned_post = self.s3_client.generate_presigned_post(
                Bucket=self.bucket,
                Key=key,
                Fields={
                    'Content-Type': content_type,
                },
                Conditions=[
                    {'Content-Type': content_type},
                    ['content-length-range', 1024, 10485760],  # 1KB - 10MB
                ],
                ExpiresIn=expires_in,
            )
            
            logger.info(f"Generated presigned upload URL for document {document_id}")
            
            return {
                'url': presigned_post['url'],
                'key': key,
                'fields': presigned_post['fields'],
                'expires_in': expires_in,
            }
            
        except ClientError as e:
            logger.error(f"Failed to generate presigned upload URL: {e}")
            raise StorageError(f"Failed to generate upload URL: {str(e)}")
    
    async def create_presigned_download(
        self,
        key: str,
        expires_in: int = 3600,  # 1 hour
    ) -> str:
        """
        Generate presigned GET URL for temporary download access.
        
        Args:
            key: S3 object key (from document.storage_path)
            expires_in: URL expiration in seconds (default: 1 hour)
        
        Returns:
            Presigned download URL (string)
        """
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket,
                    'Key': key,
                },
                ExpiresIn=expires_in,
            )
            
            logger.info(f"Generated presigned download URL for key {key}")
            return url
            
        except ClientError as e:
            logger.error(f"Failed to generate presigned download URL: {e}")
            raise StorageError(f"Failed to generate download URL: {str(e)}")
    
    async def delete(self, key: str) -> None:
        """
        Delete object from storage.
        
        Use cases:
        - User deletes document
        - Retention policy expires
        - Failed upload cleanup
        
        Args:
            key: S3 object key to delete
        """
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket,
                Key=key,
            )
            logger.info(f"Deleted object: {key}")
            
        except ClientError as e:
            logger.error(f"Failed to delete object {key}: {e}")
            raise StorageError(f"Failed to delete object: {str(e)}")
    
    async def check_exists(self, key: str) -> bool:
        """
        Check if object exists in storage.
        
        Args:
            key: S3 object key
        
        Returns:
            True if exists, False otherwise
        """
        try:
            self.s3_client.head_object(
                Bucket=self.bucket,
                Key=key,
            )
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            logger.error(f"Error checking object existence: {e}")
            raise StorageError(f"Failed to check object existence: {str(e)}")
    
    async def get_metadata(self, key: str) -> dict:
        """
        Get object metadata without downloading.
        
        Returns:
            dict with ContentType, ContentLength, LastModified, etc.
        """
        try:
            response = self.s3_client.head_object(
                Bucket=self.bucket,
                Key=key,
            )
            
            return {
                'content_type': response.get('ContentType'),
                'content_length': response.get('ContentLength'),
                'last_modified': response.get('LastModified'),
                'etag': response.get('ETag'),
            }
            
        except ClientError as e:
            logger.error(f"Failed to get object metadata: {e}")
            raise StorageError(f"Failed to get metadata: {str(e)}")
    
    async def copy(self, source_key: str, dest_key: str) -> None:
        """
        Copy object within bucket.
        
        Use case: Copy document from one applicant to another (reusable KYC)
        """
        try:
            self.s3_client.copy_object(
                Bucket=self.bucket,
                CopySource={'Bucket': self.bucket, 'Key': source_key},
                Key=dest_key,
            )
            logger.info(f"Copied object from {source_key} to {dest_key}")
            
        except ClientError as e:
            logger.error(f"Failed to copy object: {e}")
            raise StorageError(f"Failed to copy object: {str(e)}")


class StorageError(Exception):
    """Custom exception for storage errors."""
    pass


# Singleton instance
_storage_service: Optional[StorageService] = None


def get_storage_service() -> StorageService:
    """
    Get singleton storage service instance.
    
    Usage in FastAPI endpoints:
        storage: StorageService = Depends(get_storage_service)
    """
    global _storage_service
    if _storage_service is None:
        _storage_service = StorageService()
    return _storage_service
