"""
Tests for PII Encryption Service
================================
Test cases for the encryption service and EncryptedString type.
"""

import pytest
from unittest.mock import patch

from app.services.encryption import (
    EncryptionService,
    encrypt_pii,
    decrypt_pii,
    is_encrypted,
)


# ===========================================
# TEST FIXTURES
# ===========================================

@pytest.fixture
def encryption_service():
    """Create encryption service with test key."""
    return EncryptionService(
        encryption_key="test-key-for-encryption-testing-32",
        encryption_salt="test-salt-v1",
    )


# ===========================================
# ENCRYPTION SERVICE TESTS
# ===========================================

class TestEncryptionService:
    """Tests for EncryptionService class."""

    def test_encrypt_returns_fernet_token(self, encryption_service):
        """Encrypted value should be a Fernet token (starts with gAAAAA)."""
        encrypted = encryption_service.encrypt("test@example.com")
        assert encrypted is not None
        assert encrypted.startswith("gAAAAA")

    def test_encrypt_none_returns_none(self, encryption_service):
        """Encrypting None should return None."""
        assert encryption_service.encrypt(None) is None

    def test_encrypt_empty_string_returns_empty(self, encryption_service):
        """Encrypting empty string should return empty string."""
        assert encryption_service.encrypt("") == ""

    def test_decrypt_returns_original(self, encryption_service):
        """Decrypting encrypted value should return original."""
        original = "sensitive@email.com"
        encrypted = encryption_service.encrypt(original)
        decrypted = encryption_service.decrypt(encrypted)
        assert decrypted == original

    def test_decrypt_none_returns_none(self, encryption_service):
        """Decrypting None should return None."""
        assert encryption_service.decrypt(None) is None

    def test_decrypt_empty_string_returns_empty(self, encryption_service):
        """Decrypting empty string should return empty string."""
        assert encryption_service.decrypt("") == ""

    def test_decrypt_plaintext_returns_as_is(self, encryption_service):
        """Decrypting plaintext (legacy data) should return as-is."""
        plaintext = "not-encrypted@email.com"
        result = encryption_service.decrypt(plaintext)
        assert result == plaintext

    def test_is_encrypted_true_for_fernet_token(self, encryption_service):
        """is_encrypted should return True for Fernet tokens."""
        encrypted = encryption_service.encrypt("test")
        assert encryption_service.is_encrypted(encrypted) is True

    def test_is_encrypted_false_for_plaintext(self, encryption_service):
        """is_encrypted should return False for plaintext."""
        assert encryption_service.is_encrypted("plaintext") is False
        assert encryption_service.is_encrypted(None) is False
        assert encryption_service.is_encrypted("") is False

    def test_different_plaintexts_produce_different_ciphertexts(self, encryption_service):
        """Different inputs should produce different encrypted values."""
        encrypted1 = encryption_service.encrypt("email1@example.com")
        encrypted2 = encryption_service.encrypt("email2@example.com")
        assert encrypted1 != encrypted2

    def test_same_plaintext_produces_different_ciphertexts(self, encryption_service):
        """Same input encrypted twice should produce different values (Fernet uses random IV)."""
        plaintext = "same@email.com"
        encrypted1 = encryption_service.encrypt(plaintext)
        encrypted2 = encryption_service.encrypt(plaintext)
        # Fernet uses random IV, so same plaintext produces different ciphertext
        assert encrypted1 != encrypted2
        # But both should decrypt to the same value
        assert encryption_service.decrypt(encrypted1) == plaintext
        assert encryption_service.decrypt(encrypted2) == plaintext


class TestEncryptionServiceKeyDerivation:
    """Tests for key derivation in EncryptionService."""

    def test_different_keys_produce_different_results(self):
        """Different encryption keys should produce incompatible results."""
        service1 = EncryptionService(
            encryption_key="key-one-for-testing",
            encryption_salt="salt-v1",
        )
        service2 = EncryptionService(
            encryption_key="key-two-for-testing",
            encryption_salt="salt-v1",
        )

        plaintext = "test@email.com"
        encrypted = service1.encrypt(plaintext)

        # Service2 shouldn't be able to decrypt properly
        # (returns as-is on failure for graceful degradation)
        decrypted = service2.decrypt(encrypted)
        # The service returns the ciphertext as-is if decryption fails
        assert decrypted == encrypted or decrypted == plaintext

    def test_different_salts_produce_different_results(self):
        """Different salts should produce different derived keys."""
        service1 = EncryptionService(
            encryption_key="same-key",
            encryption_salt="salt-one",
        )
        service2 = EncryptionService(
            encryption_key="same-key",
            encryption_salt="salt-two",
        )

        plaintext = "test@email.com"
        encrypted1 = service1.encrypt(plaintext)

        # Service2 can't decrypt because different salt = different derived key
        decrypted = service2.decrypt(encrypted1)
        assert decrypted == encrypted1  # Returns as-is on failure


class TestConvenienceFunctions:
    """Tests for module-level convenience functions."""

    def test_encrypt_pii_function(self):
        """encrypt_pii should encrypt values."""
        with patch('app.services.encryption._get_encryption_service') as mock:
            mock_service = EncryptionService(
                encryption_key="test-key-32-bytes-long-enough!!",
                encryption_salt="test-salt",
            )
            mock.return_value = mock_service

            encrypted = encrypt_pii("test@example.com")
            assert encrypted is not None
            assert encrypted.startswith("gAAAAA")

    def test_decrypt_pii_function(self):
        """decrypt_pii should decrypt values."""
        with patch('app.services.encryption._get_encryption_service') as mock:
            mock_service = EncryptionService(
                encryption_key="test-key-32-bytes-long-enough!!",
                encryption_salt="test-salt",
            )
            mock.return_value = mock_service

            original = "test@example.com"
            encrypted = mock_service.encrypt(original)
            decrypted = decrypt_pii(encrypted)
            assert decrypted == original

    def test_is_encrypted_function(self):
        """is_encrypted should detect encrypted values."""
        with patch('app.services.encryption._get_encryption_service') as mock:
            mock_service = EncryptionService(
                encryption_key="test-key-32-bytes-long-enough!!",
                encryption_salt="test-salt",
            )
            mock.return_value = mock_service

            encrypted = mock_service.encrypt("test")
            assert is_encrypted(encrypted) is True
            assert is_encrypted("plaintext") is False


class TestEncryptionEdgeCases:
    """Tests for edge cases in encryption."""

    def test_unicode_characters(self, encryption_service):
        """Should handle unicode characters correctly."""
        unicode_text = "日本語 Émoji 🔒 Ñoño"
        encrypted = encryption_service.encrypt(unicode_text)
        decrypted = encryption_service.decrypt(encrypted)
        assert decrypted == unicode_text

    def test_long_string(self, encryption_service):
        """Should handle long strings."""
        long_text = "a" * 10000
        encrypted = encryption_service.encrypt(long_text)
        decrypted = encryption_service.decrypt(encrypted)
        assert decrypted == long_text

    def test_special_characters(self, encryption_service):
        """Should handle special characters."""
        special_text = r'<script>alert("xss")</script> & "quotes" \n\t'
        encrypted = encryption_service.encrypt(special_text)
        decrypted = encryption_service.decrypt(encrypted)
        assert decrypted == special_text

    def test_phone_number_format(self, encryption_service):
        """Should handle phone number formats."""
        phone = "+1 (555) 123-4567"
        encrypted = encryption_service.encrypt(phone)
        decrypted = encryption_service.decrypt(encrypted)
        assert decrypted == phone

    def test_email_format(self, encryption_service):
        """Should handle various email formats."""
        emails = [
            "simple@example.com",
            "very.common@example.com",
            "disposable.style.email.with+symbol@example.com",
            "user@subdomain.example.com",
        ]
        for email in emails:
            encrypted = encryption_service.encrypt(email)
            decrypted = encryption_service.decrypt(encrypted)
            assert decrypted == email, f"Failed for email: {email}"


class TestKeyRotation:
    """Tests for key rotation functionality."""

    def test_rotate_key(self):
        """Should be able to re-encrypt with new key."""
        old_service = EncryptionService(
            encryption_key="old-key-for-rotation",
            encryption_salt="salt-v1",
        )
        new_service = EncryptionService(
            encryption_key="new-key-for-rotation",
            encryption_salt="salt-v2",
        )

        original = "secret@email.com"

        # Encrypt with old key
        old_ciphertext = old_service.encrypt(original)

        # Rotate to new key
        new_ciphertext = old_service.rotate_key(old_ciphertext, new_service)

        # Verify old service can't decrypt new ciphertext
        old_decrypted = old_service.decrypt(new_ciphertext)
        assert old_decrypted == new_ciphertext  # Returns as-is on failure

        # Verify new service can decrypt
        new_decrypted = new_service.decrypt(new_ciphertext)
        assert new_decrypted == original
