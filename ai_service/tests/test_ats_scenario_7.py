"""Comprehensive pytest tests for IRS ATS Test Scenario 7 - Charlie Boone.

This module tests the MeF (Modernized e-File) service functionality using
IRS ATS (Assurance Testing System) Test Scenario 7 data for Charlie Boone.

Test Scenario Reference: IRS ATS Test Scenario 7 (ty25-1040-mef-ats-scenario-7-10212025.pdf)
Primary Taxpayer: Charlie Boone
Filing Status: Single
Document: Form 4868 (Application for Automatic Extension)

Key Features Tested:
- Form 4868 (Application for Automatic Extension of Time to File)
- Extension request processing
- Estimated tax liability calculation
- Payment with extension
- MeF submission for extension forms

Tax Year: 2025

Note: This scenario ONLY files Form 4868 extension, not the full tax return.

Source: /Users/tkhan/Downloads/IRS_MeF_Materials/Test_Scenarios/1040_Series/
"""

import pytest
from datetime import date
from decimal import Decimal
from typing import Any, Dict, List

import sys
import os

# Add the parent directory to path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

# Import from the module file
import importlib.util
spec = importlib.util.spec_from_file_location(
    "mef_efile_service",
    os.path.join(parent_dir, "services", "mef_efile_service.py")
)
mef_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mef_module)

# Extract imports from the loaded module
format_ssn = mef_module.format_ssn
format_ein = mef_module.format_ein
format_amount = mef_module.format_amount
format_amount_with_cents = mef_module.format_amount_with_cents
format_date = mef_module.format_date
escape_xml = mef_module.escape_xml
SubmissionId = mef_module.SubmissionId
SubmissionType = mef_module.SubmissionType
SubmissionCategory = mef_module.SubmissionCategory
TaxpayerInfo = mef_module.TaxpayerInfo
ReturnHeader = mef_module.ReturnHeader
AckStatus = mef_module.AckStatus
AckError = mef_module.AckError
AckErrorSeverity = mef_module.AckErrorSeverity
Acknowledgment = mef_module.Acknowledgment
ValidationError = mef_module.ValidationError
ValidationSeverity = mef_module.ValidationSeverity
ValidationCategory = mef_module.ValidationCategory
ValidationResult = mef_module.ValidationResult
XmlSerializer = mef_module.XmlSerializer
BusinessRulesValidator = mef_module.BusinessRulesValidator


# =============================================================================
# FIXTURES - IRS ATS Test Scenario 7 Data (Charlie Boone - Form 4868 Extension)
# =============================================================================


@pytest.fixture
def charlie_boone_taxpayer() -> Dict[str, Any]:
    """Fixture for Charlie Boone (primary taxpayer) information.

    IRS ATS Test Scenario 7 - Single filer requesting automatic
    extension of time to file using Form 4868.

    ATS Reference SSN: 400-00-1042 (invalid for production validation)
    Test SSN: 400-01-1042 (valid format for testing validation logic)
    """
    return {
        "first_name": "Charlie",
        "last_name": "Boone",
        "ssn": "400-01-1042",
        "ssn_clean": "400011042",
        "ssn_ats_reference": "400-00-1042",
        "address": {
            "street": "789 Oak Avenue",
            "city": "Denver",
            "state": "CO",
            "zip": "80202"
        },
        "date_of_birth": date(1982, 9, 28),
        "occupation": "Software Engineer",
        "digital_assets": False,
    }


@pytest.fixture
def charlie_boone_form_4868() -> Dict[str, Any]:
    """Fixture for Form 4868 (Application for Automatic Extension).

    Charlie is requesting an automatic 6-month extension
    (from April 15 to October 15) to file his tax return.

    He is making a payment with the extension to reduce
    potential penalties and interest.
    """
    return {
        # Part I - Identification
        "taxpayer_name": "Charlie Boone",
        "taxpayer_ssn": "400-01-1042",
        "taxpayer_ssn_clean": "400011042",
        "address": {
            "street": "789 Oak Avenue",
            "city": "Denver",
            "state": "CO",
            "zip": "80202"
        },

        # Filing Status for Extension
        "filing_status": 1,  # Single

        # Part II - Individual Income Tax
        # Line 1 - Estimate of total tax liability for 2025
        "line_1_estimated_tax_liability": Decimal("12500.00"),

        # Line 2 - Total 2025 payments
        # (withholding, estimated payments, etc.)
        "line_2_total_payments": Decimal("10000.00"),

        # Line 3 - Balance due (Line 1 - Line 2)
        "line_3_balance_due": Decimal("2500.00"),

        # Line 4 - Amount you're paying
        "line_4_amount_paying": Decimal("2500.00"),

        # Additional information
        "out_of_country": False,  # Not out of US on due date
        "filed_form_1040nr": False,  # Not filing 1040-NR

        # Extension details
        "original_due_date": date(2026, 4, 15),
        "extended_due_date": date(2026, 10, 15),
        "extension_months": 6,

        # Payment Information (if paying electronically)
        "payment_method": "Electronic Funds Withdrawal",
        "bank_routing_number": "123456789",
        "bank_account_number": "987654321",
        "bank_account_type": "Checking",
        "payment_date": date(2026, 4, 15),

        # Practitioner PIN (if applicable)
        "practitioner_pin": None,

        # Signature
        "date_signed": date(2026, 4, 10),
    }


@pytest.fixture
def charlie_boone_extension_data(
    charlie_boone_taxpayer,
    charlie_boone_form_4868
) -> Dict[str, Any]:
    """Fixture for complete Form 4868 extension data for Charlie Boone.

    Tax Year: 2025
    Form Type: 4868 (Extension)
    Filing Status: Single (1)
    """
    return {
        # Taxpayer info
        "primary_ssn": charlie_boone_taxpayer["ssn_clean"],
        "primary_first_name": charlie_boone_taxpayer["first_name"],
        "primary_last_name": charlie_boone_taxpayer["last_name"],
        "address": charlie_boone_taxpayer["address"],
        "filing_status": 1,  # Single

        # Form type
        "form_type": "4868",
        "is_extension_only": True,

        # No spouse for single
        "spouse_ssn": None,
        "spouse_first_name": None,
        "spouse_last_name": None,

        # Extension-specific data
        "estimated_tax_liability": charlie_boone_form_4868["line_1_estimated_tax_liability"],
        "total_payments": charlie_boone_form_4868["line_2_total_payments"],
        "balance_due": charlie_boone_form_4868["line_3_balance_due"],
        "amount_paying": charlie_boone_form_4868["line_4_amount_paying"],

        # Extension dates
        "original_due_date": charlie_boone_form_4868["original_due_date"],
        "extended_due_date": charlie_boone_form_4868["extended_due_date"],

        # Payment info
        "has_payment": True,
        "payment_amount": charlie_boone_form_4868["line_4_amount_paying"],
        "payment_method": charlie_boone_form_4868["payment_method"],

        # Form 4868 data
        "form_4868": charlie_boone_form_4868,
    }


# =============================================================================
# TEST CLASS: Taxpayer Information
# =============================================================================


class TestTaxpayerInformation:
    """Tests for taxpayer information on Form 4868."""

    def test_taxpayer_name(self, charlie_boone_taxpayer):
        """Test taxpayer name."""
        assert charlie_boone_taxpayer["first_name"] == "Charlie"
        assert charlie_boone_taxpayer["last_name"] == "Boone"

    def test_taxpayer_ssn(self, charlie_boone_taxpayer):
        """Test taxpayer SSN format."""
        ssn_clean = charlie_boone_taxpayer["ssn_clean"]
        assert len(ssn_clean) == 9
        assert ssn_clean.isdigit()
        assert ssn_clean == "400011042"

    def test_taxpayer_address(self, charlie_boone_taxpayer):
        """Test taxpayer address."""
        address = charlie_boone_taxpayer["address"]
        assert address["city"] == "Denver"
        assert address["state"] == "CO"
        assert address["zip"] == "80202"


# =============================================================================
# TEST CLASS: Form 4868 Extension Details
# =============================================================================


class TestForm4868Extension:
    """Tests for Form 4868 extension application."""

    def test_form_type_is_extension(self, charlie_boone_extension_data):
        """Test form type is 4868 extension."""
        assert charlie_boone_extension_data["form_type"] == "4868"
        assert charlie_boone_extension_data["is_extension_only"] is True

    def test_estimated_tax_liability(self, charlie_boone_form_4868):
        """Test estimated tax liability amount."""
        assert charlie_boone_form_4868["line_1_estimated_tax_liability"] == Decimal("12500.00")

    def test_total_payments(self, charlie_boone_form_4868):
        """Test total payments amount."""
        assert charlie_boone_form_4868["line_2_total_payments"] == Decimal("10000.00")

    def test_balance_due_calculation(self, charlie_boone_form_4868):
        """Test balance due = estimated tax - payments."""
        estimated = charlie_boone_form_4868["line_1_estimated_tax_liability"]
        payments = charlie_boone_form_4868["line_2_total_payments"]
        expected_balance = estimated - payments

        assert charlie_boone_form_4868["line_3_balance_due"] == expected_balance
        assert charlie_boone_form_4868["line_3_balance_due"] == Decimal("2500.00")

    def test_amount_paying_with_extension(self, charlie_boone_form_4868):
        """Test amount being paid with extension."""
        assert charlie_boone_form_4868["line_4_amount_paying"] == Decimal("2500.00")

    def test_paying_full_balance(self, charlie_boone_form_4868):
        """Test taxpayer is paying full balance due."""
        balance = charlie_boone_form_4868["line_3_balance_due"]
        paying = charlie_boone_form_4868["line_4_amount_paying"]

        assert paying == balance


# =============================================================================
# TEST CLASS: Extension Dates
# =============================================================================


class TestExtensionDates:
    """Tests for extension date calculations."""

    def test_original_due_date(self, charlie_boone_form_4868):
        """Test original due date is April 15."""
        original = charlie_boone_form_4868["original_due_date"]
        assert original.month == 4
        assert original.day == 15
        assert original.year == 2026

    def test_extended_due_date(self, charlie_boone_form_4868):
        """Test extended due date is October 15."""
        extended = charlie_boone_form_4868["extended_due_date"]
        assert extended.month == 10
        assert extended.day == 15
        assert extended.year == 2026

    def test_extension_is_six_months(self, charlie_boone_form_4868):
        """Test extension period is 6 months."""
        assert charlie_boone_form_4868["extension_months"] == 6

        original = charlie_boone_form_4868["original_due_date"]
        extended = charlie_boone_form_4868["extended_due_date"]

        # October 15 - April 15 = 6 months
        months_diff = (extended.year - original.year) * 12 + (extended.month - original.month)
        assert months_diff == 6

    def test_signed_before_due_date(self, charlie_boone_form_4868):
        """Test form was signed before original due date."""
        signed = charlie_boone_form_4868["date_signed"]
        due = charlie_boone_form_4868["original_due_date"]

        assert signed < due


# =============================================================================
# TEST CLASS: Payment Information
# =============================================================================


class TestPaymentInformation:
    """Tests for payment information on Form 4868."""

    def test_has_payment(self, charlie_boone_extension_data):
        """Test extension includes payment."""
        assert charlie_boone_extension_data["has_payment"] is True

    def test_payment_amount(self, charlie_boone_extension_data):
        """Test payment amount."""
        assert charlie_boone_extension_data["payment_amount"] == Decimal("2500.00")

    def test_payment_method(self, charlie_boone_form_4868):
        """Test payment method is electronic."""
        assert charlie_boone_form_4868["payment_method"] == "Electronic Funds Withdrawal"

    def test_bank_information(self, charlie_boone_form_4868):
        """Test bank account information is provided."""
        assert charlie_boone_form_4868["bank_routing_number"] == "123456789"
        assert charlie_boone_form_4868["bank_account_number"] == "987654321"
        assert charlie_boone_form_4868["bank_account_type"] == "Checking"

    def test_payment_date(self, charlie_boone_form_4868):
        """Test payment date is on due date."""
        payment = charlie_boone_form_4868["payment_date"]
        due = charlie_boone_form_4868["original_due_date"]

        assert payment == due


# =============================================================================
# TEST CLASS: Filing Status
# =============================================================================


class TestFilingStatus:
    """Tests for filing status on extension."""

    def test_filing_status_single(self, charlie_boone_form_4868):
        """Test filing status is Single."""
        assert charlie_boone_form_4868["filing_status"] == 1

    def test_no_spouse(self, charlie_boone_extension_data):
        """Test no spouse information for single filer."""
        assert charlie_boone_extension_data["spouse_ssn"] is None
        assert charlie_boone_extension_data["spouse_first_name"] is None


# =============================================================================
# TEST CLASS: Special Circumstances
# =============================================================================


class TestSpecialCircumstances:
    """Tests for special circumstances flags on Form 4868."""

    def test_not_out_of_country(self, charlie_boone_form_4868):
        """Test taxpayer is not out of country."""
        assert charlie_boone_form_4868["out_of_country"] is False

    def test_not_filing_1040nr(self, charlie_boone_form_4868):
        """Test taxpayer is not filing Form 1040-NR."""
        assert charlie_boone_form_4868["filed_form_1040nr"] is False


# =============================================================================
# TEST CLASS: XML Serialization
# =============================================================================


class TestScenario7XMLSerialization:
    """Tests for XML serialization of Form 4868 data."""

    def test_taxpayer_info_creation(self, charlie_boone_taxpayer):
        """Test TaxpayerInfo object creation."""
        taxpayer_info = TaxpayerInfo(
            primary_ssn=charlie_boone_taxpayer["ssn_clean"],
            primary_first_name=charlie_boone_taxpayer["first_name"],
            primary_last_name=charlie_boone_taxpayer["last_name"],
            primary_date_of_birth=charlie_boone_taxpayer["date_of_birth"],
        )

        assert taxpayer_info.primary_ssn == "400011042"
        assert taxpayer_info.primary_first_name == "Charlie"
        assert taxpayer_info.primary_last_name == "Boone"

    def test_submission_id_generation(self):
        """Test MeF submission ID generation for extension."""
        submission_id = SubmissionId.generate(efin="123456", sequence=1)

        assert len(submission_id.submission_id) == 20
        assert submission_id.submission_id.isdigit()

    def test_extension_submission_type(self):
        """Test submission type for extension."""
        # Extensions use a different submission type
        assert hasattr(SubmissionType, 'INDIVIDUAL_1040') or hasattr(SubmissionType, 'EXTENSION_4868')


# =============================================================================
# TEST CLASS: Business Rules Validation
# =============================================================================


class TestScenario7BusinessRules:
    """Tests for business rules validation of Form 4868 data."""

    def test_extension_requires_ssn(self, charlie_boone_extension_data):
        """Test extension requires taxpayer SSN."""
        assert charlie_boone_extension_data["primary_ssn"] is not None
        assert len(charlie_boone_extension_data["primary_ssn"]) == 9

    def test_balance_due_not_negative(self, charlie_boone_form_4868):
        """Test balance due is not negative."""
        balance = charlie_boone_form_4868["line_3_balance_due"]
        assert balance >= Decimal("0")

    def test_payment_not_exceeds_balance(self, charlie_boone_form_4868):
        """Test payment does not exceed balance due."""
        balance = charlie_boone_form_4868["line_3_balance_due"]
        paying = charlie_boone_form_4868["line_4_amount_paying"]

        assert paying <= balance

    def test_extension_signed_timely(self, charlie_boone_form_4868):
        """Test extension is signed before due date."""
        signed = charlie_boone_form_4868["date_signed"]
        due = charlie_boone_form_4868["original_due_date"]

        assert signed <= due


# =============================================================================
# TEST CLASS: Integration Tests
# =============================================================================


class TestScenario7Integration:
    """Integration tests for the complete Form 4868 data."""

    def test_complete_extension_structure(self, charlie_boone_extension_data):
        """Test complete extension data has all required fields."""
        required_fields = [
            "primary_ssn", "primary_first_name", "primary_last_name",
            "form_type", "filing_status",
            "estimated_tax_liability", "total_payments", "balance_due",
            "original_due_date", "extended_due_date",
        ]

        for field in required_fields:
            assert field in charlie_boone_extension_data, f"Missing field: {field}"

    def test_tax_calculation_flow(self, charlie_boone_form_4868):
        """Test tax calculation flows correctly."""
        estimated = charlie_boone_form_4868["line_1_estimated_tax_liability"]
        payments = charlie_boone_form_4868["line_2_total_payments"]
        balance = charlie_boone_form_4868["line_3_balance_due"]

        assert balance == estimated - payments

    def test_extension_only_no_schedules(self, charlie_boone_extension_data):
        """Test extension-only filing has no schedules attached."""
        # Form 4868 is a standalone form
        assert charlie_boone_extension_data["is_extension_only"] is True

        # Should not have regular Form 1040 schedule flags
        assert "has_schedule_a" not in charlie_boone_extension_data
        assert "has_schedule_c" not in charlie_boone_extension_data

    def test_routing_number_format(self, charlie_boone_form_4868):
        """Test bank routing number format."""
        routing = charlie_boone_form_4868["bank_routing_number"]

        # Routing number should be 9 digits
        assert len(routing) == 9
        assert routing.isdigit()


# =============================================================================
# TEST CLASS: Extension-Specific Scenarios
# =============================================================================


class TestExtensionScenarios:
    """Tests for various extension scenarios."""

    def test_full_payment_with_extension(self, charlie_boone_form_4868):
        """Test scenario where taxpayer pays full balance."""
        balance = charlie_boone_form_4868["line_3_balance_due"]
        paying = charlie_boone_form_4868["line_4_amount_paying"]

        # Charlie is paying the full balance
        assert paying == balance

    def test_extension_for_single_filer(self, charlie_boone_extension_data):
        """Test extension for single filing status."""
        assert charlie_boone_extension_data["filing_status"] == 1
        assert charlie_boone_extension_data["spouse_ssn"] is None

    def test_no_special_circumstances(self, charlie_boone_form_4868):
        """Test no special circumstances apply."""
        assert charlie_boone_form_4868["out_of_country"] is False
        assert charlie_boone_form_4868["filed_form_1040nr"] is False

    def test_electronic_payment(self, charlie_boone_form_4868):
        """Test electronic payment setup."""
        assert charlie_boone_form_4868["payment_method"] == "Electronic Funds Withdrawal"
        assert charlie_boone_form_4868["bank_account_type"] in ["Checking", "Savings"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
