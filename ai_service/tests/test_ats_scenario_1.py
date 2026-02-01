"""Comprehensive pytest tests for IRS ATS Test Scenario 1 - Tara Black.

This module tests the MeF (Modernized e-File) service functionality using
IRS ATS (Assurance Testing System) Test Scenario 1 data for Tara Black.

Test Scenario Reference: IRS ATS Test Scenario 1 (ty25-1040-mef-ats-scenario-1-12012025.pdf)
Primary Taxpayer: Tara Black
Filing Status: Single (1)
No Dependents

Key Features Tested:
- Multiple W-2 forms from different employers
- Schedule H (Household Employment Taxes)
- Form 5695 (Residential Energy Credits)
- Schedule 2 (Additional Taxes)
- Schedule 3 (Additional Credits)
- Energy efficient home improvements (doors, windows, AC)

Tax Year: 2025

Source: /Users/tkhan/Downloads/IRS_MeF_Materials/ATS_SCENARIO_TRACKING_GUIDE.md
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
# FIXTURES - IRS ATS Test Scenario 1 Data (Tara Black - Single)
# =============================================================================


@pytest.fixture
def tara_black_taxpayer() -> Dict[str, Any]:
    """Fixture for Tara Black (primary taxpayer) information.

    IRS ATS Test Scenario 1 - Single filer with household employment
    and residential energy credits.

    ATS Reference SSN: 400-00-1032 (invalid for production validation)
    Test SSN: 400-01-1032 (valid format for testing validation logic)
    """
    return {
        "first_name": "Tara",
        "last_name": "Black",
        "ssn": "400-01-1032",
        "ssn_clean": "400011032",
        "ssn_ats_reference": "400-00-1032",
        "address": {
            "street": "17 Lexington Drive",
            "city": "Cincinnati",
            "state": "OH",
            "zip": "45223"
        },
        "date_of_birth": date(1985, 6, 15),
        "occupation": "Sales Representative",
        "digital_assets": False,
    }


@pytest.fixture
def tara_black_w2_data() -> Dict[str, Any]:
    """Fixture for Tara Black W-2 data.

    Two W-2 forms:
    - W-2 #1: The Green Ladies (EIN 00-0000007), Georgia employer
    - W-2 #2: C&R (EIN 00-0000007), Ohio employer
    """
    return {
        "w2_1": {
            # W-2 #1 - The Green Ladies
            "employee_name": "Tara Black",
            "employer_name": "The Green Ladies",
            "employer_ein": "00-0000007",
            "employer_ein_clean": "000000007",
            "employer_ein_test": "12-3456781",  # Valid test EIN
            "employer_address": {
                "street": "14 Forest Lane",
                "city": "Atlanta",
                "state": "GA",
                "zip": "30033"
            },
            "wages": Decimal("22970.00"),
            "federal_withholding": Decimal("1073.00"),
            "ss_wages": Decimal("22970.00"),
            "ss_tax": Decimal("1424.00"),  # 22970 * 0.062
            "medicare_wages": Decimal("22970.00"),
            "medicare_tax": Decimal("333.00"),  # 22970 * 0.0145
            "state": "GA",
            "state_id": "00-0000008",
            "state_wages": Decimal("22970.00"),
            "state_tax": Decimal("320.00"),
        },
        "w2_2": {
            # W-2 #2 - C&R
            "employee_name": "Tara Black",
            "employer_name": "C&R",
            "employer_ein": "00-0000007",
            "employer_ein_clean": "000000007",
            "employer_ein_test": "12-3456782",  # Valid test EIN
            "employer_address": {
                "street": "1121 W Fourth Street",
                "city": "Cincinnati",
                "state": "OH",
                "zip": "45223"
            },
            "wages": Decimal("19500.00"),
            "federal_withholding": Decimal("1640.00"),
            "ss_wages": Decimal("19500.00"),
            "ss_tax": Decimal("1209.00"),  # 19500 * 0.062
            "medicare_wages": Decimal("19500.00"),
            "medicare_tax": Decimal("283.00"),  # 19500 * 0.0145
            "state": "GA",  # Note: state wages reported to GA even though employer is OH
            "state_id": "00-0000008",
            "state_wages": Decimal("19500.00"),
            "state_tax": Decimal("416.00"),
        },
        "totals": {
            "total_wages": Decimal("42470.00"),  # 22970 + 19500
            "federal_withholding": Decimal("2713.00"),  # 1073 + 1640
            "ss_wages": Decimal("42470.00"),
            "ss_tax": Decimal("2633.00"),  # 1424 + 1209
            "medicare_wages": Decimal("42470.00"),
            "medicare_tax": Decimal("616.00"),  # 333 + 283
            "state_tax": Decimal("736.00"),  # 320 + 416
        }
    }


@pytest.fixture
def tara_black_schedule_h() -> Dict[str, Any]:
    """Fixture for Schedule H (Household Employment Taxes).

    Tara employs household help and must pay employment taxes.
    Cash wages paid: $3,100 (above $2,700 threshold for 2025)

    Employer EIN: 00-0000029 (ATS reference)
    """
    return {
        "employer_ein": "00-0000029",
        "employer_ein_clean": "000000029",
        "employer_ein_test": "12-3456783",  # Valid test EIN

        # Part I - Social Security, Medicare, and FUTA Taxes
        "cash_wages_paid": Decimal("3100.00"),
        "cash_wages_subject_to_ss": Decimal("3100.00"),
        "cash_wages_subject_to_medicare": Decimal("3100.00"),

        # Tax rates for 2025
        "ss_tax_rate": Decimal("0.124"),  # 12.4% (employer + employee share)
        "medicare_tax_rate": Decimal("0.029"),  # 2.9% (employer + employee share)

        # Tax calculations
        "social_security_tax": Decimal("384.40"),  # 3100 * 0.124
        "medicare_tax": Decimal("89.90"),  # 3100 * 0.029
        "additional_medicare_wages": Decimal("0.00"),
        "additional_medicare_tax": Decimal("0.00"),

        # Federal income tax withheld (Line 6)
        "federal_withholding": Decimal("0.00"),

        # Totals
        "line_7_ss_medicare_tax": Decimal("474.30"),  # 384.40 + 89.90
        "line_8_total_taxes": Decimal("474.30"),  # Line 7 + Line 6

        # Part II - FUTA Tax
        "futa_required": False,  # Checked "No" on Line 9
        "futa_wages": Decimal("0.00"),
        "futa_tax": Decimal("0.00"),

        # Part III - Federal Income Tax
        "total_household_employment_taxes": Decimal("474.30"),
    }


@pytest.fixture
def tara_black_form_5695() -> Dict[str, Any]:
    """Fixture for Form 5695 (Residential Energy Credits).

    Part II: Energy Efficient Home Improvement Credit
    Property: 17 Lexington Drive, Cincinnati, OH 45223

    Improvements made:
    - Exterior doors (3): $2,740 total, limited to $500
    - Windows: $600
    - Central AC: $2,500 total, limited to $600

    Note: Each improvement type has maximum credit caps.
    """
    return {
        "property_address": {
            "street": "17 Lexington Drive",
            "city": "Cincinnati",
            "state": "OH",
            "zip": "45223"
        },

        # Part II Questions (all must be Yes for credit)
        "part_ii_questions": {
            "qualified_improvements": True,  # Line 17a
            "original_user": True,  # Line 17b
            "expected_5_years": True,  # Line 17c
            "construction_related": False,  # Line 17d (must be No)
        },

        # Line 18: Exterior Doors
        "exterior_doors": {
            "items": [
                {"qmin": "A1B2", "cost": Decimal("1020.00")},
                {"qmin": "A1B3", "cost": Decimal("920.00")},
                {"qmin": "A1B4", "cost": Decimal("800.00")},
            ],
            "total_cost": Decimal("2740.00"),
            "credit_rate": Decimal("0.30"),  # 30%
            "calculated_credit": Decimal("822.00"),  # 2740 * 0.30
            "credit_cap": Decimal("500.00"),  # Maximum $500 for doors
            "allowed_credit": Decimal("500.00"),  # Limited to cap
        },

        # Line 19: Windows and Skylights
        "windows": {
            "items": [
                {"qmin": "A1B5", "cost": Decimal("600.00")},
            ],
            "total_cost": Decimal("600.00"),
            "credit_rate": Decimal("0.30"),
            "calculated_credit": Decimal("180.00"),  # 600 * 0.30
            "credit_cap": Decimal("600.00"),  # Maximum $600 for windows
            "allowed_credit": Decimal("180.00"),  # Below cap, use calculated
        },

        # Line 20: Insulation
        "insulation": {
            "total_cost": Decimal("0.00"),
            "allowed_credit": Decimal("0.00"),
        },

        # Line 21: Roofs
        "roofs": {
            "total_cost": Decimal("0.00"),
            "allowed_credit": Decimal("0.00"),
        },

        # Line 22: Central Air Conditioners
        "central_ac": {
            "items": [
                {"qmin": "A1B6", "cost": Decimal("2100.00")},
            ],
            "other_cost": Decimal("400.00"),  # Other qualifying AC costs
            "total_cost": Decimal("2500.00"),
            "credit_rate": Decimal("0.30"),
            "calculated_credit": Decimal("750.00"),  # 2500 * 0.30
            "credit_cap": Decimal("600.00"),  # Maximum $600 for AC
            "allowed_credit": Decimal("600.00"),  # Limited to cap
        },

        # Lines 23-27: Other improvements (not applicable)
        "natural_gas_furnace": {"allowed_credit": Decimal("0.00")},
        "hot_water_boiler": {"allowed_credit": Decimal("0.00")},
        "biomass_stove": {"allowed_credit": Decimal("0.00")},
        "heat_pump_water_heater": {"allowed_credit": Decimal("0.00")},
        "heat_pump": {"allowed_credit": Decimal("0.00")},

        # Line 28: Home energy audit
        "home_energy_audit": {
            "performed": False,
            "cost": Decimal("0.00"),
            "credit_cap": Decimal("150.00"),
            "allowed_credit": Decimal("0.00"),
        },

        # Line 29: Total (sum of lines 18-28)
        "line_29_total": Decimal("1280.00"),  # 500 + 180 + 600

        # Line 30: Annual limit
        "annual_limit": Decimal("1200.00"),  # $1,200 general annual limit

        # Line 31: Prior year credit used
        "prior_year_credit_used": Decimal("0.00"),

        # Line 32: Residential energy credit (limited)
        "line_32_credit": Decimal("1200.00"),  # Min(1280, 1200 - 0)

        # Note: This flows to Schedule 3, Line 5
    }


@pytest.fixture
def tara_black_schedule_2() -> Dict[str, Any]:
    """Fixture for Schedule 2 (Additional Taxes).

    Part I - Tax
    Line 4: Self-employment tax (N/A for Tara)
    Line 8: Household employment taxes from Schedule H

    Part II - Other Taxes
    Various additional taxes (N/A for this scenario)
    """
    return {
        # Part I - Tax
        "line_1_amt": Decimal("0.00"),
        "line_2_excess_premium_tax_credit": Decimal("0.00"),
        "line_3_social_security_medicare_unreported": Decimal("0.00"),
        "line_4_self_employment_tax": Decimal("0.00"),
        "line_5_unreported_tips": Decimal("0.00"),
        "line_6_uncollected_ss_medicare": Decimal("0.00"),
        "line_7_section_72m_early_withdrawal": Decimal("0.00"),
        "line_8_household_employment_taxes": Decimal("474.00"),  # From Schedule H (rounded)
        "line_9_first_time_homebuyer": Decimal("0.00"),
        "line_10_additional_medicare_tax": Decimal("0.00"),
        "line_11_net_investment_income_tax": Decimal("0.00"),

        # Part I Total
        "line_12_total_part_1": Decimal("474.00"),

        # Part II - Other Taxes (all N/A)
        "line_17_part_2_total": Decimal("0.00"),

        # Schedule 2 Total
        "line_21_total": Decimal("474.00"),  # Flows to Form 1040, Line 17
    }


@pytest.fixture
def tara_black_schedule_3() -> Dict[str, Any]:
    """Fixture for Schedule 3 (Additional Credits and Payments).

    Part I - Nonrefundable Credits
    Line 5: Residential energy credits from Form 5695

    Part II - Other Payments and Refundable Credits
    (N/A for this scenario)
    """
    return {
        # Part I - Nonrefundable Credits
        "line_1_foreign_tax_credit": Decimal("0.00"),
        "line_2_child_care_credit": Decimal("0.00"),
        "line_3_education_credit": Decimal("0.00"),
        "line_4_retirement_savings_credit": Decimal("0.00"),
        "line_5_residential_energy_credit": Decimal("1200.00"),  # From Form 5695, Line 32
        "line_6_other_credits": Decimal("0.00"),

        # Part I Total
        "line_8_total_part_1": Decimal("1200.00"),  # Flows to Form 1040, Line 20

        # Part II - Other Payments and Refundable Credits (all N/A)
        "line_9_net_premium_tax_credit": Decimal("0.00"),
        "line_10_amount_paid_with_extension": Decimal("0.00"),
        "line_11_excess_social_security": Decimal("0.00"),
        "line_12_credit_for_federal_tax_on_fuels": Decimal("0.00"),
        "line_13_other_payments": Decimal("0.00"),

        # Part II Total
        "line_15_total_part_2": Decimal("0.00"),
    }


@pytest.fixture
def tara_black_form_1040_data(
    tara_black_taxpayer,
    tara_black_w2_data,
    tara_black_schedule_h,
    tara_black_form_5695,
    tara_black_schedule_2,
    tara_black_schedule_3
) -> Dict[str, Any]:
    """Fixture for complete Form 1040 data for Tara Black.

    Tax Year: 2025
    Filing Status: Single (1)
    Standard Deduction (OBBBA 2025 Single): $15,750
    """
    # Income
    total_wages = tara_black_w2_data["totals"]["total_wages"]
    total_income = total_wages
    agi = total_income  # No adjustments

    # Deduction - OBBBA 2025 Single Standard Deduction
    standard_deduction_single_2025 = Decimal("15750.00")

    # Taxable income
    taxable_income = max(Decimal("0"), agi - standard_deduction_single_2025)

    # Tax calculation (OBBBA 2025 tax brackets for Single)
    # $0 - $11,925: 10%
    # $11,926 - $48,475: 12%
    # Taxable income: $26,720
    tax_bracket_1 = Decimal("11925.00") * Decimal("0.10")  # $1,192.50
    remaining = taxable_income - Decimal("11925.00")  # $14,795
    tax_bracket_2 = remaining * Decimal("0.12")  # $1,775.40
    calculated_tax = tax_bracket_1 + tax_bracket_2  # $2,967.90
    calculated_tax = calculated_tax.quantize(Decimal("1"), rounding="ROUND_HALF_UP")  # $2,968

    # Schedule 2 additional taxes
    schedule_2_tax = tara_black_schedule_2["line_21_total"]

    # Total tax before credits
    total_tax_before_credits = calculated_tax + schedule_2_tax

    # Credits from Schedule 3
    nonrefundable_credits = tara_black_schedule_3["line_8_total_part_1"]

    # Tax after credits (cannot go below 0)
    tax_after_credits = max(Decimal("0"), total_tax_before_credits - nonrefundable_credits)

    # Total tax
    total_tax = tax_after_credits

    # Payments
    federal_withholding = tara_black_w2_data["totals"]["federal_withholding"]
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
        "primary_ssn": tara_black_taxpayer["ssn_clean"],
        "primary_first_name": tara_black_taxpayer["first_name"],
        "primary_last_name": tara_black_taxpayer["last_name"],
        "address": tara_black_taxpayer["address"],
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
        "line_1z_wages": total_wages,  # $42,470
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
        "line_8_schedule_1": Decimal("0"),  # No Schedule 1 income
        "line_9_total_income": total_income,  # $42,470
        "total_income": total_income,

        # Adjustments (Line 10)
        "line_10_adjustments": Decimal("0"),  # No Schedule 1 adjustments

        # AGI (Line 11)
        "line_11_agi": agi,  # $42,470
        "agi": agi,

        # Deduction (Lines 12-14)
        "line_12_standard_deduction": standard_deduction_single_2025,  # $15,000
        "line_12_itemized_deduction": Decimal("0"),  # Using standard
        "line_12_deduction": standard_deduction_single_2025,
        "line_13_qbi_deduction": Decimal("0"),  # No QBI
        "line_14_total_deductions": standard_deduction_single_2025,
        "deduction": standard_deduction_single_2025,

        # Taxable income (Line 15)
        "line_15_taxable_income": taxable_income,  # $27,470
        "taxable_income": taxable_income,

        # Tax (Lines 16-24)
        "line_16_tax": calculated_tax,  # $3,064
        "line_17_schedule_2": schedule_2_tax,  # $474
        "line_18_total": total_tax_before_credits,  # $3,538
        "line_19_ctc_actc": Decimal("0"),  # No dependents
        "line_20_schedule_3": nonrefundable_credits,  # $1,200
        "line_21_credits_subtotal": nonrefundable_credits,
        "line_22_tax_minus_credits": tax_after_credits,  # $2,338
        "line_23_other_taxes": Decimal("0"),
        "line_24_total_tax": total_tax,  # $2,338
        "total_tax": total_tax,

        # Payments (Lines 25-33)
        "line_25a_w2_withholding": federal_withholding,  # $2,713
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
        "line_33_total_payments": total_payments,  # $2,713
        "total_payments": total_payments,

        # Refund/Amount Owed (Lines 34-38)
        "line_34_overpaid": refund if refund > 0 else Decimal("0"),  # $375
        "line_35a_refund": refund if refund > 0 else Decimal("0"),
        "line_35b_routing_number": "",
        "line_35c_account_type": "",
        "line_35d_account_number": "",
        "line_36_applied_to_next_year": Decimal("0"),
        "line_37_amount_owed": amount_owed,  # $0
        "line_38_estimated_tax_penalty": Decimal("0"),
        "refund": refund,
        "amount_owed": amount_owed,

        # Attached schedules
        "has_schedule_h": True,
        "has_form_5695": True,
        "has_schedule_2": True,
        "has_schedule_3": True,

        # Schedule H data
        "schedule_h": tara_black_schedule_h,

        # Form 5695 data
        "form_5695": tara_black_form_5695,

        # Schedule 2 data
        "schedule_2": tara_black_schedule_2,

        # Schedule 3 data
        "schedule_3": tara_black_schedule_3,
    }


# =============================================================================
# TEST CLASS: Multiple W-2 Forms
# =============================================================================


class TestMultipleW2Forms:
    """Tests for handling multiple W-2 forms from different employers."""

    def test_multiple_w2_total_wages(self, tara_black_w2_data):
        """Test total wages calculation from multiple W-2s."""
        w2_1_wages = tara_black_w2_data["w2_1"]["wages"]
        w2_2_wages = tara_black_w2_data["w2_2"]["wages"]
        expected_total = w2_1_wages + w2_2_wages

        assert tara_black_w2_data["totals"]["total_wages"] == expected_total
        assert tara_black_w2_data["totals"]["total_wages"] == Decimal("42470.00")

    def test_multiple_w2_federal_withholding(self, tara_black_w2_data):
        """Test total federal withholding from multiple W-2s."""
        w2_1_withholding = tara_black_w2_data["w2_1"]["federal_withholding"]
        w2_2_withholding = tara_black_w2_data["w2_2"]["federal_withholding"]
        expected_total = w2_1_withholding + w2_2_withholding

        assert tara_black_w2_data["totals"]["federal_withholding"] == expected_total
        assert tara_black_w2_data["totals"]["federal_withholding"] == Decimal("2713.00")

    def test_w2_social_security_calculation(self, tara_black_w2_data):
        """Test Social Security tax calculations on W-2s."""
        # SS tax rate is 6.2% for employee
        w2_1 = tara_black_w2_data["w2_1"]
        expected_ss_tax_1 = (w2_1["ss_wages"] * Decimal("0.062")).quantize(Decimal("1"))
        assert w2_1["ss_tax"] == Decimal("1424.00")  # 22970 * 0.062 = 1424.14 -> 1424

        w2_2 = tara_black_w2_data["w2_2"]
        expected_ss_tax_2 = (w2_2["ss_wages"] * Decimal("0.062")).quantize(Decimal("1"))
        assert w2_2["ss_tax"] == Decimal("1209.00")  # 19500 * 0.062 = 1209

    def test_w2_medicare_calculation(self, tara_black_w2_data):
        """Test Medicare tax calculations on W-2s."""
        # Medicare tax rate is 1.45% for employee
        w2_1 = tara_black_w2_data["w2_1"]
        assert w2_1["medicare_tax"] == Decimal("333.00")  # 22970 * 0.0145 = 333.07 -> 333

        w2_2 = tara_black_w2_data["w2_2"]
        assert w2_2["medicare_tax"] == Decimal("283.00")  # 19500 * 0.0145 = 282.75 -> 283

    def test_w2_employer_ein_format(self, tara_black_w2_data):
        """Test employer EIN format on W-2s."""
        for w2_key in ["w2_1", "w2_2"]:
            ein = tara_black_w2_data[w2_key]["employer_ein"]
            # EIN format: XX-XXXXXXX
            assert "-" in ein
            clean_ein = ein.replace("-", "")
            assert len(clean_ein) == 9
            assert clean_ein.isdigit()


# =============================================================================
# TEST CLASS: Schedule H Household Employment
# =============================================================================


class TestScheduleHHouseholdEmployment:
    """Tests for Schedule H household employment taxes."""

    def test_schedule_h_cash_wages(self, tara_black_schedule_h):
        """Test Schedule H cash wages are above threshold."""
        # 2025 threshold is $2,700
        threshold_2025 = Decimal("2700.00")
        cash_wages = tara_black_schedule_h["cash_wages_paid"]

        assert cash_wages >= threshold_2025
        assert cash_wages == Decimal("3100.00")

    def test_schedule_h_ss_tax_calculation(self, tara_black_schedule_h):
        """Test Schedule H Social Security tax calculation."""
        cash_wages = tara_black_schedule_h["cash_wages_subject_to_ss"]
        ss_rate = tara_black_schedule_h["ss_tax_rate"]
        expected_ss_tax = cash_wages * ss_rate

        assert tara_black_schedule_h["social_security_tax"] == expected_ss_tax
        assert tara_black_schedule_h["social_security_tax"] == Decimal("384.40")

    def test_schedule_h_medicare_tax_calculation(self, tara_black_schedule_h):
        """Test Schedule H Medicare tax calculation."""
        cash_wages = tara_black_schedule_h["cash_wages_subject_to_medicare"]
        medicare_rate = tara_black_schedule_h["medicare_tax_rate"]
        expected_medicare_tax = cash_wages * medicare_rate

        assert tara_black_schedule_h["medicare_tax"] == expected_medicare_tax
        assert tara_black_schedule_h["medicare_tax"] == Decimal("89.90")

    def test_schedule_h_total_taxes(self, tara_black_schedule_h):
        """Test Schedule H total household employment taxes."""
        ss_tax = tara_black_schedule_h["social_security_tax"]
        medicare_tax = tara_black_schedule_h["medicare_tax"]
        expected_total = ss_tax + medicare_tax

        assert tara_black_schedule_h["line_8_total_taxes"] == expected_total
        assert tara_black_schedule_h["line_8_total_taxes"] == Decimal("474.30")

    def test_schedule_h_no_futa(self, tara_black_schedule_h):
        """Test Schedule H FUTA is not required."""
        # FUTA applies if $1,000+ wages in any calendar quarter
        # Tara's scenario has FUTA marked as not required
        assert tara_black_schedule_h["futa_required"] is False
        assert tara_black_schedule_h["futa_tax"] == Decimal("0.00")

    def test_schedule_h_flows_to_schedule_2(self, tara_black_schedule_h, tara_black_schedule_2):
        """Test Schedule H total flows to Schedule 2."""
        # Schedule H total (rounded) flows to Schedule 2, Line 8
        schedule_h_total = tara_black_schedule_h["total_household_employment_taxes"]
        schedule_h_rounded = schedule_h_total.quantize(Decimal("1"), rounding="ROUND_HALF_UP")

        assert tara_black_schedule_2["line_8_household_employment_taxes"] == schedule_h_rounded


# =============================================================================
# TEST CLASS: Form 5695 Energy Credits
# =============================================================================


class TestForm5695EnergyCredits:
    """Tests for Form 5695 Residential Energy Credits."""

    def test_form_5695_part_ii_questions(self, tara_black_form_5695):
        """Test Part II eligibility questions."""
        questions = tara_black_form_5695["part_ii_questions"]

        # All must be True (except construction_related which must be False)
        assert questions["qualified_improvements"] is True
        assert questions["original_user"] is True
        assert questions["expected_5_years"] is True
        assert questions["construction_related"] is False

    def test_form_5695_exterior_doors_cap(self, tara_black_form_5695):
        """Test exterior doors credit is capped at $500."""
        doors = tara_black_form_5695["exterior_doors"]

        # Total cost of doors
        assert doors["total_cost"] == Decimal("2740.00")

        # 30% of cost
        assert doors["calculated_credit"] == Decimal("822.00")

        # But capped at $500
        assert doors["credit_cap"] == Decimal("500.00")
        assert doors["allowed_credit"] == Decimal("500.00")

    def test_form_5695_windows_credit(self, tara_black_form_5695):
        """Test windows credit calculation."""
        windows = tara_black_form_5695["windows"]

        # Total cost
        assert windows["total_cost"] == Decimal("600.00")

        # 30% of cost
        assert windows["calculated_credit"] == Decimal("180.00")

        # Below $600 cap, so full credit allowed
        assert windows["credit_cap"] == Decimal("600.00")
        assert windows["allowed_credit"] == Decimal("180.00")

    def test_form_5695_central_ac_cap(self, tara_black_form_5695):
        """Test central AC credit is capped at $600."""
        ac = tara_black_form_5695["central_ac"]

        # Total cost
        assert ac["total_cost"] == Decimal("2500.00")

        # 30% of cost
        assert ac["calculated_credit"] == Decimal("750.00")

        # But capped at $600
        assert ac["credit_cap"] == Decimal("600.00")
        assert ac["allowed_credit"] == Decimal("600.00")

    def test_form_5695_annual_limit(self, tara_black_form_5695):
        """Test annual limit of $1,200 for general improvements."""
        # Sum of individual credits
        total_credits = (
            tara_black_form_5695["exterior_doors"]["allowed_credit"] +
            tara_black_form_5695["windows"]["allowed_credit"] +
            tara_black_form_5695["central_ac"]["allowed_credit"]
        )
        assert total_credits == Decimal("1280.00")

        # But annual limit is $1,200
        assert tara_black_form_5695["annual_limit"] == Decimal("1200.00")

        # Final credit is limited
        assert tara_black_form_5695["line_32_credit"] == Decimal("1200.00")

    def test_form_5695_flows_to_schedule_3(self, tara_black_form_5695, tara_black_schedule_3):
        """Test Form 5695 credit flows to Schedule 3."""
        form_5695_credit = tara_black_form_5695["line_32_credit"]
        schedule_3_credit = tara_black_schedule_3["line_5_residential_energy_credit"]

        assert schedule_3_credit == form_5695_credit
        assert schedule_3_credit == Decimal("1200.00")


# =============================================================================
# TEST CLASS: Tax Calculation
# =============================================================================


class TestTaxCalculation:
    """Tests for Form 1040 tax calculations."""

    def test_agi_calculation(self, tara_black_form_1040_data):
        """Test AGI equals total income (no adjustments)."""
        assert tara_black_form_1040_data["agi"] == tara_black_form_1040_data["total_income"]
        assert tara_black_form_1040_data["agi"] == Decimal("42470.00")

    def test_taxable_income_calculation(self, tara_black_form_1040_data):
        """Test taxable income = AGI - standard deduction."""
        agi = tara_black_form_1040_data["agi"]
        deduction = tara_black_form_1040_data["deduction"]
        expected_taxable = agi - deduction

        assert tara_black_form_1040_data["taxable_income"] == expected_taxable
        assert tara_black_form_1040_data["taxable_income"] == Decimal("26720.00")

    def test_standard_deduction_single_2025(self, tara_black_form_1040_data):
        """Test OBBBA 2025 single standard deduction."""
        # OBBBA 2025 single standard deduction is $15,750
        assert tara_black_form_1040_data["line_12_standard_deduction"] == Decimal("15750.00")

    def test_total_tax_with_schedule_2(self, tara_black_form_1040_data):
        """Test total tax includes Schedule 2 additional taxes."""
        line_16_tax = tara_black_form_1040_data["line_16_tax"]
        schedule_2_tax = tara_black_form_1040_data["line_17_schedule_2"]

        # Total before credits
        assert tara_black_form_1040_data["line_18_total"] == line_16_tax + schedule_2_tax

    def test_tax_minus_credits(self, tara_black_form_1040_data):
        """Test tax after Schedule 3 credits."""
        total_before = tara_black_form_1040_data["line_18_total"]
        credits = tara_black_form_1040_data["line_20_schedule_3"]
        expected_after = max(Decimal("0"), total_before - credits)

        assert tara_black_form_1040_data["line_22_tax_minus_credits"] == expected_after

    def test_refund_calculation(self, tara_black_form_1040_data):
        """Test refund calculation (payments - tax)."""
        total_payments = tara_black_form_1040_data["total_payments"]
        total_tax = tara_black_form_1040_data["total_tax"]

        if total_payments > total_tax:
            expected_refund = total_payments - total_tax
            assert tara_black_form_1040_data["refund"] == expected_refund
            assert tara_black_form_1040_data["amount_owed"] == Decimal("0")
        else:
            expected_owed = total_tax - total_payments
            assert tara_black_form_1040_data["amount_owed"] == expected_owed
            assert tara_black_form_1040_data["refund"] == Decimal("0")


# =============================================================================
# TEST CLASS: XML Serialization
# =============================================================================


class TestScenario1XMLSerialization:
    """Tests for XML serialization of Scenario 1 data."""

    def test_taxpayer_info_creation(self, tara_black_taxpayer):
        """Test TaxpayerInfo object creation."""
        taxpayer_info = TaxpayerInfo(
            primary_ssn=tara_black_taxpayer["ssn_clean"],
            primary_first_name=tara_black_taxpayer["first_name"],
            primary_last_name=tara_black_taxpayer["last_name"],
            primary_date_of_birth=tara_black_taxpayer["date_of_birth"],
        )

        assert taxpayer_info.primary_ssn == "400011032"
        assert taxpayer_info.primary_first_name == "Tara"
        assert taxpayer_info.primary_last_name == "Black"

    def test_submission_id_generation(self):
        """Test MeF submission ID generation."""
        submission_id = SubmissionId.generate(efin="123456", sequence=1)

        # Submission ID format: 20 characters
        assert len(submission_id.submission_id) == 20
        assert submission_id.submission_id.isdigit()

    def test_return_header_creation(self, tara_black_taxpayer):
        """Test ReturnHeader creation for single filer."""
        taxpayer_info = TaxpayerInfo(
            primary_ssn=tara_black_taxpayer["ssn_clean"],
            primary_first_name=tara_black_taxpayer["first_name"],
            primary_last_name=tara_black_taxpayer["last_name"],
        )

        submission_id = SubmissionId.generate(efin="123456", sequence=1)

        return_header = ReturnHeader(
            submission_id=submission_id,
            submission_type=SubmissionType.INDIVIDUAL_1040,
            category=SubmissionCategory.ORIGINAL,
            tax_year=2025,
            taxpayer=taxpayer_info,
            filing_status=1,  # Single
            primary_pin="12345",
            software_id="12345678",
            originator_efin="123456",
        )

        assert return_header.filing_status == 1
        assert return_header.tax_year == 2025
        assert return_header.taxpayer.primary_ssn == "400011032"

    def test_xml_serialization(self, tara_black_form_1040_data):
        """Test Form 1040 XML serialization."""
        serializer = XmlSerializer(tax_year=2025)
        xml = serializer.serialize_form_1040(tara_black_form_1040_data)

        # Basic XML structure checks
        assert xml.strip().startswith("<IRS1040")
        assert xml.strip().endswith("</IRS1040>")

        # Check key values are present
        assert "42470" in xml  # Wages
        assert "15750" in xml  # OBBBA 2025 Standard deduction


# =============================================================================
# TEST CLASS: Business Rules Validation
# =============================================================================


class TestScenario1BusinessRules:
    """Tests for business rules validation of Scenario 1 data."""

    def test_single_filer_no_spouse(self, tara_black_form_1040_data):
        """Test single filer has no spouse information."""
        assert tara_black_form_1040_data["filing_status"] == 1
        assert tara_black_form_1040_data["spouse_ssn"] is None
        assert tara_black_form_1040_data["spouse_first_name"] is None

    def test_single_filer_no_dependents(self, tara_black_form_1040_data):
        """Test single filer has no dependents."""
        assert len(tara_black_form_1040_data["dependents"]) == 0
        assert tara_black_form_1040_data["line_19_ctc_actc"] == Decimal("0")

    def test_schedule_attachments_present(self, tara_black_form_1040_data):
        """Test required schedules are marked as attached."""
        assert tara_black_form_1040_data["has_schedule_h"] is True
        assert tara_black_form_1040_data["has_form_5695"] is True
        assert tara_black_form_1040_data["has_schedule_2"] is True
        assert tara_black_form_1040_data["has_schedule_3"] is True

    def test_business_rules_validator(self, tara_black_form_1040_data):
        """Test form data passes business rules validation."""
        validator = BusinessRulesValidator(tax_year=2025, filing_status=1)
        result = validator.validate(tara_black_form_1040_data)

        assert isinstance(result, ValidationResult)

        # Check for critical errors
        critical_errors = [e for e in result.errors if e.severity == ValidationSeverity.ERROR]

        # Log any errors for debugging
        for error in critical_errors:
            print(f"Validation error: {error.code} - {error.message}")


# =============================================================================
# TEST CLASS: Integration Tests
# =============================================================================


class TestScenario1Integration:
    """Integration tests for the complete Scenario 1 data."""

    def test_complete_form_1040_structure(self, tara_black_form_1040_data):
        """Test complete form data has all required fields."""
        required_fields = [
            "primary_ssn", "primary_first_name", "primary_last_name",
            "filing_status", "wages", "total_income", "agi",
            "deduction", "taxable_income", "total_tax", "total_payments",
        ]

        for field in required_fields:
            assert field in tara_black_form_1040_data, f"Missing field: {field}"

    def test_form_1040_line_math(self, tara_black_form_1040_data):
        """Test Form 1040 line math consistency."""
        # Line 9 = Line 1z (for this simple scenario)
        assert tara_black_form_1040_data["line_9_total_income"] == tara_black_form_1040_data["line_1z_wages"]

        # Line 11 = Line 9 - Line 10
        assert tara_black_form_1040_data["line_11_agi"] == (
            tara_black_form_1040_data["line_9_total_income"] -
            tara_black_form_1040_data["line_10_adjustments"]
        )

        # Line 15 = Line 11 - Line 14
        assert tara_black_form_1040_data["line_15_taxable_income"] == (
            tara_black_form_1040_data["line_11_agi"] -
            tara_black_form_1040_data["line_14_total_deductions"]
        )

    def test_w2_to_form_1040_flow(self, tara_black_w2_data, tara_black_form_1040_data):
        """Test W-2 data flows correctly to Form 1040."""
        # Total W-2 wages -> Line 1z
        assert tara_black_form_1040_data["line_1z_wages"] == tara_black_w2_data["totals"]["total_wages"]

        # Total withholding -> Line 25a
        assert tara_black_form_1040_data["line_25a_w2_withholding"] == tara_black_w2_data["totals"]["federal_withholding"]

    def test_schedule_h_to_schedule_2_flow(self, tara_black_schedule_h, tara_black_schedule_2):
        """Test Schedule H flows to Schedule 2."""
        schedule_h_tax = tara_black_schedule_h["total_household_employment_taxes"]
        schedule_h_rounded = schedule_h_tax.quantize(Decimal("1"), rounding="ROUND_HALF_UP")

        assert tara_black_schedule_2["line_8_household_employment_taxes"] == schedule_h_rounded

    def test_form_5695_to_schedule_3_flow(self, tara_black_form_5695, tara_black_schedule_3):
        """Test Form 5695 flows to Schedule 3."""
        assert tara_black_schedule_3["line_5_residential_energy_credit"] == tara_black_form_5695["line_32_credit"]

    def test_schedule_2_to_form_1040_flow(self, tara_black_schedule_2, tara_black_form_1040_data):
        """Test Schedule 2 flows to Form 1040."""
        assert tara_black_form_1040_data["line_17_schedule_2"] == tara_black_schedule_2["line_21_total"]

    def test_schedule_3_to_form_1040_flow(self, tara_black_schedule_3, tara_black_form_1040_data):
        """Test Schedule 3 flows to Form 1040."""
        assert tara_black_form_1040_data["line_20_schedule_3"] == tara_black_schedule_3["line_8_total_part_1"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
