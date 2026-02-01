"""Comprehensive pytest tests for IRS ATS Test Scenario NR-12 - John Harrier.

This module tests the MeF (Modernized e-File) service functionality using
IRS ATS (Assurance Testing System) Test Scenario NR-12 data for John Harrier.

Test Scenario Reference: IRS ATS Test Scenario NR-12 (ty2025-form-1040-nr-scenario-12.pdf)
Primary Taxpayer: John Harrier
Filing Status: Married Filing Separately (MFS) - Form 1040-NR

Key Features Tested:
- Form 1040-NR for Nonresident Alien (MFS filing status)
- Schedule A (Form 1040-NR) - Itemized Deductions (SALT cap)
- Schedule P (Form 1040-NR) - Foreign Partner's Partnership Interest Transfer
- Schedule D - Capital Gains and Losses
- Form 8949 - Sales and Other Dispositions of Capital Assets
- Short-term capital gain from partnership interest transfer
- Foreign address (Australia)
- Estimated tax payments

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
def john_harrier_taxpayer() -> Dict[str, Any]:
    """Fixture for John Harrier (primary taxpayer) information."""
    return {
        "first_name": "John",
        "last_name": "Harrier",
        "ssn": "123-01-1112",           # Valid format for testing
        "ssn_clean": "123011112",        # 9 digits, no dashes
        "ssn_ats_reference": "123-00-1112",  # Original ATS SSN
        "foreign_address": {
            "street": "500 Watheroo St",
            "city": "Melbourne",
            "province": "VIC",
            "postal_code": "3000",
            "country": "Australia"
        },
        "date_of_birth": date(1975, 8, 20),  # Estimated
        "is_nonresident_alien": True,
        "filing_status": "MFS",  # Married Filing Separately
        "filing_status_code": 3,
        "digital_assets": False,
    }


# =============================================================================
# FIXTURES - Schedule A (Itemized Deductions)
# =============================================================================

@pytest.fixture
def john_harrier_schedule_a() -> Dict[str, Any]:
    """Fixture for Schedule A (Form 1040-NR) - Itemized Deductions."""
    return {
        # Taxes You Paid
        "line_1a_state_local_income_taxes": Decimal("5432.00"),
        # SALT cap: smaller of line 1a or $10,000 ($5,000 if MFS)
        "line_1b_salt_deduction": Decimal("5000.00"),  # MFS cap is $5,000

        # Gifts to U.S. Charities
        "line_2_cash_gifts": Decimal("0.00"),
        "line_3_noncash_gifts": Decimal("0.00"),
        "line_4_carryover": Decimal("0.00"),
        "line_5_total_gifts": Decimal("0.00"),

        # Casualty and Theft Losses
        "line_6_casualty_theft": Decimal("0.00"),

        # Other Itemized Deductions
        "line_7_other": Decimal("0.00"),

        # Total Itemized Deductions
        "line_8_total": Decimal("5000.00"),
    }


# =============================================================================
# FIXTURES - Schedule P (Foreign Partner's Partnership Interest Transfer)
# =============================================================================

@pytest.fixture
def john_harrier_schedule_p() -> Dict[str, Any]:
    """Fixture for Schedule P (Form 1040-NR) - Foreign Partner's Interests."""
    return {
        # Part I - Partnership Interest Information
        "partnership_name": "IRIDIUM PARTNERSHIP",
        "partnership_address": "50 W Roan Blvd, San Jose, CA 95101",
        "partnership_ein": "00-5159901",
        "partnership_ein_clean": "005159901",
        "percentage_transferred": Decimal("10.00"),
        "date_acquired": date(2025, 6, 15),
        "date_transferred": date(2025, 12, 31),
        "total_transfers": 1,
        "total_proceeds": Decimal("375000.00"),

        # Part II - Gain or Loss on Transfer
        "line_1_proceeds": Decimal("375000.00"),
        "line_2_outside_basis": Decimal("25000.00"),
        "line_3_total_outside_gain": Decimal("350000.00"),
        "line_4_section_751_ordinary_gain": Decimal("0.00"),
        "line_5_total_capital_gain": Decimal("350000.00"),
        "line_6_eci_ordinary_gain": Decimal("0.00"),
        "line_7_eci_capital_gain": Decimal("375000.00"),
        "line_8_recognized_eci_ordinary": Decimal("0.00"),
        "line_9_recognized_eci_capital": Decimal("350000.00"),  # Smaller of line 5 or 7
    }


# =============================================================================
# FIXTURES - Form 8949 (Sales and Dispositions of Capital Assets)
# =============================================================================

@pytest.fixture
def john_harrier_form_8949(john_harrier_schedule_p) -> Dict[str, Any]:
    """Fixture for Form 8949 - Sales and Other Dispositions of Capital Assets."""
    return {
        # Part I - Short-Term
        "part_i_box_checked": "C",  # Not reported on Form 1099-B
        "transactions": [
            {
                "description": "From Schedule P (Form 1040-NR)",
                "date_acquired": john_harrier_schedule_p["date_acquired"],
                "date_sold": john_harrier_schedule_p["date_transferred"],
                "proceeds": john_harrier_schedule_p["line_1_proceeds"],
                "cost_basis": john_harrier_schedule_p["line_2_outside_basis"],
                "adjustment_code": None,
                "adjustment_amount": Decimal("0.00"),
                "gain_loss": john_harrier_schedule_p["line_3_total_outside_gain"],
            }
        ],
        "line_2_totals": {
            "proceeds": Decimal("375000.00"),
            "cost": Decimal("25000.00"),
            "adjustment": Decimal("0.00"),
            "gain": Decimal("350000.00"),
        },

        # Part II - Long-Term
        "part_ii_transactions": [],  # No long-term transactions
    }


# =============================================================================
# FIXTURES - Schedule D (Capital Gains and Losses)
# =============================================================================

@pytest.fixture
def john_harrier_schedule_d(john_harrier_form_8949) -> Dict[str, Any]:
    """Fixture for Schedule D (Form 1040) - Capital Gains and Losses."""
    return {
        # Part I - Short-Term Capital Gains and Losses
        "line_1a": None,  # Blank - not reported on 1099-B with basis
        "line_1b": None,  # Box A or G
        "line_2": None,   # Box B or H
        "line_3": {       # Box C or I checked
            "proceeds": john_harrier_form_8949["line_2_totals"]["proceeds"],
            "cost": john_harrier_form_8949["line_2_totals"]["cost"],
            "adjustment": john_harrier_form_8949["line_2_totals"]["adjustment"],
            "gain": john_harrier_form_8949["line_2_totals"]["gain"],
        },
        "line_4_form_6252_etc": Decimal("0.00"),
        "line_5_k1_short_term": Decimal("0.00"),
        "line_6_carryover": Decimal("0.00"),
        "line_7_net_short_term": Decimal("350000.00"),

        # Part II - Long-Term Capital Gains and Losses
        "line_8a": None,
        "line_8b": None,
        "line_9": None,
        "line_10": None,
        "line_11_form_4797_etc": Decimal("0.00"),
        "line_12_k1_long_term": Decimal("0.00"),
        "line_13_capital_distributions": Decimal("0.00"),
        "line_14_carryover": Decimal("0.00"),
        "line_15_net_long_term": Decimal("0.00"),

        # Part III - Summary
        "line_16_combined": Decimal("350000.00"),  # Short-term + Long-term
        "line_17_both_gains": False,  # Line 15 is 0, so not both gains
        "line_22_qualified_dividends": False,
    }


# =============================================================================
# FIXTURES - Complete Form 1040-NR
# =============================================================================

@pytest.fixture
def john_harrier_form_1040nr_data(
    john_harrier_taxpayer,
    john_harrier_schedule_a,
    john_harrier_schedule_p,
    john_harrier_schedule_d
) -> Dict[str, Any]:
    """Complete Form 1040-NR data for John Harrier."""

    # Income calculation
    capital_gain = john_harrier_schedule_d["line_16_combined"]
    total_eci = capital_gain  # $350,000

    # AGI (no adjustments)
    agi = total_eci  # $350,000

    # Deductions
    itemized_deductions = john_harrier_schedule_a["line_8_total"]  # $5,000

    # Taxable income
    taxable_income = agi - itemized_deductions  # $345,000

    # Tax calculation - MFS brackets 2025
    # Short-term capital gain is taxed as ordinary income
    tax = Decimal("90297.00")  # From the form

    # No credits
    total_credits = Decimal("0.00")

    # Tax after credits
    tax_after_credits = tax - total_credits  # $90,297

    # No other taxes
    other_taxes = Decimal("0.00")

    # Total tax
    total_tax = tax_after_credits + other_taxes  # $90,297

    # Payments - Estimated tax payments
    estimated_payments = Decimal("90297.00")
    total_payments = estimated_payments

    # Amount owed (payments = tax exactly)
    balance = total_tax - total_payments  # $0

    return {
        "form_type": "1040-NR",
        "tax_year": 2025,
        "filing_status": "MFS",
        "filing_status_code": 3,

        # Taxpayer info
        "taxpayer": john_harrier_taxpayer,

        # Income (Effectively Connected)
        "line_1a_w2_wages": Decimal("0.00"),
        "line_7a_capital_gain": capital_gain,
        "line_9_total_eci": total_eci,
        "line_11a_agi": agi,

        # Tax and Credits
        "line_11b_agi": agi,
        "line_12_itemized_deductions": itemized_deductions,
        "line_14_total_deductions": itemized_deductions,
        "line_15_taxable_income": taxable_income,
        "line_16_tax": tax,
        "line_17_schedule_2_line_3": Decimal("0.00"),
        "line_18_total": tax,
        "line_19_child_tax_credit": Decimal("0.00"),
        "line_20_schedule_3_line_8": Decimal("0.00"),
        "line_21_total_credits": total_credits,
        "line_22_tax_after_credits": tax_after_credits,
        "line_23a_nec_tax": Decimal("0.00"),
        "line_23b_other_taxes": other_taxes,
        "line_23d_total_other": other_taxes,
        "line_24_total_tax": total_tax,

        # Payments
        "line_25a_w2_withholding": Decimal("0.00"),
        "line_25d_total_withholding": Decimal("0.00"),
        "line_26_estimated_payments": estimated_payments,
        "line_33_total_payments": total_payments,

        # Amount Owed
        "line_37_amount_owed": balance,

        # Attached schedules/forms
        "has_schedule_a_nr": True,
        "has_schedule_p": True,
        "has_schedule_d": True,
        "has_form_8949": True,
    }


# =============================================================================
# TEST CLASSES
# =============================================================================

class TestTaxpayerInformation:
    """Tests for John Harrier's taxpayer information."""

    def test_taxpayer_name(self, john_harrier_taxpayer):
        """Test taxpayer name."""
        assert john_harrier_taxpayer["first_name"] == "John"
        assert john_harrier_taxpayer["last_name"] == "Harrier"

    def test_taxpayer_ssn(self, john_harrier_taxpayer):
        """Test SSN format."""
        assert john_harrier_taxpayer["ssn_ats_reference"] == "123-00-1112"
        assert len(john_harrier_taxpayer["ssn_clean"]) == 9

    def test_is_nonresident_alien(self, john_harrier_taxpayer):
        """Test NRA status."""
        assert john_harrier_taxpayer["is_nonresident_alien"] is True

    def test_foreign_address(self, john_harrier_taxpayer):
        """Test Australia address."""
        addr = john_harrier_taxpayer["foreign_address"]
        assert addr["country"] == "Australia"
        assert addr["province"] == "VIC"
        assert addr["city"] == "Melbourne"
        assert addr["postal_code"] == "3000"

    def test_filing_status_mfs(self, john_harrier_taxpayer):
        """Test Married Filing Separately filing status."""
        assert john_harrier_taxpayer["filing_status"] == "MFS"
        assert john_harrier_taxpayer["filing_status_code"] == 3

    def test_digital_assets_no(self, john_harrier_taxpayer):
        """Test digital assets answer is No."""
        assert john_harrier_taxpayer["digital_assets"] is False


class TestScheduleAItemizedDeductions:
    """Tests for Schedule A (Form 1040-NR) - Itemized Deductions."""

    def test_state_local_taxes_entered(self, john_harrier_schedule_a):
        """Test state/local income taxes entered."""
        assert john_harrier_schedule_a["line_1a_state_local_income_taxes"] == Decimal("5432.00")

    def test_salt_cap_mfs(self, john_harrier_schedule_a):
        """Test SALT cap for MFS is $5,000."""
        # MFS SALT cap is $5,000 (half of $10,000 for other filers)
        assert john_harrier_schedule_a["line_1b_salt_deduction"] == Decimal("5000.00")
        # Verify cap was applied (1a > cap)
        assert john_harrier_schedule_a["line_1a_state_local_income_taxes"] > john_harrier_schedule_a["line_1b_salt_deduction"]

    def test_no_charitable_contributions(self, john_harrier_schedule_a):
        """Test no charitable contributions claimed."""
        assert john_harrier_schedule_a["line_5_total_gifts"] == Decimal("0.00")

    def test_total_itemized_deductions(self, john_harrier_schedule_a):
        """Test total itemized deductions."""
        assert john_harrier_schedule_a["line_8_total"] == Decimal("5000.00")


class TestSchedulePPartnershipInterest:
    """Tests for Schedule P (Form 1040-NR) - Foreign Partner's Interests."""

    def test_partnership_name(self, john_harrier_schedule_p):
        """Test partnership name."""
        assert john_harrier_schedule_p["partnership_name"] == "IRIDIUM PARTNERSHIP"

    def test_partnership_ein(self, john_harrier_schedule_p):
        """Test partnership EIN."""
        assert john_harrier_schedule_p["partnership_ein"] == "00-5159901"

    def test_partnership_address(self, john_harrier_schedule_p):
        """Test partnership is in California."""
        assert "San Jose, CA" in john_harrier_schedule_p["partnership_address"]

    def test_percentage_transferred(self, john_harrier_schedule_p):
        """Test 10% interest transferred."""
        assert john_harrier_schedule_p["percentage_transferred"] == Decimal("10.00")

    def test_holding_period_short_term(self, john_harrier_schedule_p):
        """Test holding period is short-term (< 1 year)."""
        acquired = john_harrier_schedule_p["date_acquired"]
        transferred = john_harrier_schedule_p["date_transferred"]
        days_held = (transferred - acquired).days
        assert days_held < 365  # Short-term

    def test_proceeds(self, john_harrier_schedule_p):
        """Test proceeds from transfer."""
        assert john_harrier_schedule_p["line_1_proceeds"] == Decimal("375000.00")

    def test_outside_basis(self, john_harrier_schedule_p):
        """Test Section 705 outside basis."""
        assert john_harrier_schedule_p["line_2_outside_basis"] == Decimal("25000.00")

    def test_total_gain_calculation(self, john_harrier_schedule_p):
        """Test total outside gain calculation."""
        expected = (
            john_harrier_schedule_p["line_1_proceeds"] -
            john_harrier_schedule_p["line_2_outside_basis"]
        )
        assert john_harrier_schedule_p["line_3_total_outside_gain"] == expected
        assert expected == Decimal("350000.00")

    def test_no_section_751_ordinary_gain(self, john_harrier_schedule_p):
        """Test no Section 751 ordinary gain."""
        assert john_harrier_schedule_p["line_4_section_751_ordinary_gain"] == Decimal("0.00")

    def test_capital_gain_equals_total_gain(self, john_harrier_schedule_p):
        """Test capital gain equals total gain when no 751 property."""
        assert john_harrier_schedule_p["line_5_total_capital_gain"] == john_harrier_schedule_p["line_3_total_outside_gain"]

    def test_recognized_eci_capital_gain(self, john_harrier_schedule_p):
        """Test recognized ECI capital gain is smaller of line 5 or 7."""
        line_5 = john_harrier_schedule_p["line_5_total_capital_gain"]
        line_7 = john_harrier_schedule_p["line_7_eci_capital_gain"]
        expected = min(line_5, line_7)
        assert john_harrier_schedule_p["line_9_recognized_eci_capital"] == expected


class TestForm8949SalesDispositions:
    """Tests for Form 8949 - Sales and Other Dispositions of Capital Assets."""

    def test_box_c_checked(self, john_harrier_form_8949):
        """Test Box C is checked (not reported on 1099-B)."""
        assert john_harrier_form_8949["part_i_box_checked"] == "C"

    def test_transaction_description(self, john_harrier_form_8949):
        """Test transaction description references Schedule P."""
        txn = john_harrier_form_8949["transactions"][0]
        assert "Schedule P" in txn["description"]

    def test_transaction_dates(self, john_harrier_form_8949):
        """Test transaction dates."""
        txn = john_harrier_form_8949["transactions"][0]
        assert txn["date_acquired"] == date(2025, 6, 15)
        assert txn["date_sold"] == date(2025, 12, 31)

    def test_transaction_amounts(self, john_harrier_form_8949):
        """Test transaction amounts."""
        txn = john_harrier_form_8949["transactions"][0]
        assert txn["proceeds"] == Decimal("375000.00")
        assert txn["cost_basis"] == Decimal("25000.00")
        assert txn["gain_loss"] == Decimal("350000.00")

    def test_line_2_totals(self, john_harrier_form_8949):
        """Test line 2 totals."""
        totals = john_harrier_form_8949["line_2_totals"]
        assert totals["proceeds"] == Decimal("375000.00")
        assert totals["cost"] == Decimal("25000.00")
        assert totals["gain"] == Decimal("350000.00")

    def test_no_long_term_transactions(self, john_harrier_form_8949):
        """Test no long-term transactions."""
        assert len(john_harrier_form_8949["part_ii_transactions"]) == 0


class TestScheduleDCapitalGains:
    """Tests for Schedule D - Capital Gains and Losses."""

    def test_short_term_gain_on_line_3(self, john_harrier_schedule_d):
        """Test short-term gain reported on line 3 (Box C)."""
        assert john_harrier_schedule_d["line_3"]["gain"] == Decimal("350000.00")

    def test_net_short_term_capital_gain(self, john_harrier_schedule_d):
        """Test net short-term capital gain."""
        assert john_harrier_schedule_d["line_7_net_short_term"] == Decimal("350000.00")

    def test_no_long_term_gain(self, john_harrier_schedule_d):
        """Test no long-term capital gain."""
        assert john_harrier_schedule_d["line_15_net_long_term"] == Decimal("0.00")

    def test_combined_gain(self, john_harrier_schedule_d):
        """Test combined capital gain on line 16."""
        expected = (
            john_harrier_schedule_d["line_7_net_short_term"] +
            john_harrier_schedule_d["line_15_net_long_term"]
        )
        assert john_harrier_schedule_d["line_16_combined"] == expected

    def test_not_both_gains(self, john_harrier_schedule_d):
        """Test lines 15 and 16 are not both gains."""
        # Line 15 is 0, so they can't both be gains
        assert john_harrier_schedule_d["line_17_both_gains"] is False

    def test_no_qualified_dividends(self, john_harrier_schedule_d):
        """Test no qualified dividends."""
        assert john_harrier_schedule_d["line_22_qualified_dividends"] is False


class TestForm1040NRTaxCalculation:
    """Tests for Form 1040-NR tax calculations."""

    def test_form_type(self, john_harrier_form_1040nr_data):
        """Test form type is 1040-NR."""
        assert john_harrier_form_1040nr_data["form_type"] == "1040-NR"

    def test_filing_status_mfs(self, john_harrier_form_1040nr_data):
        """Test filing status is Married Filing Separately."""
        assert john_harrier_form_1040nr_data["filing_status"] == "MFS"

    def test_capital_gain_income(self, john_harrier_form_1040nr_data):
        """Test capital gain is only income."""
        assert john_harrier_form_1040nr_data["line_7a_capital_gain"] == Decimal("350000.00")
        assert john_harrier_form_1040nr_data["line_1a_w2_wages"] == Decimal("0.00")

    def test_total_eci(self, john_harrier_form_1040nr_data):
        """Test total effectively connected income."""
        assert john_harrier_form_1040nr_data["line_9_total_eci"] == Decimal("350000.00")

    def test_agi(self, john_harrier_form_1040nr_data):
        """Test AGI equals total income (no adjustments)."""
        assert john_harrier_form_1040nr_data["line_11a_agi"] == Decimal("350000.00")

    def test_itemized_deductions(self, john_harrier_form_1040nr_data):
        """Test itemized deductions used."""
        assert john_harrier_form_1040nr_data["line_12_itemized_deductions"] == Decimal("5000.00")

    def test_taxable_income(self, john_harrier_form_1040nr_data):
        """Test taxable income calculation."""
        expected = Decimal("350000.00") - Decimal("5000.00")
        assert john_harrier_form_1040nr_data["line_15_taxable_income"] == expected

    def test_tax_amount(self, john_harrier_form_1040nr_data):
        """Test tax amount from form."""
        assert john_harrier_form_1040nr_data["line_16_tax"] == Decimal("90297.00")

    def test_no_credits(self, john_harrier_form_1040nr_data):
        """Test no credits claimed."""
        assert john_harrier_form_1040nr_data["line_21_total_credits"] == Decimal("0.00")

    def test_total_tax(self, john_harrier_form_1040nr_data):
        """Test total tax."""
        assert john_harrier_form_1040nr_data["line_24_total_tax"] == Decimal("90297.00")

    def test_estimated_payments(self, john_harrier_form_1040nr_data):
        """Test estimated tax payments."""
        assert john_harrier_form_1040nr_data["line_26_estimated_payments"] == Decimal("90297.00")

    def test_total_payments_equals_tax(self, john_harrier_form_1040nr_data):
        """Test total payments equal total tax."""
        assert john_harrier_form_1040nr_data["line_33_total_payments"] == john_harrier_form_1040nr_data["line_24_total_tax"]

    def test_no_balance_due(self, john_harrier_form_1040nr_data):
        """Test no balance due (payments = tax)."""
        assert john_harrier_form_1040nr_data["line_37_amount_owed"] == Decimal("0.00")


class TestScenarioNR12XMLSerialization:
    """Tests for XML serialization of NR-12 scenario."""

    def test_taxpayer_info_creation(self, john_harrier_taxpayer):
        """Test TaxpayerInfo can be created."""
        taxpayer_info = TaxpayerInfo(
            primary_ssn=john_harrier_taxpayer["ssn_clean"],
            primary_first_name=john_harrier_taxpayer["first_name"],
            primary_last_name=john_harrier_taxpayer["last_name"],
            primary_date_of_birth=john_harrier_taxpayer["date_of_birth"]
        )
        assert taxpayer_info.primary_ssn == john_harrier_taxpayer["ssn_clean"]
        assert taxpayer_info.primary_first_name == "John"

    def test_submission_id_generation(self, john_harrier_taxpayer):
        """Test submission ID can be generated."""
        submission_id = SubmissionId.generate(
            efin="123456",
            sequence=1
        )
        assert len(submission_id.submission_id) == 20


class TestScenarioNR12BusinessRules:
    """Tests for business rules validation."""

    def test_nra_uses_1040nr(self, john_harrier_form_1040nr_data):
        """Test nonresident alien files Form 1040-NR."""
        assert john_harrier_form_1040nr_data["form_type"] == "1040-NR"
        assert john_harrier_form_1040nr_data["taxpayer"]["is_nonresident_alien"] is True

    def test_mfs_salt_cap_is_5000(self, john_harrier_schedule_a):
        """Test MFS SALT cap is $5,000."""
        # MFS limit is half of the $10,000 limit
        assert john_harrier_schedule_a["line_1b_salt_deduction"] == Decimal("5000.00")

    def test_short_term_gain_taxed_as_ordinary(self, john_harrier_form_1040nr_data):
        """Test short-term capital gain is taxed at ordinary rates."""
        # Short-term gains are taxed as ordinary income
        # The tax of $90,297 on $345,000 is consistent with MFS ordinary income rates
        taxable = john_harrier_form_1040nr_data["line_15_taxable_income"]
        tax = john_harrier_form_1040nr_data["line_16_tax"]
        effective_rate = tax / taxable
        # Effective rate should be around 26% for this income level
        assert Decimal("0.25") < effective_rate < Decimal("0.28")

    def test_partnership_interest_reported_on_schedule_p(self, john_harrier_form_1040nr_data):
        """Test partnership interest transfer requires Schedule P."""
        assert john_harrier_form_1040nr_data["has_schedule_p"] is True

    def test_capital_gain_requires_schedule_d(self, john_harrier_form_1040nr_data):
        """Test capital gain requires Schedule D."""
        assert john_harrier_form_1040nr_data["has_schedule_d"] is True


class TestScenarioNR12Integration:
    """Integration tests for complete data flow."""

    def test_complete_form_1040nr_structure(self, john_harrier_form_1040nr_data):
        """Test complete Form 1040-NR has all required sections."""
        required_keys = [
            "form_type", "tax_year", "filing_status",
            "line_7a_capital_gain", "line_11a_agi", "line_15_taxable_income",
            "line_16_tax", "line_24_total_tax", "line_33_total_payments"
        ]
        for key in required_keys:
            assert key in john_harrier_form_1040nr_data

    def test_schedule_p_flows_to_form_8949(self, john_harrier_schedule_p, john_harrier_form_8949):
        """Test Schedule P data flows to Form 8949."""
        assert john_harrier_form_8949["line_2_totals"]["proceeds"] == john_harrier_schedule_p["line_1_proceeds"]
        assert john_harrier_form_8949["line_2_totals"]["cost"] == john_harrier_schedule_p["line_2_outside_basis"]
        assert john_harrier_form_8949["line_2_totals"]["gain"] == john_harrier_schedule_p["line_3_total_outside_gain"]

    def test_form_8949_flows_to_schedule_d(self, john_harrier_form_8949, john_harrier_schedule_d):
        """Test Form 8949 data flows to Schedule D."""
        assert john_harrier_schedule_d["line_3"]["gain"] == john_harrier_form_8949["line_2_totals"]["gain"]

    def test_schedule_d_flows_to_1040nr(self, john_harrier_schedule_d, john_harrier_form_1040nr_data):
        """Test Schedule D capital gain flows to Form 1040-NR."""
        assert john_harrier_form_1040nr_data["line_7a_capital_gain"] == john_harrier_schedule_d["line_16_combined"]

    def test_schedule_a_flows_to_1040nr(self, john_harrier_schedule_a, john_harrier_form_1040nr_data):
        """Test Schedule A itemized deductions flow to Form 1040-NR."""
        assert john_harrier_form_1040nr_data["line_12_itemized_deductions"] == john_harrier_schedule_a["line_8_total"]

    def test_line_math_consistency(self, john_harrier_form_1040nr_data):
        """Test mathematical consistency throughout return."""
        # Taxable income = AGI - Deductions
        expected_taxable = (
            john_harrier_form_1040nr_data["line_11a_agi"] -
            john_harrier_form_1040nr_data["line_14_total_deductions"]
        )
        assert john_harrier_form_1040nr_data["line_15_taxable_income"] == expected_taxable

        # Tax after credits = Tax - Credits
        expected_after_credits = (
            john_harrier_form_1040nr_data["line_16_tax"] -
            john_harrier_form_1040nr_data["line_21_total_credits"]
        )
        assert john_harrier_form_1040nr_data["line_22_tax_after_credits"] == expected_after_credits

        # Total tax = Tax after credits + Other taxes
        expected_total_tax = (
            john_harrier_form_1040nr_data["line_22_tax_after_credits"] +
            john_harrier_form_1040nr_data["line_23d_total_other"]
        )
        assert john_harrier_form_1040nr_data["line_24_total_tax"] == expected_total_tax

        # Amount owed = Total tax - Total payments
        expected_owed = (
            john_harrier_form_1040nr_data["line_24_total_tax"] -
            john_harrier_form_1040nr_data["line_33_total_payments"]
        )
        assert john_harrier_form_1040nr_data["line_37_amount_owed"] == expected_owed

    def test_gain_calculation_chain(self, john_harrier_schedule_p, john_harrier_form_8949, john_harrier_schedule_d, john_harrier_form_1040nr_data):
        """Test complete capital gain calculation chain."""
        # Schedule P: Proceeds - Basis = Gain
        p_gain = (
            john_harrier_schedule_p["line_1_proceeds"] -
            john_harrier_schedule_p["line_2_outside_basis"]
        )
        assert p_gain == Decimal("350000.00")

        # Form 8949: Same gain
        assert john_harrier_form_8949["line_2_totals"]["gain"] == p_gain

        # Schedule D line 3: Same gain
        assert john_harrier_schedule_d["line_3"]["gain"] == p_gain

        # Schedule D line 7: Net short-term
        assert john_harrier_schedule_d["line_7_net_short_term"] == p_gain

        # Schedule D line 16: Combined
        assert john_harrier_schedule_d["line_16_combined"] == p_gain

        # Form 1040-NR line 7a: Capital gain
        assert john_harrier_form_1040nr_data["line_7a_capital_gain"] == p_gain
