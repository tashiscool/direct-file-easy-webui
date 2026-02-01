"""Comprehensive pytest tests for IRS ATS Test Scenario NR-2 - Genesis DeSilva.

This module tests the MeF (Modernized e-File) service functionality using
IRS ATS (Assurance Testing System) Test Scenario NR-2 data for Genesis DeSilva.

Test Scenario Reference: IRS ATS Test Scenario NR-2 (ty25-form-1040-nr-mef-ats-scenario-2-10202025.pdf)
Primary Taxpayer: Genesis DeSilva
Filing Status: Married Filing Separately (MFS)
No Dependents

Key Features Tested:
- Form 1040-NR (Nonresident Alien Income Tax Return)
- Schedule NEC (Tax on Income Not Effectively Connected with US Trade/Business)
- Schedule OI (Other Information) - visa status, entry/exit dates, treaty info
- Schedule E (Partnership income - passive)
- Schedule 1 (Additional Income)
- W-2 wage income
- Foreign address handling (Canada)
- 30% flat tax on NEC income
- Partnership K-1 passive income
- Paid preparer information

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
# FIXTURES - IRS ATS Test Scenario NR-2 Data (Genesis DeSilva - NRA with NEC)
# =============================================================================


@pytest.fixture
def genesis_desilva_taxpayer() -> Dict[str, Any]:
    """Fixture for Genesis DeSilva (primary taxpayer) information.

    IRS ATS Test Scenario NR-2 - Nonresident alien from Canada
    with income not effectively connected with US trade/business.

    ATS Reference SSN: 123-00-3333 (invalid for production validation)
    Test SSN: 123-01-3333 (valid format for testing validation logic)
    """
    return {
        "first_name": "Genesis",
        "last_name": "DeSilva",
        "ssn": "123-01-3333",
        "ssn_clean": "123013333",
        "ssn_ats_reference": "123-00-3333",
        "address": {
            "street": "29 Woodlawn Avenue East",
            "city": "Toronto",
            "state": "",  # Foreign address - no US state
            "zip": "",    # Foreign address - no US zip
        },
        "foreign_address": {
            "country": "Canada",
            "province": "ON",
            "postal_code": "M4T 1B9",
        },
        "date_of_birth": date(1985, 6, 15),  # Approximate - not specified in PDF
        "occupation": "",
        "digital_assets": False,
        "is_nonresident_alien": True,
    }


@pytest.fixture
def genesis_desilva_schedule_oi() -> Dict[str, Any]:
    """Fixture for Schedule OI (Other Information).

    Contains visa status, entry/exit dates, and treaty information.
    """
    return {
        # Item A - Country of citizenship
        "citizenship_country": "CA",

        # Item B - Country of tax residence
        "tax_residence_country": "CA",

        # Item C - Applied for green card
        "applied_for_green_card": True,

        # Item D - US citizen or green card holder status
        "was_us_citizen": False,
        "was_green_card_holder": False,

        # Item E - Visa type
        "visa_type": "Visa Waiver",

        # Item F - Changed visa status
        "changed_visa_status": False,

        # Item G - US entry/exit dates in 2025
        "us_visits_2025": [
            {"entered": date(2025, 1, 3), "departed": date(2025, 1, 6)},
            {"entered": date(2025, 2, 23), "departed": date(2025, 2, 26)},
            {"entered": date(2025, 4, 6), "departed": date(2025, 4, 9)},
            {"entered": date(2025, 5, 1), "departed": date(2025, 5, 13)},
            {"entered": date(2025, 6, 1), "departed": date(2025, 6, 10)},
            {"entered": date(2025, 7, 4), "departed": date(2025, 7, 14)},
            {"entered": date(2025, 8, 14), "departed": date(2025, 8, 16)},
            {"entered": date(2025, 10, 16), "departed": date(2025, 10, 18)},
        ],

        # Item H - Days in US
        "days_in_us_2023": 110,
        "days_in_us_2024": 110,
        "days_in_us_2025": 110,

        # Item I - Filed prior US return
        "filed_prior_us_return": False,

        # Item J - Trust return
        "filing_for_trust": False,

        # Item K - Compensation over $250,000
        "compensation_over_250k": False,

        # Item L - Treaty-exempt income
        "has_treaty_exempt_income": False,
        "treaty_country": None,
        "treaty_article": None,
        "treaty_exempt_amount": Decimal("0.00"),

        # Item M - Real property election
        "real_property_election_first_year": False,
        "real_property_election_prior_year": False,
    }


@pytest.fixture
def genesis_desilva_w2() -> Dict[str, Any]:
    """Fixture for W-2 from Panaderia Luna de Azucar.

    Employment income effectively connected with US trade/business.
    """
    return {
        "employee_name": "Genesis DeSilva",
        "employee_ssn": "123-01-3333",
        "employer_name": "Panaderia Luna de Azucar",
        "employer_ein": "00-5559991",
        "employer_ein_clean": "005559991",
        "employer_ein_test": "12-5559991",
        "employer_address": {
            "street": "1093 Yonge Street",
            "city": "Dallas",
            "state": "TX",
            "zip": "75019"
        },
        # Box 1 - Wages, tips, other compensation
        "box_1_wages": Decimal("25988.00"),
        # Box 2 - Federal income tax withheld
        "box_2_federal_withholding": Decimal("2916.00"),
        # Box 3 - Social security wages
        "box_3_ss_wages": Decimal("25988.00"),
        # Box 4 - Social security tax withheld
        "box_4_ss_tax": Decimal("1611.00"),
        # Box 5 - Medicare wages and tips
        "box_5_medicare_wages": Decimal("25988.00"),
        # Box 6 - Medicare tax withheld
        "box_6_medicare_tax": Decimal("377.00"),
        # Boxes 15-20 - State/local (not applicable)
        "box_15_state": "",
        "box_16_state_wages": Decimal("0.00"),
        "box_17_state_tax": Decimal("0.00"),
    }


@pytest.fixture
def genesis_desilva_schedule_nec() -> Dict[str, Any]:
    """Fixture for Schedule NEC (Not Effectively Connected Income).

    Tax on income not effectively connected with US trade/business.
    This income is taxed at flat 30% rate (or treaty rate).
    """
    return {
        "taxpayer_name": "Genesis DeSilva",
        "ssn": "123-01-3333",

        # Income types at different rates
        # Column (a) - 10% rate
        "dividends_us_corp_10pct": Decimal("0.00"),
        "dividends_foreign_corp_10pct": Decimal("0.00"),
        "interest_mortgage_10pct": Decimal("0.00"),
        "interest_foreign_corp_10pct": Decimal("0.00"),
        "interest_other_10pct": Decimal("0.00"),

        # Column (b) - 15% rate
        "dividends_us_corp_15pct": Decimal("0.00"),
        "dividends_foreign_corp_15pct": Decimal("0.00"),

        # Column (c) - 30% rate (default for NRA)
        "dividends_us_corp_30pct": Decimal("0.00"),
        "dividends_foreign_corp_30pct": Decimal("0.00"),
        "interest_mortgage_30pct": Decimal("0.00"),
        "interest_foreign_corp_30pct": Decimal("0.00"),
        "interest_other_30pct": Decimal("0.00"),
        "industrial_royalties_30pct": Decimal("0.00"),
        "motion_picture_royalties_30pct": Decimal("0.00"),
        "other_royalties_30pct": Decimal("0.00"),
        "real_property_income_30pct": Decimal("0.00"),
        "pensions_annuities_30pct": Decimal("0.00"),
        "social_security_30pct": Decimal("0.00"),
        "capital_gain_30pct": Decimal("0.00"),
        "gambling_30pct": Decimal("0.00"),
        "other_income_30pct": Decimal("1100.00"),  # LTC income

        # Line 12 - Other (specify type)
        "other_income_type": "LTC",  # Long-term care or other
        "other_income_amount": Decimal("1100.00"),

        # Line 13 - Total by column
        "total_10pct": Decimal("0.00"),
        "total_15pct": Decimal("0.00"),
        "total_30pct": Decimal("1100.00"),

        # Line 14 - Tax by column
        "tax_10pct": Decimal("0.00"),  # 0 * 0.10
        "tax_15pct": Decimal("0.00"),  # 0 * 0.15
        "tax_30pct": Decimal("330.00"),  # 1100 * 0.30

        # Line 15 - Total NEC tax
        "line_15_total_nec_tax": Decimal("330.00"),

        # Capital gains section (lines 16-18)
        "capital_gains": [],
        "line_17_capital_loss": Decimal("0.00"),
        "line_17_capital_gain": Decimal("0.00"),
        "line_18_net_capital_gain": Decimal("0.00"),
    }


@pytest.fixture
def genesis_desilva_schedule_e() -> Dict[str, Any]:
    """Fixture for Schedule E (Supplemental Income and Loss).

    Part II - Partnership income from Sarah's Vegan Bakery.
    """
    return {
        "taxpayer_name": "Genesis DeSilva",
        "ssn": "123-01-3333",

        # Part I - Rental Real Estate (not used)
        "rental_properties": [],

        # Part II - Partnerships and S Corporations
        "partnerships": [
            {
                "name": "Sarah's Vegan Bakery",
                "type": "P",  # Partnership
                "is_foreign": False,
                "ein": "00-1234567",
                "ein_clean": "001234567",
                "basis_required": False,
                "at_risk": True,

                # Passive income/loss
                "passive_loss": Decimal("0.00"),
                "passive_income": Decimal("500.00"),

                # Nonpassive income/loss
                "nonpassive_loss": Decimal("0.00"),
                "section_179_expense": Decimal("0.00"),
                "nonpassive_income": Decimal("0.00"),
            }
        ],

        # Line 29a totals
        "total_passive_income": Decimal("500.00"),
        "total_nonpassive_income": Decimal("0.00"),

        # Line 29b totals
        "total_passive_loss": Decimal("0.00"),
        "total_nonpassive_loss": Decimal("0.00"),
        "total_section_179": Decimal("0.00"),

        # Line 30 - Add positive amounts
        "line_30_income": Decimal("500.00"),

        # Line 31 - Add losses
        "line_31_losses": Decimal("0.00"),

        # Line 32 - Partnership/S Corp total
        "line_32_total": Decimal("500.00"),

        # Part III - Estates and Trusts (not used)
        "estates_trusts": [],

        # Part IV - REMICs (not used)
        "remics": [],

        # Part V - Summary
        "line_40_farm_rental": Decimal("0.00"),
        "line_41_total": Decimal("500.00"),
    }


@pytest.fixture
def genesis_desilva_schedule_1() -> Dict[str, Any]:
    """Fixture for Schedule 1 (Additional Income and Adjustments).

    Part I - Additional Income (from Schedule E)
    Part II - Adjustments to Income
    """
    return {
        "taxpayer_name": "Genesis DeSilva",
        "ssn": "123-01-3333",

        # Part I - Additional Income
        "line_1_state_refunds": Decimal("0.00"),
        "line_2a_alimony": Decimal("0.00"),
        "line_3_business_income": Decimal("0.00"),
        "line_4_other_gains": Decimal("0.00"),
        "line_5_rental_royalty": Decimal("500.00"),  # From Schedule E
        "line_6_farm_income": Decimal("0.00"),
        "line_7_unemployment": Decimal("0.00"),
        "line_9_other_income_total": Decimal("0.00"),
        "line_10_total_additional_income": Decimal("500.00"),

        # Part II - Adjustments to Income
        "line_11_educator": Decimal("0.00"),
        "line_15_se_tax_deduction": Decimal("0.00"),
        "line_20_ira_deduction": Decimal("0.00"),
        "line_21_student_loan": Decimal("0.00"),
        "line_26_total_adjustments": Decimal("0.00"),
    }


@pytest.fixture
def genesis_desilva_paid_preparer() -> Dict[str, Any]:
    """Fixture for paid preparer information."""
    return {
        "preparer_name": "John Doe",
        "preparer_signature_date": date(2026, 4, 2),
        "ptin": "",  # Not shown in PDF
        "self_employed": False,
        "firm_name": "Wells and Associates",
        "firm_address": {
            "street": "4545 Summer Drive",
            "city": "Dallas",
            "state": "TX",
            "zip": "75019"
        },
        "firm_phone": "(800) 555-4456",
        "firm_ein": "00-5556664",
    }


@pytest.fixture
def genesis_desilva_form_1040nr_data(
    genesis_desilva_taxpayer,
    genesis_desilva_schedule_oi,
    genesis_desilva_w2,
    genesis_desilva_schedule_nec,
    genesis_desilva_schedule_e,
    genesis_desilva_schedule_1,
    genesis_desilva_paid_preparer
) -> Dict[str, Any]:
    """Fixture for complete Form 1040-NR data for Genesis DeSilva.

    Tax Year: 2025
    Filing Status: Married Filing Separately (MFS)

    This scenario includes both:
    1. Effectively connected income (W-2 wages, partnership)
    2. Not effectively connected income (Schedule NEC - LTC)
    """
    # W-2 income (effectively connected)
    w2_wages = genesis_desilva_w2["box_1_wages"]
    w2_withholding = genesis_desilva_w2["box_2_federal_withholding"]

    # Schedule 1 additional income
    schedule_1_income = genesis_desilva_schedule_1["line_10_total_additional_income"]

    # Total effectively connected income (Line 9)
    line_1z_wages = w2_wages
    line_8_schedule_1 = schedule_1_income
    line_9_total_eci = line_1z_wages + line_8_schedule_1

    # Adjustments (Line 10)
    line_10_adjustments = genesis_desilva_schedule_1["line_26_total_adjustments"]

    # AGI (Line 11a)
    line_11a_agi = line_9_total_eci - line_10_adjustments

    # Deductions - NRA generally cannot use standard deduction
    line_12_deduction = Decimal("0.00")
    line_13a_qbi = Decimal("0.00")
    line_14_total_deductions = line_12_deduction + line_13a_qbi

    # Taxable income (Line 15)
    line_15_taxable_income = max(Decimal("0"), line_11a_agi - line_14_total_deductions)

    # Tax on effectively connected income (Line 16)
    # Using MFS tax brackets
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

    # Lines 17-22 (no additional taxes or credits from Schedule 2/3)
    line_17_schedule_2 = Decimal("0")
    line_18_total = line_16_tax + line_17_schedule_2
    line_19_ctc = Decimal("0")
    line_20_schedule_3 = Decimal("0")
    line_21_credits = line_19_ctc + line_20_schedule_3
    line_22_tax_minus_credits = max(Decimal("0"), line_18_total - line_21_credits)

    # Line 23 - Other taxes
    # Line 23a - Tax on NEC income (from Schedule NEC)
    line_23a_nec_tax = genesis_desilva_schedule_nec["line_15_total_nec_tax"]
    line_23b_other_taxes = Decimal("0")  # No SE tax, etc.
    line_23c_transportation = Decimal("0")
    line_23d_total_other = line_23a_nec_tax + line_23b_other_taxes + line_23c_transportation

    # Line 24 - Total tax
    line_24_total_tax = line_22_tax_minus_credits + line_23d_total_other

    # Payments
    line_25a_w2_withholding = w2_withholding
    line_25d_total_withholding = line_25a_w2_withholding
    line_33_total_payments = line_25d_total_withholding

    # Refund or Amount Owed
    if line_33_total_payments > line_24_total_tax:
        line_34_overpaid = line_33_total_payments - line_24_total_tax
        line_37_amount_owed = Decimal("0")
    else:
        line_34_overpaid = Decimal("0")
        line_37_amount_owed = line_24_total_tax - line_33_total_payments

    return {
        # Form identification
        "form_type": "1040-NR",
        "tax_year": 2025,

        # Taxpayer info
        "primary_ssn": genesis_desilva_taxpayer["ssn_clean"],
        "primary_first_name": genesis_desilva_taxpayer["first_name"],
        "primary_last_name": genesis_desilva_taxpayer["last_name"],
        "address": genesis_desilva_taxpayer["address"],
        "foreign_address": genesis_desilva_taxpayer["foreign_address"],
        "filing_status": 2,  # MFS on Form 1040-NR
        "is_nonresident_alien": True,

        # Checkboxes
        "digital_assets": False,

        # No dependents
        "dependents": [],

        # Income Section (Lines 1-9)
        "line_1a_w2_wages": w2_wages,
        "line_1z_total_wages": line_1z_wages,
        "line_4a_ira_distributions": Decimal("0"),
        "line_4b_taxable_ira": Decimal("0"),
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
        "line_23a_nec_tax": line_23a_nec_tax,
        "line_23b_other_taxes": line_23b_other_taxes,
        "line_23c_transportation": line_23c_transportation,
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
        "has_schedule_e": True,
        "has_schedule_nec": True,
        "has_schedule_oi": True,
        "has_paid_preparer": True,

        # Detailed form data
        "w2": genesis_desilva_w2,
        "schedule_oi": genesis_desilva_schedule_oi,
        "schedule_nec": genesis_desilva_schedule_nec,
        "schedule_e": genesis_desilva_schedule_e,
        "schedule_1": genesis_desilva_schedule_1,
        "paid_preparer": genesis_desilva_paid_preparer,
    }


# =============================================================================
# TEST CLASS: Taxpayer Information
# =============================================================================


class TestTaxpayerInformation:
    """Tests for taxpayer information."""

    def test_taxpayer_name(self, genesis_desilva_taxpayer):
        """Test taxpayer name."""
        assert genesis_desilva_taxpayer["first_name"] == "Genesis"
        assert genesis_desilva_taxpayer["last_name"] == "DeSilva"

    def test_taxpayer_ssn(self, genesis_desilva_taxpayer):
        """Test taxpayer SSN format."""
        ssn_clean = genesis_desilva_taxpayer["ssn_clean"]
        assert len(ssn_clean) == 9
        assert ssn_clean.isdigit()

    def test_taxpayer_is_nonresident_alien(self, genesis_desilva_taxpayer):
        """Test taxpayer is flagged as nonresident alien."""
        assert genesis_desilva_taxpayer["is_nonresident_alien"] is True

    def test_foreign_address(self, genesis_desilva_taxpayer):
        """Test foreign address components."""
        foreign = genesis_desilva_taxpayer["foreign_address"]
        assert foreign["country"] == "Canada"
        assert foreign["province"] == "ON"
        assert foreign["postal_code"] == "M4T 1B9"


# =============================================================================
# TEST CLASS: Schedule OI (Other Information)
# =============================================================================


class TestScheduleOI:
    """Tests for Schedule OI (Other Information)."""

    def test_citizenship(self, genesis_desilva_schedule_oi):
        """Test citizenship country."""
        assert genesis_desilva_schedule_oi["citizenship_country"] == "CA"

    def test_tax_residence(self, genesis_desilva_schedule_oi):
        """Test tax residence country."""
        assert genesis_desilva_schedule_oi["tax_residence_country"] == "CA"

    def test_green_card_application(self, genesis_desilva_schedule_oi):
        """Test green card application status."""
        assert genesis_desilva_schedule_oi["applied_for_green_card"] is True

    def test_not_former_us_citizen(self, genesis_desilva_schedule_oi):
        """Test never was US citizen."""
        assert genesis_desilva_schedule_oi["was_us_citizen"] is False

    def test_visa_type(self, genesis_desilva_schedule_oi):
        """Test visa type."""
        assert genesis_desilva_schedule_oi["visa_type"] == "Visa Waiver"

    def test_days_in_us(self, genesis_desilva_schedule_oi):
        """Test days in US for substantial presence test."""
        assert genesis_desilva_schedule_oi["days_in_us_2023"] == 110
        assert genesis_desilva_schedule_oi["days_in_us_2024"] == 110
        assert genesis_desilva_schedule_oi["days_in_us_2025"] == 110

    def test_us_visits_count(self, genesis_desilva_schedule_oi):
        """Test number of US visits in 2025."""
        visits = genesis_desilva_schedule_oi["us_visits_2025"]
        assert len(visits) == 8

    def test_no_treaty_exempt_income(self, genesis_desilva_schedule_oi):
        """Test no treaty-exempt income claimed."""
        assert genesis_desilva_schedule_oi["has_treaty_exempt_income"] is False


# =============================================================================
# TEST CLASS: W-2 Income
# =============================================================================


class TestW2Income:
    """Tests for W-2 wage income."""

    def test_employer_name(self, genesis_desilva_w2):
        """Test employer name."""
        assert genesis_desilva_w2["employer_name"] == "Panaderia Luna de Azucar"

    def test_wages(self, genesis_desilva_w2):
        """Test wages amount."""
        assert genesis_desilva_w2["box_1_wages"] == Decimal("25988.00")

    def test_federal_withholding(self, genesis_desilva_w2):
        """Test federal withholding."""
        assert genesis_desilva_w2["box_2_federal_withholding"] == Decimal("2916.00")

    def test_ss_wages_equal_wages(self, genesis_desilva_w2):
        """Test SS wages equal total wages."""
        assert genesis_desilva_w2["box_3_ss_wages"] == genesis_desilva_w2["box_1_wages"]

    def test_medicare_wages_equal_wages(self, genesis_desilva_w2):
        """Test Medicare wages equal total wages."""
        assert genesis_desilva_w2["box_5_medicare_wages"] == genesis_desilva_w2["box_1_wages"]


# =============================================================================
# TEST CLASS: Schedule NEC (Not Effectively Connected Income)
# =============================================================================


class TestScheduleNEC:
    """Tests for Schedule NEC tax on NEC income."""

    def test_other_income_type(self, genesis_desilva_schedule_nec):
        """Test other income type is LTC."""
        assert genesis_desilva_schedule_nec["other_income_type"] == "LTC"

    def test_other_income_amount(self, genesis_desilva_schedule_nec):
        """Test other income amount."""
        assert genesis_desilva_schedule_nec["other_income_amount"] == Decimal("1100.00")

    def test_30_percent_rate_income(self, genesis_desilva_schedule_nec):
        """Test income taxed at 30% rate."""
        assert genesis_desilva_schedule_nec["total_30pct"] == Decimal("1100.00")

    def test_30_percent_tax_calculation(self, genesis_desilva_schedule_nec):
        """Test 30% tax calculation."""
        income = genesis_desilva_schedule_nec["total_30pct"]
        expected_tax = income * Decimal("0.30")
        assert genesis_desilva_schedule_nec["tax_30pct"] == expected_tax
        assert genesis_desilva_schedule_nec["tax_30pct"] == Decimal("330.00")

    def test_total_nec_tax(self, genesis_desilva_schedule_nec):
        """Test total NEC tax."""
        total_tax = (genesis_desilva_schedule_nec["tax_10pct"] +
                     genesis_desilva_schedule_nec["tax_15pct"] +
                     genesis_desilva_schedule_nec["tax_30pct"])
        assert genesis_desilva_schedule_nec["line_15_total_nec_tax"] == total_tax
        assert genesis_desilva_schedule_nec["line_15_total_nec_tax"] == Decimal("330.00")


# =============================================================================
# TEST CLASS: Schedule E (Partnership Income)
# =============================================================================


class TestScheduleE:
    """Tests for Schedule E partnership income."""

    def test_partnership_name(self, genesis_desilva_schedule_e):
        """Test partnership name."""
        partnership = genesis_desilva_schedule_e["partnerships"][0]
        assert partnership["name"] == "Sarah's Vegan Bakery"

    def test_partnership_ein(self, genesis_desilva_schedule_e):
        """Test partnership EIN."""
        partnership = genesis_desilva_schedule_e["partnerships"][0]
        assert partnership["ein"] == "00-1234567"

    def test_passive_income(self, genesis_desilva_schedule_e):
        """Test passive income from partnership."""
        partnership = genesis_desilva_schedule_e["partnerships"][0]
        assert partnership["passive_income"] == Decimal("500.00")

    def test_line_41_total(self, genesis_desilva_schedule_e):
        """Test Schedule E line 41 total."""
        assert genesis_desilva_schedule_e["line_41_total"] == Decimal("500.00")


# =============================================================================
# TEST CLASS: Schedule 1 (Additional Income)
# =============================================================================


class TestSchedule1:
    """Tests for Schedule 1 additional income."""

    def test_rental_royalty_income(self, genesis_desilva_schedule_1):
        """Test rental/royalty income from Schedule E."""
        assert genesis_desilva_schedule_1["line_5_rental_royalty"] == Decimal("500.00")

    def test_total_additional_income(self, genesis_desilva_schedule_1):
        """Test total additional income."""
        assert genesis_desilva_schedule_1["line_10_total_additional_income"] == Decimal("500.00")

    def test_no_adjustments(self, genesis_desilva_schedule_1):
        """Test no adjustments to income."""
        assert genesis_desilva_schedule_1["line_26_total_adjustments"] == Decimal("0.00")


# =============================================================================
# TEST CLASS: Form 1040-NR Tax Calculation
# =============================================================================


class TestForm1040NRTaxCalculation:
    """Tests for Form 1040-NR tax calculations."""

    def test_form_type(self, genesis_desilva_form_1040nr_data):
        """Test form type is 1040-NR."""
        assert genesis_desilva_form_1040nr_data["form_type"] == "1040-NR"

    def test_total_wages(self, genesis_desilva_form_1040nr_data):
        """Test total wages."""
        assert genesis_desilva_form_1040nr_data["line_1z_total_wages"] == Decimal("25988.00")

    def test_schedule_1_income(self, genesis_desilva_form_1040nr_data):
        """Test Schedule 1 income flows to 1040-NR."""
        assert genesis_desilva_form_1040nr_data["line_8_schedule_1"] == Decimal("500.00")

    def test_total_eci(self, genesis_desilva_form_1040nr_data):
        """Test total effectively connected income."""
        expected = Decimal("25988.00") + Decimal("500.00")
        assert genesis_desilva_form_1040nr_data["line_9_total_eci"] == expected

    def test_agi_equals_eci_minus_adjustments(self, genesis_desilva_form_1040nr_data):
        """Test AGI calculation."""
        expected = (genesis_desilva_form_1040nr_data["line_9_total_eci"] -
                    genesis_desilva_form_1040nr_data["line_10_adjustments"])
        assert genesis_desilva_form_1040nr_data["line_11a_agi"] == expected

    def test_nec_tax_included(self, genesis_desilva_form_1040nr_data):
        """Test NEC tax is included in line 23a."""
        assert genesis_desilva_form_1040nr_data["line_23a_nec_tax"] == Decimal("330.00")

    def test_total_tax_includes_nec(self, genesis_desilva_form_1040nr_data):
        """Test total tax includes both ECI tax and NEC tax."""
        eci_tax = genesis_desilva_form_1040nr_data["line_22_tax_minus_credits"]
        nec_tax = genesis_desilva_form_1040nr_data["line_23a_nec_tax"]
        expected_total = eci_tax + nec_tax

        assert genesis_desilva_form_1040nr_data["line_24_total_tax"] == expected_total


# =============================================================================
# TEST CLASS: Paid Preparer
# =============================================================================


class TestPaidPreparer:
    """Tests for paid preparer information."""

    def test_preparer_name(self, genesis_desilva_paid_preparer):
        """Test preparer name."""
        assert genesis_desilva_paid_preparer["preparer_name"] == "John Doe"

    def test_firm_name(self, genesis_desilva_paid_preparer):
        """Test firm name."""
        assert genesis_desilva_paid_preparer["firm_name"] == "Wells and Associates"

    def test_firm_ein(self, genesis_desilva_paid_preparer):
        """Test firm EIN."""
        assert genesis_desilva_paid_preparer["firm_ein"] == "00-5556664"


# =============================================================================
# TEST CLASS: XML Serialization
# =============================================================================


class TestScenarioNR2XMLSerialization:
    """Tests for XML serialization of Scenario NR-2 data."""

    def test_taxpayer_info_creation(self, genesis_desilva_taxpayer):
        """Test TaxpayerInfo object creation."""
        taxpayer_info = TaxpayerInfo(
            primary_ssn=genesis_desilva_taxpayer["ssn_clean"],
            primary_first_name=genesis_desilva_taxpayer["first_name"],
            primary_last_name=genesis_desilva_taxpayer["last_name"],
            primary_date_of_birth=genesis_desilva_taxpayer["date_of_birth"],
        )

        assert taxpayer_info.primary_ssn == "123013333"
        assert taxpayer_info.primary_first_name == "Genesis"
        assert taxpayer_info.primary_last_name == "DeSilva"

    def test_submission_id_generation(self):
        """Test MeF submission ID generation."""
        submission_id = SubmissionId.generate(efin="123456", sequence=1)

        assert len(submission_id.submission_id) == 20
        assert submission_id.submission_id.isdigit()


# =============================================================================
# TEST CLASS: Business Rules Validation
# =============================================================================


class TestScenarioNR2BusinessRules:
    """Tests for business rules validation of Scenario NR-2 data."""

    def test_nra_uses_1040nr(self, genesis_desilva_form_1040nr_data):
        """Test nonresident alien files Form 1040-NR."""
        assert genesis_desilva_form_1040nr_data["form_type"] == "1040-NR"
        assert genesis_desilva_form_1040nr_data["is_nonresident_alien"] is True

    def test_nec_income_taxed_separately(self, genesis_desilva_form_1040nr_data):
        """Test NEC income is taxed separately at flat rate."""
        # NEC income ($1,100) should not be in line 9 (ECI)
        # It should be taxed on Schedule NEC at 30%
        nec_tax = genesis_desilva_form_1040nr_data["line_23a_nec_tax"]
        assert nec_tax == Decimal("330.00")

    def test_partnership_income_is_eci(self, genesis_desilva_form_1040nr_data):
        """Test partnership income is effectively connected income."""
        # Partnership income flows through Schedule 1 to line 8
        schedule_1 = genesis_desilva_form_1040nr_data["line_8_schedule_1"]
        assert schedule_1 == Decimal("500.00")


# =============================================================================
# TEST CLASS: Integration Tests
# =============================================================================


class TestScenarioNR2Integration:
    """Integration tests for the complete Scenario NR-2 data."""

    def test_complete_form_1040nr_structure(self, genesis_desilva_form_1040nr_data):
        """Test complete form data has all required fields."""
        required_fields = [
            "form_type", "tax_year", "primary_ssn",
            "primary_first_name", "primary_last_name",
            "filing_status", "is_nonresident_alien",
            "total_income", "agi", "taxable_income",
            "total_tax", "total_payments",
            "line_23a_nec_tax",  # NEC-specific
        ]

        for field in required_fields:
            assert field in genesis_desilva_form_1040nr_data, f"Missing field: {field}"

    def test_schedule_e_flows_to_schedule_1(
        self,
        genesis_desilva_schedule_e,
        genesis_desilva_schedule_1
    ):
        """Test Schedule E flows to Schedule 1 line 5."""
        assert (genesis_desilva_schedule_e["line_41_total"] ==
                genesis_desilva_schedule_1["line_5_rental_royalty"])

    def test_schedule_1_flows_to_1040nr(
        self,
        genesis_desilva_schedule_1,
        genesis_desilva_form_1040nr_data
    ):
        """Test Schedule 1 flows to Form 1040-NR line 8."""
        assert (genesis_desilva_schedule_1["line_10_total_additional_income"] ==
                genesis_desilva_form_1040nr_data["line_8_schedule_1"])

    def test_schedule_nec_flows_to_1040nr(
        self,
        genesis_desilva_schedule_nec,
        genesis_desilva_form_1040nr_data
    ):
        """Test Schedule NEC flows to Form 1040-NR line 23a."""
        assert (genesis_desilva_schedule_nec["line_15_total_nec_tax"] ==
                genesis_desilva_form_1040nr_data["line_23a_nec_tax"])

    def test_w2_withholding_flows_to_payments(self, genesis_desilva_form_1040nr_data):
        """Test W-2 withholding flows to payments section."""
        w2_wh = genesis_desilva_form_1040nr_data["w2"]["box_2_federal_withholding"]
        assert genesis_desilva_form_1040nr_data["line_25a_w2_withholding"] == w2_wh

    def test_refund_or_owed_calculation(self, genesis_desilva_form_1040nr_data):
        """Test refund/amount owed is correctly calculated."""
        payments = genesis_desilva_form_1040nr_data["total_payments"]
        tax = genesis_desilva_form_1040nr_data["total_tax"]
        refund = genesis_desilva_form_1040nr_data["refund"]
        owed = genesis_desilva_form_1040nr_data["amount_owed"]

        if payments > tax:
            assert refund == payments - tax
            assert owed == Decimal("0")
        else:
            assert refund == Decimal("0")
            assert owed == tax - payments

    def test_dual_taxation_structure(self, genesis_desilva_form_1040nr_data):
        """Test Form 1040-NR has both ECI and NEC taxation."""
        # ECI tax on line 16
        eci_tax = genesis_desilva_form_1040nr_data["line_16_tax"]
        assert eci_tax > Decimal("0")

        # NEC tax on line 23a
        nec_tax = genesis_desilva_form_1040nr_data["line_23a_nec_tax"]
        assert nec_tax == Decimal("330.00")

        # Total includes both
        total_tax = genesis_desilva_form_1040nr_data["line_24_total_tax"]
        assert total_tax >= eci_tax + nec_tax


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
