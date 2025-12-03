"""
Get Clearance - Custom SQLAlchemy Types
=======================================
Custom SQLAlchemy column types for encrypted fields and other special types.
"""

from sqlalchemy import String, TypeDecorator


class EncryptedString(TypeDecorator):
    """
    SQLAlchemy type that encrypts/decrypts strings on database read/write.

    Uses application-level encryption via the encryption service.
    Encrypted values are stored as longer strings (Fernet tokens).

    Usage:
        class Applicant(Base):
            email: Mapped[str | None] = mapped_column(EncryptedString(512))
            phone: Mapped[str | None] = mapped_column(EncryptedString(256))

    Notes:
        - Encrypted values are ~1.4x longer than plaintext
        - Use larger column sizes to accommodate encryption overhead
        - Cannot use SQL LIKE queries on encrypted columns
        - Use hash columns for exact match lookups
    """

    impl = String
    cache_ok = True

    def __init__(self, length: int = 1024):
        """
        Initialize encrypted string type.

        Args:
            length: Maximum length of the encrypted value in database.
                   Should be ~1.4x the max plaintext length plus overhead.
                   Default 1024 handles most PII fields.
        """
        super().__init__(length)

    def process_bind_param(self, value, dialect):
        """
        Encrypt value before writing to database.

        Called when inserting or updating a row.
        """
        if value is None:
            return None

        # Import here to avoid circular imports during model definition
        from app.services.encryption import encrypt_pii

        return encrypt_pii(value)

    def process_result_value(self, value, dialect):
        """
        Decrypt value after reading from database.

        Called when loading a row from the database.
        """
        if value is None:
            return None

        # Import here to avoid circular imports during model definition
        from app.services.encryption import decrypt_pii

        return decrypt_pii(value)

    def copy(self, **kw):
        """Create a copy of this type."""
        return EncryptedString(self.impl.length)


class EncryptedJSON(TypeDecorator):
    """
    SQLAlchemy type that encrypts/decrypts JSON data on database read/write.

    Serializes JSON to string, encrypts it, and stores the result.
    On read, decrypts and deserializes back to Python dict/list.

    Usage:
        class Applicant(Base):
            address: Mapped[dict | None] = mapped_column(EncryptedJSON())

    Notes:
        - Use for structured PII like addresses
        - Cannot query individual JSON fields with SQL
        - Consider using separate encrypted string columns if you need field-level access
    """

    impl = String
    cache_ok = True

    def __init__(self, length: int = 4096):
        """
        Initialize encrypted JSON type.

        Args:
            length: Maximum length of the encrypted value in database.
                   JSON + encryption adds significant overhead.
                   Default 4096 handles most structured data.
        """
        super().__init__(length)

    def process_bind_param(self, value, dialect):
        """
        Serialize and encrypt JSON value before writing to database.
        """
        if value is None:
            return None

        import json
        from app.services.encryption import encrypt_pii

        json_str = json.dumps(value, separators=(",", ":"))
        return encrypt_pii(json_str)

    def process_result_value(self, value, dialect):
        """
        Decrypt and deserialize JSON value after reading from database.
        """
        if value is None:
            return None

        import json
        from app.services.encryption import decrypt_pii

        decrypted = decrypt_pii(value)
        if decrypted is None:
            return None

        try:
            return json.loads(decrypted)
        except json.JSONDecodeError:
            # If it's not valid JSON, it might be legacy unencrypted data
            # that was stored as a string representation
            return decrypted

    def copy(self, **kw):
        """Create a copy of this type."""
        return EncryptedJSON(self.impl.length)
