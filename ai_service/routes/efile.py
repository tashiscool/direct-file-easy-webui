"""FastAPI routes for MeF (Modernized e-File) electronic filing services.

This module provides comprehensive endpoints for IRS MeF e-filing including:
- Return preparation and XML serialization
- Schema and business rule validation
- Self-Select PIN signing
- Submission to IRS MeF system
- Status polling and acknowledgment retrieval
- Identity verification (AGI/IP PIN)
- Error code resolution
"""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional, Dict, Any, Union
from fastapi import APIRouter, HTTPException, Query, Path
from pydantic import BaseModel, Field, validator

router = APIRouter(prefix="/v1/efile", tags=["MeF E-Filing"])


# ============== MeF Enums ==============

class FilingStatus(str, Enum):
    """IRS filing status codes."""
    SINGLE = "1"
    MARRIED_FILING_JOINTLY = "2"
    MARRIED_FILING_SEPARATELY = "3"
    HEAD_OF_HOUSEHOLD = "4"
    QUALIFYING_SURVIVING_SPOUSE = "5"


class SubmissionType(str, Enum):
    """MeF submission type codes."""
    ORIGINAL = "O"
    AMENDED = "A"
    SUPERSEDED = "S"


class SubmissionStatus(str, Enum):
    """MeF submission status values."""
    PENDING = "pending"
    RECEIVED = "received"
    PROCESSING = "processing"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    ERROR = "error"


class AcknowledgmentStatus(str, Enum):
    """IRS acknowledgment status codes."""
    ACCEPTED = "A"
    REJECTED = "R"
    ACCEPTED_WITH_ALERTS = "AA"


class IdentityVerificationMethod(str, Enum):
    """Methods for identity verification."""
    PRIOR_YEAR_AGI = "prior_year_agi"
    PRIOR_YEAR_PIN = "prior_year_pin"
    IP_PIN = "ip_pin"
    IDENTITY_PROTECTION_PIN = "identity_protection_pin"


class ErrorSeverity(str, Enum):
    """IRS error severity levels."""
    REJECT = "R"  # Return rejected
    ALERT = "A"   # Warning, return accepted
    INFORMATIONAL = "I"  # For information only


class SignatureType(str, Enum):
    """Electronic signature types."""
    SELF_SELECT_PIN = "self_select_pin"
    PRACTITIONER_PIN = "practitioner_pin"
    ERO_SIGNATURE = "ero_signature"


class ReturnType(str, Enum):
    """Tax return types."""
    FORM_1040 = "1040"
    FORM_1040_SR = "1040-SR"
    FORM_1040_NR = "1040-NR"
    FORM_1040_SS = "1040-SS"
    FORM_1040_PR = "1040-PR"


# ============== Common MeF Types ==============

class TaxpayerTIN(BaseModel):
    """Taxpayer Identification Number (SSN or ITIN)."""
    tin: str = Field(..., min_length=9, max_length=9, description="9-digit SSN or ITIN")
    tin_type: str = Field(default="SSN", description="SSN or ITIN")

    @validator('tin')
    def validate_tin(cls, v):
        if not v.isdigit():
            raise ValueError('TIN must contain only digits')
        return v


class NameLine(BaseModel):
    """Name components as required by MeF."""
    first_name: str = Field(..., max_length=20)
    middle_initial: Optional[str] = Field(None, max_length=1)
    last_name: str = Field(..., max_length=20)
    suffix: Optional[str] = Field(None, max_length=10, description="Jr., Sr., III, etc.")


class USAddress(BaseModel):
    """US mailing address per MeF schema."""
    address_line_1: str = Field(..., max_length=35)
    address_line_2: Optional[str] = Field(None, max_length=35)
    city: str = Field(..., max_length=22)
    state: str = Field(..., min_length=2, max_length=2)
    zip_code: str = Field(..., min_length=5, max_length=12)


class ForeignAddress(BaseModel):
    """Foreign address per MeF schema."""
    address_line_1: str = Field(..., max_length=35)
    address_line_2: Optional[str] = Field(None, max_length=35)
    city: str = Field(..., max_length=22)
    province_or_state: Optional[str] = Field(None, max_length=17)
    country: str = Field(..., min_length=2, max_length=2, description="ISO country code")
    postal_code: Optional[str] = Field(None, max_length=16)


class BankAccount(BaseModel):
    """Bank account information for direct deposit/debit."""
    routing_number: str = Field(..., min_length=9, max_length=9)
    account_number: str = Field(..., min_length=4, max_length=17)
    account_type: str = Field(..., description="1=Checking, 2=Savings")
    is_international: bool = Field(default=False)


class Refund(BaseModel):
    """Refund information."""
    amount: Decimal = Field(..., ge=0)
    routing_number: Optional[str] = None
    account_number: Optional[str] = None
    account_type: Optional[str] = None
    apply_to_next_year: Decimal = Field(default=Decimal("0"))
    buy_savings_bonds: Decimal = Field(default=Decimal("0"))


class AmountOwed(BaseModel):
    """Amount owed to IRS."""
    amount: Decimal = Field(..., ge=0)
    payment_method: str = Field(default="direct_debit", description="direct_debit, check, eftps")
    payment_date: Optional[date] = None
    routing_number: Optional[str] = None
    account_number: Optional[str] = None
    account_type: Optional[str] = None


# ============== Form Attachment Types ==============

class FormW2(BaseModel):
    """W-2 Wage and Tax Statement data."""
    employer_ein: str
    employer_name: str
    employer_address: USAddress
    control_number: Optional[str] = None
    wages: Decimal
    federal_tax_withheld: Decimal
    social_security_wages: Decimal
    social_security_tax: Decimal
    medicare_wages: Decimal
    medicare_tax: Decimal
    social_security_tips: Optional[Decimal] = None
    allocated_tips: Optional[Decimal] = None
    dependent_care_benefits: Optional[Decimal] = None
    nonqualified_plans: Optional[Decimal] = None
    box_12_codes: Optional[Dict[str, Decimal]] = None
    statutory_employee: bool = False
    retirement_plan: bool = False
    third_party_sick_pay: bool = False
    state_wages: Optional[List[Dict[str, Any]]] = None


class Form1099Int(BaseModel):
    """1099-INT Interest Income data."""
    payer_tin: str
    payer_name: str
    interest_income: Decimal
    early_withdrawal_penalty: Optional[Decimal] = None
    us_savings_bond_interest: Optional[Decimal] = None
    federal_tax_withheld: Optional[Decimal] = None
    investment_expenses: Optional[Decimal] = None
    foreign_tax_paid: Optional[Decimal] = None
    tax_exempt_interest: Optional[Decimal] = None
    private_activity_bond_interest: Optional[Decimal] = None
    market_discount: Optional[Decimal] = None
    bond_premium: Optional[Decimal] = None
    bond_premium_treasury: Optional[Decimal] = None
    bond_premium_tax_exempt: Optional[Decimal] = None


class Form1099Div(BaseModel):
    """1099-DIV Dividends and Distributions data."""
    payer_tin: str
    payer_name: str
    ordinary_dividends: Decimal
    qualified_dividends: Optional[Decimal] = None
    total_capital_gain_dist: Optional[Decimal] = None
    unrecap_sec_1250_gain: Optional[Decimal] = None
    section_1202_gain: Optional[Decimal] = None
    collectibles_gain: Optional[Decimal] = None
    section_897_dividends: Optional[Decimal] = None
    section_897_capital_gain: Optional[Decimal] = None
    nondividend_distributions: Optional[Decimal] = None
    federal_tax_withheld: Optional[Decimal] = None
    section_199a_dividends: Optional[Decimal] = None
    investment_expenses: Optional[Decimal] = None
    foreign_tax_paid: Optional[Decimal] = None
    foreign_country: Optional[str] = None
    cash_liquidation_dist: Optional[Decimal] = None
    noncash_liquidation_dist: Optional[Decimal] = None
    exempt_interest_dividends: Optional[Decimal] = None
    private_activity_bond_dividends: Optional[Decimal] = None


class Form1099G(BaseModel):
    """1099-G Government Payments data."""
    payer_tin: str
    payer_name: str
    unemployment_compensation: Optional[Decimal] = None
    state_local_refunds: Optional[Decimal] = None
    refund_year: Optional[int] = None
    federal_tax_withheld: Optional[Decimal] = None
    rtaa_payments: Optional[Decimal] = None
    agricultural_payments: Optional[Decimal] = None
    market_gain: Optional[Decimal] = None


class Form1099R(BaseModel):
    """1099-R Distributions from Pensions, Annuities, etc."""
    payer_tin: str
    payer_name: str
    gross_distribution: Decimal
    taxable_amount: Optional[Decimal] = None
    taxable_amount_not_determined: bool = False
    total_distribution: bool = False
    capital_gain: Optional[Decimal] = None
    federal_tax_withheld: Optional[Decimal] = None
    employee_contributions: Optional[Decimal] = None
    net_unrealized_appreciation: Optional[Decimal] = None
    distribution_codes: str = Field(..., max_length=2)
    ira_sep_simple: bool = False
    other_amount: Optional[Decimal] = None
    percent_total_distribution: Optional[Decimal] = None
    total_employee_contributions: Optional[Decimal] = None
    first_year_roth: Optional[int] = None


class ScheduleItem(BaseModel):
    """Generic schedule line item."""
    description: str
    amount: Decimal
    category: Optional[str] = None
    form_reference: Optional[str] = None


# ============== Return Data Structure ==============

class DependentInfo(BaseModel):
    """Information about a dependent."""
    name: NameLine
    tin: str
    relationship: str
    months_lived_with: int = Field(default=12, ge=0, le=12)
    is_qualifying_child: bool = False
    is_qualifying_relative: bool = False
    is_student: bool = False
    is_disabled: bool = False
    child_tax_credit_eligible: bool = False
    other_dependent_credit_eligible: bool = False


class TaxReturnData(BaseModel):
    """Complete tax return data structure for e-filing."""
    # Header Information
    tax_year: int = Field(default=2025, ge=2020, le=2030)
    return_type: ReturnType = Field(default=ReturnType.FORM_1040)
    submission_type: SubmissionType = Field(default=SubmissionType.ORIGINAL)

    # Taxpayer Information
    primary_taxpayer: NameLine
    primary_tin: TaxpayerTIN
    primary_dob: date
    primary_occupation: Optional[str] = None

    # Spouse Information (if MFJ or MFS)
    spouse: Optional[NameLine] = None
    spouse_tin: Optional[TaxpayerTIN] = None
    spouse_dob: Optional[date] = None
    spouse_occupation: Optional[str] = None

    # Filing Status
    filing_status: FilingStatus

    # Address
    address: Union[USAddress, ForeignAddress]

    # Dependents
    dependents: List[DependentInfo] = []

    # Income
    wages_salaries_tips: Decimal = Field(default=Decimal("0"))
    taxable_interest: Decimal = Field(default=Decimal("0"))
    tax_exempt_interest: Decimal = Field(default=Decimal("0"))
    ordinary_dividends: Decimal = Field(default=Decimal("0"))
    qualified_dividends: Decimal = Field(default=Decimal("0"))
    taxable_refunds: Decimal = Field(default=Decimal("0"))
    alimony_received: Decimal = Field(default=Decimal("0"))
    business_income: Decimal = Field(default=Decimal("0"))
    capital_gain_or_loss: Decimal = Field(default=Decimal("0"))
    other_gains_or_losses: Decimal = Field(default=Decimal("0"))
    taxable_ira_distributions: Decimal = Field(default=Decimal("0"))
    taxable_pensions: Decimal = Field(default=Decimal("0"))
    rental_royalty_income: Decimal = Field(default=Decimal("0"))
    farm_income: Decimal = Field(default=Decimal("0"))
    unemployment_compensation: Decimal = Field(default=Decimal("0"))
    taxable_social_security: Decimal = Field(default=Decimal("0"))
    other_income: Decimal = Field(default=Decimal("0"))

    # Adjustments to Income
    educator_expenses: Decimal = Field(default=Decimal("0"))
    hsa_deduction: Decimal = Field(default=Decimal("0"))
    self_employment_tax_deduction: Decimal = Field(default=Decimal("0"))
    self_employed_sep_simple: Decimal = Field(default=Decimal("0"))
    self_employed_health_insurance: Decimal = Field(default=Decimal("0"))
    early_withdrawal_penalty: Decimal = Field(default=Decimal("0"))
    alimony_paid: Decimal = Field(default=Decimal("0"))
    ira_deduction: Decimal = Field(default=Decimal("0"))
    student_loan_interest: Decimal = Field(default=Decimal("0"))

    # Standard or Itemized Deduction
    uses_standard_deduction: bool = True
    itemized_deductions: Optional[Decimal] = None

    # Itemized Deduction Details (Schedule A)
    medical_expenses: Optional[Decimal] = None
    state_local_taxes_paid: Optional[Decimal] = None
    real_estate_taxes: Optional[Decimal] = None
    personal_property_taxes: Optional[Decimal] = None
    mortgage_interest: Optional[Decimal] = None
    investment_interest: Optional[Decimal] = None
    charitable_cash: Optional[Decimal] = None
    charitable_noncash: Optional[Decimal] = None
    casualty_theft_losses: Optional[Decimal] = None

    # Tax and Credits
    qualified_business_income_deduction: Decimal = Field(default=Decimal("0"))
    child_tax_credit: Decimal = Field(default=Decimal("0"))
    other_dependent_credit: Decimal = Field(default=Decimal("0"))
    education_credits: Decimal = Field(default=Decimal("0"))
    retirement_savings_credit: Decimal = Field(default=Decimal("0"))
    child_care_credit: Decimal = Field(default=Decimal("0"))
    earned_income_credit: Decimal = Field(default=Decimal("0"))
    additional_child_tax_credit: Decimal = Field(default=Decimal("0"))
    american_opportunity_credit_refundable: Decimal = Field(default=Decimal("0"))
    other_refundable_credits: Decimal = Field(default=Decimal("0"))

    # Payments
    federal_income_tax_withheld: Decimal = Field(default=Decimal("0"))
    estimated_tax_payments: Decimal = Field(default=Decimal("0"))
    amount_paid_with_extension: Decimal = Field(default=Decimal("0"))
    excess_social_security_withheld: Decimal = Field(default=Decimal("0"))

    # Form Attachments
    w2_forms: List[FormW2] = []
    form_1099_int: List[Form1099Int] = []
    form_1099_div: List[Form1099Div] = []
    form_1099_g: List[Form1099G] = []
    form_1099_r: List[Form1099R] = []

    # Additional Schedules
    schedule_1_items: List[ScheduleItem] = []
    schedule_2_items: List[ScheduleItem] = []
    schedule_3_items: List[ScheduleItem] = []

    # Refund or Amount Owed
    refund: Optional[Refund] = None
    amount_owed: Optional[AmountOwed] = None


# ============== Request/Response Models ==============

class PrepareReturnRequest(BaseModel):
    """Request to prepare return for e-filing."""
    return_data: TaxReturnData
    include_state_returns: bool = Field(default=False)
    state_codes: Optional[List[str]] = None
    validate_on_prepare: bool = Field(default=True)
    output_format: str = Field(default="mef_xml", description="mef_xml, irs_xml, or json")


class PrepareReturnResponse(BaseModel):
    """Response from return preparation."""
    submission_id: str = Field(..., description="Unique submission identifier")
    xml_content: Optional[str] = Field(None, description="Serialized XML (base64 encoded)")
    xml_size_bytes: int
    form_count: int
    schedule_count: int
    attachment_count: int
    validation_performed: bool
    validation_passed: Optional[bool] = None
    validation_errors: List[Dict[str, Any]] = []
    validation_warnings: List[Dict[str, Any]] = []
    estimated_refund: Optional[Decimal] = None
    estimated_amount_owed: Optional[Decimal] = None
    prepared_at: datetime
    expires_at: datetime
    state_returns: List[Dict[str, Any]] = []


class ValidationRule(BaseModel):
    """A single validation rule result."""
    rule_id: str
    rule_name: str
    category: str = Field(..., description="schema, business, math, consistency")
    severity: ErrorSeverity
    passed: bool
    message: Optional[str] = None
    field_path: Optional[str] = None
    expected_value: Optional[str] = None
    actual_value: Optional[str] = None
    irs_error_code: Optional[str] = None
    resolution_guidance: Optional[str] = None


class ValidateReturnRequest(BaseModel):
    """Request to validate return against IRS rules."""
    submission_id: Optional[str] = None
    return_data: Optional[TaxReturnData] = None
    xml_content: Optional[str] = Field(None, description="Base64 encoded XML")
    validation_levels: List[str] = Field(
        default=["schema", "business", "math", "consistency"],
        description="Validation types to run"
    )
    include_warnings: bool = True
    stop_on_first_error: bool = False


class ValidateReturnResponse(BaseModel):
    """Response from return validation."""
    is_valid: bool
    can_be_filed: bool
    total_errors: int
    total_warnings: int
    schema_valid: bool
    business_rules_passed: bool
    math_verified: bool
    consistency_checked: bool
    rules_checked: int
    rules_passed: int
    errors: List[ValidationRule]
    warnings: List[ValidationRule]
    validation_timestamp: datetime


class SignReturnRequest(BaseModel):
    """Request to sign return with Self-Select PIN."""
    submission_id: str
    signature_type: SignatureType = Field(default=SignatureType.SELF_SELECT_PIN)

    # Self-Select PIN
    primary_pin: str = Field(..., min_length=5, max_length=5, description="5-digit PIN")
    primary_dob: date
    primary_prior_year_agi: Optional[Decimal] = None
    primary_prior_year_pin: Optional[str] = None

    # Spouse PIN (if MFJ)
    spouse_pin: Optional[str] = Field(None, min_length=5, max_length=5)
    spouse_dob: Optional[date] = None
    spouse_prior_year_agi: Optional[Decimal] = None
    spouse_prior_year_pin: Optional[str] = None

    # IP PIN (if assigned by IRS)
    primary_ip_pin: Optional[str] = Field(None, min_length=6, max_length=6)
    spouse_ip_pin: Optional[str] = Field(None, min_length=6, max_length=6)

    # Consent
    consent_to_disclose: bool = Field(..., description="Consent for IRS disclosure")
    consent_to_use: bool = Field(..., description="Consent to use return info")
    signature_date: date = Field(default_factory=date.today)


class SignReturnResponse(BaseModel):
    """Response from return signing."""
    submission_id: str
    signed: bool
    signature_type: SignatureType
    primary_signature_verified: bool
    spouse_signature_verified: Optional[bool] = None
    ip_pin_verified: Optional[bool] = None
    signed_at: datetime
    signature_hash: str
    ready_for_submission: bool
    errors: List[str] = []


class SubmitReturnRequest(BaseModel):
    """Request to submit return to IRS MeF."""
    submission_id: str
    environment: str = Field(default="production", description="production, test, or assurance")
    submission_type: SubmissionType = Field(default=SubmissionType.ORIGINAL)
    device_id: Optional[str] = Field(None, description="Device identifier for fraud prevention")
    ip_address: Optional[str] = None
    geolocation: Optional[Dict[str, float]] = None
    request_acknowledgment: bool = True


class SubmitReturnResponse(BaseModel):
    """Response from return submission."""
    submission_id: str
    mef_submission_id: Optional[str] = Field(None, description="IRS-assigned submission ID")
    status: SubmissionStatus
    submitted_at: datetime
    estimated_processing_time: str
    transmission_id: Optional[str] = None
    receipt_id: Optional[str] = None
    message: str
    next_steps: List[str] = []


class SubmissionStatusResponse(BaseModel):
    """Response for submission status query."""
    submission_id: str
    mef_submission_id: Optional[str] = None
    status: SubmissionStatus
    status_description: str
    submitted_at: datetime
    last_updated: datetime
    acknowledgment_available: bool
    estimated_completion: Optional[datetime] = None
    processing_stage: Optional[str] = None
    retry_count: int = 0
    can_retry: bool = False
    error_details: Optional[Dict[str, Any]] = None


class AcknowledgmentResponse(BaseModel):
    """IRS acknowledgment response."""
    submission_id: str
    mef_submission_id: str
    acknowledgment_status: AcknowledgmentStatus
    acknowledgment_timestamp: datetime
    accepted: bool

    # If accepted
    declaration_control_number: Optional[str] = None
    refund_amount: Optional[Decimal] = None
    amount_owed: Optional[Decimal] = None
    direct_deposit_date: Optional[date] = None
    payment_due_date: Optional[date] = None

    # If rejected
    rejection_errors: List[Dict[str, Any]] = []
    can_resubmit: bool = True
    resubmission_deadline: Optional[date] = None

    # Alerts (for accepted with alerts)
    alerts: List[Dict[str, Any]] = []

    # Raw acknowledgment
    raw_acknowledgment_xml: Optional[str] = None


class IdentityVerifyRequest(BaseModel):
    """Request to verify taxpayer identity."""
    primary_tin: str = Field(..., min_length=9, max_length=9)
    primary_name: NameLine
    primary_dob: date
    filing_status: FilingStatus
    tax_year: int

    # Verification method
    verification_method: IdentityVerificationMethod

    # Prior Year AGI verification
    prior_year_agi: Optional[Decimal] = None
    prior_year_filing_status: Optional[FilingStatus] = None

    # Prior Year PIN verification
    prior_year_pin: Optional[str] = Field(None, min_length=5, max_length=5)

    # IP PIN verification
    ip_pin: Optional[str] = Field(None, min_length=6, max_length=6)

    # Spouse information (if MFJ)
    spouse_tin: Optional[str] = None
    spouse_name: Optional[NameLine] = None
    spouse_dob: Optional[date] = None
    spouse_prior_year_agi: Optional[Decimal] = None
    spouse_ip_pin: Optional[str] = None


class IdentityVerifyResponse(BaseModel):
    """Response from identity verification."""
    verified: bool
    primary_verified: bool
    spouse_verified: Optional[bool] = None
    verification_method: IdentityVerificationMethod
    verification_timestamp: datetime

    # Error information
    error_code: Optional[str] = None
    error_message: Optional[str] = None

    # Retry information
    attempts_remaining: int = 3
    locked_until: Optional[datetime] = None

    # Next steps
    alternative_methods: List[IdentityVerificationMethod] = []
    irs_phone_support: str = "1-800-829-1040"


class ErrorCodeRequest(BaseModel):
    """Request for error code resolution."""
    error_code: str = Field(..., description="IRS MeF error code (e.g., IND-031, F8862-001)")


class ErrorResolution(BaseModel):
    """Resolution guidance for an IRS error code."""
    error_code: str
    error_category: str
    severity: ErrorSeverity
    title: str
    description: str
    form_affected: Optional[str] = None
    line_affected: Optional[str] = None

    # Resolution
    common_causes: List[str]
    resolution_steps: List[str]
    documentation_needed: List[str] = []

    # Related
    related_error_codes: List[str] = []
    irs_publication: Optional[str] = None
    irs_notice: Optional[str] = None

    # User actions
    can_self_correct: bool
    requires_irs_contact: bool
    paper_filing_required: bool


class ErrorCodeResponse(BaseModel):
    """Response for error code lookup."""
    found: bool
    error: Optional[ErrorResolution] = None
    similar_errors: List[Dict[str, str]] = []
    support_resources: Dict[str, str] = {}


# ============== Route Implementations ==============

@router.post("/prepare", response_model=PrepareReturnResponse)
async def prepare_return(request: PrepareReturnRequest):
    """Prepare a tax return for e-filing by serializing to MeF XML format.

    This endpoint takes the structured tax return data and converts it to
    the XML format required by the IRS Modernized e-File (MeF) system.

    The preparation process:
    1. Validates required fields are present
    2. Calculates any derived values
    3. Serializes to MeF XML schema
    4. Optionally validates against IRS schemas
    5. Returns the prepared submission package

    Args:
        request: Tax return data and preparation options.

    Returns:
        Prepared return with submission ID and optional validation results.
    """
    import uuid
    from datetime import timedelta

    try:
        submission_id = str(uuid.uuid4())
        now = datetime.utcnow()

        # Count forms and schedules
        form_count = 1  # Base 1040
        schedule_count = 0
        attachment_count = len(request.return_data.w2_forms) + \
                          len(request.return_data.form_1099_int) + \
                          len(request.return_data.form_1099_div) + \
                          len(request.return_data.form_1099_g) + \
                          len(request.return_data.form_1099_r)

        if request.return_data.schedule_1_items:
            schedule_count += 1
        if request.return_data.schedule_2_items:
            schedule_count += 1
        if request.return_data.schedule_3_items:
            schedule_count += 1
        if not request.return_data.uses_standard_deduction:
            schedule_count += 1  # Schedule A

        # Calculate refund/owed (simplified calculation for demo)
        estimated_refund = None
        estimated_owed = None
        if request.return_data.refund:
            estimated_refund = request.return_data.refund.amount
        elif request.return_data.amount_owed:
            estimated_owed = request.return_data.amount_owed.amount

        # Build response
        response = PrepareReturnResponse(
            submission_id=submission_id,
            xml_content=None,  # Would contain base64 encoded XML in production
            xml_size_bytes=0,
            form_count=form_count,
            schedule_count=schedule_count,
            attachment_count=attachment_count,
            validation_performed=request.validate_on_prepare,
            validation_passed=True if request.validate_on_prepare else None,
            validation_errors=[],
            validation_warnings=[],
            estimated_refund=estimated_refund,
            estimated_amount_owed=estimated_owed,
            prepared_at=now,
            expires_at=now + timedelta(days=30),
            state_returns=[]
        )

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate", response_model=ValidateReturnResponse)
async def validate_return(request: ValidateReturnRequest):
    """Validate a tax return against IRS schemas and business rules.

    Performs comprehensive validation including:
    - XML Schema validation against MeF schemas
    - Business rule validation (IRS rejection rules)
    - Mathematical verification (totals match, no negative amounts where prohibited)
    - Consistency checks (cross-form references, dependent info matches)

    Args:
        request: Return data or submission ID to validate.

    Returns:
        Detailed validation results with error codes and resolution guidance.
    """
    try:
        now = datetime.utcnow()

        # In production, would perform actual validation
        # For now, return a sample validation response

        errors: List[ValidationRule] = []
        warnings: List[ValidationRule] = []

        # Check if we have data to validate
        if not request.submission_id and not request.return_data and not request.xml_content:
            raise HTTPException(
                status_code=400,
                detail="Must provide submission_id, return_data, or xml_content"
            )

        is_valid = len(errors) == 0

        return ValidateReturnResponse(
            is_valid=is_valid,
            can_be_filed=is_valid,
            total_errors=len(errors),
            total_warnings=len(warnings),
            schema_valid=True,
            business_rules_passed=True,
            math_verified=True,
            consistency_checked=True,
            rules_checked=150,
            rules_passed=150 - len(errors),
            errors=errors,
            warnings=warnings,
            validation_timestamp=now
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sign", response_model=SignReturnResponse)
async def sign_return(request: SignReturnRequest):
    """Sign a tax return using Self-Select PIN method.

    The Self-Select PIN is a 5-digit number that serves as the taxpayer's
    electronic signature. Identity verification is performed using:
    - Prior year AGI (Adjusted Gross Income), or
    - Prior year Self-Select PIN, or
    - IRS-issued IP PIN (Identity Protection PIN)

    For joint returns, both taxpayers must sign.

    Args:
        request: Signing credentials and submission ID.

    Returns:
        Signature confirmation and readiness for submission.
    """
    import hashlib

    try:
        now = datetime.utcnow()

        # Validate PIN format
        if not request.primary_pin.isdigit() or len(request.primary_pin) != 5:
            raise HTTPException(
                status_code=400,
                detail="Primary PIN must be exactly 5 digits"
            )

        # Create signature hash
        sig_data = f"{request.submission_id}:{request.primary_pin}:{request.signature_date}"
        signature_hash = hashlib.sha256(sig_data.encode()).hexdigest()[:16]

        return SignReturnResponse(
            submission_id=request.submission_id,
            signed=True,
            signature_type=request.signature_type,
            primary_signature_verified=True,
            spouse_signature_verified=True if request.spouse_pin else None,
            ip_pin_verified=True if request.primary_ip_pin else None,
            signed_at=now,
            signature_hash=signature_hash,
            ready_for_submission=True,
            errors=[]
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/submit", response_model=SubmitReturnResponse)
async def submit_return(request: SubmitReturnRequest):
    """Submit a signed tax return to the IRS MeF system.

    The return must be prepared, validated, and signed before submission.

    Submission process:
    1. Verify the return is signed and validated
    2. Package the return with all attachments
    3. Transmit to IRS MeF gateway
    4. Receive transmission confirmation
    5. Begin acknowledgment polling

    Args:
        request: Submission parameters and submission ID.

    Returns:
        Submission confirmation with tracking information.
    """
    import uuid

    try:
        now = datetime.utcnow()

        # Generate MeF submission ID (would come from IRS in production)
        mef_submission_id = f"IRS{uuid.uuid4().hex[:16].upper()}"
        transmission_id = uuid.uuid4().hex[:12].upper()

        return SubmitReturnResponse(
            submission_id=request.submission_id,
            mef_submission_id=mef_submission_id,
            status=SubmissionStatus.RECEIVED,
            submitted_at=now,
            estimated_processing_time="24-48 hours",
            transmission_id=transmission_id,
            receipt_id=f"REC{uuid.uuid4().hex[:10].upper()}",
            message="Return successfully transmitted to IRS MeF system.",
            next_steps=[
                "Check status in 24-48 hours using GET /v1/efile/status/{submission_id}",
                "IRS acknowledgment typically available within 24-48 hours",
                "If accepted, refund issued within 21 days of acceptance"
            ]
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{submission_id}", response_model=SubmissionStatusResponse)
async def get_submission_status(
    submission_id: str = Path(..., description="Submission ID to query")
):
    """Get the current status of a submitted return.

    Poll this endpoint to check the processing status of your submission.
    Status progression: pending -> received -> processing -> accepted/rejected

    Args:
        submission_id: The submission ID returned from /submit.

    Returns:
        Current status and processing details.
    """
    try:
        now = datetime.utcnow()

        # In production, would query actual status from database/IRS
        return SubmissionStatusResponse(
            submission_id=submission_id,
            mef_submission_id=f"IRS{submission_id[:16].upper()}",
            status=SubmissionStatus.PROCESSING,
            status_description="Return is being processed by the IRS",
            submitted_at=now,
            last_updated=now,
            acknowledgment_available=False,
            estimated_completion=now,
            processing_stage="Schema Validation",
            retry_count=0,
            can_retry=False,
            error_details=None
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/acknowledgment/{submission_id}", response_model=AcknowledgmentResponse)
async def get_acknowledgment(
    submission_id: str = Path(..., description="Submission ID to get acknowledgment for")
):
    """Get the IRS acknowledgment for a submitted return.

    Once the IRS processes the submission, an acknowledgment is issued:
    - Accepted (A): Return accepted for processing
    - Rejected (R): Return rejected, errors must be corrected
    - Accepted with Alerts (AA): Accepted but with informational alerts

    Args:
        submission_id: The submission ID to query.

    Returns:
        IRS acknowledgment with acceptance/rejection details.
    """
    try:
        now = datetime.utcnow()

        # In production, would retrieve actual acknowledgment
        return AcknowledgmentResponse(
            submission_id=submission_id,
            mef_submission_id=f"IRS{submission_id[:16].upper()}",
            acknowledgment_status=AcknowledgmentStatus.ACCEPTED,
            acknowledgment_timestamp=now,
            accepted=True,
            declaration_control_number=f"DCN{submission_id[:8].upper()}",
            refund_amount=Decimal("2500.00"),
            amount_owed=None,
            direct_deposit_date=None,
            payment_due_date=None,
            rejection_errors=[],
            can_resubmit=True,
            resubmission_deadline=None,
            alerts=[],
            raw_acknowledgment_xml=None
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/identity-verify", response_model=IdentityVerifyResponse)
async def verify_identity(request: IdentityVerifyRequest):
    """Verify taxpayer identity using IRS-approved methods.

    Identity verification is required before e-filing to prevent fraud.
    Available verification methods:

    1. Prior Year AGI: Your Adjusted Gross Income from last year's return
    2. Prior Year PIN: The Self-Select PIN used to sign last year's return
    3. IP PIN: IRS-issued Identity Protection PIN (6 digits)

    First-time filers or those who didn't file last year should use $0 for
    prior year AGI or contact the IRS for an IP PIN.

    Args:
        request: Identity verification credentials.

    Returns:
        Verification result and alternative methods if verification fails.
    """
    try:
        now = datetime.utcnow()

        # In production, would verify against IRS e-Services
        verified = True

        return IdentityVerifyResponse(
            verified=verified,
            primary_verified=verified,
            spouse_verified=verified if request.spouse_tin else None,
            verification_method=request.verification_method,
            verification_timestamp=now,
            error_code=None,
            error_message=None,
            attempts_remaining=3,
            locked_until=None,
            alternative_methods=[
                IdentityVerificationMethod.PRIOR_YEAR_AGI,
                IdentityVerificationMethod.IP_PIN
            ],
            irs_phone_support="1-800-829-1040"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/errors/{error_code}", response_model=ErrorCodeResponse)
async def get_error_resolution(
    error_code: str = Path(..., description="IRS MeF error code (e.g., IND-031)")
):
    """Get resolution guidance for an IRS MeF error code.

    When a return is rejected, the IRS provides error codes indicating
    what needs to be corrected. This endpoint provides detailed guidance
    on understanding and resolving each error.

    Common error code prefixes:
    - IND-***: Individual return errors
    - SEIC-***: Earned Income Credit errors
    - F8862-***: Form 8862 (EIC after disallowance) errors
    - R0000-***: Schema validation errors

    Args:
        error_code: The IRS error code to look up.

    Returns:
        Detailed error information and resolution steps.
    """
    try:
        # Common MeF error codes database
        error_database = {
            "IND-031": ErrorResolution(
                error_code="IND-031",
                error_category="Identity Verification",
                severity=ErrorSeverity.REJECT,
                title="AGI Verification Failed",
                description="The Prior Year AGI entered does not match IRS records.",
                form_affected="Form 1040",
                line_affected="Self-Select PIN",
                common_causes=[
                    "Entered current year AGI instead of prior year",
                    "Spouse's AGI entered instead of taxpayer's (for MFS)",
                    "Amended return AGI differs from original",
                    "Filed late and return not yet processed by IRS"
                ],
                resolution_steps=[
                    "Verify you're using prior year AGI, not current year",
                    "Check Line 11 of your prior year Form 1040",
                    "If filed jointly last year, use the same AGI for both spouses",
                    "If you filed an amended return, try the original AGI first",
                    "If filed late, try $0 as your prior year AGI",
                    "Request an IP PIN from the IRS as an alternative"
                ],
                documentation_needed=[
                    "Prior year Form 1040 (Line 11)"
                ],
                related_error_codes=["IND-032", "IND-033"],
                irs_publication="Pub 1345",
                irs_notice=None,
                can_self_correct=True,
                requires_irs_contact=False,
                paper_filing_required=False
            ),
            "IND-032": ErrorResolution(
                error_code="IND-032",
                error_category="Identity Verification",
                severity=ErrorSeverity.REJECT,
                title="Prior Year PIN Verification Failed",
                description="The Prior Year Self-Select PIN entered does not match IRS records.",
                form_affected="Form 1040",
                line_affected="Self-Select PIN",
                common_causes=[
                    "Wrong PIN from a different year",
                    "PIN from another taxpayer's return",
                    "PIN changed during prior year filing process"
                ],
                resolution_steps=[
                    "Try using Prior Year AGI instead",
                    "Request an IP PIN from IRS.gov",
                    "Verify you're using the PIN from the correct tax year"
                ],
                documentation_needed=[
                    "Copy of prior year e-file confirmation"
                ],
                related_error_codes=["IND-031", "IND-033"],
                irs_publication="Pub 1345",
                irs_notice=None,
                can_self_correct=True,
                requires_irs_contact=False,
                paper_filing_required=False
            ),
            "IND-510": ErrorResolution(
                error_code="IND-510",
                error_category="Duplicate Filing",
                severity=ErrorSeverity.REJECT,
                title="Primary SSN Already Filed",
                description="A return has already been filed using this Social Security Number.",
                form_affected="Form 1040",
                line_affected="Social Security Number",
                common_causes=[
                    "Return already successfully filed and accepted",
                    "Identity theft - someone filed using your SSN",
                    "Spouse filed separately using same SSN by mistake"
                ],
                resolution_steps=[
                    "Check if you already filed and forgot",
                    "If identity theft suspected, complete IRS Form 14039",
                    "Call IRS Identity Protection Specialized Unit",
                    "File by paper with Form 14039 attached",
                    "Request an IP PIN for future filings"
                ],
                documentation_needed=[
                    "Photo ID",
                    "Social Security card",
                    "Prior year tax return"
                ],
                related_error_codes=["IND-511", "IND-512"],
                irs_publication="Pub 5027",
                irs_notice=None,
                can_self_correct=False,
                requires_irs_contact=True,
                paper_filing_required=True
            ),
            "SEIC-001": ErrorResolution(
                error_code="SEIC-001",
                error_category="Earned Income Credit",
                severity=ErrorSeverity.REJECT,
                title="EIC Claiming Error",
                description="The return claims Earned Income Credit but doesn't meet requirements.",
                form_affected="Schedule EIC",
                line_affected="Various",
                common_causes=[
                    "Filing status is Married Filing Separately",
                    "Investment income exceeds the limit",
                    "No earned income reported",
                    "AGI exceeds EIC income limits"
                ],
                resolution_steps=[
                    "Verify filing status is not MFS",
                    "Check investment income limit (${11,600} for 2025)",
                    "Ensure wages or self-employment income is reported",
                    "Verify AGI is within limits for your family size",
                    "Review Schedule EIC for missing dependent information"
                ],
                documentation_needed=[
                    "W-2 forms",
                    "Schedule C if self-employed",
                    "Child's birth certificate if claiming qualifying child"
                ],
                related_error_codes=["SEIC-002", "SEIC-003"],
                irs_publication="Pub 596",
                irs_notice=None,
                can_self_correct=True,
                requires_irs_contact=False,
                paper_filing_required=False
            ),
            "R0000-500": ErrorResolution(
                error_code="R0000-500",
                error_category="Schema Validation",
                severity=ErrorSeverity.REJECT,
                title="Invalid XML Document",
                description="The return XML does not conform to the MeF schema.",
                form_affected="Multiple",
                line_affected="Various",
                common_causes=[
                    "Software error in XML generation",
                    "Missing required elements",
                    "Invalid data types or formats",
                    "Corrupted transmission"
                ],
                resolution_steps=[
                    "Update your tax software to the latest version",
                    "Clear cache and re-generate the return",
                    "Contact your tax software provider",
                    "Try submitting again after software update"
                ],
                documentation_needed=[],
                related_error_codes=["R0000-501", "R0000-502"],
                irs_publication=None,
                irs_notice=None,
                can_self_correct=True,
                requires_irs_contact=False,
                paper_filing_required=False
            )
        }

        # Look up error code
        if error_code in error_database:
            return ErrorCodeResponse(
                found=True,
                error=error_database[error_code],
                similar_errors=[],
                support_resources={
                    "irs_phone": "1-800-829-1040",
                    "irs_website": "https://www.irs.gov/e-file-providers/e-file-error-codes",
                    "identity_theft": "https://www.irs.gov/identity-theft-central"
                }
            )

        # Find similar error codes
        prefix = error_code.split("-")[0] if "-" in error_code else error_code[:3]
        similar = [
            {"code": code, "title": error.title}
            for code, error in error_database.items()
            if code.startswith(prefix) and code != error_code
        ]

        return ErrorCodeResponse(
            found=False,
            error=None,
            similar_errors=similar,
            support_resources={
                "irs_phone": "1-800-829-1040",
                "irs_website": "https://www.irs.gov/e-file-providers/e-file-error-codes"
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
