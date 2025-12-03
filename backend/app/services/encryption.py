"""
Get Clearance - PII Encryption Service
======================================
Application-level encryption for personally identifiable information (PII).

Uses Fernet symmetric encryption (AES-128-CBC with HMAC) for:
- Email addresses
- Phone numbers
- Names
- SSN/ID numbers
- Addresses

Key derivation uses PBKDF2 with high iteration count for security.
"""

import base64
import logging
from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)


class EncryptionService:
    """
    Application-level encryption for PII fields.

    Uses Fernet (AES-128-CBC with HMAC) for symmetric encryption.
    Key is derived from a master key using PBKDF2.

    Usage:
        from app.services.encryption import encryption_service

        # Encrypt
        encrypted = encryption_service.encrypt("sensitive@email.com")

        # Decrypt
        plaintext = encryption_service.decrypt(encrypted)
    """

    # Fernet tokens start with this prefix (base64 encoded version byte)
    FERNET_PREFIX = "gAAAAA"

    def __init__(self, encryption_key: str, encryption_salt: str):
        """
        Initialize encryption service with key derivation.

        Args:
            encryption_key: Master key for encryption (from settings)
            encryption_salt: Salt for key derivation (from settings)
        """
        self._encryption_key = encryption_key
        self._encryption_salt = encryption_salt
        self._fernet: Fernet | None = None

    def _get_fernet(self) -> Fernet:
        """Get or create Fernet instance with derived key."""
        if self._fernet is None:
            self._fernet = self._create_fernet()
        return self._fernet

    def _create_fernet(self) -> Fernet:
        """
        Create Fernet instance from encryption key using PBKDF2 key derivation.

        Uses 100,000 iterations of PBKDF2-HMAC-SHA256 for security.
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self._encryption_salt.encode("utf-8"),
            iterations=100000,
        )
        derived_key = kdf.derive(self._encryption_key.encode("utf-8"))
        key = base64.urlsafe_b64encode(derived_key)
        return Fernet(key)

    def encrypt(self, plaintext: str | None) -> str | None:
        """
        Encrypt a plaintext string value.

        Args:
            plaintext: String to encrypt, or None

        Returns:
            Encrypted string (Fernet token), or None if input was None
        """
        if plaintext is None:
            return None
        if not plaintext:
            return plaintext  # Empty string stays empty

        try:
            fernet = self._get_fernet()
            encrypted = fernet.encrypt(plaintext.encode("utf-8"))
            return encrypted.decode("utf-8")
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise ValueError("Failed to encrypt value") from e

    def decrypt(self, ciphertext: str | None) -> str | None:
        """
        Decrypt an encrypted string value.

        Handles both encrypted values and legacy plaintext values gracefully
        during migration periods.

        Args:
            ciphertext: Encrypted string (Fernet token) or plaintext, or None

        Returns:
            Decrypted plaintext string, or None if input was None
        """
        if ciphertext is None:
            return None
        if not ciphertext:
            return ciphertext  # Empty string stays empty

        # Check if this looks like an encrypted value
        if not ciphertext.startswith(self.FERNET_PREFIX):
            # Likely legacy plaintext data - return as-is
            # This allows graceful migration of existing data
            logger.debug("Value appears to be plaintext (legacy data)")
            return ciphertext

        try:
            fernet = self._get_fernet()
            decrypted = fernet.decrypt(ciphertext.encode("utf-8"))
            return decrypted.decode("utf-8")
        except InvalidToken:
            # If decryption fails but looks like Fernet token, it might be
            # encrypted with a different key - return as-is but log warning
            logger.warning("Failed to decrypt Fernet token - key mismatch?")
            return ciphertext
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            # Return as-is to avoid data loss
            return ciphertext

    def is_encrypted(self, value: str | None) -> bool:
        """
        Check if a value appears to be encrypted.

        Args:
            value: String value to check

        Returns:
            True if value looks like a Fernet token
        """
        if value is None or not value:
            return False
        return value.startswith(self.FERNET_PREFIX)

    def rotate_key(self, old_ciphertext: str, new_service: "EncryptionService") -> str:
        """
        Re-encrypt a value with a new key.

        Used for key rotation operations.

        Args:
            old_ciphertext: Value encrypted with current key
            new_service: EncryptionService instance with new key

        Returns:
            Value encrypted with new key
        """
        plaintext = self.decrypt(old_ciphertext)
        return new_service.encrypt(plaintext)


# ===========================================
# SINGLETON INSTANCE
# ===========================================

@lru_cache(maxsize=1)
def _get_encryption_service() -> EncryptionService:
    """
    Get cached encryption service instance.

    Loads encryption key and salt from settings.
    Uses lru_cache to ensure only one instance exists.
    """
    from app.config import settings

    return EncryptionService(
        encryption_key=settings.encryption_key,
        encryption_salt=settings.encryption_salt,
    )


def get_encryption_service() -> EncryptionService:
    """Get the encryption service singleton."""
    return _get_encryption_service()


# Convenience functions for direct use
def encrypt_pii(value: str | None) -> str | None:
    """
    Encrypt a PII field value.

    Usage:
        encrypted_email = encrypt_pii("user@example.com")
    """
    return get_encryption_service().encrypt(value)


def decrypt_pii(value: str | None) -> str | None:
    """
    Decrypt a PII field value.

    Usage:
        email = decrypt_pii(encrypted_email)
    """
    return get_encryption_service().decrypt(value)


def is_encrypted(value: str | None) -> bool:
    """
    Check if a value appears to be encrypted.

    Usage:
        if not is_encrypted(email):
            email = encrypt_pii(email)
    """
    return get_encryption_service().is_encrypted(value)
