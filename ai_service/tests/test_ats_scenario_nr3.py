"""Comprehensive pytest tests for IRS ATS Test Scenario NR-3 - Jace Alfaro.

This module tests the MeF (Modernized e-File) service functionality using
IRS ATS (Assurance Testing System) Test Scenario NR-3 data for Jace Alfaro.

Test Scenario Reference: IRS ATS Test Scenario NR-3 (ty25-1040-nr-mef-ats-scenario-3-12012025.pdf)
Primary Taxpayer: Jace Alfaro
Filing Status: Single
No Dependents

Key Features Tested:
- Form 1040-NR (Nonresident Alien Income Tax Return)
- Schedule A (Form 1040-NR) - Itemized Deductions
- Form 8283 (Noncash Charitable Contributions - Vehicle donation)
- Form 8888 (Allocation of Refund to multiple accounts)
- W-2 wage income
- State and local tax deduction (SALT)
- Foreign address handling (Spain)
- Section 301.9100-2 filing
- Form 1098-C attachment (assumed)

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
# FIXTURES - IRS ATS Test Scenario NR-3 Data (Jace Alfaro - Itemized Deductions)
# =============================================================================


@pytest.fixture
def jace_alfaro_taxpayer() -> Dict[str, Any]:
    """Fixture for Jace Alfaro (primary taxpayer) information.

    IRS ATS Test Scenario NR-3 - Nonresident alien from Spain
    with itemized deductions and vehicle donation.

    ATS Reference SSN: 123-00-4444 (invalid for production validation)
    Test SSN: 123-01-4444 (valid format for testing validation logic)
    """
    return {
        "first_name": "Jace",
        "last_name": "Alfaro",
        "ssn": "123-01-4444",
        "ssn_clean": "123014444",
        "ssn_ats_reference": "123-00-4444",
        "address": {
            "street": "147 Tomato Street",
            "city": "Logrono",
            "state": "",  # Foreign address - no US state
            "zip": "",    # Foreign address - no US zip
        },
        "foreign_address": {
            "country": "Spain",
            "province": "La Rioja",
            "postal_code": "26001",
        },
        "date_of_birth": date(1980, 5, 10),  # Approximate - not specified in PDF
        "occupation": "",
        "digital_assets": False,
        "is_nonresident_alien": True,
        "filed_pursuant_to_301_9100_2": True,  # Special filing provision
    }


@pytest.fixture
def jace_alfaro_w2() -> Dict[str, Any]:
    """Fixture for W-2 from Spain Bar and Grill.

    Employment income effectively connected with US trade/business.
    """
    return {
        "employee_name": "Jace Alfaro",
        "employee_ssn": "123-01-4444",
        "employer_name": "Spain Bar and Grill",
        "employer_ein": "03-3211167",
        "employer_ein_clean": "033211167",
        "employer_ein_test": "12-3211167",
        "employer_address": {
            "street": "2580 Food Lane",
            "city": "Los Angeles",
            "state": "CA",
            "zip": "90026"
        },
        # Box 1 - Wages, tips, other compensation
        "box_1_wages": Decimal("72102.00"),
        # Box 2 - Federal income tax withheld
        "box_2_federal_withholding": Decimal("21750.00"),
        # Box 3 - Social security wages
        "box_3_ss_wages": Decimal("72102.00"),
        # Box 4 - Social security tax withheld
        "box_4_ss_tax": Decimal("4470.00"),
        # Box 5 - Medicare wages and tips
        "box_5_medicare_wages": Decimal("72102.00"),
        # Box 6 - Medicare tax withheld
        "box_6_medicare_tax": Decimal("1045.00"),
        # Boxes 15-20 - State/local (not specified)
        "box_15_state": "",
        "box_16_state_wages": Decimal("0.00"),
        "box_17_state_tax": Decimal("0.00"),
    }


@pytest.fixture
def jace_alfaro_schedule_a() -> Dict[str, Any]:
    """Fixture for Schedule A (Form 1040-NR) - Itemized Deductions.

    Nonresident aliens use the special Schedule A for Form 1040-NR
    which has different rules than the regular Schedule A.
    """
    return {
        "taxpayer_name": "Jace Alfaro",
        "ssn": "123-01-4444",

        # Taxes You Paid
        "line_1a_state_local_taxes": Decimal("18860.00"),
        # Line 1b - smaller of 1a or $40,000 ($20,000 if MFS)
        # For Single: min(18860, 40000) = 18860
        "line_1b_salt_deduction": Decimal("18860.00"),

        # Gifts to U.S. Charities
        "line_2_cash_gifts": Decimal("0.00"),
        "line_3_noncash_gifts": Decimal("5005.00"),  # Vehicle donation from Form 8283
        "line_4_carryover": Decimal("0.00"),
        "line_5_total_gifts": Decimal("5005.00"),

        # Casualty and Theft Losses
        "line_6_casualty_loss": Decimal("0.00"),

        # Other Itemized Deductions
        "line_7_other": Decimal("0.00"),

        # Total Itemized Deductions
        "line_8_total": Decimal("23865.00"),  # 18860 + 5005
    }


@pytest.fixture
def jace_alfaro_form_8283() -> Dict[str, Any]:
    """Fixture for Form 8283 (Noncash Charitable Contributions).

    Section B - Donated Property Over $5,000 (Vehicle donation).
    """
    return {
        "taxpayer_name": "Jace Alfaro",
        "ssn": "123-01-4444",

        # Entity that made the contribution (if different)
        "entity_name": "Spain Bar and Grill",
        "entity_ein": "03-3211167",

        # Section B - Donated Property Over $5,000
        "section_b_items": [
            {
                "item_letter": "A",
                "property_type": "Vehicles",  # Box i checked
                "description": "2005 Mercedes Benz",
                "condition": "Good",
                "appraised_fmv": Decimal("5005.00"),
                "date_acquired": "Various",
                "how_acquired": "Purchase",
                "donors_cost_basis": Decimal("53470.00"),
                "bargain_sale_amount": Decimal("0.00"),
                "amount_claimed": Decimal("5005.00"),  # Limited to FMV
            }
        ],

        # Attachments
        "form_1098c_attached": True,
        "vehicle_statement_attached": True,
    }


@pytest.fixture
def jace_alfaro_form_8888() -> Dict[str, Any]:
    """Fixture for Form 8888 (Allocation of Refund).

    Refund split into multiple accounts:
    - $1,000 to savings account 1
    - $1,000 to savings account 2
    - Remainder to checking account
    """
    return {
        "taxpayer_name": "Jace Alfaro",
        "ssn": "123-01-4444",
        "tax_year": 2025,

        # Account allocations
        "accounts": [
            {
                "account_number": 1,
                "routing_number": "024567891",
                "account_number_value": "11111111111111111",
                "account_type": "checking",
                "amount": None,  # Remainder - calculated later
            },
            {
                "account_number": 2,
                "routing_number": "012345678",
                "account_number_value": "1234567",
                "account_type": "savings",
                "amount": Decimal("1000.00"),
            },
            {
                "account_number": 3,
                "routing_number": "221277735",
                "account_number_value": "222222222222222",
                "account_type": "savings",
                "amount": Decimal("1000.00"),
            },
        ],

        # Total allocation (must equal refund)
        "savings_allocation": Decimal("2000.00"),  # 1000 + 1000
    }


@pytest.fixture
def jace_alfaro_form_1040nr_data(
    jace_alfaro_taxpayer,
    jace_alfaro_w2,
    jace_alfaro_schedule_a,
    jace_alfaro_form_8283,
    jace_alfaro_form_8888
) -> Dict[str, Any]:
    """Fixture for complete Form 1040-NR data for Jace Alfaro.

    Tax Year: 2025
    Filing Status: Single

    Uses itemized deductions (Schedule A) instead of standard deduction.
    """
    # W-2 income
    w2_wages = jace_alfaro_w2["box_1_wages"]
    w2_withholding = jace_alfaro_w2["box_2_federal_withholding"]

    # Total income (Line 9)
    line_1z_wages = w2_wages
    line_9_total_eci = line_1z_wages  # No other income

    # Adjustments (Line 10)
    line_10_adjustments = Decimal("0.00")

    # AGI (Line 11a)
    line_11a_agi = line_9_total_eci - line_10_adjustments

    # Itemized Deductions (Line 12)
    line_12_deduction = jace_alfaro_schedule_a["line_8_total"]

    # QBI Deduction (Line 13a)
    line_13a_qbi = Decimal("0.00")

    # Total Deductions (Line 14)
    line_14_total_deductions = line_12_deduction + line_13a_qbi

    # Taxable Income (Line 15)
    line_15_taxable_income = max(Decimal("0"), line_11a_agi - line_14_total_deductions)

    # Tax Calculation (Line 16) - Single tax brackets
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

    line_16_tax = line_16_tax.quantize(Decimal("1"))

    # Lines 17-22 (no additional taxes or credits)
    line_17_schedule_2 = Decimal("0")
    line_18_total = line_16_tax + line_17_schedule_2
    line_19_ctc = Decimal("0")
    line_20_schedule_3 = Decimal("0")
    line_21_credits = line_19_ctc + line_20_schedule_3
    line_22_tax_minus_credits = max(Decimal("0"), line_18_total - line_21_credits)

    # Line 23 - Other taxes (none)
    line_23a_nec_tax = Decimal("0")
    line_23b_other_taxes = Decimal("0")
    line_23d_total_other = Decimal("0")

    # Line 24 - Total tax
    line_24_total_tax = line_22_tax_minus_credits + line_23d_total_other

    # Payments
    line_25a_w2_withholding = w2_withholding
    line_25d_total_withholding = line_25a_w2_withholding
    line_33_total_payments = line_25d_total_withholding

    # Refund calculation
    if line_33_total_payments > line_24_total_tax:
        line_34_overpaid = line_33_total_payments - line_24_total_tax
        line_37_amount_owed = Decimal("0")
    else:
        line_34_overpaid = Decimal("0")
        line_37_amount_owed = line_24_total_tax - line_33_total_payments

    # Update Form 8888 with remainder allocation
    refund = line_34_overpaid
    savings_total = jace_alfaro_form_8888["savings_allocation"]
    checking_amount = refund - savings_total
    jace_alfaro_form_8888["accounts"][0]["amount"] = checking_amount

    return {
        # Form identification
        "form_type": "1040-NR",
        "tax_year": 2025,

        # Taxpayer info
        "primary_ssn": jace_alfaro_taxpayer["ssn_clean"],
        "primary_first_name": jace_alfaro_taxpayer["first_name"],
        "primary_last_name": jace_alfaro_taxpayer["last_name"],
        "address": jace_alfaro_taxpayer["address"],
        "foreign_address": jace_alfaro_taxpayer["foreign_address"],
        "filing_status": 1,  # Single
        "is_nonresident_alien": True,
        "filed_pursuant_to_301_9100_2": True,

        # Checkboxes
        "digital_assets": False,

        # No dependents
        "dependents": [],

        # Income Section (Lines 1-9)
        "line_1a_w2_wages": w2_wages,
        "line_1z_total_wages": line_1z_wages,
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
        "line_23a_nec_tax": line_23a_nec_tax,
        "line_23b_other_taxes": line_23b_other_taxes,
        "line_23d_total_other": line_23d_total_other,
        "line_24_total_tax": line_24_total_tax,

        # Payments (Lines 25-33)
        "line_25a_w2_withholding": line_25a_w2_withholding,
        "line_25d_total_withholding": line_25d_total_withholding,
        "line_33_total_payments": line_33_total_payments,

        # Refund (Lines 34-36)
        "line_34_overpaid": line_34_overpaid,
        "line_35a_refund": line_34_overpaid,
        "form_8888_attached": True,
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
        "has_schedule_a": True,
        "has_form_8283": True,
        "has_form_8888": True,
        "has_form_1098c": True,

        # Detailed form data
        "w2": jace_alfaro_w2,
        "schedule_a": jace_alfaro_schedule_a,
        "form_8283": jace_alfaro_form_8283,
        "form_8888": jace_alfaro_form_8888,
    }


# =============================================================================
# TEST CLASS: Taxpayer Information
# =============================================================================


class TestTaxpayerInformation:
    """Tests for taxpayer information."""

    def test_taxpayer_name(self, jace_alfaro_taxpayer):
        """Test taxpayer name."""
        assert jace_alfaro_taxpayer["first_name"] == "Jace"
        assert jace_alfaro_taxpayer["last_name"] == "Alfaro"

    def test_taxpayer_ssn(self, jace_alfaro_taxpayer):
        """Test taxpayer SSN format."""
        ssn_clean = jace_alfaro_taxpayer["ssn_clean"]
        assert len(ssn_clean) == 9
        assert ssn_clean.isdigit()

    def test_taxpayer_is_nonresident_alien(self, jace_alfaro_taxpayer):
        """Test taxpayer is flagged as nonresident alien."""
        assert jace_alfaro_taxpayer["is_nonresident_alien"] is True

    def test_foreign_address(self, jace_alfaro_taxpayer):
        """Test foreign address components."""
        foreign = jace_alfaro_taxpayer["foreign_address"]
        assert foreign["country"] == "Spain"
        assert foreign["province"] == "La Rioja"
        assert foreign["postal_code"] == "26001"

    def test_301_9100_2_filing(self, jace_alfaro_taxpayer):
        """Test section 301.9100-2 filing flag."""
        assert jace_alfaro_taxpayer["filed_pursuant_to_301_9100_2"] is True


# =============================================================================
# TEST CLASS: W-2 Income
# =============================================================================


class TestW2Income:
    """Tests for W-2 wage income."""

    def test_employer_name(self, jace_alfaro_w2):
        """Test employer name."""
        assert jace_alfaro_w2["employer_name"] == "Spain Bar and Grill"

    def test_wages(self, jace_alfaro_w2):
        """Test wages amount."""
        assert jace_alfaro_w2["box_1_wages"] == Decimal("72102.00")

    def test_federal_withholding(self, jace_alfaro_w2):
        """Test federal withholding."""
        assert jace_alfaro_w2["box_2_federal_withholding"] == Decimal("21750.00")

    def test_ss_tax(self, jace_alfaro_w2):
        """Test Social Security tax."""
        assert jace_alfaro_w2["box_4_ss_tax"] == Decimal("4470.00")

    def test_medicare_tax(self, jace_alfaro_w2):
        """Test Medicare tax."""
        assert jace_alfaro_w2["box_6_medicare_tax"] == Decimal("1045.00")


# =============================================================================
# TEST CLASS: Schedule A (Itemized Deductions)
# =============================================================================


class TestScheduleA:
    """Tests for Schedule A itemized deductions."""

    def test_state_local_taxes(self, jace_alfaro_schedule_a):
        """Test state and local taxes."""
        assert jace_alfaro_schedule_a["line_1a_state_local_taxes"] == Decimal("18860.00")

    def test_salt_cap_single(self, jace_alfaro_schedule_a):
        """Test SALT cap for single filer ($40,000)."""
        # For single filers, cap is $40,000
        # 18860 < 40000, so full amount is deductible
        assert jace_alfaro_schedule_a["line_1b_salt_deduction"] == Decimal("18860.00")

    def test_noncash_gifts(self, jace_alfaro_schedule_a):
        """Test noncash charitable gifts."""
        assert jace_alfaro_schedule_a["line_3_noncash_gifts"] == Decimal("5005.00")

    def test_total_gifts(self, jace_alfaro_schedule_a):
        """Test total charitable gifts."""
        expected = (jace_alfaro_schedule_a["line_2_cash_gifts"] +
                    jace_alfaro_schedule_a["line_3_noncash_gifts"] +
                    jace_alfaro_schedule_a["line_4_carryover"])
        assert jace_alfaro_schedule_a["line_5_total_gifts"] == expected

    def test_total_itemized_deductions(self, jace_alfaro_schedule_a):
        """Test total itemized deductions."""
        expected = (jace_alfaro_schedule_a["line_1b_salt_deduction"] +
                    jace_alfaro_schedule_a["line_5_total_gifts"] +
                    jace_alfaro_schedule_a["line_6_casualty_loss"] +
                    jace_alfaro_schedule_a["line_7_other"])
        assert jace_alfaro_schedule_a["line_8_total"] == expected
        assert jace_alfaro_schedule_a["line_8_total"] == Decimal("23865.00")


# =============================================================================
# TEST CLASS: Form 8283 (Noncash Charitable Contributions)
# =============================================================================


class TestForm8283:
    """Tests for Form 8283 noncash charitable contributions."""

    def test_property_type(self, jace_alfaro_form_8283):
        """Test donated property type is vehicle."""
        item = jace_alfaro_form_8283["section_b_items"][0]
        assert item["property_type"] == "Vehicles"

    def test_vehicle_description(self, jace_alfaro_form_8283):
        """Test vehicle description."""
        item = jace_alfaro_form_8283["section_b_items"][0]
        assert item["description"] == "2005 Mercedes Benz"
        assert item["condition"] == "Good"

    def test_appraised_fmv(self, jace_alfaro_form_8283):
        """Test appraised fair market value."""
        item = jace_alfaro_form_8283["section_b_items"][0]
        assert item["appraised_fmv"] == Decimal("5005.00")

    def test_donors_cost_basis(self, jace_alfaro_form_8283):
        """Test donor's cost basis."""
        item = jace_alfaro_form_8283["section_b_items"][0]
        assert item["donors_cost_basis"] == Decimal("53470.00")

    def test_deduction_limited_to_fmv(self, jace_alfaro_form_8283):
        """Test deduction is limited to FMV when FMV < cost."""
        item = jace_alfaro_form_8283["section_b_items"][0]
        # For vehicles, deduction is generally limited to lesser of FMV or basis
        assert item["amount_claimed"] <= item["appraised_fmv"]
        assert item["amount_claimed"] <= item["donors_cost_basis"]

    def test_form_1098c_attached(self, jace_alfaro_form_8283):
        """Test Form 1098-C is attached."""
        assert jace_alfaro_form_8283["form_1098c_attached"] is True


# =============================================================================
# TEST CLASS: Form 8888 (Allocation of Refund)
# =============================================================================


class TestForm8888:
    """Tests for Form 8888 refund allocation."""

    def test_three_accounts(self, jace_alfaro_form_8888):
        """Test refund is split into three accounts."""
        assert len(jace_alfaro_form_8888["accounts"]) == 3

    def test_savings_account_amounts(self, jace_alfaro_form_8888):
        """Test $1,000 allocated to each savings account."""
        savings_accounts = [a for a in jace_alfaro_form_8888["accounts"]
                           if a["account_type"] == "savings"]
        assert len(savings_accounts) == 2
        for account in savings_accounts:
            assert account["amount"] == Decimal("1000.00")

    def test_checking_account_exists(self, jace_alfaro_form_8888):
        """Test checking account exists."""
        checking_accounts = [a for a in jace_alfaro_form_8888["accounts"]
                            if a["account_type"] == "checking"]
        assert len(checking_accounts) == 1

    def test_savings_allocation_total(self, jace_alfaro_form_8888):
        """Test total savings allocation."""
        assert jace_alfaro_form_8888["savings_allocation"] == Decimal("2000.00")


# =============================================================================
# TEST CLASS: Form 1040-NR Tax Calculation
# =============================================================================


class TestForm1040NRTaxCalculation:
    """Tests for Form 1040-NR tax calculations."""

    def test_form_type(self, jace_alfaro_form_1040nr_data):
        """Test form type is 1040-NR."""
        assert jace_alfaro_form_1040nr_data["form_type"] == "1040-NR"

    def test_filing_status_single(self, jace_alfaro_form_1040nr_data):
        """Test filing status is Single."""
        assert jace_alfaro_form_1040nr_data["filing_status"] == 1

    def test_total_wages(self, jace_alfaro_form_1040nr_data):
        """Test total wages."""
        assert jace_alfaro_form_1040nr_data["line_1z_total_wages"] == Decimal("72102.00")

    def test_agi_calculation(self, jace_alfaro_form_1040nr_data):
        """Test AGI equals wages (no adjustments)."""
        assert jace_alfaro_form_1040nr_data["line_11a_agi"] == Decimal("72102.00")

    def test_itemized_deduction_used(self, jace_alfaro_form_1040nr_data):
        """Test itemized deduction is used."""
        # NRA with itemized deductions
        assert jace_alfaro_form_1040nr_data["line_12_deduction"] == Decimal("23865.00")
        assert jace_alfaro_form_1040nr_data["has_schedule_a"] is True

    def test_taxable_income(self, jace_alfaro_form_1040nr_data):
        """Test taxable income calculation."""
        expected = (jace_alfaro_form_1040nr_data["line_11a_agi"] -
                    jace_alfaro_form_1040nr_data["line_14_total_deductions"])
        assert jace_alfaro_form_1040nr_data["line_15_taxable_income"] == expected
        assert jace_alfaro_form_1040nr_data["line_15_taxable_income"] == Decimal("48237.00")

    def test_has_refund(self, jace_alfaro_form_1040nr_data):
        """Test taxpayer receives a refund."""
        assert jace_alfaro_form_1040nr_data["refund"] > Decimal("0")
        assert jace_alfaro_form_1040nr_data["amount_owed"] == Decimal("0")

    def test_form_8888_attached(self, jace_alfaro_form_1040nr_data):
        """Test Form 8888 is attached for refund allocation."""
        assert jace_alfaro_form_1040nr_data["form_8888_attached"] is True


# =============================================================================
# TEST CLASS: XML Serialization
# =============================================================================


class TestScenarioNR3XMLSerialization:
    """Tests for XML serialization of Scenario NR-3 data."""

    def test_taxpayer_info_creation(self, jace_alfaro_taxpayer):
        """Test TaxpayerInfo object creation."""
        taxpayer_info = TaxpayerInfo(
            primary_ssn=jace_alfaro_taxpayer["ssn_clean"],
            primary_first_name=jace_alfaro_taxpayer["first_name"],
            primary_last_name=jace_alfaro_taxpayer["last_name"],
            primary_date_of_birth=jace_alfaro_taxpayer["date_of_birth"],
        )

        assert taxpayer_info.primary_ssn == "123014444"
        assert taxpayer_info.primary_first_name == "Jace"
        assert taxpayer_info.primary_last_name == "Alfaro"

    def test_submission_id_generation(self):
        """Test MeF submission ID generation."""
        submission_id = SubmissionId.generate(efin="123456", sequence=1)

        assert len(submission_id.submission_id) == 20
        assert submission_id.submission_id.isdigit()


# =============================================================================
# TEST CLASS: Business Rules Validation
# =============================================================================


class TestScenarioNR3BusinessRules:
    """Tests for business rules validation of Scenario NR-3 data."""

    def test_nra_uses_1040nr(self, jace_alfaro_form_1040nr_data):
        """Test nonresident alien files Form 1040-NR."""
        assert jace_alfaro_form_1040nr_data["form_type"] == "1040-NR"
        assert jace_alfaro_form_1040nr_data["is_nonresident_alien"] is True

    def test_itemized_deductions_valid(self, jace_alfaro_form_1040nr_data):
        """Test itemized deductions are properly claimed."""
        schedule_a = jace_alfaro_form_1040nr_data["schedule_a"]
        # SALT + Charitable contributions
        assert schedule_a["line_8_total"] > Decimal("0")

    def test_vehicle_donation_over_500_requires_8283(self, jace_alfaro_form_1040nr_data):
        """Test vehicle donation over $500 requires Form 8283."""
        form_8283 = jace_alfaro_form_1040nr_data["form_8283"]
        item = form_8283["section_b_items"][0]

        # Donation over $500 requires Form 8283
        assert item["appraised_fmv"] > Decimal("500")
        assert jace_alfaro_form_1040nr_data["has_form_8283"] is True


# =============================================================================
# TEST CLASS: Integration Tests
# =============================================================================


class TestScenarioNR3Integration:
    """Integration tests for the complete Scenario NR-3 data."""

    def test_complete_form_1040nr_structure(self, jace_alfaro_form_1040nr_data):
        """Test complete form data has all required fields."""
        required_fields = [
            "form_type", "tax_year", "primary_ssn",
            "primary_first_name", "primary_last_name",
            "filing_status", "is_nonresident_alien",
            "total_income", "agi", "taxable_income",
            "total_tax", "total_payments", "refund",
            "has_schedule_a", "has_form_8283", "has_form_8888",
        ]

        for field in required_fields:
            assert field in jace_alfaro_form_1040nr_data, f"Missing field: {field}"

    def test_schedule_a_flows_to_1040nr(
        self,
        jace_alfaro_schedule_a,
        jace_alfaro_form_1040nr_data
    ):
        """Test Schedule A total flows to Form 1040-NR line 12."""
        assert (jace_alfaro_schedule_a["line_8_total"] ==
                jace_alfaro_form_1040nr_data["line_12_deduction"])

    def test_form_8283_flows_to_schedule_a(
        self,
        jace_alfaro_form_8283,
        jace_alfaro_schedule_a
    ):
        """Test Form 8283 noncash contribution flows to Schedule A."""
        item = jace_alfaro_form_8283["section_b_items"][0]
        assert item["amount_claimed"] == jace_alfaro_schedule_a["line_3_noncash_gifts"]

    def test_w2_withholding_flows_to_payments(self, jace_alfaro_form_1040nr_data):
        """Test W-2 withholding flows to payments section."""
        w2_wh = jace_alfaro_form_1040nr_data["w2"]["box_2_federal_withholding"]
        assert jace_alfaro_form_1040nr_data["line_25a_w2_withholding"] == w2_wh

    def test_refund_allocation_totals(self, jace_alfaro_form_1040nr_data):
        """Test Form 8888 allocations total to refund."""
        form_8888 = jace_alfaro_form_1040nr_data["form_8888"]
        refund = jace_alfaro_form_1040nr_data["refund"]

        # Sum all account allocations
        total_allocated = sum(
            a["amount"] for a in form_8888["accounts"]
            if a["amount"] is not None
        )

        assert total_allocated == refund

    def test_line_math_consistency(self, jace_alfaro_form_1040nr_data):
        """Test Form 1040-NR line math is consistent."""
        # Line 11 = Line 9 - Line 10
        assert jace_alfaro_form_1040nr_data["line_11a_agi"] == (
            jace_alfaro_form_1040nr_data["line_9_total_eci"] -
            jace_alfaro_form_1040nr_data["line_10_adjustments"]
        )

        # Line 15 = Line 11 - Line 14
        assert jace_alfaro_form_1040nr_data["line_15_taxable_income"] == (
            jace_alfaro_form_1040nr_data["line_11a_agi"] -
            jace_alfaro_form_1040nr_data["line_14_total_deductions"]
        )

        # Line 24 = Line 22 + Line 23d
        assert jace_alfaro_form_1040nr_data["line_24_total_tax"] == (
            jace_alfaro_form_1040nr_data["line_22_tax_minus_credits"] +
            jace_alfaro_form_1040nr_data["line_23d_total_other"]
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
