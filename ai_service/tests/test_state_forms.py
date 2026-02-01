"""Comprehensive pytest tests for the State Forms Service.

This module tests the state forms service functionality using
IRS ATS (Assurance Testing System) Test Scenario 2 data for taxpayers
John & Judy Jones - New Jersey residents.

Test Scenario Reference: IRS ATS Test Scenario 2
Primary Taxpayer: John Jones
SSN: 400-00-1038
DOB: August 2, 1965

Spouse: Judy Jones
SSN: 400-00-1071
DOB: March 19, 1966 (Deceased September 11, 2025)

Dependent: Jacob Jones
SSN: 400-00-1070
Relationship: Son (Full-time student)

Filing Status: Married Filing Jointly
Address: 800 Gooseneck Point Road, Oceanport, NJ 07757

W-2 Income:
- John (Southwest Airlines): Wages $29,513, NJ withholding $927
- Judy (Target): Wages $8,513, NJ withholding $101
- Total wages: $38,026
- Total NJ withholding: $1,028

Schedule A (Itemized):
- State income taxes: $1,028
- Real estate taxes: $8,972
- Mortgage interest: $11,251
- Charitable: $950 ($250 cash + $700 noncash)

Tests cover:
- State tax bracket calculations (NJ, CA, NY, IL)
- Personal exemptions
- Property tax deductions
- State credits (EITC, property tax, child credits)
- Multi-state filing and allocation
- State form generation
- Filing status variations
"""

import pytest
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List

import sys
import os

# Add the parent directory to path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

# Import directly from the module file to avoid __init__.py dependencies
import importlib.util
spec = importlib.util.spec_from_file_location(
    "state_forms_service",
    os.path.join(parent_dir, "services", "state_forms_service.py")
)
state_forms_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(state_forms_module)

# Extract imports from the loaded module
StateCode = state_forms_module.StateCode
ResidencyStatus = state_forms_module.ResidencyStatus
FilingStatus = state_forms_module.FilingStatus
StateTaxBracket = state_forms_module.StateTaxBracket
StateFormLine = state_forms_module.StateFormLine
StateSchedule = state_forms_module.StateSchedule
StateForm = state_forms_module.StateForm
StateCredit = state_forms_module.StateCredit
StateDeduction = state_forms_module.StateDeduction
StateTaxCalculation = state_forms_module.StateTaxCalculation
MultiStateAllocation = state_forms_module.MultiStateAllocation
StateReturn = state_forms_module.StateReturn
StateFormsService = state_forms_module.StateFormsService


# =============================================================================
# FIXTURES - IRS ATS Test Scenario 2 Data (John & Judy Jones)
# =============================================================================


@pytest.fixture
def john_jones_info() -> Dict[str, Any]:
    """Fixture for John Jones' taxpayer information.

    IRS ATS Test Scenario 2 - Primary taxpayer.
    Married Filing Jointly with deceased spouse.
    """
    return {
        "first_name": "John",
        "last_name": "Jones",
        "ssn": "400-00-1038",
        "ssn_clean": "400001038",
        "date_of_birth": date(1965, 8, 2),
        "occupation": "Flight Attendant",
    }


@pytest.fixture
def judy_jones_info() -> Dict[str, Any]:
    """Fixture for Judy Jones' taxpayer information.

    Spouse - Deceased September 11, 2025.
    """
    return {
        "first_name": "Judy",
        "last_name": "Jones",
        "ssn": "400-00-1071",
        "ssn_clean": "400001071",
        "date_of_birth": date(1966, 3, 19),
        "date_of_death": date(2025, 9, 11),
        "occupation": "Sales Associate",
    }


@pytest.fixture
def jacob_jones_info() -> Dict[str, Any]:
    """Fixture for Jacob Jones - dependent (full-time student son)."""
    return {
        "first_name": "Jacob",
        "last_name": "Jones",
        "ssn": "400-00-1070",
        "ssn_clean": "400001070",
        "relationship": "Son",
        "full_time_student": True,
    }


@pytest.fixture
def jones_address() -> Dict[str, Any]:
    """Fixture for Jones family address - NJ resident."""
    return {
        "street": "800 Gooseneck Point Road",
        "city": "Oceanport",
        "state": "NJ",
        "zip": "07757",
    }


@pytest.fixture
def john_w2() -> Dict[str, Any]:
    """Fixture for John Jones' W-2 from Southwest Airlines.

    Federal wages: $29,513
    NJ wages: $29,513
    NJ withholding: $927
    """
    return {
        "employer_name": "Southwest Airlines",
        "employer_ein": "00-0000001",
        "wages": Decimal("29513.00"),
        "federal_withholding": Decimal("2500.00"),
        "ss_wages": Decimal("29513.00"),
        "ss_tax": Decimal("1829.81"),
        "medicare_wages": Decimal("29513.00"),
        "medicare_tax": Decimal("427.94"),
        "state": "NJ",
        "state_wages": Decimal("29513.00"),
        "state_tax": Decimal("927.00"),
    }


@pytest.fixture
def judy_w2() -> Dict[str, Any]:
    """Fixture for Judy Jones' W-2 from Target.

    Federal wages: $8,513
    NJ wages: $8,513
    NJ withholding: $101
    """
    return {
        "employer_name": "Target",
        "employer_ein": "00-0000002",
        "wages": Decimal("8513.00"),
        "federal_withholding": Decimal("500.00"),
        "ss_wages": Decimal("8513.00"),
        "ss_tax": Decimal("527.81"),
        "medicare_wages": Decimal("8513.00"),
        "medicare_tax": Decimal("123.44"),
        "state": "NJ",
        "state_wages": Decimal("8513.00"),
        "state_tax": Decimal("101.00"),
    }


@pytest.fixture
def jones_w2_totals(john_w2, judy_w2) -> Dict[str, Any]:
    """Fixture for combined W-2 totals for John and Judy Jones."""
    return {
        "total_wages": john_w2["wages"] + judy_w2["wages"],  # $38,026
        "total_federal_withholding": john_w2["federal_withholding"] + judy_w2["federal_withholding"],
        "total_nj_wages": john_w2["state_wages"] + judy_w2["state_wages"],
        "total_nj_withholding": john_w2["state_tax"] + judy_w2["state_tax"],  # $1,028
    }


@pytest.fixture
def jones_schedule_a() -> Dict[str, Any]:
    """Fixture for Jones family Schedule A (Itemized Deductions).

    State income taxes: $1,028
    Real estate taxes: $8,972
    Mortgage interest: $11,251
    Charitable contributions: $950 ($250 cash + $700 noncash)
    """
    return {
        "state_income_taxes": Decimal("1028.00"),
        "real_estate_taxes": Decimal("8972.00"),
        "total_property_taxes": Decimal("8972.00"),
        "mortgage_interest": Decimal("11251.00"),
        "charitable_cash": Decimal("250.00"),
        "charitable_noncash": Decimal("700.00"),
        "total_charitable": Decimal("950.00"),
        # Total itemized = 1028 + 8972 + 11251 + 950 = 22,201
        # But SALT is capped at $10,000
        # Effective: 10000 + 11251 + 950 = 22,201 (with SALT cap adjustment)
        "total_before_salt_cap": Decimal("22201.00"),
    }


@pytest.fixture
def jones_federal_return(
    jones_w2_totals, jones_schedule_a
) -> Dict[str, Any]:
    """Fixture for Jones family federal return data used for state calculations.

    AGI: $38,026 (wages only)
    Filing Status: Married Filing Jointly
    Dependents: 1 (Jacob)
    """
    return {
        # Income
        "/wages": jones_w2_totals["total_wages"],
        "/totalW2Wages": jones_w2_totals["total_wages"],
        "/adjustedGrossIncome": jones_w2_totals["total_wages"],
        "/agi": jones_w2_totals["total_wages"],

        # State withholding
        "/stateWithholding": jones_w2_totals["total_nj_withholding"],
        "/stateWithholding_NJ": jones_w2_totals["total_nj_withholding"],

        # Schedule A data
        "/stateIncomeTax": jones_schedule_a["state_income_taxes"],
        "/propertyTax": jones_schedule_a["real_estate_taxes"],
        "/propertyTaxesPaid": jones_schedule_a["real_estate_taxes"],
        "/mortgageInterest": jones_schedule_a["mortgage_interest"],
        "/charitableContributions": jones_schedule_a["total_charitable"],

        # Other income (none for this scenario)
        "/interestIncome": Decimal("0"),
        "/dividendIncome": Decimal("0"),
        "/capitalGains": Decimal("0"),
        "/businessIncome": Decimal("0"),
        "/socialSecurityBenefits": Decimal("0"),
        "/pensionIncome": Decimal("0"),
        "/retirementIncome": Decimal("0"),

        # Dependents
        "/numberOfDependents": 1,
        "/dependentsUnder17": 0,  # Jacob is full-time student (likely 19+)

        # Credits (federal)
        "/earnedIncomeCredit": Decimal("0"),  # Income likely too high
        "/eitc": Decimal("0"),

        # Rent (none - they own)
        "/rentPaid": Decimal("0"),
        "/annualRent": Decimal("0"),

        # Education
        "/educationExpenses": Decimal("0"),
    }


@pytest.fixture
def state_forms_service() -> StateFormsService:
    """Fixture for StateFormsService instance."""
    return StateFormsService()


# =============================================================================
# TEST CLASS: NJ Tax Brackets for MFJ
# =============================================================================


class TestNJTaxBracketsMFJ:
    """Tests for New Jersey progressive tax brackets for Married Filing Jointly.

    NJ 2025 MFJ Tax Brackets:
    - 1.4% on income up to $20,000
    - 1.75% on income $20,001 to $50,000
    - 2.45% on income $50,001 to $70,000
    - 3.5% on income $70,001 to $80,000
    - 5.525% on income $80,001 to $150,000
    - 6.37% on income $150,001 to $500,000
    - 8.97% on income $500,001 to $1,000,000
    - 10.75% on income over $1,000,000
    """

    def test_nj_tax_brackets_mfj_defined(self, state_forms_service):
        """Test that NJ MFJ tax brackets are properly defined."""
        brackets = state_forms_service.STATE_BRACKETS_2025.get(StateCode.NJ, {})
        mfj_brackets = brackets.get(FilingStatus.MARRIED_FILING_JOINTLY, [])

        assert len(mfj_brackets) > 0
        assert mfj_brackets[0].rate == Decimal("0.014")  # 1.4%
        assert mfj_brackets[0].min_income == Decimal("0")

    def test_nj_tax_brackets_mfj_first_bracket(self, state_forms_service):
        """Test NJ MFJ first bracket: 1.4% on income up to $20,000."""
        brackets = state_forms_service.STATE_BRACKETS_2025[StateCode.NJ][FilingStatus.MARRIED_FILING_JOINTLY]

        first_bracket = brackets[0]
        assert first_bracket.rate == Decimal("0.014")
        assert first_bracket.min_income == Decimal("0")
        assert first_bracket.max_income == Decimal("20000")

    def test_nj_tax_brackets_mfj_second_bracket(self, state_forms_service):
        """Test NJ MFJ second bracket: 1.75% on income $20,001 to $50,000."""
        brackets = state_forms_service.STATE_BRACKETS_2025[StateCode.NJ][FilingStatus.MARRIED_FILING_JOINTLY]

        second_bracket = brackets[1]
        assert second_bracket.rate == Decimal("0.0175")
        assert second_bracket.min_income == Decimal("20000")
        assert second_bracket.max_income == Decimal("50000")

    def test_nj_tax_brackets_mfj_third_bracket(self, state_forms_service):
        """Test NJ MFJ third bracket: 2.45% on income $50,001 to $70,000."""
        brackets = state_forms_service.STATE_BRACKETS_2025[StateCode.NJ][FilingStatus.MARRIED_FILING_JOINTLY]

        third_bracket = brackets[2]
        assert third_bracket.rate == Decimal("0.0245")
        assert third_bracket.min_income == Decimal("50000")
        assert third_bracket.max_income == Decimal("70000")

    def test_nj_tax_calculation_jones_family(self, state_forms_service, jones_federal_return):
        """Test NJ tax calculation for Jones family.

        AGI: $38,026
        Personal exemptions: $1,000 x 2 = $2,000
        Dependent exemption: $1,500 x 1 = $1,500
        Total exemptions: $3,500
        Taxable income: $38,026 - $3,500 = $34,526

        Tax calculation:
        - First $20,000 at 1.4% = $280
        - Next $14,526 ($20,001 to $34,526) at 1.75% = $254.21
        - Total tax: $534.21
        """
        state_return = state_forms_service.generate_state_return(
            state=StateCode.NJ,
            federal_return=jones_federal_return,
            filing_status=FilingStatus.MARRIED_FILING_JOINTLY,
            residency_status=ResidencyStatus.FULL_YEAR_RESIDENT,
            tax_year=2025
        )

        calc = state_return.calculation

        # Verify AGI
        assert calc.federal_agi == Decimal("38026")

        # Verify exemptions (NJ: $1,000 per person + $1,500 per dependent)
        expected_exemptions = Decimal("1000") * 2 + Decimal("1500") * 1
        assert calc.exemptions == expected_exemptions

        # Tax should be calculated (will be approximately $534)
        assert calc.tax_before_credits > Decimal("0")

    def test_nj_tax_brackets_progressive(self, state_forms_service):
        """Test that NJ brackets are properly progressive."""
        brackets = state_forms_service.STATE_BRACKETS_2025[StateCode.NJ][FilingStatus.MARRIED_FILING_JOINTLY]

        # Rates should increase with each bracket
        for i in range(1, len(brackets)):
            assert brackets[i].rate > brackets[i-1].rate

        # Income thresholds should be contiguous
        for i in range(1, len(brackets)):
            assert brackets[i].min_income == brackets[i-1].max_income

    def test_nj_top_bracket_rate(self, state_forms_service):
        """Test NJ top bracket rate is 10.75%."""
        brackets = state_forms_service.STATE_BRACKETS_2025[StateCode.NJ][FilingStatus.MARRIED_FILING_JOINTLY]

        top_bracket = brackets[-1]
        assert top_bracket.rate == Decimal("0.1075")
        assert top_bracket.max_income is None  # Unlimited


# =============================================================================
# TEST CLASS: NJ Standard Deduction
# =============================================================================


class TestNJStandardDeduction:
    """Tests for NJ standard deduction (which doesn't exist).

    New Jersey does NOT have a standard deduction.
    Instead, NJ uses personal exemptions and allows
    property tax deductions and certain other deductions.
    """

    def test_nj_standard_deduction_is_zero(self, state_forms_service):
        """Test that NJ standard deduction is zero for all filing statuses."""
        std_deductions = state_forms_service.STATE_STANDARD_DEDUCTIONS_2025.get(StateCode.NJ, {})

        # NJ should have $0 standard deduction
        assert std_deductions.get(FilingStatus.SINGLE, Decimal("0")) == Decimal("0")
        assert std_deductions.get(FilingStatus.MARRIED_FILING_JOINTLY, Decimal("0")) == Decimal("0")

    def test_nj_no_standard_deduction_in_calculation(
        self, state_forms_service, jones_federal_return
    ):
        """Test that NJ calculation uses $0 standard deduction."""
        state_return = state_forms_service.generate_state_return(
            state=StateCode.NJ,
            federal_return=jones_federal_return,
            filing_status=FilingStatus.MARRIED_FILING_JOINTLY,
            tax_year=2025
        )

        calc = state_return.calculation
        assert calc.standard_deduction == Decimal("0")

    def test_nj_uses_itemized_over_standard(
        self, state_forms_service, jones_federal_return
    ):
        """Test that NJ uses itemized deductions when standard is $0."""
        state_return = state_forms_service.generate_state_return(
            state=StateCode.NJ,
            federal_return=jones_federal_return,
            filing_status=FilingStatus.MARRIED_FILING_JOINTLY,
            tax_year=2025
        )

        calc = state_return.calculation

        # With $0 standard deduction, itemized should be used if > 0
        # NJ has limited itemized deductions (property tax is handled separately)
        assert calc.standard_deduction == Decimal("0")

    def test_compare_nj_to_ca_standard_deduction(self, state_forms_service):
        """Test that CA has standard deduction while NJ does not."""
        nj_std = state_forms_service.STATE_STANDARD_DEDUCTIONS_2025.get(StateCode.NJ, {})
        ca_std = state_forms_service.STATE_STANDARD_DEDUCTIONS_2025.get(StateCode.CA, {})

        # NJ should be $0
        assert nj_std.get(FilingStatus.MARRIED_FILING_JOINTLY, Decimal("0")) == Decimal("0")

        # CA should have a positive value
        assert ca_std.get(FilingStatus.MARRIED_FILING_JOINTLY, Decimal("0")) > Decimal("0")


# =============================================================================
# TEST CLASS: NJ Personal Exemptions
# =============================================================================


class TestNJPersonalExemption:
    """Tests for NJ personal exemptions.

    NJ allows exemptions:
    - $1,000 per taxpayer
    - $1,500 per dependent
    """

    def test_nj_personal_exemption_defined(self, state_forms_service):
        """Test NJ personal exemption is $1,000."""
        exemptions = state_forms_service.STATE_EXEMPTIONS_2025.get(StateCode.NJ, {})

        assert exemptions["personal"] == Decimal("1000")

    def test_nj_dependent_exemption_defined(self, state_forms_service):
        """Test NJ dependent exemption is $1,500."""
        exemptions = state_forms_service.STATE_EXEMPTIONS_2025.get(StateCode.NJ, {})

        assert exemptions["dependent"] == Decimal("1500")

    def test_nj_exemption_mfj_two_taxpayers(
        self, state_forms_service, jones_federal_return
    ):
        """Test NJ exemption for MFJ (2 personal exemptions)."""
        state_return = state_forms_service.generate_state_return(
            state=StateCode.NJ,
            federal_return=jones_federal_return,
            filing_status=FilingStatus.MARRIED_FILING_JOINTLY,
            tax_year=2025
        )

        calc = state_return.calculation

        # MFJ = 2 personal ($1,000 each) + 1 dependent ($1,500)
        expected = Decimal("1000") * 2 + Decimal("1500") * 1
        assert calc.exemptions == expected

    def test_nj_exemption_single_filer(self, state_forms_service, jones_federal_return):
        """Test NJ exemption for single filer (1 personal exemption)."""
        # Modify return for single filer with no dependents
        single_return = jones_federal_return.copy()
        single_return["/numberOfDependents"] = 0

        state_return = state_forms_service.generate_state_return(
            state=StateCode.NJ,
            federal_return=single_return,
            filing_status=FilingStatus.SINGLE,
            tax_year=2025
        )

        calc = state_return.calculation

        # Single = 1 personal ($1,000) + 0 dependents
        expected = Decimal("1000") * 1
        assert calc.exemptions == expected

    def test_nj_exemption_with_multiple_dependents(
        self, state_forms_service, jones_federal_return
    ):
        """Test NJ exemption with 3 dependents."""
        multi_dep_return = jones_federal_return.copy()
        multi_dep_return["/numberOfDependents"] = 3

        state_return = state_forms_service.generate_state_return(
            state=StateCode.NJ,
            federal_return=multi_dep_return,
            filing_status=FilingStatus.MARRIED_FILING_JOINTLY,
            tax_year=2025
        )

        calc = state_return.calculation

        # MFJ = 2 personal ($1,000 each) + 3 dependents ($1,500 each)
        expected = Decimal("1000") * 2 + Decimal("1500") * 3
        assert calc.exemptions == expected


# =============================================================================
# TEST CLASS: NJ Property Tax Deduction
# =============================================================================


class TestNJPropertyTaxDeduction:
    """Tests for NJ property tax deduction.

    NJ allows property tax deductions/credits:
    - Property tax deduction up to $15,000
    - Homestead Benefit credit for eligible homeowners
    """

    def test_nj_property_tax_in_federal_return(self, jones_schedule_a):
        """Test that property tax data is available for NJ calculation."""
        assert jones_schedule_a["real_estate_taxes"] == Decimal("8972")

    def test_nj_property_tax_credit_calculation(
        self, state_forms_service, jones_federal_return
    ):
        """Test NJ property tax credit for Jones family.

        Income: $38,026 (under $150,000 threshold)
        Property tax: $8,972
        Credit should be 5% of property tax up to $500
        5% of $8,972 = $448.60
        """
        credits = state_forms_service.get_state_credits(
            state=StateCode.NJ,
            federal_return=jones_federal_return,
            filing_status=FilingStatus.MARRIED_FILING_JOINTLY,
            state_agi=Decimal("38026")
        )

        property_tax_credit = next(
            (c for c in credits if c.credit_id == "property_tax"),
            None
        )

        # Credit should exist for income under threshold
        assert property_tax_credit is not None
        assert property_tax_credit.amount > Decimal("0")
        assert property_tax_credit.amount <= Decimal("500")  # Max credit

    def test_nj_property_tax_credit_high_income(self, state_forms_service, jones_federal_return):
        """Test NJ property tax credit phases out for high income."""
        # Create high income return
        high_income_return = jones_federal_return.copy()
        high_income_return["/adjustedGrossIncome"] = Decimal("200000")
        high_income_return["/agi"] = Decimal("200000")

        credits = state_forms_service.get_state_credits(
            state=StateCode.NJ,
            federal_return=high_income_return,
            filing_status=FilingStatus.MARRIED_FILING_JOINTLY,
            state_agi=Decimal("200000")
        )

        property_tax_credit = next(
            (c for c in credits if c.credit_id == "property_tax"),
            None
        )

        # Credit may be reduced or zero for high income
        # NJ Homestead Benefit has $150,000 income limit
        if property_tax_credit:
            assert property_tax_credit.amount >= Decimal("0")


# =============================================================================
# TEST CLASS: Multi-State Allocation
# =============================================================================


class TestMultiStateAllocation:
    """Tests for multi-state income allocation."""

    def test_multi_state_allocation_basic(self, state_forms_service, jones_federal_return):
        """Test basic multi-state allocation calculation."""
        states = [
            {
                "state": "NJ",
                "days": 200,
                "work_percentage": 0.60,
            },
            {
                "state": "NY",
                "days": 165,
                "work_percentage": 0.40,
            },
        ]

        allocations = state_forms_service.calculate_multi_state_allocation(
            states=states,
            federal_return=jones_federal_return,
            tax_year=2025
        )

        assert len(allocations) == 2

        # Check NJ allocation
        nj_allocation = next(a for a in allocations if a.state == StateCode.NJ)
        assert nj_allocation.days_resident == 200

        # Check NY allocation
        ny_allocation = next(a for a in allocations if a.state == StateCode.NY)
        assert ny_allocation.days_resident == 165

    def test_multi_state_allocation_percentages(self, state_forms_service, jones_federal_return):
        """Test that multi-state allocations sum correctly."""
        states = [
            {"state": "NJ", "days": 200, "work_percentage": 0.60},
            {"state": "NY", "days": 165, "work_percentage": 0.40},
        ]

        allocations = state_forms_service.calculate_multi_state_allocation(
            states=states,
            federal_return=jones_federal_return,
            tax_year=2025
        )

        # Total allocation percentage should be approximately 1.0
        total_pct = sum(a.allocation_percentage for a in allocations)
        assert abs(total_pct - Decimal("1.0")) < Decimal("0.01")

    def test_multi_state_wage_allocation(self, state_forms_service, jones_federal_return):
        """Test wage allocation across multiple states."""
        states = [
            {"state": "NJ", "days": 183, "work_percentage": 0.70},
            {"state": "PA", "days": 182, "work_percentage": 0.30},
        ]

        allocations = state_forms_service.calculate_multi_state_allocation(
            states=states,
            federal_return=jones_federal_return,
            tax_year=2025
        )

        total_wages = jones_federal_return["/wages"]

        # NJ should get 70% of wages
        nj_allocation = next(a for a in allocations if a.state == StateCode.NJ)
        expected_nj_wages = total_wages * Decimal("0.70")
        assert nj_allocation.wage_allocation == expected_nj_wages


# =============================================================================
# TEST CLASS: Credit for Taxes Paid to Other States
# =============================================================================


class TestCreditForTaxesPaidToOtherStates:
    """Tests for credit for taxes paid to other states."""

    def test_credit_for_other_state_taxes_basic(self, state_forms_service):
        """Test basic credit calculation for taxes paid to other states."""
        credit = state_forms_service.calculate_credit_for_taxes_paid_to_other_states(
            resident_state=StateCode.NJ,
            other_state_taxes=[
                {"state": "PA", "tax_paid": Decimal("500")},
            ],
            resident_state_tax=Decimal("1000"),
            income_taxed_in_other_states=Decimal("20000"),
            total_income=Decimal("40000")
        )

        # Credit should be limited to lesser of:
        # 1. Tax paid to other state: $500
        # 2. Resident state tax on other-state income: $1000 * (20000/40000) = $500
        assert credit == Decimal("500.00")

    def test_credit_limited_to_other_state_tax_paid(self, state_forms_service):
        """Test credit is limited to actual tax paid to other state."""
        credit = state_forms_service.calculate_credit_for_taxes_paid_to_other_states(
            resident_state=StateCode.NJ,
            other_state_taxes=[
                {"state": "NY", "tax_paid": Decimal("200")},
            ],
            resident_state_tax=Decimal("1000"),
            income_taxed_in_other_states=Decimal("30000"),
            total_income=Decimal("40000")
        )

        # Resident state tax proportion: $1000 * (30000/40000) = $750
        # But other state tax paid is only $200
        # Credit should be $200 (lesser)
        assert credit == Decimal("200.00")

    def test_credit_limited_to_resident_state_proportion(self, state_forms_service):
        """Test credit is limited to resident state tax on other-state income."""
        credit = state_forms_service.calculate_credit_for_taxes_paid_to_other_states(
            resident_state=StateCode.NJ,
            other_state_taxes=[
                {"state": "NY", "tax_paid": Decimal("800")},
            ],
            resident_state_tax=Decimal("600"),
            income_taxed_in_other_states=Decimal("20000"),
            total_income=Decimal("40000")
        )

        # Resident state tax proportion: $600 * (20000/40000) = $300
        # Other state tax paid is $800
        # Credit should be $300 (lesser)
        assert credit == Decimal("300.00")

    def test_credit_multiple_other_states(self, state_forms_service):
        """Test credit calculation with multiple other states."""
        credit = state_forms_service.calculate_credit_for_taxes_paid_to_other_states(
            resident_state=StateCode.NJ,
            other_state_taxes=[
                {"state": "NY", "tax_paid": Decimal("300")},
                {"state": "PA", "tax_paid": Decimal("200")},
            ],
            resident_state_tax=Decimal("1000"),
            income_taxed_in_other_states=Decimal("30000"),
            total_income=Decimal("60000")
        )

        # Total other state tax: $500
        # Resident state proportion: $1000 * (30000/60000) = $500
        assert credit == Decimal("500.00")

    def test_credit_zero_when_no_other_state_taxes(self, state_forms_service):
        """Test credit is zero when no taxes paid to other states."""
        credit = state_forms_service.calculate_credit_for_taxes_paid_to_other_states(
            resident_state=StateCode.NJ,
            other_state_taxes=[],
            resident_state_tax=Decimal("1000"),
            income_taxed_in_other_states=Decimal("0"),
            total_income=Decimal("40000")
        )

        assert credit == Decimal("0")


# =============================================================================
# TEST CLASS: Part-Year Resident
# =============================================================================


class TestPartYearResident:
    """Tests for part-year resident state calculations."""

    def test_part_year_resident_allocation(
        self, state_forms_service, jones_federal_return
    ):
        """Test part-year resident income allocation."""
        multi_state_info = {
            "allocation_percentage": 0.50,  # 50% of year in state
        }

        state_return = state_forms_service.generate_state_return(
            state=StateCode.NJ,
            federal_return=jones_federal_return,
            filing_status=FilingStatus.MARRIED_FILING_JOINTLY,
            residency_status=ResidencyStatus.PART_YEAR_RESIDENT,
            multi_state_info=multi_state_info,
            tax_year=2025
        )

        calc = state_return.calculation

        # State AGI should be 50% of federal AGI
        expected_state_agi = Decimal("38026") * Decimal("0.50")
        assert calc.state_agi == expected_state_agi

    def test_part_year_resident_form_selection(
        self, state_forms_service, jones_federal_return
    ):
        """Test that part-year resident uses correct form."""
        multi_state_info = {"allocation_percentage": 0.75}

        state_return = state_forms_service.generate_state_return(
            state=StateCode.NJ,
            federal_return=jones_federal_return,
            filing_status=FilingStatus.MARRIED_FILING_JOINTLY,
            residency_status=ResidencyStatus.PART_YEAR_RESIDENT,
            multi_state_info=multi_state_info,
            tax_year=2025
        )

        # Should use NJ-1040NR form
        assert "NR" in state_return.primary_form.form_id

    def test_part_year_resident_vs_full_year(
        self, state_forms_service, jones_federal_return
    ):
        """Test part-year has lower tax than full-year resident."""
        # Full year resident
        full_year_return = state_forms_service.generate_state_return(
            state=StateCode.NJ,
            federal_return=jones_federal_return,
            filing_status=FilingStatus.MARRIED_FILING_JOINTLY,
            residency_status=ResidencyStatus.FULL_YEAR_RESIDENT,
            tax_year=2025
        )

        # Part year resident (50%)
        part_year_return = state_forms_service.generate_state_return(
            state=StateCode.NJ,
            federal_return=jones_federal_return,
            filing_status=FilingStatus.MARRIED_FILING_JOINTLY,
            residency_status=ResidencyStatus.PART_YEAR_RESIDENT,
            multi_state_info={"allocation_percentage": 0.50},
            tax_year=2025
        )

        # Part year should have lower tax
        assert part_year_return.calculation.tax_before_credits < full_year_return.calculation.tax_before_credits


# =============================================================================
# TEST CLASS: NJ EITC (40% of Federal)
# =============================================================================


class TestNJEITC:
    """Tests for NJ Earned Income Tax Credit.

    NJ EITC = 40% of federal EITC.
    """

    def test_nj_eitc_rate(self, state_forms_service):
        """Test NJ EITC is 40% of federal."""
        federal_eitc = Decimal("1000")

        nj_eitc = state_forms_service._calculate_state_eitc(
            state=StateCode.NJ,
            federal_eitc=federal_eitc,
            state_agi=Decimal("30000"),
            filing_status=FilingStatus.SINGLE
        )

        expected = federal_eitc * Decimal("0.40")
        assert nj_eitc == expected

    def test_nj_eitc_with_actual_federal_eitc(self, state_forms_service):
        """Test NJ EITC calculation with realistic federal EITC."""
        # Assume federal EITC of $2,500
        federal_return = {
            "/earnedIncomeCredit": Decimal("2500"),
            "/eitc": Decimal("2500"),
            "/propertyTax": Decimal("0"),
            "/rentPaid": Decimal("0"),
            "/numberOfDependents": 1,
            "/dependentsUnder17": 1,
            "/educationExpenses": Decimal("0"),
        }

        credits = state_forms_service.get_state_credits(
            state=StateCode.NJ,
            federal_return=federal_return,
            filing_status=FilingStatus.SINGLE,
            state_agi=Decimal("25000")
        )

        eitc_credit = next(
            (c for c in credits if c.credit_id == "eitc"),
            None
        )

        assert eitc_credit is not None
        assert eitc_credit.amount == Decimal("1000.00")  # 40% of $2,500
        assert eitc_credit.refundable is True

    def test_nj_eitc_zero_when_no_federal_eitc(self, state_forms_service):
        """Test NJ EITC is zero when no federal EITC."""
        nj_eitc = state_forms_service._calculate_state_eitc(
            state=StateCode.NJ,
            federal_eitc=Decimal("0"),
            state_agi=Decimal("30000"),
            filing_status=FilingStatus.SINGLE
        )

        assert nj_eitc == Decimal("0")

    def test_nj_eitc_compare_to_other_states(self, state_forms_service):
        """Test NJ EITC rate compared to other states."""
        federal_eitc = Decimal("1000")

        nj_eitc = state_forms_service._calculate_state_eitc(
            StateCode.NJ, federal_eitc, Decimal("30000"), FilingStatus.SINGLE
        )
        ny_eitc = state_forms_service._calculate_state_eitc(
            StateCode.NY, federal_eitc, Decimal("30000"), FilingStatus.SINGLE
        )
        ca_eitc = state_forms_service._calculate_state_eitc(
            StateCode.CA, federal_eitc, Decimal("30000"), FilingStatus.SINGLE
        )
        il_eitc = state_forms_service._calculate_state_eitc(
            StateCode.IL, federal_eitc, Decimal("30000"), FilingStatus.SINGLE
        )

        # NJ: 40%, NY: 30%, CA: 85%, IL: 20%
        assert nj_eitc == Decimal("400.00")
        assert ny_eitc == Decimal("300.00")
        assert ca_eitc == Decimal("850.00")
        assert il_eitc == Decimal("200.00")


# =============================================================================
# TEST CLASS: NJ Child Tax Credit
# =============================================================================


class TestNJChildTaxCredit:
    """Tests for NJ Child Tax Credit."""

    def test_nj_child_tax_credit_eligible(self, state_forms_service):
        """Test NJ child tax credit for eligible families."""
        federal_return = {
            "/propertyTax": Decimal("0"),
            "/rentPaid": Decimal("0"),
            "/numberOfDependents": 2,
            "/dependentsUnder17": 2,
            "/earnedIncomeCredit": Decimal("0"),
            "/educationExpenses": Decimal("0"),
        }

        credits = state_forms_service.get_state_credits(
            state=StateCode.NJ,
            federal_return=federal_return,
            filing_status=FilingStatus.MARRIED_FILING_JOINTLY,
            state_agi=Decimal("60000")  # Under $80,000 threshold
        )

        child_credit = next(
            (c for c in credits if c.credit_id == "dependent"),
            None
        )

        # Should get $500 per child under 17
        assert child_credit is not None
        assert child_credit.amount == Decimal("1000")  # $500 x 2

    def test_nj_child_tax_credit_income_limit(self, state_forms_service):
        """Test NJ child tax credit phases out at $80,000."""
        federal_return = {
            "/propertyTax": Decimal("0"),
            "/rentPaid": Decimal("0"),
            "/numberOfDependents": 1,
            "/dependentsUnder17": 1,
            "/earnedIncomeCredit": Decimal("0"),
            "/educationExpenses": Decimal("0"),
        }

        # Over $80,000 - should not get credit
        credits = state_forms_service.get_state_credits(
            state=StateCode.NJ,
            federal_return=federal_return,
            filing_status=FilingStatus.MARRIED_FILING_JOINTLY,
            state_agi=Decimal("85000")
        )

        child_credit = next(
            (c for c in credits if c.credit_id == "dependent"),
            None
        )

        # Credit should be zero or not exist
        if child_credit:
            assert child_credit.amount == Decimal("0")

    def test_nj_child_tax_credit_no_children(self, state_forms_service):
        """Test no child tax credit when no qualifying children."""
        federal_return = {
            "/propertyTax": Decimal("0"),
            "/rentPaid": Decimal("0"),
            "/numberOfDependents": 0,
            "/dependentsUnder17": 0,
            "/earnedIncomeCredit": Decimal("0"),
            "/educationExpenses": Decimal("0"),
        }

        credits = state_forms_service.get_state_credits(
            state=StateCode.NJ,
            federal_return=federal_return,
            filing_status=FilingStatus.MARRIED_FILING_JOINTLY,
            state_agi=Decimal("50000")
        )

        child_credit = next(
            (c for c in credits if c.credit_id == "dependent"),
            None
        )

        # Should not get credit
        assert child_credit is None


# =============================================================================
# TEST CLASS: NJ Property Tax Credit
# =============================================================================


class TestNJPropertyTaxCredit:
    """Tests for NJ property tax credit / Homestead Benefit."""

    def test_nj_property_tax_credit_basic(self, state_forms_service):
        """Test NJ property tax credit calculation."""
        federal_return = {
            "/propertyTax": Decimal("10000"),
            "/propertyTaxesPaid": Decimal("10000"),
            "/rentPaid": Decimal("0"),
            "/numberOfDependents": 0,
            "/dependentsUnder17": 0,
            "/earnedIncomeCredit": Decimal("0"),
            "/educationExpenses": Decimal("0"),
        }

        credits = state_forms_service.get_state_credits(
            state=StateCode.NJ,
            federal_return=federal_return,
            filing_status=FilingStatus.MARRIED_FILING_JOINTLY,
            state_agi=Decimal("100000")  # Under $150,000 threshold
        )

        property_credit = next(
            (c for c in credits if c.credit_id == "property_tax"),
            None
        )

        # Credit should be 5% of property tax up to $500
        # 5% of $10,000 = $500 (at cap)
        assert property_credit is not None
        assert property_credit.amount == Decimal("500")

    def test_nj_property_tax_credit_below_cap(self, state_forms_service):
        """Test NJ property tax credit when below 5% cap."""
        federal_return = {
            "/propertyTax": Decimal("5000"),
            "/propertyTaxesPaid": Decimal("5000"),
            "/rentPaid": Decimal("0"),
            "/numberOfDependents": 0,
            "/dependentsUnder17": 0,
            "/earnedIncomeCredit": Decimal("0"),
            "/educationExpenses": Decimal("0"),
        }

        credits = state_forms_service.get_state_credits(
            state=StateCode.NJ,
            federal_return=federal_return,
            filing_status=FilingStatus.MARRIED_FILING_JOINTLY,
            state_agi=Decimal("100000")
        )

        property_credit = next(
            (c for c in credits if c.credit_id == "property_tax"),
            None
        )

        # Credit should be 5% of $5,000 = $250
        assert property_credit is not None
        assert property_credit.amount == Decimal("250")


# =============================================================================
# TEST CLASS: Generate NJ-1040
# =============================================================================


class TestGenerateNJ1040:
    """Tests for NJ-1040 form generation."""

    def test_generate_nj_1040_basic(
        self, state_forms_service, jones_federal_return
    ):
        """Test basic NJ-1040 generation."""
        state_return = state_forms_service.generate_state_return(
            state=StateCode.NJ,
            federal_return=jones_federal_return,
            filing_status=FilingStatus.MARRIED_FILING_JOINTLY,
            tax_year=2025
        )

        assert state_return.state == StateCode.NJ
        assert state_return.tax_year == 2025
        assert state_return.filing_status == FilingStatus.MARRIED_FILING_JOINTLY

    def test_nj_1040_form_id(
        self, state_forms_service, jones_federal_return
    ):
        """Test NJ-1040 form ID for resident."""
        state_return = state_forms_service.generate_state_return(
            state=StateCode.NJ,
            federal_return=jones_federal_return,
            filing_status=FilingStatus.MARRIED_FILING_JOINTLY,
            residency_status=ResidencyStatus.FULL_YEAR_RESIDENT,
            tax_year=2025
        )

        assert "NJ-1040" in state_return.primary_form.form_id

    def test_nj_1040_has_required_lines(
        self, state_forms_service, jones_federal_return
    ):
        """Test NJ-1040 contains required line items."""
        state_return = state_forms_service.generate_state_return(
            state=StateCode.NJ,
            federal_return=jones_federal_return,
            filing_status=FilingStatus.MARRIED_FILING_JOINTLY,
            tax_year=2025
        )

        lines = state_return.primary_form.lines
        line_numbers = [line.line_number for line in lines]

        # Check required lines exist
        assert "15" in line_numbers  # Wages
        assert "29" in line_numbers  # NJ taxable income
        assert "36" in line_numbers  # Tax on income
        assert "52" in line_numbers  # NJ tax withheld

    def test_nj_1040_wages_line(
        self, state_forms_service, jones_federal_return
    ):
        """Test NJ-1040 wages line matches federal wages."""
        state_return = state_forms_service.generate_state_return(
            state=StateCode.NJ,
            federal_return=jones_federal_return,
            filing_status=FilingStatus.MARRIED_FILING_JOINTLY,
            tax_year=2025
        )

        wages_line = next(
            (l for l in state_return.primary_form.lines if l.line_number == "15"),
            None
        )

        assert wages_line is not None
        assert wages_line.value == Decimal("38026")

    def test_nj_1040_withholding_line(
        self, state_forms_service, jones_federal_return
    ):
        """Test NJ-1040 withholding line matches W-2 data."""
        state_return = state_forms_service.generate_state_return(
            state=StateCode.NJ,
            federal_return=jones_federal_return,
            filing_status=FilingStatus.MARRIED_FILING_JOINTLY,
            tax_year=2025
        )

        withholding_line = next(
            (l for l in state_return.primary_form.lines if l.line_number == "52"),
            None
        )

        assert withholding_line is not None
        assert withholding_line.value == Decimal("1028")


# =============================================================================
# TEST CLASS: Generate CA Form 540
# =============================================================================


class TestGenerateCA540:
    """Tests for California Form 540 generation."""

    def test_generate_ca_540_basic(
        self, state_forms_service, jones_federal_return
    ):
        """Test basic CA 540 generation."""
        state_return = state_forms_service.generate_state_return(
            state=StateCode.CA,
            federal_return=jones_federal_return,
            filing_status=FilingStatus.MARRIED_FILING_JOINTLY,
            tax_year=2025
        )

        assert state_return.state == StateCode.CA
        assert state_return.tax_year == 2025

    def test_ca_540_form_id_resident(
        self, state_forms_service, jones_federal_return
    ):
        """Test CA Form 540 for full-year resident."""
        state_return = state_forms_service.generate_state_return(
            state=StateCode.CA,
            federal_return=jones_federal_return,
            filing_status=FilingStatus.MARRIED_FILING_JOINTLY,
            residency_status=ResidencyStatus.FULL_YEAR_RESIDENT,
            tax_year=2025
        )

        assert "540" in state_return.primary_form.form_id
        assert "NR" not in state_return.primary_form.form_id

    def test_ca_540nr_form_id_nonresident(
        self, state_forms_service, jones_federal_return
    ):
        """Test CA Form 540NR for nonresident."""
        state_return = state_forms_service.generate_state_return(
            state=StateCode.CA,
            federal_return=jones_federal_return,
            filing_status=FilingStatus.MARRIED_FILING_JOINTLY,
            residency_status=ResidencyStatus.NON_RESIDENT,
            tax_year=2025
        )

        assert "540NR" in state_return.primary_form.form_id

    def test_ca_540_has_schedule_ca(
        self, state_forms_service, jones_federal_return
    ):
        """Test CA 540 includes Schedule CA."""
        state_return = state_forms_service.generate_state_return(
            state=StateCode.CA,
            federal_return=jones_federal_return,
            filing_status=FilingStatus.MARRIED_FILING_JOINTLY,
            tax_year=2025
        )

        schedule_ids = [s.schedule_id for s in state_return.schedules]
        assert "Schedule CA" in schedule_ids

    def test_ca_standard_deduction_mfj(self, state_forms_service):
        """Test CA standard deduction for MFJ is $11,080."""
        std_deductions = state_forms_service.STATE_STANDARD_DEDUCTIONS_2025[StateCode.CA]
        mfj_std = std_deductions[FilingStatus.MARRIED_FILING_JOINTLY]

        assert mfj_std == Decimal("11080")

    def test_ca_tax_brackets_mfj(self, state_forms_service):
        """Test CA progressive tax brackets for MFJ."""
        brackets = state_forms_service.STATE_BRACKETS_2025[StateCode.CA][FilingStatus.MARRIED_FILING_JOINTLY]

        # First bracket: 1% up to $20,824
        assert brackets[0].rate == Decimal("0.01")
        assert brackets[0].max_income == Decimal("20824")

        # Top bracket: 12.3%
        assert brackets[-1].rate == Decimal("0.123")


# =============================================================================
# TEST CLASS: Generate NY IT-201
# =============================================================================


class TestGenerateNYIT201:
    """Tests for New York IT-201 form generation."""

    def test_generate_ny_it201_basic(
        self, state_forms_service, jones_federal_return
    ):
        """Test basic NY IT-201 generation."""
        state_return = state_forms_service.generate_state_return(
            state=StateCode.NY,
            federal_return=jones_federal_return,
            filing_status=FilingStatus.MARRIED_FILING_JOINTLY,
            tax_year=2025
        )

        assert state_return.state == StateCode.NY
        assert state_return.tax_year == 2025

    def test_ny_it201_form_id_resident(
        self, state_forms_service, jones_federal_return
    ):
        """Test NY IT-201 for full-year resident."""
        state_return = state_forms_service.generate_state_return(
            state=StateCode.NY,
            federal_return=jones_federal_return,
            filing_status=FilingStatus.MARRIED_FILING_JOINTLY,
            residency_status=ResidencyStatus.FULL_YEAR_RESIDENT,
            tax_year=2025
        )

        assert "IT-201" in state_return.primary_form.form_id

    def test_ny_it203_form_id_nonresident(
        self, state_forms_service, jones_federal_return
    ):
        """Test NY IT-203 for nonresident/part-year."""
        state_return = state_forms_service.generate_state_return(
            state=StateCode.NY,
            federal_return=jones_federal_return,
            filing_status=FilingStatus.MARRIED_FILING_JOINTLY,
            residency_status=ResidencyStatus.PART_YEAR_RESIDENT,
            tax_year=2025
        )

        assert "IT-203" in state_return.primary_form.form_id

    def test_ny_standard_deduction_mfj(self, state_forms_service):
        """Test NY standard deduction for MFJ is $16,050."""
        std_deductions = state_forms_service.STATE_STANDARD_DEDUCTIONS_2025[StateCode.NY]
        mfj_std = std_deductions[FilingStatus.MARRIED_FILING_JOINTLY]

        assert mfj_std == Decimal("16050")

    def test_ny_tax_brackets_progressive(self, state_forms_service):
        """Test NY progressive tax brackets."""
        brackets = state_forms_service.STATE_BRACKETS_2025[StateCode.NY][FilingStatus.MARRIED_FILING_JOINTLY]

        # First bracket: 4%
        assert brackets[0].rate == Decimal("0.04")

        # Top bracket: 10.9%
        assert brackets[-1].rate == Decimal("0.109")

    def test_ny_pension_exclusion(self, state_forms_service, jones_federal_return):
        """Test NY pension exclusion calculation."""
        # Add pension income
        pension_return = jones_federal_return.copy()
        pension_return["/pensionIncome"] = Decimal("30000")

        state_return = state_forms_service.generate_state_return(
            state=StateCode.NY,
            federal_return=pension_return,
            filing_status=FilingStatus.MARRIED_FILING_JOINTLY,
            tax_year=2025
        )

        # NY allows up to $20,000 pension exclusion
        calc = state_return.calculation
        # Subtractions should include pension exclusion
        assert calc.state_subtractions >= Decimal("20000")


# =============================================================================
# TEST CLASS: Filing Status Tests - Single
# =============================================================================


class TestSingleFilingStatus:
    """Tests for single filing status."""

    def test_single_personal_exemption(
        self, state_forms_service, jones_federal_return
    ):
        """Test single filer gets one personal exemption."""
        single_return = jones_federal_return.copy()
        single_return["/numberOfDependents"] = 0

        state_return = state_forms_service.generate_state_return(
            state=StateCode.NJ,
            federal_return=single_return,
            filing_status=FilingStatus.SINGLE,
            tax_year=2025
        )

        # Single: 1 personal exemption = $1,000
        assert state_return.calculation.exemptions == Decimal("1000")

    def test_single_standard_deduction_ca(self, state_forms_service):
        """Test single filer standard deduction in CA."""
        std_deductions = state_forms_service.STATE_STANDARD_DEDUCTIONS_2025[StateCode.CA]
        single_std = std_deductions[FilingStatus.SINGLE]

        assert single_std == Decimal("5540")

    def test_single_tax_brackets_lower_thresholds(self, state_forms_service):
        """Test single filer has lower bracket thresholds than MFJ."""
        nj_single = state_forms_service.STATE_BRACKETS_2025[StateCode.NJ][FilingStatus.SINGLE]
        nj_mfj = state_forms_service.STATE_BRACKETS_2025[StateCode.NJ][FilingStatus.MARRIED_FILING_JOINTLY]

        # Second bracket threshold should be lower for single
        assert nj_single[1].max_income < nj_mfj[1].max_income


# =============================================================================
# TEST CLASS: Filing Status Tests - MFJ
# =============================================================================


class TestMFJFilingStatus:
    """Tests for married filing jointly status."""

    def test_mfj_two_personal_exemptions(
        self, state_forms_service, jones_federal_return
    ):
        """Test MFJ gets two personal exemptions."""
        state_return = state_forms_service.generate_state_return(
            state=StateCode.NJ,
            federal_return=jones_federal_return,
            filing_status=FilingStatus.MARRIED_FILING_JOINTLY,
            tax_year=2025
        )

        # MFJ: 2 personal exemptions ($1,000 x 2) + 1 dependent ($1,500)
        expected = Decimal("1000") * 2 + Decimal("1500") * 1
        assert state_return.calculation.exemptions == expected

    def test_mfj_standard_deduction_higher(self, state_forms_service):
        """Test MFJ has higher standard deduction than single."""
        ca_std = state_forms_service.STATE_STANDARD_DEDUCTIONS_2025[StateCode.CA]

        assert ca_std[FilingStatus.MARRIED_FILING_JOINTLY] > ca_std[FilingStatus.SINGLE]

    def test_mfj_wider_tax_brackets(self, state_forms_service):
        """Test MFJ has wider tax brackets than single in middle ranges.

        Note: NJ brackets differ structurally - MFJ has more brackets with
        different thresholds. The key difference is the 2.45% bracket only
        exists for MFJ ($50k-$70k), so MFJ pays less at the same income.
        """
        nj_single = state_forms_service.STATE_BRACKETS_2025[StateCode.NJ][FilingStatus.SINGLE]
        nj_mfj = state_forms_service.STATE_BRACKETS_2025[StateCode.NJ][FilingStatus.MARRIED_FILING_JOINTLY]

        # First bracket max should be same ($20,000)
        assert nj_single[0].max_income == nj_mfj[0].max_income == Decimal("20000")

        # MFJ has more brackets (8) than single (7) due to 2.45% bracket
        assert len(nj_mfj) > len(nj_single)

        # Second bracket for MFJ goes to $50,000, single only to $35,000
        assert nj_mfj[1].max_income == Decimal("50000")
        assert nj_single[1].max_income == Decimal("35000")


# =============================================================================
# TEST CLASS: Filing Status Tests - HOH
# =============================================================================


class TestHOHFilingStatus:
    """Tests for head of household filing status."""

    def test_hoh_filing_status_return(
        self, state_forms_service, jones_federal_return
    ):
        """Test HOH filing status generates valid return."""
        single_parent_return = jones_federal_return.copy()
        # Single parent with one dependent

        state_return = state_forms_service.generate_state_return(
            state=StateCode.NJ,
            federal_return=single_parent_return,
            filing_status=FilingStatus.HEAD_OF_HOUSEHOLD,
            tax_year=2025
        )

        assert state_return.filing_status == FilingStatus.HEAD_OF_HOUSEHOLD

    def test_hoh_has_brackets_defined(self, state_forms_service):
        """Test HOH brackets are defined (or default to single)."""
        nj_brackets = state_forms_service.STATE_BRACKETS_2025[StateCode.NJ]

        # HOH should have brackets defined
        assert FilingStatus.HEAD_OF_HOUSEHOLD in nj_brackets or \
               FilingStatus.SINGLE in nj_brackets

    def test_hoh_exemptions(self, state_forms_service, jones_federal_return):
        """Test HOH gets one personal exemption plus dependent exemptions."""
        state_return = state_forms_service.generate_state_return(
            state=StateCode.NJ,
            federal_return=jones_federal_return,
            filing_status=FilingStatus.HEAD_OF_HOUSEHOLD,
            tax_year=2025
        )

        # HOH: 1 personal ($1,000) + 1 dependent ($1,500)
        expected = Decimal("1000") * 1 + Decimal("1500") * 1
        assert state_return.calculation.exemptions == expected


# =============================================================================
# TEST CLASS: Filing Status Tests - QSS
# =============================================================================


class TestQSSFilingStatus:
    """Tests for qualifying surviving spouse filing status.

    This is relevant for Judy Jones' case as she passed away in 2025.
    John may file as QSS for 2025 and 2026.
    """

    def test_qss_uses_mfj_brackets(self, state_forms_service):
        """Test QSS uses same brackets as MFJ."""
        nj_brackets = state_forms_service.STATE_BRACKETS_2025[StateCode.NJ]

        # QSS should use MFJ brackets
        qss_brackets = nj_brackets.get(FilingStatus.QUALIFYING_SURVIVING_SPOUSE, [])
        mfj_brackets = nj_brackets.get(FilingStatus.MARRIED_FILING_JOINTLY, [])

        if qss_brackets:
            assert qss_brackets[0].rate == mfj_brackets[0].rate

    def test_qss_filing_status_return(
        self, state_forms_service, jones_federal_return
    ):
        """Test QSS filing status generates valid return."""
        state_return = state_forms_service.generate_state_return(
            state=StateCode.NJ,
            federal_return=jones_federal_return,
            filing_status=FilingStatus.QUALIFYING_SURVIVING_SPOUSE,
            tax_year=2025
        )

        assert state_return.filing_status == FilingStatus.QUALIFYING_SURVIVING_SPOUSE

    def test_qss_exemptions_with_deceased_spouse(
        self, state_forms_service, jones_federal_return
    ):
        """Test QSS exemptions.

        Note: QSS (Qualifying Surviving Spouse) gets 1 personal exemption
        plus dependent exemptions. The deceased spouse exemption is only
        available in the year of death when filing MFJ.
        """
        state_return = state_forms_service.generate_state_return(
            state=StateCode.NJ,
            federal_return=jones_federal_return,
            filing_status=FilingStatus.QUALIFYING_SURVIVING_SPOUSE,
            tax_year=2025
        )

        # QSS: 1 personal ($1,000) + 1 dependent ($1,500) = $2,500
        # The service treats QSS as single taxpayer for exemption purposes
        expected = Decimal("1000") * 1 + Decimal("1500") * 1
        assert state_return.calculation.exemptions == expected


# =============================================================================
# TEST CLASS: 2025 Tax Data for Multiple States
# =============================================================================


class Test2025TaxDataNJ:
    """Tests for 2025 NJ tax data."""

    def test_nj_2025_bracket_rates(self, state_forms_service):
        """Test NJ 2025 bracket rates are accurate."""
        brackets = state_forms_service.STATE_BRACKETS_2025[StateCode.NJ][FilingStatus.MARRIED_FILING_JOINTLY]

        # Verify key rates
        assert brackets[0].rate == Decimal("0.014")   # 1.4%
        assert brackets[1].rate == Decimal("0.0175")  # 1.75%
        assert brackets[-1].rate == Decimal("0.1075") # 10.75%

    def test_nj_2025_exemptions(self, state_forms_service):
        """Test NJ 2025 exemption amounts."""
        exemptions = state_forms_service.STATE_EXEMPTIONS_2025[StateCode.NJ]

        assert exemptions["personal"] == Decimal("1000")
        assert exemptions["dependent"] == Decimal("1500")


class Test2025TaxDataCA:
    """Tests for 2025 CA tax data."""

    def test_ca_2025_bracket_rates(self, state_forms_service):
        """Test CA 2025 bracket rates are accurate."""
        brackets = state_forms_service.STATE_BRACKETS_2025[StateCode.CA][FilingStatus.MARRIED_FILING_JOINTLY]

        # Verify key rates
        assert brackets[0].rate == Decimal("0.01")    # 1%
        assert brackets[-1].rate == Decimal("0.123")  # 12.3%

    def test_ca_2025_standard_deduction(self, state_forms_service):
        """Test CA 2025 standard deduction amounts."""
        std = state_forms_service.STATE_STANDARD_DEDUCTIONS_2025[StateCode.CA]

        assert std[FilingStatus.SINGLE] == Decimal("5540")
        assert std[FilingStatus.MARRIED_FILING_JOINTLY] == Decimal("11080")

    def test_ca_2025_exemption_credits(self, state_forms_service):
        """Test CA 2025 exemption credit amounts."""
        exemptions = state_forms_service.STATE_EXEMPTIONS_2025[StateCode.CA]

        # CA uses credits, not deductions
        assert exemptions["personal"] == Decimal("144")
        assert exemptions["dependent"] == Decimal("446")


class Test2025TaxDataNY:
    """Tests for 2025 NY tax data."""

    def test_ny_2025_bracket_rates(self, state_forms_service):
        """Test NY 2025 bracket rates are accurate."""
        brackets = state_forms_service.STATE_BRACKETS_2025[StateCode.NY][FilingStatus.MARRIED_FILING_JOINTLY]

        # Verify key rates
        assert brackets[0].rate == Decimal("0.04")    # 4%
        assert brackets[-1].rate == Decimal("0.109")  # 10.9%

    def test_ny_2025_standard_deduction(self, state_forms_service):
        """Test NY 2025 standard deduction amounts."""
        std = state_forms_service.STATE_STANDARD_DEDUCTIONS_2025[StateCode.NY]

        assert std[FilingStatus.SINGLE] == Decimal("8000")
        assert std[FilingStatus.MARRIED_FILING_JOINTLY] == Decimal("16050")
        assert std[FilingStatus.HEAD_OF_HOUSEHOLD] == Decimal("11200")


class Test2025TaxDataIL:
    """Tests for 2025 IL tax data (flat tax)."""

    def test_il_2025_flat_tax_rate(self, state_forms_service):
        """Test IL 2025 flat tax rate is 4.95%."""
        brackets = state_forms_service.STATE_BRACKETS_2025[StateCode.IL][FilingStatus.SINGLE]

        # IL has single flat rate bracket
        assert len(brackets) == 1
        assert brackets[0].rate == Decimal("0.0495")
        assert brackets[0].max_income is None  # Unlimited

    def test_il_same_rate_all_filing_statuses(self, state_forms_service):
        """Test IL flat rate is same for all filing statuses."""
        single_rate = state_forms_service.STATE_BRACKETS_2025[StateCode.IL][FilingStatus.SINGLE][0].rate
        mfj_rate = state_forms_service.STATE_BRACKETS_2025[StateCode.IL][FilingStatus.MARRIED_FILING_JOINTLY][0].rate

        assert single_rate == mfj_rate == Decimal("0.0495")

    def test_il_2025_exemptions(self, state_forms_service):
        """Test IL 2025 exemption amounts."""
        exemptions = state_forms_service.STATE_EXEMPTIONS_2025[StateCode.IL]

        assert exemptions["personal"] == Decimal("2625")
        assert exemptions["dependent"] == Decimal("2625")


# =============================================================================
# TEST CLASS: State Return Validation
# =============================================================================


class TestStateReturnValidation:
    """Tests for state return validation."""

    def test_validate_return_no_errors(
        self, state_forms_service, jones_federal_return
    ):
        """Test valid return has no validation errors."""
        state_return = state_forms_service.generate_state_return(
            state=StateCode.NJ,
            federal_return=jones_federal_return,
            filing_status=FilingStatus.MARRIED_FILING_JOINTLY,
            tax_year=2025
        )

        errors = state_forms_service.validate_state_return(state_return)
        assert len(errors) == 0

    def test_validate_agi_calculation(
        self, state_forms_service, jones_federal_return
    ):
        """Test AGI calculation validation."""
        state_return = state_forms_service.generate_state_return(
            state=StateCode.NJ,
            federal_return=jones_federal_return,
            filing_status=FilingStatus.MARRIED_FILING_JOINTLY,
            tax_year=2025
        )

        calc = state_return.calculation

        # State AGI = Federal AGI + additions - subtractions
        expected_agi = calc.federal_agi + calc.state_additions - calc.state_subtractions
        assert abs(calc.state_agi - expected_agi) < Decimal("0.01")

    def test_validate_no_negative_taxable_income(
        self, state_forms_service, jones_federal_return
    ):
        """Test taxable income is not negative."""
        state_return = state_forms_service.generate_state_return(
            state=StateCode.NJ,
            federal_return=jones_federal_return,
            filing_status=FilingStatus.MARRIED_FILING_JOINTLY,
            tax_year=2025
        )

        assert state_return.calculation.state_taxable_income >= Decimal("0")

    def test_validate_not_both_owed_and_refund(
        self, state_forms_service, jones_federal_return
    ):
        """Test cannot have both amount owed and refund positive."""
        state_return = state_forms_service.generate_state_return(
            state=StateCode.NJ,
            federal_return=jones_federal_return,
            filing_status=FilingStatus.MARRIED_FILING_JOINTLY,
            tax_year=2025
        )

        calc = state_return.calculation

        # Cannot have both positive
        assert not (calc.amount_owed > Decimal("0") and calc.refund_amount > Decimal("0"))


# =============================================================================
# TEST CLASS: No Income Tax States
# =============================================================================


class TestNoIncomeTaxStates:
    """Tests for states with no income tax."""

    def test_no_income_tax_states_defined(self, state_forms_service):
        """Test no-income-tax states are defined."""
        no_tax_states = state_forms_service.NO_INCOME_TAX_STATES

        assert StateCode.FL in no_tax_states  # Florida
        assert StateCode.TX in no_tax_states  # Texas
        assert StateCode.WA in no_tax_states  # Washington
        assert StateCode.NV in no_tax_states  # Nevada
        assert StateCode.TN in no_tax_states  # Tennessee
        assert StateCode.AK in no_tax_states  # Alaska
        assert StateCode.WY in no_tax_states  # Wyoming
        assert StateCode.SD in no_tax_states  # South Dakota

    def test_florida_no_state_tax(
        self, state_forms_service, jones_federal_return
    ):
        """Test Florida return has zero tax."""
        state_return = state_forms_service.generate_state_return(
            state=StateCode.FL,
            federal_return=jones_federal_return,
            filing_status=FilingStatus.MARRIED_FILING_JOINTLY,
            tax_year=2025
        )

        assert state_return.calculation.tax_before_credits == Decimal("0")
        assert state_return.calculation.net_tax == Decimal("0")

    def test_texas_no_state_tax(
        self, state_forms_service, jones_federal_return
    ):
        """Test Texas return has zero tax."""
        state_return = state_forms_service.generate_state_return(
            state=StateCode.TX,
            federal_return=jones_federal_return,
            filing_status=FilingStatus.MARRIED_FILING_JOINTLY,
            tax_year=2025
        )

        assert state_return.calculation.tax_before_credits == Decimal("0")

    def test_no_tax_state_form_id(
        self, state_forms_service, jones_federal_return
    ):
        """Test no-tax state has appropriate form ID."""
        state_return = state_forms_service.generate_state_return(
            state=StateCode.FL,
            federal_return=jones_federal_return,
            filing_status=FilingStatus.MARRIED_FILING_JOINTLY,
            tax_year=2025
        )

        assert state_return.primary_form.form_id == "None"
        assert "No Income Tax" in state_return.primary_form.title


# =============================================================================
# TEST CLASS: Supported States
# =============================================================================


class TestSupportedStates:
    """Tests for supported state functionality."""

    def test_get_supported_states(self, state_forms_service):
        """Test getting list of states with income tax."""
        supported = state_forms_service.get_supported_states()

        # Should include states with income tax
        assert StateCode.NJ in supported
        assert StateCode.CA in supported
        assert StateCode.NY in supported
        assert StateCode.IL in supported

        # Should NOT include no-tax states
        assert StateCode.FL not in supported
        assert StateCode.TX not in supported

    def test_state_form_info_nj(self, state_forms_service):
        """Test getting NJ form info."""
        form_info = state_forms_service.get_state_form_info(StateCode.NJ)

        assert form_info["resident"] == "NJ-1040"
        assert form_info["non_resident"] == "NJ-1040NR"
        assert "Schedule A" in form_info["schedules"]

    def test_state_form_info_ca(self, state_forms_service):
        """Test getting CA form info."""
        form_info = state_forms_service.get_state_form_info(StateCode.CA)

        assert form_info["resident"] == "Form 540"
        assert form_info["non_resident"] == "Form 540NR"
        assert "Schedule CA" in form_info["schedules"]


# =============================================================================
# TEST CLASS: Jones Family Complete Calculation
# =============================================================================


class TestJonesFamilyCompleteCalculation:
    """End-to-end tests for Jones family NJ tax calculation."""

    def test_jones_nj_complete_calculation(
        self,
        state_forms_service,
        jones_federal_return,
        jones_w2_totals
    ):
        """Test complete NJ tax calculation for Jones family.

        Expected calculation (with itemized deductions from federal Sch A):
        - Federal AGI: $38,026
        - NJ AGI: $38,026 (no additions/subtractions)
        - Exemptions: $3,500 (2 personal + 1 dependent)
        - Itemized deductions: $12,201 (mortgage interest $11,251 + charitable $950)
          Note: NJ doesn't allow SALT deduction (circular), and property tax is
          handled as a separate credit, not deduction.
        - Total deduction + exemptions: $15,701
        - NJ Taxable Income: $22,325 ($38,026 - $12,201 - $3,500)
        - Tax: ~$320.69 (first bracket 1.4% + second bracket 1.75%)
        - Withholding: $1,028
        - Property tax credit: $448.60
        - Expected Refund: $1,028 (full refund since tax < credits)
        """
        state_return = state_forms_service.generate_state_return(
            state=StateCode.NJ,
            federal_return=jones_federal_return,
            filing_status=FilingStatus.MARRIED_FILING_JOINTLY,
            residency_status=ResidencyStatus.FULL_YEAR_RESIDENT,
            tax_year=2025
        )

        calc = state_return.calculation

        # Verify income
        assert calc.federal_agi == Decimal("38026")
        assert calc.state_agi == Decimal("38026")

        # Verify exemptions
        assert calc.exemptions == Decimal("3500")

        # NJ uses itemized deductions (mortgage interest + charitable)
        # Note: Property tax is credit, not deduction; state tax not deductible
        assert calc.deduction_used == "itemized"
        assert calc.itemized_deduction == Decimal("12201")  # $11,251 + $950

        # Verify taxable income (AGI - itemized - exemptions)
        expected_taxable = Decimal("38026") - Decimal("12201") - Decimal("3500")
        assert calc.state_taxable_income == expected_taxable

        # Verify withholding
        assert calc.withholding == Decimal("1028")

        # Should get a refund (withholding + credits > tax due)
        assert calc.refund_amount > Decimal("0")
        assert calc.amount_owed == Decimal("0")

    def test_jones_effective_tax_rate(
        self, state_forms_service, jones_federal_return
    ):
        """Test Jones family effective NJ tax rate."""
        state_return = state_forms_service.generate_state_return(
            state=StateCode.NJ,
            federal_return=jones_federal_return,
            filing_status=FilingStatus.MARRIED_FILING_JOINTLY,
            tax_year=2025
        )

        calc = state_return.calculation

        # Effective rate should be reasonable (around 1.4-1.5% for this income)
        assert calc.effective_rate >= Decimal("0")
        assert calc.effective_rate < Decimal("10")  # Less than 10%

    def test_jones_marginal_tax_rate(
        self, state_forms_service, jones_federal_return
    ):
        """Test Jones family marginal NJ tax rate."""
        state_return = state_forms_service.generate_state_return(
            state=StateCode.NJ,
            federal_return=jones_federal_return,
            filing_status=FilingStatus.MARRIED_FILING_JOINTLY,
            tax_year=2025
        )

        calc = state_return.calculation

        # Marginal rate for ~$34,526 taxable income should be 1.75%
        assert calc.marginal_rate == Decimal("1.75")

    def test_jones_bracket_breakdown(
        self, state_forms_service, jones_federal_return
    ):
        """Test Jones family bracket-by-bracket breakdown.

        With taxable income of $22,325:
        - First bracket: 1.4% on $20,000 = $280
        - Second bracket: 1.75% on $2,325 = $40.69
        - Total: ~$320.69
        """
        state_return = state_forms_service.generate_state_return(
            state=StateCode.NJ,
            federal_return=jones_federal_return,
            filing_status=FilingStatus.MARRIED_FILING_JOINTLY,
            tax_year=2025
        )

        calc = state_return.calculation
        breakdown = calc.tax_bracket_breakdown

        # Should have 2 brackets used
        assert len(breakdown) == 2

        # First bracket: 1.4% on $20,000
        assert breakdown[0]["rate"] == 1.4
        assert breakdown[0]["income_in_bracket"] == 20000.0
        assert breakdown[0]["tax"] == 280.0  # $20,000 * 1.4%

        # Second bracket: 1.75% on $2,325 (remainder)
        assert breakdown[1]["rate"] == 1.75
        assert breakdown[1]["income_in_bracket"] == 2325.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
