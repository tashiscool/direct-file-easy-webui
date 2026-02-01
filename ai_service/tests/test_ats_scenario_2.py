"""Comprehensive pytest tests for IRS ATS Test Scenario 2 - John and Judy Jones.

This module tests the MeF (Modernized e-File) service functionality using
IRS ATS (Assurance Testing System) Test Scenario 2 data for John and Judy Jones.

Test Scenario Reference: IRS ATS Test Scenario 2 (1040-mef-ats-scenario-2-12012025.pdf)
Primary Taxpayer: John Jones
Secondary Taxpayer: Judy Jones (Deceased 09/11/2025)
Filing Status: Married Filing Jointly (2)
One Dependent: Jacob Jones (Son, full-time high school student)

Key Features Tested:
- Married Filing Jointly with deceased spouse
- Spouse Identity Protection PIN (876543)
- Multiple W-2 forms (John from Southwest Airlines, Judy from Target)
- Schedule C (Statutory Employee - Furniture Sales)
- Schedule A (Itemized Deductions)
- Form 8283 (Noncash Charitable Contributions)
- Nonresident Spouse Choice Statement (binary attachment)
- Estimated tax payment applied from prior year
- Former spouse SSN for estimated payments

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
# FIXTURES - IRS ATS Test Scenario 2 Data (John and Judy Jones - MFJ)
# =============================================================================


@pytest.fixture
def john_jones_taxpayer() -> Dict[str, Any]:
    """Fixture for John Jones (primary taxpayer) information.

    IRS ATS Test Scenario 2 - Married Filing Jointly with deceased spouse.

    ATS Reference SSN: 400-00-1038
    """
    return {
        "first_name": "John",
        "last_name": "Jones",
        "ssn": "400-01-1038",
        "ssn_clean": "400011038",
        "ssn_ats_reference": "400-00-1038",
        "address": {
            "street": "800 Gooseneck Point Road",
            "city": "Oceanport",
            "state": "NJ",
            "zip": "07757"
        },
        "date_of_birth": date(1965, 8, 2),
        "occupation": "Sales Representative",
        "digital_assets": False,
    }


@pytest.fixture
def judy_jones_spouse() -> Dict[str, Any]:
    """Fixture for Judy Jones (deceased spouse) information.

    Spouse Identity Protection PIN: 876543
    Date of Death: September 11, 2025
    """
    return {
        "first_name": "Judy",
        "last_name": "Jones",
        "ssn": "400-01-1071",
        "ssn_clean": "400011071",
        "ssn_ats_reference": "400-00-1071",
        "date_of_birth": date(1966, 3, 19),
        "date_of_death": date(2025, 9, 11),
        "ip_pin": "876543",
        "is_nonresident_alien_treated_as_resident": True,
    }


@pytest.fixture
def jacob_jones_dependent() -> Dict[str, Any]:
    """Fixture for Jacob Jones (dependent) information.

    Full-time high school student.
    """
    return {
        "first_name": "Jacob",
        "last_name": "Jones",
        "ssn": "400-01-1070",
        "ssn_clean": "400011070",
        "ssn_ats_reference": "400-00-1070",
        "relationship": "Son",
        "date_of_birth": date(2006, 7, 20),
        "is_full_time_student": True,
        "lived_with_taxpayer": True,
        "months_in_us": 12,
        "qualifies_for_ctc": False,  # Over 16
        "qualifies_for_odc": True,  # Credit for Other Dependents
    }


@pytest.fixture
def john_jones_w2_data() -> Dict[str, Any]:
    """Fixture for John Jones W-2 from Southwest Airlines.

    Statutory employee - income reported on Schedule C.
    """
    return {
        "employee_name": "John Jones",
        "employer_name": "Southwest Airlines",
        "employer_ein": "00-1111111",
        "employer_ein_clean": "001111111",
        "employer_address": {
            "street": "5000 Flight Street",
            "street2": "77 North Washington Street",
            "city": "Boston",
            "state": "MA",
            "zip": "02114"
        },
        "wages": Decimal("29513.00"),
        "federal_withholding": Decimal("1003.00"),
        "ss_wages": Decimal("29513.00"),
        "ss_tax": Decimal("1830.00"),
        "medicare_wages": Decimal("29513.00"),
        "medicare_tax": Decimal("428.00"),
        "is_statutory_employee": True,
        "state": "NJ",
        "state_id": "00-0000056",
        "state_wages": Decimal("29513.00"),
        "state_tax": Decimal("927.00"),
    }


@pytest.fixture
def judy_jones_w2_data() -> Dict[str, Any]:
    """Fixture for Judy Jones W-2 from Target Corporation."""
    return {
        "employee_name": "Judy Jones",
        "employer_name": "Target Corporation",
        "employer_ein": "00-0000013",
        "employer_ein_clean": "000000013",
        "employer_address": {
            "street": "8652 James Street",
            "city": "Poughkeepsie",
            "state": "NY",
            "zip": "12601"
        },
        "wages": Decimal("8513.00"),
        "federal_withholding": Decimal("161.00"),
        "ss_wages": Decimal("8513.00"),
        "ss_tax": Decimal("528.00"),
        "medicare_wages": Decimal("8513.00"),
        "medicare_tax": Decimal("123.00"),
        "is_statutory_employee": False,
        "state": "NJ",
        "state_id": "00-0000056",
        "state_wages": Decimal("8513.00"),
        "state_tax": Decimal("101.00"),
    }


@pytest.fixture
def john_jones_schedule_c() -> Dict[str, Any]:
    """Fixture for Schedule C (Profit or Loss from Business).

    John is a statutory employee doing furniture sales.
    Principal Business Code: 449110 (Furniture Sales)
    """
    return {
        "proprietor_name": "John Jones",
        "principal_business": "Furniture Sales",
        "principal_business_code": "449110",
        "business_address": {
            "street": "800 Gooseneck Point Road",
            "city": "Oceanport",
            "state": "NJ",
            "zip": "07757"
        },
        "accounting_method": "Cash",
        "materially_participated": True,

        # Part I - Income (Statutory employee W-2 income)
        "line_1_gross_receipts": Decimal("0.00"),  # Reported on W-2
        "line_7_gross_income": Decimal("0.00"),

        # Part II - Expenses
        "expenses": {
            "line_8_advertising": Decimal("850.00"),
            "line_9_car_truck": Decimal("466.00"),
            "line_18_office_expense": Decimal("550.00"),
            "line_22_supplies": Decimal("610.00"),
            "line_23_taxes_licenses": Decimal("58.00"),
        },

        # Line 28 - Total expenses
        "line_28_total_expenses": Decimal("2534.00"),

        # Since statutory employee, net is a loss
        "line_31_net_profit_loss": Decimal("0.00"),

        # Part IV - Vehicle Information
        "vehicle_placed_in_service": date(2023, 8, 22),
        "business_miles": 665,
        "commuting_miles": 710,
        "other_miles": 15151,
        "vehicle_available_off_duty": True,
        "another_vehicle_available": True,
        "evidence_to_support": True,
        "evidence_written": True,
    }


@pytest.fixture
def jones_schedule_a() -> Dict[str, Any]:
    """Fixture for Schedule A (Itemized Deductions).

    Itemizing because total exceeds standard deduction.
    """
    return {
        # Medical and Dental (Line 1-4) - N/A

        # Taxes You Paid (Lines 5-7)
        "line_5a_state_local_income_tax": Decimal("1028.00"),
        "line_5b_real_estate_taxes": Decimal("8972.00"),
        "line_5c_personal_property_taxes": Decimal("0.00"),
        "line_5d_total_taxes": Decimal("10000.00"),
        "line_5e_salt_limited": Decimal("10000.00"),  # $10,000 SALT cap

        "line_7_total_taxes": Decimal("10000.00"),

        # Interest You Paid (Lines 8-10)
        "line_8a_home_mortgage_interest": Decimal("11000.00"),
        "line_8c_points_not_on_1098": Decimal("251.00"),
        "line_8e_total_mortgage_interest": Decimal("11251.00"),

        "line_10_total_interest": Decimal("11251.00"),

        # Gifts to Charity (Lines 11-14)
        # Per ATS additional info: dotted line = $200, line 11 = $250
        "line_11_cash_contributions": Decimal("250.00"),
        "line_11_dotted_line": Decimal("200.00"),  # Qualified contributions
        "line_12_other_contributions": Decimal("700.00"),  # From Form 8283
        "line_14_total_gifts": Decimal("950.00"),

        # Casualty and Theft (Line 15) - N/A
        # Other Itemized Deductions (Line 16) - N/A

        # Line 17 - Total Itemized Deductions
        # $10,000 (taxes) + $11,251 (interest) + $950 (gifts) = $22,201
        "line_17_total_itemized": Decimal("22201.00"),

        # Note: This exceeds MFJ standard deduction of ~$30,000 for 2025
        # Actually based on the form, they're electing to itemize even if less
        "elected_to_itemize": True,
    }


@pytest.fixture
def jones_form_8283() -> Dict[str, Any]:
    """Fixture for Form 8283 (Noncash Charitable Contributions).

    Clothes and toys donated to Goodwill.
    """
    return {
        # Section A - Donated Property of $5,000 or Less
        "donee_organization": {
            "name": "Goodwill",
            "address": "936 Folly Road, Charleston, SC 29412",
        },
        "donated_property": {
            "description": "Clothes & toys",
            "date_contributed": date(2025, 11, 13),
            "date_acquired": "Various",
            "how_acquired": "Purchase",
            "donors_cost_basis": Decimal("3470.00"),
            "fair_market_value": Decimal("700.00"),
            "fmv_method": "Thrift Store Value",
        },
    }


@pytest.fixture
def jones_schedule_1() -> Dict[str, Any]:
    """Fixture for Schedule 1 (Additional Income and Adjustments).

    Business income from Schedule C flows here.
    """
    return {
        # Part I - Additional Income
        "line_3_business_income": Decimal("0.00"),  # Statutory employee, no net

        "line_10_total_additional_income": Decimal("0.00"),

        # Part II - Adjustments to Income
        "line_26_total_adjustments": Decimal("0.00"),
    }


@pytest.fixture
def jones_form_1040_data(
    john_jones_taxpayer,
    judy_jones_spouse,
    jacob_jones_dependent,
    john_jones_w2_data,
    judy_jones_w2_data,
    john_jones_schedule_c,
    jones_schedule_a,
    jones_form_8283,
    jones_schedule_1
) -> Dict[str, Any]:
    """Fixture for complete Form 1040 data for John and Judy Jones.

    Tax Year: 2025
    Filing Status: Married Filing Jointly (2)
    """
    # Income
    john_wages = john_jones_w2_data["wages"]
    judy_wages = judy_jones_w2_data["wages"]
    total_wages = john_wages + judy_wages
    total_income = total_wages
    agi = total_income  # No adjustments

    # Deduction - Using itemized from Schedule A
    itemized_deduction = jones_schedule_a["line_17_total_itemized"]

    # Taxable income
    taxable_income = max(Decimal("0"), agi - itemized_deduction)

    # Tax calculation (2025 MFJ brackets)
    # $0 - $23,200: 10%
    # $23,201 - $94,300: 12%
    # Taxable income: ~$15,875 (all in 10% bracket)
    calculated_tax = (taxable_income * Decimal("0.10")).quantize(Decimal("1"))

    # Credits
    # Credit for Other Dependents: $500 for Jacob (over 16)
    odc_credit = Decimal("500.00")
    total_credits = odc_credit

    # Tax after credits
    tax_after_credits = max(Decimal("0"), calculated_tax - total_credits)

    # Total tax
    total_tax = tax_after_credits

    # Payments
    john_withholding = john_jones_w2_data["federal_withholding"]
    judy_withholding = judy_jones_w2_data["federal_withholding"]
    total_withholding = john_withholding + judy_withholding
    estimated_payment_from_prior = Decimal("300.00")

    total_payments = total_withholding + estimated_payment_from_prior

    # Refund or owed
    if total_payments > total_tax:
        refund = total_payments - total_tax
        amount_owed = Decimal("0")
    else:
        refund = Decimal("0")
        amount_owed = total_tax - total_payments

    return {
        # Taxpayer info
        "primary_ssn": john_jones_taxpayer["ssn_clean"],
        "primary_first_name": john_jones_taxpayer["first_name"],
        "primary_last_name": john_jones_taxpayer["last_name"],
        "address": john_jones_taxpayer["address"],
        "filing_status": 2,  # Married Filing Jointly

        # Spouse info
        "spouse_ssn": judy_jones_spouse["ssn_clean"],
        "spouse_first_name": judy_jones_spouse["first_name"],
        "spouse_last_name": judy_jones_spouse["last_name"],
        "spouse_date_of_death": judy_jones_spouse["date_of_death"],
        "spouse_ip_pin": judy_jones_spouse["ip_pin"],
        "spouse_is_nonresident_treated_as_resident": True,

        # Checkboxes
        "presidential_campaign_you": True,
        "presidential_campaign_spouse": True,
        "digital_assets": False,

        # Dependents
        "dependents": [jacob_jones_dependent],

        # Income (Lines 1-9)
        "line_1z_wages": total_wages,
        "wages": total_wages,
        "line_9_total_income": total_income,
        "total_income": total_income,

        # Adjustments (Line 10)
        "line_10_adjustments": Decimal("0"),

        # AGI (Line 11)
        "line_11_agi": agi,
        "agi": agi,

        # Deduction (Lines 12-14)
        "line_12_itemized_deduction": itemized_deduction,
        "line_12_deduction": itemized_deduction,
        "line_14_total_deductions": itemized_deduction,
        "deduction": itemized_deduction,
        "using_itemized": True,

        # Taxable income (Line 15)
        "line_15_taxable_income": taxable_income,
        "taxable_income": taxable_income,

        # Tax (Lines 16-24)
        "line_16_tax": calculated_tax,
        "line_17_schedule_2": Decimal("0"),
        "line_18_total": calculated_tax,
        "line_19_ctc_actc": Decimal("0"),
        "line_19_odc": odc_credit,
        "line_20_schedule_3": Decimal("0"),
        "line_21_credits_subtotal": total_credits,
        "line_22_tax_minus_credits": tax_after_credits,
        "line_23_other_taxes": Decimal("0"),
        "line_24_total_tax": total_tax,
        "total_tax": total_tax,

        # Payments (Lines 25-33)
        "line_25a_w2_withholding": total_withholding,
        "line_25d_total_withholding": total_withholding,
        "line_26_estimated_payments": estimated_payment_from_prior,
        "former_spouse_ssn": "400-01-1037",  # For estimated payments
        "line_27c_no_eic": True,  # Checked - not claiming EIC
        "line_33_total_payments": total_payments,
        "total_payments": total_payments,

        # Refund/Amount Owed
        "line_34_overpaid": refund,
        "line_35a_refund": refund,
        "line_37_amount_owed": amount_owed,
        "refund": refund,
        "amount_owed": amount_owed,

        # Attached forms/schedules
        "has_schedule_1": True,
        "has_schedule_a": True,
        "has_schedule_c": True,
        "has_form_8283": True,
        "has_binary_attachment": True,
        "binary_attachment_description": "Nonresident Spouse Choice Statement",

        # Form data
        "schedule_1": jones_schedule_1,
        "schedule_a": jones_schedule_a,
        "schedule_c": john_jones_schedule_c,
        "form_8283": jones_form_8283,
        "w2_john": john_jones_w2_data,
        "w2_judy": judy_jones_w2_data,
    }


# =============================================================================
# TEST CLASS: Taxpayer and Spouse Information
# =============================================================================


class TestTaxpayerInformation:
    """Tests for taxpayer and spouse information."""

    def test_primary_taxpayer_name(self, john_jones_taxpayer):
        """Test primary taxpayer name."""
        assert john_jones_taxpayer["first_name"] == "John"
        assert john_jones_taxpayer["last_name"] == "Jones"

    def test_spouse_deceased(self, judy_jones_spouse):
        """Test spouse is marked as deceased."""
        assert judy_jones_spouse["date_of_death"] == date(2025, 9, 11)

    def test_spouse_ip_pin(self, judy_jones_spouse):
        """Test spouse has Identity Protection PIN."""
        assert judy_jones_spouse["ip_pin"] == "876543"

    def test_spouse_nonresident_election(self, judy_jones_spouse):
        """Test spouse is treated as US resident (nonresident alien election)."""
        assert judy_jones_spouse["is_nonresident_alien_treated_as_resident"] is True


# =============================================================================
# TEST CLASS: Dependent Information
# =============================================================================


class TestDependentInformation:
    """Tests for dependent information."""

    def test_dependent_is_student(self, jacob_jones_dependent):
        """Test dependent is full-time student."""
        assert jacob_jones_dependent["is_full_time_student"] is True

    def test_dependent_qualifies_for_odc(self, jacob_jones_dependent):
        """Test dependent qualifies for Other Dependents Credit (over 16)."""
        assert jacob_jones_dependent["qualifies_for_odc"] is True
        assert jacob_jones_dependent["qualifies_for_ctc"] is False


# =============================================================================
# TEST CLASS: W-2 Income
# =============================================================================


class TestW2Income:
    """Tests for W-2 wage income."""

    def test_john_w2_wages(self, john_jones_w2_data):
        """Test John's W-2 wages."""
        assert john_jones_w2_data["wages"] == Decimal("29513.00")

    def test_john_statutory_employee(self, john_jones_w2_data):
        """Test John is a statutory employee."""
        assert john_jones_w2_data["is_statutory_employee"] is True

    def test_judy_w2_wages(self, judy_jones_w2_data):
        """Test Judy's W-2 wages."""
        assert judy_jones_w2_data["wages"] == Decimal("8513.00")

    def test_total_wages(self, john_jones_w2_data, judy_jones_w2_data):
        """Test combined W-2 wages."""
        total = john_jones_w2_data["wages"] + judy_jones_w2_data["wages"]
        assert total == Decimal("38026.00")

    def test_total_withholding(self, john_jones_w2_data, judy_jones_w2_data):
        """Test combined federal withholding."""
        total = (john_jones_w2_data["federal_withholding"] +
                 judy_jones_w2_data["federal_withholding"])
        assert total == Decimal("1164.00")


# =============================================================================
# TEST CLASS: Schedule C Business Income
# =============================================================================


class TestScheduleCBusinessIncome:
    """Tests for Schedule C business expenses."""

    def test_principal_business(self, john_jones_schedule_c):
        """Test principal business description."""
        assert john_jones_schedule_c["principal_business"] == "Furniture Sales"
        assert john_jones_schedule_c["principal_business_code"] == "449110"

    def test_total_expenses(self, john_jones_schedule_c):
        """Test total business expenses."""
        expenses = john_jones_schedule_c["expenses"]
        expected = sum(expenses.values())
        assert john_jones_schedule_c["line_28_total_expenses"] == expected

    def test_vehicle_information(self, john_jones_schedule_c):
        """Test vehicle information is provided."""
        assert john_jones_schedule_c["business_miles"] == 665
        assert john_jones_schedule_c["evidence_to_support"] is True


# =============================================================================
# TEST CLASS: Schedule A Itemized Deductions
# =============================================================================


class TestScheduleAItemizedDeductions:
    """Tests for Schedule A itemized deductions."""

    def test_salt_cap_applied(self, jones_schedule_a):
        """Test $10,000 SALT cap is applied."""
        total_taxes = jones_schedule_a["line_5d_total_taxes"]
        limited_taxes = jones_schedule_a["line_5e_salt_limited"]

        # Total taxes exceed $10,000 but are capped
        assert total_taxes == Decimal("10000.00")
        assert limited_taxes == Decimal("10000.00")

    def test_mortgage_interest(self, jones_schedule_a):
        """Test mortgage interest deduction."""
        assert jones_schedule_a["line_8a_home_mortgage_interest"] == Decimal("11000.00")
        assert jones_schedule_a["line_8c_points_not_on_1098"] == Decimal("251.00")

    def test_charitable_contributions(self, jones_schedule_a):
        """Test charitable contributions.

        Per ATS additional info: dotted line = $200, line 11 = $250.
        """
        cash = jones_schedule_a["line_11_cash_contributions"]
        noncash = jones_schedule_a["line_12_other_contributions"]
        total = jones_schedule_a["line_14_total_gifts"]

        assert cash == Decimal("250.00")
        assert noncash == Decimal("700.00")
        assert total == cash + noncash

    def test_total_itemized_deductions(self, jones_schedule_a):
        """Test total itemized deductions.

        Total = $10,000 (taxes) + $11,251 (interest) + $950 (gifts) = $22,201
        """
        taxes = jones_schedule_a["line_7_total_taxes"]
        interest = jones_schedule_a["line_10_total_interest"]
        gifts = jones_schedule_a["line_14_total_gifts"]
        expected = taxes + interest + gifts

        assert jones_schedule_a["line_17_total_itemized"] == expected
        assert jones_schedule_a["line_17_total_itemized"] == Decimal("22201.00")


# =============================================================================
# TEST CLASS: Form 8283 Noncash Contributions
# =============================================================================


class TestForm8283NoncashContributions:
    """Tests for Form 8283 noncash charitable contributions."""

    def test_donee_organization(self, jones_form_8283):
        """Test donee organization information."""
        assert jones_form_8283["donee_organization"]["name"] == "Goodwill"

    def test_donated_property(self, jones_form_8283):
        """Test donated property details."""
        prop = jones_form_8283["donated_property"]
        assert prop["description"] == "Clothes & toys"
        assert prop["fair_market_value"] == Decimal("700.00")

    def test_fmv_less_than_cost(self, jones_form_8283):
        """Test FMV is less than donor's cost basis."""
        prop = jones_form_8283["donated_property"]
        assert prop["fair_market_value"] < prop["donors_cost_basis"]


# =============================================================================
# TEST CLASS: Tax Calculation
# =============================================================================


class TestTaxCalculation:
    """Tests for Form 1040 tax calculations."""

    def test_filing_status_mfj(self, jones_form_1040_data):
        """Test filing status is Married Filing Jointly."""
        assert jones_form_1040_data["filing_status"] == 2

    def test_agi_calculation(self, jones_form_1040_data):
        """Test AGI calculation."""
        wages = jones_form_1040_data["wages"]
        adjustments = jones_form_1040_data["line_10_adjustments"]
        agi = jones_form_1040_data["agi"]

        assert agi == wages - adjustments

    def test_using_itemized_deduction(self, jones_form_1040_data):
        """Test using itemized deduction."""
        assert jones_form_1040_data["using_itemized"] is True

    def test_odc_credit(self, jones_form_1040_data):
        """Test Other Dependents Credit for Jacob."""
        assert jones_form_1040_data["line_19_odc"] == Decimal("500.00")

    def test_estimated_payment_included(self, jones_form_1040_data):
        """Test estimated payment from prior year is included."""
        assert jones_form_1040_data["line_26_estimated_payments"] == Decimal("300.00")

    def test_former_spouse_ssn_for_estimates(self, jones_form_1040_data):
        """Test former spouse SSN is provided for estimated payments."""
        assert jones_form_1040_data["former_spouse_ssn"] == "400-01-1037"


# =============================================================================
# TEST CLASS: XML Serialization
# =============================================================================


class TestScenario2XMLSerialization:
    """Tests for XML serialization of Scenario 2 data."""

    def test_taxpayer_info_creation(self, john_jones_taxpayer):
        """Test TaxpayerInfo object creation."""
        taxpayer_info = TaxpayerInfo(
            primary_ssn=john_jones_taxpayer["ssn_clean"],
            primary_first_name=john_jones_taxpayer["first_name"],
            primary_last_name=john_jones_taxpayer["last_name"],
            primary_date_of_birth=john_jones_taxpayer["date_of_birth"],
        )

        assert taxpayer_info.primary_ssn == "400011038"
        assert taxpayer_info.primary_first_name == "John"
        assert taxpayer_info.primary_last_name == "Jones"

    def test_submission_id_generation(self):
        """Test MeF submission ID generation."""
        submission_id = SubmissionId.generate(efin="123456", sequence=1)

        assert len(submission_id.submission_id) == 20
        assert submission_id.submission_id.isdigit()


# =============================================================================
# TEST CLASS: Business Rules Validation
# =============================================================================


class TestScenario2BusinessRules:
    """Tests for business rules validation of Scenario 2 data."""

    def test_mfj_requires_spouse_ssn(self, jones_form_1040_data):
        """Test MFJ filing requires spouse SSN."""
        assert jones_form_1040_data["filing_status"] == 2
        assert jones_form_1040_data["spouse_ssn"] is not None

    def test_deceased_spouse_has_death_date(self, jones_form_1040_data):
        """Test deceased spouse has death date."""
        assert jones_form_1040_data["spouse_date_of_death"] == date(2025, 9, 11)

    def test_required_forms_attached(self, jones_form_1040_data):
        """Test required forms are marked as attached."""
        assert jones_form_1040_data["has_schedule_1"] is True
        assert jones_form_1040_data["has_schedule_a"] is True
        assert jones_form_1040_data["has_schedule_c"] is True
        assert jones_form_1040_data["has_form_8283"] is True

    def test_binary_attachment_present(self, jones_form_1040_data):
        """Test binary attachment for nonresident spouse statement."""
        assert jones_form_1040_data["has_binary_attachment"] is True
        assert "Nonresident" in jones_form_1040_data["binary_attachment_description"]


# =============================================================================
# TEST CLASS: Integration Tests
# =============================================================================


class TestScenario2Integration:
    """Integration tests for the complete Scenario 2 data."""

    def test_complete_form_1040_structure(self, jones_form_1040_data):
        """Test complete form data has all required fields."""
        required_fields = [
            "primary_ssn", "primary_first_name", "primary_last_name",
            "spouse_ssn", "filing_status",
            "wages", "total_income", "agi", "deduction", "taxable_income",
            "total_tax", "total_payments",
        ]

        for field in required_fields:
            assert field in jones_form_1040_data, f"Missing field: {field}"

    def test_w2_to_form_1040_flow(self, john_jones_w2_data, judy_jones_w2_data, jones_form_1040_data):
        """Test W-2 data flows correctly to Form 1040."""
        total_wages = john_jones_w2_data["wages"] + judy_jones_w2_data["wages"]
        assert jones_form_1040_data["line_1z_wages"] == total_wages

        total_withholding = (john_jones_w2_data["federal_withholding"] +
                            judy_jones_w2_data["federal_withholding"])
        assert jones_form_1040_data["line_25a_w2_withholding"] == total_withholding

    def test_schedule_a_to_form_1040_flow(self, jones_schedule_a, jones_form_1040_data):
        """Test Schedule A flows to Form 1040."""
        assert jones_form_1040_data["line_12_itemized_deduction"] == jones_schedule_a["line_17_total_itemized"]

    def test_form_8283_to_schedule_a_flow(self, jones_form_8283, jones_schedule_a):
        """Test Form 8283 noncash contribution flows to Schedule A."""
        fmv = jones_form_8283["donated_property"]["fair_market_value"]
        schedule_a_noncash = jones_schedule_a["line_12_other_contributions"]

        assert schedule_a_noncash == fmv


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
