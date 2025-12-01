"""
Get Clearance - OCR Service
============================
AWS Textract integration for document text extraction.

Provides OCR capabilities for:
- Passport text extraction
- ID card text extraction
- Driver's license text extraction
- General document OCR

Includes quality detection:
- Blur detection (Laplacian variance)
- Resolution checks
- Glare detection (histogram analysis)

Usage:
    result = await ocr_service.extract_text(document_id)
    # Returns: {ocr_text, extracted_data, quality_issues, ocr_confidence}
"""

import io
import logging
from datetime import datetime
from typing import Any
from uuid import UUID

import aioboto3
import httpx
import numpy as np
from botocore.config import Config as BotoConfig
from botocore.exceptions import ClientError

from app.config import settings
from app.services.storage import storage_service, StorageDownloadError

logger = logging.getLogger(__name__)


class OCRServiceError(Exception):
    """Raised when OCR API fails."""
    pass


class OCRConfigError(Exception):
    """Raised when AWS is not configured."""
    pass


class OCRService:
    """
    Service for document OCR via AWS Textract.

    Downloads documents from R2 storage, processes with Textract,
    and returns extracted text and structured data.

    Usage:
        result = await ocr_service.extract_text(
            storage_key="tenants/abc/documents/passport.jpg",
            document_type="passport"
        )
    """

    def __init__(
        self,
        access_key_id: str | None = None,
        secret_access_key: str | None = None,
        region: str | None = None,
        timeout: int | None = None,
    ):
        self.access_key_id = access_key_id or settings.aws_access_key_id
        self.secret_access_key = secret_access_key or settings.aws_secret_access_key
        self.region = region or settings.aws_region
        self.timeout = timeout or settings.aws_textract_timeout

        self._session: aioboto3.Session | None = None

    @property
    def is_configured(self) -> bool:
        """Check if service is properly configured."""
        return bool(self.access_key_id and self.secret_access_key)

    def _get_session(self) -> aioboto3.Session:
        """Get or create aioboto3 session."""
        if self._session is None:
            self._session = aioboto3.Session(
                aws_access_key_id=self.access_key_id,
                aws_secret_access_key=self.secret_access_key,
                region_name=self.region,
            )
        return self._session

    def _get_client_config(self) -> BotoConfig:
        """Get boto3 client configuration."""
        return BotoConfig(
            connect_timeout=10,
            read_timeout=self.timeout,
            retries={"max_attempts": 3, "mode": "adaptive"},
        )

    async def _download_document(self, storage_key: str) -> bytes:
        """
        Download document bytes from R2 storage.

        Args:
            storage_key: Storage path in R2

        Returns:
            Document bytes

        Raises:
            OCRServiceError: If download fails
        """
        try:
            # Get presigned download URL
            download_url = await storage_service.create_presigned_download(
                key=storage_key,
                expires_in=300,  # 5 minutes
            )

            # Download the file
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(download_url)
                response.raise_for_status()
                return response.content

        except StorageDownloadError as e:
            logger.error(f"Failed to get download URL for {storage_key}: {e}")
            raise OCRServiceError(f"Failed to download document: {e}")
        except httpx.HTTPError as e:
            logger.error(f"Failed to download document from R2: {e}")
            raise OCRServiceError(f"Failed to download document: {e}")

    def _detect_quality_issues(self, image_bytes: bytes) -> list[dict[str, Any]]:
        """
        Detect image quality issues using OpenCV.

        Checks for:
        - Blur (Laplacian variance < 100)
        - Low resolution (< 640x480)
        - Glare (bright spots > threshold)

        Args:
            image_bytes: Raw image bytes

        Returns:
            List of quality issues with severity
        """
        issues = []

        try:
            # Import cv2 here to avoid startup cost if not used
            import cv2

            # Decode image
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if img is None:
                return [{"issue": "invalid_image", "severity": "high", "confidence": 100}]

            height, width = img.shape[:2]
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            # Check blur using Laplacian variance
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            if laplacian_var < 100:
                severity = "high" if laplacian_var < 50 else "medium"
                issues.append({
                    "issue": "blur",
                    "severity": severity,
                    "confidence": int(100 - laplacian_var),
                    "details": f"Laplacian variance: {laplacian_var:.2f}",
                })
            elif laplacian_var < 200:
                issues.append({
                    "issue": "slight_blur",
                    "severity": "low",
                    "confidence": int(max(0, 100 - (laplacian_var - 100))),
                    "details": f"Laplacian variance: {laplacian_var:.2f}",
                })

            # Check resolution
            if width < 640 or height < 480:
                issues.append({
                    "issue": "low_resolution",
                    "severity": "medium",
                    "confidence": 85,
                    "details": f"Resolution: {width}x{height}",
                })

            # Check for glare using histogram analysis
            hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
            bright_pixels = np.sum(hist[230:256])  # Pixels with value > 230
            total_pixels = gray.size
            bright_ratio = bright_pixels / total_pixels

            if bright_ratio > 0.15:  # More than 15% very bright pixels
                severity = "high" if bright_ratio > 0.25 else "medium"
                issues.append({
                    "issue": "glare",
                    "severity": severity,
                    "confidence": int(min(100, bright_ratio * 300)),
                    "details": f"Bright pixel ratio: {bright_ratio:.2%}",
                })

        except ImportError:
            logger.warning("OpenCV not installed, skipping quality checks")
        except Exception as e:
            logger.warning(f"Quality check failed: {e}")

        return issues

    async def extract_text(
        self,
        storage_key: str,
        document_type: str = "unknown",
        check_quality: bool = True,
    ) -> dict[str, Any]:
        """
        Extract text from a document using AWS Textract.

        Downloads document from R2, sends to Textract, and returns
        extracted text with structured data.

        Args:
            storage_key: R2 storage path for the document
            document_type: Type of document (passport, drivers_license, etc.)
            check_quality: Whether to run quality checks

        Returns:
            Dict with:
                - ocr_text: Full extracted text
                - extracted_data: Structured fields (name, DOB, etc.)
                - quality_issues: List of quality problems detected
                - ocr_confidence: Overall confidence score (0-100)

        Raises:
            OCRConfigError: If AWS is not configured
            OCRServiceError: If OCR processing fails
        """
        if not self.is_configured:
            raise OCRConfigError("AWS Textract not configured")

        logger.info(f"Starting OCR for document: {storage_key}")

        # Download document
        doc_bytes = await self._download_document(storage_key)

        # Check quality if enabled
        quality_issues = []
        if check_quality and not storage_key.lower().endswith('.pdf'):
            quality_issues = self._detect_quality_issues(doc_bytes)

        # Call Textract
        session = self._get_session()
        config = self._get_client_config()

        try:
            async with session.client(
                "textract",
                region_name=self.region,
                config=config,
            ) as textract:
                # Use detect_document_text for images
                # For PDFs, would need to use start_document_text_detection
                response = await textract.detect_document_text(
                    Document={"Bytes": doc_bytes}
                )

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            error_msg = e.response.get("Error", {}).get("Message", str(e))
            logger.error(f"Textract API error: {error_code} - {error_msg}")
            raise OCRServiceError(f"Textract API failed: {error_msg}")
        except Exception as e:
            logger.error(f"Unexpected Textract error: {e}")
            raise OCRServiceError(f"OCR processing failed: {e}")

        # Parse Textract response
        result = self._parse_textract_response(response, document_type)
        result["quality_issues"] = quality_issues

        # Adjust confidence based on quality issues
        if quality_issues:
            high_severity_count = sum(1 for i in quality_issues if i["severity"] == "high")
            result["ocr_confidence"] = max(0, result["ocr_confidence"] - (high_severity_count * 15))

        logger.info(
            f"OCR complete for {storage_key}: "
            f"confidence={result['ocr_confidence']}, "
            f"quality_issues={len(quality_issues)}"
        )

        return result

    def _parse_textract_response(
        self,
        response: dict[str, Any],
        document_type: str,
    ) -> dict[str, Any]:
        """
        Parse Textract response into structured format.

        Args:
            response: Raw Textract API response
            document_type: Type of document for field extraction

        Returns:
            Dict with ocr_text, extracted_data, ocr_confidence
        """
        blocks = response.get("Blocks", [])

        # Extract all text lines
        lines = []
        total_confidence = 0.0
        line_count = 0

        for block in blocks:
            if block["BlockType"] == "LINE":
                text = block.get("Text", "")
                confidence = block.get("Confidence", 0)
                lines.append(text)
                total_confidence += confidence
                line_count += 1

        ocr_text = "\n".join(lines)
        avg_confidence = total_confidence / line_count if line_count > 0 else 0

        # Extract structured data based on document type
        extracted_data = self._extract_structured_data(lines, document_type)

        return {
            "ocr_text": ocr_text,
            "extracted_data": extracted_data,
            "ocr_confidence": int(avg_confidence),
        }

    def _extract_structured_data(
        self,
        lines: list[str],
        document_type: str,
    ) -> dict[str, Any]:
        """
        Extract structured fields from OCR text.

        Uses pattern matching to find common document fields.

        Args:
            lines: List of text lines from OCR
            document_type: Type of document

        Returns:
            Dict with extracted fields
        """
        import re

        data: dict[str, Any] = {}
        full_text = " ".join(lines).upper()

        # Common patterns
        patterns = {
            # Date patterns: DD/MM/YYYY, MM/DD/YYYY, YYYY-MM-DD, DD-MMM-YYYY
            "date": r"\b(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4}|\d{4}[/\-\.]\d{1,2}[/\-\.]\d{1,2}|\d{1,2}[/\-\.](?:JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)[/\-\.]\d{2,4})\b",
            # Document number patterns
            "doc_number": r"\b([A-Z]{1,2}\d{6,9}|\d{9,12})\b",
            # Name patterns (ALL CAPS, multiple words)
            "name": r"\b([A-Z][A-Z]+(?:\s+[A-Z][A-Z]+)+)\b",
        }

        # Extract dates
        dates = re.findall(patterns["date"], full_text, re.IGNORECASE)
        if dates:
            # Try to identify which date is DOB vs expiry
            for i, date_str in enumerate(dates[:3]):
                parsed = self._parse_date(date_str)
                if parsed:
                    if i == 0:
                        # First date often is DOB
                        data["date_of_birth"] = parsed
                    elif i == 1 and "date_of_birth" in data:
                        # Second date often is expiry
                        data["expiry_date"] = parsed

        # Look for specific labels
        for line in lines:
            line_upper = line.upper().strip()

            # Date of birth labels
            if any(label in line_upper for label in ["DOB", "BIRTH", "BORN", "DATE OF BIRTH"]):
                match = re.search(patterns["date"], line_upper)
                if match:
                    parsed = self._parse_date(match.group(1))
                    if parsed:
                        data["date_of_birth"] = parsed

            # Expiry labels
            if any(label in line_upper for label in ["EXP", "EXPIRY", "VALID UNTIL", "EXPIRES"]):
                match = re.search(patterns["date"], line_upper)
                if match:
                    parsed = self._parse_date(match.group(1))
                    if parsed:
                        data["expiry_date"] = parsed

            # Document number
            if any(label in line_upper for label in ["PASSPORT NO", "LICENSE NO", "DOCUMENT NO", "ID NO"]):
                match = re.search(patterns["doc_number"], line_upper)
                if match:
                    data["document_number"] = match.group(1)

            # Nationality
            if any(label in line_upper for label in ["NATIONALITY", "CITIZEN"]):
                # Extract 3-letter country code or full name
                code_match = re.search(r"\b([A-Z]{3})\b", line_upper)
                if code_match and code_match.group(1) not in ["THE", "AND", "FOR"]:
                    data["nationality"] = code_match.group(1)

            # Sex/Gender
            if any(label in line_upper for label in ["SEX", "GENDER"]):
                if "M" in line_upper and "F" not in line_upper:
                    data["sex"] = "M"
                elif "F" in line_upper:
                    data["sex"] = "F"

        # Try to extract document number if not found
        if "document_number" not in data:
            numbers = re.findall(patterns["doc_number"], full_text)
            if numbers:
                # Take the first plausible document number
                for num in numbers:
                    if len(num) >= 6:
                        data["document_number"] = num
                        break

        # Try to extract name
        if "full_name" not in data:
            # Look for name patterns near common labels
            for i, line in enumerate(lines):
                line_upper = line.upper().strip()
                if any(label in line_upper for label in ["SURNAME", "GIVEN NAME", "NAME"]):
                    # Check next line or same line
                    name_parts = []
                    for check_line in [line] + lines[i+1:i+3] if i < len(lines) - 1 else [line]:
                        names = re.findall(r"\b([A-Z][A-Z]+)\b", check_line.upper())
                        name_parts.extend([n for n in names if len(n) > 1 and n not in ["NAME", "SURNAME", "GIVEN", "THE"]])
                    if name_parts:
                        data["full_name"] = " ".join(name_parts[:5])  # Max 5 name parts
                        break

        # For passports, look for MRZ
        if document_type == "passport":
            mrz_lines = self._extract_mrz(lines)
            if mrz_lines:
                data["mrz_lines"] = mrz_lines

        return data

    def _parse_date(self, date_str: str) -> str | None:
        """
        Parse date string to ISO format (YYYY-MM-DD).

        Args:
            date_str: Date string in various formats

        Returns:
            ISO date string or None if parsing fails
        """
        from datetime import datetime

        formats = [
            "%d/%m/%Y", "%m/%d/%Y", "%Y-%m-%d",
            "%d-%m-%Y", "%d.%m.%Y", "%Y/%m/%d",
            "%d-%b-%Y", "%d/%b/%Y",
        ]

        date_str = date_str.strip().upper()

        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue

        return None

    def _extract_mrz(self, lines: list[str]) -> list[str] | None:
        """
        Extract MRZ (Machine Readable Zone) from OCR lines.

        MRZ is typically at the bottom of passport, 2 lines of 44 chars each.

        Args:
            lines: OCR text lines

        Returns:
            List of 2 MRZ lines or None if not found
        """
        import re

        mrz_pattern = r"^[A-Z0-9<]{30,44}$"
        mrz_lines = []

        for line in lines:
            # Clean the line
            clean = line.upper().replace(" ", "").replace("O", "0").strip()

            # Check if it looks like MRZ
            if re.match(mrz_pattern, clean):
                mrz_lines.append(clean)

        # Return only if we found exactly 2 lines of proper length
        if len(mrz_lines) >= 2:
            # Find the two longest lines (should be 44 chars each for passports)
            mrz_lines.sort(key=len, reverse=True)
            if len(mrz_lines[0]) >= 30 and len(mrz_lines[1]) >= 30:
                return mrz_lines[:2]

        return None

    async def analyze_document_async(
        self,
        storage_key: str,
        document_type: str = "unknown",
    ) -> dict[str, Any]:
        """
        Analyze document using Textract's AnalyzeDocument API.

        This provides more detailed analysis including forms and tables.
        Use for complex documents requiring field extraction.

        Args:
            storage_key: R2 storage path
            document_type: Document type hint

        Returns:
            Analysis results with forms and tables
        """
        if not self.is_configured:
            raise OCRConfigError("AWS Textract not configured")

        doc_bytes = await self._download_document(storage_key)

        session = self._get_session()
        config = self._get_client_config()

        try:
            async with session.client(
                "textract",
                region_name=self.region,
                config=config,
            ) as textract:
                response = await textract.analyze_document(
                    Document={"Bytes": doc_bytes},
                    FeatureTypes=["FORMS", "TABLES"],
                )

        except ClientError as e:
            error_msg = e.response.get("Error", {}).get("Message", str(e))
            raise OCRServiceError(f"Textract analysis failed: {error_msg}")

        return self._parse_analyze_response(response)

    def _parse_analyze_response(
        self,
        response: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Parse AnalyzeDocument response.

        Extracts key-value pairs from forms and table data.
        """
        blocks = response.get("Blocks", [])

        # Build block map for relationship lookup
        block_map = {b["Id"]: b for b in blocks}

        # Extract key-value pairs
        key_values = {}
        for block in blocks:
            if block["BlockType"] == "KEY_VALUE_SET" and "KEY" in block.get("EntityTypes", []):
                key_text = self._get_text_from_block(block, block_map)
                value_block = self._get_value_block(block, block_map)
                if value_block:
                    value_text = self._get_text_from_block(value_block, block_map)
                    if key_text and value_text:
                        key_values[key_text.strip()] = value_text.strip()

        # Extract tables
        tables = []
        for block in blocks:
            if block["BlockType"] == "TABLE":
                table = self._extract_table(block, block_map)
                if table:
                    tables.append(table)

        return {
            "key_values": key_values,
            "tables": tables,
        }

    def _get_text_from_block(
        self,
        block: dict[str, Any],
        block_map: dict[str, Any],
    ) -> str:
        """Get text content from a block and its children."""
        text_parts = []

        if "Relationships" in block:
            for rel in block["Relationships"]:
                if rel["Type"] == "CHILD":
                    for child_id in rel["Ids"]:
                        child = block_map.get(child_id)
                        if child and child["BlockType"] == "WORD":
                            text_parts.append(child.get("Text", ""))

        return " ".join(text_parts)

    def _get_value_block(
        self,
        key_block: dict[str, Any],
        block_map: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Get the VALUE block associated with a KEY block."""
        if "Relationships" in key_block:
            for rel in key_block["Relationships"]:
                if rel["Type"] == "VALUE":
                    for value_id in rel["Ids"]:
                        return block_map.get(value_id)
        return None

    def _extract_table(
        self,
        table_block: dict[str, Any],
        block_map: dict[str, Any],
    ) -> list[list[str]] | None:
        """Extract table data as 2D list."""
        if "Relationships" not in table_block:
            return None

        cells = {}
        for rel in table_block["Relationships"]:
            if rel["Type"] == "CHILD":
                for cell_id in rel["Ids"]:
                    cell = block_map.get(cell_id)
                    if cell and cell["BlockType"] == "CELL":
                        row_idx = cell.get("RowIndex", 1) - 1
                        col_idx = cell.get("ColumnIndex", 1) - 1
                        text = self._get_text_from_block(cell, block_map)
                        cells[(row_idx, col_idx)] = text

        if not cells:
            return None

        # Build table
        max_row = max(r for r, c in cells.keys()) + 1
        max_col = max(c for r, c in cells.keys()) + 1
        table = [["" for _ in range(max_col)] for _ in range(max_row)]

        for (row, col), text in cells.items():
            table[row][col] = text

        return table


# ===========================================
# SINGLETON INSTANCE
# ===========================================

ocr_service = OCRService()
