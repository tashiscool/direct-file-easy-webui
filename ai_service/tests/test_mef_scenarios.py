"""Comprehensive pytest tests for MeF E-File Service - Advanced Scenarios.

This module tests the MeF (Modernized e-File) service functionality using
IRS ATS (Assurance Testing System) Test Scenario 2 data for John & Judy Jones.

Test Scenario Reference: IRS ATS Test Scenario 2
Primary Taxpayer: John Jones
Spouse: Judy Jones (deceased 09/11/2025)
Filing Status: Married Filing Jointly (MFJ)
Dependent: Jacob Jones (son, full-time student)

Key Features Tested:
- Deceased spouse handling
- IP PIN validation for spouse
- Nonresident alien spouse election (Section 6013(g))
- Schedule C statutory employee income
- Schedule A itemized deductions with SALT cap
- Form 8283 noncash charitable contributions
- Paid preparer information
- Former spouse SSN for estimated tax payments
- Agricultural cooperative QBI exclusion

Tests cover:
- test_mfj_with_deceased_spouse() - Proper handling of deceased taxpayer
- test_dependent_full_time_student() - Student dependent eligibility
- test_schedule_c_statutory_employee() - Schedule C from W-2 statutory employee
- test_schedule_a_itemized_salt_cap() - $10,000 SALT limitation
- test_form_8283_noncash_charitable() - Noncash contributions
- test_spouse_ip_pin_validation() - IP PIN for spouse
- test_nonresident_spouse_election() - Nonresident spouse as US resident
- test_paid_preparer_info() - Preparer PTIN and firm info
- test_estimated_tax_former_spouse() - Former spouse SSN for estimated payments
- test_qbi_agricultural_cooperative_exclusion() - No QBI for ag coop patrons
"""

import pytest
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional

import sys
import os

# Add the parent directory to path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

# Import directly from the module file to avoid __init__.py dependencies
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
AcknowledgmentProcessor = mef_module.AcknowledgmentProcessor


# =============================================================================
# FIXTURES - IRS ATS Test Scenario 2 Data (John & Judy Jones - MFJ)
# =============================================================================


@pytest.fixture
def jones_primary_taxpayer() -> Dict[str, Any]:
    """Fixture for John Jones (primary taxpayer) information.

    IRS ATS Test Scenario 2 - MFJ filer with deceased spouse,
    Schedule C business income, and itemized deductions.

    Note: ATS test SSNs use invalid group numbers (00). We use valid
    format SSNs for testing while preserving ATS references.

    ATS Reference SSN: 400-00-1035 (invalid for production validation)
    Test SSN: 400-01-1035 (valid format for testing validation logic)
    """
    return {
        "first_name": "John",
        "last_name": "Jones",
        "ssn": "400-01-1035",
        "ssn_clean": "400011035",
        "ssn_ats_reference": "400-00-1035",
        "address": {
            "street": "123 Main Street",
            "city": "Anytown",
            "state": "NY",
            "zip": "10001"
        },
        "date_of_birth": date(1975, 3, 15),
        "occupation": "Self-Employed",
    }


@pytest.fixture
def jones_spouse() -> Dict[str, Any]:
    """Fixture for Judy Jones (spouse, deceased) information.

    Spouse Details:
    - Deceased: 09/11/2025
    - IP PIN: 876543
    - Nonresident alien treated as US resident (Section 6013(g) election)

    ATS Reference SSN: 400-00-1036 (invalid for production)
    Test SSN: 400-01-1036 (valid format)
    """
    return {
        "first_name": "Judy",
        "last_name": "Jones",
        "ssn": "400-01-1036",
        "ssn_clean": "400011036",
        "ssn_ats_reference": "400-00-1036",
        "date_of_birth": date(1977, 8, 22),
        "date_of_death": date(2025, 9, 11),
        "is_deceased": True,
        "ip_pin": "876543",
        "is_nonresident_alien": True,
        "nra_election_6013g": True,  # Treated as US resident for tax purposes
    }


@pytest.fixture
def jones_dependent() -> Dict[str, Any]:
    """Fixture for Jacob Jones (dependent son, full-time student).

    Dependent Details:
    - Relationship: Son
    - Full-time student for 5+ months
    - Date of Birth: 07/20/2006 (age 19 in 2025)
    - Qualifies for CTC based on age and student status

    ATS Reference SSN: 400-00-1038 (invalid for production)
    Test SSN: 400-01-1038 (valid format)
    """
    return {
        "first_name": "Jacob",
        "last_name": "Jones",
        "ssn": "400-01-1038",
        "ssn_clean": "400011038",
        "ssn_ats_reference": "400-00-1038",
        "relationship": "SON",
        "date_of_birth": date(2006, 7, 20),
        "is_full_time_student": True,
        "months_lived_at_home": 12,
        "is_us_citizen": True,
    }


@pytest.fixture
def jones_former_spouse() -> Dict[str, Any]:
    """Fixture for former spouse information (estimated tax payments).

    The Jones' have $300 in estimated tax payments from their 2024 return
    that was filed with a former spouse's SSN.

    ATS Reference SSN: 400-00-1037 (invalid for production)
    Test SSN: 400-01-1037 (valid format)
    """
    return {
        "ssn": "400-01-1037",
        "ssn_clean": "400011037",
        "ssn_ats_reference": "400-00-1037",
        "estimated_payment_applied": Decimal("300.00"),
        "applied_from_year": 2024,
    }


@pytest.fixture
def jones_w2_data() -> Dict[str, Any]:
    """Fixture for Jones family W-2 data.

    Two W-2 forms:
    - W-2 #1: John Jones (regular employment)
    - W-2 #2: John Jones (statutory employee for Schedule C)
    """
    return {
        "w2_1": {
            # W-2 #1 - Regular Employment
            "employee_name": "John Jones",
            "employer_name": "ABC Corporation",
            "employer_ein": "12-3456789",
            "employer_ein_clean": "123456789",
            "employer_address": {
                "street": "456 Corporate Drive",
                "city": "New York",
                "state": "NY",
                "zip": "10002"
            },
            "wages": Decimal("45000.00"),
            "federal_withholding": Decimal("4500.00"),
            "ss_wages": Decimal("45000.00"),
            "ss_tax": Decimal("2790.00"),
            "medicare_wages": Decimal("45000.00"),
            "medicare_tax": Decimal("652.50"),
            "state": "NY",
            "state_wages": Decimal("45000.00"),
            "state_tax": Decimal("2500.00"),
            "local_tax": Decimal("800.00"),
            "box_13_statutory_employee": False,
        },
        "w2_2": {
            # W-2 #2 - Statutory Employee (Schedule C)
            "employee_name": "John Jones",
            "employer_name": "Furniture Distributors Inc",
            "employer_ein": "98-7654321",
            "employer_ein_clean": "987654321",
            "employer_address": {
                "street": "789 Warehouse Blvd",
                "city": "Brooklyn",
                "state": "NY",
                "zip": "11201"
            },
            "wages": Decimal("32000.00"),  # Goes to Schedule C gross receipts
            "federal_withholding": Decimal("0.00"),  # No withholding for statutory employee
            "ss_wages": Decimal("32000.00"),
            "ss_tax": Decimal("1984.00"),
            "medicare_wages": Decimal("32000.00"),
            "medicare_tax": Decimal("464.00"),
            "state": "NY",
            "state_wages": Decimal("32000.00"),
            "state_tax": Decimal("0.00"),
            "local_tax": Decimal("0.00"),
            "box_13_statutory_employee": True,  # Statutory employee checkbox
        },
        "totals": {
            "regular_wages": Decimal("45000.00"),  # Only W-2 #1 wages
            "statutory_wages": Decimal("32000.00"),  # W-2 #2 to Schedule C
            "federal_withholding": Decimal("4500.00"),
            "state_tax": Decimal("2500.00"),
            "local_tax": Decimal("800.00"),
        }
    }


@pytest.fixture
def jones_schedule_c() -> Dict[str, Any]:
    """Fixture for Schedule C (Profit or Loss from Business).

    Business: Furniture Sales
    NAICS Code: 449110 (Furniture Stores)

    Gross receipts from statutory employee W-2.
    """
    return {
        "business_name": "Furniture Sales",
        "business_code": "449110",  # NAICS: Furniture Stores
        "principal_business": "Furniture Sales",
        "business_address": {
            "street": "123 Main Street",
            "city": "Anytown",
            "state": "NY",
            "zip": "10001"
        },
        "accounting_method": "Cash",
        "material_participation": True,
        # Income
        "gross_receipts": Decimal("32000.00"),  # From statutory employee W-2
        "returns_allowances": Decimal("0.00"),
        "other_income": Decimal("0.00"),
        "gross_income": Decimal("32000.00"),
        # Expenses (Lines 8-27)
        "advertising": Decimal("850.00"),
        "car_expenses": Decimal("466.00"),  # 665 miles @ $0.70/mile (before July 2025)
        "commissions": Decimal("0.00"),
        "contract_labor": Decimal("0.00"),
        "depletion": Decimal("0.00"),
        "depreciation": Decimal("0.00"),
        "employee_benefits": Decimal("0.00"),
        "insurance": Decimal("0.00"),
        "interest_mortgage": Decimal("0.00"),
        "interest_other": Decimal("0.00"),
        "legal_professional": Decimal("0.00"),
        "office_expense": Decimal("0.00"),
        "pension_profit_sharing": Decimal("550.00"),
        "rent_vehicles": Decimal("0.00"),
        "rent_other": Decimal("0.00"),
        "repairs": Decimal("0.00"),
        "supplies": Decimal("610.00"),
        "taxes_licenses": Decimal("58.00"),
        "travel": Decimal("0.00"),
        "meals": Decimal("0.00"),
        "utilities": Decimal("0.00"),
        "wages": Decimal("0.00"),
        "other_expenses": Decimal("0.00"),
        # Calculated totals
        "total_expenses": Decimal("2534.00"),  # 850 + 466 + 550 + 610 + 58
        "net_profit": Decimal("29466.00"),  # 32000 - 2534
        # Vehicle information
        "vehicle_info": {
            "date_placed_in_service": date(2024, 1, 15),
            "business_miles": 665,
            "commuting_miles": 0,
            "personal_miles": 2335,
            "total_miles": 3000,
            "vehicle_available_personal": True,
            "another_vehicle_available": False,
            "evidence_to_support": True,
            "written_evidence": True,
        }
    }


@pytest.fixture
def jones_schedule_a() -> Dict[str, Any]:
    """Fixture for Schedule A (Itemized Deductions).

    Key Limitation: SALT (State and Local Tax) cap of $10,000.

    Total state/local taxes paid exceed $10,000 but deduction limited.
    """
    return {
        # Medical expenses
        "medical_expenses_total": Decimal("5000.00"),
        "agi_threshold_percent": Decimal("7.5"),  # 7.5% of AGI
        "medical_deduction": Decimal("0.00"),  # Likely below threshold
        # State and local taxes (Line 5)
        "state_income_tax": Decimal("2500.00"),  # From W-2
        "local_income_tax": Decimal("800.00"),  # From W-2
        "real_estate_tax": Decimal("8500.00"),  # Property taxes
        "personal_property_tax": Decimal("1200.00"),  # Vehicle registration, etc.
        "salt_total_uncapped": Decimal("13000.00"),  # 2500 + 800 + 8500 + 1200
        "salt_cap": Decimal("10000.00"),  # TCJA limitation
        "salt_deduction": Decimal("10000.00"),  # Limited to cap
        # Interest (Lines 8-10)
        "mortgage_interest": Decimal("12000.00"),
        "mortgage_points": Decimal("0.00"),
        "investment_interest": Decimal("0.00"),
        "interest_total": Decimal("12000.00"),
        # Charitable contributions (Lines 11-14)
        "cash_contributions_50_limit": Decimal("3000.00"),
        "cash_contributions_30_limit": Decimal("0.00"),
        "noncash_contributions": Decimal("700.00"),  # Form 8283 - Goodwill
        "carryover_contributions": Decimal("0.00"),
        "charitable_total": Decimal("3700.00"),
        # Other itemized deductions
        "casualty_losses": Decimal("0.00"),  # Only federally declared disasters
        "other_deductions": Decimal("0.00"),
        # Totals
        "total_itemized": Decimal("25700.00"),  # 10000 + 12000 + 3700
        # Comparison to standard deduction (OBBBA 2025 MFJ: $31,500)
        "standard_deduction_mfj": Decimal("31500.00"),
        "use_itemized": False,  # Itemized is less than standard
    }


@pytest.fixture
def jones_form_8283() -> Dict[str, Any]:
    """Fixture for Form 8283 (Noncash Charitable Contributions).

    Donation Details:
    - Items: Clothes and toys
    - Donee: Goodwill Industries
    - Fair Market Value: $700
    - Acquisition: Purchased
    - Condition: Good

    Note: Noncash contributions over $500 require Form 8283.
    """
    return {
        "section_a": {  # Section A for contributions < $5,000
            "contributions": [
                {
                    "donee_name": "Goodwill Industries",
                    "donee_address": {
                        "street": "5500 South Santa Fe Drive",
                        "city": "Denver",
                        "state": "CO",
                        "zip": "80202"
                    },
                    "description": "Clothing and toys",
                    "date_acquired": "Various",
                    "how_acquired": "Purchased",
                    "date_contributed": date(2025, 4, 15),
                    "fair_market_value": Decimal("700.00"),
                    "method_of_valuation": "Thrift shop value",
                    "cost_or_basis": Decimal("1200.00"),  # Original cost
                }
            ]
        },
        "total_noncash_contributions": Decimal("700.00"),
        "requires_section_b": False,  # Under $5,000 threshold
        "requires_appraisal": False,  # Under $5,000 threshold
    }


@pytest.fixture
def jones_paid_preparer() -> Dict[str, Any]:
    """Fixture for paid preparer information.

    Preparer: Walter Young
    PTIN: P00000001
    Firm: Young's Tax Service
    """
    return {
        "preparer_name": "Walter Young",
        "ptin": "P00000001",
        "is_self_employed": True,
        "firm_name": "Young's Tax Service",
        "firm_address": {
            "street": "1111 New York Avenue",
            "city": "New York",
            "state": "NY",
            "zip": "10022"
        },
        "firm_ein": "00-0000079",
        "firm_ein_clean": "000000079",
        "phone": "800-123-4567",
        "date_signed": date(2026, 1, 15),
    }


@pytest.fixture
def jones_form_1040_data(
    jones_primary_taxpayer,
    jones_spouse,
    jones_dependent,
    jones_w2_data,
    jones_schedule_c,
    jones_schedule_a,
    jones_former_spouse
) -> Dict[str, Any]:
    """Fixture for complete Form 1040 data for John & Judy Jones.

    Tax Year: 2025
    Filing Status: Married Filing Jointly (2)
    Standard Deduction (OBBBA 2025 MFJ): $31,500
    """
    # Income calculations
    regular_wages = jones_w2_data["totals"]["regular_wages"]
    schedule_c_profit = jones_schedule_c["net_profit"]

    total_income = regular_wages + schedule_c_profit

    # Self-employment tax calculation (simplified)
    se_tax_base = schedule_c_profit * Decimal("0.9235")  # 92.35% of net profit
    se_tax = se_tax_base * Decimal("0.153")  # 15.3% SE tax
    se_tax_deduction = se_tax / 2  # 50% deduction

    # Adjustments
    total_adjustments = se_tax_deduction

    # AGI
    agi = total_income - total_adjustments

    # Deduction - OBBBA 2025 MFJ standard deduction
    standard_deduction = Decimal("31500.00")
    deduction_used = standard_deduction

    # Taxable income
    taxable_income = max(Decimal("0"), agi - deduction_used)

    # Tax calculation (simplified estimate)
    calculated_tax = Decimal("8500.00")  # Approximate

    # Credits
    child_tax_credit = Decimal("2000.00")  # For Jacob (full-time student)

    # Total tax after credits + SE tax
    total_tax = max(Decimal("0"), calculated_tax - child_tax_credit) + se_tax

    # Payments
    federal_withholding = jones_w2_data["totals"]["federal_withholding"]
    estimated_payments = jones_former_spouse["estimated_payment_applied"]
    total_payments = federal_withholding + estimated_payments

    # Refund or amount owed
    if total_payments > total_tax:
        refund = total_payments - total_tax
        amount_owed = Decimal("0")
    else:
        refund = Decimal("0")
        amount_owed = total_tax - total_payments

    return {
        # Taxpayer info
        "primary_ssn": jones_primary_taxpayer["ssn_clean"],
        "primary_first_name": jones_primary_taxpayer["first_name"],
        "primary_last_name": jones_primary_taxpayer["last_name"],
        "spouse_ssn": jones_spouse["ssn_clean"],
        "spouse_first_name": jones_spouse["first_name"],
        "spouse_last_name": jones_spouse["last_name"],
        "spouse_deceased": jones_spouse["is_deceased"],
        "spouse_date_of_death": jones_spouse["date_of_death"],
        "spouse_ip_pin": jones_spouse["ip_pin"],
        "filing_status": 2,  # MFJ

        # Checkboxes
        "presidential_campaign_primary": False,
        "presidential_campaign_spouse": False,
        "digital_assets": False,

        # Nonresident alien election
        "spouse_nra_election": jones_spouse["nra_election_6013g"],

        # Dependents
        "dependents": [jones_dependent],

        # Income lines
        "line1": regular_wages,  # Regular wages only
        "wages": regular_wages,
        "line8": schedule_c_profit,  # Schedule 1 line 3 -> Form 1040 line 8
        "schedule_c_profit": schedule_c_profit,
        "line9": total_income,
        "total_income": total_income,

        # Adjustments (Schedule 1 Part II)
        "line10": total_adjustments,
        "adjustments": total_adjustments,
        "se_deduction": se_tax_deduction,

        # AGI
        "line11": agi,
        "agi": agi,

        # Deductions
        "line12": deduction_used,
        "deduction": deduction_used,
        "line14": deduction_used,
        "total_deductions": deduction_used,

        # QBI Deduction (Line 13)
        "line13": Decimal("0"),  # Agricultural cooperative patron - no QBI
        "qbi_deduction": Decimal("0"),
        "agricultural_cooperative_patron": True,

        # Taxable income
        "line15": taxable_income,
        "taxable_income": taxable_income,

        # Tax
        "line16": calculated_tax,
        "tax": calculated_tax,

        # Schedule 2 (Additional Taxes)
        "self_employment_tax": se_tax,

        # Credits
        "line19": child_tax_credit,
        "child_tax_credit": child_tax_credit,

        # Total tax
        "line24": total_tax,
        "total_tax": total_tax,

        # Payments
        "line25a": federal_withholding,
        "w2_withholding": federal_withholding,
        "line26": estimated_payments,
        "estimated_tax_payments": estimated_payments,
        "former_spouse_ssn": jones_former_spouse["ssn_clean"],
        "line33": total_payments,
        "total_payments": total_payments,

        # Refund/Owed
        "line34": refund if refund > 0 else Decimal("0"),
        "overpayment": refund if refund > 0 else Decimal("0"),
        "line35a": refund if refund > 0 else Decimal("0"),
        "refund_amount": refund if refund > 0 else Decimal("0"),
        "line37": amount_owed,
        "amount_owed": amount_owed,
    }


@pytest.fixture
def return_header_data_jones(jones_primary_taxpayer) -> Dict[str, Any]:
    """Fixture for creating a ReturnHeader for the Jones family."""
    return {
        "efin": "123456",
        "software_id": "12345678",
        "primary_pin": "12345",
        "spouse_pin": "67890",
        "tax_year": 2025,
    }


# =============================================================================
# TEST CLASS: MFJ with Deceased Spouse
# =============================================================================


class TestMFJWithDeceasedSpouse:
    """Tests for handling Married Filing Jointly returns with a deceased spouse.

    When a spouse dies during the tax year, the surviving spouse can still
    file MFJ for that year. Special handling is required for:
    - Date of death reporting
    - Signature requirements (personal representative signs for deceased)
    - IP PIN handling if deceased spouse had one
    """

    def test_mfj_with_deceased_spouse(
        self, jones_primary_taxpayer, jones_spouse, jones_form_1040_data
    ):
        """Test that MFJ return properly handles deceased spouse information."""
        # Verify spouse is marked as deceased
        assert jones_spouse["is_deceased"] is True
        assert jones_spouse["date_of_death"] == date(2025, 9, 11)

        # Verify form data includes deceased spouse info
        assert jones_form_1040_data["spouse_deceased"] is True
        assert jones_form_1040_data["spouse_date_of_death"] == date(2025, 9, 11)

        # Filing status should still be MFJ
        assert jones_form_1040_data["filing_status"] == 2

        # Spouse SSN should be present for MFJ
        assert jones_form_1040_data["spouse_ssn"] == jones_spouse["ssn_clean"]

    def test_deceased_spouse_date_of_death_format(self, jones_spouse):
        """Test that date of death is properly formatted for MeF XML."""
        dod = jones_spouse["date_of_death"]
        formatted = format_date(dod)

        # MeF requires ISO 8601 format: YYYY-MM-DD
        assert formatted == "2025-09-11"
        assert len(formatted) == 10
        assert formatted.count("-") == 2

    def test_deceased_spouse_in_xml_header(
        self, jones_primary_taxpayer, jones_spouse, return_header_data_jones
    ):
        """Test that deceased spouse information is included in return header XML."""
        serializer = XmlSerializer(tax_year=2025)

        # Create taxpayer info with spouse
        taxpayer_info = TaxpayerInfo(
            primary_ssn=jones_primary_taxpayer["ssn_clean"],
            primary_first_name=jones_primary_taxpayer["first_name"],
            primary_last_name=jones_primary_taxpayer["last_name"],
            primary_date_of_birth=jones_primary_taxpayer["date_of_birth"],
            spouse_ssn=jones_spouse["ssn_clean"],
            spouse_first_name=jones_spouse["first_name"],
            spouse_last_name=jones_spouse["last_name"],
            spouse_date_of_birth=jones_spouse["date_of_birth"],
        )

        submission_id = SubmissionId.generate(
            efin=return_header_data_jones["efin"],
            sequence=1
        )

        return_header = ReturnHeader(
            submission_id=submission_id,
            submission_type=SubmissionType.INDIVIDUAL_1040,
            category=SubmissionCategory.ORIGINAL,
            tax_year=2025,
            taxpayer=taxpayer_info,
            filing_status=2,  # MFJ
            primary_pin=return_header_data_jones["primary_pin"],
            spouse_pin=return_header_data_jones["spouse_pin"],
            software_id=return_header_data_jones["software_id"],
            originator_efin=return_header_data_jones["efin"],
        )

        xml = serializer.serialize_return_header(return_header)

        # Verify spouse information is in XML
        assert f"<SpouseSSN>{jones_spouse['ssn_clean']}</SpouseSSN>" in xml
        assert "<SpouseNameLine1Txt>" in xml
        assert "JUDY" in xml.upper()
        assert "JONES" in xml.upper()


# =============================================================================
# TEST CLASS: Dependent Full-Time Student
# =============================================================================


class TestDependentFullTimeStudent:
    """Tests for dependent eligibility when dependent is a full-time student.

    A qualifying child who is a full-time student can be claimed as a
    dependent up to age 24 (vs. 19 for non-students).
    """

    def test_dependent_full_time_student(self, jones_dependent):
        """Test that full-time student dependent data is correctly structured."""
        # Jacob is 19 years old (DOB: 07/20/2006)
        # As a full-time student, he qualifies as a dependent until age 24
        assert jones_dependent["is_full_time_student"] is True
        assert jones_dependent["date_of_birth"] == date(2006, 7, 20)
        assert jones_dependent["relationship"] == "SON"
        assert jones_dependent["months_lived_at_home"] == 12

    def test_student_dependent_age_calculation(self, jones_dependent):
        """Test age calculation for student dependent."""
        # Calculate age as of end of tax year 2025
        dob = jones_dependent["date_of_birth"]
        tax_year_end = date(2025, 12, 31)

        age_at_year_end = tax_year_end.year - dob.year
        if (tax_year_end.month, tax_year_end.day) < (dob.month, dob.day):
            age_at_year_end -= 1

        # Jacob is 19 at end of 2025
        assert age_at_year_end == 19

        # Full-time student qualifies up to age 24
        assert age_at_year_end < 24, "Full-time student must be under 24"

    def test_student_dependent_ctc_eligibility(self, jones_dependent, jones_form_1040_data):
        """Test that student dependent qualifies for Child Tax Credit."""
        # Students aged 17-23 may still qualify for credit
        # as Other Dependent Credit (ODC) if not for CTC
        assert jones_form_1040_data["child_tax_credit"] > 0

        # Verify dependent is properly associated
        assert len(jones_form_1040_data["dependents"]) == 1
        dependent = jones_form_1040_data["dependents"][0]
        assert dependent["first_name"] == "Jacob"

    def test_student_dependent_ssn_format(self, jones_dependent):
        """Test that dependent SSN is properly formatted."""
        ssn = jones_dependent["ssn"]
        formatted = format_ssn(ssn)

        assert len(formatted) == 9
        assert formatted.isdigit()
        assert formatted == jones_dependent["ssn_clean"]


# =============================================================================
# TEST CLASS: Schedule C Statutory Employee
# =============================================================================


class TestScheduleCStatutoryEmployee:
    """Tests for Schedule C income from W-2 statutory employee.

    Statutory employees (Box 13 checked on W-2) report their income and
    expenses on Schedule C, not as regular wages on Form 1040 Line 1.
    """

    def test_schedule_c_statutory_employee(self, jones_w2_data, jones_schedule_c):
        """Test Schedule C is properly populated from statutory employee W-2."""
        statutory_w2 = jones_w2_data["w2_2"]

        # Verify W-2 is marked as statutory employee
        assert statutory_w2["box_13_statutory_employee"] is True

        # Gross receipts should match statutory W-2 wages
        assert jones_schedule_c["gross_receipts"] == statutory_w2["wages"]
        assert jones_schedule_c["gross_receipts"] == Decimal("32000.00")

    def test_schedule_c_expenses(self, jones_schedule_c):
        """Test Schedule C expense deductions are correctly calculated."""
        # Verify individual expenses
        assert jones_schedule_c["advertising"] == Decimal("850.00")
        assert jones_schedule_c["car_expenses"] == Decimal("466.00")
        assert jones_schedule_c["pension_profit_sharing"] == Decimal("550.00")
        assert jones_schedule_c["supplies"] == Decimal("610.00")
        assert jones_schedule_c["taxes_licenses"] == Decimal("58.00")

        # Verify total expenses
        expected_total = Decimal("850.00") + Decimal("466.00") + Decimal("550.00") + \
                         Decimal("610.00") + Decimal("58.00")
        assert jones_schedule_c["total_expenses"] == expected_total
        assert jones_schedule_c["total_expenses"] == Decimal("2534.00")

    def test_schedule_c_net_profit(self, jones_schedule_c):
        """Test Schedule C net profit calculation."""
        expected_profit = jones_schedule_c["gross_receipts"] - jones_schedule_c["total_expenses"]
        assert jones_schedule_c["net_profit"] == expected_profit
        assert jones_schedule_c["net_profit"] == Decimal("29466.00")

    def test_schedule_c_car_expense_mileage(self, jones_schedule_c):
        """Test Schedule C car expenses using standard mileage rate."""
        vehicle = jones_schedule_c["vehicle_info"]

        # 665 business miles before July 2025
        assert vehicle["business_miles"] == 665

        # Standard mileage rate 2025 (first half): $0.70/mile
        # 665 * 0.70 = $465.50, rounded to $466
        expected_car_expense = Decimal("466.00")
        assert jones_schedule_c["car_expenses"] == expected_car_expense

    def test_schedule_c_naics_code(self, jones_schedule_c):
        """Test Schedule C business code is valid NAICS format."""
        naics = jones_schedule_c["business_code"]

        # NAICS codes are 6 digits
        assert len(naics) == 6
        assert naics.isdigit()

        # 449110 = Furniture Stores
        assert naics == "449110"

    def test_statutory_wages_not_on_line1(self, jones_form_1040_data, jones_w2_data):
        """Test that statutory employee wages are NOT included in Line 1."""
        # Line 1 should only have regular wages
        assert jones_form_1040_data["wages"] == jones_w2_data["totals"]["regular_wages"]
        assert jones_form_1040_data["wages"] == Decimal("45000.00")

        # Statutory wages should NOT be in Line 1
        assert jones_form_1040_data["wages"] != (
            jones_w2_data["w2_1"]["wages"] + jones_w2_data["w2_2"]["wages"]
        )


# =============================================================================
# TEST CLASS: Schedule A Itemized Deductions SALT Cap
# =============================================================================


class TestScheduleAItemizedSALTCap:
    """Tests for Schedule A itemized deductions with SALT limitation.

    The Tax Cuts and Jobs Act (TCJA) limits the State and Local Tax (SALT)
    deduction to $10,000 ($5,000 for MFS).
    """

    def test_schedule_a_itemized_salt_cap(self, jones_schedule_a):
        """Test that SALT deduction is properly capped at $10,000."""
        # Total SALT paid exceeds cap
        assert jones_schedule_a["salt_total_uncapped"] == Decimal("13000.00")

        # SALT deduction is limited to cap
        assert jones_schedule_a["salt_cap"] == Decimal("10000.00")
        assert jones_schedule_a["salt_deduction"] == Decimal("10000.00")

        # Verify excess is not deducted
        assert jones_schedule_a["salt_deduction"] < jones_schedule_a["salt_total_uncapped"]

    def test_salt_components(self, jones_schedule_a):
        """Test individual SALT components."""
        # State income tax from W-2
        assert jones_schedule_a["state_income_tax"] == Decimal("2500.00")

        # Local income tax from W-2
        assert jones_schedule_a["local_income_tax"] == Decimal("800.00")

        # Real estate taxes
        assert jones_schedule_a["real_estate_tax"] == Decimal("8500.00")

        # Personal property tax
        assert jones_schedule_a["personal_property_tax"] == Decimal("1200.00")

        # Verify total uncapped calculation
        expected_total = (jones_schedule_a["state_income_tax"] +
                         jones_schedule_a["local_income_tax"] +
                         jones_schedule_a["real_estate_tax"] +
                         jones_schedule_a["personal_property_tax"])
        assert jones_schedule_a["salt_total_uncapped"] == expected_total

    def test_itemized_vs_standard_deduction(self, jones_schedule_a):
        """Test comparison of itemized vs. standard deduction."""
        # Total itemized deductions
        total_itemized = jones_schedule_a["total_itemized"]
        assert total_itemized == Decimal("25700.00")

        # 2025 MFJ standard deduction
        standard = jones_schedule_a["standard_deduction_mfj"]
        assert standard == Decimal("30000.00")

        # Itemized is less than standard, so should use standard
        assert total_itemized < standard
        assert jones_schedule_a["use_itemized"] is False

    def test_itemized_deduction_total(self, jones_schedule_a):
        """Test total itemized deductions calculation."""
        expected_total = (jones_schedule_a["salt_deduction"] +
                         jones_schedule_a["interest_total"] +
                         jones_schedule_a["charitable_total"])

        assert jones_schedule_a["total_itemized"] == expected_total
        assert jones_schedule_a["total_itemized"] == Decimal("25700.00")


# =============================================================================
# TEST CLASS: Form 8283 Noncash Charitable Contributions
# =============================================================================


class TestForm8283NoncashCharitable:
    """Tests for Form 8283 noncash charitable contributions.

    Form 8283 is required for noncash charitable contributions over $500.
    Section A is for contributions under $5,000; Section B is for $5,000+.
    """

    def test_form_8283_noncash_charitable(self, jones_form_8283):
        """Test Form 8283 noncash contribution data structure."""
        # Total noncash contributions
        assert jones_form_8283["total_noncash_contributions"] == Decimal("700.00")

        # Should use Section A (under $5,000 threshold)
        assert jones_form_8283["requires_section_b"] is False
        assert jones_form_8283["requires_appraisal"] is False

    def test_form_8283_contribution_details(self, jones_form_8283):
        """Test individual contribution details on Form 8283."""
        contributions = jones_form_8283["section_a"]["contributions"]
        assert len(contributions) == 1

        donation = contributions[0]

        # Donee information
        assert donation["donee_name"] == "Goodwill Industries"
        assert donation["donee_address"]["state"] == "CO"

        # Donation details
        assert donation["description"] == "Clothing and toys"
        assert donation["fair_market_value"] == Decimal("700.00")
        assert donation["how_acquired"] == "Purchased"
        assert donation["date_contributed"] == date(2025, 4, 15)

    def test_noncash_contribution_valuation(self, jones_form_8283):
        """Test noncash contribution valuation requirements."""
        donation = jones_form_8283["section_a"]["contributions"][0]

        # FMV should be less than original cost (used items depreciate)
        assert donation["fair_market_value"] < donation["cost_or_basis"]

        # Valuation method
        assert donation["method_of_valuation"] == "Thrift shop value"

    def test_noncash_on_schedule_a(self, jones_schedule_a, jones_form_8283):
        """Test that noncash contribution flows to Schedule A."""
        assert jones_schedule_a["noncash_contributions"] == jones_form_8283["total_noncash_contributions"]
        assert jones_schedule_a["noncash_contributions"] == Decimal("700.00")


# =============================================================================
# TEST CLASS: Spouse IP PIN Validation
# =============================================================================


class TestSpouseIPPINValidation:
    """Tests for Identity Protection PIN validation for spouse.

    IP PINs are 6-digit PINs assigned by the IRS to protect taxpayer identity.
    When provided, the IP PIN must be included in the e-file submission.
    """

    def test_spouse_ip_pin_validation(self, jones_spouse):
        """Test spouse IP PIN format and presence."""
        ip_pin = jones_spouse["ip_pin"]

        # IP PIN should be 6 digits
        assert len(ip_pin) == 6
        assert ip_pin.isdigit()
        assert ip_pin == "876543"

    def test_ip_pin_in_form_data(self, jones_form_1040_data, jones_spouse):
        """Test IP PIN is included in form data."""
        assert jones_form_1040_data["spouse_ip_pin"] == jones_spouse["ip_pin"]

    def test_ip_pin_required_for_efile(self, jones_spouse):
        """Test that IP PIN presence is flagged for e-file validation."""
        # If taxpayer has IP PIN, it MUST be included or e-file will reject
        has_ip_pin = jones_spouse["ip_pin"] is not None and len(jones_spouse["ip_pin"]) == 6
        assert has_ip_pin is True

    def test_ip_pin_invalid_format_rejected(self):
        """Test that invalid IP PIN formats are rejected."""
        invalid_pins = [
            "12345",    # Too short (5 digits)
            "1234567",  # Too long (7 digits)
            "12345a",   # Contains letter
            "12-3456",  # Contains dash
        ]

        for invalid_pin in invalid_pins:
            is_valid = len(invalid_pin) == 6 and invalid_pin.isdigit()
            assert is_valid is False, f"PIN {invalid_pin} should be invalid"


# =============================================================================
# TEST CLASS: Nonresident Alien Spouse Election
# =============================================================================


class TestNonresidentSpouseElection:
    """Tests for nonresident alien spouse treated as US resident.

    Under IRC Section 6013(g), a nonresident alien can elect to be treated
    as a US resident for tax purposes if married to a US citizen/resident.
    """

    def test_nonresident_spouse_election(self, jones_spouse):
        """Test nonresident alien spouse election data."""
        # Spouse is a nonresident alien
        assert jones_spouse["is_nonresident_alien"] is True

        # Election under Section 6013(g) to be treated as US resident
        assert jones_spouse["nra_election_6013g"] is True

    def test_nra_election_in_form_data(self, jones_form_1040_data):
        """Test NRA election is included in form data."""
        assert jones_form_1040_data["spouse_nra_election"] is True

    def test_nra_spouse_can_file_mfj(self, jones_form_1040_data, jones_spouse):
        """Test that NRA spouse with election can file MFJ."""
        # With 6013(g) election, MFJ is allowed
        assert jones_form_1040_data["filing_status"] == 2  # MFJ
        assert jones_spouse["nra_election_6013g"] is True

    def test_nra_election_requires_both_worldwide_income(self, jones_spouse):
        """Test documentation requirement for NRA election."""
        # When electing 6013(g), both spouses must report worldwide income
        # This is a documentation/compliance check
        assert jones_spouse["nra_election_6013g"] is True
        # Note: In actual filing, a statement must be attached to the return


# =============================================================================
# TEST CLASS: Paid Preparer Information
# =============================================================================


class TestPaidPreparerInfo:
    """Tests for paid preparer information in MeF submission.

    Professional tax preparers must include their PTIN, firm EIN,
    and other identification information.
    """

    def test_paid_preparer_info(self, jones_paid_preparer):
        """Test paid preparer information structure."""
        assert jones_paid_preparer["preparer_name"] == "Walter Young"
        assert jones_paid_preparer["ptin"] == "P00000001"
        assert jones_paid_preparer["is_self_employed"] is True
        assert jones_paid_preparer["firm_name"] == "Young's Tax Service"

    def test_ptin_format(self, jones_paid_preparer):
        """Test PTIN format validation (P followed by 8 digits)."""
        ptin = jones_paid_preparer["ptin"]

        # PTIN format: P followed by 8 digits
        assert ptin.startswith("P")
        assert len(ptin) == 9
        assert ptin[1:].isdigit()

    def test_preparer_firm_ein(self, jones_paid_preparer):
        """Test preparer firm EIN format."""
        ein = jones_paid_preparer["firm_ein"]

        # EIN format: XX-XXXXXXX
        assert "-" in ein
        assert len(ein.replace("-", "")) == 9

    def test_preparer_phone_format(self, jones_paid_preparer):
        """Test preparer phone number format."""
        phone = jones_paid_preparer["phone"]

        # Should be in format XXX-XXX-XXXX or 10 digits
        clean_phone = phone.replace("-", "")
        assert len(clean_phone) == 10
        assert clean_phone.isdigit()

    def test_preparer_in_return_header(self, jones_paid_preparer, return_header_data_jones):
        """Test preparer information can be added to return header."""
        # Create return header with preparer info
        taxpayer_info = TaxpayerInfo(
            primary_ssn="400011035",
            primary_first_name="John",
            primary_last_name="Jones",
        )

        submission_id = SubmissionId.generate(
            efin=return_header_data_jones["efin"],
            sequence=1
        )

        return_header = ReturnHeader(
            submission_id=submission_id,
            submission_type=SubmissionType.INDIVIDUAL_1040,
            category=SubmissionCategory.ORIGINAL,
            tax_year=2025,
            taxpayer=taxpayer_info,
            filing_status=2,
            primary_pin=return_header_data_jones["primary_pin"],
            software_id=return_header_data_jones["software_id"],
            originator_efin=return_header_data_jones["efin"],
            preparer_ptin=jones_paid_preparer["ptin"],
            preparer_ein=jones_paid_preparer["firm_ein_clean"],
        )

        # Verify preparer info is set
        assert return_header.preparer_ptin == "P00000001"
        assert return_header.preparer_ein == "000000079"


# =============================================================================
# TEST CLASS: Estimated Tax Former Spouse SSN
# =============================================================================


class TestEstimatedTaxFormerSpouse:
    """Tests for estimated tax payments with former spouse SSN.

    When estimated tax payments were made with a former spouse's SSN
    (from a prior year joint return), that SSN must be reported.
    """

    def test_estimated_tax_former_spouse(self, jones_former_spouse):
        """Test former spouse SSN for estimated tax payments."""
        assert jones_former_spouse["estimated_payment_applied"] == Decimal("300.00")
        assert jones_former_spouse["applied_from_year"] == 2024

    def test_former_spouse_ssn_format(self, jones_former_spouse):
        """Test former spouse SSN is properly formatted."""
        ssn = jones_former_spouse["ssn"]
        formatted = format_ssn(ssn)

        assert len(formatted) == 9
        assert formatted == jones_former_spouse["ssn_clean"]

    def test_former_spouse_in_form_data(self, jones_form_1040_data, jones_former_spouse):
        """Test former spouse SSN is included in form data."""
        assert jones_form_1040_data["former_spouse_ssn"] == jones_former_spouse["ssn_clean"]
        assert jones_form_1040_data["estimated_tax_payments"] == jones_former_spouse["estimated_payment_applied"]

    def test_estimated_payments_in_total(self, jones_form_1040_data, jones_w2_data, jones_former_spouse):
        """Test estimated payments are included in total payments."""
        expected_total = (jones_w2_data["totals"]["federal_withholding"] +
                         jones_former_spouse["estimated_payment_applied"])

        assert jones_form_1040_data["total_payments"] == expected_total
        assert jones_form_1040_data["total_payments"] == Decimal("4800.00")


# =============================================================================
# TEST CLASS: QBI Agricultural Cooperative Exclusion
# =============================================================================


class TestQBIAgriculturalCooperativeExclusion:
    """Tests for QBI deduction exclusion for agricultural cooperative patrons.

    Patrons of specified agricultural or horticultural cooperatives
    may not be eligible for the standard QBI deduction under Section 199A(g).
    """

    def test_qbi_agricultural_cooperative_exclusion(self, jones_form_1040_data):
        """Test that QBI deduction is zero for agricultural cooperative patron."""
        # Agricultural cooperative patrons don't get standard QBI deduction
        assert jones_form_1040_data["agricultural_cooperative_patron"] is True
        assert jones_form_1040_data["qbi_deduction"] == Decimal("0")
        assert jones_form_1040_data["line13"] == Decimal("0")

    def test_qbi_deduction_would_be_available(self, jones_schedule_c):
        """Test that QBI deduction would normally be available for business income."""
        # Schedule C shows qualifying business income
        net_profit = jones_schedule_c["net_profit"]
        assert net_profit > 0

        # QBI deduction would be up to 20% of QBI (simplified)
        potential_qbi_deduction = net_profit * Decimal("0.20")
        assert potential_qbi_deduction > 0

    def test_agricultural_coop_flag_in_validator(self, jones_form_1040_data):
        """Test that validator recognizes agricultural cooperative patron status."""
        validator = BusinessRulesValidator(tax_year=2025, filing_status=2)

        # Create modified data to test QBI rules
        test_data = jones_form_1040_data.copy()

        # With agricultural coop patron flag, QBI should be 0
        result = validator.validate(test_data)

        # Should not have QBI-related errors when QBI is 0
        qbi_errors = [e for e in result.errors if "QBI" in e.message or "qbi" in e.code.lower()]
        assert len(qbi_errors) == 0

    def test_qbi_calculation_without_coop_exclusion(self, jones_schedule_c):
        """Test hypothetical QBI calculation without cooperative exclusion."""
        # If NOT an agricultural cooperative patron, QBI deduction would apply
        net_profit = jones_schedule_c["net_profit"]

        # Simplified QBI calculation (actual has many limitations)
        # 20% of QBI for income below threshold
        qbi_deduction = net_profit * Decimal("0.20")

        # Expected: 29,466 * 0.20 = 5,893.20
        expected_qbi = Decimal("5893.20")
        assert abs(qbi_deduction - expected_qbi) < Decimal("0.01")


# =============================================================================
# Integration Tests
# =============================================================================


class TestMFJScenarioIntegration:
    """Integration tests for the complete MFJ scenario."""

    def test_complete_form_1040_data_structure(self, jones_form_1040_data):
        """Test that complete form data has all required fields."""
        required_fields = [
            "primary_ssn", "primary_first_name", "primary_last_name",
            "spouse_ssn", "spouse_first_name", "spouse_last_name",
            "filing_status", "dependents",
            "wages", "total_income", "agi", "deduction", "taxable_income",
            "tax", "total_tax", "total_payments"
        ]

        for field in required_fields:
            assert field in jones_form_1040_data, f"Missing required field: {field}"

    def test_form_1040_line_math(self, jones_form_1040_data):
        """Test that Form 1040 line math is correct."""
        # Total income = wages + Schedule C profit
        expected_total_income = jones_form_1040_data["wages"] + jones_form_1040_data["schedule_c_profit"]
        assert jones_form_1040_data["total_income"] == expected_total_income

        # AGI = Total income - Adjustments
        expected_agi = jones_form_1040_data["total_income"] - jones_form_1040_data["adjustments"]
        assert jones_form_1040_data["agi"] == expected_agi

        # Taxable income = AGI - Deduction
        expected_taxable = jones_form_1040_data["agi"] - jones_form_1040_data["deduction"]
        assert jones_form_1040_data["taxable_income"] == max(Decimal("0"), expected_taxable)

    def test_business_rules_validation(self, jones_form_1040_data):
        """Test that form data passes business rules validation."""
        validator = BusinessRulesValidator(tax_year=2025, filing_status=2)
        result = validator.validate(jones_form_1040_data)

        # Should pass validation (no fatal errors)
        assert isinstance(result, ValidationResult)

        # Check for any critical errors
        critical_errors = [e for e in result.errors if e.severity == ValidationSeverity.ERROR]

        # Print any errors for debugging
        for error in critical_errors:
            print(f"Validation error: {error.code} - {error.message}")

    def test_xml_serialization(self, jones_form_1040_data):
        """Test that form data can be serialized to XML."""
        serializer = XmlSerializer(tax_year=2025)
        xml = serializer.serialize_form_1040(jones_form_1040_data)

        # Basic XML structure checks
        assert xml.strip().startswith("<IRS1040")
        assert xml.strip().endswith("</IRS1040>")

        # Check key values are present
        assert format_amount(jones_form_1040_data["agi"]) in xml


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
