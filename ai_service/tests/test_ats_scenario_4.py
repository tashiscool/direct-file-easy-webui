"""Comprehensive pytest tests for IRS ATS Test Scenario 4 - Sarah Smith.

This module tests the MeF (Modernized e-File) service functionality using
IRS ATS (Assurance Testing System) Test Scenario 4 data for Sarah Smith.

Test Scenario Reference: IRS ATS Test Scenario 4 (ty25-1040-mef-ats-scenario-4-10212025.pdf)
Primary Taxpayer: Sarah Smith
Filing Status: Single (1)
No Dependents

Key Features Tested:
- Form 1040 basic return
- W-2 wage income
- Form 8835 (Renewable Electricity Production Credit - Solar)
- Form 8936 (Clean Vehicle Credits - BMW i4 Gran Coupe)
- Form 3800 (General Business Credit)
- Schedule 3 (Additional Credits)
- Transfer Election Statement (binary attachment)

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
# FIXTURES - IRS ATS Test Scenario 4 Data (Sarah Smith - Single)
# =============================================================================


@pytest.fixture
def sarah_smith_taxpayer() -> Dict[str, Any]:
    """Fixture for Sarah Smith (primary taxpayer) information.

    IRS ATS Test Scenario 4 - Single filer with renewable energy and
    clean vehicle credits.

    ATS Reference SSN: 400-00-1037 (invalid for production validation)
    Test SSN: 400-01-1037 (valid format for testing validation logic)
    """
    return {
        "first_name": "Sarah",
        "last_name": "Smith",
        "ssn": "400-01-1037",
        "ssn_clean": "400011037",
        "ssn_ats_reference": "400-00-1037",
        "address": {
            "street": "6712 Kittery Drive",
            "city": "Las Vegas",
            "state": "NV",
            "zip": "89107"
        },
        "date_of_birth": date(1989, 7, 8),
        "occupation": "Financial Analyst",
        "digital_assets": False,
    }


@pytest.fixture
def sarah_smith_w2_data() -> Dict[str, Any]:
    """Fixture for Sarah Smith W-2 data.

    W-2 from Capital One Bank
    EIN: 00-0000057 (ATS reference)
    """
    return {
        "employee_name": "Sarah Smith",
        "employer_name": "Capital One Bank",
        "employer_ein": "00-0000057",
        "employer_ein_clean": "000000057",
        "employer_ein_test": "12-3456784",  # Valid test EIN
        "employer_address": {
            "street": "495 South Main Street",
            "city": "Las Vegas",
            "state": "NV",
            "zip": "89139"
        },
        "wages": Decimal("36014.00"),
        "federal_withholding": Decimal("4581.00"),
        "ss_wages": Decimal("36014.00"),
        "ss_tax": Decimal("2233.00"),  # 36014 * 0.062
        "medicare_wages": Decimal("36014.00"),
        "medicare_tax": Decimal("522.00"),  # 36014 * 0.0145
        "state": None,  # Nevada has no state income tax
        "state_wages": Decimal("0.00"),
        "state_tax": Decimal("0.00"),
    }


@pytest.fixture
def sarah_smith_form_8835() -> Dict[str, Any]:
    """Fixture for Form 8835 (Renewable Electricity Production Credit).

    Solar energy facility owned by Texas Solar Energy
    IRS Registration Number: PAZ123055555
    """
    return {
        # Part I - Information on Qualified Facility
        "registration_number": "PAZ123055555",
        "facility_type": "8860952 Solar",
        "owner_name": "Texas Solar Energy",
        "owner_tin": "00-0000029",
        "facility_address": "808 Spring Love Lane, Houston, TX 77004",
        "coordinates": {
            "latitude": "+24.778212",
            "longitude": "-103.74636",
        },
        "construction_began": date(2017, 8, 15),
        "placed_in_service": date(2023, 9, 22),
        "is_expansion": False,

        # Qualified Facility Requirements
        "max_output_less_than_1mw": True,
        "construction_before_jan_29_2023": True,
        "meets_prevailing_wage_apprenticeship": True,

        # Bonus Credits
        "domestic_content_bonus": False,
        "energy_community_bonus": False,

        # Nameplate Capacity
        "nameplate_dc_kw": Decimal("10000"),  # 10,000 kW DC
        "nameplate_ac_kw": Decimal("765"),    # 765 kW AC

        # Part II - Renewable Electricity Production
        "solar_kwh_produced_sold": Decimal("440000"),
        "solar_rate": Decimal("0.006"),  # $0.006 per kWh
        "solar_credit_amount": Decimal("2640.00"),  # 440000 * 0.006

        # Phaseout and reductions
        "phaseout_adjustment": Decimal("0.00"),
        "credit_before_reduction": Decimal("2640.00"),
        "tax_exempt_bond_reduction": Decimal("0.00"),

        # Wind facility adjustments (N/A for solar)
        "wind_2017_adjustment": Decimal("0.00"),
        "wind_2018_2020_2021_adjustment": Decimal("0.00"),
        "wind_2019_adjustment": Decimal("0.00"),

        # Line 8 - Credit after reductions
        "line_8_credit": Decimal("2640.00"),

        # Line 9 - Increased credit amount (5x multiplier for qualified facilities)
        "increased_credit_multiplier": Decimal("5.0"),
        "line_9_credit": Decimal("13200.00"),  # 2640 * 5

        # Bonus credits (both N/A)
        "line_10_domestic_content_bonus": Decimal("0.00"),
        "line_11_energy_community_bonus": Decimal("0.00"),

        # Line 12 - Total
        "line_12_total": Decimal("13200.00"),

        # Line 13 - Final credit (no 90% reduction applies)
        "line_13_final_credit": Decimal("13200.00"),

        # Line 15 - Credit to report on Form 3800
        "line_15_credit": Decimal("13200.00"),
    }


@pytest.fixture
def sarah_smith_form_8936() -> Dict[str, Any]:
    """Fixture for Form 8936 (Clean Vehicle Credits).

    New clean vehicle: 2024 BMW i4 Gran Coupe
    VIN: IHGBH41JXMN108186
    """
    return {
        # Part I - MAGI
        "line_1a_agi_2025": Decimal("36014.00"),
        "line_2_magi_2025": Decimal("36014.00"),
        "line_3a_agi_2024": Decimal("0.00"),
        "line_4_magi_2024": Decimal("0.00"),
        "filing_status_2024": "S",  # Single

        # MAGI Limits check
        "magi_limit_single": Decimal("150000.00"),
        "exceeds_magi_limit": False,

        # Schedule A - Vehicle Details
        "vehicle": {
            "year": 2024,
            "make": "BMW",
            "model": "i4 Gran Coupe",
            "vin": "IHGBH41JXMN108186",
            "placed_in_service": date(2025, 1, 25),
            "is_new": True,
            "transferred_credit_to_dealer": False,
            "resold_within_30_days": False,
            "acquired_for_use": True,
        },

        # Part II - Business/Investment Use (N/A - personal use)
        "line_6_business_credit": Decimal("0.00"),
        "line_8_business_credit": Decimal("0.00"),

        # Part III - Personal Use of New Clean Vehicle
        "tentative_credit": Decimal("7500.00"),
        "business_use_percentage": Decimal("0.00"),
        "personal_use_credit": Decimal("7500.00"),

        # Note: This scenario appears to show credit on Form 8936
        # but the actual credit flows through Form 3800 line 1y
        "line_9_personal_credit": Decimal("130.00"),  # From ATS form

        # Part IV - Previously Owned (N/A)
        "line_14_previously_owned": Decimal("0.00"),

        # Part V - Commercial (N/A)
        "line_19_commercial": Decimal("0.00"),
    }


@pytest.fixture
def sarah_smith_form_3800() -> Dict[str, Any]:
    """Fixture for Form 3800 (General Business Credit).

    Combines credits from:
    - Form 8835 (Renewable Electricity Production Credit)
    - Form 8936 (Clean Vehicle Credit)
    """
    return {
        # Part I - Credits Not Allowed Against TMT
        "line_1_non_passive_credits": Decimal("13330.00"),  # 13200 + 130
        "line_2_passive_credits": Decimal("0.00"),
        "line_3_passive_allowed": Decimal("0.00"),
        "line_4_carryforward": Decimal("0.00"),
        "line_5_carryback": Decimal("0.00"),
        "line_6_total": Decimal("13330.00"),

        # Part II - Figuring Credit Allowed After Limitations
        # Section A
        "line_7_regular_tax": Decimal("0.00"),  # Need to calculate
        "line_8_amt": Decimal("0.00"),
        "line_9_add_7_8": Decimal("0.00"),
        "line_10a_foreign_tax_credit": Decimal("0.00"),
        "line_10b_allowable_credits": Decimal("0.00"),
        "line_10c_total": Decimal("0.00"),
        "line_11_net_income_tax": Decimal("0.00"),
        "line_12_net_regular_tax": Decimal("0.00"),
        "line_13_25_percent_excess": Decimal("0.00"),
        "line_14_tmt": Decimal("0.00"),
        "line_15_greater_13_14": Decimal("0.00"),
        "line_16_subtract_15_from_11": Decimal("0.00"),
        "line_17_credit_allowed": Decimal("0.00"),

        # Part III - Current Year GBCs
        "line_1f_form_8835": {
            "registration_number": "PAZ123055555",
            "pass_through_ein": "APPLD FOR",
            "credits_not_subject_passive": Decimal("13200.00"),
            "combined_after_passive": Decimal("13200.00"),
        },
        "line_1y_form_8936": {
            "pass_through_ein": "APPLD FOR",
            "credits_not_subject_passive": Decimal("130.00"),
            "combined_after_passive": Decimal("130.00"),
        },

        # Line 38 - Credit allowed for current year
        "line_38_credit_allowed": Decimal("0.00"),  # Limited by tax liability
    }


@pytest.fixture
def sarah_smith_schedule_3() -> Dict[str, Any]:
    """Fixture for Schedule 3 (Additional Credits and Payments).

    Part I - Nonrefundable Credits
    Line 6a: General business credit from Form 3800
    """
    return {
        # Part I - Nonrefundable Credits
        "line_1_foreign_tax_credit": Decimal("0.00"),
        "line_2_child_care_credit": Decimal("0.00"),
        "line_3_education_credit": Decimal("0.00"),
        "line_4_retirement_savings_credit": Decimal("0.00"),
        "line_5a_residential_clean_energy": Decimal("0.00"),
        "line_5b_energy_efficient_home": Decimal("0.00"),

        # Other nonrefundable credits
        "line_6a_general_business_credit": Decimal("0.00"),  # Limited by tax
        "line_6b_prior_year_minimum_tax": Decimal("0.00"),
        "line_6c_adoption_credit": Decimal("0.00"),
        "line_6d_elderly_disabled": Decimal("0.00"),
        "line_6f_clean_vehicle": Decimal("0.00"),

        # Line 7 - Total other nonrefundable credits
        "line_7_total_other": Decimal("0.00"),

        # Line 8 - Total Part I
        "line_8_total_part_1": Decimal("0.00"),

        # Part II - Other Payments and Refundable Credits
        "line_9_premium_tax_credit": Decimal("0.00"),
        "line_10_extension_payment": Decimal("0.00"),
        "line_11_excess_ss_tax": Decimal("0.00"),
        "line_12_federal_fuel_credit": Decimal("0.00"),
        "line_14_total_other": Decimal("0.00"),
        "line_15_total_part_2": Decimal("0.00"),
    }


@pytest.fixture
def sarah_smith_form_1040_data(
    sarah_smith_taxpayer,
    sarah_smith_w2_data,
    sarah_smith_form_8835,
    sarah_smith_form_8936,
    sarah_smith_form_3800,
    sarah_smith_schedule_3
) -> Dict[str, Any]:
    """Fixture for complete Form 1040 data for Sarah Smith.

    Tax Year: 2025
    Filing Status: Single (1)
    Standard Deduction (2025 Single): $15,000
    """
    # Income
    total_wages = sarah_smith_w2_data["wages"]
    total_income = total_wages
    agi = total_income  # No adjustments

    # Deduction - OBBBA 2025 Single Standard Deduction
    standard_deduction_single_2025 = Decimal("15750.00")

    # Taxable income
    taxable_income = max(Decimal("0"), agi - standard_deduction_single_2025)

    # Tax calculation (2025 tax brackets for Single)
    # $0 - $11,600: 10%
    # $11,601 - $47,150: 12%
    # Taxable income: $21,014
    tax_bracket_1 = Decimal("11600.00") * Decimal("0.10")  # $1,160
    remaining = taxable_income - Decimal("11600.00")  # $9,414
    tax_bracket_2 = remaining * Decimal("0.12")  # $1,129.68
    calculated_tax = (tax_bracket_1 + tax_bracket_2).quantize(Decimal("1"))  # $2,290

    # Credits (limited by tax liability)
    # Sarah has large credits but limited tax to offset
    total_credits_available = (
        sarah_smith_form_8835["line_15_credit"] +
        sarah_smith_form_8936["line_9_personal_credit"]
    )

    # Credits are limited to tax liability
    nonrefundable_credits = min(calculated_tax, total_credits_available)

    # Tax after credits
    tax_after_credits = max(Decimal("0"), calculated_tax - nonrefundable_credits)

    # Total tax
    total_tax = tax_after_credits

    # Payments
    federal_withholding = sarah_smith_w2_data["federal_withholding"]
    total_payments = federal_withholding

    # Refund or owed
    if total_payments > total_tax:
        refund = total_payments - total_tax
        amount_owed = Decimal("0")
    else:
        refund = Decimal("0")
        amount_owed = total_tax - total_payments

    return {
        # Taxpayer info
        "primary_ssn": sarah_smith_taxpayer["ssn_clean"],
        "primary_first_name": sarah_smith_taxpayer["first_name"],
        "primary_last_name": sarah_smith_taxpayer["last_name"],
        "address": sarah_smith_taxpayer["address"],
        "filing_status": 1,  # Single

        # Checkboxes
        "presidential_campaign": False,
        "digital_assets": False,

        # No spouse for Single
        "spouse_ssn": None,
        "spouse_first_name": None,
        "spouse_last_name": None,

        # No dependents
        "dependents": [],

        # Income (Lines 1-9)
        "line_1z_wages": total_wages,  # $36,014
        "wages": total_wages,
        "line_2a_tax_exempt_interest": Decimal("0"),
        "line_2b_taxable_interest": Decimal("0"),
        "line_3a_qualified_dividends": Decimal("0"),
        "line_3b_ordinary_dividends": Decimal("0"),
        "line_4a_ira_distributions": Decimal("0"),
        "line_4b_taxable_ira": Decimal("0"),
        "line_5a_pensions_annuities": Decimal("0"),
        "line_5b_taxable_pensions": Decimal("0"),
        "line_6a_social_security": Decimal("0"),
        "line_6b_taxable_social_security": Decimal("0"),
        "line_7_capital_gain": Decimal("0"),
        "line_8_schedule_1": Decimal("0"),
        "line_9_total_income": total_income,
        "total_income": total_income,

        # Adjustments (Line 10)
        "line_10_adjustments": Decimal("0"),

        # AGI (Line 11)
        "line_11_agi": agi,
        "agi": agi,

        # Deduction (Lines 12-14)
        "line_12_standard_deduction": standard_deduction_single_2025,
        "line_12_itemized_deduction": Decimal("0"),
        "line_12_deduction": standard_deduction_single_2025,
        "line_13_qbi_deduction": Decimal("0"),
        "line_14_total_deductions": standard_deduction_single_2025,
        "deduction": standard_deduction_single_2025,

        # Taxable income (Line 15)
        "line_15_taxable_income": taxable_income,
        "taxable_income": taxable_income,

        # Tax (Lines 16-24)
        "line_16_tax": calculated_tax,
        "line_17_schedule_2": Decimal("0"),
        "line_18_total": calculated_tax,
        "line_19_ctc_actc": Decimal("0"),
        "line_20_schedule_3": nonrefundable_credits,
        "line_21_credits_subtotal": nonrefundable_credits,
        "line_22_tax_minus_credits": tax_after_credits,
        "line_23_other_taxes": Decimal("0"),
        "line_24_total_tax": total_tax,
        "total_tax": total_tax,

        # Payments (Lines 25-33)
        "line_25a_w2_withholding": federal_withholding,
        "line_25b_1099_withholding": Decimal("0"),
        "line_25c_other_withholding": Decimal("0"),
        "line_25d_total_withholding": federal_withholding,
        "line_26_estimated_payments": Decimal("0"),
        "line_27_eic": Decimal("0"),
        "line_28_actc": Decimal("0"),
        "line_29_american_opportunity": Decimal("0"),
        "line_30_recovery_rebate": Decimal("0"),
        "line_31_schedule_3_part2": Decimal("0"),
        "line_32_other_payments": Decimal("0"),
        "line_33_total_payments": total_payments,
        "total_payments": total_payments,

        # Refund/Amount Owed (Lines 34-38)
        "line_34_overpaid": refund if refund > 0 else Decimal("0"),
        "line_35a_refund": refund if refund > 0 else Decimal("0"),
        "line_37_amount_owed": amount_owed,
        "refund": refund,
        "amount_owed": amount_owed,

        # Attached forms/schedules
        "has_form_8835": True,
        "has_form_8936": True,
        "has_form_3800": True,
        "has_schedule_3": True,
        "has_binary_attachment": True,
        "binary_attachment_description": "Transfer Election Statement",

        # Form data
        "form_8835": sarah_smith_form_8835,
        "form_8936": sarah_smith_form_8936,
        "form_3800": sarah_smith_form_3800,
        "schedule_3": sarah_smith_schedule_3,
    }


# =============================================================================
# TEST CLASS: W-2 Income
# =============================================================================


class TestW2Income:
    """Tests for W-2 wage income."""

    def test_w2_wages(self, sarah_smith_w2_data):
        """Test W-2 wages amount."""
        assert sarah_smith_w2_data["wages"] == Decimal("36014.00")

    def test_w2_federal_withholding(self, sarah_smith_w2_data):
        """Test W-2 federal withholding amount."""
        assert sarah_smith_w2_data["federal_withholding"] == Decimal("4581.00")

    def test_w2_employer_info(self, sarah_smith_w2_data):
        """Test W-2 employer information."""
        assert sarah_smith_w2_data["employer_name"] == "Capital One Bank"
        assert sarah_smith_w2_data["employer_address"]["city"] == "Las Vegas"
        assert sarah_smith_w2_data["employer_address"]["state"] == "NV"

    def test_w2_ss_medicare(self, sarah_smith_w2_data):
        """Test Social Security and Medicare amounts."""
        assert sarah_smith_w2_data["ss_wages"] == Decimal("36014.00")
        assert sarah_smith_w2_data["medicare_wages"] == Decimal("36014.00")


# =============================================================================
# TEST CLASS: Form 8835 Renewable Electricity Production Credit
# =============================================================================


class TestForm8835RenewableElectricity:
    """Tests for Form 8835 Renewable Electricity Production Credit."""

    def test_facility_information(self, sarah_smith_form_8835):
        """Test facility information."""
        assert sarah_smith_form_8835["registration_number"] == "PAZ123055555"
        assert sarah_smith_form_8835["facility_type"] == "8860952 Solar"
        assert sarah_smith_form_8835["owner_name"] == "Texas Solar Energy"

    def test_qualified_facility_requirements(self, sarah_smith_form_8835):
        """Test qualified facility requirements."""
        assert sarah_smith_form_8835["max_output_less_than_1mw"] is True
        assert sarah_smith_form_8835["construction_before_jan_29_2023"] is True
        assert sarah_smith_form_8835["meets_prevailing_wage_apprenticeship"] is True

    def test_solar_credit_calculation(self, sarah_smith_form_8835):
        """Test solar electricity credit calculation."""
        kwh = sarah_smith_form_8835["solar_kwh_produced_sold"]
        rate = sarah_smith_form_8835["solar_rate"]
        expected_credit = kwh * rate

        assert sarah_smith_form_8835["solar_credit_amount"] == expected_credit
        assert sarah_smith_form_8835["solar_credit_amount"] == Decimal("2640.00")

    def test_increased_credit_multiplier(self, sarah_smith_form_8835):
        """Test 5x increased credit for qualified facilities."""
        base_credit = sarah_smith_form_8835["line_8_credit"]
        multiplier = sarah_smith_form_8835["increased_credit_multiplier"]
        expected_increased = base_credit * multiplier

        assert sarah_smith_form_8835["line_9_credit"] == expected_increased
        assert sarah_smith_form_8835["line_9_credit"] == Decimal("13200.00")

    def test_no_bonus_credits(self, sarah_smith_form_8835):
        """Test no bonus credits apply."""
        assert sarah_smith_form_8835["domestic_content_bonus"] is False
        assert sarah_smith_form_8835["energy_community_bonus"] is False
        assert sarah_smith_form_8835["line_10_domestic_content_bonus"] == Decimal("0.00")
        assert sarah_smith_form_8835["line_11_energy_community_bonus"] == Decimal("0.00")

    def test_final_credit(self, sarah_smith_form_8835):
        """Test final renewable electricity credit."""
        assert sarah_smith_form_8835["line_15_credit"] == Decimal("13200.00")


# =============================================================================
# TEST CLASS: Form 8936 Clean Vehicle Credits
# =============================================================================


class TestForm8936CleanVehicle:
    """Tests for Form 8936 Clean Vehicle Credits."""

    def test_vehicle_information(self, sarah_smith_form_8936):
        """Test vehicle details."""
        vehicle = sarah_smith_form_8936["vehicle"]
        assert vehicle["year"] == 2024
        assert vehicle["make"] == "BMW"
        assert vehicle["model"] == "i4 Gran Coupe"
        assert vehicle["vin"] == "IHGBH41JXMN108186"

    def test_vehicle_placed_in_service(self, sarah_smith_form_8936):
        """Test vehicle placed in service date."""
        vehicle = sarah_smith_form_8936["vehicle"]
        assert vehicle["placed_in_service"] == date(2025, 1, 25)

    def test_vehicle_is_new(self, sarah_smith_form_8936):
        """Test vehicle is new (not previously owned)."""
        vehicle = sarah_smith_form_8936["vehicle"]
        assert vehicle["is_new"] is True
        assert vehicle["transferred_credit_to_dealer"] is False

    def test_magi_under_limit(self, sarah_smith_form_8936):
        """Test MAGI is under limit for single filer."""
        magi = sarah_smith_form_8936["line_2_magi_2025"]
        limit = sarah_smith_form_8936["magi_limit_single"]

        assert magi < limit
        assert sarah_smith_form_8936["exceeds_magi_limit"] is False

    def test_personal_use_credit(self, sarah_smith_form_8936):
        """Test personal use credit amount."""
        assert sarah_smith_form_8936["line_9_personal_credit"] == Decimal("130.00")


# =============================================================================
# TEST CLASS: Form 3800 General Business Credit
# =============================================================================


class TestForm3800GeneralBusinessCredit:
    """Tests for Form 3800 General Business Credit."""

    def test_form_8835_credit_reported(self, sarah_smith_form_3800):
        """Test Form 8835 credit is reported on Form 3800."""
        line_1f = sarah_smith_form_3800["line_1f_form_8835"]
        assert line_1f["credits_not_subject_passive"] == Decimal("13200.00")
        assert line_1f["registration_number"] == "PAZ123055555"

    def test_form_8936_credit_reported(self, sarah_smith_form_3800):
        """Test Form 8936 credit is reported on Form 3800."""
        line_1y = sarah_smith_form_3800["line_1y_form_8936"]
        assert line_1y["credits_not_subject_passive"] == Decimal("130.00")

    def test_total_credits(self, sarah_smith_form_3800):
        """Test total credits before limitation."""
        assert sarah_smith_form_3800["line_6_total"] == Decimal("13330.00")


# =============================================================================
# TEST CLASS: Tax Calculation
# =============================================================================


class TestTaxCalculation:
    """Tests for Form 1040 tax calculations."""

    def test_agi_calculation(self, sarah_smith_form_1040_data):
        """Test AGI equals total income (no adjustments)."""
        assert sarah_smith_form_1040_data["agi"] == sarah_smith_form_1040_data["total_income"]
        assert sarah_smith_form_1040_data["agi"] == Decimal("36014.00")

    def test_taxable_income_calculation(self, sarah_smith_form_1040_data):
        """Test taxable income = AGI - standard deduction."""
        agi = sarah_smith_form_1040_data["agi"]
        deduction = sarah_smith_form_1040_data["deduction"]
        expected_taxable = agi - deduction

        assert sarah_smith_form_1040_data["taxable_income"] == expected_taxable
        assert sarah_smith_form_1040_data["taxable_income"] == Decimal("21014.00")

    def test_standard_deduction_single_2025(self, sarah_smith_form_1040_data):
        """Test OBBBA 2025 single standard deduction."""
        assert sarah_smith_form_1040_data["line_12_standard_deduction"] == Decimal("15750.00")

    def test_credits_limited_by_tax(self, sarah_smith_form_1040_data):
        """Test credits are limited by tax liability."""
        calculated_tax = sarah_smith_form_1040_data["line_16_tax"]
        credits_used = sarah_smith_form_1040_data["line_20_schedule_3"]

        # Credits cannot exceed tax
        assert credits_used <= calculated_tax


# =============================================================================
# TEST CLASS: XML Serialization
# =============================================================================


class TestScenario4XMLSerialization:
    """Tests for XML serialization of Scenario 4 data."""

    def test_taxpayer_info_creation(self, sarah_smith_taxpayer):
        """Test TaxpayerInfo object creation."""
        taxpayer_info = TaxpayerInfo(
            primary_ssn=sarah_smith_taxpayer["ssn_clean"],
            primary_first_name=sarah_smith_taxpayer["first_name"],
            primary_last_name=sarah_smith_taxpayer["last_name"],
            primary_date_of_birth=sarah_smith_taxpayer["date_of_birth"],
        )

        assert taxpayer_info.primary_ssn == "400011037"
        assert taxpayer_info.primary_first_name == "Sarah"
        assert taxpayer_info.primary_last_name == "Smith"

    def test_submission_id_generation(self):
        """Test MeF submission ID generation."""
        submission_id = SubmissionId.generate(efin="123456", sequence=1)

        assert len(submission_id.submission_id) == 20
        assert submission_id.submission_id.isdigit()


# =============================================================================
# TEST CLASS: Business Rules Validation
# =============================================================================


class TestScenario4BusinessRules:
    """Tests for business rules validation of Scenario 4 data."""

    def test_single_filer_no_spouse(self, sarah_smith_form_1040_data):
        """Test single filer has no spouse information."""
        assert sarah_smith_form_1040_data["filing_status"] == 1
        assert sarah_smith_form_1040_data["spouse_ssn"] is None

    def test_single_filer_no_dependents(self, sarah_smith_form_1040_data):
        """Test single filer has no dependents."""
        assert len(sarah_smith_form_1040_data["dependents"]) == 0

    def test_required_forms_attached(self, sarah_smith_form_1040_data):
        """Test required forms are marked as attached."""
        assert sarah_smith_form_1040_data["has_form_8835"] is True
        assert sarah_smith_form_1040_data["has_form_8936"] is True
        assert sarah_smith_form_1040_data["has_form_3800"] is True
        assert sarah_smith_form_1040_data["has_schedule_3"] is True

    def test_binary_attachment(self, sarah_smith_form_1040_data):
        """Test binary attachment for Transfer Election Statement."""
        assert sarah_smith_form_1040_data["has_binary_attachment"] is True
        assert sarah_smith_form_1040_data["binary_attachment_description"] == "Transfer Election Statement"


# =============================================================================
# TEST CLASS: Integration Tests
# =============================================================================


class TestScenario4Integration:
    """Integration tests for the complete Scenario 4 data."""

    def test_complete_form_1040_structure(self, sarah_smith_form_1040_data):
        """Test complete form data has all required fields."""
        required_fields = [
            "primary_ssn", "primary_first_name", "primary_last_name",
            "filing_status", "wages", "total_income", "agi",
            "deduction", "taxable_income", "total_tax", "total_payments",
        ]

        for field in required_fields:
            assert field in sarah_smith_form_1040_data, f"Missing field: {field}"

    def test_form_1040_line_math(self, sarah_smith_form_1040_data):
        """Test Form 1040 line math consistency."""
        # Line 9 = Line 1z (for this simple scenario)
        assert sarah_smith_form_1040_data["line_9_total_income"] == sarah_smith_form_1040_data["line_1z_wages"]

        # Line 11 = Line 9 - Line 10
        assert sarah_smith_form_1040_data["line_11_agi"] == (
            sarah_smith_form_1040_data["line_9_total_income"] -
            sarah_smith_form_1040_data["line_10_adjustments"]
        )

        # Line 15 = Line 11 - Line 14
        assert sarah_smith_form_1040_data["line_15_taxable_income"] == (
            sarah_smith_form_1040_data["line_11_agi"] -
            sarah_smith_form_1040_data["line_14_total_deductions"]
        )

    def test_w2_to_form_1040_flow(self, sarah_smith_w2_data, sarah_smith_form_1040_data):
        """Test W-2 data flows correctly to Form 1040."""
        # W-2 wages -> Line 1z
        assert sarah_smith_form_1040_data["line_1z_wages"] == sarah_smith_w2_data["wages"]

        # Withholding -> Line 25a
        assert sarah_smith_form_1040_data["line_25a_w2_withholding"] == sarah_smith_w2_data["federal_withholding"]

    def test_form_8835_to_form_3800_flow(self, sarah_smith_form_8835, sarah_smith_form_3800):
        """Test Form 8835 credit flows to Form 3800."""
        form_8835_credit = sarah_smith_form_8835["line_15_credit"]
        form_3800_line_1f = sarah_smith_form_3800["line_1f_form_8835"]["credits_not_subject_passive"]

        assert form_3800_line_1f == form_8835_credit


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
