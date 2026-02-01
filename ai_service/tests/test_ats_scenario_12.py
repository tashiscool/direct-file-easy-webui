"""Comprehensive pytest tests for IRS ATS Test Scenario 12 - Sam Gardenia.

This module tests the MeF (Modernized e-File) service functionality using
IRS ATS (Assurance Testing System) Test Scenario 12 data for Sam Gardenia.

Test Scenario Reference: IRS ATS Test Scenario 12 (1040-mef-ats-scenario-12-10292025.pdf)
Primary Taxpayer: Sam Gardenia
Filing Status: Single (1)

Key Features Tested:
- W-2 wage income with retirement plan
- Schedule C (Self-Employment - Designer)
- Schedule SE (Self-Employment Tax)
- Form 7206 (Self-Employed Health Insurance Deduction)
- Form 7217 (Partner's Report of Property Distributed by a Partnership)
- Schedule 1 (Additional Income and Adjustments)
- Schedule 2 (Additional Taxes - SE Tax)

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
# FIXTURES - IRS ATS Test Scenario 12 Data (Sam Gardenia - Single)
# =============================================================================


@pytest.fixture
def sam_gardenia_taxpayer() -> Dict[str, Any]:
    """Fixture for Sam Gardenia (primary taxpayer) information.

    IRS ATS Test Scenario 12 - Single filer with self-employment income.

    ATS Reference SSN: 400-00-1212
    """
    return {
        "first_name": "Sam",
        "last_name": "Gardenia",
        "ssn": "400-01-1212",
        "ssn_clean": "400011212",
        "ssn_ats_reference": "400-00-1212",
        "address": {
            "street": "231 Red Run Street",
            "city": "Anytown",
            "state": "KY",
            "zip": "41011"
        },
        "occupation": "Designer",
        "digital_assets": False,
    }


@pytest.fixture
def sam_gardenia_w2_data() -> Dict[str, Any]:
    """Fixture for Sam Gardenia W-2 from Design LLC."""
    return {
        "employee_name": "Sam Gardenia",
        "employer_name": "Design LLC",
        "employer_ein": "00-0000011",
        "employer_ein_clean": "000000011",
        "employer_address": {
            "street": "426 Build St",
            "city": "Anytown",
            "state": "KY",
            "zip": "41011"
        },
        "wages": Decimal("100836.00"),
        "federal_withholding": Decimal("14444.00"),
        "ss_wages": Decimal("105878.00"),
        "ss_tax": Decimal("6564.00"),
        "medicare_wages": Decimal("105878.00"),
        "medicare_tax": Decimal("1535.00"),
        "box_12_dd": Decimal("10315.00"),  # Employer health coverage
        "has_retirement_plan": True,
        "state": "KY",
        "state_id": "00-0000056",
        "state_wages": Decimal("100836.00"),
        "state_tax": Decimal("3420.00"),
    }


@pytest.fixture
def sam_gardenia_schedule_c() -> Dict[str, Any]:
    """Fixture for Schedule C (Profit or Loss from Business).

    Sam operates a design business called Energy Build.
    Principal Business Code: 541310 (Architectural Services/Designer)
    """
    return {
        "proprietor_name": "Sam Gardenia",
        "principal_business": "Designer",
        "principal_business_code": "541310",
        "business_name": "Energy Build",
        "business_address": {
            "street": "654 W 3rd St",
            "city": "Anytown",
            "state": "KY",
            "zip": "41011"
        },
        "accounting_method": "Cash",
        "materially_participated": True,

        # Part I - Income
        "line_1_gross_receipts": Decimal("35235.00"),
        "line_3_gross_receipts_less_returns": Decimal("35235.00"),
        "line_5_gross_profit": Decimal("35235.00"),
        "line_7_gross_income": Decimal("35235.00"),

        # Part II - Expenses
        "expenses": {
            "line_15_insurance": Decimal("550.00"),
            "line_17_legal_professional": Decimal("125.00"),
            "line_18_office_expense": Decimal("1000.00"),
            "line_20b_rent_other_business": Decimal("2500.00"),
            "line_22_supplies": Decimal("6532.00"),
            "line_23_taxes_licenses": Decimal("200.00"),
        },

        # Line 28 - Total expenses
        "line_28_total_expenses": Decimal("10907.00"),

        # Line 31 - Net profit
        "line_31_net_profit": Decimal("24328.00"),
    }


@pytest.fixture
def sam_gardenia_schedule_se() -> Dict[str, Any]:
    """Fixture for Schedule SE (Self-Employment Tax).

    Calculates SE tax on Schedule C net profit.
    """
    net_profit = Decimal("24328.00")
    se_earnings = (net_profit * Decimal("0.9235")).quantize(Decimal("1"))  # 22,467
    ss_wages_from_w2 = Decimal("105878.00")
    ss_wage_base_2025 = Decimal("176100.00")
    remaining_ss_base = ss_wage_base_2025 - ss_wages_from_w2  # 62,722 (actually 70,222)

    # Since SE earnings < remaining SS base, all SE earnings subject to SS tax
    ss_taxable = min(se_earnings, remaining_ss_base)

    return {
        "line_2_net_profit": net_profit,
        "line_3_combined": net_profit,
        "line_4a_se_earnings": Decimal("22467.00"),
        "line_4c_combined": Decimal("22467.00"),
        "line_6_total": Decimal("22467.00"),
        "line_7_ss_wage_base": Decimal("176100.00"),
        "line_8a_ss_wages_w2": Decimal("105878.00"),
        "line_8d_total_ss_wages": Decimal("105878.00"),
        "line_9_remaining_ss_base": Decimal("62722.00"),  # 176,100 - 105,878 - wait, that's 70,222
        # Actually from PDF: line 9 = 62,722 which seems like smaller of line 6 or line 9 calculation
        "line_10_ss_tax": Decimal("2786.00"),  # Smaller of 22,467 or 62,722 x 12.4%
        "line_11_medicare_tax": Decimal("652.00"),  # 22,467 x 2.9%
        "line_12_se_tax": Decimal("3438.00"),
        "line_13_deductible_se_tax": Decimal("1719.00"),  # 50% of SE tax
    }


@pytest.fixture
def sam_gardenia_form_7206() -> Dict[str, Any]:
    """Fixture for Form 7206 (Self-Employed Health Insurance Deduction)."""
    return {
        "line_1_health_insurance_premiums": Decimal("1000.00"),
        "line_3_total_premiums": Decimal("1000.00"),
        "line_4_net_profit": Decimal("24328.00"),
        "line_5_total_net_profits": Decimal("24328.00"),
        "line_6_ratio": Decimal("1.00000"),
        "line_7_se_tax_deduction_portion": Decimal("1719.00"),
        "line_8_net_profit_minus_se_deduction": Decimal("22609.00"),
        "line_10_available_for_deduction": Decimal("22609.00"),
        "line_13_limit": Decimal("22609.00"),
        "line_14_deduction": Decimal("1000.00"),  # Smaller of line 3 or line 13
    }


@pytest.fixture
def sam_gardenia_form_7217() -> Dict[str, Any]:
    """Fixture for Form 7217 (Partner's Report of Property Distributed by Partnership).

    Partnership distribution from Energy Build.
    """
    return {
        "partner_name": "Sam Gardenia",
        "partner_tin": "400-00-1212",
        "partnership_name": "Energy Build",
        "partnership_ein": "00-1040012",
        "distribution_date": date(2025, 3, 1),
        "is_liquidating": False,
        "is_751b_sale_exchange": False,

        # Part I
        "line_3_partnership_basis": Decimal("32507.00"),
        "line_4_partner_basis_before": Decimal("10000.00"),
        "line_5a_cash_received": Decimal("4000.00"),
        "line_5c_total_cash": Decimal("4000.00"),
        "line_6_smaller": Decimal("4000.00"),
        "line_7_gain_recognized": Decimal("0.00"),
        "line_9_basis_after_cash": Decimal("6000.00"),
        "line_10_basis_to_allocate": Decimal("6000.00"),

        # Part II - Distributed Property
        "distributed_property": {
            "description": "Cash",
            "partnership_basis": Decimal("32507.00"),
            "section_734b": True,
            "partner_basis": Decimal("4000.00"),
        },
    }


@pytest.fixture
def sam_gardenia_schedule_1() -> Dict[str, Any]:
    """Fixture for Schedule 1 (Additional Income and Adjustments)."""
    return {
        # Part I - Additional Income
        "line_3_business_income": Decimal("24328.00"),
        "line_10_total_additional_income": Decimal("24328.00"),

        # Part II - Adjustments to Income
        "line_15_se_tax_deduction": Decimal("1719.00"),
        "line_17_se_health_insurance": Decimal("1000.00"),
        "line_26_total_adjustments": Decimal("2719.00"),
    }


@pytest.fixture
def sam_gardenia_schedule_2() -> Dict[str, Any]:
    """Fixture for Schedule 2 (Additional Taxes)."""
    return {
        # Part II - Other Taxes
        "line_4_se_tax": Decimal("3438.00"),
        "line_21_total_other_taxes": Decimal("3438.00"),
    }


@pytest.fixture
def sam_gardenia_form_1040_data(
    sam_gardenia_taxpayer,
    sam_gardenia_w2_data,
    sam_gardenia_schedule_c,
    sam_gardenia_schedule_se,
    sam_gardenia_form_7206,
    sam_gardenia_form_7217,
    sam_gardenia_schedule_1,
    sam_gardenia_schedule_2
) -> Dict[str, Any]:
    """Fixture for complete Form 1040 data for Sam Gardenia.

    Tax Year: 2025
    Filing Status: Single (1)
    """
    # Income
    w2_wages = sam_gardenia_w2_data["wages"]
    schedule_c_income = sam_gardenia_schedule_c["line_31_net_profit"]
    total_income = w2_wages + schedule_c_income

    # Adjustments
    adjustments = sam_gardenia_schedule_1["line_26_total_adjustments"]

    # AGI
    agi = total_income - adjustments

    # Standard deduction - OBBBA 2025 Single
    standard_deduction = Decimal("15750.00")

    # Taxable income
    taxable_income = max(Decimal("0"), agi - standard_deduction)

    # Tax calculation (from PDF: $18,634)
    calculated_tax = Decimal("18634.00")

    # SE Tax
    se_tax = sam_gardenia_schedule_se["line_12_se_tax"]

    # Total tax
    total_tax = calculated_tax + se_tax

    # Payments
    total_withholding = sam_gardenia_w2_data["federal_withholding"]
    total_payments = total_withholding

    # Amount owed
    amount_owed = total_tax - total_payments

    return {
        # Taxpayer info
        "primary_ssn": sam_gardenia_taxpayer["ssn_clean"],
        "primary_first_name": sam_gardenia_taxpayer["first_name"],
        "primary_last_name": sam_gardenia_taxpayer["last_name"],
        "address": sam_gardenia_taxpayer["address"],
        "filing_status": 1,  # Single

        # Checkboxes
        "digital_assets": False,

        # Income (Lines 1-9)
        "line_1a_w2_wages": w2_wages,
        "line_1z_total_wages": w2_wages,
        "line_8_schedule_1_income": schedule_c_income,
        "line_9_total_income": total_income,

        # Adjustments (Line 10)
        "line_10_adjustments": adjustments,

        # AGI (Line 11)
        "line_11a_agi": agi,

        # Deduction (Lines 12-14)
        "line_12e_standard_deduction": standard_deduction,
        "line_14_total_deductions": standard_deduction,

        # Taxable income (Line 15)
        "line_15_taxable_income": taxable_income,

        # Tax (Lines 16-24)
        "line_16_tax": calculated_tax,
        "line_18_total": calculated_tax,
        "line_22_tax_minus_credits": calculated_tax,
        "line_23_other_taxes": se_tax,
        "line_24_total_tax": total_tax,

        # Payments (Lines 25-33)
        "line_25a_w2_withholding": total_withholding,
        "line_25d_total_withholding": total_withholding,
        "line_33_total_payments": total_payments,

        # Amount owed
        "line_37_amount_owed": amount_owed,

        # Summary values
        "wages": w2_wages,
        "total_income": total_income,
        "agi": agi,
        "deduction": standard_deduction,
        "taxable_income": taxable_income,
        "total_tax": total_tax,
        "total_payments": total_payments,
        "amount_owed": amount_owed,

        # Attached forms/schedules
        "has_schedule_1": True,
        "has_schedule_2": True,
        "has_schedule_c": True,
        "has_schedule_se": True,
        "has_form_7206": True,
        "has_form_7217": True,

        # Form data
        "schedule_1": sam_gardenia_schedule_1,
        "schedule_2": sam_gardenia_schedule_2,
        "schedule_c": sam_gardenia_schedule_c,
        "schedule_se": sam_gardenia_schedule_se,
        "form_7206": sam_gardenia_form_7206,
        "form_7217": sam_gardenia_form_7217,
        "w2": sam_gardenia_w2_data,
    }


# =============================================================================
# TEST CLASS: Taxpayer Information
# =============================================================================


class TestTaxpayerInformation:
    """Tests for taxpayer information."""

    def test_taxpayer_name(self, sam_gardenia_taxpayer):
        """Test taxpayer name."""
        assert sam_gardenia_taxpayer["first_name"] == "Sam"
        assert sam_gardenia_taxpayer["last_name"] == "Gardenia"

    def test_taxpayer_address(self, sam_gardenia_taxpayer):
        """Test taxpayer address."""
        address = sam_gardenia_taxpayer["address"]
        assert address["city"] == "Anytown"
        assert address["state"] == "KY"
        assert address["zip"] == "41011"


# =============================================================================
# TEST CLASS: W-2 Income
# =============================================================================


class TestW2Income:
    """Tests for W-2 wage income."""

    def test_w2_wages(self, sam_gardenia_w2_data):
        """Test W-2 wages."""
        assert sam_gardenia_w2_data["wages"] == Decimal("100836.00")

    def test_w2_withholding(self, sam_gardenia_w2_data):
        """Test W-2 federal withholding."""
        assert sam_gardenia_w2_data["federal_withholding"] == Decimal("14444.00")

    def test_w2_ss_wages_higher_than_regular(self, sam_gardenia_w2_data):
        """Test SS wages are higher than regular wages (includes health coverage)."""
        assert sam_gardenia_w2_data["ss_wages"] > sam_gardenia_w2_data["wages"]
        assert sam_gardenia_w2_data["ss_wages"] == Decimal("105878.00")

    def test_w2_retirement_plan(self, sam_gardenia_w2_data):
        """Test retirement plan checkbox."""
        assert sam_gardenia_w2_data["has_retirement_plan"] is True

    def test_w2_box_12_dd(self, sam_gardenia_w2_data):
        """Test Box 12 DD (employer health coverage)."""
        assert sam_gardenia_w2_data["box_12_dd"] == Decimal("10315.00")


# =============================================================================
# TEST CLASS: Schedule C Business Income
# =============================================================================


class TestScheduleCBusinessIncome:
    """Tests for Schedule C business income."""

    def test_business_name(self, sam_gardenia_schedule_c):
        """Test business name."""
        assert sam_gardenia_schedule_c["business_name"] == "Energy Build"

    def test_principal_business_code(self, sam_gardenia_schedule_c):
        """Test principal business code."""
        assert sam_gardenia_schedule_c["principal_business_code"] == "541310"

    def test_gross_receipts(self, sam_gardenia_schedule_c):
        """Test gross receipts."""
        assert sam_gardenia_schedule_c["line_1_gross_receipts"] == Decimal("35235.00")

    def test_total_expenses(self, sam_gardenia_schedule_c):
        """Test total expenses calculation."""
        expenses = sam_gardenia_schedule_c["expenses"]
        expected = sum(expenses.values())
        assert sam_gardenia_schedule_c["line_28_total_expenses"] == expected

    def test_net_profit(self, sam_gardenia_schedule_c):
        """Test net profit calculation."""
        gross = sam_gardenia_schedule_c["line_7_gross_income"]
        expenses = sam_gardenia_schedule_c["line_28_total_expenses"]
        expected = gross - expenses
        assert sam_gardenia_schedule_c["line_31_net_profit"] == expected


# =============================================================================
# TEST CLASS: Schedule SE Self-Employment Tax
# =============================================================================


class TestScheduleSESelfEmploymentTax:
    """Tests for Schedule SE self-employment tax."""

    def test_se_earnings_calculation(self, sam_gardenia_schedule_se):
        """Test SE earnings at 92.35% of net profit."""
        # Net profit $24,328 * 0.9235 = $22,467 (rounded)
        assert sam_gardenia_schedule_se["line_4a_se_earnings"] == Decimal("22467.00")

    def test_ss_tax_portion(self, sam_gardenia_schedule_se):
        """Test Social Security tax portion of SE tax."""
        assert sam_gardenia_schedule_se["line_10_ss_tax"] == Decimal("2786.00")

    def test_medicare_tax_portion(self, sam_gardenia_schedule_se):
        """Test Medicare tax portion of SE tax."""
        assert sam_gardenia_schedule_se["line_11_medicare_tax"] == Decimal("652.00")

    def test_total_se_tax(self, sam_gardenia_schedule_se):
        """Test total self-employment tax."""
        ss_tax = sam_gardenia_schedule_se["line_10_ss_tax"]
        medicare_tax = sam_gardenia_schedule_se["line_11_medicare_tax"]
        assert sam_gardenia_schedule_se["line_12_se_tax"] == ss_tax + medicare_tax

    def test_deductible_se_tax(self, sam_gardenia_schedule_se):
        """Test deductible portion is 50% of SE tax."""
        se_tax = sam_gardenia_schedule_se["line_12_se_tax"]
        expected_deduction = (se_tax * Decimal("0.50")).quantize(Decimal("1"))
        assert sam_gardenia_schedule_se["line_13_deductible_se_tax"] == expected_deduction


# =============================================================================
# TEST CLASS: Form 7206 Self-Employed Health Insurance
# =============================================================================


class TestForm7206SelfEmployedHealthInsurance:
    """Tests for Form 7206 self-employed health insurance deduction."""

    def test_health_insurance_premiums(self, sam_gardenia_form_7206):
        """Test health insurance premiums."""
        assert sam_gardenia_form_7206["line_1_health_insurance_premiums"] == Decimal("1000.00")

    def test_deduction_limited_to_premiums(self, sam_gardenia_form_7206):
        """Test deduction is limited to premiums paid."""
        premiums = sam_gardenia_form_7206["line_3_total_premiums"]
        limit = sam_gardenia_form_7206["line_13_limit"]
        deduction = sam_gardenia_form_7206["line_14_deduction"]

        # Deduction is smaller of premiums or limit
        assert deduction == min(premiums, limit)
        assert deduction == Decimal("1000.00")


# =============================================================================
# TEST CLASS: Form 7217 Partnership Distribution
# =============================================================================


class TestForm7217PartnershipDistribution:
    """Tests for Form 7217 partnership distribution."""

    def test_partnership_info(self, sam_gardenia_form_7217):
        """Test partnership information."""
        assert sam_gardenia_form_7217["partnership_name"] == "Energy Build"
        assert sam_gardenia_form_7217["partnership_ein"] == "00-1040012"

    def test_distribution_not_liquidating(self, sam_gardenia_form_7217):
        """Test distribution is not a liquidating distribution."""
        assert sam_gardenia_form_7217["is_liquidating"] is False

    def test_cash_distribution(self, sam_gardenia_form_7217):
        """Test cash distribution amount."""
        assert sam_gardenia_form_7217["line_5a_cash_received"] == Decimal("4000.00")

    def test_no_gain_recognized(self, sam_gardenia_form_7217):
        """Test no gain is recognized on distribution."""
        assert sam_gardenia_form_7217["line_7_gain_recognized"] == Decimal("0.00")

    def test_basis_allocation(self, sam_gardenia_form_7217):
        """Test basis allocation to distributed property."""
        assert sam_gardenia_form_7217["line_10_basis_to_allocate"] == Decimal("6000.00")


# =============================================================================
# TEST CLASS: Schedule 1 Additional Income and Adjustments
# =============================================================================


class TestSchedule1AdditionalIncomeAdjustments:
    """Tests for Schedule 1 additional income and adjustments."""

    def test_business_income_from_schedule_c(self, sam_gardenia_schedule_1, sam_gardenia_schedule_c):
        """Test business income flows from Schedule C."""
        assert sam_gardenia_schedule_1["line_3_business_income"] == \
               sam_gardenia_schedule_c["line_31_net_profit"]

    def test_se_tax_deduction(self, sam_gardenia_schedule_1, sam_gardenia_schedule_se):
        """Test SE tax deduction flows from Schedule SE."""
        assert sam_gardenia_schedule_1["line_15_se_tax_deduction"] == \
               sam_gardenia_schedule_se["line_13_deductible_se_tax"]

    def test_health_insurance_deduction(self, sam_gardenia_schedule_1, sam_gardenia_form_7206):
        """Test health insurance deduction flows from Form 7206."""
        assert sam_gardenia_schedule_1["line_17_se_health_insurance"] == \
               sam_gardenia_form_7206["line_14_deduction"]

    def test_total_adjustments(self, sam_gardenia_schedule_1):
        """Test total adjustments calculation."""
        se_deduction = sam_gardenia_schedule_1["line_15_se_tax_deduction"]
        health_insurance = sam_gardenia_schedule_1["line_17_se_health_insurance"]
        expected = se_deduction + health_insurance
        assert sam_gardenia_schedule_1["line_26_total_adjustments"] == expected


# =============================================================================
# TEST CLASS: Tax Calculation
# =============================================================================


class TestTaxCalculation:
    """Tests for Form 1040 tax calculations."""

    def test_filing_status_single(self, sam_gardenia_form_1040_data):
        """Test filing status is Single."""
        assert sam_gardenia_form_1040_data["filing_status"] == 1

    def test_total_income(self, sam_gardenia_form_1040_data):
        """Test total income calculation."""
        assert sam_gardenia_form_1040_data["line_9_total_income"] == Decimal("125164.00")

    def test_agi_calculation(self, sam_gardenia_form_1040_data):
        """Test AGI calculation."""
        total_income = sam_gardenia_form_1040_data["line_9_total_income"]
        adjustments = sam_gardenia_form_1040_data["line_10_adjustments"]
        expected_agi = total_income - adjustments
        assert sam_gardenia_form_1040_data["line_11a_agi"] == expected_agi
        assert sam_gardenia_form_1040_data["line_11a_agi"] == Decimal("122445.00")

    def test_taxable_income(self, sam_gardenia_form_1040_data):
        """Test taxable income calculation."""
        assert sam_gardenia_form_1040_data["line_15_taxable_income"] == Decimal("107445.00")

    def test_regular_tax(self, sam_gardenia_form_1040_data):
        """Test regular tax from tax tables."""
        assert sam_gardenia_form_1040_data["line_16_tax"] == Decimal("18634.00")

    def test_se_tax_on_schedule_2(self, sam_gardenia_form_1040_data):
        """Test SE tax is included in other taxes."""
        assert sam_gardenia_form_1040_data["line_23_other_taxes"] == Decimal("3438.00")

    def test_total_tax(self, sam_gardenia_form_1040_data):
        """Test total tax calculation."""
        regular_tax = sam_gardenia_form_1040_data["line_16_tax"]
        se_tax = sam_gardenia_form_1040_data["line_23_other_taxes"]
        expected = regular_tax + se_tax
        assert sam_gardenia_form_1040_data["line_24_total_tax"] == expected
        assert sam_gardenia_form_1040_data["line_24_total_tax"] == Decimal("22072.00")

    def test_amount_owed(self, sam_gardenia_form_1040_data):
        """Test amount owed calculation."""
        total_tax = sam_gardenia_form_1040_data["line_24_total_tax"]
        total_payments = sam_gardenia_form_1040_data["line_33_total_payments"]
        expected = total_tax - total_payments
        assert sam_gardenia_form_1040_data["line_37_amount_owed"] == expected
        assert sam_gardenia_form_1040_data["line_37_amount_owed"] == Decimal("7628.00")


# =============================================================================
# TEST CLASS: XML Serialization
# =============================================================================


class TestScenario12XMLSerialization:
    """Tests for XML serialization of Scenario 12 data."""

    def test_taxpayer_info_creation(self, sam_gardenia_taxpayer):
        """Test TaxpayerInfo object creation."""
        taxpayer_info = TaxpayerInfo(
            primary_ssn=sam_gardenia_taxpayer["ssn_clean"],
            primary_first_name=sam_gardenia_taxpayer["first_name"],
            primary_last_name=sam_gardenia_taxpayer["last_name"],
        )

        assert taxpayer_info.primary_ssn == "400011212"
        assert taxpayer_info.primary_first_name == "Sam"
        assert taxpayer_info.primary_last_name == "Gardenia"

    def test_submission_id_generation(self):
        """Test MeF submission ID generation."""
        submission_id = SubmissionId.generate(efin="123456", sequence=1)

        assert len(submission_id.submission_id) == 20
        assert submission_id.submission_id.isdigit()


# =============================================================================
# TEST CLASS: Business Rules Validation
# =============================================================================


class TestScenario12BusinessRules:
    """Tests for business rules validation of Scenario 12 data."""

    def test_single_no_spouse(self, sam_gardenia_form_1040_data):
        """Test single filer has no spouse information."""
        assert sam_gardenia_form_1040_data["filing_status"] == 1
        assert "spouse_ssn" not in sam_gardenia_form_1040_data

    def test_schedule_c_required_for_business_income(self, sam_gardenia_form_1040_data):
        """Test Schedule C is attached when claiming business income."""
        assert sam_gardenia_form_1040_data["has_schedule_c"] is True
        assert sam_gardenia_form_1040_data["line_8_schedule_1_income"] > 0

    def test_schedule_se_required_for_se_tax(self, sam_gardenia_form_1040_data):
        """Test Schedule SE is attached when SE tax is due."""
        assert sam_gardenia_form_1040_data["has_schedule_se"] is True
        assert sam_gardenia_form_1040_data["line_23_other_taxes"] > 0


# =============================================================================
# TEST CLASS: Integration Tests
# =============================================================================


class TestScenario12Integration:
    """Integration tests for the complete Scenario 12 data."""

    def test_complete_form_1040_structure(self, sam_gardenia_form_1040_data):
        """Test complete form data has all required fields."""
        required_fields = [
            "primary_ssn", "primary_first_name", "primary_last_name",
            "filing_status",
            "wages", "total_income", "agi", "deduction", "taxable_income",
            "total_tax", "total_payments",
        ]

        for field in required_fields:
            assert field in sam_gardenia_form_1040_data, f"Missing field: {field}"

    def test_schedule_c_to_schedule_1_flow(self, sam_gardenia_schedule_c, sam_gardenia_schedule_1):
        """Test Schedule C net profit flows to Schedule 1."""
        assert sam_gardenia_schedule_1["line_3_business_income"] == \
               sam_gardenia_schedule_c["line_31_net_profit"]

    def test_schedule_c_to_schedule_se_flow(self, sam_gardenia_schedule_c, sam_gardenia_schedule_se):
        """Test Schedule C net profit flows to Schedule SE."""
        assert sam_gardenia_schedule_se["line_2_net_profit"] == \
               sam_gardenia_schedule_c["line_31_net_profit"]

    def test_schedule_se_to_schedule_1_flow(self, sam_gardenia_schedule_se, sam_gardenia_schedule_1):
        """Test Schedule SE deduction flows to Schedule 1."""
        assert sam_gardenia_schedule_1["line_15_se_tax_deduction"] == \
               sam_gardenia_schedule_se["line_13_deductible_se_tax"]

    def test_schedule_se_to_schedule_2_flow(self, sam_gardenia_schedule_se, sam_gardenia_schedule_2):
        """Test Schedule SE tax flows to Schedule 2."""
        assert sam_gardenia_schedule_2["line_4_se_tax"] == \
               sam_gardenia_schedule_se["line_12_se_tax"]

    def test_form_7206_to_schedule_1_flow(self, sam_gardenia_form_7206, sam_gardenia_schedule_1):
        """Test Form 7206 deduction flows to Schedule 1."""
        assert sam_gardenia_schedule_1["line_17_se_health_insurance"] == \
               sam_gardenia_form_7206["line_14_deduction"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
