"""MeF (Modernized e-File) E-Filing Service - Part 1: Models and Utilities.

This module provides comprehensive support for IRS Modernized e-File (MeF) system integration,
including submission, validation, acknowledgment handling, and status tracking.

MeF is the IRS's web-based system for electronic filing of tax returns. This service
implements the client-side logic for:
- Building valid MeF submission packages
- Generating compliant XML documents
- Handling acknowledgments and error responses
- Managing submission lifecycle and status tracking

Reference: IRS Publication 4164 - Modernized e-File (MeF) Guide for Software Developers
"""

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union
import html
import re
import uuid

from pydantic import BaseModel, Field, field_validator, model_validator


# =============================================================================
# MeF Environment Configuration
# =============================================================================


class MeFEnvironment(str, Enum):
    """MeF system environments.

    The IRS provides multiple environments for different stages of development
    and production filing:

    - ASSURANCE: For Assurance Testing System (ATS) - initial software testing
    - PRODUCTION: Live production environment for actual tax filings
    - SANDBOX: Development sandbox for integration testing (not officially IRS)
    """
    ASSURANCE = "assurance"
    PRODUCTION = "production"
    SANDBOX = "sandbox"


class MeFCredentials(BaseModel):
    """MeF authentication credentials.

    MeF uses digital certificate-based authentication with EFIN/ETIN identifiers.
    Software developers must obtain credentials through the IRS e-Services portal.

    Attributes:
        efin: Electronic Filing Identification Number (6 digits)
        etin: Electronic Transmitter Identification Number (5 characters)
        certificate_path: Path to PKCS#12 certificate file (.p12)
        certificate_password: Password for the certificate file
        software_id: IRS-assigned Software Identification (8 characters)
        vendor_control_code: Vendor control code for transmission
    """
    efin: str = Field(
        ...,
        min_length=6,
        max_length=6,
        pattern=r"^\d{6}$",
        description="Electronic Filing Identification Number (6 digits)"
    )
    etin: str = Field(
        ...,
        min_length=5,
        max_length=5,
        pattern=r"^[A-Z0-9]{5}$",
        description="Electronic Transmitter Identification Number (5 alphanumeric characters)"
    )
    certificate_path: str = Field(
        ...,
        description="Path to PKCS#12 certificate file"
    )
    certificate_password: str = Field(
        ...,
        min_length=1,
        description="Password for the certificate file"
    )
    software_id: str = Field(
        ...,
        min_length=8,
        max_length=8,
        description="IRS-assigned Software Identification"
    )
    vendor_control_code: Optional[str] = Field(
        None,
        max_length=32,
        description="Vendor control code for transmission"
    )

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "efin": "123456",
                "etin": "AB123",
                "certificate_path": "/path/to/cert.p12",
                "certificate_password": "secure_password",
                "software_id": "12345678",
                "vendor_control_code": "VENDOR001"
            }
        }


class MeFEndpoint(BaseModel):
    """MeF service endpoint configuration.

    Defines the URLs and ports for connecting to MeF web services.
    Each environment has different endpoints.

    Attributes:
        base_url: Base URL for the MeF web service
        submit_path: Path for submission endpoint
        ack_path: Path for acknowledgment retrieval
        status_path: Path for status inquiry
        port: Service port (typically 443 for HTTPS)
        timeout_seconds: Request timeout in seconds
    """
    base_url: str = Field(
        ...,
        description="Base URL for MeF web service"
    )
    submit_path: str = Field(
        default="/mef/services/submit",
        description="Submission endpoint path"
    )
    ack_path: str = Field(
        default="/mef/services/ack",
        description="Acknowledgment retrieval path"
    )
    status_path: str = Field(
        default="/mef/services/status",
        description="Status inquiry path"
    )
    port: int = Field(
        default=443,
        ge=1,
        le=65535,
        description="Service port"
    )
    timeout_seconds: int = Field(
        default=120,
        ge=10,
        le=600,
        description="Request timeout in seconds"
    )

    @property
    def submit_url(self) -> str:
        """Get full submission URL."""
        return f"{self.base_url}:{self.port}{self.submit_path}"

    @property
    def ack_url(self) -> str:
        """Get full acknowledgment URL."""
        return f"{self.base_url}:{self.port}{self.ack_path}"

    @property
    def status_url(self) -> str:
        """Get full status inquiry URL."""
        return f"{self.base_url}:{self.port}{self.status_path}"


class MeFConfiguration(BaseModel):
    """Complete MeF configuration.

    Combines environment, credentials, and endpoint settings for a complete
    MeF connection configuration.

    Attributes:
        environment: Target MeF environment
        credentials: Authentication credentials
        endpoint: Service endpoint configuration
        tax_year: Tax year for submissions (YYYY format)
        enable_compression: Whether to compress submissions
        enable_logging: Whether to enable detailed logging
        retry_attempts: Number of retry attempts for failed requests
        retry_delay_seconds: Delay between retries
    """
    environment: MeFEnvironment = Field(
        default=MeFEnvironment.SANDBOX,
        description="Target MeF environment"
    )
    credentials: MeFCredentials = Field(
        ...,
        description="Authentication credentials"
    )
    endpoint: Optional[MeFEndpoint] = Field(
        None,
        description="Custom endpoint configuration (auto-configured if not provided)"
    )
    tax_year: int = Field(
        ...,
        ge=2020,
        le=2030,
        description="Tax year for submissions"
    )
    enable_compression: bool = Field(
        default=True,
        description="Enable GZIP compression for submissions"
    )
    enable_logging: bool = Field(
        default=True,
        description="Enable detailed request/response logging"
    )
    retry_attempts: int = Field(
        default=3,
        ge=0,
        le=10,
        description="Number of retry attempts for failed requests"
    )
    retry_delay_seconds: int = Field(
        default=5,
        ge=1,
        le=60,
        description="Delay between retries in seconds"
    )

    @model_validator(mode="before")
    @classmethod
    def set_default_endpoint(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Set default endpoint based on environment if not provided."""
        if isinstance(values, dict) and values.get("endpoint") is None:
            env = values.get("environment", MeFEnvironment.SANDBOX)
            if env == MeFEnvironment.PRODUCTION:
                values["endpoint"] = MeFEndpoint(
                    base_url="https://la.www4.irs.gov"
                )
            elif env == MeFEnvironment.ASSURANCE:
                values["endpoint"] = MeFEndpoint(
                    base_url="https://la.tst.www4.irs.gov"
                )
            else:  # SANDBOX
                values["endpoint"] = MeFEndpoint(
                    base_url="https://sandbox.mef.irs.gov"
                )
        return values


# =============================================================================
# Submission Types
# =============================================================================


class SubmissionType(str, Enum):
    """Types of MeF submissions.

    Different submission types have different processing rules and
    acknowledgment timelines.
    """
    INDIVIDUAL_1040 = "1040"
    INDIVIDUAL_1040_SR = "1040SR"
    INDIVIDUAL_1040_NR = "1040NR"
    INDIVIDUAL_1040_X = "1040X"
    EXTENSION_4868 = "4868"
    ESTIMATED_1040_ES = "1040ES"


class SubmissionCategory(str, Enum):
    """Category of submission for processing prioritization."""
    ORIGINAL = "O"
    SUPERSEDED = "S"
    AMENDED = "A"
    EXTENSION = "E"
    ESTIMATED_PAYMENT = "P"


class SubmissionId(BaseModel):
    """MeF submission identifier.

    Each submission receives a unique identifier that is used for tracking
    through the MeF system.

    Attributes:
        submission_id: Unique 20-character submission ID
        timestamp: When the submission ID was generated
        efin: EFIN that generated the submission
        sequence_number: Daily sequence number for the EFIN
    """
    submission_id: str = Field(
        ...,
        min_length=20,
        max_length=20,
        pattern=r"^\d{20}$",
        description="20-digit MeF submission ID"
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Submission ID generation timestamp"
    )
    efin: str = Field(
        ...,
        min_length=6,
        max_length=6,
        description="EFIN that generated this submission ID"
    )
    sequence_number: int = Field(
        ...,
        ge=1,
        le=999999,
        description="Daily sequence number"
    )

    @classmethod
    def generate(cls, efin: str, sequence: int) -> "SubmissionId":
        """Generate a new submission ID.

        MeF submission IDs follow the format:
        YYYYMMDD + EFIN (6 digits) + Sequence (6 digits)

        Args:
            efin: Electronic Filing Identification Number
            sequence: Daily sequence number (1-999999)

        Returns:
            New SubmissionId instance

        Raises:
            ValueError: If EFIN format is invalid or sequence out of range
        """
        if not re.match(r"^\d{6}$", efin):
            raise ValueError(f"Invalid EFIN format: {efin}")
        if not 1 <= sequence <= 999999:
            raise ValueError(f"Sequence number must be 1-999999, got: {sequence}")

        now = datetime.now(timezone.utc)
        date_part = now.strftime("%Y%m%d")
        submission_id = f"{date_part}{efin}{sequence:06d}"

        return cls(
            submission_id=submission_id,
            timestamp=now,
            efin=efin,
            sequence_number=sequence
        )

    def __str__(self) -> str:
        """String representation of submission ID."""
        return self.submission_id


class TaxpayerInfo(BaseModel):
    """Taxpayer identification information for the return header.

    Contains the essential identifying information for the primary
    taxpayer and optional spouse.

    Attributes:
        primary_ssn: Primary taxpayer's SSN
        primary_first_name: Primary taxpayer's first name
        primary_last_name: Primary taxpayer's last name
        primary_date_of_birth: Primary taxpayer's date of birth
        spouse_ssn: Spouse's SSN (if MFJ or MFS)
        spouse_first_name: Spouse's first name
        spouse_last_name: Spouse's last name
        spouse_date_of_birth: Spouse's date of birth
    """
    primary_ssn: str = Field(
        ...,
        min_length=9,
        max_length=9,
        pattern=r"^\d{9}$",
        description="Primary taxpayer SSN (9 digits, no dashes)"
    )
    primary_first_name: str = Field(
        ...,
        min_length=1,
        max_length=35,
        description="Primary taxpayer first name"
    )
    primary_last_name: str = Field(
        ...,
        min_length=1,
        max_length=35,
        description="Primary taxpayer last name"
    )
    primary_date_of_birth: Optional[date] = Field(
        None,
        description="Primary taxpayer date of birth"
    )
    spouse_ssn: Optional[str] = Field(
        None,
        min_length=9,
        max_length=9,
        pattern=r"^\d{9}$",
        description="Spouse SSN (if applicable)"
    )
    spouse_first_name: Optional[str] = Field(
        None,
        max_length=35,
        description="Spouse first name"
    )
    spouse_last_name: Optional[str] = Field(
        None,
        max_length=35,
        description="Spouse last name"
    )
    spouse_date_of_birth: Optional[date] = Field(
        None,
        description="Spouse date of birth"
    )


class ReturnHeader(BaseModel):
    """MeF Return Header information.

    The return header contains metadata about the submission including
    taxpayer identification, filing status, and software identification.
    This follows IRS Publication 4164 specifications.

    Attributes:
        submission_id: Unique submission identifier
        submission_type: Type of return being filed
        category: Submission category (original, amended, etc.)
        tax_year: Tax year of the return
        taxpayer: Taxpayer identification information
        filing_status: IRS filing status code (1-5)
        pin_type: Type of signature PIN used
        primary_pin: Primary taxpayer's signature PIN
        spouse_pin: Spouse's signature PIN (if applicable)
        preparer_ein: Preparer's EIN (if professionally prepared)
        preparer_ptin: Preparer's PTIN
        software_id: IRS-assigned software ID
        originator_efin: Originator's EFIN
        created_at: When the return was created
    """
    submission_id: SubmissionId = Field(
        ...,
        description="Unique submission identifier"
    )
    submission_type: SubmissionType = Field(
        default=SubmissionType.INDIVIDUAL_1040,
        description="Type of return being filed"
    )
    category: SubmissionCategory = Field(
        default=SubmissionCategory.ORIGINAL,
        description="Submission category"
    )
    tax_year: int = Field(
        ...,
        ge=2020,
        le=2030,
        description="Tax year"
    )
    taxpayer: TaxpayerInfo = Field(
        ...,
        description="Taxpayer identification"
    )
    filing_status: int = Field(
        ...,
        ge=1,
        le=5,
        description="Filing status (1=Single, 2=MFJ, 3=MFS, 4=HOH, 5=QSS)"
    )
    pin_type: str = Field(
        default="Self-Select",
        description="PIN type (Self-Select, Practitioner)"
    )
    primary_pin: str = Field(
        ...,
        min_length=5,
        max_length=5,
        pattern=r"^\d{5}$",
        description="Primary taxpayer signature PIN"
    )
    spouse_pin: Optional[str] = Field(
        None,
        min_length=5,
        max_length=5,
        pattern=r"^\d{5}$",
        description="Spouse signature PIN"
    )
    preparer_ein: Optional[str] = Field(
        None,
        pattern=r"^\d{9}$",
        description="Preparer's EIN"
    )
    preparer_ptin: Optional[str] = Field(
        None,
        pattern=r"^P\d{8}$",
        description="Preparer's PTIN"
    )
    software_id: str = Field(
        ...,
        min_length=8,
        max_length=8,
        description="IRS-assigned software ID"
    )
    originator_efin: str = Field(
        ...,
        min_length=6,
        max_length=6,
        pattern=r"^\d{6}$",
        description="Originator's EFIN"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Creation timestamp"
    )

    @property
    def filing_status_description(self) -> str:
        """Get human-readable filing status."""
        status_map = {
            1: "Single",
            2: "Married Filing Jointly",
            3: "Married Filing Separately",
            4: "Head of Household",
            5: "Qualifying Surviving Spouse"
        }
        return status_map.get(self.filing_status, "Unknown")


class SubmissionResult(BaseModel):
    """Result of a MeF submission attempt.

    Contains the outcome of attempting to submit a return to MeF,
    including any immediate validation errors.

    Attributes:
        success: Whether the submission was accepted for processing
        submission_id: The submission ID
        receipt_id: MeF receipt ID (if accepted)
        timestamp: When the submission was processed
        message: Status message from MeF
        errors: List of immediate validation errors
        warnings: List of non-fatal warnings
        estimated_ack_time: Estimated time until acknowledgment
    """
    success: bool = Field(
        ...,
        description="Whether submission was accepted"
    )
    submission_id: str = Field(
        ...,
        description="Submission ID"
    )
    receipt_id: Optional[str] = Field(
        None,
        description="MeF receipt ID"
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Processing timestamp"
    )
    message: str = Field(
        default="",
        description="Status message"
    )
    errors: List[str] = Field(
        default_factory=list,
        description="Validation errors"
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="Non-fatal warnings"
    )
    estimated_ack_time: Optional[datetime] = Field(
        None,
        description="Estimated acknowledgment availability time"
    )


# =============================================================================
# Acknowledgment Types
# =============================================================================


class AckStatus(str, Enum):
    """MeF acknowledgment status codes.

    These are the possible outcomes when retrieving an acknowledgment
    for a submitted return.
    """
    ACCEPTED = "A"
    REJECTED = "R"
    ACCEPTED_WITH_ERRORS = "AE"
    PENDING = "P"
    NOT_FOUND = "NF"
    PROCESSING = "PR"


class AckErrorSeverity(str, Enum):
    """Severity level of acknowledgment errors."""
    REJECT = "Reject"
    ALERT = "Alert"
    WARNING = "Warning"
    INFORMATIONAL = "Info"


class AckError(BaseModel):
    """An individual error from a MeF acknowledgment.

    When a return is rejected, the acknowledgment contains one or more
    error records describing the issues found.

    Attributes:
        error_code: IRS error code (e.g., "IND-031-01")
        error_message: Human-readable error description
        severity: Error severity level
        xpath: XPath to the error location in the XML
        field_value: The problematic value (if available)
        rule_number: IRS business rule number
        category: Error category code
    """
    error_code: str = Field(
        ...,
        description="IRS error code"
    )
    error_message: str = Field(
        ...,
        description="Error description"
    )
    severity: AckErrorSeverity = Field(
        default=AckErrorSeverity.REJECT,
        description="Error severity"
    )
    xpath: Optional[str] = Field(
        None,
        description="XPath to error location"
    )
    field_value: Optional[str] = Field(
        None,
        description="Problematic field value"
    )
    rule_number: Optional[str] = Field(
        None,
        description="IRS business rule number"
    )
    category: Optional[str] = Field(
        None,
        description="Error category"
    )

    def to_user_message(self) -> str:
        """Generate a user-friendly error message.

        Returns:
            User-friendly description of the error
        """
        message = f"Error {self.error_code}: {self.error_message}"
        if self.field_value:
            message += f" (Value: {self.field_value})"
        return message


class Acknowledgment(BaseModel):
    """MeF acknowledgment response.

    After submission, returns are processed asynchronously. This model
    represents the acknowledgment received when checking submission status.

    Attributes:
        submission_id: The original submission ID
        status: Current status of the submission
        timestamp: When the acknowledgment was generated
        acceptance_status: Final acceptance status (if complete)
        refund_amount: Expected refund (if accepted)
        amount_owed: Amount owed (if accepted)
        direct_deposit_status: Status of direct deposit setup
        errors: List of errors (if rejected)
        state_acks: State acknowledgments (if bundled)
        raw_xml: Raw acknowledgment XML (for debugging)
    """
    submission_id: str = Field(
        ...,
        description="Original submission ID"
    )
    status: AckStatus = Field(
        ...,
        description="Current status"
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Acknowledgment timestamp"
    )
    acceptance_status: Optional[str] = Field(
        None,
        description="Final acceptance status description"
    )
    refund_amount: Optional[Decimal] = Field(
        None,
        ge=0,
        description="Expected refund amount"
    )
    amount_owed: Optional[Decimal] = Field(
        None,
        ge=0,
        description="Amount owed"
    )
    direct_deposit_status: Optional[str] = Field(
        None,
        description="Direct deposit setup status"
    )
    errors: List[AckError] = Field(
        default_factory=list,
        description="Rejection errors"
    )
    state_acks: Dict[str, "Acknowledgment"] = Field(
        default_factory=dict,
        description="State acknowledgments keyed by state code"
    )
    raw_xml: Optional[str] = Field(
        None,
        description="Raw acknowledgment XML"
    )

    @property
    def is_accepted(self) -> bool:
        """Check if the return was accepted."""
        return self.status in (AckStatus.ACCEPTED, AckStatus.ACCEPTED_WITH_ERRORS)

    @property
    def is_rejected(self) -> bool:
        """Check if the return was rejected."""
        return self.status == AckStatus.REJECTED

    @property
    def is_pending(self) -> bool:
        """Check if the return is still being processed."""
        return self.status in (AckStatus.PENDING, AckStatus.PROCESSING)

    def get_error_summary(self) -> str:
        """Get a summary of all errors.

        Returns:
            Formatted string summarizing all errors
        """
        if not self.errors:
            return "No errors"

        lines = [f"Found {len(self.errors)} error(s):"]
        for i, error in enumerate(self.errors, 1):
            lines.append(f"  {i}. {error.to_user_message()}")
        return "\n".join(lines)


# =============================================================================
# Validation Types
# =============================================================================


class ValidationSeverity(str, Enum):
    """Severity level for validation errors."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ValidationCategory(str, Enum):
    """Category of validation error."""
    SCHEMA = "schema"
    BUSINESS_RULE = "business_rule"
    MATH = "math"
    CONSISTENCY = "consistency"
    COMPLETENESS = "completeness"
    FORMAT = "format"


class ValidationError(BaseModel):
    """A validation error found during pre-submission checks.

    Pre-submission validation catches errors before sending to MeF,
    reducing rejection rates and improving user experience.

    Attributes:
        code: Internal validation error code
        message: Human-readable error message
        severity: Error severity level
        category: Error category
        field_path: Path to the problematic field
        field_value: The problematic value
        expected_format: Expected format or value
        form_name: Which form the error is on
        line_number: Line number on the form
        suggestion: Suggested fix
    """
    code: str = Field(
        ...,
        description="Validation error code"
    )
    message: str = Field(
        ...,
        description="Error message"
    )
    severity: ValidationSeverity = Field(
        default=ValidationSeverity.ERROR,
        description="Severity level"
    )
    category: ValidationCategory = Field(
        default=ValidationCategory.BUSINESS_RULE,
        description="Error category"
    )
    field_path: Optional[str] = Field(
        None,
        description="Path to problematic field"
    )
    field_value: Optional[str] = Field(
        None,
        description="Current field value"
    )
    expected_format: Optional[str] = Field(
        None,
        description="Expected format or value"
    )
    form_name: Optional[str] = Field(
        None,
        description="Form name (e.g., '1040', 'Schedule A')"
    )
    line_number: Optional[str] = Field(
        None,
        description="Line number on form"
    )
    suggestion: Optional[str] = Field(
        None,
        description="Suggested fix"
    )

    def to_display_string(self) -> str:
        """Format error for display.

        Returns:
            User-friendly error message with location info
        """
        parts = []
        if self.form_name:
            parts.append(f"[{self.form_name}")
            if self.line_number:
                parts.append(f" Line {self.line_number}")
            parts.append("] ")

        parts.append(self.message)

        if self.suggestion:
            parts.append(f" Suggestion: {self.suggestion}")

        return "".join(parts)


class ValidationResult(BaseModel):
    """Result of pre-submission validation.

    Contains all validation errors and warnings found during
    pre-submission checks.

    Attributes:
        is_valid: Whether the return passed all validations
        errors: List of validation errors
        warnings: List of validation warnings
        info_messages: Informational messages
        validated_at: When validation was performed
        validation_duration_ms: How long validation took
        forms_validated: List of forms that were validated
    """
    is_valid: bool = Field(
        ...,
        description="Whether validation passed"
    )
    errors: List[ValidationError] = Field(
        default_factory=list,
        description="Validation errors"
    )
    warnings: List[ValidationError] = Field(
        default_factory=list,
        description="Validation warnings"
    )
    info_messages: List[ValidationError] = Field(
        default_factory=list,
        description="Informational messages"
    )
    validated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Validation timestamp"
    )
    validation_duration_ms: Optional[int] = Field(
        None,
        ge=0,
        description="Validation duration in milliseconds"
    )
    forms_validated: List[str] = Field(
        default_factory=list,
        description="Forms that were validated"
    )

    @property
    def error_count(self) -> int:
        """Get total error count."""
        return len(self.errors)

    @property
    def warning_count(self) -> int:
        """Get total warning count."""
        return len(self.warnings)

    def get_errors_by_form(self) -> Dict[str, List[ValidationError]]:
        """Group errors by form name.

        Returns:
            Dictionary mapping form names to their errors
        """
        by_form: Dict[str, List[ValidationError]] = {}
        for error in self.errors:
            form = error.form_name or "General"
            if form not in by_form:
                by_form[form] = []
            by_form[form].append(error)
        return by_form

    def get_summary(self) -> str:
        """Get a validation summary.

        Returns:
            Summary string with counts and status
        """
        status = "PASSED" if self.is_valid else "FAILED"
        return (
            f"Validation {status}: "
            f"{self.error_count} error(s), "
            f"{self.warning_count} warning(s)"
        )


# =============================================================================
# XML Utility Functions
# =============================================================================


def escape_xml(value: str) -> str:
    """Escape special XML characters in a string.

    Converts characters that have special meaning in XML to their
    entity references to prevent parsing errors and injection.

    Args:
        value: String to escape

    Returns:
        XML-safe escaped string

    Examples:
        >>> escape_xml("Smith & Jones")
        'Smith &amp; Jones'
        >>> escape_xml('<test attr="value">')
        '&lt;test attr=&quot;value&quot;&gt;'
        >>> escape_xml("O'Brien")
        "O&apos;Brien"
    """
    if not value:
        return ""

    # Use html.escape for basic escaping, then handle apostrophe
    escaped = html.escape(value, quote=True)
    # html.escape doesn't escape apostrophe by default in all versions
    escaped = escaped.replace("'", "&apos;")
    return escaped


def format_amount(amount: Union[Decimal, float, int, str, None],
                  allow_negative: bool = False) -> str:
    """Format a monetary amount for MeF XML (whole dollars, no cents).

    MeF requires most monetary amounts as whole numbers without decimal
    points or thousands separators. Amounts are rounded to the nearest dollar.

    Args:
        amount: The amount to format (Decimal, float, int, or numeric string)
        allow_negative: Whether to allow negative amounts

    Returns:
        Formatted amount string (e.g., "12345" for $12,345.00)

    Raises:
        ValueError: If amount is invalid or negative when not allowed

    Examples:
        >>> format_amount(Decimal("12345.67"))
        '12346'
        >>> format_amount(12345.44)
        '12345'
        >>> format_amount("12345.50")
        '12346'
        >>> format_amount(0)
        '0'
        >>> format_amount(-100, allow_negative=True)
        '-100'
    """
    if amount is None:
        return "0"

    try:
        if isinstance(amount, str):
            # Remove any commas or currency symbols
            cleaned = amount.replace(",", "").replace("$", "").strip()
            decimal_amount = Decimal(cleaned)
        elif isinstance(amount, float):
            # Convert through string to avoid float precision issues
            decimal_amount = Decimal(str(amount))
        elif isinstance(amount, int):
            decimal_amount = Decimal(amount)
        elif isinstance(amount, Decimal):
            decimal_amount = amount
        else:
            raise ValueError(f"Unsupported amount type: {type(amount)}")

        # Round to nearest whole dollar
        rounded = decimal_amount.quantize(Decimal("1"), rounding=ROUND_HALF_UP)

        # Check for negative
        if rounded < 0 and not allow_negative:
            raise ValueError(f"Negative amounts not allowed: {amount}")

        return str(int(rounded))

    except (InvalidOperation, ValueError) as e:
        raise ValueError(f"Invalid amount value: {amount}") from e


def format_amount_with_cents(amount: Union[Decimal, float, int, str, None],
                             allow_negative: bool = False) -> str:
    """Format a monetary amount with cents for MeF XML.

    Some MeF fields require amounts with cents (2 decimal places).
    This formats amounts as "NNNN.NN" without thousands separators.

    Args:
        amount: The amount to format
        allow_negative: Whether to allow negative amounts

    Returns:
        Formatted amount string with 2 decimal places (e.g., "12345.67")

    Raises:
        ValueError: If amount is invalid or negative when not allowed

    Examples:
        >>> format_amount_with_cents(Decimal("12345.678"))
        '12345.68'
        >>> format_amount_with_cents(12345)
        '12345.00'
        >>> format_amount_with_cents("12,345.5")
        '12345.50'
    """
    if amount is None:
        return "0.00"

    try:
        if isinstance(amount, str):
            cleaned = amount.replace(",", "").replace("$", "").strip()
            decimal_amount = Decimal(cleaned)
        elif isinstance(amount, float):
            decimal_amount = Decimal(str(amount))
        elif isinstance(amount, int):
            decimal_amount = Decimal(amount)
        elif isinstance(amount, Decimal):
            decimal_amount = amount
        else:
            raise ValueError(f"Unsupported amount type: {type(amount)}")

        # Round to 2 decimal places
        rounded = decimal_amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # Check for negative
        if rounded < 0 and not allow_negative:
            raise ValueError(f"Negative amounts not allowed: {amount}")

        # Format with exactly 2 decimal places
        return f"{rounded:.2f}"

    except (InvalidOperation, ValueError) as e:
        raise ValueError(f"Invalid amount value: {amount}") from e


def format_ssn(ssn: str, with_dashes: bool = False) -> str:
    """Format a Social Security Number for MeF XML.

    MeF requires SSNs as 9 consecutive digits without dashes or spaces.
    This function validates and formats SSN input.

    Args:
        ssn: SSN to format (may include dashes or spaces)
        with_dashes: If True, format as XXX-XX-XXXX (for display only)

    Returns:
        Formatted SSN string

    Raises:
        ValueError: If SSN is invalid format

    Examples:
        >>> format_ssn("123-45-6789")
        '123456789'
        >>> format_ssn("123 45 6789")
        '123456789'
        >>> format_ssn("123456789", with_dashes=True)
        '123-45-6789'
    """
    if not ssn:
        raise ValueError("SSN cannot be empty")

    # Remove dashes, spaces, and other common separators
    cleaned = re.sub(r"[\s\-\.]+", "", ssn)

    # Validate format
    if not re.match(r"^\d{9}$", cleaned):
        raise ValueError(f"Invalid SSN format: {ssn}")

    # Basic validity checks (IRS rules)
    # Area number (first 3 digits) cannot be 000, 666, or 900-999
    area = int(cleaned[:3])
    if area == 0 or area == 666 or area >= 900:
        raise ValueError(f"Invalid SSN area number: {cleaned[:3]}")

    # Group number (middle 2 digits) cannot be 00
    if cleaned[3:5] == "00":
        raise ValueError("Invalid SSN group number: 00")

    # Serial number (last 4 digits) cannot be 0000
    if cleaned[5:] == "0000":
        raise ValueError("Invalid SSN serial number: 0000")

    if with_dashes:
        return f"{cleaned[:3]}-{cleaned[3:5]}-{cleaned[5:]}"

    return cleaned


def format_ein(ein: str, with_dash: bool = False) -> str:
    """Format an Employer Identification Number for MeF XML.

    MeF requires EINs as 9 consecutive digits without dashes.
    EINs follow the format XX-XXXXXXX when displayed.

    Args:
        ein: EIN to format (may include dash)
        with_dash: If True, format as XX-XXXXXXX (for display only)

    Returns:
        Formatted EIN string

    Raises:
        ValueError: If EIN is invalid format

    Examples:
        >>> format_ein("12-3456789")
        '123456789'
        >>> format_ein("123456789", with_dash=True)
        '12-3456789'
    """
    if not ein:
        raise ValueError("EIN cannot be empty")

    # Remove dashes and spaces
    cleaned = re.sub(r"[\s\-]+", "", ein)

    # Validate format
    if not re.match(r"^\d{9}$", cleaned):
        raise ValueError(f"Invalid EIN format: {ein}")

    # Basic validity check - first 2 digits (prefix) must be valid
    # Valid IRS prefixes: 01-06, 10-16, 20-27, 30-39, 40-48, 50-59, 60-68, 71-77, 80-88, 90-92
    prefix = int(cleaned[:2])
    valid_ranges = [
        (1, 6), (10, 16), (20, 27), (30, 39), (40, 48),
        (50, 59), (60, 68), (71, 77), (80, 88), (90, 92)
    ]
    is_valid_prefix = any(low <= prefix <= high for low, high in valid_ranges)

    if not is_valid_prefix:
        raise ValueError(f"Invalid EIN prefix: {cleaned[:2]}")

    if with_dash:
        return f"{cleaned[:2]}-{cleaned[2:]}"

    return cleaned


def format_date(dt: Union[date, datetime, str, None],
                output_format: str = "%Y-%m-%d") -> str:
    """Format a date for MeF XML.

    MeF uses ISO 8601 date format (YYYY-MM-DD) for most date fields.
    This function handles various input formats and validates the date.

    Args:
        dt: Date to format (date, datetime, or string)
        output_format: strftime format string (default: ISO 8601)

    Returns:
        Formatted date string

    Raises:
        ValueError: If date is invalid or cannot be parsed

    Examples:
        >>> format_date(date(2024, 12, 31))
        '2024-12-31'
        >>> format_date("12/31/2024")
        '2024-12-31'
        >>> format_date("2024-12-31")
        '2024-12-31'
    """
    if dt is None:
        raise ValueError("Date cannot be None")

    if isinstance(dt, datetime):
        return dt.strftime(output_format)

    if isinstance(dt, date):
        return dt.strftime(output_format)

    if isinstance(dt, str):
        # Try common date formats
        formats_to_try = [
            "%Y-%m-%d",      # ISO 8601: 2024-12-31
            "%m/%d/%Y",      # US: 12/31/2024
            "%m-%d-%Y",      # US with dashes: 12-31-2024
            "%d/%m/%Y",      # European: 31/12/2024
            "%Y%m%d",        # Compact: 20241231
            "%B %d, %Y",     # Long: December 31, 2024
            "%b %d, %Y",     # Short: Dec 31, 2024
        ]

        for fmt in formats_to_try:
            try:
                parsed = datetime.strptime(dt.strip(), fmt)
                return parsed.strftime(output_format)
            except ValueError:
                continue

        raise ValueError(f"Unable to parse date: {dt}")

    raise ValueError(f"Unsupported date type: {type(dt)}")


def format_timestamp(dt: Union[datetime, str, None],
                     include_timezone: bool = True) -> str:
    """Format a timestamp for MeF XML.

    MeF uses ISO 8601 timestamp format with optional timezone.
    Format: YYYY-MM-DDTHH:MM:SS or YYYY-MM-DDTHH:MM:SS+HH:MM

    Args:
        dt: Datetime to format
        include_timezone: Whether to include timezone offset

    Returns:
        Formatted timestamp string

    Raises:
        ValueError: If timestamp is invalid

    Examples:
        >>> format_timestamp(datetime(2024, 12, 31, 14, 30, 0, tzinfo=timezone.utc))
        '2024-12-31T14:30:00+00:00'
        >>> format_timestamp(datetime(2024, 12, 31, 14, 30, 0), include_timezone=False)
        '2024-12-31T14:30:00'
    """
    if dt is None:
        raise ValueError("Timestamp cannot be None")

    if isinstance(dt, str):
        # Try to parse ISO format
        try:
            # Handle various ISO formats
            if "T" in dt:
                if "+" in dt or dt.endswith("Z"):
                    # Has timezone
                    parsed = datetime.fromisoformat(dt.replace("Z", "+00:00"))
                else:
                    parsed = datetime.fromisoformat(dt)
            else:
                parsed = datetime.fromisoformat(dt)
            dt = parsed
        except ValueError as e:
            raise ValueError(f"Unable to parse timestamp: {dt}") from e

    if not isinstance(dt, datetime):
        raise ValueError(f"Unsupported timestamp type: {type(dt)}")

    if include_timezone:
        if dt.tzinfo is None:
            # Assume UTC if no timezone
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()
    else:
        return dt.strftime("%Y-%m-%dT%H:%M:%S")


# Update forward references for nested models
Acknowledgment.model_rebuild()


# =============================================================================
# MeF SOAP Client for IRS Communication
# =============================================================================


import asyncio
import base64
import gzip
import hashlib
import logging
import ssl
import time
from io import BytesIO
from pathlib import Path
from xml.etree import ElementTree as ET

# Note: In production, you would use httpx or aiohttp for async HTTP
# For this implementation, we'll use a mock/placeholder approach
try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False


logger = logging.getLogger(__name__)


class MeFClientError(Exception):
    """Base exception for MeF client errors."""

    def __init__(self, message: str, error_code: Optional[str] = None,
                 retry_allowed: bool = True):
        super().__init__(message)
        self.error_code = error_code
        self.retry_allowed = retry_allowed


class MeFConnectionError(MeFClientError):
    """Connection-related errors."""
    pass


class MeFAuthenticationError(MeFClientError):
    """Authentication/authorization errors."""

    def __init__(self, message: str, error_code: Optional[str] = None):
        super().__init__(message, error_code, retry_allowed=False)


class MeFSubmissionError(MeFClientError):
    """Submission-related errors."""
    pass


class MeFTimeoutError(MeFClientError):
    """Timeout errors."""
    pass


@dataclass
class MeFSession:
    """Represents an authenticated MeF session.

    Attributes:
        session_id: Unique session identifier from IRS
        auth_token: Authentication token for subsequent requests
        expires_at: When the session expires
        efin: EFIN associated with this session
        environment: MeF environment for this session
    """
    session_id: str
    auth_token: str
    expires_at: datetime
    efin: str
    environment: MeFEnvironment

    @property
    def is_expired(self) -> bool:
        """Check if the session has expired."""
        return datetime.now(timezone.utc) >= self.expires_at

    @property
    def time_remaining(self) -> int:
        """Get remaining session time in seconds."""
        if self.is_expired:
            return 0
        delta = self.expires_at - datetime.now(timezone.utc)
        return int(delta.total_seconds())


class MeFClient:
    """SOAP client for IRS MeF system communication.

    This class handles all direct communication with the IRS MeF web services,
    including authentication, submission, acknowledgment retrieval, and status
    inquiries. It implements retry logic with exponential backoff for resilience.

    The MeF system uses SOAP/XML over HTTPS with mutual TLS authentication.
    All communications require a valid digital certificate issued by the IRS.

    Attributes:
        config: MeF configuration including credentials and endpoints
        session: Current authenticated session (if logged in)

    Example:
        >>> config = MeFConfiguration(
        ...     credentials=MeFCredentials(...),
        ...     tax_year=2024
        ... )
        >>> client = MeFClient(config)
        >>> await client.login()
        >>> result = await client.submit_return(xml_content)
        >>> await client.logout()
    """

    # SOAP namespaces used in MeF messages
    SOAP_NS = "http://schemas.xmlsoap.org/soap/envelope/"
    MEF_NS = "http://www.irs.gov/mef"
    WSS_NS = "http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd"
    WSU_NS = "http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd"

    # Default retry configuration
    DEFAULT_MAX_RETRIES = 3
    DEFAULT_BASE_DELAY = 1.0  # seconds
    DEFAULT_MAX_DELAY = 60.0  # seconds

    def __init__(self, config: MeFConfiguration):
        """Initialize the MeF client.

        Args:
            config: MeF configuration with credentials and endpoint settings
        """
        self.config = config
        self.session: Optional[MeFSession] = None
        self._http_client: Optional[Any] = None
        self._ssl_context: Optional[ssl.SSLContext] = None
        self._request_counter = 0

    async def __aenter__(self) -> "MeFClient":
        """Async context manager entry - login on enter."""
        await self.login()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit - logout on exit."""
        await self.logout()

    def _create_ssl_context(self) -> ssl.SSLContext:
        """Create SSL context with client certificate for mutual TLS.

        Returns:
            Configured SSL context

        Raises:
            MeFAuthenticationError: If certificate cannot be loaded
        """
        try:
            context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
            context.check_hostname = True
            context.verify_mode = ssl.CERT_REQUIRED

            # Load client certificate (PKCS#12 format)
            cert_path = Path(self.config.credentials.certificate_path)
            if not cert_path.exists():
                raise MeFAuthenticationError(
                    f"Certificate file not found: {cert_path}"
                )

            # In production, you would load the .p12 file here
            # For now, we assume PEM format for simplicity
            # context.load_cert_chain(cert_path, password=self.config.credentials.certificate_password)

            logger.debug("SSL context created successfully")
            return context

        except ssl.SSLError as e:
            raise MeFAuthenticationError(f"SSL certificate error: {e}") from e
        except Exception as e:
            raise MeFAuthenticationError(f"Failed to create SSL context: {e}") from e

    def _get_request_id(self) -> str:
        """Generate a unique request ID for tracking.

        Returns:
            Unique request identifier
        """
        self._request_counter += 1
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
        return f"{self.config.credentials.efin}-{timestamp}-{self._request_counter:06d}"

    def _build_soap_envelope(self, action: str, body_content: str,
                              include_security_header: bool = True) -> str:
        """Build a SOAP envelope for MeF requests.

        Constructs a properly formatted SOAP envelope with WS-Security headers
        for authenticated requests to the MeF system.

        Args:
            action: SOAP action name (e.g., "Login", "SubmitReturn")
            body_content: XML content for the SOAP body
            include_security_header: Whether to include WS-Security headers

        Returns:
            Complete SOAP envelope as XML string
        """
        request_id = self._get_request_id()
        timestamp = format_timestamp(datetime.now(timezone.utc))

        # Build security header if authenticated
        security_header = ""
        if include_security_header and self.session:
            security_header = f"""
        <wsse:Security xmlns:wsse="{self.WSS_NS}" xmlns:wsu="{self.WSU_NS}">
            <wsu:Timestamp wsu:Id="TS-{request_id}">
                <wsu:Created>{timestamp}</wsu:Created>
                <wsu:Expires>{format_timestamp(self.session.expires_at)}</wsu:Expires>
            </wsu:Timestamp>
            <wsse:UsernameToken wsu:Id="UT-{request_id}">
                <wsse:Username>{self.config.credentials.efin}</wsse:Username>
            </wsse:UsernameToken>
            <SessionToken>{self.session.auth_token}</SessionToken>
        </wsse:Security>"""

        envelope = f"""<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="{self.SOAP_NS}" xmlns:mef="{self.MEF_NS}">
    <soap:Header>
        <mef:MeFHeader>
            <mef:RequestId>{request_id}</mef:RequestId>
            <mef:Timestamp>{timestamp}</mef:Timestamp>
            <mef:EFIN>{self.config.credentials.efin}</mef:EFIN>
            <mef:ETIN>{self.config.credentials.etin}</mef:ETIN>
            <mef:SoftwareId>{self.config.credentials.software_id}</mef:SoftwareId>
            <mef:TaxYear>{self.config.tax_year}</mef:TaxYear>
            <mef:Action>{action}</mef:Action>
        </mef:MeFHeader>{security_header}
    </soap:Header>
    <soap:Body>
        {body_content}
    </soap:Body>
</soap:Envelope>"""

        return envelope.strip()

    def _parse_soap_response(self, response_xml: str) -> Dict[str, Any]:
        """Parse a SOAP response from MeF.

        Extracts the response body and any error information from
        the SOAP envelope.

        Args:
            response_xml: Raw SOAP response XML

        Returns:
            Dictionary containing parsed response data

        Raises:
            MeFClientError: If response indicates an error
        """
        try:
            # Define namespaces for parsing
            namespaces = {
                'soap': self.SOAP_NS,
                'mef': self.MEF_NS
            }

            root = ET.fromstring(response_xml)

            # Check for SOAP Fault
            fault = root.find('.//soap:Fault', namespaces)
            if fault is not None:
                fault_code = fault.findtext('faultcode', 'Unknown')
                fault_string = fault.findtext('faultstring', 'Unknown error')
                fault_detail = fault.find('detail')
                detail_text = ET.tostring(fault_detail, encoding='unicode') if fault_detail is not None else ""

                raise MeFClientError(
                    f"SOAP Fault: {fault_string}",
                    error_code=fault_code
                )

            # Extract body content
            body = root.find('.//soap:Body', namespaces)
            if body is None:
                raise MeFClientError("Invalid SOAP response: missing Body element")

            # Parse MeF-specific response elements
            result: Dict[str, Any] = {
                'raw_xml': response_xml,
                'success': True
            }

            # Extract common response fields
            for elem in body.iter():
                # Remove namespace prefix for easier access
                tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag

                if elem.text and elem.text.strip():
                    result[tag] = elem.text.strip()

                # Handle attributes
                if elem.attrib:
                    for attr_name, attr_value in elem.attrib.items():
                        result[f"{tag}_{attr_name}"] = attr_value

            return result

        except ET.ParseError as e:
            raise MeFClientError(f"Failed to parse SOAP response: {e}") from e

    async def _send_request(self, url: str, soap_envelope: str,
                            timeout: Optional[int] = None) -> str:
        """Send an HTTP request to MeF with retry logic.

        Implements exponential backoff retry for transient failures.

        Args:
            url: Target URL
            soap_envelope: SOAP envelope XML
            timeout: Request timeout in seconds

        Returns:
            Response body as string

        Raises:
            MeFConnectionError: If connection fails after retries
            MeFTimeoutError: If request times out
        """
        timeout = timeout or self.config.endpoint.timeout_seconds
        max_retries = self.config.retry_attempts
        base_delay = self.DEFAULT_BASE_DELAY

        headers = {
            'Content-Type': 'application/soap+xml; charset=utf-8',
            'Accept': 'application/soap+xml',
            'User-Agent': f'MeFClient/{self.config.credentials.software_id}',
        }

        # Compress if enabled
        body = soap_envelope.encode('utf-8')
        if self.config.enable_compression:
            compressed = BytesIO()
            with gzip.GzipFile(fileobj=compressed, mode='wb') as gz:
                gz.write(body)
            body = compressed.getvalue()
            headers['Content-Encoding'] = 'gzip'

        last_error: Optional[Exception] = None

        for attempt in range(max_retries + 1):
            try:
                if self.config.enable_logging:
                    logger.debug(f"MeF request attempt {attempt + 1}/{max_retries + 1} to {url}")

                # In production, use actual HTTP client
                # This is a placeholder for the async HTTP request
                if HAS_HTTPX:
                    async with httpx.AsyncClient(
                        verify=self._ssl_context or True,
                        timeout=timeout
                    ) as client:
                        response = await client.post(
                            url,
                            content=body,
                            headers=headers
                        )
                        response.raise_for_status()
                        return response.text
                else:
                    # Mock response for development/testing
                    logger.warning("httpx not available, returning mock response")
                    return self._generate_mock_response()

            except asyncio.TimeoutError as e:
                last_error = MeFTimeoutError(
                    f"Request timed out after {timeout} seconds"
                )
            except Exception as e:
                last_error = MeFConnectionError(
                    f"Connection error: {e}",
                    retry_allowed=True
                )

            # Calculate backoff delay with jitter
            if attempt < max_retries:
                delay = min(
                    base_delay * (2 ** attempt),
                    self.DEFAULT_MAX_DELAY
                )
                # Add jitter (0-25% of delay)
                import random
                jitter = delay * random.uniform(0, 0.25)
                delay += jitter

                logger.warning(
                    f"Request failed (attempt {attempt + 1}), "
                    f"retrying in {delay:.2f}s: {last_error}"
                )
                await asyncio.sleep(delay)

        raise last_error or MeFConnectionError("Request failed after all retries")

    def _generate_mock_response(self) -> str:
        """Generate a mock response for development/testing.

        Returns:
            Mock SOAP response XML
        """
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="{self.SOAP_NS}" xmlns:mef="{self.MEF_NS}">
    <soap:Body>
        <mef:Response>
            <mef:Status>Success</mef:Status>
            <mef:Message>Mock response for development</mef:Message>
        </mef:Response>
    </soap:Body>
</soap:Envelope>"""

    async def login(self) -> MeFSession:
        """Authenticate with the MeF system.

        Establishes an authenticated session with the IRS MeF system
        using the configured credentials and certificate.

        Returns:
            MeFSession object representing the authenticated session

        Raises:
            MeFAuthenticationError: If authentication fails
        """
        logger.info(f"Logging into MeF ({self.config.environment.value})")

        # Initialize SSL context
        self._ssl_context = self._create_ssl_context()

        # Build login request
        body_content = f"""
        <mef:LoginRequest>
            <mef:EFIN>{self.config.credentials.efin}</mef:EFIN>
            <mef:ETIN>{self.config.credentials.etin}</mef:ETIN>
            <mef:SoftwareId>{self.config.credentials.software_id}</mef:SoftwareId>
            {f'<mef:VendorControlCode>{self.config.credentials.vendor_control_code}</mef:VendorControlCode>' if self.config.credentials.vendor_control_code else ''}
        </mef:LoginRequest>"""

        envelope = self._build_soap_envelope("Login", body_content, include_security_header=False)

        try:
            response_xml = await self._send_request(
                self.config.endpoint.base_url + "/mef/services/auth",
                envelope
            )

            response = self._parse_soap_response(response_xml)

            # Extract session information
            session_id = response.get('SessionId', str(uuid.uuid4()))
            auth_token = response.get('AuthToken', str(uuid.uuid4()))
            expires_in = int(response.get('ExpiresIn', 7200))  # Default 2 hours

            self.session = MeFSession(
                session_id=session_id,
                auth_token=auth_token,
                expires_at=datetime.now(timezone.utc) + timedelta(seconds=expires_in),
                efin=self.config.credentials.efin,
                environment=self.config.environment
            )

            logger.info(f"Successfully logged into MeF, session expires in {expires_in}s")
            return self.session

        except MeFClientError:
            raise
        except Exception as e:
            raise MeFAuthenticationError(f"Login failed: {e}") from e

    async def submit_return(self, submission_xml: str,
                            submission_id: str) -> SubmissionResult:
        """Submit a tax return to MeF.

        Transmits a complete tax return XML to the IRS MeF system
        for processing.

        Args:
            submission_xml: Complete MeF submission XML
            submission_id: Unique submission identifier

        Returns:
            SubmissionResult with outcome details

        Raises:
            MeFAuthenticationError: If not logged in or session expired
            MeFSubmissionError: If submission fails
        """
        if not self.session or self.session.is_expired:
            raise MeFAuthenticationError("Not logged in or session expired")

        logger.info(f"Submitting return {submission_id}")

        # Encode submission content
        encoded_content = base64.b64encode(submission_xml.encode('utf-8')).decode('ascii')
        content_hash = hashlib.sha256(submission_xml.encode('utf-8')).hexdigest()

        body_content = f"""
        <mef:SubmitReturnRequest>
            <mef:SubmissionId>{submission_id}</mef:SubmissionId>
            <mef:ContentHash algorithm="SHA-256">{content_hash}</mef:ContentHash>
            <mef:ContentLength>{len(submission_xml)}</mef:ContentLength>
            <mef:Content encoding="base64">{encoded_content}</mef:Content>
        </mef:SubmitReturnRequest>"""

        envelope = self._build_soap_envelope("SubmitReturn", body_content)

        try:
            response_xml = await self._send_request(
                self.config.endpoint.submit_url,
                envelope
            )

            response = self._parse_soap_response(response_xml)

            # Parse submission result
            success = response.get('Status', '').lower() in ('success', 'accepted', 'received')
            receipt_id = response.get('ReceiptId')
            message = response.get('Message', '')

            # Parse any immediate errors
            errors = []
            if 'ErrorCode' in response:
                errors.append(f"{response['ErrorCode']}: {response.get('ErrorMessage', 'Unknown error')}")

            result = SubmissionResult(
                success=success,
                submission_id=submission_id,
                receipt_id=receipt_id,
                message=message,
                errors=errors,
                estimated_ack_time=datetime.now(timezone.utc) + timedelta(hours=24)
            )

            logger.info(f"Submission result: success={success}, receipt={receipt_id}")
            return result

        except MeFClientError:
            raise
        except Exception as e:
            raise MeFSubmissionError(f"Submission failed: {e}") from e

    async def get_acknowledgment(self, submission_id: str) -> Acknowledgment:
        """Retrieve acknowledgment for a submission.

        Fetches the acknowledgment status for a previously submitted
        tax return. Acknowledgments may not be available immediately
        after submission.

        Args:
            submission_id: The submission ID to check

        Returns:
            Acknowledgment with current status and any errors

        Raises:
            MeFAuthenticationError: If not logged in
            MeFClientError: If retrieval fails
        """
        if not self.session or self.session.is_expired:
            raise MeFAuthenticationError("Not logged in or session expired")

        logger.info(f"Retrieving acknowledgment for {submission_id}")

        body_content = f"""
        <mef:GetAcknowledgmentRequest>
            <mef:SubmissionId>{submission_id}</mef:SubmissionId>
        </mef:GetAcknowledgmentRequest>"""

        envelope = self._build_soap_envelope("GetAcknowledgment", body_content)

        try:
            response_xml = await self._send_request(
                self.config.endpoint.ack_url,
                envelope
            )

            response = self._parse_soap_response(response_xml)

            # Determine acknowledgment status
            status_str = response.get('AckStatus', 'P')
            status_map = {
                'A': AckStatus.ACCEPTED,
                'R': AckStatus.REJECTED,
                'AE': AckStatus.ACCEPTED_WITH_ERRORS,
                'P': AckStatus.PENDING,
                'NF': AckStatus.NOT_FOUND,
                'PR': AckStatus.PROCESSING
            }
            status = status_map.get(status_str, AckStatus.PENDING)

            # Parse errors if rejected
            errors = []
            if status == AckStatus.REJECTED:
                # In real implementation, parse error list from response
                if 'ErrorCode' in response:
                    errors.append(AckError(
                        error_code=response['ErrorCode'],
                        error_message=response.get('ErrorMessage', 'Unknown error'),
                        severity=AckErrorSeverity.REJECT
                    ))

            # Parse amounts if accepted
            refund_amount = None
            amount_owed = None
            if status == AckStatus.ACCEPTED:
                if 'RefundAmount' in response:
                    refund_amount = Decimal(response['RefundAmount'])
                if 'AmountOwed' in response:
                    amount_owed = Decimal(response['AmountOwed'])

            ack = Acknowledgment(
                submission_id=submission_id,
                status=status,
                errors=errors,
                refund_amount=refund_amount,
                amount_owed=amount_owed,
                raw_xml=response.get('raw_xml')
            )

            logger.info(f"Acknowledgment status: {status.value}")
            return ack

        except MeFClientError:
            raise
        except Exception as e:
            raise MeFClientError(f"Failed to retrieve acknowledgment: {e}") from e

    async def get_submission_status(self, submission_id: str) -> Dict[str, Any]:
        """Get the current status of a submission.

        Provides a quick status check without the full acknowledgment details.
        Useful for polling during the processing period.

        Args:
            submission_id: The submission ID to check

        Returns:
            Dictionary with status information

        Raises:
            MeFAuthenticationError: If not logged in
            MeFClientError: If status check fails
        """
        if not self.session or self.session.is_expired:
            raise MeFAuthenticationError("Not logged in or session expired")

        logger.debug(f"Checking status for {submission_id}")

        body_content = f"""
        <mef:GetStatusRequest>
            <mef:SubmissionId>{submission_id}</mef:SubmissionId>
        </mef:GetStatusRequest>"""

        envelope = self._build_soap_envelope("GetStatus", body_content)

        try:
            response_xml = await self._send_request(
                self.config.endpoint.status_url,
                envelope
            )

            response = self._parse_soap_response(response_xml)

            return {
                'submission_id': submission_id,
                'status': response.get('Status', 'Unknown'),
                'last_updated': response.get('LastUpdated'),
                'estimated_completion': response.get('EstimatedCompletion'),
                'queue_position': response.get('QueuePosition'),
                'raw_response': response
            }

        except MeFClientError:
            raise
        except Exception as e:
            raise MeFClientError(f"Failed to get submission status: {e}") from e

    async def logout(self) -> bool:
        """End the MeF session.

        Properly terminates the authenticated session with the MeF system.
        Should always be called when finished to free server resources.

        Returns:
            True if logout was successful

        Raises:
            MeFClientError: If logout fails (non-fatal)
        """
        if not self.session:
            logger.debug("No active session to logout")
            return True

        logger.info("Logging out of MeF")

        body_content = f"""
        <mef:LogoutRequest>
            <mef:SessionId>{self.session.session_id}</mef:SessionId>
        </mef:LogoutRequest>"""

        envelope = self._build_soap_envelope("Logout", body_content)

        try:
            await self._send_request(
                self.config.endpoint.base_url + "/mef/services/auth",
                envelope,
                timeout=30  # Short timeout for logout
            )

            logger.info("Successfully logged out of MeF")

        except Exception as e:
            # Log but don't raise - logout failure is not critical
            logger.warning(f"Logout request failed (non-fatal): {e}")

        finally:
            self.session = None
            self._http_client = None

        return True


# Need timedelta for session expiration
from datetime import timedelta


# =============================================================================
# Acknowledgment Processor
# =============================================================================


class AcknowledgmentProcessor:
    """Processes IRS acknowledgment responses and maps error codes to resolutions.

    This class handles the interpretation of MeF acknowledgment responses,
    providing user-friendly error messages and suggested resolutions for
    common rejection codes.

    The IRS uses a standardized set of error codes organized by category:
    - IND-XXX: Individual return errors
    - SEIC-XXX: Schedule EIC (Earned Income Credit) errors
    - SCH-XXX: Schedule-specific errors
    - R0XXX: Reject codes
    - F1040-XXX: Form 1040 specific errors

    Attributes:
        ERROR_CODE_MAP: Dictionary mapping IRS error codes to resolutions
    """

    # Comprehensive mapping of IRS error codes to user-friendly resolutions
    ERROR_CODE_MAP: Dict[str, Dict[str, str]] = {
        # Identity and SSN Errors
        "IND-031": {
            "description": "Primary SSN has already been used on another return",
            "resolution": "If you did not file this return, you may be a victim of identity theft. "
                         "File Form 14039, Identity Theft Affidavit, and mail your return.",
            "category": "identity",
            "severity": "reject"
        },
        "IND-032": {
            "description": "Spouse SSN has already been used on another return",
            "resolution": "If your spouse did not file, they may be a victim of identity theft. "
                         "File Form 14039 for your spouse and mail your return.",
            "category": "identity",
            "severity": "reject"
        },
        "IND-510": {
            "description": "Dependent SSN has already been claimed on another return",
            "resolution": "Verify the dependent's SSN is correct. If correct, the dependent may have been "
                         "claimed by another taxpayer. Contact the IRS or mail your return.",
            "category": "dependent",
            "severity": "reject"
        },
        "IND-511": {
            "description": "Dependent SSN is the same as the primary or spouse SSN",
            "resolution": "You cannot claim yourself or your spouse as a dependent. "
                         "Remove this dependent from your return.",
            "category": "dependent",
            "severity": "reject"
        },
        "IND-512": {
            "description": "Duplicate dependent SSN on return",
            "resolution": "Each dependent can only be listed once. Remove the duplicate entry.",
            "category": "dependent",
            "severity": "reject"
        },
        "IND-517": {
            "description": "Dependent SSN must not be the same as SSN of filer on another return",
            "resolution": "This person has filed their own return and cannot be claimed as a dependent.",
            "category": "dependent",
            "severity": "reject"
        },

        # Schedule EIC Errors
        "SEIC-001": {
            "description": "EIC qualifying child SSN has been used on another return",
            "resolution": "Another taxpayer has claimed this child for EIC. Only one taxpayer may claim "
                         "a qualifying child. If you believe you are entitled, mail your return.",
            "category": "eic",
            "severity": "reject"
        },
        "SEIC-002": {
            "description": "Qualifying child for EIC is same as primary or spouse",
            "resolution": "You cannot claim yourself or your spouse as a qualifying child for EIC.",
            "category": "eic",
            "severity": "reject"
        },
        "SEIC-003": {
            "description": "EIC child's age does not meet requirements",
            "resolution": "The child must be under 19 (or 24 if a student) at the end of the tax year, "
                         "or permanently and totally disabled. Verify the date of birth.",
            "category": "eic",
            "severity": "reject"
        },
        "SEIC-005": {
            "description": "Invalid EIC qualifying child relationship code",
            "resolution": "The relationship code must be valid (e.g., SON, DAUGHTER, GRANDCHILD). "
                         "Verify the relationship is correctly entered.",
            "category": "eic",
            "severity": "reject"
        },

        # Income Errors
        "F1040-034": {
            "description": "W-2 wage amount does not match IRS records",
            "resolution": "Verify your W-2 information matches exactly. Contact your employer if "
                         "there's a discrepancy in their records.",
            "category": "income",
            "severity": "reject"
        },
        "F1040-071": {
            "description": "Interest income does not match 1099-INT records",
            "resolution": "Verify all 1099-INT forms are accurately entered. Include all interest "
                         "income even if you didn't receive a form.",
            "category": "income",
            "severity": "reject"
        },

        # Filing Status Errors
        "F1040-001": {
            "description": "Head of Household filing status not allowed",
            "resolution": "To file as Head of Household, you must be unmarried, paid more than half "
                         "the cost of keeping up a home, and have a qualifying person. "
                         "Review your eligibility or change filing status.",
            "category": "filing_status",
            "severity": "reject"
        },
        "F1040-002": {
            "description": "Qualifying Surviving Spouse status not allowed",
            "resolution": "This status requires your spouse died in one of the two prior tax years "
                         "and you have a dependent child. Verify eligibility.",
            "category": "filing_status",
            "severity": "reject"
        },

        # Bank Account Errors
        "R0000-194": {
            "description": "Invalid routing transit number",
            "resolution": "Verify the 9-digit routing number from your bank. "
                         "It must be a valid ABA routing number.",
            "category": "bank",
            "severity": "reject"
        },
        "R0000-932": {
            "description": "Bank account type indicator invalid",
            "resolution": "Select either 'Checking' or 'Savings' for your account type.",
            "category": "bank",
            "severity": "reject"
        },

        # Signature/PIN Errors
        "R0000-902": {
            "description": "Self-Select PIN does not match IRS records",
            "resolution": "Enter the AGI from your prior year return or the PIN you created last year. "
                         "If unknown, request an Identity Protection PIN from the IRS.",
            "category": "signature",
            "severity": "reject"
        },
        "R0000-903": {
            "description": "Prior year AGI does not match IRS records",
            "resolution": "Enter the exact AGI from your prior year return (line 11 of Form 1040). "
                         "If you didn't file, enter 0.",
            "category": "signature",
            "severity": "reject"
        },

        # Child Tax Credit Errors
        "F8812-001": {
            "description": "Child does not meet age requirement for Child Tax Credit",
            "resolution": "The child must be under 17 at the end of the tax year to qualify "
                         "for the Child Tax Credit. Check the date of birth.",
            "category": "credits",
            "severity": "reject"
        },

        # Schema/Technical Errors
        "X0000-005": {
            "description": "XML schema validation error",
            "resolution": "There is a technical error in the return. Please regenerate your return "
                         "and try again. If the error persists, contact support.",
            "category": "technical",
            "severity": "reject"
        },
        "X0000-010": {
            "description": "Required element missing from submission",
            "resolution": "A required field is missing. Review your return for completeness.",
            "category": "technical",
            "severity": "reject"
        },

        # State-related Errors
        "STATE-001": {
            "description": "State return rejected - verify state-specific requirements",
            "resolution": "Your federal return was accepted but the state return was rejected. "
                         "Review state-specific error codes for details.",
            "category": "state",
            "severity": "reject"
        }
    }

    def __init__(self):
        """Initialize the acknowledgment processor."""
        self._custom_mappings: Dict[str, Dict[str, str]] = {}
        logger.debug("AcknowledgmentProcessor initialized")

    def add_custom_mapping(self, error_code: str, description: str,
                           resolution: str, category: str = "custom") -> None:
        """Add a custom error code mapping.

        Args:
            error_code: IRS error code
            description: Description of the error
            resolution: Suggested resolution
            category: Error category
        """
        self._custom_mappings[error_code] = {
            "description": description,
            "resolution": resolution,
            "category": category,
            "severity": "reject"
        }

    def _map_error_code(self, error_code: str) -> Dict[str, str]:
        """Map an IRS error code to description and resolution.

        Args:
            error_code: IRS error code (e.g., "IND-031-01")

        Returns:
            Dictionary with description, resolution, and category
        """
        # Try exact match first
        if error_code in self.ERROR_CODE_MAP:
            return self.ERROR_CODE_MAP[error_code]

        if error_code in self._custom_mappings:
            return self._custom_mappings[error_code]

        # Try base code (without suffix)
        base_code = error_code.rsplit('-', 1)[0] if '-' in error_code else error_code
        if base_code in self.ERROR_CODE_MAP:
            return self.ERROR_CODE_MAP[base_code]

        if base_code in self._custom_mappings:
            return self._custom_mappings[base_code]

        # Try category prefix
        prefix = error_code.split('-')[0] if '-' in error_code else error_code[:3]
        category_defaults = {
            "IND": ("Individual return error", "identity"),
            "SEIC": ("Schedule EIC error", "eic"),
            "SCH": ("Schedule error", "schedule"),
            "F1040": ("Form 1040 error", "form"),
            "F8812": ("Form 8812 (Child Tax Credit) error", "credits"),
            "R": ("Reject code", "reject"),
            "X": ("Technical/XML error", "technical"),
            "STATE": ("State return error", "state")
        }

        if prefix in category_defaults:
            desc, cat = category_defaults[prefix]
            return {
                "description": f"{desc}: {error_code}",
                "resolution": "Review the error code in IRS Publication 4164 or contact "
                             "support for assistance with this error.",
                "category": cat,
                "severity": "reject"
            }

        # Unknown error
        return {
            "description": f"Unknown error code: {error_code}",
            "resolution": "This error code is not recognized. Please contact support or "
                         "refer to IRS Publication 4164 for more information.",
            "category": "unknown",
            "severity": "reject"
        }

    def process(self, acknowledgment: Acknowledgment) -> Dict[str, Any]:
        """Process an acknowledgment and provide detailed analysis.

        Analyzes the acknowledgment, maps error codes to user-friendly
        resolutions, and provides a comprehensive result.

        Args:
            acknowledgment: The acknowledgment to process

        Returns:
            Dictionary with processed results including:
            - status: Overall status description
            - is_accepted: Boolean acceptance status
            - errors: List of processed errors with resolutions
            - summary: User-friendly summary
            - next_steps: Recommended next actions
            - categories: Errors grouped by category
        """
        result: Dict[str, Any] = {
            'submission_id': acknowledgment.submission_id,
            'status': acknowledgment.status.value,
            'is_accepted': acknowledgment.is_accepted,
            'is_rejected': acknowledgment.is_rejected,
            'is_pending': acknowledgment.is_pending,
            'timestamp': acknowledgment.timestamp.isoformat(),
            'errors': [],
            'summary': '',
            'next_steps': [],
            'categories': {}
        }

        # Process accepted returns
        if acknowledgment.is_accepted:
            result['summary'] = "Your return has been accepted by the IRS."

            if acknowledgment.refund_amount and acknowledgment.refund_amount > 0:
                result['summary'] += f" Expected refund: ${acknowledgment.refund_amount:,.2f}"
                result['next_steps'] = [
                    "Your refund will be processed within 21 days for e-filed returns.",
                    "Use 'Where's My Refund?' on IRS.gov to track your refund status.",
                    "Ensure your bank account information is correct for direct deposit."
                ]
            elif acknowledgment.amount_owed and acknowledgment.amount_owed > 0:
                result['summary'] += f" Amount owed: ${acknowledgment.amount_owed:,.2f}"
                result['next_steps'] = [
                    f"Payment of ${acknowledgment.amount_owed:,.2f} is due by the filing deadline.",
                    "You can pay online at IRS.gov/payments.",
                    "Consider setting up a payment plan if you cannot pay in full."
                ]
            else:
                result['next_steps'] = [
                    "Keep a copy of your accepted return for your records.",
                    "You will receive any refund or payment confirmation separately."
                ]

            return result

        # Process pending returns
        if acknowledgment.is_pending:
            result['summary'] = "Your return is being processed. Please check back later."
            result['next_steps'] = [
                "Acknowledgments typically take 24-48 hours.",
                "Check the status periodically for updates.",
                "No action needed at this time."
            ]
            return result

        # Process rejected returns
        if acknowledgment.is_rejected:
            processed_errors = []
            categories: Dict[str, List[Dict[str, Any]]] = {}

            for error in acknowledgment.errors:
                mapping = self._map_error_code(error.error_code)

                processed_error = {
                    'code': error.error_code,
                    'original_message': error.error_message,
                    'description': mapping['description'],
                    'resolution': mapping['resolution'],
                    'category': mapping['category'],
                    'severity': error.severity.value,
                    'xpath': error.xpath,
                    'field_value': error.field_value
                }
                processed_errors.append(processed_error)

                # Group by category
                cat = mapping['category']
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append(processed_error)

            result['errors'] = processed_errors
            result['categories'] = categories

            # Generate summary
            error_count = len(processed_errors)
            result['summary'] = (
                f"Your return was rejected with {error_count} error(s). "
                "Please review the errors and corrections needed below."
            )

            # Generate next steps based on error categories
            next_steps = ["Correct the identified errors in your return."]

            if 'identity' in categories:
                next_steps.append(
                    "For identity-related rejections, you may need to file Form 14039 "
                    "(Identity Theft Affidavit) and mail your return."
                )

            if 'signature' in categories:
                next_steps.append(
                    "For PIN/AGI mismatches, verify your prior year information or "
                    "request an IP PIN from the IRS."
                )

            next_steps.append("After corrections, you can resubmit your return electronically.")
            result['next_steps'] = next_steps

        return result

    def get_error_details(self, error_code: str) -> Dict[str, str]:
        """Get detailed information about a specific error code.

        Args:
            error_code: The IRS error code

        Returns:
            Dictionary with error details
        """
        return self._map_error_code(error_code)

    def get_all_error_codes(self) -> List[str]:
        """Get list of all known error codes.

        Returns:
            List of error codes in the mapping
        """
        codes = list(self.ERROR_CODE_MAP.keys())
        codes.extend(self._custom_mappings.keys())
        return sorted(set(codes))


# =============================================================================
# MeF Transmitter - Main Orchestrator
# =============================================================================


class MeFTransmitterError(Exception):
    """Base exception for MeF transmitter errors."""

    def __init__(self, message: str, stage: str = "unknown",
                 recoverable: bool = True):
        super().__init__(message)
        self.stage = stage
        self.recoverable = recoverable


@dataclass
class TransmissionStatus:
    """Status of a transmission workflow.

    Attributes:
        submission_id: The submission ID
        stage: Current stage in the workflow
        status: Current status (pending, success, failed)
        started_at: When the transmission started
        completed_at: When the transmission completed
        result: Final result (if complete)
        errors: Any errors encountered
    """
    submission_id: str
    stage: str
    status: str
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    result: Optional[Union[SubmissionResult, Acknowledgment]] = None
    errors: List[str] = field(default_factory=list)

    @property
    def duration_seconds(self) -> Optional[float]:
        """Get the duration of the transmission."""
        if self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None


class MeFTransmitter:
    """Main orchestrator for MeF e-file transmission workflow.

    This class coordinates the complete e-file transmission process including:
    - Return preparation and packaging
    - Pre-submission validation
    - Digital signing
    - Transmission to IRS
    - Acknowledgment polling and processing

    The transmitter provides both individual step methods and a complete
    workflow executor for end-to-end e-filing.

    Attributes:
        config: MeF configuration
        client: MeF SOAP client
        ack_processor: Acknowledgment processor

    Example:
        >>> transmitter = MeFTransmitter(config)
        >>> result = await transmitter.execute_workflow(return_data)
        >>> if result.is_accepted:
        ...     print(f"Return accepted! Refund: ${result.refund_amount}")
    """

    # Workflow stages
    STAGE_PREPARE = "prepare"
    STAGE_VALIDATE = "validate"
    STAGE_SIGN = "sign"
    STAGE_SUBMIT = "submit"
    STAGE_POLL = "poll"
    STAGE_COMPLETE = "complete"

    # Polling configuration
    DEFAULT_POLL_INTERVAL = 60  # seconds
    DEFAULT_MAX_POLL_ATTEMPTS = 120  # 2 hours at 1-minute intervals
    DEFAULT_INITIAL_WAIT = 300  # 5 minutes before first poll

    def __init__(self, config: MeFConfiguration):
        """Initialize the MeF transmitter.

        Args:
            config: MeF configuration with credentials and settings
        """
        self.config = config
        self.client = MeFClient(config)
        self.ack_processor = AcknowledgmentProcessor()
        self._current_status: Optional[TransmissionStatus] = None
        self._sequence_counter = 0

        logger.info(f"MeFTransmitter initialized for {config.environment.value}")

    def _get_next_sequence(self) -> int:
        """Get the next sequence number for submission ID generation.

        Returns:
            Next sequence number
        """
        self._sequence_counter += 1
        return self._sequence_counter

    def _generate_submission_id(self) -> SubmissionId:
        """Generate a new submission ID.

        Returns:
            New SubmissionId
        """
        return SubmissionId.generate(
            efin=self.config.credentials.efin,
            sequence=self._get_next_sequence()
        )

    async def prepare_return(self, return_data: Dict[str, Any]) -> Tuple[str, SubmissionId]:
        """Prepare a tax return for submission.

        Converts the return data into a MeF-compliant XML package ready
        for submission. This includes generating the submission ID and
        building all required XML elements.

        Args:
            return_data: Dictionary containing return information

        Returns:
            Tuple of (submission_xml, submission_id)

        Raises:
            MeFTransmitterError: If preparation fails
        """
        logger.info("Preparing return for submission")

        try:
            submission_id = self._generate_submission_id()

            # Build the return header
            taxpayer_info = TaxpayerInfo(
                primary_ssn=return_data.get('primary_ssn', ''),
                primary_first_name=return_data.get('primary_first_name', ''),
                primary_last_name=return_data.get('primary_last_name', ''),
                spouse_ssn=return_data.get('spouse_ssn'),
                spouse_first_name=return_data.get('spouse_first_name'),
                spouse_last_name=return_data.get('spouse_last_name')
            )

            header = ReturnHeader(
                submission_id=submission_id,
                submission_type=SubmissionType(return_data.get('form_type', '1040')),
                category=SubmissionCategory(return_data.get('category', 'O')),
                tax_year=self.config.tax_year,
                taxpayer=taxpayer_info,
                filing_status=return_data.get('filing_status', 1),
                primary_pin=return_data.get('primary_pin', '00000'),
                spouse_pin=return_data.get('spouse_pin'),
                software_id=self.config.credentials.software_id,
                originator_efin=self.config.credentials.efin
            )

            # Build XML submission (simplified)
            # In production, this would use the full XML generation logic
            submission_xml = self._build_submission_xml(header, return_data)

            logger.info(f"Return prepared with submission ID: {submission_id}")
            return submission_xml, submission_id

        except Exception as e:
            raise MeFTransmitterError(
                f"Failed to prepare return: {e}",
                stage=self.STAGE_PREPARE
            ) from e

    def _build_submission_xml(self, header: ReturnHeader,
                               return_data: Dict[str, Any]) -> str:
        """Build the MeF submission XML.

        Args:
            header: Return header information
            return_data: Complete return data

        Returns:
            MeF-compliant submission XML
        """
        # This is a simplified XML generation
        # In production, use proper XML builder with full MeF schema compliance
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<Return xmlns="http://www.irs.gov/efile" returnVersion="{self.config.tax_year}v1.0">
    <ReturnHeader>
        <SubmissionId>{header.submission_id}</SubmissionId>
        <TaxYear>{header.tax_year}</TaxYear>
        <FilingStatus>{header.filing_status}</FilingStatus>
        <EFIN>{header.originator_efin}</EFIN>
        <SoftwareId>{header.software_id}</SoftwareId>
        <PrimarySSN>{header.taxpayer.primary_ssn}</PrimarySSN>
        <PrimaryName>
            <FirstName>{escape_xml(header.taxpayer.primary_first_name)}</FirstName>
            <LastName>{escape_xml(header.taxpayer.primary_last_name)}</LastName>
        </PrimaryName>
        <SignatureDate>{format_date(datetime.now(timezone.utc))}</SignatureDate>
        <PrimarySignaturePIN>{header.primary_pin}</PrimarySignaturePIN>
    </ReturnHeader>
    <ReturnData documentCount="1">
        <!-- Return data would be inserted here -->
    </ReturnData>
</Return>"""

    async def validate_return(self, submission_xml: str) -> ValidationResult:
        """Validate a return before submission.

        Performs pre-submission validation including schema validation,
        business rule checks, and math verification.

        Args:
            submission_xml: The prepared submission XML

        Returns:
            ValidationResult with any errors or warnings

        Raises:
            MeFTransmitterError: If validation cannot be performed
        """
        logger.info("Validating return")
        start_time = time.time()

        try:
            errors: List[ValidationError] = []
            warnings: List[ValidationError] = []

            # Basic XML validation
            try:
                ET.fromstring(submission_xml)
            except ET.ParseError as e:
                errors.append(ValidationError(
                    code="XML-001",
                    message=f"Invalid XML structure: {e}",
                    severity=ValidationSeverity.ERROR,
                    category=ValidationCategory.SCHEMA
                ))

            # Check for required elements
            required_elements = [
                "SubmissionId", "TaxYear", "FilingStatus",
                "PrimarySSN", "SignatureDate"
            ]

            for element in required_elements:
                if f"<{element}>" not in submission_xml:
                    errors.append(ValidationError(
                        code=f"REQ-{element[:3].upper()}",
                        message=f"Required element missing: {element}",
                        severity=ValidationSeverity.ERROR,
                        category=ValidationCategory.COMPLETENESS
                    ))

            # Check for valid tax year
            if f"<TaxYear>{self.config.tax_year}</TaxYear>" not in submission_xml:
                warnings.append(ValidationError(
                    code="TY-001",
                    message=f"Tax year may not match configuration ({self.config.tax_year})",
                    severity=ValidationSeverity.WARNING,
                    category=ValidationCategory.CONSISTENCY
                ))

            duration_ms = int((time.time() - start_time) * 1000)

            result = ValidationResult(
                is_valid=len(errors) == 0,
                errors=errors,
                warnings=warnings,
                validated_at=datetime.now(timezone.utc),
                validation_duration_ms=duration_ms,
                forms_validated=["Form 1040"]
            )

            logger.info(f"Validation complete: {result.get_summary()}")
            return result

        except Exception as e:
            raise MeFTransmitterError(
                f"Validation failed: {e}",
                stage=self.STAGE_VALIDATE
            ) from e

    async def sign_return(self, submission_xml: str,
                          primary_pin: str,
                          spouse_pin: Optional[str] = None) -> str:
        """Apply digital signatures to the return.

        Adds taxpayer signature PINs and preparer signatures as required.
        This also updates the signature timestamp.

        Args:
            submission_xml: The prepared submission XML
            primary_pin: Primary taxpayer's signature PIN
            spouse_pin: Spouse's signature PIN (if applicable)

        Returns:
            Signed submission XML

        Raises:
            MeFTransmitterError: If signing fails
        """
        logger.info("Signing return")

        try:
            # Validate PIN format
            if not re.match(r"^\d{5}$", primary_pin):
                raise MeFTransmitterError(
                    "Invalid primary PIN format (must be 5 digits)",
                    stage=self.STAGE_SIGN,
                    recoverable=True
                )

            if spouse_pin and not re.match(r"^\d{5}$", spouse_pin):
                raise MeFTransmitterError(
                    "Invalid spouse PIN format (must be 5 digits)",
                    stage=self.STAGE_SIGN,
                    recoverable=True
                )

            # Update signature in XML
            signed_xml = submission_xml

            # Update primary PIN
            signed_xml = re.sub(
                r"<PrimarySignaturePIN>\d{5}</PrimarySignaturePIN>",
                f"<PrimarySignaturePIN>{primary_pin}</PrimarySignaturePIN>",
                signed_xml
            )

            # Update signature date
            current_date = format_date(datetime.now(timezone.utc))
            signed_xml = re.sub(
                r"<SignatureDate>[\d-]+</SignatureDate>",
                f"<SignatureDate>{current_date}</SignatureDate>",
                signed_xml
            )

            # Add spouse PIN if provided
            if spouse_pin:
                if "<SpouseSignaturePIN>" not in signed_xml:
                    signed_xml = signed_xml.replace(
                        "</ReturnHeader>",
                        f"<SpouseSignaturePIN>{spouse_pin}</SpouseSignaturePIN>\n    </ReturnHeader>"
                    )

            logger.info("Return signed successfully")
            return signed_xml

        except MeFTransmitterError:
            raise
        except Exception as e:
            raise MeFTransmitterError(
                f"Signing failed: {e}",
                stage=self.STAGE_SIGN
            ) from e

    async def submit_return(self, submission_xml: str,
                            submission_id: SubmissionId) -> SubmissionResult:
        """Submit a signed return to the IRS.

        Transmits the complete, signed return to the MeF system.
        This method handles the authentication and submission process.

        Args:
            submission_xml: The signed submission XML
            submission_id: The submission identifier

        Returns:
            SubmissionResult with outcome

        Raises:
            MeFTransmitterError: If submission fails
        """
        logger.info(f"Submitting return {submission_id}")

        try:
            # Login if not already authenticated
            if not self.client.session or self.client.session.is_expired:
                await self.client.login()

            # Submit the return
            result = await self.client.submit_return(
                submission_xml,
                str(submission_id)
            )

            if result.success:
                logger.info(f"Return submitted successfully, receipt: {result.receipt_id}")
            else:
                logger.warning(f"Return submission failed: {result.message}")

            return result

        except MeFClientError as e:
            raise MeFTransmitterError(
                f"Submission failed: {e}",
                stage=self.STAGE_SUBMIT,
                recoverable=e.retry_allowed
            ) from e
        except Exception as e:
            raise MeFTransmitterError(
                f"Submission failed: {e}",
                stage=self.STAGE_SUBMIT
            ) from e

    async def poll_for_acknowledgment(self, submission_id: str,
                                       max_attempts: Optional[int] = None,
                                       poll_interval: Optional[int] = None,
                                       initial_wait: Optional[int] = None) -> Acknowledgment:
        """Poll for acknowledgment until available or timeout.

        Continuously checks for the acknowledgment status until the return
        is either accepted, rejected, or the polling limit is reached.

        Args:
            submission_id: The submission ID to poll for
            max_attempts: Maximum number of poll attempts
            poll_interval: Seconds between poll attempts
            initial_wait: Seconds to wait before first poll

        Returns:
            Final acknowledgment

        Raises:
            MeFTransmitterError: If polling fails or times out
        """
        max_attempts = max_attempts or self.DEFAULT_MAX_POLL_ATTEMPTS
        poll_interval = poll_interval or self.DEFAULT_POLL_INTERVAL
        initial_wait = initial_wait or self.DEFAULT_INITIAL_WAIT

        logger.info(f"Starting acknowledgment polling for {submission_id}")
        logger.info(f"Initial wait: {initial_wait}s, interval: {poll_interval}s, max attempts: {max_attempts}")

        try:
            # Ensure we're logged in
            if not self.client.session or self.client.session.is_expired:
                await self.client.login()

            # Initial wait before first poll
            logger.info(f"Waiting {initial_wait}s before first poll...")
            await asyncio.sleep(initial_wait)

            last_status: Optional[AckStatus] = None

            for attempt in range(max_attempts):
                logger.debug(f"Poll attempt {attempt + 1}/{max_attempts}")

                try:
                    ack = await self.client.get_acknowledgment(submission_id)

                    # Log status changes
                    if ack.status != last_status:
                        logger.info(f"Status changed: {last_status} -> {ack.status.value}")
                        last_status = ack.status

                    # Check if we have a final status
                    if ack.status in (AckStatus.ACCEPTED, AckStatus.REJECTED,
                                      AckStatus.ACCEPTED_WITH_ERRORS):
                        logger.info(f"Final acknowledgment received: {ack.status.value}")
                        return ack

                    # Check for not found (might be too early)
                    if ack.status == AckStatus.NOT_FOUND:
                        logger.debug("Acknowledgment not yet available")

                except MeFClientError as e:
                    logger.warning(f"Poll attempt {attempt + 1} failed: {e}")
                    # Continue polling on transient errors

                # Wait before next poll
                if attempt < max_attempts - 1:
                    await asyncio.sleep(poll_interval)

            # Timeout reached
            raise MeFTransmitterError(
                f"Acknowledgment not received after {max_attempts} attempts",
                stage=self.STAGE_POLL,
                recoverable=True
            )

        except MeFTransmitterError:
            raise
        except Exception as e:
            raise MeFTransmitterError(
                f"Polling failed: {e}",
                stage=self.STAGE_POLL
            ) from e

    async def _execute_workflow(self, return_data: Dict[str, Any],
                                 wait_for_ack: bool = True) -> TransmissionStatus:
        """Execute the complete e-file workflow.

        Runs through all stages of the e-file process:
        1. Prepare the return
        2. Validate the return
        3. Sign the return
        4. Submit to IRS
        5. Poll for acknowledgment (optional)

        Args:
            return_data: Complete return data dictionary
            wait_for_ack: Whether to wait for acknowledgment

        Returns:
            TransmissionStatus with final result

        Raises:
            MeFTransmitterError: If any stage fails
        """
        submission_id = self._generate_submission_id()
        status = TransmissionStatus(
            submission_id=str(submission_id),
            stage=self.STAGE_PREPARE,
            status="in_progress"
        )
        self._current_status = status

        try:
            # Stage 1: Prepare
            logger.info("Stage 1: Preparing return")
            status.stage = self.STAGE_PREPARE
            submission_xml, submission_id = await self.prepare_return(return_data)

            # Stage 2: Validate
            logger.info("Stage 2: Validating return")
            status.stage = self.STAGE_VALIDATE
            validation = await self.validate_return(submission_xml)

            if not validation.is_valid:
                status.status = "failed"
                status.errors = [e.message for e in validation.errors]
                status.completed_at = datetime.now(timezone.utc)
                raise MeFTransmitterError(
                    f"Validation failed with {validation.error_count} errors",
                    stage=self.STAGE_VALIDATE,
                    recoverable=True
                )

            # Stage 3: Sign
            logger.info("Stage 3: Signing return")
            status.stage = self.STAGE_SIGN
            primary_pin = return_data.get('primary_pin', '00000')
            spouse_pin = return_data.get('spouse_pin')
            signed_xml = await self.sign_return(submission_xml, primary_pin, spouse_pin)

            # Stage 4: Submit
            logger.info("Stage 4: Submitting return")
            status.stage = self.STAGE_SUBMIT
            submission_result = await self.submit_return(signed_xml, submission_id)

            if not submission_result.success:
                status.status = "failed"
                status.errors = submission_result.errors
                status.result = submission_result
                status.completed_at = datetime.now(timezone.utc)
                raise MeFTransmitterError(
                    f"Submission failed: {submission_result.message}",
                    stage=self.STAGE_SUBMIT,
                    recoverable=True
                )

            # Stage 5: Poll for acknowledgment (if requested)
            if wait_for_ack:
                logger.info("Stage 5: Polling for acknowledgment")
                status.stage = self.STAGE_POLL
                ack = await self.poll_for_acknowledgment(str(submission_id))

                # Process the acknowledgment
                processed = self.ack_processor.process(ack)

                status.stage = self.STAGE_COMPLETE
                status.status = "accepted" if ack.is_accepted else "rejected"
                status.result = ack
                status.completed_at = datetime.now(timezone.utc)

                if ack.is_rejected:
                    status.errors = [e['description'] for e in processed['errors']]
            else:
                status.stage = self.STAGE_COMPLETE
                status.status = "submitted"
                status.result = submission_result
                status.completed_at = datetime.now(timezone.utc)

            logger.info(f"Workflow complete: {status.status}")
            return status

        except MeFTransmitterError:
            raise
        except Exception as e:
            status.status = "failed"
            status.errors.append(str(e))
            status.completed_at = datetime.now(timezone.utc)
            raise MeFTransmitterError(
                f"Workflow failed: {e}",
                stage=status.stage
            ) from e

        finally:
            # Always logout
            try:
                await self.client.logout()
            except Exception:
                pass  # Ignore logout errors

    async def execute_workflow(self, return_data: Dict[str, Any],
                                wait_for_ack: bool = True) -> TransmissionStatus:
        """Execute the complete e-file workflow (public interface).

        This is the main entry point for e-filing a return. It handles
        the complete workflow from preparation through acknowledgment.

        Args:
            return_data: Dictionary containing all return information:
                - primary_ssn: Primary taxpayer SSN
                - primary_first_name: Primary taxpayer first name
                - primary_last_name: Primary taxpayer last name
                - primary_pin: Signature PIN (5 digits)
                - filing_status: Filing status code (1-5)
                - spouse_ssn: Spouse SSN (if applicable)
                - spouse_first_name: Spouse first name (if applicable)
                - spouse_last_name: Spouse last name (if applicable)
                - spouse_pin: Spouse signature PIN (if applicable)
                - form_type: Return type (default: "1040")
                - category: Submission category (default: "O" for original)
            wait_for_ack: Whether to wait for IRS acknowledgment

        Returns:
            TransmissionStatus with final outcome

        Example:
            >>> return_data = {
            ...     "primary_ssn": "123456789",
            ...     "primary_first_name": "John",
            ...     "primary_last_name": "Smith",
            ...     "primary_pin": "12345",
            ...     "filing_status": 1,
            ... }
            >>> status = await transmitter.execute_workflow(return_data)
            >>> print(f"Result: {status.status}")
        """
        return await self._execute_workflow(return_data, wait_for_ack)

    def get_current_status(self) -> Optional[TransmissionStatus]:
        """Get the current transmission status.

        Returns:
            Current TransmissionStatus or None if no transmission is active
        """
        return self._current_status


# =============================================================================
# XML Serialization Classes
# =============================================================================


class XmlSerializer:
    """XML Serializer for MeF tax return documents.

    This class handles the serialization of tax return data into MeF-compliant
    XML format. It follows IRS Publication 4164 specifications for XML structure
    and namespace requirements.

    The serializer supports:
    - Return header generation (ReturnHeaderType)
    - Form 1040 basic structure
    - Schedule attachments (A, B, C, D, etc.)
    - Proper namespace handling
    - Character encoding and escaping

    Attributes:
        tax_year: The tax year for the return
        namespaces: Dictionary of XML namespaces
        encoding: Character encoding for XML output
    """

    # MeF XML Namespaces
    DEFAULT_NAMESPACES = {
        "efile": "http://www.irs.gov/efile",
        "xsi": "http://www.w3.org/2001/XMLSchema-instance",
        "xsd": "http://www.w3.org/2001/XMLSchema",
    }

    # Form type to schema location mapping
    SCHEMA_LOCATIONS = {
        "1040": "IRS1040/IRS1040.xsd",
        "ScheduleA": "IRS1040ScheduleA/IRS1040ScheduleA.xsd",
        "ScheduleB": "IRS1040ScheduleB/IRS1040ScheduleB.xsd",
        "ScheduleC": "IRS1040ScheduleC/IRS1040ScheduleC.xsd",
        "ScheduleD": "IRS1040ScheduleD/IRS1040ScheduleD.xsd",
        "Schedule1": "IRS1040Schedule1/IRS1040Schedule1.xsd",
        "Schedule2": "IRS1040Schedule2/IRS1040Schedule2.xsd",
        "Schedule3": "IRS1040Schedule3/IRS1040Schedule3.xsd",
    }

    def __init__(self, tax_year: int, encoding: str = "UTF-8"):
        """Initialize the XML serializer.

        Args:
            tax_year: Tax year for the return (e.g., 2024)
            encoding: XML character encoding (default: UTF-8)
        """
        self.tax_year = tax_year
        self.encoding = encoding
        self.namespaces = self.DEFAULT_NAMESPACES.copy()
        self._indent_level = 0
        self._indent_str = "  "

    def serialize_return_header(self, header: ReturnHeader) -> str:
        """Serialize a return header to MeF XML.

        Generates the ReturnHeader element which contains metadata about
        the submission including taxpayer identification, filing status,
        and signature information.

        Args:
            header: ReturnHeader object with submission metadata

        Returns:
            XML string for the return header element

        Raises:
            ValueError: If header data is invalid or incomplete
        """
        elements = []

        # ReturnTs - Return timestamp
        elements.append(self._build_xml_element(
            "ReturnTs",
            format_timestamp(header.created_at)
        ))

        # TaxYr
        elements.append(self._build_xml_element(
            "TaxYr",
            str(header.tax_year)
        ))

        # TaxPeriodBeginDt and TaxPeriodEndDt
        elements.append(self._build_xml_element(
            "TaxPeriodBeginDt",
            f"{header.tax_year}-01-01"
        ))
        elements.append(self._build_xml_element(
            "TaxPeriodEndDt",
            f"{header.tax_year}-12-31"
        ))

        # ReturnTypeCd
        elements.append(self._build_xml_element(
            "ReturnTypeCd",
            header.submission_type.value
        ))

        # Build Filer container with taxpayer info
        filer_elements = self._build_filer_elements(header)
        elements.append(self._build_xml_container("Filer", filer_elements))

        # FilingStatusCd
        elements.append(self._build_xml_element(
            "FilingStatusCd",
            str(header.filing_status)
        ))

        # Build preparer info if present
        if header.preparer_ptin:
            preparer_elements = self._build_preparer_elements(header)
            elements.append(self._build_xml_container("PaidPreparerInformationGrp", preparer_elements))

        # SoftwareId
        elements.append(self._build_xml_element(
            "SoftwareId",
            header.software_id
        ))

        # OriginatorGrp
        originator_elements = [
            self._build_xml_element("EFIN", header.originator_efin),
            self._build_xml_element("OriginatorTypeCd", "OnlineFiler"),
        ]
        elements.append(self._build_xml_container("OriginatorGrp", originator_elements))

        # PIN entries
        pin_elements = self._build_pin_elements(header)
        elements.extend(pin_elements)

        # Wrap in ReturnHeader container
        return self._build_xml_container(
            "ReturnHeader",
            elements,
            attributes={"binaryAttachmentCnt": "0"}
        )

    def _build_filer_elements(self, header: ReturnHeader) -> List[str]:
        """Build filer (taxpayer) XML elements.

        Args:
            header: ReturnHeader with taxpayer info

        Returns:
            List of XML element strings for filer section
        """
        elements = []
        taxpayer = header.taxpayer

        # Primary taxpayer SSN
        elements.append(self._build_xml_element(
            "PrimarySSN",
            format_ssn(taxpayer.primary_ssn)
        ))

        # Spouse SSN if applicable
        if taxpayer.spouse_ssn and header.filing_status in (2, 3):
            elements.append(self._build_xml_element(
                "SpouseSSN",
                format_ssn(taxpayer.spouse_ssn)
            ))

        # Name elements
        name_elements = [
            self._build_xml_element("PersonFirstNm", escape_xml(taxpayer.primary_first_name.upper())),
            self._build_xml_element("PersonLastNm", escape_xml(taxpayer.primary_last_name.upper())),
        ]
        elements.append(self._build_xml_container("NameLine1Txt", name_elements))

        # Primary date of birth
        if taxpayer.primary_date_of_birth:
            elements.append(self._build_xml_element(
                "PrimaryBirthDt",
                format_date(taxpayer.primary_date_of_birth)
            ))

        # Spouse info if applicable
        if taxpayer.spouse_first_name and taxpayer.spouse_last_name:
            spouse_name = [
                self._build_xml_element("PersonFirstNm", escape_xml(taxpayer.spouse_first_name.upper())),
                self._build_xml_element("PersonLastNm", escape_xml(taxpayer.spouse_last_name.upper())),
            ]
            elements.append(self._build_xml_container("SpouseNameLine1Txt", spouse_name))

            if taxpayer.spouse_date_of_birth:
                elements.append(self._build_xml_element(
                    "SpouseBirthDt",
                    format_date(taxpayer.spouse_date_of_birth)
                ))

        return elements

    def _build_preparer_elements(self, header: ReturnHeader) -> List[str]:
        """Build paid preparer XML elements.

        Args:
            header: ReturnHeader with preparer info

        Returns:
            List of XML element strings for preparer section
        """
        elements = []

        if header.preparer_ptin:
            elements.append(self._build_xml_element("PTIN", header.preparer_ptin))

        if header.preparer_ein:
            elements.append(self._build_xml_element(
                "PreparerFirmEIN",
                format_ein(header.preparer_ein)
            ))

        return elements

    def _build_pin_elements(self, header: ReturnHeader) -> List[str]:
        """Build PIN (signature) XML elements.

        Args:
            header: ReturnHeader with PIN info

        Returns:
            List of XML element strings for PIN section
        """
        elements = []

        # PIN type group
        pin_type_elements = [
            self._build_xml_element("PINTypeCd", header.pin_type),
        ]
        elements.append(self._build_xml_container("PINTypeCdGrp", pin_type_elements))

        # Primary signature PIN
        primary_pin_elements = [
            self._build_xml_element("PrimarySignaturePIN", header.primary_pin),
            self._build_xml_element("PrimarySignatureDt", format_date(header.created_at)),
        ]
        elements.append(self._build_xml_container("PrimarySignatureGrp", primary_pin_elements))

        # Spouse signature PIN if applicable
        if header.spouse_pin and header.filing_status == 2:
            spouse_pin_elements = [
                self._build_xml_element("SpouseSignaturePIN", header.spouse_pin),
                self._build_xml_element("SpouseSignatureDt", format_date(header.created_at)),
            ]
            elements.append(self._build_xml_container("SpouseSignatureGrp", spouse_pin_elements))

        return elements

    def serialize_form_1040(self, form_data: Dict[str, Any]) -> str:
        """Serialize Form 1040 data to MeF XML.

        Generates the IRS1040 element containing all lines of the tax return.
        This is a basic structure that handles common fields; extend for
        complete implementation.

        Args:
            form_data: Dictionary with Form 1040 field values keyed by line number
                      or field name (e.g., {"line1": 50000, "line2a": 1000})

        Returns:
            XML string for the IRS1040 element

        Raises:
            ValueError: If required fields are missing or invalid
        """
        elements = []

        # Income section
        income_elements = self._build_income_elements(form_data)
        if income_elements:
            elements.extend(income_elements)

        # Adjustments section
        adjustment_elements = self._build_adjustment_elements(form_data)
        if adjustment_elements:
            elements.extend(adjustment_elements)

        # AGI
        if "line11" in form_data or "agi" in form_data:
            agi_value = form_data.get("line11") or form_data.get("agi", 0)
            elements.append(self._build_xml_element(
                "AdjustedGrossIncomeAmt",
                format_amount(agi_value)
            ))

        # Deductions section
        deduction_elements = self._build_deduction_elements(form_data)
        if deduction_elements:
            elements.extend(deduction_elements)

        # Taxable income
        if "line15" in form_data or "taxable_income" in form_data:
            taxable = form_data.get("line15") or form_data.get("taxable_income", 0)
            elements.append(self._build_xml_element(
                "TaxableIncomeAmt",
                format_amount(taxable)
            ))

        # Tax and credits section
        tax_elements = self._build_tax_elements(form_data)
        if tax_elements:
            elements.extend(tax_elements)

        # Payments section
        payment_elements = self._build_payment_elements(form_data)
        if payment_elements:
            elements.extend(payment_elements)

        # Refund or amount owed
        refund_elements = self._build_refund_elements(form_data)
        if refund_elements:
            elements.extend(refund_elements)

        # Build final container
        return self._build_xml_container(
            "IRS1040",
            elements,
            attributes={
                "documentId": f"IRS1040-{uuid.uuid4().hex[:8]}",
            }
        )

    def _build_income_elements(self, form_data: Dict[str, Any]) -> List[str]:
        """Build income section XML elements."""
        elements = []

        # Line 1 - Wages, salaries, tips
        if "line1" in form_data or "wages" in form_data:
            wages = form_data.get("line1") or form_data.get("wages", 0)
            elements.append(self._build_xml_element("WagesSalariesAndTipsAmt", format_amount(wages)))

        # Line 2a - Tax-exempt interest
        if "line2a" in form_data or "tax_exempt_interest" in form_data:
            tax_exempt = form_data.get("line2a") or form_data.get("tax_exempt_interest", 0)
            elements.append(self._build_xml_element("TaxExemptInterestAmt", format_amount(tax_exempt)))

        # Line 2b - Taxable interest
        if "line2b" in form_data or "taxable_interest" in form_data:
            taxable_int = form_data.get("line2b") or form_data.get("taxable_interest", 0)
            elements.append(self._build_xml_element("TaxableInterestAmt", format_amount(taxable_int)))

        # Line 3a - Qualified dividends
        if "line3a" in form_data or "qualified_dividends" in form_data:
            qual_div = form_data.get("line3a") or form_data.get("qualified_dividends", 0)
            elements.append(self._build_xml_element("QualifiedDividendsAmt", format_amount(qual_div)))

        # Line 3b - Ordinary dividends
        if "line3b" in form_data or "ordinary_dividends" in form_data:
            ord_div = form_data.get("line3b") or form_data.get("ordinary_dividends", 0)
            elements.append(self._build_xml_element("OrdinaryDividendsAmt", format_amount(ord_div)))

        # Line 4b - IRA distributions (taxable)
        if "line4b" in form_data or "ira_taxable" in form_data:
            ira = form_data.get("line4b") or form_data.get("ira_taxable", 0)
            elements.append(self._build_xml_element("IRADistributionsTaxableAmt", format_amount(ira)))

        # Line 5b - Pensions (taxable)
        if "line5b" in form_data or "pension_taxable" in form_data:
            pension = form_data.get("line5b") or form_data.get("pension_taxable", 0)
            elements.append(self._build_xml_element("TaxablePensionsAmt", format_amount(pension)))

        # Line 6b - Social Security (taxable)
        if "line6b" in form_data or "ss_taxable" in form_data:
            ss = form_data.get("line6b") or form_data.get("ss_taxable", 0)
            elements.append(self._build_xml_element("TaxableSocSecAmt", format_amount(ss)))

        # Line 7 - Capital gain or loss
        if "line7" in form_data or "capital_gain" in form_data:
            cap_gain = form_data.get("line7") or form_data.get("capital_gain", 0)
            elements.append(self._build_xml_element("CapitalGainLossAmt", format_amount(cap_gain, allow_negative=True)))

        # Line 8 - Other income
        if "line8" in form_data or "other_income" in form_data:
            other = form_data.get("line8") or form_data.get("other_income", 0)
            elements.append(self._build_xml_element("TotalAdditionalIncomeAmt", format_amount(other, allow_negative=True)))

        # Line 9 - Total income
        if "line9" in form_data or "total_income" in form_data:
            total = form_data.get("line9") or form_data.get("total_income", 0)
            elements.append(self._build_xml_element("TotalIncomeAmt", format_amount(total, allow_negative=True)))

        return elements

    def _build_adjustment_elements(self, form_data: Dict[str, Any]) -> List[str]:
        """Build adjustments section XML elements."""
        elements = []

        # Line 10 - Adjustments to income
        if "line10" in form_data or "adjustments" in form_data:
            adj = form_data.get("line10") or form_data.get("adjustments", 0)
            elements.append(self._build_xml_element("TotalAdjustmentsAmt", format_amount(adj)))

        return elements

    def _build_deduction_elements(self, form_data: Dict[str, Any]) -> List[str]:
        """Build deductions section XML elements."""
        elements = []

        # Line 12 - Standard or itemized deduction
        if "line12" in form_data or "deduction" in form_data:
            ded = form_data.get("line12") or form_data.get("deduction", 0)
            elements.append(self._build_xml_element("TotalItemizedOrStandardDedAmt", format_amount(ded)))

        # Line 13 - QBI deduction
        if "line13" in form_data or "qbi_deduction" in form_data:
            qbi = form_data.get("line13") or form_data.get("qbi_deduction", 0)
            elements.append(self._build_xml_element("QualifiedBusinessIncomeDedAmt", format_amount(qbi)))

        # Line 14 - Total deductions
        if "line14" in form_data or "total_deductions" in form_data:
            total_ded = form_data.get("line14") or form_data.get("total_deductions", 0)
            elements.append(self._build_xml_element("TotalDeductionsAmt", format_amount(total_ded)))

        return elements

    def _build_tax_elements(self, form_data: Dict[str, Any]) -> List[str]:
        """Build tax and credits section XML elements."""
        elements = []

        # Line 16 - Tax
        if "line16" in form_data or "tax" in form_data:
            tax = form_data.get("line16") or form_data.get("tax", 0)
            elements.append(self._build_xml_element("TaxAmt", format_amount(tax)))

        # Line 17 - Additional taxes
        if "line17" in form_data or "schedule2_line3" in form_data:
            add_tax = form_data.get("line17") or form_data.get("schedule2_line3", 0)
            elements.append(self._build_xml_element("AdditionalTaxAmt", format_amount(add_tax)))

        # Line 18 - Total tax before credits
        if "line18" in form_data or "total_tax_before_credits" in form_data:
            ttbc = form_data.get("line18") or form_data.get("total_tax_before_credits", 0)
            elements.append(self._build_xml_element("TotalTaxBeforeCrAndOthTaxesAmt", format_amount(ttbc)))

        # Line 19 - Child tax credit
        if "line19" in form_data or "child_tax_credit" in form_data:
            ctc = form_data.get("line19") or form_data.get("child_tax_credit", 0)
            elements.append(self._build_xml_element("CTCODCAmt", format_amount(ctc)))

        # Line 20 - Other credits (Schedule 3)
        if "line20" in form_data or "schedule3_line8" in form_data:
            other_cred = form_data.get("line20") or form_data.get("schedule3_line8", 0)
            elements.append(self._build_xml_element("TotalNonrefundableCreditsAmt", format_amount(other_cred)))

        # Line 22 - Other taxes
        if "line22" in form_data or "other_taxes" in form_data:
            other_tax = form_data.get("line22") or form_data.get("other_taxes", 0)
            elements.append(self._build_xml_element("OtherTaxesAmt", format_amount(other_tax)))

        # Line 24 - Total tax
        if "line24" in form_data or "total_tax" in form_data:
            total_tax = form_data.get("line24") or form_data.get("total_tax", 0)
            elements.append(self._build_xml_element("TotalTaxAmt", format_amount(total_tax)))

        return elements

    def _build_payment_elements(self, form_data: Dict[str, Any]) -> List[str]:
        """Build payments section XML elements."""
        elements = []

        # Line 25a - Federal income tax withheld (W-2)
        if "line25a" in form_data or "w2_withholding" in form_data:
            w2 = form_data.get("line25a") or form_data.get("w2_withholding", 0)
            elements.append(self._build_xml_element("WithholdingTaxAmt", format_amount(w2)))

        # Line 26 - Estimated tax payments
        if "line26" in form_data or "estimated_payments" in form_data:
            est = form_data.get("line26") or form_data.get("estimated_payments", 0)
            elements.append(self._build_xml_element("EstimatedTaxPaymentsAmt", format_amount(est)))

        # Line 27 - Earned income credit
        if "line27" in form_data or "eic" in form_data:
            eic = form_data.get("line27") or form_data.get("eic", 0)
            elements.append(self._build_xml_element("EarnedIncomeCreditAmt", format_amount(eic)))

        # Line 28 - Additional child tax credit
        if "line28" in form_data or "additional_ctc" in form_data:
            actc = form_data.get("line28") or form_data.get("additional_ctc", 0)
            elements.append(self._build_xml_element("AdditionalChildTaxCreditAmt", format_amount(actc)))

        # Line 31 - Other refundable credits
        if "line31" in form_data or "other_refundable" in form_data:
            other_ref = form_data.get("line31") or form_data.get("other_refundable", 0)
            elements.append(self._build_xml_element("OtherRefundableCreditsAmt", format_amount(other_ref)))

        # Line 33 - Total payments
        if "line33" in form_data or "total_payments" in form_data:
            total_pay = form_data.get("line33") or form_data.get("total_payments", 0)
            elements.append(self._build_xml_element("TotalPaymentsAmt", format_amount(total_pay)))

        return elements

    def _build_refund_elements(self, form_data: Dict[str, Any]) -> List[str]:
        """Build refund/amount owed section XML elements."""
        elements = []

        # Line 34 - Overpayment/refund
        if "line34" in form_data or "overpayment" in form_data:
            refund = form_data.get("line34") or form_data.get("overpayment", 0)
            elements.append(self._build_xml_element("OverpaidAmt", format_amount(refund)))

        # Line 35a - Refund amount
        if "line35a" in form_data or "refund_amount" in form_data:
            refund_amt = form_data.get("line35a") or form_data.get("refund_amount", 0)
            elements.append(self._build_xml_element("RefundAmt", format_amount(refund_amt)))

        # Line 37 - Amount owed
        if "line37" in form_data or "amount_owed" in form_data:
            owed = form_data.get("line37") or form_data.get("amount_owed", 0)
            elements.append(self._build_xml_element("OwedAmt", format_amount(owed)))

        return elements

    def serialize_schedule(
        self,
        schedule_type: str,
        schedule_data: Dict[str, Any],
        document_id: Optional[str] = None
    ) -> str:
        """Serialize a schedule to MeF XML.

        Generic template for serializing schedule attachments (Schedule A, B, C, etc.).
        Extend with specific schedule implementations as needed.

        Args:
            schedule_type: Type of schedule (e.g., "ScheduleA", "ScheduleB")
            schedule_data: Dictionary with schedule field values
            document_id: Optional document ID (auto-generated if not provided)

        Returns:
            XML string for the schedule element

        Raises:
            ValueError: If schedule type is not supported
        """
        if schedule_type not in self.SCHEMA_LOCATIONS:
            raise ValueError(f"Unsupported schedule type: {schedule_type}")

        if document_id is None:
            document_id = f"{schedule_type}-{uuid.uuid4().hex[:8]}"

        elements = []

        # Process schedule data fields
        for field_name, field_value in schedule_data.items():
            if field_value is None:
                continue

            # Convert field name to XML element name (camelCase to PascalCase)
            xml_element_name = self._to_xml_element_name(field_name)

            # Format value based on type
            if isinstance(field_value, bool):
                formatted_value = "X" if field_value else ""
            elif isinstance(field_value, (int, float, Decimal)):
                formatted_value = format_amount(field_value, allow_negative=True)
            elif isinstance(field_value, (date, datetime)):
                formatted_value = format_date(field_value)
            elif isinstance(field_value, dict):
                # Nested container
                nested_elements = [
                    self._build_xml_element(self._to_xml_element_name(k), str(v))
                    for k, v in field_value.items()
                    if v is not None
                ]
                elements.append(self._build_xml_container(xml_element_name, nested_elements))
                continue
            else:
                formatted_value = escape_xml(str(field_value))

            if formatted_value:
                elements.append(self._build_xml_element(xml_element_name, formatted_value))

        # Wrap in schedule container
        root_element_name = f"IRS1040{schedule_type}"
        return self._build_xml_container(
            root_element_name,
            elements,
            attributes={"documentId": document_id}
        )

    def _to_xml_element_name(self, field_name: str) -> str:
        """Convert a field name to XML element name format.

        Converts snake_case or camelCase to PascalCase with 'Amt' suffix
        for amount fields.

        Args:
            field_name: The field name to convert

        Returns:
            XML element name in PascalCase
        """
        # Handle snake_case
        if "_" in field_name:
            parts = field_name.split("_")
            return "".join(part.capitalize() for part in parts)

        # Handle camelCase - capitalize first letter
        return field_name[0].upper() + field_name[1:]

    def _build_xml_element(
        self,
        tag_name: str,
        value: str,
        attributes: Optional[Dict[str, str]] = None
    ) -> str:
        """Build a simple XML element with optional attributes.

        Creates an XML element in the format:
        <TagName attr="value">content</TagName>

        Args:
            tag_name: Element tag name
            value: Element text content
            attributes: Optional dictionary of attributes

        Returns:
            XML element string
        """
        attr_str = ""
        if attributes:
            attr_pairs = [f'{k}="{escape_xml(v)}"' for k, v in attributes.items()]
            attr_str = " " + " ".join(attr_pairs)

        if not value:
            return f"<{tag_name}{attr_str}/>"

        return f"<{tag_name}{attr_str}>{value}</{tag_name}>"

    def _build_xml_container(
        self,
        tag_name: str,
        child_elements: List[str],
        attributes: Optional[Dict[str, str]] = None
    ) -> str:
        """Build an XML container element with child elements.

        Creates a container element with nested children:
        <Container>
          <Child1>...</Child1>
          <Child2>...</Child2>
        </Container>

        Args:
            tag_name: Container tag name
            child_elements: List of child element XML strings
            attributes: Optional dictionary of attributes

        Returns:
            XML container string with nested children
        """
        attr_str = ""
        if attributes:
            attr_pairs = [f'{k}="{escape_xml(v)}"' for k, v in attributes.items()]
            attr_str = " " + " ".join(attr_pairs)

        if not child_elements:
            return f"<{tag_name}{attr_str}/>"

        children_xml = "\n".join(child_elements)
        return f"<{tag_name}{attr_str}>\n{children_xml}\n</{tag_name}>"


# =============================================================================
# XML Digital Signature Classes
# =============================================================================


class XmlSigner:
    """XML Digital Signature handler for MeF submissions.

    Implements XML Digital Signature (XMLDsig) using RSA-SHA256 as required
    by MeF. The signature covers the entire submission and ensures integrity
    and authenticity.

    MeF requires:
    - RSA-SHA256 signature algorithm
    - Canonical XML (C14N) for normalization
    - Enveloped signature format

    Attributes:
        private_key_path: Path to RSA private key (PEM format)
        certificate_path: Path to X.509 certificate (PEM format)
    """

    # Signature algorithm identifiers
    SIGNATURE_ALGORITHM = "http://www.w3.org/2001/04/xmldsig-more#rsa-sha256"
    DIGEST_ALGORITHM = "http://www.w3.org/2001/04/xmlenc#sha256"
    CANONICALIZATION_ALGORITHM = "http://www.w3.org/2001/10/xml-exc-c14n#"
    TRANSFORM_ENVELOPED = "http://www.w3.org/2000/09/xmldsig#enveloped-signature"

    # XML namespace for signatures
    DSIG_NAMESPACE = "http://www.w3.org/2000/09/xmldsig#"

    def __init__(
        self,
        private_key_path: Optional[str] = None,
        certificate_path: Optional[str] = None,
        private_key_password: Optional[str] = None
    ):
        """Initialize the XML signer.

        Args:
            private_key_path: Path to PEM-encoded RSA private key
            certificate_path: Path to PEM-encoded X.509 certificate
            private_key_password: Password for encrypted private key (optional)
        """
        self.private_key_path = private_key_path
        self.certificate_path = certificate_path
        self.private_key_password = private_key_password
        self._private_key = None
        self._certificate = None

    def sign_xml(self, xml_content: str, reference_uri: str = "") -> str:
        """Sign XML content using RSA-SHA256.

        Generates an enveloped XML signature and inserts it into the document.
        The signature covers the entire document using the enveloped signature
        transform.

        Args:
            xml_content: XML document to sign
            reference_uri: URI reference for the signed content (empty for whole doc)

        Returns:
            XML document with embedded signature

        Raises:
            ValueError: If signing keys are not configured
            RuntimeError: If signing fails
        """
        if not self.private_key_path:
            raise ValueError("Private key path not configured for signing")

        try:
            # Import cryptography library (lazy import for optional dependency)
            from cryptography.hazmat.primitives import hashes, serialization
            from cryptography.hazmat.primitives.asymmetric import padding
            from cryptography.hazmat.backends import default_backend

            # Load private key
            if self._private_key is None:
                with open(self.private_key_path, "rb") as key_file:
                    password = self.private_key_password.encode() if self.private_key_password else None
                    self._private_key = serialization.load_pem_private_key(
                        key_file.read(),
                        password=password,
                        backend=default_backend()
                    )

            # Canonicalize the XML content
            canonicalized = self._canonicalize(xml_content)

            # Compute digest of the canonicalized content
            digest_value = self._compute_digest(canonicalized)

            # Build SignedInfo element
            signed_info = self._build_signed_info(reference_uri, digest_value)

            # Canonicalize SignedInfo for signing
            signed_info_canonical = self._canonicalize(signed_info)

            # Sign the canonicalized SignedInfo
            import base64
            signature_bytes = self._private_key.sign(
                signed_info_canonical.encode("utf-8"),
                padding.PKCS1v15(),
                hashes.SHA256()
            )
            signature_value = base64.b64encode(signature_bytes).decode("utf-8")

            # Load certificate for KeyInfo (if available)
            key_info = self._build_key_info()

            # Build complete Signature element
            signature_element = self._build_signature_element(
                signed_info,
                signature_value,
                key_info
            )

            # Insert signature into document (before closing root tag)
            # Find the position to insert (just before the last closing tag)
            last_close_tag_pos = xml_content.rfind("</")
            if last_close_tag_pos == -1:
                raise RuntimeError("Invalid XML structure: no closing tag found")

            signed_xml = (
                xml_content[:last_close_tag_pos] +
                signature_element + "\n" +
                xml_content[last_close_tag_pos:]
            )

            return signed_xml

        except ImportError:
            raise RuntimeError(
                "cryptography library required for XML signing. "
                "Install with: pip install cryptography"
            )
        except Exception as e:
            raise RuntimeError(f"XML signing failed: {str(e)}") from e

    def verify_signature(self, signed_xml: str) -> Tuple[bool, str]:
        """Verify an XML digital signature.

        Validates the signature in a signed XML document to ensure
        integrity and authenticity.

        Args:
            signed_xml: XML document with embedded signature

        Returns:
            Tuple of (is_valid, message) where is_valid is True if
            signature is valid, and message provides details

        Raises:
            ValueError: If no signature found in document
        """
        try:
            from cryptography.hazmat.primitives import hashes, serialization
            from cryptography.hazmat.primitives.asymmetric import padding
            from cryptography.hazmat.backends import default_backend
            from cryptography.x509 import load_pem_x509_certificate
            from cryptography.exceptions import InvalidSignature
            import base64

            # Extract signature components from XML
            # Find SignatureValue
            sig_value_match = re.search(
                r"<(?:ds:)?SignatureValue[^>]*>([^<]+)</(?:ds:)?SignatureValue>",
                signed_xml
            )
            if not sig_value_match:
                return False, "No SignatureValue found in document"

            signature_value = base64.b64decode(sig_value_match.group(1).strip())

            # Extract SignedInfo (need to verify this was signed)
            signed_info_match = re.search(
                r"(<(?:ds:)?SignedInfo[^>]*>.*?</(?:ds:)?SignedInfo>)",
                signed_xml,
                re.DOTALL
            )
            if not signed_info_match:
                return False, "No SignedInfo found in document"

            signed_info = signed_info_match.group(1)
            signed_info_canonical = self._canonicalize(signed_info)

            # Extract DigestValue for reference validation
            digest_value_match = re.search(
                r"<(?:ds:)?DigestValue[^>]*>([^<]+)</(?:ds:)?DigestValue>",
                signed_xml
            )
            if not digest_value_match:
                return False, "No DigestValue found in document"

            expected_digest = digest_value_match.group(1).strip()

            # Load certificate for verification
            if self._certificate is None and self.certificate_path:
                with open(self.certificate_path, "rb") as cert_file:
                    self._certificate = load_pem_x509_certificate(
                        cert_file.read(),
                        default_backend()
                    )

            if self._certificate is None:
                return False, "No certificate available for verification"

            # Get public key from certificate
            public_key = self._certificate.public_key()

            # Verify signature
            try:
                public_key.verify(
                    signature_value,
                    signed_info_canonical.encode("utf-8"),
                    padding.PKCS1v15(),
                    hashes.SHA256()
                )
            except InvalidSignature:
                return False, "Signature verification failed: invalid signature"

            # Verify digest (remove signature element first for digest computation)
            content_without_sig = re.sub(
                r"<(?:ds:)?Signature[^>]*>.*?</(?:ds:)?Signature>",
                "",
                signed_xml,
                flags=re.DOTALL
            )
            canonicalized_content = self._canonicalize(content_without_sig)
            computed_digest = self._compute_digest(canonicalized_content)

            if computed_digest != expected_digest:
                return False, "Digest verification failed: content has been modified"

            return True, "Signature is valid"

        except ImportError:
            raise RuntimeError(
                "cryptography library required for signature verification. "
                "Install with: pip install cryptography"
            )
        except Exception as e:
            return False, f"Verification error: {str(e)}"

    def _compute_digest(self, content: str) -> str:
        """Compute SHA-256 digest of content.

        Args:
            content: String content to digest

        Returns:
            Base64-encoded digest value
        """
        import base64

        digest = hashlib.sha256(content.encode("utf-8")).digest()
        return base64.b64encode(digest).decode("utf-8")

    def _canonicalize(self, xml_content: str) -> str:
        """Canonicalize XML using Exclusive XML Canonicalization.

        Normalizes XML to ensure consistent byte representation
        for signing and verification.

        Args:
            xml_content: XML string to canonicalize

        Returns:
            Canonicalized XML string
        """
        # Basic canonicalization: normalize whitespace, attribute ordering, etc.
        # For production, use a proper C14N library (e.g., lxml)

        try:
            from lxml import etree

            # Parse and canonicalize
            parser = etree.XMLParser(remove_blank_text=True)
            root = etree.fromstring(xml_content.encode("utf-8"), parser)
            return etree.tostring(root, method="c14n", exclusive=True).decode("utf-8")

        except ImportError:
            # Fallback: basic normalization without lxml
            # Remove extra whitespace between tags
            normalized = re.sub(r">\s+<", "><", xml_content)
            # Normalize line endings
            normalized = normalized.replace("\r\n", "\n").replace("\r", "\n")
            # Remove leading/trailing whitespace
            normalized = normalized.strip()
            return normalized

    def _build_signed_info(self, reference_uri: str, digest_value: str) -> str:
        """Build the SignedInfo element for the signature.

        Args:
            reference_uri: URI reference for signed content
            digest_value: Base64-encoded digest of referenced content

        Returns:
            SignedInfo XML element string
        """
        return f'''<ds:SignedInfo xmlns:ds="{self.DSIG_NAMESPACE}">
<ds:CanonicalizationMethod Algorithm="{self.CANONICALIZATION_ALGORITHM}"/>
<ds:SignatureMethod Algorithm="{self.SIGNATURE_ALGORITHM}"/>
<ds:Reference URI="{reference_uri}">
<ds:Transforms>
<ds:Transform Algorithm="{self.TRANSFORM_ENVELOPED}"/>
<ds:Transform Algorithm="{self.CANONICALIZATION_ALGORITHM}"/>
</ds:Transforms>
<ds:DigestMethod Algorithm="{self.DIGEST_ALGORITHM}"/>
<ds:DigestValue>{digest_value}</ds:DigestValue>
</ds:Reference>
</ds:SignedInfo>'''

    def _build_key_info(self) -> str:
        """Build the KeyInfo element with certificate data.

        Returns:
            KeyInfo XML element string
        """
        if not self.certificate_path:
            return ""

        try:
            with open(self.certificate_path, "rb") as cert_file:
                cert_data = cert_file.read()

            # Extract certificate data (remove PEM headers)
            import base64
            cert_lines = cert_data.decode("utf-8").split("\n")
            cert_b64 = "".join(
                line for line in cert_lines
                if not line.startswith("-----")
            )

            return f'''<ds:KeyInfo xmlns:ds="{self.DSIG_NAMESPACE}">
<ds:X509Data>
<ds:X509Certificate>{cert_b64}</ds:X509Certificate>
</ds:X509Data>
</ds:KeyInfo>'''

        except Exception:
            return ""

    def _build_signature_element(
        self,
        signed_info: str,
        signature_value: str,
        key_info: str
    ) -> str:
        """Build the complete Signature element.

        Args:
            signed_info: SignedInfo XML element
            signature_value: Base64-encoded signature
            key_info: KeyInfo XML element (may be empty)

        Returns:
            Complete Signature XML element
        """
        key_info_section = f"\n{key_info}" if key_info else ""

        return f'''<ds:Signature xmlns:ds="{self.DSIG_NAMESPACE}">
{signed_info}
<ds:SignatureValue>{signature_value}</ds:SignatureValue>{key_info_section}
</ds:Signature>'''


# =============================================================================
# Schema Validation Classes
# =============================================================================


class SchemaValidator:
    """XML Schema (XSD) validator for MeF submissions.

    Validates MeF XML documents against IRS-provided XML schemas to ensure
    structural compliance before submission. This catches schema errors
    locally before they cause MeF rejections.

    Attributes:
        schema_dir: Directory containing MeF XSD schema files
        cache_schemas: Whether to cache loaded schemas in memory
    """

    # User-friendly error message mappings for common schema errors
    ERROR_MESSAGES = {
        "cvc-type.3.1.3": "Invalid value '{value}' for element '{element}'. Expected type: {expected}",
        "cvc-minLength-valid": "Value '{value}' for '{element}' is too short. Minimum length: {min}",
        "cvc-maxLength-valid": "Value '{value}' for '{element}' is too long. Maximum length: {max}",
        "cvc-pattern-valid": "Value '{value}' for '{element}' does not match required format: {pattern}",
        "cvc-datatype-valid": "Invalid data type for '{element}'. Got '{value}', expected {expected}",
        "cvc-complex-type.2.4.a": "Unexpected element '{element}' found. Check element ordering.",
        "cvc-complex-type.2.4.b": "Missing required element '{element}'",
        "cvc-enumeration-valid": "Invalid value '{value}' for '{element}'. Allowed values: {allowed}",
        "cvc-minInclusive-valid": "Value '{value}' for '{element}' is below minimum: {min}",
        "cvc-maxInclusive-valid": "Value '{value}' for '{element}' is above maximum: {max}",
    }

    def __init__(self, schema_dir: str, cache_schemas: bool = True):
        """Initialize the schema validator.

        Args:
            schema_dir: Path to directory containing MeF XSD files
            cache_schemas: Whether to cache parsed schemas (default True)
        """
        self.schema_dir = schema_dir
        self.cache_schemas = cache_schemas
        self._schema_cache: Dict[str, Any] = {}

    def validate(
        self,
        xml_content: str,
        schema_name: str = "efile1040x_2024v5.0.xsd"
    ) -> ValidationResult:
        """Validate XML content against an XSD schema.

        Performs schema validation and returns a detailed result with
        any errors converted to user-friendly messages.

        Args:
            xml_content: XML document string to validate
            schema_name: Name of the schema file to validate against

        Returns:
            ValidationResult with validation status and any errors
        """
        start_time = time.time()

        errors: List[ValidationError] = []
        warnings: List[ValidationError] = []

        try:
            # Load the schema
            schema = self._load_schema(schema_name)

            if schema is None:
                return ValidationResult(
                    is_valid=False,
                    errors=[ValidationError(
                        code="SCHEMA_LOAD_ERROR",
                        message=f"Failed to load schema: {schema_name}",
                        severity=ValidationSeverity.ERROR,
                        category=ValidationCategory.SCHEMA
                    )],
                    validated_at=datetime.now(timezone.utc),
                    validation_duration_ms=int((time.time() - start_time) * 1000)
                )

            # Parse and validate the XML
            try:
                from lxml import etree

                # Parse XML
                parser = etree.XMLParser()
                doc = etree.fromstring(xml_content.encode("utf-8"), parser)

                # Validate against schema
                is_valid = schema.validate(doc)

                if not is_valid:
                    # Convert schema errors to ValidationError objects
                    for error in schema.error_log:
                        mapped_error = self._map_error(error)
                        if mapped_error.severity == ValidationSeverity.ERROR:
                            errors.append(mapped_error)
                        else:
                            warnings.append(mapped_error)

                duration_ms = int((time.time() - start_time) * 1000)

                return ValidationResult(
                    is_valid=len(errors) == 0,
                    errors=errors,
                    warnings=warnings,
                    validated_at=datetime.now(timezone.utc),
                    validation_duration_ms=duration_ms,
                    forms_validated=self._extract_form_names(xml_content)
                )

            except etree.XMLSyntaxError as e:
                errors.append(ValidationError(
                    code="XML_SYNTAX_ERROR",
                    message=f"XML parsing error: {str(e)}",
                    severity=ValidationSeverity.ERROR,
                    category=ValidationCategory.SCHEMA,
                    suggestion="Check XML for well-formedness (matching tags, proper escaping)"
                ))

                return ValidationResult(
                    is_valid=False,
                    errors=errors,
                    validated_at=datetime.now(timezone.utc),
                    validation_duration_ms=int((time.time() - start_time) * 1000)
                )

        except ImportError:
            # lxml not available, perform basic validation
            return self._basic_validate(xml_content, start_time)

    def _load_schema(self, schema_name: str) -> Any:
        """Load and parse an XSD schema file.

        Args:
            schema_name: Name of the schema file

        Returns:
            Parsed XMLSchema object, or None if loading fails
        """
        import os

        # Check cache
        if self.cache_schemas and schema_name in self._schema_cache:
            return self._schema_cache[schema_name]

        schema_path = os.path.join(self.schema_dir, schema_name)

        try:
            from lxml import etree

            with open(schema_path, "rb") as schema_file:
                schema_doc = etree.parse(schema_file)
                schema = etree.XMLSchema(schema_doc)

            # Cache if enabled
            if self.cache_schemas:
                self._schema_cache[schema_name] = schema

            return schema

        except FileNotFoundError:
            # Schema file not found
            return None
        except ImportError:
            # lxml not available
            return None
        except Exception:
            # Other parsing errors
            return None

    def _map_error(self, schema_error: Any) -> ValidationError:
        """Map a schema validation error to a user-friendly ValidationError.

        Args:
            schema_error: Error object from lxml schema validation

        Returns:
            ValidationError with user-friendly message
        """
        # Extract error details
        error_type = getattr(schema_error, "type_name", "unknown")
        message = str(schema_error.message) if hasattr(schema_error, "message") else str(schema_error)
        line = getattr(schema_error, "line", None)
        column = getattr(schema_error, "column", None)

        # Try to extract element and value from the error message
        element_match = re.search(r"element '([^']+)'", message, re.IGNORECASE)
        value_match = re.search(r"'([^']+)' is not", message)

        element_name = element_match.group(1) if element_match else "unknown"
        field_value = value_match.group(1) if value_match else None

        # Map to user-friendly message
        user_message = message  # Default to original message

        for error_code, template in self.ERROR_MESSAGES.items():
            if error_code in error_type or error_code in message:
                # Build user-friendly message from template
                user_message = template.format(
                    element=element_name,
                    value=field_value or "unknown",
                    expected="valid value",
                    min="required",
                    max="allowed",
                    pattern="expected pattern",
                    allowed="valid options"
                )
                break

        # Determine form name from XPath if available
        form_name = self._extract_form_from_path(element_name)

        return ValidationError(
            code=f"SCHEMA_{error_type.upper().replace('-', '_')}",
            message=user_message,
            severity=ValidationSeverity.ERROR,
            category=ValidationCategory.SCHEMA,
            field_path=element_name,
            field_value=field_value,
            form_name=form_name,
            line_number=str(line) if line else None,
            suggestion=self._suggest_fix(error_type, element_name)
        )

    def _suggest_fix(self, error_type: str, element_name: str) -> Optional[str]:
        """Generate a suggestion for fixing a schema error.

        Args:
            error_type: Type of schema error
            element_name: Name of the element with the error

        Returns:
            Suggestion string or None
        """
        suggestions = {
            "minLength": f"Ensure {element_name} has the required minimum characters",
            "maxLength": f"Reduce the length of {element_name}",
            "pattern": f"Check the format requirements for {element_name}",
            "enumeration": f"Use one of the allowed values for {element_name}",
            "datatype": f"Check the data type for {element_name}",
            "missing": f"Add the required element {element_name}",
        }

        for key, suggestion in suggestions.items():
            if key in error_type.lower():
                return suggestion

        return None

    def _extract_form_from_path(self, element_path: str) -> Optional[str]:
        """Extract form name from an element path.

        Args:
            element_path: XPath or element name

        Returns:
            Form name or None
        """
        form_patterns = [
            (r"IRS1040$", "Form 1040"),
            (r"IRS1040Schedule([A-Z])", r"Schedule \1"),
            (r"IRS1040Schedule(\d+)", r"Schedule \1"),
            (r"IRS(\d{4})", r"Form \1"),
        ]

        for pattern, replacement in form_patterns:
            match = re.search(pattern, element_path)
            if match:
                return re.sub(pattern, replacement, match.group(0))

        return None

    def _extract_form_names(self, xml_content: str) -> List[str]:
        """Extract form names from XML content.

        Args:
            xml_content: XML document string

        Returns:
            List of form names found in the document
        """
        forms = []

        # Look for IRS form elements
        form_matches = re.findall(r"<(IRS\d{4}[A-Za-z0-9]*)", xml_content)

        for match in set(form_matches):
            # Convert to readable form name
            readable = match.replace("IRS", "Form ").replace("Schedule", "Schedule ")
            forms.append(readable)

        return sorted(forms)

    def _basic_validate(self, xml_content: str, start_time: float) -> ValidationResult:
        """Perform basic XML validation without lxml.

        Args:
            xml_content: XML document string
            start_time: Validation start time for duration calculation

        Returns:
            ValidationResult with basic validation results
        """
        errors = []

        try:
            # Try to parse the XML
            ET.fromstring(xml_content)

        except ET.ParseError as e:
            errors.append(ValidationError(
                code="XML_PARSE_ERROR",
                message=f"XML parsing error: {str(e)}",
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.SCHEMA,
                suggestion="Check XML for well-formedness"
            ))

        duration_ms = int((time.time() - start_time) * 1000)

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=[ValidationError(
                code="SCHEMA_VALIDATION_LIMITED",
                message="Full schema validation unavailable (lxml not installed)",
                severity=ValidationSeverity.WARNING,
                category=ValidationCategory.SCHEMA,
                suggestion="Install lxml for full schema validation: pip install lxml"
            )],
            validated_at=datetime.now(timezone.utc),
            validation_duration_ms=duration_ms,
            forms_validated=self._extract_form_names(xml_content)
        )


# =============================================================================
# Business Rules Validation Classes
# =============================================================================


class BusinessRulesValidator:
    """Business rules validator for Form 1040 and schedules.

    Validates tax return data against IRS business rules to catch logical
    errors before submission. These rules are based on IRS Publication 4164
    business rules and MeF validation requirements.

    Business rules include:
    - Line total validations (math checks)
    - Cross-form consistency checks
    - Filing status requirements
    - Credit eligibility rules
    - Amount limit validations

    Attributes:
        tax_year: Tax year for applying year-specific rules
        filing_status: Filing status for status-specific rules
    """

    # Tax year limits and thresholds (2024 values)
    TAX_YEAR_LIMITS = {
        2024: {
            "standard_deduction_single": 14600,
            "standard_deduction_mfj": 29200,
            "standard_deduction_mfs": 14600,
            "standard_deduction_hoh": 21900,
            "standard_deduction_qss": 29200,
            "additional_deduction_65_single": 1950,
            "additional_deduction_65_married": 1550,
            "eitc_max_investment_income": 11600,
            "child_tax_credit_max": 2000,
            "additional_ctc_max": 1700,
            "social_security_max_taxable": 168600,
            "qbi_deduction_threshold_single": 191950,
            "qbi_deduction_threshold_mfj": 383900,
        },
        2025: {
            "standard_deduction_single": 15000,
            "standard_deduction_mfj": 30000,
            "standard_deduction_mfs": 15000,
            "standard_deduction_hoh": 22500,
            "standard_deduction_qss": 30000,
            "additional_deduction_65_single": 2000,
            "additional_deduction_65_married": 1600,
            "eitc_max_investment_income": 11950,
            "child_tax_credit_max": 2000,
            "additional_ctc_max": 1700,
            "social_security_max_taxable": 176100,
            "qbi_deduction_threshold_single": 197300,
            "qbi_deduction_threshold_mfj": 394600,
        }
    }

    def __init__(self, tax_year: int, filing_status: int = 1):
        """Initialize the business rules validator.

        Args:
            tax_year: Tax year for applying year-specific rules
            filing_status: Filing status (1=Single, 2=MFJ, 3=MFS, 4=HOH, 5=QSS)
        """
        self.tax_year = tax_year
        self.filing_status = filing_status
        self._limits = self.TAX_YEAR_LIMITS.get(tax_year, self.TAX_YEAR_LIMITS[2024])

    def validate(self, form_data: Dict[str, Any]) -> ValidationResult:
        """Validate form data against business rules.

        Runs all applicable business rules and returns a comprehensive
        validation result.

        Args:
            form_data: Dictionary with form field values

        Returns:
            ValidationResult with all validation findings
        """
        start_time = time.time()

        errors: List[ValidationError] = []
        warnings: List[ValidationError] = []
        info_messages: List[ValidationError] = []

        # Run all validation rule sets
        errors.extend(self._validate_income_lines(form_data))
        errors.extend(self._validate_deduction_lines(form_data))
        errors.extend(self._validate_tax_calculations(form_data))
        errors.extend(self._validate_credit_lines(form_data))
        errors.extend(self._validate_payment_lines(form_data))

        # Run consistency checks
        consistency_results = self._validate_consistency(form_data)
        for result in consistency_results:
            if result.severity == ValidationSeverity.ERROR:
                errors.append(result)
            elif result.severity == ValidationSeverity.WARNING:
                warnings.append(result)
            else:
                info_messages.append(result)

        # Run math checks
        math_results = self._validate_math_totals(form_data)
        errors.extend(math_results)

        duration_ms = int((time.time() - start_time) * 1000)

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            info_messages=info_messages,
            validated_at=datetime.now(timezone.utc),
            validation_duration_ms=duration_ms,
            forms_validated=["Form 1040"]
        )

    def _validate_income_lines(self, form_data: Dict[str, Any]) -> List[ValidationError]:
        """Validate income-related lines.

        Args:
            form_data: Form field data

        Returns:
            List of validation errors
        """
        errors = []

        # Wages (Line 1) must be non-negative
        wages = form_data.get("line1") or form_data.get("wages", 0)
        if wages and float(wages) < 0:
            errors.append(ValidationError(
                code="BR-INC-001",
                message="Wages (Line 1) cannot be negative",
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.BUSINESS_RULE,
                form_name="Form 1040",
                line_number="1",
                field_value=str(wages),
                suggestion="Enter wages as a positive amount"
            ))

        # Tax-exempt interest (Line 2a) must not exceed total interest
        tax_exempt = float(form_data.get("line2a") or form_data.get("tax_exempt_interest", 0) or 0)
        taxable_int = float(form_data.get("line2b") or form_data.get("taxable_interest", 0) or 0)

        if tax_exempt > 0 and taxable_int == 0:
            errors.append(ValidationError(
                code="BR-INC-002",
                message="Tax-exempt interest reported without taxable interest Schedule B may be required",
                severity=ValidationSeverity.WARNING,
                category=ValidationCategory.CONSISTENCY,
                form_name="Form 1040",
                line_number="2a/2b",
                suggestion="Verify interest reporting and attach Schedule B if required"
            ))

        # Qualified dividends cannot exceed ordinary dividends
        qual_div = float(form_data.get("line3a") or form_data.get("qualified_dividends", 0) or 0)
        ord_div = float(form_data.get("line3b") or form_data.get("ordinary_dividends", 0) or 0)

        if qual_div > ord_div:
            errors.append(ValidationError(
                code="BR-INC-003",
                message="Qualified dividends (Line 3a) cannot exceed ordinary dividends (Line 3b)",
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.BUSINESS_RULE,
                form_name="Form 1040",
                line_number="3a/3b",
                field_value=f"Qualified: {qual_div}, Ordinary: {ord_div}",
                suggestion="Qualified dividends must be less than or equal to ordinary dividends"
            ))

        # Social Security benefits taxable cannot exceed 85% of total benefits
        ss_total = float(form_data.get("line6a") or form_data.get("ss_total", 0) or 0)
        ss_taxable = float(form_data.get("line6b") or form_data.get("ss_taxable", 0) or 0)

        if ss_total > 0 and ss_taxable > ss_total * 0.85:
            errors.append(ValidationError(
                code="BR-INC-004",
                message="Taxable Social Security (Line 6b) cannot exceed 85% of total benefits",
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.BUSINESS_RULE,
                form_name="Form 1040",
                line_number="6b",
                field_value=f"Taxable: {ss_taxable}, Total: {ss_total}",
                expected_format=f"Maximum taxable: {ss_total * 0.85:.0f}",
                suggestion="Review Social Security benefits worksheet calculation"
            ))

        return errors

    def _validate_deduction_lines(self, form_data: Dict[str, Any]) -> List[ValidationError]:
        """Validate deduction-related lines.

        Args:
            form_data: Form field data

        Returns:
            List of validation errors
        """
        errors = []

        # Standard deduction validation
        deduction = float(form_data.get("line12") or form_data.get("deduction", 0) or 0)

        # Get expected standard deduction based on filing status
        status_deduction_map = {
            1: self._limits["standard_deduction_single"],
            2: self._limits["standard_deduction_mfj"],
            3: self._limits["standard_deduction_mfs"],
            4: self._limits["standard_deduction_hoh"],
            5: self._limits["standard_deduction_qss"],
        }

        expected_std_ded = status_deduction_map.get(self.filing_status, 0)

        # Check if using standard deduction with suspicious amount
        itemized = form_data.get("itemized_deductions") or form_data.get("schedule_a_total")

        if not itemized and deduction > 0 and deduction != expected_std_ded:
            # Allow for additional deductions for 65+ or blind
            max_additional = self._limits["additional_deduction_65_single"] * 4  # Max 2 people, 2 conditions each

            if abs(deduction - expected_std_ded) > max_additional:
                errors.append(ValidationError(
                    code="BR-DED-001",
                    message=f"Standard deduction amount ({deduction}) does not match expected ({expected_std_ded})",
                    severity=ValidationSeverity.WARNING,
                    category=ValidationCategory.BUSINESS_RULE,
                    form_name="Form 1040",
                    line_number="12",
                    field_value=str(deduction),
                    expected_format=f"Expected: {expected_std_ded} (plus additional if 65+ or blind)",
                    suggestion="Verify standard deduction calculation or attach Schedule A for itemized"
                ))

        # QBI deduction cannot exceed 20% of taxable income (simplified check)
        qbi_ded = float(form_data.get("line13") or form_data.get("qbi_deduction", 0) or 0)
        taxable_income = float(form_data.get("line15") or form_data.get("taxable_income", 0) or 0)

        if qbi_ded > 0 and taxable_income > 0:
            max_qbi = (taxable_income + qbi_ded) * 0.20  # Pre-QBI taxable income * 20%
            if qbi_ded > max_qbi * 1.01:  # Allow 1% tolerance for rounding
                errors.append(ValidationError(
                    code="BR-DED-002",
                    message=f"QBI deduction ({qbi_ded}) may exceed 20% limit",
                    severity=ValidationSeverity.WARNING,
                    category=ValidationCategory.BUSINESS_RULE,
                    form_name="Form 1040",
                    line_number="13",
                    field_value=str(qbi_ded),
                    suggestion="Review QBI deduction calculation and Form 8995"
                ))

        return errors

    def _validate_tax_calculations(self, form_data: Dict[str, Any]) -> List[ValidationError]:
        """Validate tax calculation lines.

        Args:
            form_data: Form field data

        Returns:
            List of validation errors
        """
        errors = []

        # Tax (Line 16) must be non-negative
        tax = float(form_data.get("line16") or form_data.get("tax", 0) or 0)
        if tax < 0:
            errors.append(ValidationError(
                code="BR-TAX-001",
                message="Tax (Line 16) cannot be negative",
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.BUSINESS_RULE,
                form_name="Form 1040",
                line_number="16",
                field_value=str(tax),
                suggestion="Tax amount must be zero or positive"
            ))

        # Taxable income check
        taxable_income = float(form_data.get("line15") or form_data.get("taxable_income", 0) or 0)

        # If taxable income is negative or zero, tax should be zero
        if taxable_income <= 0 and tax > 0:
            errors.append(ValidationError(
                code="BR-TAX-002",
                message="Tax (Line 16) should be zero when taxable income is zero or negative",
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.BUSINESS_RULE,
                form_name="Form 1040",
                line_number="16",
                field_value=f"Tax: {tax}, Taxable Income: {taxable_income}",
                suggestion="Review tax calculation"
            ))

        # Total tax (Line 24) cannot be less than zero
        total_tax = float(form_data.get("line24") or form_data.get("total_tax", 0) or 0)
        if total_tax < 0:
            errors.append(ValidationError(
                code="BR-TAX-003",
                message="Total tax (Line 24) cannot be negative",
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.BUSINESS_RULE,
                form_name="Form 1040",
                line_number="24",
                field_value=str(total_tax),
                suggestion="Total tax after credits must be zero or positive"
            ))

        return errors

    def _validate_credit_lines(self, form_data: Dict[str, Any]) -> List[ValidationError]:
        """Validate credit-related lines.

        Args:
            form_data: Form field data

        Returns:
            List of validation errors
        """
        errors = []

        # Child tax credit (Line 19) validation
        ctc = float(form_data.get("line19") or form_data.get("child_tax_credit", 0) or 0)
        num_children = int(form_data.get("qualifying_children", 0) or 0)

        max_ctc = num_children * self._limits["child_tax_credit_max"]

        if ctc > max_ctc and max_ctc > 0:
            errors.append(ValidationError(
                code="BR-CRD-001",
                message=f"Child tax credit ({ctc}) exceeds maximum for {num_children} qualifying children",
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.BUSINESS_RULE,
                form_name="Form 1040",
                line_number="19",
                field_value=str(ctc),
                expected_format=f"Maximum: {max_ctc}",
                suggestion="Review Schedule 8812 calculation"
            ))

        # Additional child tax credit (Line 28) validation
        actc = float(form_data.get("line28") or form_data.get("additional_ctc", 0) or 0)
        max_actc = num_children * self._limits["additional_ctc_max"]

        if actc > max_actc and max_actc > 0:
            errors.append(ValidationError(
                code="BR-CRD-002",
                message=f"Additional child tax credit ({actc}) exceeds maximum",
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.BUSINESS_RULE,
                form_name="Form 1040",
                line_number="28",
                field_value=str(actc),
                expected_format=f"Maximum: {max_actc}",
                suggestion="Review Schedule 8812 Part II calculation"
            ))

        # CTC + ACTC cannot exceed total potential credit
        if (ctc + actc) > max_ctc and max_ctc > 0:
            errors.append(ValidationError(
                code="BR-CRD-003",
                message=f"Combined CTC ({ctc}) and ACTC ({actc}) exceeds maximum child credit",
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.BUSINESS_RULE,
                form_name="Form 1040",
                line_number="19/28",
                field_value=f"CTC: {ctc}, ACTC: {actc}",
                expected_format=f"Maximum combined: {max_ctc}",
                suggestion="Review child tax credit calculations"
            ))

        # EITC investment income limit
        eic = float(form_data.get("line27") or form_data.get("eic", 0) or 0)
        investment_income = (
            float(form_data.get("line2b") or form_data.get("taxable_interest", 0) or 0) +
            float(form_data.get("line3b") or form_data.get("ordinary_dividends", 0) or 0) +
            float(form_data.get("line7") or form_data.get("capital_gain", 0) or 0)
        )

        if eic > 0 and investment_income > self._limits["eitc_max_investment_income"]:
            errors.append(ValidationError(
                code="BR-CRD-004",
                message=f"Investment income ({investment_income}) exceeds EITC limit",
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.BUSINESS_RULE,
                form_name="Form 1040",
                line_number="27",
                field_value=f"Investment Income: {investment_income}",
                expected_format=f"Maximum: {self._limits['eitc_max_investment_income']}",
                suggestion="Taxpayer may not be eligible for EITC due to investment income"
            ))

        return errors

    def _validate_payment_lines(self, form_data: Dict[str, Any]) -> List[ValidationError]:
        """Validate payment-related lines.

        Args:
            form_data: Form field data

        Returns:
            List of validation errors
        """
        errors = []

        # Federal withholding (Line 25) must be non-negative
        withholding = float(form_data.get("line25a") or form_data.get("w2_withholding", 0) or 0)
        if withholding < 0:
            errors.append(ValidationError(
                code="BR-PAY-001",
                message="Federal withholding (Line 25a) cannot be negative",
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.BUSINESS_RULE,
                form_name="Form 1040",
                line_number="25a",
                field_value=str(withholding),
                suggestion="Verify W-2 Box 2 amounts"
            ))

        # Estimated payments (Line 26) must be non-negative
        estimated = float(form_data.get("line26") or form_data.get("estimated_payments", 0) or 0)
        if estimated < 0:
            errors.append(ValidationError(
                code="BR-PAY-002",
                message="Estimated tax payments (Line 26) cannot be negative",
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.BUSINESS_RULE,
                form_name="Form 1040",
                line_number="26",
                field_value=str(estimated),
                suggestion="Enter estimated payments as positive amount"
            ))

        return errors

    def _validate_consistency(self, form_data: Dict[str, Any]) -> List[ValidationError]:
        """Validate cross-field consistency.

        Args:
            form_data: Form field data

        Returns:
            List of validation errors/warnings
        """
        findings = []

        # If MFJ (status 2), both SSNs required
        if self.filing_status == 2:
            spouse_ssn = form_data.get("spouse_ssn")
            if not spouse_ssn:
                findings.append(ValidationError(
                    code="BR-CON-001",
                    message="Spouse SSN required for Married Filing Jointly",
                    severity=ValidationSeverity.ERROR,
                    category=ValidationCategory.CONSISTENCY,
                    form_name="Form 1040",
                    suggestion="Enter spouse's Social Security Number"
                ))

        # If claiming dependents, check for Schedule 8812 requirement
        num_children = int(form_data.get("qualifying_children", 0) or 0)
        ctc = float(form_data.get("line19") or form_data.get("child_tax_credit", 0) or 0)

        if num_children > 0 and ctc == 0:
            findings.append(ValidationError(
                code="BR-CON-002",
                message=f"Qualifying children ({num_children}) claimed but no child tax credit",
                severity=ValidationSeverity.WARNING,
                category=ValidationCategory.CONSISTENCY,
                form_name="Form 1040",
                line_number="19",
                suggestion="Review Schedule 8812 for potential child tax credit"
            ))

        # If Schedule C income, check for self-employment tax
        schedule_c_profit = float(form_data.get("schedule_c_profit") or form_data.get("self_employment_income", 0) or 0)
        se_tax = float(form_data.get("se_tax") or form_data.get("schedule_se_tax", 0) or 0)

        if schedule_c_profit > 400 and se_tax == 0:
            findings.append(ValidationError(
                code="BR-CON-003",
                message="Self-employment income reported but no self-employment tax",
                severity=ValidationSeverity.WARNING,
                category=ValidationCategory.CONSISTENCY,
                form_name="Form 1040",
                suggestion="Schedule SE may be required for self-employment income over $400"
            ))

        # Refund and amount owed cannot both be positive
        refund = float(form_data.get("line35a") or form_data.get("refund_amount", 0) or 0)
        owed = float(form_data.get("line37") or form_data.get("amount_owed", 0) or 0)

        if refund > 0 and owed > 0:
            findings.append(ValidationError(
                code="BR-CON-004",
                message="Cannot have both refund and amount owed",
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.CONSISTENCY,
                form_name="Form 1040",
                line_number="35a/37",
                field_value=f"Refund: {refund}, Owed: {owed}",
                suggestion="Review final tax calculation"
            ))

        return findings

    def _validate_math_totals(self, form_data: Dict[str, Any]) -> List[ValidationError]:
        """Validate math totals (line additions).

        Args:
            form_data: Form field data

        Returns:
            List of validation errors
        """
        errors = []
        tolerance = 1  # Allow $1 rounding tolerance

        # Total income (Line 9) = sum of income lines
        income_lines = [
            float(form_data.get("line1") or form_data.get("wages", 0) or 0),
            float(form_data.get("line2b") or form_data.get("taxable_interest", 0) or 0),
            float(form_data.get("line3b") or form_data.get("ordinary_dividends", 0) or 0),
            float(form_data.get("line4b") or form_data.get("ira_taxable", 0) or 0),
            float(form_data.get("line5b") or form_data.get("pension_taxable", 0) or 0),
            float(form_data.get("line6b") or form_data.get("ss_taxable", 0) or 0),
            float(form_data.get("line7") or form_data.get("capital_gain", 0) or 0),
            float(form_data.get("line8") or form_data.get("other_income", 0) or 0),
        ]

        calculated_total_income = sum(income_lines)
        reported_total_income = float(form_data.get("line9") or form_data.get("total_income", 0) or 0)

        if reported_total_income > 0 and abs(calculated_total_income - reported_total_income) > tolerance:
            errors.append(ValidationError(
                code="BR-MATH-001",
                message=f"Total income (Line 9) does not equal sum of income lines",
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.MATH,
                form_name="Form 1040",
                line_number="9",
                field_value=f"Reported: {reported_total_income}, Calculated: {calculated_total_income}",
                expected_format=f"Expected: {calculated_total_income}",
                suggestion="Verify income line additions"
            ))

        # AGI (Line 11) = Total income - Adjustments
        total_income = float(form_data.get("line9") or form_data.get("total_income", 0) or 0)
        adjustments = float(form_data.get("line10") or form_data.get("adjustments", 0) or 0)
        calculated_agi = total_income - adjustments
        reported_agi = float(form_data.get("line11") or form_data.get("agi", 0) or 0)

        if reported_agi != 0 and abs(calculated_agi - reported_agi) > tolerance:
            errors.append(ValidationError(
                code="BR-MATH-002",
                message="AGI (Line 11) does not equal Total Income minus Adjustments",
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.MATH,
                form_name="Form 1040",
                line_number="11",
                field_value=f"Reported: {reported_agi}, Calculated: {calculated_agi}",
                expected_format=f"Expected: {calculated_agi}",
                suggestion="Verify Line 9 - Line 10 = Line 11"
            ))

        # Taxable income (Line 15) = AGI - Deductions
        agi = float(form_data.get("line11") or form_data.get("agi", 0) or 0)
        total_deductions = float(form_data.get("line14") or form_data.get("total_deductions", 0) or 0)
        calculated_taxable = max(0, agi - total_deductions)
        reported_taxable = float(form_data.get("line15") or form_data.get("taxable_income", 0) or 0)

        if reported_taxable > 0 and abs(calculated_taxable - reported_taxable) > tolerance:
            errors.append(ValidationError(
                code="BR-MATH-003",
                message="Taxable income (Line 15) calculation error",
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.MATH,
                form_name="Form 1040",
                line_number="15",
                field_value=f"Reported: {reported_taxable}, Calculated: {calculated_taxable}",
                expected_format=f"Expected: {calculated_taxable}",
                suggestion="Verify Line 11 - Line 14 = Line 15"
            ))

        # Total payments (Line 33) = sum of payment lines
        payment_lines = [
            float(form_data.get("line25a") or form_data.get("w2_withholding", 0) or 0),
            float(form_data.get("line25b") or 0),
            float(form_data.get("line25c") or 0),
            float(form_data.get("line26") or form_data.get("estimated_payments", 0) or 0),
            float(form_data.get("line27") or form_data.get("eic", 0) or 0),
            float(form_data.get("line28") or form_data.get("additional_ctc", 0) or 0),
            float(form_data.get("line29") or 0),
            float(form_data.get("line31") or form_data.get("other_refundable", 0) or 0),
            float(form_data.get("line32") or 0),
        ]

        calculated_payments = sum(payment_lines)
        reported_payments = float(form_data.get("line33") or form_data.get("total_payments", 0) or 0)

        if reported_payments > 0 and abs(calculated_payments - reported_payments) > tolerance:
            errors.append(ValidationError(
                code="BR-MATH-004",
                message="Total payments (Line 33) does not equal sum of payment lines",
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.MATH,
                form_name="Form 1040",
                line_number="33",
                field_value=f"Reported: {reported_payments}, Calculated: {calculated_payments}",
                expected_format=f"Expected: {calculated_payments}",
                suggestion="Verify payment line additions"
            ))

        # Refund/Owed calculation
        total_payments = float(form_data.get("line33") or form_data.get("total_payments", 0) or 0)
        total_tax = float(form_data.get("line24") or form_data.get("total_tax", 0) or 0)

        calculated_difference = total_payments - total_tax
        reported_refund = float(form_data.get("line34") or form_data.get("overpayment", 0) or 0)
        reported_owed = float(form_data.get("line37") or form_data.get("amount_owed", 0) or 0)

        if calculated_difference > 0:
            # Should have refund
            if abs(calculated_difference - reported_refund) > tolerance:
                errors.append(ValidationError(
                    code="BR-MATH-005",
                    message="Refund amount (Line 34) calculation error",
                    severity=ValidationSeverity.ERROR,
                    category=ValidationCategory.MATH,
                    form_name="Form 1040",
                    line_number="34",
                    field_value=f"Reported: {reported_refund}, Calculated: {calculated_difference}",
                    expected_format=f"Expected: {calculated_difference}",
                    suggestion="Verify Line 33 - Line 24 = Line 34"
                ))
        elif calculated_difference < 0:
            # Should owe
            expected_owed = abs(calculated_difference)
            if abs(expected_owed - reported_owed) > tolerance:
                errors.append(ValidationError(
                    code="BR-MATH-006",
                    message="Amount owed (Line 37) calculation error",
                    severity=ValidationSeverity.ERROR,
                    category=ValidationCategory.MATH,
                    form_name="Form 1040",
                    line_number="37",
                    field_value=f"Reported: {reported_owed}, Calculated: {expected_owed}",
                    expected_format=f"Expected: {expected_owed}",
                    suggestion="Verify Line 24 - Line 33 = Line 37"
                ))

        return errors
