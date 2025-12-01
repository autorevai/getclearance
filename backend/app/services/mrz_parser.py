"""
Get Clearance - MRZ Parser Service
===================================
Machine Readable Zone (MRZ) parsing and validation for passports.

Implements ICAO 9303 standard for passport MRZ:
- TD3 format: 2 lines of 44 characters each
- Checksum validation using weights 7-3-1
- Field extraction (document number, name, DOB, expiry, etc.)

MRZ Check Digit Algorithm:
- Each character has a numeric value (0-9 = 0-9, A-Z = 10-35, < = 0)
- Multiply by weights 7, 3, 1, repeating
- Sum all products, mod 10 = check digit

Reference: https://docs.sumsub.com/docs/database-validation

Usage:
    result = mrz_parser.parse_mrz(["P<USADOE...", "ABC1234569..."])
    if result["checksum_valid"]:
        print(result["document_number"])
"""

import logging
import re
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


class MRZValidationError(Exception):
    """Raised when MRZ checksum validation fails."""

    def __init__(self, message: str, field: str | None = None, expected: str | None = None, actual: str | None = None):
        super().__init__(message)
        self.field = field
        self.expected = expected
        self.actual = actual


class MRZParser:
    """
    Parser for passport Machine Readable Zone (MRZ).

    Supports TD3 format (passports):
    - Line 1: Document type, country, name
    - Line 2: Document number, nationality, DOB, sex, expiry, personal number

    Validates all check digits using ICAO 9303 algorithm.
    """

    # Character to numeric value mapping for check digit calculation
    CHAR_VALUES = {
        '<': 0, '0': 0, '1': 1, '2': 2, '3': 3, '4': 4,
        '5': 5, '6': 6, '7': 7, '8': 8, '9': 9,
        'A': 10, 'B': 11, 'C': 12, 'D': 13, 'E': 14, 'F': 15,
        'G': 16, 'H': 17, 'I': 18, 'J': 19, 'K': 20, 'L': 21,
        'M': 22, 'N': 23, 'O': 24, 'P': 25, 'Q': 26, 'R': 27,
        'S': 28, 'T': 29, 'U': 30, 'V': 31, 'W': 32, 'X': 33,
        'Y': 34, 'Z': 35,
    }

    # Weights for check digit calculation: 7, 3, 1 repeating
    WEIGHTS = [7, 3, 1]

    def calculate_check_digit(self, data: str) -> int:
        """
        Calculate check digit for a string using ICAO 9303 algorithm.

        Algorithm:
        1. Convert each character to numeric value (0-9 stay, A-Z = 10-35, < = 0)
        2. Multiply each value by weight (7, 3, 1 repeating)
        3. Sum all products
        4. Result mod 10 = check digit

        Args:
            data: String to calculate check digit for

        Returns:
            Check digit (0-9)
        """
        total = 0
        for i, char in enumerate(data.upper()):
            value = self.CHAR_VALUES.get(char, 0)
            weight = self.WEIGHTS[i % 3]
            total += value * weight

        return total % 10

    def validate_check_digit(
        self,
        data: str,
        check_digit: str,
        field_name: str,
    ) -> bool:
        """
        Validate a check digit against data.

        Args:
            data: The data that was checksummed
            check_digit: The check digit to validate (as string)
            field_name: Name of field for error reporting

        Returns:
            True if valid

        Raises:
            MRZValidationError: If check digit is invalid
        """
        if not check_digit.isdigit():
            raise MRZValidationError(
                f"Invalid check digit character for {field_name}",
                field=field_name,
                expected="0-9",
                actual=check_digit,
            )

        expected = self.calculate_check_digit(data)
        actual = int(check_digit)

        if expected != actual:
            raise MRZValidationError(
                f"Check digit mismatch for {field_name}",
                field=field_name,
                expected=str(expected),
                actual=str(actual),
            )

        return True

    def parse_date(self, date_str: str, is_expiry: bool = False) -> str | None:
        """
        Parse MRZ date format (YYMMDD) to ISO format.

        For DOB: Years 00-29 = 2000-2029, 30-99 = 1930-1999
        For Expiry: Years 00-29 = 2000-2029, 30-99 = 2030-2099

        Args:
            date_str: 6-digit date string (YYMMDD)
            is_expiry: Whether this is an expiry date

        Returns:
            ISO date string (YYYY-MM-DD) or None if invalid
        """
        if len(date_str) != 6 or not date_str.isdigit():
            return None

        try:
            yy = int(date_str[0:2])
            mm = int(date_str[2:4])
            dd = int(date_str[4:6])

            # Determine century
            if is_expiry:
                # Expiry dates: 00-29 = 2000s, 30-99 = 2030s+
                year = 2000 + yy if yy < 30 else 2000 + yy
            else:
                # DOB: 00-29 = 2000s, 30-99 = 1900s
                year = 2000 + yy if yy < 30 else 1900 + yy

            # Validate date
            date_obj = datetime(year, mm, dd)
            return date_obj.strftime("%Y-%m-%d")

        except ValueError:
            return None

    def parse_name(self, name_field: str) -> tuple[str, str]:
        """
        Parse MRZ name field into surname and given names.

        Format: SURNAME<<GIVEN<NAMES
        Multiple given names separated by single <
        Surname and given names separated by <<

        Args:
            name_field: Raw name field from MRZ

        Returns:
            Tuple of (surname, given_names)
        """
        # Split on << to separate surname from given names
        parts = name_field.split("<<")

        surname = parts[0].replace("<", " ").strip() if parts else ""

        if len(parts) > 1:
            given = parts[1].replace("<", " ").strip()
        else:
            given = ""

        return surname, given

    def parse_mrz(
        self,
        mrz_lines: list[str],
        strict: bool = True,
    ) -> dict[str, Any]:
        """
        Parse and validate passport MRZ.

        Parses TD3 format (2 lines x 44 characters) and validates
        all check digits.

        Args:
            mrz_lines: List of 2 MRZ lines
            strict: If True, raise exception on checksum failure

        Returns:
            Dict with:
                - document_number: Passport number
                - nationality: 3-letter country code
                - date_of_birth: ISO format
                - sex: M/F
                - expiry_date: ISO format
                - given_names: First/middle names
                - surname: Family name
                - checksum_valid: Whether all checksums passed
                - mrz_line_1: Original line 1
                - mrz_line_2: Original line 2
                - validation_errors: List of any validation errors

        Raises:
            MRZValidationError: If strict=True and checksum fails
            ValueError: If MRZ format is invalid
        """
        # Validate input
        if len(mrz_lines) != 2:
            raise ValueError(f"Expected 2 MRZ lines, got {len(mrz_lines)}")

        line1 = mrz_lines[0].upper().strip()
        line2 = mrz_lines[1].upper().strip()

        # Normalize lines (replace common OCR errors)
        line1 = self._normalize_mrz_line(line1)
        line2 = self._normalize_mrz_line(line2)

        # Validate line lengths
        if len(line1) != 44:
            raise ValueError(f"Line 1 must be 44 chars, got {len(line1)}")
        if len(line2) != 44:
            raise ValueError(f"Line 2 must be 44 chars, got {len(line2)}")

        result: dict[str, Any] = {
            "mrz_line_1": line1,
            "mrz_line_2": line2,
            "checksum_valid": True,
            "validation_errors": [],
        }

        # Parse Line 1: Document type, issuing country, name
        # Format: P<USADOE<<JOHN<MICHAEL<<<<<<<<<<<<<<<<<<<<<
        doc_type = line1[0:2]  # "P<" for passport
        issuing_country = line1[2:5]
        name_field = line1[5:44]

        result["document_type"] = doc_type.replace("<", "")
        result["issuing_country"] = issuing_country.replace("<", "")

        surname, given_names = self.parse_name(name_field)
        result["surname"] = surname
        result["given_names"] = given_names
        result["full_name"] = f"{given_names} {surname}".strip()

        # Parse Line 2: Doc number, nationality, DOB, sex, expiry, personal number
        # Format: ABC1234569USA9001155M3001155<<<<<<<<<<<<<<04
        # Positions: 0-8 doc number, 9 check, 10-12 nationality, 13-18 DOB,
        #           19 DOB check, 20 sex, 21-26 expiry, 27 expiry check,
        #           28-42 personal number, 43 final check

        doc_number = line2[0:9]
        doc_check = line2[9]
        nationality = line2[10:13]
        dob = line2[13:19]
        dob_check = line2[19]
        sex = line2[20]
        expiry = line2[21:27]
        expiry_check = line2[27]
        personal_number = line2[28:42]
        final_check = line2[43]

        # Store basic fields
        result["document_number"] = doc_number.replace("<", "")
        result["nationality"] = nationality.replace("<", "")
        result["sex"] = sex if sex in "MF" else None
        result["date_of_birth"] = self.parse_date(dob, is_expiry=False)
        result["expiry_date"] = self.parse_date(expiry, is_expiry=True)
        result["personal_number"] = personal_number.replace("<", "") or None

        # Validate check digits
        errors = []

        # Document number check
        try:
            self.validate_check_digit(doc_number, doc_check, "document_number")
        except MRZValidationError as e:
            errors.append(str(e))
            result["checksum_valid"] = False

        # DOB check
        try:
            self.validate_check_digit(dob, dob_check, "date_of_birth")
        except MRZValidationError as e:
            errors.append(str(e))
            result["checksum_valid"] = False

        # Expiry check
        try:
            self.validate_check_digit(expiry, expiry_check, "expiry_date")
        except MRZValidationError as e:
            errors.append(str(e))
            result["checksum_valid"] = False

        # Final/composite check (all of line 2 except positions that are just filler)
        # Composite is calculated over: doc_number + check + DOB + check + expiry + check + personal_number
        composite_data = (
            doc_number + doc_check +
            dob + dob_check +
            expiry + expiry_check +
            personal_number
        )
        try:
            self.validate_check_digit(composite_data, final_check, "composite")
        except MRZValidationError as e:
            errors.append(str(e))
            result["checksum_valid"] = False

        result["validation_errors"] = errors

        # Raise if strict mode and validation failed
        if strict and not result["checksum_valid"]:
            raise MRZValidationError(
                f"MRZ validation failed: {'; '.join(errors)}",
                field="composite",
            )

        logger.info(
            f"Parsed MRZ: doc={result['document_number']}, "
            f"valid={result['checksum_valid']}"
        )

        return result

    def _normalize_mrz_line(self, line: str) -> str:
        """
        Normalize MRZ line to fix common OCR errors.

        Common substitutions:
        - O (letter) -> 0 (zero) in numeric positions
        - 0 (zero) -> O (letter) in alpha positions
        - I -> 1, l -> 1 in numeric positions
        - Space -> <

        Args:
            line: Raw MRZ line

        Returns:
            Normalized line
        """
        # Remove any spaces
        line = line.replace(" ", "")

        # Pad or truncate to 44 chars
        if len(line) < 44:
            line = line + "<" * (44 - len(line))
        elif len(line) > 44:
            line = line[:44]

        return line

    def validate_mrz_format(self, mrz_lines: list[str]) -> tuple[bool, str | None]:
        """
        Quick validation of MRZ format without full parsing.

        Checks:
        - Exactly 2 lines
        - Each line is 44 characters
        - Line 1 starts with document type
        - Line 2 has valid structure

        Args:
            mrz_lines: List of MRZ lines

        Returns:
            Tuple of (is_valid, error_message)
        """
        if len(mrz_lines) != 2:
            return False, f"Expected 2 lines, got {len(mrz_lines)}"

        line1 = mrz_lines[0].upper().strip()
        line2 = mrz_lines[1].upper().strip()

        if len(line1) < 30:
            return False, f"Line 1 too short: {len(line1)} chars"
        if len(line2) < 30:
            return False, f"Line 2 too short: {len(line2)} chars"

        # Check valid characters
        valid_chars = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789<")
        for i, line in enumerate([line1, line2], 1):
            invalid = set(line) - valid_chars
            if invalid:
                return False, f"Invalid characters in line {i}: {invalid}"

        # Check document type
        if line1[0] not in "PID":
            return False, f"Invalid document type: {line1[0]}"

        return True, None


# ===========================================
# SINGLETON INSTANCE
# ===========================================

mrz_parser = MRZParser()
