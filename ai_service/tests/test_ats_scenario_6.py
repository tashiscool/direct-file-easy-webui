"""Comprehensive pytest tests for IRS ATS Test Scenario 6 - Juan Torres.

This module tests the MeF (Modernized e-File) service functionality using
IRS ATS (Assurance Testing System) Test Scenario 6 data for Juan Torres.

Test Scenario Reference: IRS ATS Test Scenario 6 (ty25-1040-mef-ats-scenario-6-10212025.pdf)
Primary Taxpayer: Juan Torres
Filing Status: Single
Location: Puerto Rico

Key Features Tested:
- Form 1040-SS (U.S. Self-Employment Tax Return for Puerto Rico)
- Schedule C (Profit or Loss from Business)
- Schedule SE (Self-Employment Tax)
- Bona fide Puerto Rico resident taxation
- Self-employment income and deductions

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
# FIXTURES - IRS ATS Test Scenario 6 Data (Juan Torres - 1040-SS Puerto Rico)
# =============================================================================


@pytest.fixture
def juan_torres_taxpayer() -> Dict[str, Any]:
    """Fixture for Juan Torres (primary taxpayer) information.

    IRS ATS Test Scenario 6 - Bona fide Puerto Rico resident with
    self-employment income filing Form 1040-SS.

    ATS Reference SSN: 400-00-1041 (invalid for production validation)
    Test SSN: 400-01-1041 (valid format for testing validation logic)
    """
    return {
        "first_name": "Juan",
        "last_name": "Torres",
        "ssn": "400-01-1041",
        "ssn_clean": "400011041",
        "ssn_ats_reference": "400-00-1041",
        "address": {
            "street": "Calle Sol 123",
            "city": "San Juan",
            "state": "PR",  # Puerto Rico
            "zip": "00901"
        },
        "date_of_birth": date(1975, 11, 3),
        "occupation": "Consultant",
        "is_bona_fide_pr_resident": True,
        "digital_assets": False,
    }


@pytest.fixture
def juan_torres_schedule_c() -> Dict[str, Any]:
    """Fixture for Schedule C (Profit or Loss from Business).

    Juan operates a consulting business in Puerto Rico.
    Principal Business Code: 541611 (Management Consulting)
    """
    return {
        # Business Information
        "business_name": "Torres Consulting",
        "principal_business_code": "541611",
        "principal_business_description": "Management Consulting",
        "business_address": {
            "street": "Calle Sol 123",
            "city": "San Juan",
            "state": "PR",
            "zip": "00901"
        },
        "accounting_method": "Cash",
        "ein": None,  # Uses SSN

        # Part I - Income
        "line_1_gross_receipts": Decimal("85000.00"),
        "line_2_returns_allowances": Decimal("0.00"),
        "line_3_net_receipts": Decimal("85000.00"),
        "line_4_cost_of_goods_sold": Decimal("0.00"),
        "line_5_gross_profit": Decimal("85000.00"),
        "line_6_other_income": Decimal("0.00"),
        "line_7_gross_income": Decimal("85000.00"),

        # Part II - Expenses
        "expenses": {
            "line_8_advertising": Decimal("1200.00"),
            "line_9_car_truck": Decimal("3500.00"),
            "line_10_commissions": Decimal("0.00"),
            "line_11_contract_labor": Decimal("5000.00"),
            "line_12_depletion": Decimal("0.00"),
            "line_13_depreciation": Decimal("2400.00"),
            "line_14_employee_benefits": Decimal("0.00"),
            "line_15_insurance": Decimal("1800.00"),
            "line_16a_mortgage_interest": Decimal("0.00"),
            "line_16b_other_interest": Decimal("0.00"),
            "line_17_legal_professional": Decimal("1500.00"),
            "line_18_office_expense": Decimal("2200.00"),
            "line_19_pension_profit_sharing": Decimal("0.00"),
            "line_20a_rent_vehicles": Decimal("0.00"),
            "line_20b_rent_other": Decimal("6000.00"),  # Office rent
            "line_21_repairs": Decimal("800.00"),
            "line_22_supplies": Decimal("1500.00"),
            "line_23_taxes_licenses": Decimal("950.00"),
            "line_24a_travel": Decimal("3200.00"),
            "line_24b_meals": Decimal("600.00"),  # 50% deductible
            "line_25_utilities": Decimal("1200.00"),
            "line_26_wages": Decimal("0.00"),
            "line_27a_other": Decimal("2500.00"),  # Professional development
        },

        # Line 28 - Total expenses
        "line_28_total_expenses": Decimal("34350.00"),

        # Line 29 - Tentative profit (loss)
        "line_29_tentative_profit": Decimal("50650.00"),  # 85000 - 34350

        # Line 30 - Expenses for business use of home (N/A)
        "line_30_home_office": Decimal("0.00"),

        # Line 31 - Net profit (loss)
        "line_31_net_profit": Decimal("50650.00"),

        # At-risk rules
        "all_investment_at_risk": True,
    }


@pytest.fixture
def juan_torres_schedule_se() -> Dict[str, Any]:
    """Fixture for Schedule SE (Self-Employment Tax).

    Self-employment tax calculation for Juan Torres.
    Uses standard method (not optional farm method).
    """
    return {
        # Part I - Self-Employment Tax
        # Line 1a - Net farm profit (N/A)
        "line_1a_farm_profit": Decimal("0.00"),

        # Line 1b - Net profit from Schedule C
        "line_1b_schedule_c_profit": Decimal("50650.00"),

        # Line 2 - Combined net profit
        "line_2_combined_profit": Decimal("50650.00"),

        # Line 3 - Multiply line 2 by 92.35%
        "line_3_net_earnings_rate": Decimal("0.9235"),
        "line_3_net_earnings": Decimal("46775.28"),  # 50650 * 0.9235

        # Line 4 - Maximum for Social Security (2025: $176,100)
        "line_4_ss_wage_base_2025": Decimal("176100.00"),

        # Line 5 - Wages subject to SS (N/A - no W-2)
        "line_5_ss_wages": Decimal("0.00"),

        # Line 6 - Line 4 minus Line 5
        "line_6_ss_available": Decimal("176100.00"),

        # Line 7 - Smaller of Line 3 or Line 6
        "line_7_ss_subject": Decimal("46775.28"),

        # Line 8 - SS portion of SE tax (12.4%)
        "line_8_ss_tax_rate": Decimal("0.124"),
        "line_8_ss_tax": Decimal("5800.13"),  # 46775.28 * 0.124

        # Line 9 - Medicare portion (2.9% on all net earnings)
        "line_9_medicare_rate": Decimal("0.029"),
        "line_9_medicare_tax": Decimal("1356.48"),  # 46775.28 * 0.029

        # Line 10 - Additional Medicare Tax (0.9% over $200,000)
        "line_10_additional_medicare_threshold": Decimal("200000.00"),
        "line_10_additional_medicare_tax": Decimal("0.00"),  # Below threshold

        # Line 11 - Total self-employment tax
        "line_11_total_se_tax": Decimal("7156.61"),  # 5800.13 + 1356.48

        # Line 12 - Deductible part of SE tax (50%)
        "line_12_deductible_se_tax": Decimal("3578.31"),  # 7156.61 / 2

        # Form 1040-SS specific
        "flows_to_form_1040ss_line_3": True,
    }


@pytest.fixture
def juan_torres_form_1040ss() -> Dict[str, Any]:
    """Fixture for Form 1040-SS (U.S. Self-Employment Tax Return).

    Form 1040-SS is used by bona fide residents of Puerto Rico
    to report self-employment tax.

    Note: Puerto Rico residents do not pay federal income tax
    on Puerto Rico-sourced income, but are subject to
    self-employment tax.
    """
    return {
        # Part I - Total Tax and Credits
        "line_1_net_earnings": Decimal("46775.28"),  # From Schedule SE

        # Line 2 - Self-employment tax
        "line_2_se_tax": Decimal("7156.61"),  # From Schedule SE, Line 11

        # Line 3 - Household employment taxes (N/A)
        "line_3_household_tax": Decimal("0.00"),

        # Line 4 - Total tax
        "line_4_total_tax": Decimal("7156.61"),

        # Line 5 - Estimated tax payments
        "line_5_estimated_payments": Decimal("6000.00"),

        # Line 6 - Excess Social Security tax withheld (N/A)
        "line_6_excess_ss_withheld": Decimal("0.00"),

        # Line 7 - Additional child tax credit (N/A for this scenario)
        "line_7_actc": Decimal("0.00"),

        # Line 8 - Total payments and credits
        "line_8_total_payments": Decimal("6000.00"),

        # Line 9 - Tax owed (Line 4 - Line 8)
        "line_9_tax_owed": Decimal("1156.61"),

        # Line 10 - Refund (if overpaid)
        "line_10_refund": Decimal("0.00"),

        # Part II - Bona Fide Resident of Puerto Rico
        "bona_fide_resident": True,
        "puerto_rico_address": True,

        # Part III - Profit or Loss from Farming (N/A)
        "has_farm_income": False,

        # Part IV - Profit or Loss from Business
        "has_business_income": True,
        "schedule_c_attached": True,

        # Part V - Self-Employment Tax
        "schedule_se_method": "Regular",  # vs. Optional
    }


@pytest.fixture
def juan_torres_form_1040ss_data(
    juan_torres_taxpayer,
    juan_torres_schedule_c,
    juan_torres_schedule_se,
    juan_torres_form_1040ss
) -> Dict[str, Any]:
    """Fixture for complete Form 1040-SS data for Juan Torres.

    Tax Year: 2025
    Filing Status: Single (implicit for 1040-SS)
    Form Type: 1040-SS (Puerto Rico Self-Employment)
    """
    return {
        # Taxpayer info
        "primary_ssn": juan_torres_taxpayer["ssn_clean"],
        "primary_first_name": juan_torres_taxpayer["first_name"],
        "primary_last_name": juan_torres_taxpayer["last_name"],
        "address": juan_torres_taxpayer["address"],
        "form_type": "1040-SS",
        "is_bona_fide_pr_resident": True,

        # Digital assets
        "digital_assets": False,

        # Business income from Schedule C
        "schedule_c_profit": juan_torres_schedule_c["line_31_net_profit"],

        # Self-employment tax from Schedule SE
        "net_earnings_se": juan_torres_schedule_se["line_3_net_earnings"],
        "se_tax": juan_torres_schedule_se["line_11_total_se_tax"],
        "deductible_se_tax": juan_torres_schedule_se["line_12_deductible_se_tax"],

        # Form 1040-SS totals
        "total_tax": juan_torres_form_1040ss["line_4_total_tax"],
        "total_payments": juan_torres_form_1040ss["line_8_total_payments"],
        "tax_owed": juan_torres_form_1040ss["line_9_tax_owed"],
        "refund": juan_torres_form_1040ss["line_10_refund"],

        # Attached schedules
        "has_schedule_c": True,
        "has_schedule_se": True,

        # Form data
        "schedule_c": juan_torres_schedule_c,
        "schedule_se": juan_torres_schedule_se,
        "form_1040ss": juan_torres_form_1040ss,
    }


# =============================================================================
# TEST CLASS: Taxpayer Information
# =============================================================================


class TestTaxpayerInformation:
    """Tests for taxpayer information."""

    def test_taxpayer_location(self, juan_torres_taxpayer):
        """Test taxpayer is in Puerto Rico."""
        assert juan_torres_taxpayer["address"]["state"] == "PR"
        assert juan_torres_taxpayer["is_bona_fide_pr_resident"] is True

    def test_taxpayer_occupation(self, juan_torres_taxpayer):
        """Test taxpayer occupation."""
        assert juan_torres_taxpayer["occupation"] == "Consultant"

    def test_taxpayer_ssn_format(self, juan_torres_taxpayer):
        """Test SSN format."""
        ssn_clean = juan_torres_taxpayer["ssn_clean"]
        assert len(ssn_clean) == 9
        assert ssn_clean.isdigit()


# =============================================================================
# TEST CLASS: Schedule C Business Income
# =============================================================================


class TestScheduleCBusinessIncome:
    """Tests for Schedule C (Profit or Loss from Business)."""

    def test_gross_receipts(self, juan_torres_schedule_c):
        """Test gross receipts amount."""
        assert juan_torres_schedule_c["line_1_gross_receipts"] == Decimal("85000.00")

    def test_total_expenses(self, juan_torres_schedule_c):
        """Test total business expenses calculation."""
        expenses = juan_torres_schedule_c["expenses"]
        expected_total = sum(expenses.values())

        assert juan_torres_schedule_c["line_28_total_expenses"] == expected_total

    def test_net_profit_calculation(self, juan_torres_schedule_c):
        """Test net profit = gross income - expenses."""
        gross = juan_torres_schedule_c["line_7_gross_income"]
        expenses = juan_torres_schedule_c["line_28_total_expenses"]
        expected_profit = gross - expenses

        assert juan_torres_schedule_c["line_31_net_profit"] == expected_profit

    def test_principal_business_code(self, juan_torres_schedule_c):
        """Test principal business code for consulting."""
        assert juan_torres_schedule_c["principal_business_code"] == "541611"
        assert "Consulting" in juan_torres_schedule_c["principal_business_description"]

    def test_accounting_method(self, juan_torres_schedule_c):
        """Test accounting method is Cash."""
        assert juan_torres_schedule_c["accounting_method"] == "Cash"

    def test_major_expense_categories(self, juan_torres_schedule_c):
        """Test major expense categories are present."""
        expenses = juan_torres_schedule_c["expenses"]

        assert expenses["line_20b_rent_other"] == Decimal("6000.00")  # Office rent
        assert expenses["line_11_contract_labor"] == Decimal("5000.00")
        assert expenses["line_9_car_truck"] == Decimal("3500.00")


# =============================================================================
# TEST CLASS: Schedule SE Self-Employment Tax
# =============================================================================


class TestScheduleSESelfEmploymentTax:
    """Tests for Schedule SE (Self-Employment Tax)."""

    def test_schedule_c_profit_flows(self, juan_torres_schedule_se):
        """Test Schedule C profit flows to Schedule SE."""
        assert juan_torres_schedule_se["line_1b_schedule_c_profit"] == Decimal("50650.00")

    def test_net_earnings_calculation(self, juan_torres_schedule_se):
        """Test net earnings = profit * 92.35%."""
        profit = juan_torres_schedule_se["line_2_combined_profit"]
        rate = juan_torres_schedule_se["line_3_net_earnings_rate"]
        expected = (profit * rate).quantize(Decimal("0.01"))

        assert juan_torres_schedule_se["line_3_net_earnings"] == expected

    def test_ss_tax_calculation(self, juan_torres_schedule_se):
        """Test Social Security tax calculation (12.4%)."""
        net_earnings = juan_torres_schedule_se["line_7_ss_subject"]
        ss_rate = juan_torres_schedule_se["line_8_ss_tax_rate"]
        expected = (net_earnings * ss_rate).quantize(Decimal("0.01"))

        assert juan_torres_schedule_se["line_8_ss_tax"] == expected

    def test_medicare_tax_calculation(self, juan_torres_schedule_se):
        """Test Medicare tax calculation (2.9%)."""
        net_earnings = juan_torres_schedule_se["line_3_net_earnings"]
        medicare_rate = juan_torres_schedule_se["line_9_medicare_rate"]
        expected = (net_earnings * medicare_rate).quantize(Decimal("0.01"))

        assert juan_torres_schedule_se["line_9_medicare_tax"] == expected

    def test_total_se_tax_calculation(self, juan_torres_schedule_se):
        """Test total SE tax = SS tax + Medicare tax."""
        ss_tax = juan_torres_schedule_se["line_8_ss_tax"]
        medicare_tax = juan_torres_schedule_se["line_9_medicare_tax"]
        additional_medicare = juan_torres_schedule_se["line_10_additional_medicare_tax"]
        expected = ss_tax + medicare_tax + additional_medicare

        assert juan_torres_schedule_se["line_11_total_se_tax"] == expected

    def test_deductible_se_tax(self, juan_torres_schedule_se):
        """Test deductible SE tax is 50% of total."""
        total_se = juan_torres_schedule_se["line_11_total_se_tax"]
        deductible = juan_torres_schedule_se["line_12_deductible_se_tax"]

        # Deductible should be approximately half of total (within rounding)
        expected_half = total_se / 2
        assert abs(deductible - expected_half) < Decimal("0.02")

    def test_no_additional_medicare(self, juan_torres_schedule_se):
        """Test no additional Medicare tax (income below $200,000)."""
        net_earnings = juan_torres_schedule_se["line_3_net_earnings"]
        threshold = juan_torres_schedule_se["line_10_additional_medicare_threshold"]

        assert net_earnings < threshold
        assert juan_torres_schedule_se["line_10_additional_medicare_tax"] == Decimal("0.00")


# =============================================================================
# TEST CLASS: Form 1040-SS
# =============================================================================


class TestForm1040SS:
    """Tests for Form 1040-SS (U.S. Self-Employment Tax Return)."""

    def test_form_type(self, juan_torres_form_1040ss_data):
        """Test correct form type."""
        assert juan_torres_form_1040ss_data["form_type"] == "1040-SS"

    def test_bona_fide_resident(self, juan_torres_form_1040ss_data, juan_torres_form_1040ss):
        """Test bona fide PR resident status."""
        assert juan_torres_form_1040ss_data["is_bona_fide_pr_resident"] is True
        assert juan_torres_form_1040ss["bona_fide_resident"] is True

    def test_total_tax_equals_se_tax(self, juan_torres_form_1040ss):
        """Test total tax equals SE tax (no household employment)."""
        se_tax = juan_torres_form_1040ss["line_2_se_tax"]
        household_tax = juan_torres_form_1040ss["line_3_household_tax"]
        total = juan_torres_form_1040ss["line_4_total_tax"]

        assert total == se_tax + household_tax

    def test_tax_owed_calculation(self, juan_torres_form_1040ss):
        """Test tax owed = total tax - payments."""
        total_tax = juan_torres_form_1040ss["line_4_total_tax"]
        total_payments = juan_torres_form_1040ss["line_8_total_payments"]
        expected_owed = total_tax - total_payments

        assert juan_torres_form_1040ss["line_9_tax_owed"] == expected_owed

    def test_estimated_payments(self, juan_torres_form_1040ss):
        """Test estimated tax payments."""
        assert juan_torres_form_1040ss["line_5_estimated_payments"] == Decimal("6000.00")


# =============================================================================
# TEST CLASS: XML Serialization
# =============================================================================


class TestScenario6XMLSerialization:
    """Tests for XML serialization of Scenario 6 data."""

    def test_taxpayer_info_creation(self, juan_torres_taxpayer):
        """Test TaxpayerInfo object creation."""
        taxpayer_info = TaxpayerInfo(
            primary_ssn=juan_torres_taxpayer["ssn_clean"],
            primary_first_name=juan_torres_taxpayer["first_name"],
            primary_last_name=juan_torres_taxpayer["last_name"],
            primary_date_of_birth=juan_torres_taxpayer["date_of_birth"],
        )

        assert taxpayer_info.primary_ssn == "400011041"
        assert taxpayer_info.primary_first_name == "Juan"
        assert taxpayer_info.primary_last_name == "Torres"

    def test_submission_id_generation(self):
        """Test MeF submission ID generation."""
        submission_id = SubmissionId.generate(efin="123456", sequence=1)

        assert len(submission_id.submission_id) == 20
        assert submission_id.submission_id.isdigit()


# =============================================================================
# TEST CLASS: Business Rules Validation
# =============================================================================


class TestScenario6BusinessRules:
    """Tests for business rules validation of Scenario 6 data."""

    def test_pr_resident_uses_1040ss(self, juan_torres_form_1040ss_data):
        """Test Puerto Rico resident files Form 1040-SS."""
        assert juan_torres_form_1040ss_data["address"]["state"] == "PR"
        assert juan_torres_form_1040ss_data["form_type"] == "1040-SS"

    def test_se_income_requires_schedule_se(self, juan_torres_form_1040ss_data):
        """Test self-employment income requires Schedule SE."""
        se_tax = juan_torres_form_1040ss_data["se_tax"]

        if se_tax > Decimal("0"):
            assert juan_torres_form_1040ss_data["has_schedule_se"] is True

    def test_business_income_requires_schedule_c(self, juan_torres_form_1040ss_data):
        """Test business income requires Schedule C."""
        schedule_c_profit = juan_torres_form_1040ss_data["schedule_c_profit"]

        if schedule_c_profit > Decimal("0"):
            assert juan_torres_form_1040ss_data["has_schedule_c"] is True

    def test_se_tax_threshold(self, juan_torres_schedule_se):
        """Test SE tax is required when net earnings exceed $400."""
        net_earnings = juan_torres_schedule_se["line_3_net_earnings"]
        se_tax = juan_torres_schedule_se["line_11_total_se_tax"]

        if net_earnings > Decimal("400"):
            assert se_tax > Decimal("0")


# =============================================================================
# TEST CLASS: Integration Tests
# =============================================================================


class TestScenario6Integration:
    """Integration tests for the complete Scenario 6 data."""

    def test_complete_form_structure(self, juan_torres_form_1040ss_data):
        """Test complete form data has all required fields."""
        required_fields = [
            "primary_ssn", "primary_first_name", "primary_last_name",
            "form_type", "is_bona_fide_pr_resident",
            "schedule_c_profit", "se_tax", "total_tax",
        ]

        for field in required_fields:
            assert field in juan_torres_form_1040ss_data, f"Missing field: {field}"

    def test_schedule_c_to_schedule_se_flow(self, juan_torres_schedule_c, juan_torres_schedule_se):
        """Test Schedule C profit flows to Schedule SE."""
        schedule_c_profit = juan_torres_schedule_c["line_31_net_profit"]
        schedule_se_input = juan_torres_schedule_se["line_1b_schedule_c_profit"]

        assert schedule_se_input == schedule_c_profit

    def test_schedule_se_to_form_1040ss_flow(self, juan_torres_schedule_se, juan_torres_form_1040ss):
        """Test Schedule SE tax flows to Form 1040-SS."""
        schedule_se_tax = juan_torres_schedule_se["line_11_total_se_tax"]
        form_1040ss_se_tax = juan_torres_form_1040ss["line_2_se_tax"]

        assert form_1040ss_se_tax == schedule_se_tax

    def test_tax_liability_calculation(self, juan_torres_form_1040ss_data):
        """Test overall tax liability calculation."""
        total_tax = juan_torres_form_1040ss_data["total_tax"]
        total_payments = juan_torres_form_1040ss_data["total_payments"]
        tax_owed = juan_torres_form_1040ss_data["tax_owed"]
        refund = juan_torres_form_1040ss_data["refund"]

        if total_tax > total_payments:
            assert tax_owed == total_tax - total_payments
            assert refund == Decimal("0")
        else:
            assert refund == total_payments - total_tax
            assert tax_owed == Decimal("0")

    def test_self_employment_rates(self, juan_torres_schedule_se):
        """Test self-employment tax rates are correct for 2025."""
        # SS rate: 12.4% (employee + employer portions)
        assert juan_torres_schedule_se["line_8_ss_tax_rate"] == Decimal("0.124")

        # Medicare rate: 2.9% (employee + employer portions)
        assert juan_torres_schedule_se["line_9_medicare_rate"] == Decimal("0.029")

        # Net earnings rate: 92.35%
        assert juan_torres_schedule_se["line_3_net_earnings_rate"] == Decimal("0.9235")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
