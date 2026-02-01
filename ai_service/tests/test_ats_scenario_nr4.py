"""Comprehensive pytest tests for IRS ATS Test Scenario NR-4 - Isaac Hill.

This module tests the MeF (Modernized e-File) service functionality using
IRS ATS (Assurance Testing System) Test Scenario NR-4 data for Isaac Hill.

Test Scenario Reference: IRS ATS Test Scenario NR-4 (ty25-1040-nr-mef-ats-scenario-4-10212025.pdf)
Primary Taxpayer: Isaac Hill
Filing Status: Qualifying Surviving Spouse (QSS) - Form 1040-NR
Spouse Deceased: 02/18/2024

Key Features Tested:
- Form 1040-NR for Nonresident Alien (QSS filing status)
- W-2 wage income from Pink Paradise LLC
- IRA distribution with early withdrawal penalty (Form 5329 implied)
- Schedule 2 (Additional Taxes) - early IRA distribution penalty
- Schedule 3 (Additional Credits and Payments)
- Form 3800 (General Business Credit)
- Form 8835 (Renewable Electricity Production Credit) - Solar
- Form 8936 (Clean Vehicle Credits)
- Schedule A (Form 8936) - New clean vehicle credit
- Foreign address (Thailand)
- Federal Disaster designation

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

# Import from the module file using dynamic loading
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
# FIXTURES - Taxpayer Information
# =============================================================================

@pytest.fixture
def isaac_hill_taxpayer() -> Dict[str, Any]:
    """Fixture for Isaac Hill (primary taxpayer) information."""
    return {
        "first_name": "Isaac",
        "last_name": "Hill",
        "ssn": "123-01-5555",           # Valid format for testing
        "ssn_clean": "123015555",        # 9 digits, no dashes
        "ssn_ats_reference": "123-00-5555",  # Original ATS SSN
        "foreign_address": {
            "street": "123 Sukhumvit Road",
            "city": "Khlong Toei",
            "province": "Bangkok",
            "postal_code": "10110",
            "country": "Thailand"
        },
        "date_of_birth": date(1980, 5, 15),  # Estimated
        "occupation": "Driver",
        "digital_assets": False,
        "is_nonresident_alien": True,
        "filing_status": "QSS",  # Qualifying Surviving Spouse
        "filing_status_code": 5,
        "spouse_deceased_date": date(2024, 2, 18),
        "federal_disaster": True,
        "prior_year_magi": Decimal("47511.00"),  # TY 2024 MAGI
        "prior_year_filing_status": "Single",
    }


# =============================================================================
# FIXTURES - W-2 Income
# =============================================================================

@pytest.fixture
def isaac_hill_w2_data() -> Dict[str, Any]:
    """Fixture for Isaac Hill's W-2 from Pink Paradise LLC."""
    return {
        "employee_name": "Issac Hill",  # Note: W-2 shows "Issac" (typo)
        "employer_name": "Pink Paradise LLC",
        "employer_ein": "00-5559992",
        "employer_ein_clean": "005559992",
        "employer_ein_test": "12-3456992",  # Valid test EIN
        "employer_address": {
            "street": "4222 Terrance Lane",
            "city": "Houston",
            "state": "TX",
            "zip": "77059"
        },
        # Box 1 - Wages, tips, other compensation
        "wages": Decimal("53792.00"),
        # Box 2 - Federal income tax withheld
        "federal_withholding": Decimal("8493.00"),
        # Box 3 - Social security wages
        "ss_wages": Decimal("53792.00"),
        # Box 4 - Social security tax withheld
        "ss_tax": Decimal("3335.00"),
        # Box 5 - Medicare wages and tips
        "medicare_wages": Decimal("53792.00"),
        # Box 6 - Medicare tax withheld
        "medicare_tax": Decimal("780.00"),
        # No state taxes
        "state": None,
        "state_wages": Decimal("0.00"),
        "state_tax": Decimal("0.00"),
    }


# =============================================================================
# FIXTURES - IRA Distribution
# =============================================================================

@pytest.fixture
def isaac_hill_ira_distribution() -> Dict[str, Any]:
    """Fixture for IRA distribution (Form 1099-R implied)."""
    return {
        # Line 4a - Total IRA distributions
        "gross_distribution": Decimal("6200.00"),
        # Line 4b - Taxable amount
        "taxable_amount": Decimal("3200.00"),
        # Implies rollover of $3,000 ($6,200 - $3,200)
        "rollover_amount": Decimal("3000.00"),
        # Early withdrawal penalty on Form 5329
        "early_withdrawal_penalty": Decimal("320.00"),  # 10% of $3,200
    }


# =============================================================================
# FIXTURES - Schedule 2 (Additional Taxes)
# =============================================================================

@pytest.fixture
def isaac_hill_schedule_2(isaac_hill_ira_distribution) -> Dict[str, Any]:
    """Fixture for Schedule 2 (Form 1040) - Additional Taxes."""
    return {
        # Part I - Tax
        "line_1z_additions_to_tax": Decimal("0.00"),
        "line_2_amt": Decimal("0.00"),
        "line_3_total_part_i": Decimal("0.00"),

        # Part II - Other Taxes
        "line_4_self_employment_tax": Decimal("0.00"),
        "line_7_total_additional_ss_medicare": Decimal("0.00"),
        "line_8_additional_ira_tax": isaac_hill_ira_distribution["early_withdrawal_penalty"],
        "line_9_household_employment": Decimal("0.00"),
        "line_11_additional_medicare": Decimal("0.00"),
        "line_12_niit": Decimal("0.00"),
        "line_18_other_taxes": Decimal("0.00"),
        "line_21_total_other_taxes": Decimal("320.00"),  # Just the IRA penalty
    }


# =============================================================================
# FIXTURES - Form 8835 (Renewable Electricity Production Credit)
# =============================================================================

@pytest.fixture
def isaac_hill_form_8835() -> Dict[str, Any]:
    """Fixture for Form 8835 - Renewable Electricity Production Credit."""
    return {
        # Part I - Information on Qualified Facility
        "registration_number": "PA1Z12305555",
        "facility_type": "Photovoltaic Solar System",
        "facility_address": "1234 Pine Street, Boulder, CO 80302",
        "latitude": "+40.020923",
        "longitude": "-105.281386",
        "construction_began": date(2022, 3, 8),
        "placed_in_service": date(2023, 5, 6),
        "is_expansion": False,
        "qualified_facility_under_1mw": True,
        "construction_before_jan_29_2023": True,
        "meets_prevailing_wage_apprenticeship": True,
        "domestic_content_bonus": False,
        "energy_community_bonus": False,
        "nameplate_capacity_ac_kw": 845,

        # Part II - Renewable Electricity Production
        "kwh_produced_sold": 21900,
        "rate_per_kwh": Decimal("0.006"),
        "line_2_base_credit": Decimal("131.40"),  # 21900 * 0.006
        "line_3_phaseout": Decimal("0.00"),
        "line_4_credit_before_reduction": Decimal("131.40"),
        "tax_exempt_bond_reduction": False,
        "line_6_after_bond_reduction": Decimal("131.40"),
        "line_8_after_wind_reduction": Decimal("131.40"),
        # Increased credit amount (×5 for qualified facility)
        "line_9_increased_credit": Decimal("657.00"),  # 131.40 × 5 ≈ 657
        "line_10_domestic_content_bonus": Decimal("0.00"),
        "line_11_energy_community_bonus": Decimal("0.00"),
        "line_12_total": Decimal("657.00"),
        "line_13_final_credit": Decimal("655.00"),  # After rounding
        "line_15_to_form_3800": Decimal("655.00"),
    }


# =============================================================================
# FIXTURES - Form 8936 / Schedule A (Clean Vehicle Credits)
# =============================================================================

@pytest.fixture
def isaac_hill_form_8936() -> Dict[str, Any]:
    """Fixture for Form 8936 - Clean Vehicle Credits."""
    return {
        # Part I - MAGI
        "line_2_current_year_magi": Decimal("56992.00"),  # AGI
        "line_4_prior_year_magi": Decimal("47511.00"),
        "line_5_prior_year_filing_status": "S",  # Single
        "magi_limit_part_ii_iii": Decimal("150000.00"),  # QSS limit

        # Part II - Business/Investment Use of New Clean Vehicles
        "line_6_total_business_credit": Decimal("350.00"),
        "line_8_business_use_credit": Decimal("350.00"),

        # Part III - Personal Use (if any)
        "line_9_personal_credit": Decimal("0.00"),  # Only 10% business use

        # Schedule A details
        "schedule_a": {
            "vehicle_year": 2024,
            "vehicle_make": "GMC",
            "vehicle_model": "Sierra",
            "vin": "1HGBH41JXMN108186",
            "placed_in_service": date(2025, 3, 20),
            "is_new_clean_vehicle": True,
            "credit_transferred_to_dealer": False,
            "line_9_tentative_credit": Decimal("3500.00"),
            "line_10_business_investment_pct": Decimal("10.00"),
            "line_11_business_credit": Decimal("350.00"),  # 3500 × 10%
        },
    }


# =============================================================================
# FIXTURES - Form 3800 (General Business Credit)
# =============================================================================

@pytest.fixture
def isaac_hill_form_3800(
    isaac_hill_form_8835,
    isaac_hill_form_8936
) -> Dict[str, Any]:
    """Fixture for Form 3800 - General Business Credit."""
    form_8835_credit = isaac_hill_form_8835["line_15_to_form_3800"]
    form_8936_credit = isaac_hill_form_8936["line_8_business_use_credit"]

    return {
        # Question A/B
        "is_applicable_corporation": False,
        "has_transfer_election": True,  # Yes for Form 8835

        # Part I - Credits Not Allowed Against TMT
        "line_1_non_passive_credits": form_8835_credit + form_8936_credit,
        "line_3_passive_allowed": Decimal("0.00"),
        "line_6_total": form_8835_credit + form_8936_credit,  # $1,005

        # Part II - Figuring Credit Allowed
        "line_7_regular_tax": Decimal("2775.00"),  # Estimated
        "line_8_amt": Decimal("0.00"),
        "line_9_total_tax": Decimal("2775.00"),
        "line_10c_allowable_credits": Decimal("0.00"),
        "line_11_net_income_tax": Decimal("2775.00"),
        "line_12_net_regular_tax": Decimal("2775.00"),
        "line_13_25pct_excess": Decimal("0.00"),  # Tax under $25,000
        "line_14_tmt": Decimal("0.00"),
        "line_15_greater": Decimal("0.00"),
        "line_16_credit_limit": Decimal("2775.00"),
        "line_17_credit_allowed": form_8835_credit + form_8936_credit,  # $1,005

        # Part III - Current Year GBCs
        "line_1f_form_8835": form_8835_credit,  # $655
        "line_1y_form_8936": form_8936_credit,  # $350
        "line_2_total": form_8835_credit + form_8936_credit,  # $1,005

        # Section D - Credits Allowed
        "line_38_credit_allowed": form_8835_credit + form_8936_credit,  # $1,005
    }


# =============================================================================
# FIXTURES - Schedule 3 (Additional Credits and Payments)
# =============================================================================

@pytest.fixture
def isaac_hill_schedule_3(isaac_hill_form_3800) -> Dict[str, Any]:
    """Fixture for Schedule 3 (Form 1040) - Additional Credits and Payments."""
    return {
        # Part I - Nonrefundable Credits
        "line_1_foreign_tax_credit": Decimal("0.00"),
        "line_2_dependent_care_credit": Decimal("0.00"),
        "line_3_education_credits": Decimal("0.00"),
        "line_4_retirement_savings_credit": Decimal("0.00"),
        "line_5a_residential_energy": Decimal("0.00"),
        "line_5b_energy_improvement": Decimal("0.00"),
        "line_6a_general_business_credit": isaac_hill_form_3800["line_38_credit_allowed"],
        "line_6f_clean_vehicle_credit": Decimal("0.00"),  # Personal use
        "line_7_total_other_credits": isaac_hill_form_3800["line_38_credit_allowed"],
        "line_8_total_nonrefundable": isaac_hill_form_3800["line_38_credit_allowed"],

        # Part II - Other Payments and Refundable Credits
        "line_14_total_other_payments": Decimal("0.00"),
        "line_15_total_refundable": Decimal("0.00"),
    }


# =============================================================================
# FIXTURES - Complete Form 1040-NR
# =============================================================================

@pytest.fixture
def isaac_hill_form_1040nr_data(
    isaac_hill_taxpayer,
    isaac_hill_w2_data,
    isaac_hill_ira_distribution,
    isaac_hill_schedule_2,
    isaac_hill_schedule_3,
    isaac_hill_form_3800
) -> Dict[str, Any]:
    """Complete Form 1040-NR data for Isaac Hill."""

    # Income calculation
    wages = isaac_hill_w2_data["wages"]
    taxable_ira = isaac_hill_ira_distribution["taxable_amount"]
    total_eci = wages + taxable_ira  # $56,992

    # AGI
    agi = total_eci  # No adjustments

    # Deductions - OBBBA 2025 QSS standard deduction
    standard_deduction_qss = Decimal("31500.00")

    # Taxable income
    taxable_income = agi - standard_deduction_qss  # $26,992

    # Tax calculation (MFJ brackets for QSS)
    # 10% on first $23,200 = $2,320
    # 12% on remaining $3,792 = $455.04
    tax = Decimal("2775.00")  # Rounded

    # Credits
    total_credits = isaac_hill_schedule_3["line_8_total_nonrefundable"]

    # Tax after credits
    tax_after_credits = max(tax - total_credits, Decimal("0.00"))  # $1,770

    # Other taxes from Schedule 2
    other_taxes = isaac_hill_schedule_2["line_21_total_other_taxes"]  # $320

    # Total tax
    total_tax = tax_after_credits + other_taxes  # $2,090

    # Payments
    federal_withholding = isaac_hill_w2_data["federal_withholding"]
    total_payments = federal_withholding  # $8,493

    # Refund
    overpayment = total_payments - total_tax  # $6,403

    return {
        "form_type": "1040-NR",
        "tax_year": 2025,
        "filing_status": "QSS",
        "filing_status_code": 5,

        # Taxpayer info
        "taxpayer": isaac_hill_taxpayer,

        # Income (Effectively Connected)
        "line_1a_w2_wages": wages,
        "line_4a_ira_distributions": isaac_hill_ira_distribution["gross_distribution"],
        "line_4b_taxable_ira": taxable_ira,
        "line_9_total_eci": total_eci,
        "line_11a_agi": agi,

        # Tax and Credits
        "line_11b_agi": agi,
        "line_12_itemized_deductions": Decimal("0.00"),  # Using standard
        "line_14_total_deductions": standard_deduction_qss,
        "line_15_taxable_income": taxable_income,
        "line_16_tax": tax,
        "line_17_schedule_2_line_3": isaac_hill_schedule_2["line_3_total_part_i"],
        "line_18_total": tax + isaac_hill_schedule_2["line_3_total_part_i"],
        "line_19_child_tax_credit": Decimal("0.00"),
        "line_20_schedule_3_line_8": total_credits,
        "line_21_total_credits": total_credits,
        "line_22_tax_after_credits": tax_after_credits,
        "line_23b_other_taxes": other_taxes,
        "line_23d_total_other": other_taxes,
        "line_24_total_tax": total_tax,

        # Payments
        "line_25a_w2_withholding": federal_withholding,
        "line_25d_total_withholding": federal_withholding,
        "line_33_total_payments": total_payments,

        # Refund
        "line_34_overpayment": overpayment,
        "line_35a_refund": overpayment,

        # Attached schedules/forms
        "has_schedule_2": True,
        "has_schedule_3": True,
        "has_form_3800": True,
        "has_form_8835": True,
        "has_form_8936": True,

        # Binary attachments
        "binary_attachments": [
            "Substantiate VIN",
            "Transfer Election Statement"
        ],
    }


# =============================================================================
# TEST CLASSES
# =============================================================================

class TestTaxpayerInformation:
    """Tests for Isaac Hill's taxpayer information."""

    def test_taxpayer_name(self, isaac_hill_taxpayer):
        """Test taxpayer name."""
        assert isaac_hill_taxpayer["first_name"] == "Isaac"
        assert isaac_hill_taxpayer["last_name"] == "Hill"

    def test_taxpayer_ssn(self, isaac_hill_taxpayer):
        """Test SSN format."""
        assert isaac_hill_taxpayer["ssn_ats_reference"] == "123-00-5555"
        assert len(isaac_hill_taxpayer["ssn_clean"]) == 9

    def test_is_nonresident_alien(self, isaac_hill_taxpayer):
        """Test NRA status."""
        assert isaac_hill_taxpayer["is_nonresident_alien"] is True

    def test_foreign_address(self, isaac_hill_taxpayer):
        """Test Thailand address."""
        addr = isaac_hill_taxpayer["foreign_address"]
        assert addr["country"] == "Thailand"
        assert addr["province"] == "Bangkok"
        assert addr["postal_code"] == "10110"

    def test_filing_status_qss(self, isaac_hill_taxpayer):
        """Test Qualifying Surviving Spouse filing status."""
        assert isaac_hill_taxpayer["filing_status"] == "QSS"
        assert isaac_hill_taxpayer["filing_status_code"] == 5

    def test_spouse_deceased(self, isaac_hill_taxpayer):
        """Test spouse deceased date."""
        assert isaac_hill_taxpayer["spouse_deceased_date"] == date(2024, 2, 18)

    def test_federal_disaster(self, isaac_hill_taxpayer):
        """Test Federal Disaster designation."""
        assert isaac_hill_taxpayer["federal_disaster"] is True

    def test_occupation(self, isaac_hill_taxpayer):
        """Test occupation."""
        assert isaac_hill_taxpayer["occupation"] == "Driver"


class TestW2Income:
    """Tests for W-2 wage income from Pink Paradise LLC."""

    def test_employer_name(self, isaac_hill_w2_data):
        """Test employer name."""
        assert isaac_hill_w2_data["employer_name"] == "Pink Paradise LLC"

    def test_employer_ein(self, isaac_hill_w2_data):
        """Test employer EIN."""
        assert isaac_hill_w2_data["employer_ein"] == "00-5559992"

    def test_wages(self, isaac_hill_w2_data):
        """Test total wages."""
        assert isaac_hill_w2_data["wages"] == Decimal("53792.00")

    def test_federal_withholding(self, isaac_hill_w2_data):
        """Test federal tax withheld."""
        assert isaac_hill_w2_data["federal_withholding"] == Decimal("8493.00")

    def test_ss_tax(self, isaac_hill_w2_data):
        """Test Social Security tax withheld."""
        assert isaac_hill_w2_data["ss_tax"] == Decimal("3335.00")

    def test_medicare_tax(self, isaac_hill_w2_data):
        """Test Medicare tax withheld."""
        assert isaac_hill_w2_data["medicare_tax"] == Decimal("780.00")

    def test_employer_in_texas(self, isaac_hill_w2_data):
        """Test employer address is in Texas (no state income tax)."""
        assert isaac_hill_w2_data["employer_address"]["state"] == "TX"
        assert isaac_hill_w2_data["state_tax"] == Decimal("0.00")


class TestIRADistribution:
    """Tests for IRA distribution with early withdrawal penalty."""

    def test_gross_distribution(self, isaac_hill_ira_distribution):
        """Test gross IRA distribution."""
        assert isaac_hill_ira_distribution["gross_distribution"] == Decimal("6200.00")

    def test_taxable_amount(self, isaac_hill_ira_distribution):
        """Test taxable portion."""
        assert isaac_hill_ira_distribution["taxable_amount"] == Decimal("3200.00")

    def test_rollover_amount(self, isaac_hill_ira_distribution):
        """Test implied rollover amount."""
        rollover = (
            isaac_hill_ira_distribution["gross_distribution"] -
            isaac_hill_ira_distribution["taxable_amount"]
        )
        assert rollover == Decimal("3000.00")

    def test_early_withdrawal_penalty(self, isaac_hill_ira_distribution):
        """Test 10% early withdrawal penalty."""
        expected_penalty = isaac_hill_ira_distribution["taxable_amount"] * Decimal("0.10")
        assert isaac_hill_ira_distribution["early_withdrawal_penalty"] == expected_penalty


class TestForm8835RenewableElectricity:
    """Tests for Form 8835 - Renewable Electricity Production Credit."""

    def test_facility_type(self, isaac_hill_form_8835):
        """Test solar facility type."""
        assert isaac_hill_form_8835["facility_type"] == "Photovoltaic Solar System"

    def test_registration_number(self, isaac_hill_form_8835):
        """Test IRS registration number."""
        assert isaac_hill_form_8835["registration_number"] == "PA1Z12305555"

    def test_facility_location(self, isaac_hill_form_8835):
        """Test facility in Colorado."""
        assert "Boulder, CO" in isaac_hill_form_8835["facility_address"]

    def test_kwh_produced(self, isaac_hill_form_8835):
        """Test kilowatt-hours produced."""
        assert isaac_hill_form_8835["kwh_produced_sold"] == 21900

    def test_base_credit_calculation(self, isaac_hill_form_8835):
        """Test base credit calculation."""
        expected = isaac_hill_form_8835["kwh_produced_sold"] * float(isaac_hill_form_8835["rate_per_kwh"])
        assert float(isaac_hill_form_8835["line_2_base_credit"]) == pytest.approx(expected, rel=0.01)

    def test_increased_credit_multiplier(self, isaac_hill_form_8835):
        """Test 5x multiplier for qualified facility."""
        base = isaac_hill_form_8835["line_4_credit_before_reduction"]
        increased = isaac_hill_form_8835["line_9_increased_credit"]
        # Should be approximately 5x
        assert float(increased / base) == pytest.approx(5.0, rel=0.1)

    def test_final_credit(self, isaac_hill_form_8835):
        """Test final Form 8835 credit amount."""
        assert isaac_hill_form_8835["line_15_to_form_3800"] == Decimal("655.00")

    def test_nameplate_capacity(self, isaac_hill_form_8835):
        """Test nameplate capacity under 1MW."""
        assert isaac_hill_form_8835["nameplate_capacity_ac_kw"] == 845
        assert isaac_hill_form_8835["qualified_facility_under_1mw"] is True


class TestForm8936CleanVehicle:
    """Tests for Form 8936 - Clean Vehicle Credits."""

    def test_vehicle_details(self, isaac_hill_form_8936):
        """Test vehicle identification."""
        sched_a = isaac_hill_form_8936["schedule_a"]
        assert sched_a["vehicle_year"] == 2024
        assert sched_a["vehicle_make"] == "GMC"
        assert sched_a["vehicle_model"] == "Sierra"

    def test_vin(self, isaac_hill_form_8936):
        """Test VIN."""
        assert isaac_hill_form_8936["schedule_a"]["vin"] == "1HGBH41JXMN108186"

    def test_is_new_clean_vehicle(self, isaac_hill_form_8936):
        """Test new clean vehicle status."""
        assert isaac_hill_form_8936["schedule_a"]["is_new_clean_vehicle"] is True

    def test_tentative_credit(self, isaac_hill_form_8936):
        """Test tentative credit amount from scenario notes."""
        # "Taxpayer's tentative credit amount for Part II, line 9 on Schedule A (Form 8936) is $3,500"
        assert isaac_hill_form_8936["schedule_a"]["line_9_tentative_credit"] == Decimal("3500.00")

    def test_business_investment_percentage(self, isaac_hill_form_8936):
        """Test business/investment use percentage from scenario notes."""
        # "Business/investment use percentage for Part II, line 10 on Schedule A (Form 8936) is 10%"
        assert isaac_hill_form_8936["schedule_a"]["line_10_business_investment_pct"] == Decimal("10.00")

    def test_business_credit_calculation(self, isaac_hill_form_8936):
        """Test business credit calculation."""
        sched_a = isaac_hill_form_8936["schedule_a"]
        expected = sched_a["line_9_tentative_credit"] * sched_a["line_10_business_investment_pct"] / 100
        assert sched_a["line_11_business_credit"] == expected

    def test_total_business_credit(self, isaac_hill_form_8936):
        """Test Form 8936 Part II total."""
        assert isaac_hill_form_8936["line_8_business_use_credit"] == Decimal("350.00")


class TestForm3800GeneralBusinessCredit:
    """Tests for Form 3800 - General Business Credit."""

    def test_form_8835_credit_included(self, isaac_hill_form_3800):
        """Test Form 8835 credit flows to Form 3800."""
        assert isaac_hill_form_3800["line_1f_form_8835"] == Decimal("655.00")

    def test_form_8936_credit_included(self, isaac_hill_form_3800):
        """Test Form 8936 credit flows to Form 3800."""
        assert isaac_hill_form_3800["line_1y_form_8936"] == Decimal("350.00")

    def test_total_gbc(self, isaac_hill_form_3800):
        """Test total general business credit."""
        expected = (
            isaac_hill_form_3800["line_1f_form_8835"] +
            isaac_hill_form_3800["line_1y_form_8936"]
        )
        assert isaac_hill_form_3800["line_2_total"] == expected
        assert expected == Decimal("1005.00")

    def test_credit_allowed(self, isaac_hill_form_3800):
        """Test credit allowed after limitations."""
        assert isaac_hill_form_3800["line_38_credit_allowed"] == Decimal("1005.00")

    def test_credit_within_tax_liability(self, isaac_hill_form_3800):
        """Test credit doesn't exceed tax liability."""
        assert isaac_hill_form_3800["line_38_credit_allowed"] <= isaac_hill_form_3800["line_16_credit_limit"]


class TestSchedule2AdditionalTaxes:
    """Tests for Schedule 2 (Form 1040) - Additional Taxes."""

    def test_ira_penalty(self, isaac_hill_schedule_2):
        """Test early IRA distribution penalty."""
        assert isaac_hill_schedule_2["line_8_additional_ira_tax"] == Decimal("320.00")

    def test_total_other_taxes(self, isaac_hill_schedule_2):
        """Test total other taxes."""
        assert isaac_hill_schedule_2["line_21_total_other_taxes"] == Decimal("320.00")

    def test_no_self_employment_tax(self, isaac_hill_schedule_2):
        """Test no self-employment tax (W-2 wages only)."""
        assert isaac_hill_schedule_2["line_4_self_employment_tax"] == Decimal("0.00")


class TestSchedule3AdditionalCredits:
    """Tests for Schedule 3 (Form 1040) - Additional Credits and Payments."""

    def test_gbc_on_schedule_3(self, isaac_hill_schedule_3):
        """Test General Business Credit reported on Schedule 3."""
        assert isaac_hill_schedule_3["line_6a_general_business_credit"] == Decimal("1005.00")

    def test_total_nonrefundable_credits(self, isaac_hill_schedule_3):
        """Test total nonrefundable credits."""
        assert isaac_hill_schedule_3["line_8_total_nonrefundable"] == Decimal("1005.00")


class TestForm1040NRTaxCalculation:
    """Tests for Form 1040-NR tax calculations."""

    def test_form_type(self, isaac_hill_form_1040nr_data):
        """Test form type is 1040-NR."""
        assert isaac_hill_form_1040nr_data["form_type"] == "1040-NR"

    def test_filing_status_qss(self, isaac_hill_form_1040nr_data):
        """Test filing status is Qualifying Surviving Spouse."""
        assert isaac_hill_form_1040nr_data["filing_status"] == "QSS"

    def test_total_wages(self, isaac_hill_form_1040nr_data):
        """Test W-2 wages on line 1a."""
        assert isaac_hill_form_1040nr_data["line_1a_w2_wages"] == Decimal("53792.00")

    def test_total_eci(self, isaac_hill_form_1040nr_data):
        """Test total effectively connected income."""
        expected = Decimal("53792.00") + Decimal("3200.00")
        assert isaac_hill_form_1040nr_data["line_9_total_eci"] == expected

    def test_agi(self, isaac_hill_form_1040nr_data):
        """Test AGI calculation."""
        assert isaac_hill_form_1040nr_data["line_11a_agi"] == Decimal("56992.00")

    def test_standard_deduction_qss(self, isaac_hill_form_1040nr_data):
        """Test QSS standard deduction used."""
        assert isaac_hill_form_1040nr_data["line_14_total_deductions"] == Decimal("30000.00")

    def test_taxable_income(self, isaac_hill_form_1040nr_data):
        """Test taxable income calculation."""
        expected = Decimal("56992.00") - Decimal("30000.00")
        assert isaac_hill_form_1040nr_data["line_15_taxable_income"] == expected

    def test_total_credits(self, isaac_hill_form_1040nr_data):
        """Test total credits from Schedule 3."""
        assert isaac_hill_form_1040nr_data["line_21_total_credits"] == Decimal("1005.00")

    def test_total_tax(self, isaac_hill_form_1040nr_data):
        """Test total tax calculation."""
        # Tax after credits + Other taxes (IRA penalty)
        assert isaac_hill_form_1040nr_data["line_24_total_tax"] == Decimal("2090.00")

    def test_total_payments(self, isaac_hill_form_1040nr_data):
        """Test total payments (withholding)."""
        assert isaac_hill_form_1040nr_data["line_33_total_payments"] == Decimal("8493.00")

    def test_has_refund(self, isaac_hill_form_1040nr_data):
        """Test overpayment results in refund."""
        assert isaac_hill_form_1040nr_data["line_34_overpayment"] > 0

    def test_refund_amount(self, isaac_hill_form_1040nr_data):
        """Test refund calculation."""
        expected = Decimal("8493.00") - Decimal("2090.00")
        assert isaac_hill_form_1040nr_data["line_35a_refund"] == expected


class TestBinaryAttachments:
    """Tests for required binary attachments."""

    def test_has_vin_substantiation(self, isaac_hill_form_1040nr_data):
        """Test VIN substantiation attachment required."""
        assert "Substantiate VIN" in isaac_hill_form_1040nr_data["binary_attachments"]

    def test_has_transfer_election_statement(self, isaac_hill_form_1040nr_data):
        """Test Transfer Election Statement attachment required."""
        assert "Transfer Election Statement" in isaac_hill_form_1040nr_data["binary_attachments"]


class TestScenarioNR4XMLSerialization:
    """Tests for XML serialization of NR-4 scenario."""

    def test_taxpayer_info_creation(self, isaac_hill_taxpayer):
        """Test TaxpayerInfo can be created."""
        taxpayer_info = TaxpayerInfo(
            primary_ssn=isaac_hill_taxpayer["ssn_clean"],
            primary_first_name=isaac_hill_taxpayer["first_name"],
            primary_last_name=isaac_hill_taxpayer["last_name"],
            primary_date_of_birth=isaac_hill_taxpayer["date_of_birth"]
        )
        assert taxpayer_info.primary_ssn == isaac_hill_taxpayer["ssn_clean"]
        assert taxpayer_info.primary_first_name == "Isaac"

    def test_submission_id_generation(self, isaac_hill_taxpayer):
        """Test submission ID can be generated."""
        submission_id = SubmissionId.generate(
            efin="123456",
            sequence=1
        )
        assert len(submission_id.submission_id) == 20


class TestScenarioNR4BusinessRules:
    """Tests for business rules validation."""

    def test_nra_uses_1040nr(self, isaac_hill_form_1040nr_data):
        """Test nonresident alien files Form 1040-NR."""
        assert isaac_hill_form_1040nr_data["form_type"] == "1040-NR"
        assert isaac_hill_form_1040nr_data["taxpayer"]["is_nonresident_alien"] is True

    def test_qss_can_use_standard_deduction(self, isaac_hill_form_1040nr_data):
        """Test QSS filer can use standard deduction."""
        assert isaac_hill_form_1040nr_data["filing_status"] == "QSS"
        assert isaac_hill_form_1040nr_data["line_14_total_deductions"] == Decimal("30000.00")

    def test_magi_within_clean_vehicle_limit(self, isaac_hill_form_8936, isaac_hill_taxpayer):
        """Test MAGI is within clean vehicle credit limit."""
        magi = isaac_hill_form_8936["line_2_current_year_magi"]
        limit = isaac_hill_form_8936["magi_limit_part_ii_iii"]
        assert magi <= limit

    def test_gbc_limited_by_tax(self, isaac_hill_form_3800):
        """Test GBC cannot exceed tax liability."""
        gbc = isaac_hill_form_3800["line_38_credit_allowed"]
        tax_limit = isaac_hill_form_3800["line_16_credit_limit"]
        assert gbc <= tax_limit


class TestScenarioNR4Integration:
    """Integration tests for complete data flow."""

    def test_complete_form_1040nr_structure(self, isaac_hill_form_1040nr_data):
        """Test complete Form 1040-NR has all required sections."""
        required_keys = [
            "form_type", "tax_year", "filing_status",
            "line_1a_w2_wages", "line_11a_agi", "line_15_taxable_income",
            "line_16_tax", "line_24_total_tax", "line_33_total_payments"
        ]
        for key in required_keys:
            assert key in isaac_hill_form_1040nr_data

    def test_w2_flows_to_1040nr(self, isaac_hill_w2_data, isaac_hill_form_1040nr_data):
        """Test W-2 wages flow correctly to Form 1040-NR."""
        assert isaac_hill_form_1040nr_data["line_1a_w2_wages"] == isaac_hill_w2_data["wages"]

    def test_form_8835_flows_to_3800(self, isaac_hill_form_8835, isaac_hill_form_3800):
        """Test Form 8835 credit flows to Form 3800."""
        assert isaac_hill_form_3800["line_1f_form_8835"] == isaac_hill_form_8835["line_15_to_form_3800"]

    def test_form_8936_flows_to_3800(self, isaac_hill_form_8936, isaac_hill_form_3800):
        """Test Form 8936 credit flows to Form 3800."""
        assert isaac_hill_form_3800["line_1y_form_8936"] == isaac_hill_form_8936["line_8_business_use_credit"]

    def test_form_3800_flows_to_schedule_3(self, isaac_hill_form_3800, isaac_hill_schedule_3):
        """Test Form 3800 credit flows to Schedule 3."""
        assert isaac_hill_schedule_3["line_6a_general_business_credit"] == isaac_hill_form_3800["line_38_credit_allowed"]

    def test_schedule_2_flows_to_1040nr(self, isaac_hill_schedule_2, isaac_hill_form_1040nr_data):
        """Test Schedule 2 other taxes flow to Form 1040-NR."""
        assert isaac_hill_form_1040nr_data["line_23b_other_taxes"] == isaac_hill_schedule_2["line_21_total_other_taxes"]

    def test_schedule_3_flows_to_1040nr(self, isaac_hill_schedule_3, isaac_hill_form_1040nr_data):
        """Test Schedule 3 credits flow to Form 1040-NR."""
        assert isaac_hill_form_1040nr_data["line_20_schedule_3_line_8"] == isaac_hill_schedule_3["line_8_total_nonrefundable"]

    def test_withholding_flows_to_payments(self, isaac_hill_w2_data, isaac_hill_form_1040nr_data):
        """Test W-2 withholding flows to payments."""
        assert isaac_hill_form_1040nr_data["line_25a_w2_withholding"] == isaac_hill_w2_data["federal_withholding"]

    def test_line_math_consistency(self, isaac_hill_form_1040nr_data):
        """Test mathematical consistency throughout return."""
        # Total ECI = Wages + Taxable IRA
        expected_eci = (
            isaac_hill_form_1040nr_data["line_1a_w2_wages"] +
            isaac_hill_form_1040nr_data["line_4b_taxable_ira"]
        )
        assert isaac_hill_form_1040nr_data["line_9_total_eci"] == expected_eci

        # Taxable income = AGI - Deductions
        expected_taxable = (
            isaac_hill_form_1040nr_data["line_11a_agi"] -
            isaac_hill_form_1040nr_data["line_14_total_deductions"]
        )
        assert isaac_hill_form_1040nr_data["line_15_taxable_income"] == expected_taxable

        # Tax after credits = Tax - Credits (min 0)
        expected_after_credits = max(
            isaac_hill_form_1040nr_data["line_16_tax"] -
            isaac_hill_form_1040nr_data["line_21_total_credits"],
            Decimal("0.00")
        )
        assert isaac_hill_form_1040nr_data["line_22_tax_after_credits"] == expected_after_credits

        # Total tax = Tax after credits + Other taxes
        expected_total_tax = (
            isaac_hill_form_1040nr_data["line_22_tax_after_credits"] +
            isaac_hill_form_1040nr_data["line_23d_total_other"]
        )
        assert isaac_hill_form_1040nr_data["line_24_total_tax"] == expected_total_tax

        # Refund = Payments - Total tax
        expected_refund = (
            isaac_hill_form_1040nr_data["line_33_total_payments"] -
            isaac_hill_form_1040nr_data["line_24_total_tax"]
        )
        assert isaac_hill_form_1040nr_data["line_35a_refund"] == expected_refund
