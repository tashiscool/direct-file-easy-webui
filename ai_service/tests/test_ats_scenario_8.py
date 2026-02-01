"""Comprehensive pytest tests for IRS ATS Test Scenario 8 - Carter Lewis.

This module tests the MeF (Modernized e-File) service functionality using
IRS ATS (Assurance Testing System) Test Scenario 8 data for Carter Lewis.

Test Scenario Reference: IRS ATS Test Scenario 8 (ty25-1040-mef-ats-scenario-8-10212025.pdf)
Primary Taxpayer: Carter Lewis
Filing Status: Married Filing Separately (3)
No Dependents

Key Features Tested:
- Married Filing Separately filing status
- Form 1099-R (Distributions from Pensions, Annuities, Retirement)
- IRA Rollover transactions (60-day rule)
- Social Security benefits (SSA-1099)
- Taxation of Social Security benefits
- Pension income with withholding
- Standard deduction for MFS

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
# FIXTURES - IRS ATS Test Scenario 8 Data (Carter Lewis - MFS with Retirement)
# =============================================================================


@pytest.fixture
def carter_lewis_taxpayer() -> Dict[str, Any]:
    """Fixture for Carter Lewis (primary taxpayer) information.

    IRS ATS Test Scenario 8 - Married Filing Separately with
    retirement distributions and Social Security benefits.

    ATS Reference SSN: 400-00-1039 (invalid for production validation)
    Test SSN: 400-01-1043 (valid format for testing validation logic)

    Note: The spouse (Dana Lewis) is filing separately.
    """
    return {
        "first_name": "Carter",
        "last_name": "Lewis",
        "ssn": "400-01-1043",
        "ssn_clean": "400011043",
        "ssn_ats_reference": "400-00-1039",
        "address": {
            "street": "456 Maple Lane",
            "city": "Phoenix",
            "state": "AZ",
            "zip": "85001"
        },
        "date_of_birth": date(1958, 6, 20),  # Age 67 in 2025
        "occupation": "Retired",
        "digital_assets": False,
    }


@pytest.fixture
def carter_lewis_spouse() -> Dict[str, Any]:
    """Fixture for spouse information (filing separately).

    The spouse is required for MFS even though filing separately.
    Only SSN is reported on the return.
    """
    return {
        "first_name": "Dana",
        "last_name": "Lewis",
        "ssn": "400-01-1044",
        "ssn_clean": "400011044",
        "ssn_ats_reference": "400-00-1040",
    }


@pytest.fixture
def carter_lewis_form_1099r_pension() -> Dict[str, Any]:
    """Fixture for Form 1099-R #1 (Pension Distribution).

    Pension distribution from employer retirement plan.
    This is a regular periodic pension payment (not a rollover).
    """
    return {
        "payer_name": "State Teachers Retirement System",
        "payer_tin": "00-0000071",
        "payer_tin_clean": "000000071",
        "payer_address": {
            "street": "100 Retirement Plaza",
            "city": "Phoenix",
            "state": "AZ",
            "zip": "85002"
        },

        # Box 1 - Gross distribution
        "box_1_gross_distribution": Decimal("36000.00"),

        # Box 2a - Taxable amount
        "box_2a_taxable_amount": Decimal("36000.00"),

        # Box 2b - Taxable amount not determined / Total distribution
        "box_2b_taxable_not_determined": False,
        "box_2b_total_distribution": False,

        # Box 3 - Capital gain (N/A)
        "box_3_capital_gain": Decimal("0.00"),

        # Box 4 - Federal income tax withheld
        "box_4_federal_withholding": Decimal("4320.00"),  # 12% withheld

        # Box 5 - Employee contributions (after-tax)
        "box_5_employee_contributions": Decimal("0.00"),

        # Box 6 - Net unrealized appreciation
        "box_6_nua": Decimal("0.00"),

        # Box 7 - Distribution code
        # Code 7 = Normal distribution
        "box_7_distribution_code": "7",

        # Box 8 - Other (N/A)
        "box_8_other": Decimal("0.00"),

        # Box 9a - Your percentage of total distribution
        "box_9a_percentage": Decimal("0.00"),

        # Box 9b - Total employee contributions
        "box_9b_total_contributions": Decimal("0.00"),

        # Box 10-15 - State/local information
        "box_12_state_distribution": Decimal("36000.00"),
        "box_14_state_withholding": Decimal("1080.00"),
        "state_id": "AZ",

        # IRA indicator
        "is_ira": False,
    }


@pytest.fixture
def carter_lewis_form_1099r_rollover() -> Dict[str, Any]:
    """Fixture for Form 1099-R #2 (IRA Rollover).

    IRA distribution that was rolled over within 60 days.
    The taxable amount is zero because it was a valid rollover.
    """
    return {
        "payer_name": "Fidelity Investments",
        "payer_tin": "00-0000072",
        "payer_tin_clean": "000000072",
        "payer_address": {
            "street": "200 Financial Drive",
            "city": "Boston",
            "state": "MA",
            "zip": "02109"
        },

        # Box 1 - Gross distribution
        "box_1_gross_distribution": Decimal("25000.00"),

        # Box 2a - Taxable amount (0 for rollover)
        "box_2a_taxable_amount": Decimal("0.00"),

        # Box 2b - Taxable amount not determined / Total distribution
        "box_2b_taxable_not_determined": False,
        "box_2b_total_distribution": True,  # This is a total distribution

        # Box 3 - Capital gain (N/A)
        "box_3_capital_gain": Decimal("0.00"),

        # Box 4 - Federal income tax withheld (none for direct rollover)
        "box_4_federal_withholding": Decimal("0.00"),

        # Box 5 - Employee contributions (after-tax)
        "box_5_employee_contributions": Decimal("0.00"),

        # Box 7 - Distribution code
        # Code G = Direct rollover to qualified plan or IRA
        "box_7_distribution_code": "G",

        # IRA indicator
        "is_ira": True,
        "is_rollover": True,
        "rollover_type": "Direct",  # vs. "60-day"
    }


@pytest.fixture
def carter_lewis_ssa_1099() -> Dict[str, Any]:
    """Fixture for SSA-1099 (Social Security Benefits).

    Social Security retirement benefits for Carter Lewis.
    Up to 85% may be taxable based on income.
    """
    return {
        "recipient_name": "Carter Lewis",
        "recipient_ssn": "400-01-1043",

        # Box 1 - Name (Agency name)
        "payer_name": "Social Security Administration",

        # Box 3 - Benefits paid in 2025
        "box_3_benefits_paid": Decimal("24000.00"),

        # Box 4 - Benefits repaid to SSA
        "box_4_benefits_repaid": Decimal("0.00"),

        # Box 5 - Net benefits (Box 3 - Box 4)
        "box_5_net_benefits": Decimal("24000.00"),

        # Box 6 - Voluntary federal income tax withheld
        "box_6_federal_withholding": Decimal("2400.00"),  # 10% withheld

        # Medicare premiums deducted (informational)
        "medicare_part_b_deducted": Decimal("2089.20"),  # ~$174.10/month

        # Taxation calculation
        "half_of_benefits": Decimal("12000.00"),  # 24000 / 2
    }


@pytest.fixture
def carter_lewis_social_security_worksheet() -> Dict[str, Any]:
    """Fixture for Social Security Benefits Worksheet.

    Calculates the taxable portion of Social Security benefits.
    MFS filers who lived with spouse have 85% taxable if any
    income threshold is met.
    """
    return {
        # Line 1 - Total Social Security benefits (from SSA-1099)
        "line_1_total_benefits": Decimal("24000.00"),

        # Line 2 - One-half of line 1
        "line_2_half_benefits": Decimal("12000.00"),

        # Line 3 - Other income (pension, etc.)
        "line_3_other_income": Decimal("36000.00"),

        # Line 4 - Tax-exempt interest (N/A)
        "line_4_tax_exempt_interest": Decimal("0.00"),

        # Line 5 - Add lines 2, 3, and 4
        "line_5_combined": Decimal("48000.00"),  # 12000 + 36000

        # Line 6 - Certain deductions
        "line_6_deductions": Decimal("0.00"),

        # Line 7 - Subtract line 6 from line 5 (provisional income)
        "line_7_provisional_income": Decimal("48000.00"),

        # Line 8 - Base amount for filing status
        # MFS living with spouse: $0 base amount
        "line_8_base_amount": Decimal("0.00"),

        # Line 9 - Subtract line 8 from line 7
        "line_9_excess": Decimal("48000.00"),

        # MFS Rule: If lived with spouse at any time during year,
        # up to 85% of benefits may be taxable if line 9 > $0

        # Taxable Social Security calculation
        # For MFS who lived with spouse: 85% of benefits if provisional income > 0
        "lived_with_spouse": True,
        "taxable_percentage": Decimal("0.85"),
        "taxable_social_security": Decimal("20400.00"),  # 24000 * 0.85
    }


@pytest.fixture
def carter_lewis_form_1040_data(
    carter_lewis_taxpayer,
    carter_lewis_spouse,
    carter_lewis_form_1099r_pension,
    carter_lewis_form_1099r_rollover,
    carter_lewis_ssa_1099,
    carter_lewis_social_security_worksheet
) -> Dict[str, Any]:
    """Fixture for complete Form 1040 data for Carter Lewis.

    Tax Year: 2025
    Filing Status: Married Filing Separately (3)
    Standard Deduction (2025 MFS): $15,000
    """
    # Income
    pension_income = carter_lewis_form_1099r_pension["box_2a_taxable_amount"]
    rollover_taxable = carter_lewis_form_1099r_rollover["box_2a_taxable_amount"]  # $0
    ss_taxable = carter_lewis_social_security_worksheet["taxable_social_security"]

    total_income = pension_income + rollover_taxable + ss_taxable
    agi = total_income  # No adjustments

    # Deduction - OBBBA 2025 MFS Standard Deduction
    standard_deduction_mfs_2025 = Decimal("15750.00")

    # Taxable income
    taxable_income = max(Decimal("0"), agi - standard_deduction_mfs_2025)

    # Tax calculation (2025 tax brackets for MFS)
    # MFS uses same brackets as Single
    # $0 - $11,600: 10%
    # $11,601 - $47,150: 12%
    # Taxable income: $41,400
    if taxable_income <= Decimal("11600.00"):
        calculated_tax = taxable_income * Decimal("0.10")
    elif taxable_income <= Decimal("47150.00"):
        tax_bracket_1 = Decimal("11600.00") * Decimal("0.10")  # $1,160
        remaining = taxable_income - Decimal("11600.00")  # $29,800
        tax_bracket_2 = remaining * Decimal("0.12")  # $3,576
        calculated_tax = tax_bracket_1 + tax_bracket_2  # $4,736
    else:
        # Higher brackets (not expected for this scenario)
        tax_bracket_1 = Decimal("11600.00") * Decimal("0.10")
        tax_bracket_2 = Decimal("35550.00") * Decimal("0.12")
        remaining = taxable_income - Decimal("47150.00")
        tax_bracket_3 = remaining * Decimal("0.22")
        calculated_tax = tax_bracket_1 + tax_bracket_2 + tax_bracket_3

    calculated_tax = calculated_tax.quantize(Decimal("1"))  # Round to whole dollar

    # Total tax (no additional taxes)
    total_tax = calculated_tax

    # Payments
    pension_withholding = carter_lewis_form_1099r_pension["box_4_federal_withholding"]
    ss_withholding = carter_lewis_ssa_1099["box_6_federal_withholding"]
    total_withholding = pension_withholding + ss_withholding

    total_payments = total_withholding

    # Refund or owed
    if total_payments > total_tax:
        refund = total_payments - total_tax
        amount_owed = Decimal("0")
    else:
        refund = Decimal("0")
        amount_owed = total_tax - total_payments

    return {
        # Taxpayer info
        "primary_ssn": carter_lewis_taxpayer["ssn_clean"],
        "primary_first_name": carter_lewis_taxpayer["first_name"],
        "primary_last_name": carter_lewis_taxpayer["last_name"],
        "address": carter_lewis_taxpayer["address"],
        "filing_status": 3,  # Married Filing Separately

        # Checkboxes
        "presidential_campaign": False,
        "digital_assets": False,

        # Spouse info (required for MFS)
        "spouse_ssn": carter_lewis_spouse["ssn_clean"],
        "spouse_first_name": carter_lewis_spouse["first_name"],
        "spouse_last_name": carter_lewis_spouse["last_name"],

        # No dependents
        "dependents": [],

        # Income (Lines 1-9)
        "line_1z_wages": Decimal("0"),  # No wages (retired)
        "wages": Decimal("0"),
        "line_2a_tax_exempt_interest": Decimal("0"),
        "line_2b_taxable_interest": Decimal("0"),
        "line_3a_qualified_dividends": Decimal("0"),
        "line_3b_ordinary_dividends": Decimal("0"),
        "line_4a_ira_distributions": carter_lewis_form_1099r_rollover["box_1_gross_distribution"],
        "line_4b_taxable_ira": carter_lewis_form_1099r_rollover["box_2a_taxable_amount"],
        "line_5a_pensions_annuities": carter_lewis_form_1099r_pension["box_1_gross_distribution"],
        "line_5b_taxable_pensions": carter_lewis_form_1099r_pension["box_2a_taxable_amount"],
        "line_6a_social_security": carter_lewis_ssa_1099["box_5_net_benefits"],
        "line_6b_taxable_social_security": ss_taxable,
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
        "line_12_standard_deduction": standard_deduction_mfs_2025,
        "line_12_itemized_deduction": Decimal("0"),
        "line_12_deduction": standard_deduction_mfs_2025,
        "line_13_qbi_deduction": Decimal("0"),
        "line_14_total_deductions": standard_deduction_mfs_2025,
        "deduction": standard_deduction_mfs_2025,

        # Taxable income (Line 15)
        "line_15_taxable_income": taxable_income,
        "taxable_income": taxable_income,

        # Tax (Lines 16-24)
        "line_16_tax": calculated_tax,
        "line_17_schedule_2": Decimal("0"),
        "line_18_total": calculated_tax,
        "line_19_ctc_actc": Decimal("0"),  # No dependents
        "line_20_schedule_3": Decimal("0"),
        "line_21_credits_subtotal": Decimal("0"),
        "line_22_tax_minus_credits": calculated_tax,
        "line_23_other_taxes": Decimal("0"),
        "line_24_total_tax": total_tax,
        "total_tax": total_tax,

        # Payments (Lines 25-33)
        "line_25a_w2_withholding": Decimal("0"),
        "line_25b_1099_withholding": total_withholding,
        "line_25c_other_withholding": Decimal("0"),
        "line_25d_total_withholding": total_withholding,
        "line_26_estimated_payments": Decimal("0"),
        "line_27_eic": Decimal("0"),
        "line_28_actc": Decimal("0"),
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
        "has_form_1099r": True,
        "has_ssa_1099": True,

        # Form data
        "form_1099r_pension": carter_lewis_form_1099r_pension,
        "form_1099r_rollover": carter_lewis_form_1099r_rollover,
        "ssa_1099": carter_lewis_ssa_1099,
        "social_security_worksheet": carter_lewis_social_security_worksheet,
    }


# =============================================================================
# TEST CLASS: Taxpayer and Spouse Information
# =============================================================================


class TestTaxpayerInformation:
    """Tests for taxpayer and spouse information."""

    def test_taxpayer_name(self, carter_lewis_taxpayer):
        """Test taxpayer name."""
        assert carter_lewis_taxpayer["first_name"] == "Carter"
        assert carter_lewis_taxpayer["last_name"] == "Lewis"

    def test_taxpayer_ssn(self, carter_lewis_taxpayer):
        """Test taxpayer SSN format."""
        ssn_clean = carter_lewis_taxpayer["ssn_clean"]
        assert len(ssn_clean) == 9
        assert ssn_clean.isdigit()

    def test_taxpayer_is_retired(self, carter_lewis_taxpayer):
        """Test taxpayer occupation is retired."""
        assert carter_lewis_taxpayer["occupation"] == "Retired"

    def test_spouse_info_present(self, carter_lewis_spouse):
        """Test spouse information is present for MFS."""
        assert carter_lewis_spouse["first_name"] == "Dana"
        assert carter_lewis_spouse["last_name"] == "Lewis"
        assert len(carter_lewis_spouse["ssn_clean"]) == 9


# =============================================================================
# TEST CLASS: Form 1099-R Pension
# =============================================================================


class TestForm1099RPension:
    """Tests for Form 1099-R pension distribution."""

    def test_gross_distribution(self, carter_lewis_form_1099r_pension):
        """Test gross distribution amount."""
        assert carter_lewis_form_1099r_pension["box_1_gross_distribution"] == Decimal("36000.00")

    def test_taxable_amount(self, carter_lewis_form_1099r_pension):
        """Test taxable amount equals gross (no basis)."""
        gross = carter_lewis_form_1099r_pension["box_1_gross_distribution"]
        taxable = carter_lewis_form_1099r_pension["box_2a_taxable_amount"]

        assert taxable == gross

    def test_federal_withholding(self, carter_lewis_form_1099r_pension):
        """Test federal withholding on pension."""
        assert carter_lewis_form_1099r_pension["box_4_federal_withholding"] == Decimal("4320.00")

    def test_distribution_code(self, carter_lewis_form_1099r_pension):
        """Test distribution code is 7 (normal distribution)."""
        assert carter_lewis_form_1099r_pension["box_7_distribution_code"] == "7"

    def test_not_ira(self, carter_lewis_form_1099r_pension):
        """Test pension is not an IRA distribution."""
        assert carter_lewis_form_1099r_pension["is_ira"] is False


# =============================================================================
# TEST CLASS: Form 1099-R Rollover
# =============================================================================


class TestForm1099RRollover:
    """Tests for Form 1099-R IRA rollover."""

    def test_gross_distribution(self, carter_lewis_form_1099r_rollover):
        """Test gross distribution amount."""
        assert carter_lewis_form_1099r_rollover["box_1_gross_distribution"] == Decimal("25000.00")

    def test_taxable_amount_is_zero(self, carter_lewis_form_1099r_rollover):
        """Test taxable amount is zero for rollover."""
        assert carter_lewis_form_1099r_rollover["box_2a_taxable_amount"] == Decimal("0.00")

    def test_distribution_code_rollover(self, carter_lewis_form_1099r_rollover):
        """Test distribution code is G (direct rollover)."""
        assert carter_lewis_form_1099r_rollover["box_7_distribution_code"] == "G"

    def test_is_ira(self, carter_lewis_form_1099r_rollover):
        """Test this is an IRA distribution."""
        assert carter_lewis_form_1099r_rollover["is_ira"] is True

    def test_is_rollover(self, carter_lewis_form_1099r_rollover):
        """Test this is marked as a rollover."""
        assert carter_lewis_form_1099r_rollover["is_rollover"] is True
        assert carter_lewis_form_1099r_rollover["rollover_type"] == "Direct"


# =============================================================================
# TEST CLASS: Social Security Benefits
# =============================================================================


class TestSocialSecurityBenefits:
    """Tests for SSA-1099 Social Security benefits."""

    def test_net_benefits(self, carter_lewis_ssa_1099):
        """Test net Social Security benefits."""
        assert carter_lewis_ssa_1099["box_5_net_benefits"] == Decimal("24000.00")

    def test_federal_withholding(self, carter_lewis_ssa_1099):
        """Test federal withholding on Social Security."""
        assert carter_lewis_ssa_1099["box_6_federal_withholding"] == Decimal("2400.00")

    def test_half_of_benefits_calculation(self, carter_lewis_ssa_1099):
        """Test half of benefits calculation."""
        net = carter_lewis_ssa_1099["box_5_net_benefits"]
        half = carter_lewis_ssa_1099["half_of_benefits"]

        assert half == net / 2
        assert half == Decimal("12000.00")


# =============================================================================
# TEST CLASS: Social Security Taxation Worksheet
# =============================================================================


class TestSocialSecurityWorksheet:
    """Tests for Social Security benefits taxation worksheet."""

    def test_provisional_income_calculation(self, carter_lewis_social_security_worksheet):
        """Test provisional income calculation."""
        half_ss = carter_lewis_social_security_worksheet["line_2_half_benefits"]
        other_income = carter_lewis_social_security_worksheet["line_3_other_income"]
        expected = half_ss + other_income

        assert carter_lewis_social_security_worksheet["line_7_provisional_income"] == expected

    def test_mfs_base_amount_zero(self, carter_lewis_social_security_worksheet):
        """Test MFS base amount is $0 when living with spouse."""
        assert carter_lewis_social_security_worksheet["lived_with_spouse"] is True
        assert carter_lewis_social_security_worksheet["line_8_base_amount"] == Decimal("0.00")

    def test_mfs_85_percent_taxable(self, carter_lewis_social_security_worksheet):
        """Test 85% of Social Security is taxable for MFS with income."""
        assert carter_lewis_social_security_worksheet["taxable_percentage"] == Decimal("0.85")

    def test_taxable_social_security_calculation(self, carter_lewis_social_security_worksheet):
        """Test taxable Social Security amount."""
        total_benefits = carter_lewis_social_security_worksheet["line_1_total_benefits"]
        rate = carter_lewis_social_security_worksheet["taxable_percentage"]
        expected = total_benefits * rate

        assert carter_lewis_social_security_worksheet["taxable_social_security"] == expected


# =============================================================================
# TEST CLASS: Tax Calculation
# =============================================================================


class TestTaxCalculation:
    """Tests for Form 1040 tax calculations."""

    def test_filing_status_mfs(self, carter_lewis_form_1040_data):
        """Test filing status is Married Filing Separately."""
        assert carter_lewis_form_1040_data["filing_status"] == 3

    def test_spouse_ssn_required(self, carter_lewis_form_1040_data):
        """Test spouse SSN is present for MFS."""
        assert carter_lewis_form_1040_data["spouse_ssn"] is not None

    def test_no_wages(self, carter_lewis_form_1040_data):
        """Test no wages for retired taxpayer."""
        assert carter_lewis_form_1040_data["wages"] == Decimal("0")

    def test_total_income_calculation(self, carter_lewis_form_1040_data):
        """Test total income includes pension and SS."""
        pension = carter_lewis_form_1040_data["line_5b_taxable_pensions"]
        ss_taxable = carter_lewis_form_1040_data["line_6b_taxable_social_security"]

        expected_total = pension + ss_taxable
        assert carter_lewis_form_1040_data["total_income"] == expected_total

    def test_standard_deduction_mfs(self, carter_lewis_form_1040_data):
        """Test MFS standard deduction for 2025."""
        assert carter_lewis_form_1040_data["deduction"] == Decimal("15000.00")

    def test_ira_rollover_not_taxable(self, carter_lewis_form_1040_data):
        """Test IRA rollover is not included in taxable income."""
        ira_taxable = carter_lewis_form_1040_data["line_4b_taxable_ira"]
        assert ira_taxable == Decimal("0.00")


# =============================================================================
# TEST CLASS: Withholding and Payments
# =============================================================================


class TestWithholdingPayments:
    """Tests for withholding and payments."""

    def test_pension_withholding(self, carter_lewis_form_1040_data):
        """Test pension withholding is included."""
        pension_wh = carter_lewis_form_1040_data["form_1099r_pension"]["box_4_federal_withholding"]
        assert pension_wh == Decimal("4320.00")

    def test_ss_withholding(self, carter_lewis_form_1040_data):
        """Test Social Security withholding is included."""
        ss_wh = carter_lewis_form_1040_data["ssa_1099"]["box_6_federal_withholding"]
        assert ss_wh == Decimal("2400.00")

    def test_total_withholding(self, carter_lewis_form_1040_data):
        """Test total withholding calculation."""
        expected = Decimal("4320.00") + Decimal("2400.00")  # Pension + SS
        assert carter_lewis_form_1040_data["line_25d_total_withholding"] == expected

    def test_1099_withholding_line(self, carter_lewis_form_1040_data):
        """Test withholding reported on Line 25b (1099 withholding)."""
        # Pension and SS withholding goes to Line 25b
        total_1099_wh = carter_lewis_form_1040_data["line_25b_1099_withholding"]
        expected = Decimal("4320.00") + Decimal("2400.00")

        assert total_1099_wh == expected


# =============================================================================
# TEST CLASS: XML Serialization
# =============================================================================


class TestScenario8XMLSerialization:
    """Tests for XML serialization of Scenario 8 data."""

    def test_taxpayer_info_creation(self, carter_lewis_taxpayer):
        """Test TaxpayerInfo object creation."""
        taxpayer_info = TaxpayerInfo(
            primary_ssn=carter_lewis_taxpayer["ssn_clean"],
            primary_first_name=carter_lewis_taxpayer["first_name"],
            primary_last_name=carter_lewis_taxpayer["last_name"],
            primary_date_of_birth=carter_lewis_taxpayer["date_of_birth"],
        )

        assert taxpayer_info.primary_ssn == "400011043"
        assert taxpayer_info.primary_first_name == "Carter"
        assert taxpayer_info.primary_last_name == "Lewis"

    def test_submission_id_generation(self):
        """Test MeF submission ID generation."""
        submission_id = SubmissionId.generate(efin="123456", sequence=1)

        assert len(submission_id.submission_id) == 20
        assert submission_id.submission_id.isdigit()


# =============================================================================
# TEST CLASS: Business Rules Validation
# =============================================================================


class TestScenario8BusinessRules:
    """Tests for business rules validation of Scenario 8 data."""

    def test_mfs_requires_spouse_ssn(self, carter_lewis_form_1040_data):
        """Test MFS filing requires spouse SSN."""
        assert carter_lewis_form_1040_data["filing_status"] == 3
        assert carter_lewis_form_1040_data["spouse_ssn"] is not None

    def test_mfs_no_eic(self, carter_lewis_form_1040_data):
        """Test MFS filer is not eligible for EIC."""
        assert carter_lewis_form_1040_data["line_27_eic"] == Decimal("0")

    def test_rollover_properly_excluded(self, carter_lewis_form_1040_data):
        """Test rollover amount is properly excluded from income."""
        gross_ira = carter_lewis_form_1040_data["line_4a_ira_distributions"]
        taxable_ira = carter_lewis_form_1040_data["line_4b_taxable_ira"]

        # Gross shows full distribution, taxable shows 0 for rollover
        assert gross_ira == Decimal("25000.00")
        assert taxable_ira == Decimal("0.00")


# =============================================================================
# TEST CLASS: Integration Tests
# =============================================================================


class TestScenario8Integration:
    """Integration tests for the complete Scenario 8 data."""

    def test_complete_form_1040_structure(self, carter_lewis_form_1040_data):
        """Test complete form data has all required fields."""
        required_fields = [
            "primary_ssn", "primary_first_name", "primary_last_name",
            "spouse_ssn", "filing_status",
            "total_income", "agi", "deduction", "taxable_income",
            "total_tax", "total_payments",
        ]

        for field in required_fields:
            assert field in carter_lewis_form_1040_data, f"Missing field: {field}"

    def test_form_1040_line_math(self, carter_lewis_form_1040_data):
        """Test Form 1040 line math consistency."""
        # Line 11 = Line 9 - Line 10
        assert carter_lewis_form_1040_data["line_11_agi"] == (
            carter_lewis_form_1040_data["line_9_total_income"] -
            carter_lewis_form_1040_data["line_10_adjustments"]
        )

        # Line 15 = Line 11 - Line 14
        assert carter_lewis_form_1040_data["line_15_taxable_income"] == (
            carter_lewis_form_1040_data["line_11_agi"] -
            carter_lewis_form_1040_data["line_14_total_deductions"]
        )

    def test_pension_to_form_1040_flow(self, carter_lewis_form_1099r_pension, carter_lewis_form_1040_data):
        """Test pension distribution flows to Form 1040."""
        pension_taxable = carter_lewis_form_1099r_pension["box_2a_taxable_amount"]
        form_1040_pension = carter_lewis_form_1040_data["line_5b_taxable_pensions"]

        assert form_1040_pension == pension_taxable

    def test_ss_to_form_1040_flow(self, carter_lewis_social_security_worksheet, carter_lewis_form_1040_data):
        """Test Social Security taxable amount flows to Form 1040."""
        worksheet_taxable = carter_lewis_social_security_worksheet["taxable_social_security"]
        form_1040_ss = carter_lewis_form_1040_data["line_6b_taxable_social_security"]

        assert form_1040_ss == worksheet_taxable

    def test_withholding_totals(self, carter_lewis_form_1040_data):
        """Test all withholding sources are totaled."""
        pension_wh = carter_lewis_form_1040_data["form_1099r_pension"]["box_4_federal_withholding"]
        ss_wh = carter_lewis_form_1040_data["ssa_1099"]["box_6_federal_withholding"]
        total_wh = carter_lewis_form_1040_data["line_25d_total_withholding"]

        assert total_wh == pension_wh + ss_wh


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
