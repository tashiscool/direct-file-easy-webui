"""Comprehensive pytest tests for IRS ATS Test Scenario 13 - William and Nancy Birch.

This module tests the MeF (Modernized e-File) service functionality using
IRS ATS (Assurance Testing System) Test Scenario 13 data for William and Nancy Birch.

Test Scenario Reference: IRS ATS Test Scenario 13 (1040-mef-ats-scenario-13.pdf)
Primary Taxpayer: William Birch
Secondary Taxpayer: Nancy Birch
Filing Status: Married Filing Jointly (2)

Key Features Tested:
- Married Filing Jointly with low income
- Form 8911 (Alternative Fuel Vehicle Refueling Property Credit)
- Form 8911 Schedule A (Refueling Property Details)
- Form 6251 (Alternative Minimum Tax - no AMT due)
- Schedule 3 (Additional Credits and Payments)
- Credit exceeds tax liability (results in refund)

Tax Year: 2025

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
# FIXTURES - IRS ATS Test Scenario 13 Data (William and Nancy Birch - MFJ)
# =============================================================================


@pytest.fixture
def william_birch_taxpayer() -> Dict[str, Any]:
    """Fixture for William Birch (primary taxpayer) information.

    IRS ATS Test Scenario 13 - Married Filing Jointly with refueling credit.

    ATS Reference SSN: 400-00-1313
    """
    return {
        "first_name": "William",
        "last_name": "Birch",
        "ssn": "400-01-1313",
        "ssn_clean": "400011313",
        "ssn_ats_reference": "400-00-1313",
        "address": {
            "street": "13 Elm Street",
            "city": "Anytown",
            "state": "TX",
            "zip": "77013"
        },
        "digital_assets": False,
    }


@pytest.fixture
def nancy_birch_spouse() -> Dict[str, Any]:
    """Fixture for Nancy Birch (spouse) information.

    ATS Reference SSN: 400-00-1234
    """
    return {
        "first_name": "Nancy",
        "last_name": "Birch",
        "ssn": "400-01-1234",
        "ssn_clean": "400011234",
        "ssn_ats_reference": "400-00-1234",
    }


@pytest.fixture
def william_birch_w2_data() -> Dict[str, Any]:
    """Fixture for William Birch W-2 from Oak Supply Co."""
    return {
        "employee_name": "William Birch",
        "employer_name": "Oak Supply Co",
        "employer_ein": "00-0000014",
        "employer_ein_clean": "000000014",
        "employer_address": {
            "street": "201 Elm Drive",
            "city": "Anytown",
            "state": "TX",
            "zip": "77013"
        },
        "wages": Decimal("31620.00"),
        "federal_withholding": Decimal("609.00"),
        "ss_wages": Decimal("31620.00"),
        "ss_tax": Decimal("1960.00"),
        "medicare_wages": Decimal("31620.00"),
        "medicare_tax": Decimal("458.00"),
        "state": None,  # Texas has no state income tax
        "state_wages": None,
        "state_tax": None,
    }


@pytest.fixture
def birch_form_8911_schedule_a() -> Dict[str, Any]:
    """Fixture for Form 8911 Schedule A (Alternative Fuel Vehicle Refueling Property).

    Electric charger installed at main home.
    """
    return {
        # Part I - Property Details
        "description": "Electric Charger",
        "location_address": "13 Elm Street, Anytown TX 77013",
        "census_tract_geoid": "48201100000",
        "date_construction_began": date(2025, 3, 1),
        "date_placed_in_service": date(2025, 3, 1),
        "is_eligible_census_tract": True,

        # Part II - Business/Investment Use (N/A for personal use)
        "line_8_cost": Decimal("1000.00"),
        "line_9_business_use_percent": Decimal("0"),
        "line_10_business_portion": Decimal("0.00"),

        # Part III - Personal Use
        "is_main_home": True,
        "line_18_personal_portion": Decimal("1000.00"),
        "line_19_personal_credit_rate": Decimal("300.00"),  # 30% of $1,000
        "line_20_max_personal_credit": Decimal("1000.00"),
        "line_21_personal_credit": Decimal("300.00"),  # Smaller of 19 or 20
    }


@pytest.fixture
def birch_form_8911() -> Dict[str, Any]:
    """Fixture for Form 8911 (Alternative Fuel Vehicle Refueling Property Credit)."""
    return {
        # Part I - Business/Investment Credit
        "line_1_business_credit_schedule_a": Decimal("0.00"),
        "line_3_business_credit": Decimal("0.00"),

        # Part II - Personal Use Credit
        "line_4_personal_credit_schedule_a": Decimal("300.00"),
        "line_5_regular_tax_before_credits": Decimal("162.00"),
        "line_6c_credits_reducing_tax": Decimal("0.00"),
        "line_7_net_regular_tax": Decimal("162.00"),
        "line_8_tentative_minimum_tax": Decimal("0.00"),
        "line_9_available_for_credit": Decimal("162.00"),
        "line_10_personal_credit": Decimal("162.00"),  # Smaller of line 4 or line 9
    }


@pytest.fixture
def birch_form_6251() -> Dict[str, Any]:
    """Fixture for Form 6251 (Alternative Minimum Tax - Individuals).

    No AMT is due because income is below exemption amount.
    """
    return {
        # Part I - AMTI
        "line_1_taxable_income": Decimal("1620.00"),
        "line_2a_standard_deduction": Decimal("31500.00"),  # Add back for AMT (OBBBA 2025)
        "line_4_amti": Decimal("31620.00"),

        # Part II - AMT
        "line_5_exemption": Decimal("137000.00"),  # MFJ exemption 2025
        "line_6_amti_over_exemption": Decimal("0.00"),  # 31,620 - 137,000 = negative, so 0
        "line_7_amt_rate_calculation": Decimal("0.00"),
        "line_9_tentative_minimum_tax": Decimal("0.00"),
        "line_10_regular_tax": Decimal("162.00"),
        "line_11_amt": Decimal("0.00"),  # No AMT because TMT < regular tax
    }


@pytest.fixture
def birch_schedule_3() -> Dict[str, Any]:
    """Fixture for Schedule 3 (Additional Credits and Payments)."""
    return {
        # Part I - Nonrefundable Credits
        "line_6j_alternative_fuel_refueling_credit": Decimal("162.00"),
        "line_7_total_other_credits": Decimal("162.00"),
        "line_8_total_nonrefundable_credits": Decimal("162.00"),

        # Part II - Other Payments (none)
        "line_15_total_payments": Decimal("0.00"),
    }


@pytest.fixture
def birch_form_1040_data(
    william_birch_taxpayer,
    nancy_birch_spouse,
    william_birch_w2_data,
    birch_form_8911_schedule_a,
    birch_form_8911,
    birch_form_6251,
    birch_schedule_3
) -> Dict[str, Any]:
    """Fixture for complete Form 1040 data for William and Nancy Birch.

    Tax Year: 2025
    Filing Status: Married Filing Jointly (2)
    """
    # Income
    w2_wages = william_birch_w2_data["wages"]
    total_income = w2_wages

    # AGI (no adjustments)
    agi = total_income

    # Standard deduction - OBBBA 2025 MFJ
    standard_deduction = Decimal("31500.00")

    # Taxable income
    taxable_income = max(Decimal("0"), agi - standard_deduction)

    # Tax calculation (10% bracket for MFJ on $1,620)
    calculated_tax = Decimal("162.00")

    # Credits from Schedule 3
    total_credits = birch_schedule_3["line_8_total_nonrefundable_credits"]

    # Tax after credits
    tax_after_credits = max(Decimal("0"), calculated_tax - total_credits)

    # Total tax
    total_tax = tax_after_credits

    # Payments
    total_withholding = william_birch_w2_data["federal_withholding"]
    total_payments = total_withholding

    # Refund
    if total_payments > total_tax:
        refund = total_payments - total_tax
        amount_owed = Decimal("0")
    else:
        refund = Decimal("0")
        amount_owed = total_tax - total_payments

    return {
        # Taxpayer info
        "primary_ssn": william_birch_taxpayer["ssn_clean"],
        "primary_first_name": william_birch_taxpayer["first_name"],
        "primary_last_name": william_birch_taxpayer["last_name"],
        "address": william_birch_taxpayer["address"],
        "filing_status": 2,  # Married Filing Jointly

        # Spouse info
        "spouse_ssn": nancy_birch_spouse["ssn_clean"],
        "spouse_first_name": nancy_birch_spouse["first_name"],
        "spouse_last_name": nancy_birch_spouse["last_name"],

        # Checkboxes
        "digital_assets": False,

        # Income (Lines 1-9)
        "line_1a_w2_wages": w2_wages,
        "line_1z_total_wages": w2_wages,
        "line_9_total_income": total_income,

        # AGI (Line 11)
        "line_11a_agi": agi,
        "line_11b_agi": agi,

        # Deduction (Lines 12-14)
        "line_12e_standard_deduction": standard_deduction,
        "line_14_total_deductions": standard_deduction,

        # Taxable income (Line 15)
        "line_15_taxable_income": taxable_income,

        # Tax (Lines 16-24)
        "line_16_tax": calculated_tax,
        "line_18_total": calculated_tax,
        "line_20_schedule_3_credits": total_credits,
        "line_21_total_credits": total_credits,
        "line_22_tax_minus_credits": tax_after_credits,
        "line_24_total_tax": total_tax,

        # Payments (Lines 25-33)
        "line_25a_w2_withholding": total_withholding,
        "line_25d_total_withholding": total_withholding,
        "line_33_total_payments": total_payments,

        # Refund
        "line_34_overpaid": refund,
        "line_35a_refund": refund,
        "line_37_amount_owed": amount_owed,

        # Summary values
        "wages": w2_wages,
        "total_income": total_income,
        "agi": agi,
        "deduction": standard_deduction,
        "taxable_income": taxable_income,
        "total_tax": total_tax,
        "total_payments": total_payments,
        "refund": refund,
        "amount_owed": amount_owed,

        # Attached forms/schedules
        "has_schedule_3": True,
        "has_form_8911": True,
        "has_form_8911_schedule_a": True,
        "has_form_6251": True,

        # Form data
        "schedule_3": birch_schedule_3,
        "form_8911": birch_form_8911,
        "form_8911_schedule_a": birch_form_8911_schedule_a,
        "form_6251": birch_form_6251,
        "w2": william_birch_w2_data,
    }


# =============================================================================
# TEST CLASS: Taxpayer Information
# =============================================================================


class TestTaxpayerInformation:
    """Tests for taxpayer and spouse information."""

    def test_primary_taxpayer_name(self, william_birch_taxpayer):
        """Test primary taxpayer name."""
        assert william_birch_taxpayer["first_name"] == "William"
        assert william_birch_taxpayer["last_name"] == "Birch"

    def test_spouse_name(self, nancy_birch_spouse):
        """Test spouse name."""
        assert nancy_birch_spouse["first_name"] == "Nancy"
        assert nancy_birch_spouse["last_name"] == "Birch"

    def test_texas_address(self, william_birch_taxpayer):
        """Test Texas address (no state income tax)."""
        address = william_birch_taxpayer["address"]
        assert address["state"] == "TX"


# =============================================================================
# TEST CLASS: W-2 Income
# =============================================================================


class TestW2Income:
    """Tests for W-2 wage income."""

    def test_w2_wages(self, william_birch_w2_data):
        """Test W-2 wages."""
        assert william_birch_w2_data["wages"] == Decimal("31620.00")

    def test_w2_withholding(self, william_birch_w2_data):
        """Test W-2 federal withholding."""
        assert william_birch_w2_data["federal_withholding"] == Decimal("609.00")

    def test_no_state_tax(self, william_birch_w2_data):
        """Test no state tax (Texas)."""
        assert william_birch_w2_data["state"] is None
        assert william_birch_w2_data["state_tax"] is None


# =============================================================================
# TEST CLASS: Form 8911 Schedule A - Refueling Property
# =============================================================================


class TestForm8911ScheduleARefuelingProperty:
    """Tests for Form 8911 Schedule A refueling property details."""

    def test_property_description(self, birch_form_8911_schedule_a):
        """Test refueling property is an electric charger."""
        assert birch_form_8911_schedule_a["description"] == "Electric Charger"

    def test_eligible_census_tract(self, birch_form_8911_schedule_a):
        """Test property is in eligible census tract."""
        assert birch_form_8911_schedule_a["is_eligible_census_tract"] is True

    def test_census_tract_geoid(self, birch_form_8911_schedule_a):
        """Test census tract GEOID."""
        assert birch_form_8911_schedule_a["census_tract_geoid"] == "48201100000"

    def test_installed_at_main_home(self, birch_form_8911_schedule_a):
        """Test property is installed at main home."""
        assert birch_form_8911_schedule_a["is_main_home"] is True

    def test_property_cost(self, birch_form_8911_schedule_a):
        """Test property cost."""
        assert birch_form_8911_schedule_a["line_8_cost"] == Decimal("1000.00")

    def test_personal_use_credit_calculation(self, birch_form_8911_schedule_a):
        """Test 30% credit calculation for personal use."""
        cost = birch_form_8911_schedule_a["line_18_personal_portion"]
        expected_credit = cost * Decimal("0.30")
        assert birch_form_8911_schedule_a["line_19_personal_credit_rate"] == expected_credit

    def test_final_personal_credit(self, birch_form_8911_schedule_a):
        """Test final personal credit is smaller of calculated or max."""
        calculated = birch_form_8911_schedule_a["line_19_personal_credit_rate"]
        maximum = birch_form_8911_schedule_a["line_20_max_personal_credit"]
        credit = birch_form_8911_schedule_a["line_21_personal_credit"]
        assert credit == min(calculated, maximum)
        assert credit == Decimal("300.00")


# =============================================================================
# TEST CLASS: Form 8911 - Refueling Credit
# =============================================================================


class TestForm8911RefuelingCredit:
    """Tests for Form 8911 alternative fuel vehicle refueling property credit."""

    def test_no_business_credit(self, birch_form_8911):
        """Test no business/investment credit claimed."""
        assert birch_form_8911["line_3_business_credit"] == Decimal("0.00")

    def test_personal_credit_from_schedule_a(self, birch_form_8911, birch_form_8911_schedule_a):
        """Test personal credit flows from Schedule A."""
        assert birch_form_8911["line_4_personal_credit_schedule_a"] == \
               birch_form_8911_schedule_a["line_21_personal_credit"]

    def test_credit_limited_by_tax(self, birch_form_8911):
        """Test credit is limited by available tax liability."""
        potential_credit = birch_form_8911["line_4_personal_credit_schedule_a"]
        available_tax = birch_form_8911["line_9_available_for_credit"]
        actual_credit = birch_form_8911["line_10_personal_credit"]

        # Credit of $300 is limited by tax of $162
        assert potential_credit == Decimal("300.00")
        assert available_tax == Decimal("162.00")
        assert actual_credit == min(potential_credit, available_tax)
        assert actual_credit == Decimal("162.00")

    def test_no_tentative_minimum_tax(self, birch_form_8911):
        """Test no tentative minimum tax affects credit."""
        assert birch_form_8911["line_8_tentative_minimum_tax"] == Decimal("0.00")


# =============================================================================
# TEST CLASS: Form 6251 - Alternative Minimum Tax
# =============================================================================


class TestForm6251AlternativeMinimumTax:
    """Tests for Form 6251 alternative minimum tax."""

    def test_amti_calculation(self, birch_form_6251):
        """Test alternative minimum taxable income calculation."""
        # AMTI = taxable income + standard deduction (add-back)
        taxable = birch_form_6251["line_1_taxable_income"]
        std_ded = birch_form_6251["line_2a_standard_deduction"]
        expected_amti = taxable + std_ded
        assert birch_form_6251["line_4_amti"] == expected_amti

    def test_amti_below_exemption(self, birch_form_6251):
        """Test AMTI is below exemption amount."""
        amti = birch_form_6251["line_4_amti"]
        exemption = birch_form_6251["line_5_exemption"]
        assert amti < exemption

    def test_no_amt_due(self, birch_form_6251):
        """Test no AMT is due."""
        assert birch_form_6251["line_6_amti_over_exemption"] == Decimal("0.00")
        assert birch_form_6251["line_9_tentative_minimum_tax"] == Decimal("0.00")
        assert birch_form_6251["line_11_amt"] == Decimal("0.00")


# =============================================================================
# TEST CLASS: Schedule 3 - Additional Credits
# =============================================================================


class TestSchedule3AdditionalCredits:
    """Tests for Schedule 3 additional credits and payments."""

    def test_refueling_credit_on_line_6j(self, birch_schedule_3):
        """Test refueling credit is reported on line 6j."""
        assert birch_schedule_3["line_6j_alternative_fuel_refueling_credit"] == Decimal("162.00")

    def test_total_nonrefundable_credits(self, birch_schedule_3, birch_form_8911):
        """Test total nonrefundable credits equals Form 8911 credit."""
        assert birch_schedule_3["line_8_total_nonrefundable_credits"] == \
               birch_form_8911["line_10_personal_credit"]


# =============================================================================
# TEST CLASS: Tax Calculation
# =============================================================================


class TestTaxCalculation:
    """Tests for Form 1040 tax calculations."""

    def test_filing_status_mfj(self, birch_form_1040_data):
        """Test filing status is Married Filing Jointly."""
        assert birch_form_1040_data["filing_status"] == 2

    def test_total_income(self, birch_form_1040_data):
        """Test total income equals W-2 wages."""
        assert birch_form_1040_data["line_9_total_income"] == Decimal("31620.00")

    def test_standard_deduction_mfj(self, birch_form_1040_data):
        """Test OBBBA 2025 MFJ standard deduction."""
        assert birch_form_1040_data["line_12e_standard_deduction"] == Decimal("31500.00")

    def test_taxable_income(self, birch_form_1040_data):
        """Test taxable income calculation."""
        agi = birch_form_1040_data["agi"]
        deduction = birch_form_1040_data["deduction"]
        expected = agi - deduction
        assert birch_form_1040_data["line_15_taxable_income"] == expected
        assert birch_form_1040_data["line_15_taxable_income"] == Decimal("1620.00")

    def test_tax_at_10_percent(self, birch_form_1040_data):
        """Test tax is 10% of taxable income (lowest bracket)."""
        taxable = birch_form_1040_data["line_15_taxable_income"]
        tax = birch_form_1040_data["line_16_tax"]
        # $1,620 * 10% = $162
        assert tax == Decimal("162.00")

    def test_credits_reduce_tax_to_zero(self, birch_form_1040_data):
        """Test credits reduce tax to zero."""
        tax = birch_form_1040_data["line_16_tax"]
        credits = birch_form_1040_data["line_20_schedule_3_credits"]
        tax_after_credits = birch_form_1040_data["line_22_tax_minus_credits"]

        assert tax == Decimal("162.00")
        assert credits == Decimal("162.00")
        assert tax_after_credits == Decimal("0.00")

    def test_total_tax_is_zero(self, birch_form_1040_data):
        """Test total tax is zero after credits."""
        assert birch_form_1040_data["line_24_total_tax"] == Decimal("0.00")

    def test_refund(self, birch_form_1040_data):
        """Test refund calculation."""
        total_payments = birch_form_1040_data["line_33_total_payments"]
        total_tax = birch_form_1040_data["line_24_total_tax"]
        expected_refund = total_payments - total_tax

        assert birch_form_1040_data["line_34_overpaid"] == expected_refund
        assert birch_form_1040_data["line_35a_refund"] == Decimal("609.00")


# =============================================================================
# TEST CLASS: XML Serialization
# =============================================================================


class TestScenario13XMLSerialization:
    """Tests for XML serialization of Scenario 13 data."""

    def test_taxpayer_info_creation(self, william_birch_taxpayer, nancy_birch_spouse):
        """Test TaxpayerInfo object creation for MFJ."""
        taxpayer_info = TaxpayerInfo(
            primary_ssn=william_birch_taxpayer["ssn_clean"],
            primary_first_name=william_birch_taxpayer["first_name"],
            primary_last_name=william_birch_taxpayer["last_name"],
            spouse_ssn=nancy_birch_spouse["ssn_clean"],
            spouse_first_name=nancy_birch_spouse["first_name"],
            spouse_last_name=nancy_birch_spouse["last_name"],
        )

        assert taxpayer_info.primary_ssn == "400011313"
        assert taxpayer_info.spouse_ssn == "400011234"

    def test_submission_id_generation(self):
        """Test MeF submission ID generation."""
        submission_id = SubmissionId.generate(efin="123456", sequence=1)

        assert len(submission_id.submission_id) == 20
        assert submission_id.submission_id.isdigit()


# =============================================================================
# TEST CLASS: Business Rules Validation
# =============================================================================


class TestScenario13BusinessRules:
    """Tests for business rules validation of Scenario 13 data."""

    def test_mfj_requires_spouse_ssn(self, birch_form_1040_data):
        """Test MFJ filing requires spouse SSN."""
        assert birch_form_1040_data["filing_status"] == 2
        assert birch_form_1040_data["spouse_ssn"] is not None

    def test_form_8911_required_for_refueling_credit(self, birch_form_1040_data):
        """Test Form 8911 is attached when claiming refueling credit."""
        assert birch_form_1040_data["has_form_8911"] is True
        assert birch_form_1040_data["has_form_8911_schedule_a"] is True

    def test_form_6251_completed(self, birch_form_1040_data):
        """Test Form 6251 is attached (even though no AMT due)."""
        assert birch_form_1040_data["has_form_6251"] is True

    def test_nonrefundable_credit_limited_to_tax(self, birch_form_8911):
        """Test nonrefundable credit cannot exceed tax liability."""
        potential = birch_form_8911["line_4_personal_credit_schedule_a"]
        actual = birch_form_8911["line_10_personal_credit"]
        available_tax = birch_form_8911["line_9_available_for_credit"]

        assert actual <= potential
        assert actual <= available_tax


# =============================================================================
# TEST CLASS: Integration Tests
# =============================================================================


class TestScenario13Integration:
    """Integration tests for the complete Scenario 13 data."""

    def test_complete_form_1040_structure(self, birch_form_1040_data):
        """Test complete form data has all required fields."""
        required_fields = [
            "primary_ssn", "primary_first_name", "primary_last_name",
            "spouse_ssn", "filing_status",
            "wages", "total_income", "agi", "deduction", "taxable_income",
            "total_tax", "total_payments", "refund",
        ]

        for field in required_fields:
            assert field in birch_form_1040_data, f"Missing field: {field}"

    def test_form_8911_schedule_a_to_8911_flow(self, birch_form_8911_schedule_a, birch_form_8911):
        """Test Form 8911 Schedule A flows to Form 8911."""
        assert birch_form_8911["line_4_personal_credit_schedule_a"] == \
               birch_form_8911_schedule_a["line_21_personal_credit"]

    def test_form_8911_to_schedule_3_flow(self, birch_form_8911, birch_schedule_3):
        """Test Form 8911 credit flows to Schedule 3."""
        assert birch_schedule_3["line_6j_alternative_fuel_refueling_credit"] == \
               birch_form_8911["line_10_personal_credit"]

    def test_schedule_3_to_form_1040_flow(self, birch_schedule_3, birch_form_1040_data):
        """Test Schedule 3 credits flow to Form 1040."""
        assert birch_form_1040_data["line_20_schedule_3_credits"] == \
               birch_schedule_3["line_8_total_nonrefundable_credits"]

    def test_form_6251_tmt_to_form_8911(self, birch_form_6251, birch_form_8911):
        """Test Form 6251 TMT flows to Form 8911."""
        assert birch_form_8911["line_8_tentative_minimum_tax"] == \
               birch_form_6251["line_9_tentative_minimum_tax"]

    def test_credit_wasted_due_to_low_tax(self, birch_form_8911_schedule_a, birch_form_8911):
        """Test credit potential partially wasted due to low tax liability."""
        potential_credit = birch_form_8911_schedule_a["line_21_personal_credit"]
        actual_credit = birch_form_8911["line_10_personal_credit"]
        wasted_credit = potential_credit - actual_credit

        # $300 potential - $162 actual = $138 wasted (nonrefundable)
        assert potential_credit == Decimal("300.00")
        assert actual_credit == Decimal("162.00")
        assert wasted_credit == Decimal("138.00")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
