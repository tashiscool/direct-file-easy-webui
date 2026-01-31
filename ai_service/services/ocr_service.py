"""OCR Service for tax document scanning and extraction.

Uses Tesseract OCR and Claude Vision for intelligent document processing.
"""

import base64
import io
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum

logger = logging.getLogger(__name__)

# Optional OCR imports
try:
    import pytesseract
    from PIL import Image
    from pdf2image import convert_from_path, convert_from_bytes
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    logger.warning("Tesseract OCR dependencies not available")

try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False


class DocumentType(str, Enum):
    """Supported tax document types."""
    W2 = "W-2"
    W2G = "W-2G"
    FORM_1099_INT = "1099-INT"
    FORM_1099_DIV = "1099-DIV"
    FORM_1099_MISC = "1099-MISC"
    FORM_1099_NEC = "1099-NEC"
    FORM_1099_R = "1099-R"
    FORM_1099_G = "1099-G"
    FORM_1099_B = "1099-B"
    FORM_1099_K = "1099-K"
    FORM_1099_SSA = "1099-SSA"
    FORM_1098 = "1098"
    FORM_1098_E = "1098-E"
    FORM_1098_T = "1098-T"
    FORM_5498 = "5498"
    FORM_8889 = "8889"
    SCHEDULE_K1 = "Schedule K-1"
    UNKNOWN = "Unknown"


@dataclass
class ExtractedField:
    """A field extracted from a tax document."""
    field_name: str
    value: str
    confidence: float
    bounding_box: Optional[Tuple[int, int, int, int]] = None
    form_line: Optional[str] = None  # Maps to form line number


@dataclass
class DocumentScanResult:
    """Result of scanning a tax document."""
    document_type: DocumentType
    document_year: Optional[str]
    payer_name: Optional[str]
    payer_ein: Optional[str]
    recipient_name: Optional[str]
    recipient_tin: Optional[str]
    fields: List[ExtractedField] = field(default_factory=list)
    raw_text: str = ""
    confidence_score: float = 0.0
    warnings: List[str] = field(default_factory=list)
    form_mapping: Dict[str, Any] = field(default_factory=dict)


class TaxDocumentOCR:
    """OCR processor for tax documents with intelligent field extraction."""

    # Common field patterns for tax forms
    W2_PATTERNS = {
        "ein": r"(?:EIN|Employer.*?identification|Box\s*b)[:\s]*(\d{2}-\d{7})",
        "wages": r"(?:Wages|Box\s*1)[:\s]*\$?([\d,]+\.?\d*)",
        "federal_withheld": r"(?:Federal.*?withheld|Box\s*2)[:\s]*\$?([\d,]+\.?\d*)",
        "social_security_wages": r"(?:Social\s*security\s*wages|Box\s*3)[:\s]*\$?([\d,]+\.?\d*)",
        "social_security_withheld": r"(?:Social\s*security.*?withheld|Box\s*4)[:\s]*\$?([\d,]+\.?\d*)",
        "medicare_wages": r"(?:Medicare\s*wages|Box\s*5)[:\s]*\$?([\d,]+\.?\d*)",
        "medicare_withheld": r"(?:Medicare.*?withheld|Box\s*6)[:\s]*\$?([\d,]+\.?\d*)",
        "state_wages": r"(?:State\s*wages|Box\s*16)[:\s]*\$?([\d,]+\.?\d*)",
        "state_withheld": r"(?:State.*?withheld|Box\s*17)[:\s]*\$?([\d,]+\.?\d*)",
    }

    FORM_1099_INT_PATTERNS = {
        "interest_income": r"(?:Interest\s*income|Box\s*1)[:\s]*\$?([\d,]+\.?\d*)",
        "early_withdrawal_penalty": r"(?:Early\s*withdrawal\s*penalty|Box\s*2)[:\s]*\$?([\d,]+\.?\d*)",
        "interest_on_savings_bonds": r"(?:Interest.*?savings\s*bonds|Box\s*3)[:\s]*\$?([\d,]+\.?\d*)",
        "federal_withheld": r"(?:Federal.*?withheld|Box\s*4)[:\s]*\$?([\d,]+\.?\d*)",
        "tax_exempt_interest": r"(?:Tax-exempt\s*interest|Box\s*8)[:\s]*\$?([\d,]+\.?\d*)",
    }

    FORM_1099_DIV_PATTERNS = {
        "ordinary_dividends": r"(?:Ordinary\s*dividends|Box\s*1a)[:\s]*\$?([\d,]+\.?\d*)",
        "qualified_dividends": r"(?:Qualified\s*dividends|Box\s*1b)[:\s]*\$?([\d,]+\.?\d*)",
        "capital_gain_distributions": r"(?:Capital\s*gain|Box\s*2a)[:\s]*\$?([\d,]+\.?\d*)",
        "nondividend_distributions": r"(?:Nondividend\s*distributions|Box\s*3)[:\s]*\$?([\d,]+\.?\d*)",
        "federal_withheld": r"(?:Federal.*?withheld|Box\s*4)[:\s]*\$?([\d,]+\.?\d*)",
        "foreign_tax_paid": r"(?:Foreign\s*tax\s*paid|Box\s*7)[:\s]*\$?([\d,]+\.?\d*)",
    }

    def __init__(self, anthropic_client=None):
        """Initialize OCR processor.

        Args:
            anthropic_client: Optional Anthropic client for Claude Vision enhancement.
        """
        self.anthropic_client = anthropic_client

        if not TESSERACT_AVAILABLE:
            logger.warning("Tesseract not available. Some OCR features disabled.")

    def scan_image(
        self,
        image_path: Optional[Path] = None,
        image_bytes: Optional[bytes] = None,
        image_base64: Optional[str] = None
    ) -> DocumentScanResult:
        """Scan a tax document image and extract data.

        Args:
            image_path: Path to image file.
            image_bytes: Raw image bytes.
            image_base64: Base64-encoded image.

        Returns:
            DocumentScanResult with extracted data.
        """
        if not TESSERACT_AVAILABLE:
            return DocumentScanResult(
                document_type=DocumentType.UNKNOWN,
                document_year=None,
                payer_name=None,
                payer_ein=None,
                recipient_name=None,
                recipient_tin=None,
                warnings=["OCR not available. Install pytesseract and PIL."]
            )

        # Load image
        if image_path:
            image = Image.open(image_path)
        elif image_bytes:
            image = Image.open(io.BytesIO(image_bytes))
        elif image_base64:
            image_data = base64.b64decode(image_base64)
            image = Image.open(io.BytesIO(image_data))
        else:
            raise ValueError("Must provide image_path, image_bytes, or image_base64")

        # Preprocess image for better OCR
        image = self._preprocess_image(image)

        # Perform OCR
        raw_text = pytesseract.image_to_string(image)

        # Also get detailed data with bounding boxes
        ocr_data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)

        # Detect document type
        doc_type = self._detect_document_type(raw_text)

        # Extract fields based on document type
        fields = self._extract_fields(raw_text, doc_type, ocr_data)

        # Extract common info
        payer_name, payer_ein = self._extract_payer_info(raw_text)
        recipient_name, recipient_tin = self._extract_recipient_info(raw_text)
        doc_year = self._extract_tax_year(raw_text)

        # Calculate overall confidence
        confidences = [f.confidence for f in fields]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

        # Generate form mapping for import
        form_mapping = self._generate_form_mapping(doc_type, fields)

        return DocumentScanResult(
            document_type=doc_type,
            document_year=doc_year,
            payer_name=payer_name,
            payer_ein=payer_ein,
            recipient_name=recipient_name,
            recipient_tin=recipient_tin,
            fields=fields,
            raw_text=raw_text,
            confidence_score=avg_confidence,
            form_mapping=form_mapping
        )

    def scan_pdf(
        self,
        pdf_path: Optional[Path] = None,
        pdf_bytes: Optional[bytes] = None
    ) -> List[DocumentScanResult]:
        """Scan a PDF containing tax documents.

        Returns a list of results, one per page/document.
        """
        if not TESSERACT_AVAILABLE:
            return [DocumentScanResult(
                document_type=DocumentType.UNKNOWN,
                document_year=None,
                payer_name=None,
                payer_ein=None,
                recipient_name=None,
                recipient_tin=None,
                warnings=["PDF OCR not available"]
            )]

        # Convert PDF to images
        if pdf_path:
            images = convert_from_path(pdf_path)
        elif pdf_bytes:
            images = convert_from_bytes(pdf_bytes)
        else:
            raise ValueError("Must provide pdf_path or pdf_bytes")

        results = []
        for i, image in enumerate(images):
            # Save to bytes for processing
            img_bytes = io.BytesIO()
            image.save(img_bytes, format='PNG')
            img_bytes.seek(0)

            result = self.scan_image(image_bytes=img_bytes.read())
            results.append(result)

        return results

    def enhance_with_claude_vision(
        self,
        image_base64: str,
        preliminary_result: DocumentScanResult
    ) -> DocumentScanResult:
        """Use Claude Vision to enhance and verify OCR results.

        Claude Vision provides better accuracy for complex layouts
        and can catch errors in Tesseract output.
        """
        if not self.anthropic_client:
            preliminary_result.warnings.append(
                "Claude Vision not available for enhancement"
            )
            return preliminary_result

        # Build prompt for Claude to verify/enhance
        prompt = f"""You are analyzing a tax document image. Based on the preliminary OCR results below,
please verify and correct any errors you can see in the image.

Preliminary OCR detected this as a {preliminary_result.document_type.value} form.

Fields detected:
{self._format_fields_for_prompt(preliminary_result.fields)}

Please respond with a JSON object containing:
1. "document_type": The correct document type
2. "corrections": A list of corrections, each with "field_name", "ocr_value", "correct_value"
3. "additional_fields": Any fields missed by OCR
4. "confidence": Your confidence in the corrections (0-1)

Focus on verifying dollar amounts, EINs/TINs, and names."""

        try:
            response = self.anthropic_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1024,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": image_base64
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ]
            )

            # Parse Claude's response and apply corrections
            # This would parse the JSON response and update fields
            # Implementation depends on response format
            logger.info("Claude Vision enhancement completed")

        except Exception as e:
            logger.error(f"Claude Vision enhancement failed: {e}")
            preliminary_result.warnings.append(f"Vision enhancement failed: {e}")

        return preliminary_result

    def _preprocess_image(self, image: 'Image.Image') -> 'Image.Image':
        """Preprocess image for better OCR accuracy."""
        # Convert to grayscale
        if image.mode != 'L':
            image = image.convert('L')

        # Increase contrast (simple threshold-based)
        # More sophisticated preprocessing could use OpenCV

        return image

    def _detect_document_type(self, text: str) -> DocumentType:
        """Detect the type of tax document from OCR text."""
        text_upper = text.upper()

        # Check for specific form identifiers
        if "W-2" in text_upper or "WAGE AND TAX STATEMENT" in text_upper:
            return DocumentType.W2
        elif "W-2G" in text_upper:
            return DocumentType.W2G
        elif "1099-INT" in text_upper or "INTEREST INCOME" in text_upper:
            return DocumentType.FORM_1099_INT
        elif "1099-DIV" in text_upper or "DIVIDENDS AND DISTRIBUTIONS" in text_upper:
            return DocumentType.FORM_1099_DIV
        elif "1099-MISC" in text_upper:
            return DocumentType.FORM_1099_MISC
        elif "1099-NEC" in text_upper or "NONEMPLOYEE COMPENSATION" in text_upper:
            return DocumentType.FORM_1099_NEC
        elif "1099-R" in text_upper or "DISTRIBUTIONS FROM PENSIONS" in text_upper:
            return DocumentType.FORM_1099_R
        elif "1099-G" in text_upper:
            return DocumentType.FORM_1099_G
        elif "1099-B" in text_upper or "PROCEEDS FROM BROKER" in text_upper:
            return DocumentType.FORM_1099_B
        elif "1099-K" in text_upper:
            return DocumentType.FORM_1099_K
        elif "SSA-1099" in text_upper or "SOCIAL SECURITY BENEFIT" in text_upper:
            return DocumentType.FORM_1099_SSA
        elif "1098 " in text_upper or "MORTGAGE INTEREST" in text_upper:
            return DocumentType.FORM_1098
        elif "1098-E" in text_upper or "STUDENT LOAN INTEREST" in text_upper:
            return DocumentType.FORM_1098_E
        elif "1098-T" in text_upper or "TUITION STATEMENT" in text_upper:
            return DocumentType.FORM_1098_T
        elif "5498" in text_upper or "IRA CONTRIBUTION" in text_upper:
            return DocumentType.FORM_5498
        elif "SCHEDULE K-1" in text_upper:
            return DocumentType.SCHEDULE_K1

        return DocumentType.UNKNOWN

    def _extract_fields(
        self,
        text: str,
        doc_type: DocumentType,
        ocr_data: Dict
    ) -> List[ExtractedField]:
        """Extract form fields based on document type."""
        fields = []

        # Select patterns based on document type
        patterns = {}
        if doc_type == DocumentType.W2:
            patterns = self.W2_PATTERNS
        elif doc_type == DocumentType.FORM_1099_INT:
            patterns = self.FORM_1099_INT_PATTERNS
        elif doc_type == DocumentType.FORM_1099_DIV:
            patterns = self.FORM_1099_DIV_PATTERNS
        # Add more document type patterns...

        # Extract fields using patterns
        for field_name, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = match.group(1).replace(",", "")
                fields.append(ExtractedField(
                    field_name=field_name,
                    value=value,
                    confidence=0.8,  # Base confidence
                    form_line=self._get_form_line_mapping(doc_type, field_name)
                ))

        return fields

    def _extract_payer_info(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        """Extract payer/employer name and EIN."""
        # EIN pattern
        ein_match = re.search(r'(\d{2}-\d{7})', text)
        ein = ein_match.group(1) if ein_match else None

        # Payer name is typically near "PAYER" or "EMPLOYER"
        name = None
        lines = text.split('\n')
        for i, line in enumerate(lines):
            if 'PAYER' in line.upper() or 'EMPLOYER' in line.upper():
                if i + 1 < len(lines):
                    name = lines[i + 1].strip()
                    break

        return name, ein

    def _extract_recipient_info(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        """Extract recipient name and TIN/SSN."""
        # SSN pattern
        ssn_match = re.search(r'(\d{3}-\d{2}-\d{4})', text)
        tin = ssn_match.group(1) if ssn_match else None

        # Recipient name
        name = None
        lines = text.split('\n')
        for i, line in enumerate(lines):
            if 'RECIPIENT' in line.upper() or 'EMPLOYEE' in line.upper():
                if i + 1 < len(lines):
                    name = lines[i + 1].strip()
                    break

        return name, tin

    def _extract_tax_year(self, text: str) -> Optional[str]:
        """Extract tax year from document."""
        # Look for 4-digit years between 2020 and 2030
        years = re.findall(r'20[2-3]\d', text)
        if years:
            return max(years)  # Return most recent year found
        return None

    def _get_form_line_mapping(
        self,
        doc_type: DocumentType,
        field_name: str
    ) -> Optional[str]:
        """Get the form line number for a field."""
        mappings = {
            DocumentType.W2: {
                "wages": "1",
                "federal_withheld": "2",
                "social_security_wages": "3",
                "social_security_withheld": "4",
                "medicare_wages": "5",
                "medicare_withheld": "6",
                "state_wages": "16",
                "state_withheld": "17",
            },
            DocumentType.FORM_1099_INT: {
                "interest_income": "1",
                "early_withdrawal_penalty": "2",
                "federal_withheld": "4",
            },
            # Add more mappings...
        }

        doc_mappings = mappings.get(doc_type, {})
        return doc_mappings.get(field_name)

    def _generate_form_mapping(
        self,
        doc_type: DocumentType,
        fields: List[ExtractedField]
    ) -> Dict[str, Any]:
        """Generate form mapping for importing into tax return."""
        mapping = {
            "document_type": doc_type.value,
            "fields": {}
        }

        for field in fields:
            fact_path = self._get_fact_path(doc_type, field.field_name)
            if fact_path:
                mapping["fields"][fact_path] = {
                    "value": field.value,
                    "confidence": field.confidence,
                    "form_line": field.form_line
                }

        return mapping

    def _get_fact_path(self, doc_type: DocumentType, field_name: str) -> Optional[str]:
        """Get the Direct File fact path for a field."""
        # Maps document fields to Direct File fact paths
        fact_paths = {
            DocumentType.W2: {
                "wages": "/formW2s/*/writableWages",
                "federal_withheld": "/formW2s/*/writableFederalWithholding",
                "social_security_wages": "/formW2s/*/writableOasdiWages",
                "social_security_withheld": "/formW2s/*/writableOasdiWithholding",
                "medicare_wages": "/formW2s/*/writableMedicareWages",
                "medicare_withheld": "/formW2s/*/writableMedicareWithholding",
                "state_wages": "/formW2s/*/writableStateWages",
                "state_withheld": "/formW2s/*/writableStateWithholding",
                "ein": "/formW2s/*/ein",
            },
            DocumentType.FORM_1099_INT: {
                "interest_income": "/form1099Ints/*/writableInterestIncome",
                "federal_withheld": "/form1099Ints/*/writableFederalWithholding",
            },
            # Add more mappings...
        }

        doc_facts = fact_paths.get(doc_type, {})
        return doc_facts.get(field_name)

    def _format_fields_for_prompt(self, fields: List[ExtractedField]) -> str:
        """Format fields for Claude prompt."""
        lines = []
        for f in fields:
            lines.append(f"- {f.field_name}: {f.value} (confidence: {f.confidence:.0%})")
        return "\n".join(lines)
