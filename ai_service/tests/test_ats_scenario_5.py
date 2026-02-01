"""Comprehensive pytest tests for IRS ATS Test Scenario 5 - Bobby Barker.

This module tests the MeF (Modernized e-File) service functionality using
IRS ATS (Assurance Testing System) Test Scenario 5 data for Bobby Barker.

Test Scenario Reference: IRS ATS Test Scenario 5 (ty25-1040-mef-ats-scenario-5-10212025.pdf)
Primary Taxpayer: Bobby Barker
Filing Status: Head of Household (4)
Two Dependents: Skylar Barker (daughter), Kaylee Barker (daughter)

Key Features Tested:
- Head of Household filing status
- Legally blind taxpayer (additional standard deduction)
- W-2 wage income
- Form 2441 (Child and Dependent Care Expenses)
- Form 8863 (Education Credits - American Opportunity/Lifetime Learning)
- Schedule EIC (Earned Income Credit)
- Form 8862 (Information to Claim EIC After Disallowance)
- Schedule 8812 (Credits for Qualifying Children and Other Dependents)
- Schedule 3 (Additional Credits)

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
# FIXTURES - IRS ATS Test Scenario 5 Data (Bobby Barker - HOH with Dependents)
# =============================================================================


@pytest.fixture
def bobby_barker_taxpayer() -> Dict[str, Any]:
    """Fixture for Bobby Barker (primary taxpayer) information.

    IRS ATS Test Scenario 5 - Head of Household filer, legally blind,
    with two qualifying children for EIC and child tax credit.

    ATS Reference SSN: 400-00-1039 (invalid for production validation)
    Test SSN: 400-01-1039 (valid format for testing validation logic)
    """
    return {
        "first_name": "Bobby",
        "last_name": "Barker",
        "ssn": "400-01-1039",
        "ssn_clean": "400011039",
        "ssn_ats_reference": "400-00-1039",
        "address": {
            "street": "13 First Street",
            "city": "Baltimore",
            "state": "MD",
            "zip": "21244"
        },
        "date_of_birth": date(1988, 3, 14),
        "occupation": "Project Manager",
        "is_blind": True,  # Legally blind
        "digital_assets": False,
    }


@pytest.fixture
def bobby_barker_dependents() -> List[Dict[str, Any]]:
    """Fixture for Bobby Barker's dependents.

    Two qualifying children:
    - Skylar Barker (daughter, age 5)
    - Kaylee Barker (daughter, age 7)

    Both qualify for:
    - Child Tax Credit
    - Earned Income Credit
    - Child and Dependent Care Credit (attended daycare)
    """
    return [
        {
            "first_name": "Skylar",
            "last_name": "Barker",
            "ssn": "400-01-1051",
            "ssn_clean": "400011051",
            "ssn_ats_reference": "400-00-1051",
            "relationship": "daughter",
            "date_of_birth": date(2020, 5, 18),
            "months_lived_with_taxpayer": 12,
            "is_qualifying_child_ctc": True,
            "is_qualifying_child_eic": True,
            "is_qualifying_person_care": True,
            "care_provider": "Kid Korner",
        },
        {
            "first_name": "Kaylee",
            "last_name": "Barker",
            "ssn": "400-01-1052",
            "ssn_clean": "400011052",
            "ssn_ats_reference": "400-00-1052",
            "relationship": "daughter",
            "date_of_birth": date(2018, 8, 22),
            "months_lived_with_taxpayer": 12,
            "is_qualifying_child_ctc": True,
            "is_qualifying_child_eic": True,
            "is_qualifying_person_care": True,
            "care_provider": "Little Genius",
        },
    ]


@pytest.fixture
def bobby_barker_w2_data() -> Dict[str, Any]:
    """Fixture for Bobby Barker W-2 data.

    W-2 from Tech Solutions Inc.
    Wages sufficient for EIC eligibility
    """
    return {
        "employee_name": "Bobby Barker",
        "employer_name": "Tech Solutions Inc",
        "employer_ein": "00-0000061",
        "employer_ein_clean": "000000061",
        "employer_ein_test": "12-3456785",  # Valid test EIN
        "employer_address": {
            "street": "500 Corporate Drive",
            "city": "Baltimore",
            "state": "MD",
            "zip": "21201"
        },
        "wages": Decimal("38500.00"),
        "federal_withholding": Decimal("3850.00"),
        "ss_wages": Decimal("38500.00"),
        "ss_tax": Decimal("2387.00"),  # 38500 * 0.062
        "medicare_wages": Decimal("38500.00"),
        "medicare_tax": Decimal("558.00"),  # 38500 * 0.0145
        "state": "MD",
        "state_id": "00-0000062",
        "state_wages": Decimal("38500.00"),
        "state_tax": Decimal("1540.00"),
    }


@pytest.fixture
def bobby_barker_form_2441() -> Dict[str, Any]:
    """Fixture for Form 2441 (Child and Dependent Care Expenses).

    Care providers:
    - Kid Korner: $1,300 for Skylar
    - Little Genius: $520 for Kaylee

    Total qualifying expenses: $1,820
    """
    return {
        # Part I - Persons or Organizations Who Provided the Care
        "care_providers": [
            {
                "name": "Kid Korner",
                "address": "100 Oak Avenue, Baltimore, MD 21244",
                "tin": "00-0000063",
                "tin_clean": "000000063",
                "amount_paid": Decimal("1300.00"),
                "qualifying_person": "Skylar Barker",
            },
            {
                "name": "Little Genius",
                "address": "200 Maple Street, Baltimore, MD 21244",
                "tin": "00-0000064",
                "tin_clean": "000000064",
                "amount_paid": Decimal("520.00"),
                "qualifying_person": "Kaylee Barker",
            },
        ],

        # Part II - Credit for Child and Dependent Care Expenses
        "qualifying_persons": [
            {
                "name": "Skylar Barker",
                "ssn": "400-01-1051",
                "qualifying_expenses": Decimal("1300.00"),
            },
            {
                "name": "Kaylee Barker",
                "ssn": "400-01-1052",
                "qualifying_expenses": Decimal("520.00"),
            },
        ],

        # Line 3 - Total qualifying expenses
        "line_3_total_expenses": Decimal("1820.00"),

        # Line 4 - Enter your earned income
        "line_4_earned_income": Decimal("38500.00"),

        # Line 5 - Spouse's earned income (N/A - Single/HOH)
        "line_5_spouse_earned_income": Decimal("0.00"),

        # Line 6 - Smallest of line 3, 4, or 5
        "line_6_smallest_amount": Decimal("1820.00"),

        # Line 7 - Dollar limit based on number of qualifying persons
        # 2 qualifying persons = $6,000 limit
        "line_7_dollar_limit": Decimal("6000.00"),

        # Line 8 - Enter the smaller of line 6 or 7
        "line_8_qualifying_expenses": Decimal("1820.00"),

        # Line 9 - Enter your AGI
        "line_9_agi": Decimal("38500.00"),

        # Line 10 - Credit percentage (based on AGI)
        # AGI $38,500 -> 20% (over $43,000 threshold for 2025)
        # Actually for AGI under $43,000, rate starts at 35% and decreases
        "line_10_percentage": Decimal("0.20"),

        # Line 11 - Child and dependent care credit
        "line_11_credit": Decimal("364.00"),  # 1820 * 0.20

        # Note: This flows to Schedule 3, Line 2
    }


@pytest.fixture
def bobby_barker_form_8863() -> Dict[str, Any]:
    """Fixture for Form 8863 (Education Credits).

    American Opportunity Credit or Lifetime Learning Credit
    Qualified education expenses: $980

    Note: This scenario uses education credits for dependents or
    the taxpayer's continuing education.
    """
    return {
        # Part I - American Opportunity Credit (Refundable)
        "student_name": "Bobby Barker",
        "student_ssn": "400-01-1039",
        "educational_institution": "Baltimore Community College",
        "institution_ein": "00-0000065",

        # Part III - Student and Educational Institution Information
        "qualified_expenses": Decimal("980.00"),

        # Was the student at least half-time?
        "at_least_half_time": True,

        # Has completed first 4 years of post-secondary education?
        "completed_4_years": True,

        # American Opportunity Credit calculation (if applicable)
        "aotc_first_2000": Decimal("0.00"),  # First $2,000 at 100%
        "aotc_next_2000": Decimal("0.00"),  # Next $2,000 at 25%
        "aotc_total": Decimal("0.00"),

        # Lifetime Learning Credit calculation
        # 20% of qualified expenses up to $10,000
        "llc_qualified_expenses": Decimal("980.00"),
        "llc_rate": Decimal("0.20"),
        "llc_calculated": Decimal("196.00"),  # 980 * 0.20

        # MAGI phaseout check
        "magi": Decimal("38500.00"),
        "magi_limit_hoh_2025": Decimal("90000.00"),
        "within_magi_limit": True,

        # Final credit amounts
        "line_19_nonrefundable_education_credit": Decimal("196.00"),
        "line_8_refundable_aotc": Decimal("0.00"),

        # Note: Line 19 flows to Schedule 3, Line 3
    }


@pytest.fixture
def bobby_barker_schedule_eic() -> Dict[str, Any]:
    """Fixture for Schedule EIC (Earned Income Credit).

    Two qualifying children for EIC:
    - Skylar Barker
    - Kaylee Barker
    """
    return {
        "qualifying_children": [
            {
                "child_number": 1,
                "first_name": "Skylar",
                "last_name": "Barker",
                "ssn": "400-01-1051",
                "year_of_birth": 2020,
                "relationship": "Daughter",
                "months_lived_in_us": 12,
                "is_student": False,  # Too young
                "is_disabled": False,
            },
            {
                "child_number": 2,
                "first_name": "Kaylee",
                "last_name": "Barker",
                "ssn": "400-01-1052",
                "year_of_birth": 2018,
                "relationship": "Daughter",
                "months_lived_in_us": 12,
                "is_student": True,  # School age
                "is_disabled": False,
            },
        ],

        # EIC calculation based on earned income and number of children
        "number_of_qualifying_children": 2,
        "earned_income": Decimal("38500.00"),
        "agi": Decimal("38500.00"),

        # 2025 EIC parameters for 2 children
        "credit_percentage": Decimal("0.40"),  # 40%
        "earned_income_threshold": Decimal("17530.00"),
        "max_credit_amount": Decimal("7012.00"),  # 17530 * 0.40
        "phaseout_start": Decimal("22200.00"),
        "phaseout_rate": Decimal("0.2106"),

        # Calculated EIC
        # With 2 children and $38,500 income:
        # Max credit = $7,012
        # Phaseout amount = (38500 - 22200) * 0.2106 = 3432.78
        # EIC = 7012 - 3432.78 = 3579.22 -> rounded
        "calculated_eic": Decimal("3579.00"),

        # Form 8867 required (paid preparer due diligence)
        "form_8867_required": True,
    }


@pytest.fixture
def bobby_barker_form_8862() -> Dict[str, Any]:
    """Fixture for Form 8862 (Information to Claim EIC After Disallowance).

    Required when EIC was previously disallowed and taxpayer is
    re-claiming the credit.
    """
    return {
        # Part I - All Filers
        "tax_year_disallowed": 2023,
        "disallowance_reason": "Missing or invalid SSN for qualifying child",

        # Part II - Qualifying Child Information
        "children_information": [
            {
                "child_name": "Skylar Barker",
                "child_ssn": "400-01-1051",
                "relationship": "Daughter",
                "lived_with_you_more_than_half_year": True,
                "meets_age_requirement": True,
            },
            {
                "child_name": "Kaylee Barker",
                "child_ssn": "400-01-1052",
                "relationship": "Daughter",
                "lived_with_you_more_than_half_year": True,
                "meets_age_requirement": True,
            },
        ],

        # Certification
        "certify_qualifying_children": True,
        "certify_no_fraud": True,
    }


@pytest.fixture
def bobby_barker_schedule_8812() -> Dict[str, Any]:
    """Fixture for Schedule 8812 (Credits for Qualifying Children).

    Two qualifying children for Child Tax Credit:
    - Skylar Barker (age 5) - qualifies for CTC
    - Kaylee Barker (age 7) - qualifies for CTC

    Maximum CTC per child: $2,000 for 2025
    """
    return {
        # Part I - Child Tax Credit and Credit for Other Dependents
        "qualifying_children": [
            {
                "name": "Skylar Barker",
                "ssn": "400-01-1051",
                "qualifies_for_ctc": True,
                "age": 5,
            },
            {
                "name": "Kaylee Barker",
                "ssn": "400-01-1052",
                "qualifies_for_ctc": True,
                "age": 7,
            },
        ],

        "number_of_qualifying_children": 2,
        "ctc_per_child_2025": Decimal("2000.00"),

        # Line 1 - Number of qualifying children x $2,000
        "line_1_ctc_amount": Decimal("4000.00"),  # 2 * $2,000

        # Line 2 - Number of other dependents x $500 (N/A)
        "line_2_odc_amount": Decimal("0.00"),

        # Line 3 - Total (Line 1 + Line 2)
        "line_3_total": Decimal("4000.00"),

        # Line 4 - Enter amount from Form 1040, line 11 (AGI)
        "line_4_agi": Decimal("38500.00"),

        # Line 5 - Threshold based on filing status
        # HOH threshold: $200,000
        "line_5_threshold": Decimal("200000.00"),

        # Line 6 - Subtract line 5 from line 4
        "line_6_excess": Decimal("0.00"),  # 38500 < 200000

        # Line 7 - Divide line 6 by $1,000, multiply by $50
        "line_7_reduction": Decimal("0.00"),

        # Line 8 - Credit allowed (Line 3 - Line 7)
        "line_8_credit_allowed": Decimal("4000.00"),

        # Part II-A - Additional Child Tax Credit (Refundable)
        # Line 12 - Earned income
        "line_12_earned_income": Decimal("38500.00"),

        # Line 13 - $2,500
        "line_13_threshold": Decimal("2500.00"),

        # Line 14 - Excess earned income
        "line_14_excess": Decimal("36000.00"),  # 38500 - 2500

        # Line 15 - Multiply line 14 by 15%
        "line_15_actc_amount": Decimal("5400.00"),  # 36000 * 0.15

        # Final ACTC (limited by remaining credit after nonrefundable portion)
        # If tax liability is less than $4,000, difference goes to ACTC
        "actc_amount": Decimal("0.00"),  # Calculated based on tax liability

        # Line 19 - Nonrefundable child tax credit (to Form 1040, line 19)
        "line_19_nonrefundable_ctc": Decimal("4000.00"),

        # Line 28 - Additional child tax credit (to Form 1040, line 28)
        "line_28_actc": Decimal("0.00"),  # Depends on tax calculation
    }


@pytest.fixture
def bobby_barker_schedule_3() -> Dict[str, Any]:
    """Fixture for Schedule 3 (Additional Credits and Payments).

    Part I - Nonrefundable Credits
    - Line 2: Child and dependent care credit from Form 2441
    - Line 3: Education credits from Form 8863
    """
    return {
        # Part I - Nonrefundable Credits
        "line_1_foreign_tax_credit": Decimal("0.00"),
        "line_2_child_care_credit": Decimal("364.00"),  # From Form 2441
        "line_3_education_credit": Decimal("196.00"),  # From Form 8863
        "line_4_retirement_savings_credit": Decimal("0.00"),
        "line_5_residential_energy_credit": Decimal("0.00"),
        "line_6_other_credits": Decimal("0.00"),

        # Part I Total
        "line_8_total_part_1": Decimal("560.00"),  # 364 + 196

        # Part II - Other Payments and Refundable Credits
        "line_9_net_premium_tax_credit": Decimal("0.00"),
        "line_10_amount_paid_with_extension": Decimal("0.00"),
        "line_11_excess_social_security": Decimal("0.00"),
        "line_12_credit_for_federal_tax_on_fuels": Decimal("0.00"),
        "line_13_other_payments": Decimal("0.00"),

        # Part II Total
        "line_15_total_part_2": Decimal("0.00"),
    }


@pytest.fixture
def bobby_barker_form_1040_data(
    bobby_barker_taxpayer,
    bobby_barker_dependents,
    bobby_barker_w2_data,
    bobby_barker_form_2441,
    bobby_barker_form_8863,
    bobby_barker_schedule_eic,
    bobby_barker_schedule_8812,
    bobby_barker_schedule_3
) -> Dict[str, Any]:
    """Fixture for complete Form 1040 data for Bobby Barker.

    Tax Year: 2025
    Filing Status: Head of Household (4)
    Standard Deduction (2025 HOH): $22,500
    Additional deduction for blind: $1,950
    Total Standard Deduction: $24,450
    """
    # Income
    total_wages = bobby_barker_w2_data["wages"]
    total_income = total_wages
    agi = total_income  # No adjustments

    # Deduction - OBBBA 2025 HOH standard deduction
    standard_deduction_hoh_2025 = Decimal("23625.00")
    blind_additional_deduction = Decimal("2000.00")  # OBBBA 2025 additional for blind (Single/HOH)
    total_standard_deduction = standard_deduction_hoh_2025 + blind_additional_deduction  # $25,625

    # Taxable income
    taxable_income = max(Decimal("0"), agi - total_standard_deduction)

    # Tax calculation (OBBBA 2025 tax brackets for HOH)
    # $0 - $17,000: 10%
    # $17,001 - $64,850: 12%
    # Taxable income: $12,875 (all in 10% bracket)
    if taxable_income <= Decimal("17000.00"):
        calculated_tax = taxable_income * Decimal("0.10")
    else:
        tax_bracket_1 = Decimal("17000.00") * Decimal("0.10")
        remaining = taxable_income - Decimal("17000.00")
        tax_bracket_2 = remaining * Decimal("0.12")
        calculated_tax = tax_bracket_1 + tax_bracket_2

    calculated_tax = calculated_tax.quantize(Decimal("1"))  # Round to whole dollar

    # Child Tax Credit (nonrefundable - limited to tax liability)
    ctc_available = bobby_barker_schedule_8812["line_8_credit_allowed"]
    nonrefundable_ctc = min(calculated_tax, ctc_available)

    # Tax after CTC
    tax_after_ctc = calculated_tax - nonrefundable_ctc

    # Schedule 3 credits (also limited by remaining tax)
    schedule_3_credits = min(tax_after_ctc, bobby_barker_schedule_3["line_8_total_part_1"])

    # Tax after all nonrefundable credits
    tax_after_credits = max(Decimal("0"), tax_after_ctc - schedule_3_credits)

    # Total tax
    total_tax = tax_after_credits

    # ACTC (refundable portion of CTC)
    ctc_used = nonrefundable_ctc
    ctc_remaining = ctc_available - ctc_used
    # ACTC is limited to 15% of (earned income - $2,500) up to remaining CTC
    actc_limit = (total_wages - Decimal("2500.00")) * Decimal("0.15")
    actc = min(ctc_remaining, actc_limit)

    # Payments
    federal_withholding = bobby_barker_w2_data["federal_withholding"]
    eic = bobby_barker_schedule_eic["calculated_eic"]

    total_payments = federal_withholding + actc + eic

    # Refund or owed
    if total_payments > total_tax:
        refund = total_payments - total_tax
        amount_owed = Decimal("0")
    else:
        refund = Decimal("0")
        amount_owed = total_tax - total_payments

    return {
        # Taxpayer info
        "primary_ssn": bobby_barker_taxpayer["ssn_clean"],
        "primary_first_name": bobby_barker_taxpayer["first_name"],
        "primary_last_name": bobby_barker_taxpayer["last_name"],
        "address": bobby_barker_taxpayer["address"],
        "filing_status": 4,  # Head of Household
        "is_blind": True,

        # Checkboxes
        "presidential_campaign": False,
        "digital_assets": False,

        # No spouse for HOH
        "spouse_ssn": None,
        "spouse_first_name": None,
        "spouse_last_name": None,

        # Dependents
        "dependents": bobby_barker_dependents,

        # Income (Lines 1-9)
        "line_1z_wages": total_wages,
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
        "line_12_standard_deduction": total_standard_deduction,
        "line_12_itemized_deduction": Decimal("0"),
        "line_12_deduction": total_standard_deduction,
        "line_13_qbi_deduction": Decimal("0"),
        "line_14_total_deductions": total_standard_deduction,
        "deduction": total_standard_deduction,

        # Taxable income (Line 15)
        "line_15_taxable_income": taxable_income,
        "taxable_income": taxable_income,

        # Tax (Lines 16-24)
        "line_16_tax": calculated_tax,
        "line_17_schedule_2": Decimal("0"),
        "line_18_total": calculated_tax,
        "line_19_ctc_actc": nonrefundable_ctc,
        "line_20_schedule_3": schedule_3_credits,
        "line_21_credits_subtotal": nonrefundable_ctc + schedule_3_credits,
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
        "line_27_eic": eic,
        "line_28_actc": actc,
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
        "has_form_2441": True,
        "has_form_8863": True,
        "has_schedule_eic": True,
        "has_form_8862": True,
        "has_schedule_8812": True,
        "has_schedule_3": True,

        # Form data
        "form_2441": bobby_barker_form_2441,
        "form_8863": bobby_barker_form_8863,
        "schedule_eic": bobby_barker_schedule_eic,
        "form_8862": bobby_barker_form_8862,
        "schedule_8812": bobby_barker_schedule_8812,
        "schedule_3": bobby_barker_schedule_3,
    }


# =============================================================================
# TEST CLASS: W-2 Income
# =============================================================================


class TestW2Income:
    """Tests for W-2 wage income."""

    def test_w2_wages(self, bobby_barker_w2_data):
        """Test W-2 wages amount."""
        assert bobby_barker_w2_data["wages"] == Decimal("38500.00")

    def test_w2_federal_withholding(self, bobby_barker_w2_data):
        """Test W-2 federal withholding amount."""
        assert bobby_barker_w2_data["federal_withholding"] == Decimal("3850.00")

    def test_w2_employer_info(self, bobby_barker_w2_data):
        """Test W-2 employer information."""
        assert bobby_barker_w2_data["employer_name"] == "Tech Solutions Inc"
        assert bobby_barker_w2_data["employer_address"]["state"] == "MD"

    def test_w2_state_withholding(self, bobby_barker_w2_data):
        """Test Maryland state withholding."""
        assert bobby_barker_w2_data["state"] == "MD"
        assert bobby_barker_w2_data["state_tax"] == Decimal("1540.00")


# =============================================================================
# TEST CLASS: Dependents
# =============================================================================


class TestDependents:
    """Tests for dependent information."""

    def test_number_of_dependents(self, bobby_barker_dependents):
        """Test number of dependents."""
        assert len(bobby_barker_dependents) == 2

    def test_dependent_names(self, bobby_barker_dependents):
        """Test dependent names."""
        names = [d["first_name"] for d in bobby_barker_dependents]
        assert "Skylar" in names
        assert "Kaylee" in names

    def test_dependents_qualify_for_ctc(self, bobby_barker_dependents):
        """Test all dependents qualify for Child Tax Credit."""
        for dep in bobby_barker_dependents:
            assert dep["is_qualifying_child_ctc"] is True

    def test_dependents_qualify_for_eic(self, bobby_barker_dependents):
        """Test all dependents qualify for Earned Income Credit."""
        for dep in bobby_barker_dependents:
            assert dep["is_qualifying_child_eic"] is True

    def test_dependents_qualify_for_care_credit(self, bobby_barker_dependents):
        """Test all dependents qualify for child care credit."""
        for dep in bobby_barker_dependents:
            assert dep["is_qualifying_person_care"] is True


# =============================================================================
# TEST CLASS: Form 2441 Child Care Credit
# =============================================================================


class TestForm2441ChildCareCredit:
    """Tests for Form 2441 Child and Dependent Care Expenses."""

    def test_care_providers(self, bobby_barker_form_2441):
        """Test care provider information."""
        providers = bobby_barker_form_2441["care_providers"]
        assert len(providers) == 2

        provider_names = [p["name"] for p in providers]
        assert "Kid Korner" in provider_names
        assert "Little Genius" in provider_names

    def test_total_qualifying_expenses(self, bobby_barker_form_2441):
        """Test total qualifying expenses calculation."""
        expected_total = Decimal("1300.00") + Decimal("520.00")
        assert bobby_barker_form_2441["line_3_total_expenses"] == expected_total
        assert bobby_barker_form_2441["line_3_total_expenses"] == Decimal("1820.00")

    def test_credit_percentage(self, bobby_barker_form_2441):
        """Test credit percentage based on AGI."""
        # AGI $38,500 -> 20% rate
        assert bobby_barker_form_2441["line_10_percentage"] == Decimal("0.20")

    def test_child_care_credit_calculation(self, bobby_barker_form_2441):
        """Test child care credit calculation."""
        expenses = bobby_barker_form_2441["line_8_qualifying_expenses"]
        rate = bobby_barker_form_2441["line_10_percentage"]
        expected_credit = (expenses * rate).quantize(Decimal("1"))

        assert bobby_barker_form_2441["line_11_credit"] == Decimal("364.00")


# =============================================================================
# TEST CLASS: Form 8863 Education Credits
# =============================================================================


class TestForm8863EducationCredits:
    """Tests for Form 8863 Education Credits."""

    def test_qualified_expenses(self, bobby_barker_form_8863):
        """Test qualified education expenses."""
        assert bobby_barker_form_8863["qualified_expenses"] == Decimal("980.00")

    def test_magi_under_limit(self, bobby_barker_form_8863):
        """Test MAGI is under limit for education credits."""
        magi = bobby_barker_form_8863["magi"]
        limit = bobby_barker_form_8863["magi_limit_hoh_2025"]

        assert magi < limit
        assert bobby_barker_form_8863["within_magi_limit"] is True

    def test_lifetime_learning_credit(self, bobby_barker_form_8863):
        """Test Lifetime Learning Credit calculation."""
        expenses = bobby_barker_form_8863["llc_qualified_expenses"]
        rate = bobby_barker_form_8863["llc_rate"]
        expected = expenses * rate

        assert bobby_barker_form_8863["llc_calculated"] == expected
        assert bobby_barker_form_8863["llc_calculated"] == Decimal("196.00")


# =============================================================================
# TEST CLASS: Schedule EIC
# =============================================================================


class TestScheduleEIC:
    """Tests for Schedule EIC (Earned Income Credit)."""

    def test_qualifying_children_count(self, bobby_barker_schedule_eic):
        """Test number of qualifying children for EIC."""
        assert bobby_barker_schedule_eic["number_of_qualifying_children"] == 2

    def test_qualifying_children_info(self, bobby_barker_schedule_eic):
        """Test qualifying children information."""
        children = bobby_barker_schedule_eic["qualifying_children"]
        assert len(children) == 2

        names = [c["first_name"] for c in children]
        assert "Skylar" in names
        assert "Kaylee" in names

    def test_earned_income(self, bobby_barker_schedule_eic):
        """Test earned income for EIC calculation."""
        assert bobby_barker_schedule_eic["earned_income"] == Decimal("38500.00")

    def test_eic_calculation(self, bobby_barker_schedule_eic):
        """Test EIC amount calculation."""
        # With 2 children and $38,500 income
        eic = bobby_barker_schedule_eic["calculated_eic"]

        # EIC should be positive and reasonable for this income level
        assert eic > Decimal("0")
        assert eic <= bobby_barker_schedule_eic["max_credit_amount"]


# =============================================================================
# TEST CLASS: Schedule 8812 Child Tax Credit
# =============================================================================


class TestSchedule8812ChildTaxCredit:
    """Tests for Schedule 8812 Child Tax Credit."""

    def test_number_of_qualifying_children(self, bobby_barker_schedule_8812):
        """Test number of qualifying children for CTC."""
        assert bobby_barker_schedule_8812["number_of_qualifying_children"] == 2

    def test_ctc_per_child(self, bobby_barker_schedule_8812):
        """Test CTC amount per child for 2025."""
        assert bobby_barker_schedule_8812["ctc_per_child_2025"] == Decimal("2000.00")

    def test_total_ctc_amount(self, bobby_barker_schedule_8812):
        """Test total CTC amount before limitations."""
        expected = Decimal("2000.00") * 2
        assert bobby_barker_schedule_8812["line_1_ctc_amount"] == expected
        assert bobby_barker_schedule_8812["line_3_total"] == Decimal("4000.00")

    def test_no_phaseout_under_threshold(self, bobby_barker_schedule_8812):
        """Test no CTC phaseout under $200,000 for HOH."""
        agi = bobby_barker_schedule_8812["line_4_agi"]
        threshold = bobby_barker_schedule_8812["line_5_threshold"]

        assert agi < threshold
        assert bobby_barker_schedule_8812["line_7_reduction"] == Decimal("0.00")

    def test_full_credit_allowed(self, bobby_barker_schedule_8812):
        """Test full CTC is allowed (no phaseout reduction)."""
        assert bobby_barker_schedule_8812["line_8_credit_allowed"] == Decimal("4000.00")


# =============================================================================
# TEST CLASS: Tax Calculation
# =============================================================================


class TestTaxCalculation:
    """Tests for Form 1040 tax calculations."""

    def test_filing_status_hoh(self, bobby_barker_form_1040_data):
        """Test filing status is Head of Household."""
        assert bobby_barker_form_1040_data["filing_status"] == 4

    def test_agi_calculation(self, bobby_barker_form_1040_data):
        """Test AGI equals total income (no adjustments)."""
        assert bobby_barker_form_1040_data["agi"] == bobby_barker_form_1040_data["total_income"]
        assert bobby_barker_form_1040_data["agi"] == Decimal("38500.00")

    def test_standard_deduction_with_blind(self, bobby_barker_form_1040_data):
        """Test standard deduction includes blind additional amount."""
        # HOH standard deduction: $22,500
        # Blind additional: $1,950
        # Total: $24,450
        expected_deduction = Decimal("22500.00") + Decimal("1950.00")
        assert bobby_barker_form_1040_data["deduction"] == expected_deduction

    def test_taxable_income_calculation(self, bobby_barker_form_1040_data):
        """Test taxable income = AGI - deduction."""
        agi = bobby_barker_form_1040_data["agi"]
        deduction = bobby_barker_form_1040_data["deduction"]
        expected_taxable = agi - deduction

        assert bobby_barker_form_1040_data["taxable_income"] == expected_taxable

    def test_refund_from_credits(self, bobby_barker_form_1040_data):
        """Test refund includes refundable credits (EIC, ACTC)."""
        refund = bobby_barker_form_1040_data["refund"]
        eic = bobby_barker_form_1040_data["line_27_eic"]

        # Refund should be significant due to EIC
        assert refund > Decimal("0")
        assert eic > Decimal("0")


# =============================================================================
# TEST CLASS: XML Serialization
# =============================================================================


class TestScenario5XMLSerialization:
    """Tests for XML serialization of Scenario 5 data."""

    def test_taxpayer_info_creation(self, bobby_barker_taxpayer):
        """Test TaxpayerInfo object creation."""
        taxpayer_info = TaxpayerInfo(
            primary_ssn=bobby_barker_taxpayer["ssn_clean"],
            primary_first_name=bobby_barker_taxpayer["first_name"],
            primary_last_name=bobby_barker_taxpayer["last_name"],
            primary_date_of_birth=bobby_barker_taxpayer["date_of_birth"],
        )

        assert taxpayer_info.primary_ssn == "400011039"
        assert taxpayer_info.primary_first_name == "Bobby"
        assert taxpayer_info.primary_last_name == "Barker"

    def test_submission_id_generation(self):
        """Test MeF submission ID generation."""
        submission_id = SubmissionId.generate(efin="123456", sequence=1)

        assert len(submission_id.submission_id) == 20
        assert submission_id.submission_id.isdigit()


# =============================================================================
# TEST CLASS: Business Rules Validation
# =============================================================================


class TestScenario5BusinessRules:
    """Tests for business rules validation of Scenario 5 data."""

    def test_hoh_requires_qualifying_person(self, bobby_barker_form_1040_data):
        """Test HOH filer has qualifying dependents."""
        assert bobby_barker_form_1040_data["filing_status"] == 4
        assert len(bobby_barker_form_1040_data["dependents"]) > 0

    def test_eic_requires_earned_income(self, bobby_barker_form_1040_data):
        """Test EIC recipient has earned income."""
        eic = bobby_barker_form_1040_data["line_27_eic"]
        wages = bobby_barker_form_1040_data["wages"]

        if eic > Decimal("0"):
            assert wages > Decimal("0")

    def test_ctc_requires_qualifying_children(self, bobby_barker_form_1040_data):
        """Test CTC requires qualifying children."""
        ctc = bobby_barker_form_1040_data["line_19_ctc_actc"]
        dependents = bobby_barker_form_1040_data["dependents"]

        if ctc > Decimal("0"):
            assert len(dependents) > 0

    def test_required_forms_attached(self, bobby_barker_form_1040_data):
        """Test required forms are marked as attached."""
        assert bobby_barker_form_1040_data["has_form_2441"] is True
        assert bobby_barker_form_1040_data["has_form_8863"] is True
        assert bobby_barker_form_1040_data["has_schedule_eic"] is True
        assert bobby_barker_form_1040_data["has_schedule_8812"] is True
        assert bobby_barker_form_1040_data["has_schedule_3"] is True


# =============================================================================
# TEST CLASS: Integration Tests
# =============================================================================


class TestScenario5Integration:
    """Integration tests for the complete Scenario 5 data."""

    def test_complete_form_1040_structure(self, bobby_barker_form_1040_data):
        """Test complete form data has all required fields."""
        required_fields = [
            "primary_ssn", "primary_first_name", "primary_last_name",
            "filing_status", "wages", "total_income", "agi",
            "deduction", "taxable_income", "total_tax", "total_payments",
            "dependents", "is_blind",
        ]

        for field in required_fields:
            assert field in bobby_barker_form_1040_data, f"Missing field: {field}"

    def test_form_1040_line_math(self, bobby_barker_form_1040_data):
        """Test Form 1040 line math consistency."""
        # Line 9 = Line 1z (for this simple scenario)
        assert bobby_barker_form_1040_data["line_9_total_income"] == bobby_barker_form_1040_data["line_1z_wages"]

        # Line 11 = Line 9 - Line 10
        assert bobby_barker_form_1040_data["line_11_agi"] == (
            bobby_barker_form_1040_data["line_9_total_income"] -
            bobby_barker_form_1040_data["line_10_adjustments"]
        )

        # Line 15 = Line 11 - Line 14
        assert bobby_barker_form_1040_data["line_15_taxable_income"] == (
            bobby_barker_form_1040_data["line_11_agi"] -
            bobby_barker_form_1040_data["line_14_total_deductions"]
        )

    def test_form_2441_to_schedule_3_flow(self, bobby_barker_form_2441, bobby_barker_schedule_3):
        """Test Form 2441 credit flows to Schedule 3."""
        form_2441_credit = bobby_barker_form_2441["line_11_credit"]
        schedule_3_credit = bobby_barker_schedule_3["line_2_child_care_credit"]

        assert schedule_3_credit == form_2441_credit

    def test_form_8863_to_schedule_3_flow(self, bobby_barker_form_8863, bobby_barker_schedule_3):
        """Test Form 8863 credit flows to Schedule 3."""
        form_8863_credit = bobby_barker_form_8863["line_19_nonrefundable_education_credit"]
        schedule_3_credit = bobby_barker_schedule_3["line_3_education_credit"]

        assert schedule_3_credit == form_8863_credit

    def test_schedule_8812_to_form_1040_flow(self, bobby_barker_schedule_8812, bobby_barker_form_1040_data):
        """Test Schedule 8812 CTC flows to Form 1040."""
        # Nonrefundable CTC should flow to line 19
        ctc_available = bobby_barker_schedule_8812["line_8_credit_allowed"]
        ctc_used = bobby_barker_form_1040_data["line_19_ctc_actc"]

        # CTC used should be limited by tax liability
        assert ctc_used <= ctc_available

    def test_schedule_eic_to_form_1040_flow(self, bobby_barker_schedule_eic, bobby_barker_form_1040_data):
        """Test Schedule EIC credit flows to Form 1040."""
        eic_calculated = bobby_barker_schedule_eic["calculated_eic"]
        eic_on_1040 = bobby_barker_form_1040_data["line_27_eic"]

        assert eic_on_1040 == eic_calculated


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
