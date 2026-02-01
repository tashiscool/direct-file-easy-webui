"""Comprehensive pytest tests for IRS ATS Test Scenario NR-1 - Lucas LeBlanc.

This module tests the MeF (Modernized e-File) service functionality using
IRS ATS (Assurance Testing System) Test Scenario NR-1 data for Lucas LeBlanc.

Test Scenario Reference: IRS ATS Test Scenario NR-1 (ty25-1040-nr-mef-ats-scenario-1-10202025.pdf)
Primary Taxpayer: Lucas LeBlanc
Filing Status: Married Filing Separately (MFS)
No Dependents

Key Features Tested:
- Form 1040-NR (Nonresident Alien Income Tax Return)
- Nonresident alien using simplified refund method
- Multiple W-2 forms (2 employers)
- Schedule C (Profit or Loss From Business - Independent Writer)
- Schedule SE with Form 4361 exemption (Minister exemption)
- IRA distributions (not taxable - Form 4361 on file)
- Form 5329 (Additional Taxes on Qualified Plans)
- Foreign address handling (Canada)
- Self-select signature PIN method

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
# FIXTURES - IRS ATS Test Scenario NR-1 Data (Lucas LeBlanc - Nonresident Alien)
# =============================================================================


@pytest.fixture
def lucas_leblanc_taxpayer() -> Dict[str, Any]:
    """Fixture for Lucas LeBlanc (primary taxpayer) information.

    IRS ATS Test Scenario NR-1 - Nonresident alien from Canada
    filing Married Filing Separately using simplified refund method.

    ATS Reference SSN: 123-00-1111 (invalid for production validation)
    Test SSN: 123-01-1111 (valid format for testing validation logic)

    Note: Taxpayer has Form 4361 on file with IRS (minister exemption
    from self-employment tax).
    """
    return {
        "first_name": "Lucas",
        "last_name": "LeBlanc",
        "ssn": "123-01-1111",
        "ssn_clean": "123011111",
        "ssn_ats_reference": "123-00-1111",
        "address": {
            "street": "105 Yonge Street",
            "city": "Toronto",
            "state": "",  # Foreign address - no US state
            "zip": "",    # Foreign address - no US zip
        },
        "foreign_address": {
            "country": "Canada",
            "province": "Ontario",
            "postal_code": "M4R-1A2",
        },
        "date_of_birth": date(1951, 3, 17),  # Age 74 in 2025
        "occupation": "Writer",
        "digital_assets": False,
        "is_nonresident_alien": True,
        "simplified_refund_method": True,
        "has_form_4361": True,  # Minister exemption from SE tax
        "signature_method": "self_select_pin",
    }


@pytest.fixture
def lucas_leblanc_w2_google() -> Dict[str, Any]:
    """Fixture for W-2 #1 from Google.

    Primary employment income from Google.
    """
    return {
        "employee_name": "Lucas LeBlanc",
        "employee_ssn": "123-01-1111",
        "employer_name": "Google",
        "employer_ein": "00-0000055",
        "employer_ein_clean": "000000055",
        "employer_ein_test": "12-3456055",
        "employer_address": {
            "street": "52 Henry Street",
            "city": "Detroit",
            "state": "MI",
            "zip": "48201"
        },
        # Box 1 - Wages, tips, other compensation
        "box_1_wages": Decimal("33255.00"),
        # Box 2 - Federal income tax withheld
        "box_2_federal_withholding": Decimal("4788.00"),
        # Box 3 - Social security wages
        "box_3_ss_wages": Decimal("33255.00"),
        # Box 4 - Social security tax withheld
        "box_4_ss_tax": Decimal("2062.00"),
        # Box 5 - Medicare wages and tips
        "box_5_medicare_wages": Decimal("33255.00"),
        # Box 6 - Medicare tax withheld
        "box_6_medicare_tax": Decimal("482.00"),
        # Boxes 15-20 - State/local (not applicable for nonresident)
        "box_15_state": "",
        "box_16_state_wages": Decimal("0.00"),
        "box_17_state_tax": Decimal("0.00"),
    }


@pytest.fixture
def lucas_leblanc_w2_children_of_god() -> Dict[str, Any]:
    """Fixture for W-2 #2 from Children of God.

    Secondary employment income - possibly church/ministry related
    (supporting Form 4361 exemption).
    """
    return {
        "employee_name": "Lucas LeBlanc",
        "employee_ssn": "123-01-1111",
        "employer_name": "Children of God",
        "employer_ein": "00-0000013",
        "employer_ein_clean": "000000013",
        "employer_ein_test": "12-3456013",
        "employer_address": {
            "street": "107 West Lake Street",
            "city": "Detroit",
            "state": "MI",
            "zip": "48201"
        },
        # Box 1 - Wages, tips, other compensation
        "box_1_wages": Decimal("600.00"),
        # Box 2 - Federal income tax withheld
        "box_2_federal_withholding": Decimal("0.00"),
        # Box 3 - Social security wages
        "box_3_ss_wages": Decimal("600.00"),
        # Box 4 - Social security tax withheld
        "box_4_ss_tax": Decimal("37.00"),
        # Box 5 - Medicare wages and tips
        "box_5_medicare_wages": Decimal("600.00"),
        # Box 6 - Medicare tax withheld
        "box_6_medicare_tax": Decimal("9.00"),
        # Boxes 15-20 - State/local (not applicable)
        "box_15_state": "",
        "box_16_state_wages": Decimal("0.00"),
        "box_17_state_tax": Decimal("0.00"),
    }


@pytest.fixture
def lucas_leblanc_schedule_c() -> Dict[str, Any]:
    """Fixture for Schedule C (Profit or Loss From Business).

    Self-employment as an independent writer.
    Business code 711510 - Independent artists, writers, and performers.
    """
    return {
        "business_name": "",  # No separate business name
        "principal_business": "Independent Writer",
        "business_code": "711510",
        "business_address": {
            "street": "105 Yonge Street",
            "city": "Toronto",
            "country": "Canada",
            "postal_code": "M4R-1A2"
        },
        "employer_ein": "00-9999999",  # Placeholder EIN
        "accounting_method": "cash",
        "material_participation": True,
        "started_in_2025": False,

        # Part I - Income
        "line_1_gross_receipts": Decimal("27355.00"),
        "line_2_returns_allowances": Decimal("0.00"),
        "line_3_gross_receipts_net": Decimal("27355.00"),
        "line_4_cost_of_goods_sold": Decimal("0.00"),
        "line_5_gross_profit": Decimal("27355.00"),
        "line_6_other_income": Decimal("0.00"),
        "line_7_gross_income": Decimal("27355.00"),

        # Part II - Expenses
        "line_8_advertising": Decimal("150.00"),
        "line_9_car_truck": Decimal("0.00"),
        "line_10_commissions_fees": Decimal("0.00"),
        "line_11_contract_labor": Decimal("0.00"),
        "line_12_depletion": Decimal("0.00"),
        "line_13_depreciation": Decimal("0.00"),
        "line_14_employee_benefits": Decimal("0.00"),
        "line_15_insurance": Decimal("0.00"),
        "line_16a_mortgage_interest": Decimal("0.00"),
        "line_16b_other_interest": Decimal("0.00"),
        "line_17_legal_professional": Decimal("0.00"),
        "line_18_office_expense": Decimal("100.00"),
        "line_19_pension_profit_sharing": Decimal("0.00"),
        "line_20a_rent_vehicles": Decimal("0.00"),
        "line_20b_rent_other": Decimal("0.00"),
        "line_21_repairs_maintenance": Decimal("0.00"),
        "line_22_supplies": Decimal("300.00"),
        "line_23_taxes_licenses": Decimal("125.00"),
        "line_24a_travel": Decimal("0.00"),
        "line_24b_meals": Decimal("0.00"),
        "line_25_utilities": Decimal("0.00"),
        "line_26_wages": Decimal("0.00"),
        "line_27a_energy_deduction": Decimal("0.00"),
        "line_27b_other_expenses": Decimal("0.00"),

        # Line 28 - Total expenses
        "line_28_total_expenses": Decimal("675.00"),  # 150+100+300+125

        # Line 29 - Tentative profit
        "line_29_tentative_profit": Decimal("26680.00"),  # 27355 - 675

        # Line 30 - Home office deduction
        "line_30_home_office": Decimal("0.00"),

        # Line 31 - Net profit
        "line_31_net_profit": Decimal("26680.00"),
    }


@pytest.fixture
def lucas_leblanc_schedule_se() -> Dict[str, Any]:
    """Fixture for Schedule SE (Self-Employment Tax).

    Note: Taxpayer has Form 4361 on file (minister exemption).
    This exempts self-employment income from SE tax.
    """
    return {
        # Form 4361 exemption
        "has_form_4361": True,
        "is_minister": True,

        # Line 2 - Net profit from Schedule C
        "line_2_net_profit": Decimal("26680.00"),

        # Line 3 - Combined net earnings
        "line_3_combined": Decimal("26680.00"),

        # Line 4a - 92.35% of line 3
        "line_4a_net_earnings": Decimal("24639.08"),  # 26680 * 0.9235

        # Due to Form 4361 exemption, no SE tax is calculated
        "se_tax_exempt": True,
        "line_12_se_tax": Decimal("0.00"),
        "line_13_deduction": Decimal("0.00"),
    }


@pytest.fixture
def lucas_leblanc_ira_info() -> Dict[str, Any]:
    """Fixture for IRA distribution information.

    Traditional IRA with required minimum distribution.
    Distribution is not taxable per scenario instructions.

    Note: Taxpayer is 74 years old (born 3/17/1951), so RMD applies.
    """
    return {
        # IRA account info
        "account_type": "Traditional IRA",
        "has_rmd": True,

        # Required Minimum Distribution (RMD)
        "rmd_amount": Decimal("10000.00"),

        # Actual distribution taken
        "distribution_amount": Decimal("6500.00"),

        # Form 1040-NR Line 4
        "line_4a_ira_distributions": Decimal("6500.00"),
        "line_4b_taxable_amount": Decimal("0.00"),  # Not taxable per scenario

        # Shortfall for Form 5329
        "rmd_shortfall": Decimal("3500.00"),  # 10000 - 6500

        # Form 4361 affects IRA taxation
        "form_4361_exemption": True,
    }


@pytest.fixture
def lucas_leblanc_form_5329() -> Dict[str, Any]:
    """Fixture for Form 5329 (Additional Taxes on Qualified Plans).

    Part IX - Additional Tax on Excess Accumulation.
    Taxpayer did not receive full RMD.
    """
    return {
        # Part IX - Excess Accumulation
        "line_52b_minimum_required": Decimal("10000.00"),  # RMD
        "line_53b_amount_distributed": Decimal("6500.00"),  # Actual distribution

        # Shortfall
        "rmd_shortfall": Decimal("3500.00"),  # 10000 - 6500

        # Penalty calculation (25% of shortfall)
        # Note: Reduced from 50% to 25% per SECURE 2.0 Act for 2023+
        "penalty_rate": Decimal("0.25"),
        "line_54b_penalty": Decimal("875.00"),  # 3500 * 0.25

        # Total from Part IX
        "line_55_total": Decimal("875.00"),
    }


@pytest.fixture
def lucas_leblanc_schedule_1() -> Dict[str, Any]:
    """Fixture for Schedule 1 (Additional Income and Adjustments).

    Part I - Additional Income
    Part II - Adjustments to Income
    """
    return {
        # Part I - Additional Income
        "line_3_business_income": Decimal("26680.00"),  # From Schedule C
        "line_10_total_additional_income": Decimal("26680.00"),

        # Part II - Adjustments to Income
        "line_15_se_tax_deduction": Decimal("0.00"),  # Form 4361 exemption
        "line_26_total_adjustments": Decimal("0.00"),
    }


@pytest.fixture
def lucas_leblanc_schedule_2() -> Dict[str, Any]:
    """Fixture for Schedule 2 (Additional Taxes).

    Part I - Tax (AMT, etc.)
    Part II - Other Taxes (SE tax, Form 5329, etc.)
    """
    return {
        # Part I - Tax
        "line_1z_additions": Decimal("0.00"),
        "line_2_amt": Decimal("0.00"),
        "line_3_total": Decimal("0.00"),

        # Part II - Other Taxes
        "line_4_se_tax": Decimal("0.00"),  # Form 4361 exemption
        "line_8_form_5329": Decimal("875.00"),  # From Form 5329
        "line_21_total_other_taxes": Decimal("875.00"),
    }


@pytest.fixture
def lucas_leblanc_form_1040nr_data(
    lucas_leblanc_taxpayer,
    lucas_leblanc_w2_google,
    lucas_leblanc_w2_children_of_god,
    lucas_leblanc_schedule_c,
    lucas_leblanc_schedule_se,
    lucas_leblanc_ira_info,
    lucas_leblanc_form_5329,
    lucas_leblanc_schedule_1,
    lucas_leblanc_schedule_2
) -> Dict[str, Any]:
    """Fixture for complete Form 1040-NR data for Lucas LeBlanc.

    Tax Year: 2025
    Filing Status: Married Filing Separately (MFS)

    Note: Nonresident aliens cannot claim standard deduction
    (except certain residents of India per US-India tax treaty).
    They must itemize deductions.
    """
    # W-2 income totals
    w2_wages_total = (
        lucas_leblanc_w2_google["box_1_wages"] +
        lucas_leblanc_w2_children_of_god["box_1_wages"]
    )
    w2_federal_withholding = (
        lucas_leblanc_w2_google["box_2_federal_withholding"] +
        lucas_leblanc_w2_children_of_god["box_2_federal_withholding"]
    )

    # Schedule C income
    schedule_c_profit = lucas_leblanc_schedule_c["line_31_net_profit"]

    # Total effectively connected income (Line 9)
    # For 1040-NR: wages + business income (no IRA since not taxable)
    total_eci = w2_wages_total + schedule_c_profit
    # IRA distributions are on line 4 but not taxable
    ira_distributions = lucas_leblanc_ira_info["line_4a_ira_distributions"]
    ira_taxable = lucas_leblanc_ira_info["line_4b_taxable_amount"]

    # Line 1z - Total wages
    line_1z_wages = w2_wages_total  # $33,855

    # Line 8 - Additional income from Schedule 1
    line_8_schedule_1 = lucas_leblanc_schedule_1["line_10_total_additional_income"]

    # Line 9 - Total effectively connected income
    line_9_total_eci = line_1z_wages + ira_taxable + line_8_schedule_1

    # Line 10 - Adjustments
    line_10_adjustments = lucas_leblanc_schedule_1["line_26_total_adjustments"]

    # Line 11a - Adjusted Gross Income
    line_11a_agi = line_9_total_eci - line_10_adjustments

    # Line 12 - Itemized deductions (or standard for India residents)
    # Nonresident aliens generally cannot use standard deduction
    # Assuming no itemized deductions for this scenario
    line_12_deduction = Decimal("0.00")

    # Line 13a - QBI deduction
    line_13a_qbi = Decimal("0.00")

    # Line 14 - Total deductions
    line_14_total_deductions = line_12_deduction + line_13a_qbi

    # Line 15 - Taxable income
    line_15_taxable_income = max(Decimal("0"), line_11a_agi - line_14_total_deductions)

    # Line 16 - Tax (using MFS tax brackets)
    # 2025 MFS brackets (same as Single):
    # $0 - $11,600: 10%
    # $11,601 - $47,150: 12%
    # $47,151 - $100,525: 22%
    # $100,526 - $191,950: 24%
    taxable = line_15_taxable_income
    if taxable <= Decimal("11600"):
        line_16_tax = taxable * Decimal("0.10")
    elif taxable <= Decimal("47150"):
        line_16_tax = (Decimal("11600") * Decimal("0.10") +
                       (taxable - Decimal("11600")) * Decimal("0.12"))
    elif taxable <= Decimal("100525"):
        line_16_tax = (Decimal("11600") * Decimal("0.10") +
                       Decimal("35550") * Decimal("0.12") +
                       (taxable - Decimal("47150")) * Decimal("0.22"))
    else:
        line_16_tax = (Decimal("11600") * Decimal("0.10") +
                       Decimal("35550") * Decimal("0.12") +
                       Decimal("53375") * Decimal("0.22") +
                       (taxable - Decimal("100525")) * Decimal("0.24"))

    line_16_tax = line_16_tax.quantize(Decimal("1"))  # Round to whole dollar

    # Line 17 - Schedule 2, line 3
    line_17_schedule_2 = lucas_leblanc_schedule_2["line_3_total"]

    # Line 18 - Add lines 16 and 17
    line_18_total = line_16_tax + line_17_schedule_2

    # Lines 19-22 - Credits (none for this scenario)
    line_19_ctc = Decimal("0")
    line_20_schedule_3 = Decimal("0")
    line_21_credits = line_19_ctc + line_20_schedule_3
    line_22_tax_minus_credits = max(Decimal("0"), line_18_total - line_21_credits)

    # Line 23 - Other taxes (Schedule 2 line 21 for SE tax, Form 5329)
    line_23b_other_taxes = lucas_leblanc_schedule_2["line_21_total_other_taxes"]
    line_23d_total_other = line_23b_other_taxes

    # Line 24 - Total tax
    line_24_total_tax = line_22_tax_minus_credits + line_23d_total_other

    # Line 25 - Federal income tax withheld
    line_25a_w2_withholding = w2_federal_withholding
    line_25d_total_withholding = line_25a_w2_withholding

    # Line 33 - Total payments
    line_33_total_payments = line_25d_total_withholding

    # Refund or Amount Owed
    if line_33_total_payments > line_24_total_tax:
        line_34_overpaid = line_33_total_payments - line_24_total_tax
        line_37_amount_owed = Decimal("0")
    else:
        line_34_overpaid = Decimal("0")
        line_37_amount_owed = line_24_total_tax - line_33_total_payments

    return {
        # Taxpayer info
        "form_type": "1040-NR",
        "tax_year": 2025,
        "primary_ssn": lucas_leblanc_taxpayer["ssn_clean"],
        "primary_first_name": lucas_leblanc_taxpayer["first_name"],
        "primary_last_name": lucas_leblanc_taxpayer["last_name"],
        "address": lucas_leblanc_taxpayer["address"],
        "foreign_address": lucas_leblanc_taxpayer["foreign_address"],
        "filing_status": 2,  # MFS on Form 1040-NR (code 2, not 3)
        "is_nonresident_alien": True,
        "simplified_refund_method": True,

        # Checkboxes
        "digital_assets": False,

        # No dependents
        "dependents": [],

        # Income Section (Lines 1-9)
        "line_1a_w2_wages": w2_wages_total,
        "line_1z_total_wages": line_1z_wages,
        "line_4a_ira_distributions": ira_distributions,
        "line_4b_taxable_ira": ira_taxable,
        "line_8_schedule_1": line_8_schedule_1,
        "line_9_total_eci": line_9_total_eci,

        # Adjustments (Line 10-11)
        "line_10_adjustments": line_10_adjustments,
        "line_11a_agi": line_11a_agi,
        "line_11b_agi": line_11a_agi,

        # Deductions (Lines 12-15)
        "line_12_deduction": line_12_deduction,
        "line_13a_qbi": line_13a_qbi,
        "line_14_total_deductions": line_14_total_deductions,
        "line_15_taxable_income": line_15_taxable_income,

        # Tax (Lines 16-24)
        "line_16_tax": line_16_tax,
        "line_17_schedule_2": line_17_schedule_2,
        "line_18_total": line_18_total,
        "line_19_ctc": line_19_ctc,
        "line_20_schedule_3": line_20_schedule_3,
        "line_21_credits": line_21_credits,
        "line_22_tax_minus_credits": line_22_tax_minus_credits,
        "line_23b_other_taxes": line_23b_other_taxes,
        "line_23d_total_other": line_23d_total_other,
        "line_24_total_tax": line_24_total_tax,

        # Payments (Lines 25-33)
        "line_25a_w2_withholding": line_25a_w2_withholding,
        "line_25d_total_withholding": line_25d_total_withholding,
        "line_33_total_payments": line_33_total_payments,

        # Refund/Amount Owed (Lines 34-37)
        "line_34_overpaid": line_34_overpaid,
        "line_35a_refund": line_34_overpaid,
        "line_37_amount_owed": line_37_amount_owed,

        # Summary values
        "total_income": line_9_total_eci,
        "agi": line_11a_agi,
        "taxable_income": line_15_taxable_income,
        "total_tax": line_24_total_tax,
        "total_payments": line_33_total_payments,
        "refund": line_34_overpaid,
        "amount_owed": line_37_amount_owed,

        # Attached forms/schedules
        "has_schedule_1": True,
        "has_schedule_2": True,
        "has_schedule_c": True,
        "has_schedule_se": True,
        "has_form_5329": True,
        "w2_count": 2,

        # Detailed form data
        "w2_google": lucas_leblanc_w2_google,
        "w2_children_of_god": lucas_leblanc_w2_children_of_god,
        "schedule_c": lucas_leblanc_schedule_c,
        "schedule_se": lucas_leblanc_schedule_se,
        "ira_info": lucas_leblanc_ira_info,
        "form_5329": lucas_leblanc_form_5329,
        "schedule_1": lucas_leblanc_schedule_1,
        "schedule_2": lucas_leblanc_schedule_2,
    }


# =============================================================================
# TEST CLASS: Taxpayer Information
# =============================================================================


class TestTaxpayerInformation:
    """Tests for taxpayer information."""

    def test_taxpayer_name(self, lucas_leblanc_taxpayer):
        """Test taxpayer name."""
        assert lucas_leblanc_taxpayer["first_name"] == "Lucas"
        assert lucas_leblanc_taxpayer["last_name"] == "LeBlanc"

    def test_taxpayer_ssn(self, lucas_leblanc_taxpayer):
        """Test taxpayer SSN format."""
        ssn_clean = lucas_leblanc_taxpayer["ssn_clean"]
        assert len(ssn_clean) == 9
        assert ssn_clean.isdigit()

    def test_taxpayer_is_nonresident_alien(self, lucas_leblanc_taxpayer):
        """Test taxpayer is flagged as nonresident alien."""
        assert lucas_leblanc_taxpayer["is_nonresident_alien"] is True

    def test_foreign_address(self, lucas_leblanc_taxpayer):
        """Test foreign address components."""
        foreign = lucas_leblanc_taxpayer["foreign_address"]
        assert foreign["country"] == "Canada"
        assert foreign["province"] == "Ontario"
        assert foreign["postal_code"] == "M4R-1A2"

    def test_has_form_4361(self, lucas_leblanc_taxpayer):
        """Test Form 4361 exemption flag."""
        assert lucas_leblanc_taxpayer["has_form_4361"] is True

    def test_taxpayer_age(self, lucas_leblanc_taxpayer):
        """Test taxpayer age calculation (74 in 2025)."""
        dob = lucas_leblanc_taxpayer["date_of_birth"]
        age_in_2025 = 2025 - dob.year
        if dob.month > 12 or (dob.month == 12 and dob.day > 31):
            age_in_2025 -= 1
        assert age_in_2025 == 74


# =============================================================================
# TEST CLASS: W-2 Income
# =============================================================================


class TestW2Income:
    """Tests for W-2 wage income."""

    def test_google_wages(self, lucas_leblanc_w2_google):
        """Test Google W-2 wages."""
        assert lucas_leblanc_w2_google["box_1_wages"] == Decimal("33255.00")

    def test_google_withholding(self, lucas_leblanc_w2_google):
        """Test Google W-2 federal withholding."""
        assert lucas_leblanc_w2_google["box_2_federal_withholding"] == Decimal("4788.00")

    def test_google_ss_wages(self, lucas_leblanc_w2_google):
        """Test Google W-2 Social Security wages."""
        assert lucas_leblanc_w2_google["box_3_ss_wages"] == Decimal("33255.00")

    def test_children_of_god_wages(self, lucas_leblanc_w2_children_of_god):
        """Test Children of God W-2 wages."""
        assert lucas_leblanc_w2_children_of_god["box_1_wages"] == Decimal("600.00")

    def test_children_of_god_no_withholding(self, lucas_leblanc_w2_children_of_god):
        """Test Children of God W-2 has no federal withholding."""
        assert lucas_leblanc_w2_children_of_god["box_2_federal_withholding"] == Decimal("0.00")

    def test_total_w2_wages(self, lucas_leblanc_w2_google, lucas_leblanc_w2_children_of_god):
        """Test total W-2 wages from both employers."""
        total = (lucas_leblanc_w2_google["box_1_wages"] +
                 lucas_leblanc_w2_children_of_god["box_1_wages"])
        assert total == Decimal("33855.00")

    def test_total_federal_withholding(self, lucas_leblanc_w2_google, lucas_leblanc_w2_children_of_god):
        """Test total federal withholding."""
        total = (lucas_leblanc_w2_google["box_2_federal_withholding"] +
                 lucas_leblanc_w2_children_of_god["box_2_federal_withholding"])
        assert total == Decimal("4788.00")


# =============================================================================
# TEST CLASS: Schedule C (Business Income)
# =============================================================================


class TestScheduleC:
    """Tests for Schedule C business income."""

    def test_gross_receipts(self, lucas_leblanc_schedule_c):
        """Test gross receipts."""
        assert lucas_leblanc_schedule_c["line_1_gross_receipts"] == Decimal("27355.00")

    def test_business_expenses(self, lucas_leblanc_schedule_c):
        """Test business expenses calculation."""
        expected_expenses = (
            lucas_leblanc_schedule_c["line_8_advertising"] +  # 150
            lucas_leblanc_schedule_c["line_18_office_expense"] +  # 100
            lucas_leblanc_schedule_c["line_22_supplies"] +  # 300
            lucas_leblanc_schedule_c["line_23_taxes_licenses"]  # 125
        )
        assert expected_expenses == Decimal("675.00")
        assert lucas_leblanc_schedule_c["line_28_total_expenses"] == Decimal("675.00")

    def test_net_profit(self, lucas_leblanc_schedule_c):
        """Test net profit calculation."""
        expected = (lucas_leblanc_schedule_c["line_7_gross_income"] -
                    lucas_leblanc_schedule_c["line_28_total_expenses"])
        assert expected == Decimal("26680.00")
        assert lucas_leblanc_schedule_c["line_31_net_profit"] == expected

    def test_business_code(self, lucas_leblanc_schedule_c):
        """Test business code for writer."""
        assert lucas_leblanc_schedule_c["business_code"] == "711510"

    def test_accounting_method(self, lucas_leblanc_schedule_c):
        """Test accounting method is cash."""
        assert lucas_leblanc_schedule_c["accounting_method"] == "cash"


# =============================================================================
# TEST CLASS: Schedule SE (Self-Employment Tax)
# =============================================================================


class TestScheduleSE:
    """Tests for Schedule SE self-employment tax."""

    def test_form_4361_exemption(self, lucas_leblanc_schedule_se):
        """Test Form 4361 exemption is claimed."""
        assert lucas_leblanc_schedule_se["has_form_4361"] is True
        assert lucas_leblanc_schedule_se["se_tax_exempt"] is True

    def test_net_profit_from_schedule_c(self, lucas_leblanc_schedule_se, lucas_leblanc_schedule_c):
        """Test Schedule C profit flows to Schedule SE."""
        assert (lucas_leblanc_schedule_se["line_2_net_profit"] ==
                lucas_leblanc_schedule_c["line_31_net_profit"])

    def test_se_tax_is_zero(self, lucas_leblanc_schedule_se):
        """Test SE tax is zero due to Form 4361 exemption."""
        assert lucas_leblanc_schedule_se["line_12_se_tax"] == Decimal("0.00")

    def test_se_deduction_is_zero(self, lucas_leblanc_schedule_se):
        """Test SE deduction is zero due to exemption."""
        assert lucas_leblanc_schedule_se["line_13_deduction"] == Decimal("0.00")


# =============================================================================
# TEST CLASS: IRA Distribution
# =============================================================================


class TestIRADistribution:
    """Tests for IRA distribution handling."""

    def test_ira_distribution_amount(self, lucas_leblanc_ira_info):
        """Test IRA distribution amount."""
        assert lucas_leblanc_ira_info["distribution_amount"] == Decimal("6500.00")

    def test_ira_not_taxable(self, lucas_leblanc_ira_info):
        """Test IRA distribution is not taxable per scenario."""
        assert lucas_leblanc_ira_info["line_4b_taxable_amount"] == Decimal("0.00")

    def test_rmd_requirement(self, lucas_leblanc_ira_info):
        """Test RMD amount."""
        assert lucas_leblanc_ira_info["rmd_amount"] == Decimal("10000.00")

    def test_rmd_shortfall(self, lucas_leblanc_ira_info):
        """Test RMD shortfall calculation."""
        expected = (lucas_leblanc_ira_info["rmd_amount"] -
                    lucas_leblanc_ira_info["distribution_amount"])
        assert expected == Decimal("3500.00")
        assert lucas_leblanc_ira_info["rmd_shortfall"] == expected


# =============================================================================
# TEST CLASS: Form 5329 (Additional Taxes)
# =============================================================================


class TestForm5329:
    """Tests for Form 5329 additional taxes."""

    def test_rmd_shortfall_penalty(self, lucas_leblanc_form_5329):
        """Test RMD shortfall penalty calculation."""
        shortfall = lucas_leblanc_form_5329["rmd_shortfall"]
        rate = lucas_leblanc_form_5329["penalty_rate"]
        expected_penalty = shortfall * rate

        assert shortfall == Decimal("3500.00")
        assert rate == Decimal("0.25")  # SECURE 2.0 reduced rate
        assert expected_penalty == Decimal("875.00")
        assert lucas_leblanc_form_5329["line_54b_penalty"] == expected_penalty

    def test_secure_20_penalty_rate(self, lucas_leblanc_form_5329):
        """Test SECURE 2.0 Act reduced penalty rate (25% vs old 50%)."""
        assert lucas_leblanc_form_5329["penalty_rate"] == Decimal("0.25")


# =============================================================================
# TEST CLASS: Form 1040-NR Tax Calculation
# =============================================================================


class TestForm1040NRTaxCalculation:
    """Tests for Form 1040-NR tax calculations."""

    def test_form_type(self, lucas_leblanc_form_1040nr_data):
        """Test form type is 1040-NR."""
        assert lucas_leblanc_form_1040nr_data["form_type"] == "1040-NR"

    def test_filing_status_mfs(self, lucas_leblanc_form_1040nr_data):
        """Test filing status is MFS."""
        assert lucas_leblanc_form_1040nr_data["filing_status"] == 2  # MFS on 1040-NR

    def test_total_wages(self, lucas_leblanc_form_1040nr_data):
        """Test total wages on line 1z."""
        assert lucas_leblanc_form_1040nr_data["line_1z_total_wages"] == Decimal("33855.00")

    def test_agi_calculation(self, lucas_leblanc_form_1040nr_data):
        """Test AGI calculation."""
        # AGI = Total ECI (wages + business income) - adjustments
        expected_agi = (
            lucas_leblanc_form_1040nr_data["line_1z_total_wages"] +  # W-2 wages
            lucas_leblanc_form_1040nr_data["line_4b_taxable_ira"] +  # IRA taxable (0)
            lucas_leblanc_form_1040nr_data["line_8_schedule_1"]  # Schedule C income
        )
        assert lucas_leblanc_form_1040nr_data["line_11a_agi"] == expected_agi

    def test_no_standard_deduction_for_nra(self, lucas_leblanc_form_1040nr_data):
        """Test nonresident aliens cannot use standard deduction."""
        # NRAs generally cannot use standard deduction
        # (except India treaty residents)
        assert lucas_leblanc_form_1040nr_data["line_12_deduction"] == Decimal("0.00")

    def test_taxable_income(self, lucas_leblanc_form_1040nr_data):
        """Test taxable income equals AGI for NRA with no deductions."""
        assert (lucas_leblanc_form_1040nr_data["line_15_taxable_income"] ==
                lucas_leblanc_form_1040nr_data["line_11a_agi"])

    def test_other_taxes_include_form_5329(self, lucas_leblanc_form_1040nr_data):
        """Test other taxes include Form 5329 penalty."""
        assert lucas_leblanc_form_1040nr_data["line_23b_other_taxes"] == Decimal("875.00")


# =============================================================================
# TEST CLASS: XML Serialization
# =============================================================================


class TestScenarioNR1XMLSerialization:
    """Tests for XML serialization of Scenario NR-1 data."""

    def test_taxpayer_info_creation(self, lucas_leblanc_taxpayer):
        """Test TaxpayerInfo object creation."""
        taxpayer_info = TaxpayerInfo(
            primary_ssn=lucas_leblanc_taxpayer["ssn_clean"],
            primary_first_name=lucas_leblanc_taxpayer["first_name"],
            primary_last_name=lucas_leblanc_taxpayer["last_name"],
            primary_date_of_birth=lucas_leblanc_taxpayer["date_of_birth"],
        )

        assert taxpayer_info.primary_ssn == "123011111"
        assert taxpayer_info.primary_first_name == "Lucas"
        assert taxpayer_info.primary_last_name == "LeBlanc"

    def test_submission_id_generation(self):
        """Test MeF submission ID generation."""
        submission_id = SubmissionId.generate(efin="123456", sequence=1)

        assert len(submission_id.submission_id) == 20
        assert submission_id.submission_id.isdigit()

    def test_foreign_address_xml_escape(self, lucas_leblanc_taxpayer):
        """Test foreign address characters are properly escaped."""
        # M4R-1A2 should be safe, but test escape function
        postal_code = lucas_leblanc_taxpayer["foreign_address"]["postal_code"]
        escaped = escape_xml(postal_code)
        assert escaped == "M4R-1A2"


# =============================================================================
# TEST CLASS: Business Rules Validation
# =============================================================================


class TestScenarioNR1BusinessRules:
    """Tests for business rules validation of Scenario NR-1 data."""

    def test_nra_uses_1040nr(self, lucas_leblanc_form_1040nr_data):
        """Test nonresident alien files Form 1040-NR."""
        assert lucas_leblanc_form_1040nr_data["form_type"] == "1040-NR"
        assert lucas_leblanc_form_1040nr_data["is_nonresident_alien"] is True

    def test_form_4361_exempts_se_tax(self, lucas_leblanc_schedule_se):
        """Test Form 4361 exempts self-employment tax."""
        assert lucas_leblanc_schedule_se["has_form_4361"] is True
        assert lucas_leblanc_schedule_se["line_12_se_tax"] == Decimal("0.00")

    def test_rmd_penalty_applied(self, lucas_leblanc_form_1040nr_data):
        """Test RMD shortfall penalty is included in total tax."""
        form_5329_penalty = lucas_leblanc_form_1040nr_data["form_5329"]["line_54b_penalty"]
        other_taxes = lucas_leblanc_form_1040nr_data["line_23b_other_taxes"]

        assert form_5329_penalty == Decimal("875.00")
        assert other_taxes >= form_5329_penalty


# =============================================================================
# TEST CLASS: Integration Tests
# =============================================================================


class TestScenarioNR1Integration:
    """Integration tests for the complete Scenario NR-1 data."""

    def test_complete_form_1040nr_structure(self, lucas_leblanc_form_1040nr_data):
        """Test complete form data has all required fields."""
        required_fields = [
            "form_type", "tax_year", "primary_ssn",
            "primary_first_name", "primary_last_name",
            "filing_status", "is_nonresident_alien",
            "total_income", "agi", "taxable_income",
            "total_tax", "total_payments",
        ]

        for field in required_fields:
            assert field in lucas_leblanc_form_1040nr_data, f"Missing field: {field}"

    def test_schedule_c_flows_to_schedule_1(
        self,
        lucas_leblanc_schedule_c,
        lucas_leblanc_schedule_1
    ):
        """Test Schedule C profit flows to Schedule 1."""
        assert (lucas_leblanc_schedule_c["line_31_net_profit"] ==
                lucas_leblanc_schedule_1["line_3_business_income"])

    def test_schedule_1_flows_to_1040nr(
        self,
        lucas_leblanc_schedule_1,
        lucas_leblanc_form_1040nr_data
    ):
        """Test Schedule 1 flows to Form 1040-NR line 8."""
        assert (lucas_leblanc_schedule_1["line_10_total_additional_income"] ==
                lucas_leblanc_form_1040nr_data["line_8_schedule_1"])

    def test_form_5329_flows_to_schedule_2(
        self,
        lucas_leblanc_form_5329,
        lucas_leblanc_schedule_2
    ):
        """Test Form 5329 penalty flows to Schedule 2."""
        assert (lucas_leblanc_form_5329["line_55_total"] ==
                lucas_leblanc_schedule_2["line_8_form_5329"])

    def test_schedule_2_flows_to_1040nr(
        self,
        lucas_leblanc_schedule_2,
        lucas_leblanc_form_1040nr_data
    ):
        """Test Schedule 2 flows to Form 1040-NR line 23b."""
        assert (lucas_leblanc_schedule_2["line_21_total_other_taxes"] ==
                lucas_leblanc_form_1040nr_data["line_23b_other_taxes"])

    def test_w2_withholding_flows_to_payments(self, lucas_leblanc_form_1040nr_data):
        """Test W-2 withholding flows to payments section."""
        w2_wh = (lucas_leblanc_form_1040nr_data["w2_google"]["box_2_federal_withholding"] +
                 lucas_leblanc_form_1040nr_data["w2_children_of_god"]["box_2_federal_withholding"])
        assert lucas_leblanc_form_1040nr_data["line_25a_w2_withholding"] == w2_wh

    def test_refund_or_owed_calculation(self, lucas_leblanc_form_1040nr_data):
        """Test refund/amount owed is correctly calculated."""
        payments = lucas_leblanc_form_1040nr_data["total_payments"]
        tax = lucas_leblanc_form_1040nr_data["total_tax"]
        refund = lucas_leblanc_form_1040nr_data["refund"]
        owed = lucas_leblanc_form_1040nr_data["amount_owed"]

        if payments > tax:
            assert refund == payments - tax
            assert owed == Decimal("0")
        else:
            assert refund == Decimal("0")
            assert owed == tax - payments


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
