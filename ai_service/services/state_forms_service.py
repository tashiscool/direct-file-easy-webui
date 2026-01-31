"""State Tax Forms Service.

Provides comprehensive state tax form generation with parity to UsTaxes state capabilities.
Includes state form generation, multi-state support, state-specific credits and deductions,
and special handling for major states (CA, NY, IL, MA, NJ, PA).
"""

from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union
from datetime import date


class StateCode(Enum):
    """US State codes for tax filing."""
    AL = "AL"  # Alabama
    AK = "AK"  # Alaska (no income tax)
    AZ = "AZ"  # Arizona
    AR = "AR"  # Arkansas
    CA = "CA"  # California
    CO = "CO"  # Colorado
    CT = "CT"  # Connecticut
    DE = "DE"  # Delaware
    FL = "FL"  # Florida (no income tax)
    GA = "GA"  # Georgia
    HI = "HI"  # Hawaii
    ID = "ID"  # Idaho
    IL = "IL"  # Illinois
    IN = "IN"  # Indiana
    IA = "IA"  # Iowa
    KS = "KS"  # Kansas
    KY = "KY"  # Kentucky
    LA = "LA"  # Louisiana
    ME = "ME"  # Maine
    MD = "MD"  # Maryland
    MA = "MA"  # Massachusetts
    MI = "MI"  # Michigan
    MN = "MN"  # Minnesota
    MS = "MS"  # Mississippi
    MO = "MO"  # Missouri
    MT = "MT"  # Montana
    NE = "NE"  # Nebraska
    NV = "NV"  # Nevada (no income tax)
    NH = "NH"  # New Hampshire (interest/dividends only)
    NJ = "NJ"  # New Jersey
    NM = "NM"  # New Mexico
    NY = "NY"  # New York
    NC = "NC"  # North Carolina
    ND = "ND"  # North Dakota
    OH = "OH"  # Ohio
    OK = "OK"  # Oklahoma
    OR = "OR"  # Oregon
    PA = "PA"  # Pennsylvania
    RI = "RI"  # Rhode Island
    SC = "SC"  # South Carolina
    SD = "SD"  # South Dakota (no income tax)
    TN = "TN"  # Tennessee (no income tax)
    TX = "TX"  # Texas (no income tax)
    UT = "UT"  # Utah
    VT = "VT"  # Vermont
    VA = "VA"  # Virginia
    WA = "WA"  # Washington (no income tax)
    WV = "WV"  # West Virginia
    WI = "WI"  # Wisconsin
    WY = "WY"  # Wyoming (no income tax)
    DC = "DC"  # District of Columbia


class ResidencyStatus(Enum):
    """Residency status for state tax purposes."""
    FULL_YEAR_RESIDENT = "full_year_resident"
    PART_YEAR_RESIDENT = "part_year_resident"
    NON_RESIDENT = "non_resident"


class FilingStatus(Enum):
    """Filing status options."""
    SINGLE = "single"
    MARRIED_FILING_JOINTLY = "mfj"
    MARRIED_FILING_SEPARATELY = "mfs"
    HEAD_OF_HOUSEHOLD = "hoh"
    QUALIFYING_SURVIVING_SPOUSE = "qss"


@dataclass
class StateTaxBracket:
    """A state tax bracket with rate and threshold."""
    rate: Decimal
    min_income: Decimal
    max_income: Optional[Decimal] = None


@dataclass
class StateFormLine:
    """A single line item on a state tax form."""
    line_number: str
    description: str
    value: Decimal
    source: Optional[str] = None  # e.g., "Federal 1040 Line 11"
    notes: Optional[str] = None


@dataclass
class StateSchedule:
    """A state tax schedule attachment."""
    schedule_id: str
    title: str
    lines: List[StateFormLine] = field(default_factory=list)
    total: Decimal = Decimal("0")


@dataclass
class StateForm:
    """A state tax form with line-by-line breakdown."""
    form_id: str
    title: str
    tax_year: int
    state: StateCode
    lines: List[StateFormLine] = field(default_factory=list)
    schedules: List[StateSchedule] = field(default_factory=list)


@dataclass
class StateCredit:
    """A state tax credit."""
    credit_id: str
    name: str
    amount: Decimal
    refundable: bool = False
    carryforward_years: int = 0
    form_reference: Optional[str] = None


@dataclass
class StateDeduction:
    """A state-specific deduction."""
    deduction_id: str
    name: str
    amount: Decimal
    category: str  # 'above_line', 'itemized', 'standard'
    source: Optional[str] = None


@dataclass
class StateTaxCalculation:
    """Complete state tax calculation breakdown."""
    # Income
    federal_agi: Decimal
    state_additions: Decimal
    state_subtractions: Decimal
    state_agi: Decimal

    # Deductions
    standard_deduction: Decimal
    itemized_deduction: Decimal
    deduction_used: str  # 'standard' or 'itemized'
    total_deduction: Decimal
    exemptions: Decimal

    # Taxable Income
    state_taxable_income: Decimal

    # Tax
    tax_before_credits: Decimal
    tax_bracket_breakdown: List[Dict[str, Any]]

    # Credits
    nonrefundable_credits: Decimal
    refundable_credits: Decimal
    total_credits: Decimal
    credit_details: List[StateCredit]

    # Final
    net_tax: Decimal
    withholding: Decimal
    estimated_payments: Decimal
    credits_for_other_states: Decimal
    amount_owed: Decimal
    refund_amount: Decimal

    # Rates
    marginal_rate: Decimal
    effective_rate: Decimal


@dataclass
class MultiStateAllocation:
    """Income allocation for multi-state filing."""
    state: StateCode
    allocation_percentage: Decimal
    days_resident: int
    income_sourced: Decimal
    wage_allocation: Decimal
    business_allocation: Decimal
    investment_allocation: Decimal


@dataclass
class StateReturn:
    """Complete state tax return."""
    state: StateCode
    tax_year: int
    residency_status: ResidencyStatus
    filing_status: FilingStatus
    primary_form: StateForm
    schedules: List[StateSchedule]
    attachments: List[StateForm]
    calculation: StateTaxCalculation
    multi_state_info: Optional[MultiStateAllocation] = None
    credits: List[StateCredit] = field(default_factory=list)
    deductions: List[StateDeduction] = field(default_factory=list)
    payment_info: Dict[str, Any] = field(default_factory=dict)


class StateFormsService:
    """Service for generating state tax forms and calculations."""

    # States with no income tax
    NO_INCOME_TAX_STATES = {
        StateCode.AK, StateCode.FL, StateCode.NV, StateCode.SD,
        StateCode.TN, StateCode.TX, StateCode.WA, StateCode.WY
    }

    # 2025 State Tax Brackets (major states)
    STATE_BRACKETS_2025 = {
        StateCode.CA: {
            FilingStatus.SINGLE: [
                StateTaxBracket(Decimal("0.01"), Decimal("0"), Decimal("10412")),
                StateTaxBracket(Decimal("0.02"), Decimal("10412"), Decimal("24684")),
                StateTaxBracket(Decimal("0.04"), Decimal("24684"), Decimal("38959")),
                StateTaxBracket(Decimal("0.06"), Decimal("38959"), Decimal("54081")),
                StateTaxBracket(Decimal("0.08"), Decimal("54081"), Decimal("68350")),
                StateTaxBracket(Decimal("0.093"), Decimal("68350"), Decimal("349137")),
                StateTaxBracket(Decimal("0.103"), Decimal("349137"), Decimal("418961")),
                StateTaxBracket(Decimal("0.113"), Decimal("418961"), Decimal("698271")),
                StateTaxBracket(Decimal("0.123"), Decimal("698271"), None),
            ],
            FilingStatus.MARRIED_FILING_JOINTLY: [
                StateTaxBracket(Decimal("0.01"), Decimal("0"), Decimal("20824")),
                StateTaxBracket(Decimal("0.02"), Decimal("20824"), Decimal("49368")),
                StateTaxBracket(Decimal("0.04"), Decimal("49368"), Decimal("77918")),
                StateTaxBracket(Decimal("0.06"), Decimal("77918"), Decimal("108162")),
                StateTaxBracket(Decimal("0.08"), Decimal("108162"), Decimal("136700")),
                StateTaxBracket(Decimal("0.093"), Decimal("136700"), Decimal("698274")),
                StateTaxBracket(Decimal("0.103"), Decimal("698274"), Decimal("837922")),
                StateTaxBracket(Decimal("0.113"), Decimal("837922"), Decimal("1396542")),
                StateTaxBracket(Decimal("0.123"), Decimal("1396542"), None),
            ],
        },
        StateCode.NY: {
            FilingStatus.SINGLE: [
                StateTaxBracket(Decimal("0.04"), Decimal("0"), Decimal("8500")),
                StateTaxBracket(Decimal("0.045"), Decimal("8500"), Decimal("11700")),
                StateTaxBracket(Decimal("0.0525"), Decimal("11700"), Decimal("13900")),
                StateTaxBracket(Decimal("0.0585"), Decimal("13900"), Decimal("80650")),
                StateTaxBracket(Decimal("0.0625"), Decimal("80650"), Decimal("215400")),
                StateTaxBracket(Decimal("0.0685"), Decimal("215400"), Decimal("1077550")),
                StateTaxBracket(Decimal("0.0965"), Decimal("1077550"), Decimal("5000000")),
                StateTaxBracket(Decimal("0.103"), Decimal("5000000"), Decimal("25000000")),
                StateTaxBracket(Decimal("0.109"), Decimal("25000000"), None),
            ],
            FilingStatus.MARRIED_FILING_JOINTLY: [
                StateTaxBracket(Decimal("0.04"), Decimal("0"), Decimal("17150")),
                StateTaxBracket(Decimal("0.045"), Decimal("17150"), Decimal("23600")),
                StateTaxBracket(Decimal("0.0525"), Decimal("23600"), Decimal("27900")),
                StateTaxBracket(Decimal("0.0585"), Decimal("27900"), Decimal("161550")),
                StateTaxBracket(Decimal("0.0625"), Decimal("161550"), Decimal("323200")),
                StateTaxBracket(Decimal("0.0685"), Decimal("323200"), Decimal("2155350")),
                StateTaxBracket(Decimal("0.0965"), Decimal("2155350"), Decimal("5000000")),
                StateTaxBracket(Decimal("0.103"), Decimal("5000000"), Decimal("25000000")),
                StateTaxBracket(Decimal("0.109"), Decimal("25000000"), None),
            ],
        },
        StateCode.IL: {
            # Illinois has a flat tax rate
            FilingStatus.SINGLE: [
                StateTaxBracket(Decimal("0.0495"), Decimal("0"), None),
            ],
            FilingStatus.MARRIED_FILING_JOINTLY: [
                StateTaxBracket(Decimal("0.0495"), Decimal("0"), None),
            ],
        },
        StateCode.MA: {
            # Massachusetts has a flat tax rate (with millionaire's tax)
            FilingStatus.SINGLE: [
                StateTaxBracket(Decimal("0.05"), Decimal("0"), Decimal("1000000")),
                StateTaxBracket(Decimal("0.09"), Decimal("1000000"), None),  # 4% surtax
            ],
            FilingStatus.MARRIED_FILING_JOINTLY: [
                StateTaxBracket(Decimal("0.05"), Decimal("0"), Decimal("1000000")),
                StateTaxBracket(Decimal("0.09"), Decimal("1000000"), None),
            ],
        },
        StateCode.NJ: {
            FilingStatus.SINGLE: [
                StateTaxBracket(Decimal("0.014"), Decimal("0"), Decimal("20000")),
                StateTaxBracket(Decimal("0.0175"), Decimal("20000"), Decimal("35000")),
                StateTaxBracket(Decimal("0.035"), Decimal("35000"), Decimal("40000")),
                StateTaxBracket(Decimal("0.05525"), Decimal("40000"), Decimal("75000")),
                StateTaxBracket(Decimal("0.0637"), Decimal("75000"), Decimal("500000")),
                StateTaxBracket(Decimal("0.0897"), Decimal("500000"), Decimal("1000000")),
                StateTaxBracket(Decimal("0.1075"), Decimal("1000000"), None),
            ],
            FilingStatus.MARRIED_FILING_JOINTLY: [
                StateTaxBracket(Decimal("0.014"), Decimal("0"), Decimal("20000")),
                StateTaxBracket(Decimal("0.0175"), Decimal("20000"), Decimal("50000")),
                StateTaxBracket(Decimal("0.0245"), Decimal("50000"), Decimal("70000")),
                StateTaxBracket(Decimal("0.035"), Decimal("70000"), Decimal("80000")),
                StateTaxBracket(Decimal("0.05525"), Decimal("80000"), Decimal("150000")),
                StateTaxBracket(Decimal("0.0637"), Decimal("150000"), Decimal("500000")),
                StateTaxBracket(Decimal("0.0897"), Decimal("500000"), Decimal("1000000")),
                StateTaxBracket(Decimal("0.1075"), Decimal("1000000"), None),
            ],
        },
        StateCode.PA: {
            # Pennsylvania has a flat tax rate
            FilingStatus.SINGLE: [
                StateTaxBracket(Decimal("0.0307"), Decimal("0"), None),
            ],
            FilingStatus.MARRIED_FILING_JOINTLY: [
                StateTaxBracket(Decimal("0.0307"), Decimal("0"), None),
            ],
        },
    }

    # 2025 State Standard Deductions
    STATE_STANDARD_DEDUCTIONS_2025 = {
        StateCode.CA: {
            FilingStatus.SINGLE: Decimal("5540"),
            FilingStatus.MARRIED_FILING_JOINTLY: Decimal("11080"),
            FilingStatus.MARRIED_FILING_SEPARATELY: Decimal("5540"),
            FilingStatus.HEAD_OF_HOUSEHOLD: Decimal("11080"),
        },
        StateCode.NY: {
            FilingStatus.SINGLE: Decimal("8000"),
            FilingStatus.MARRIED_FILING_JOINTLY: Decimal("16050"),
            FilingStatus.MARRIED_FILING_SEPARATELY: Decimal("8000"),
            FilingStatus.HEAD_OF_HOUSEHOLD: Decimal("11200"),
        },
        StateCode.IL: {  # Illinois uses exemptions, not standard deduction
            FilingStatus.SINGLE: Decimal("0"),
            FilingStatus.MARRIED_FILING_JOINTLY: Decimal("0"),
        },
        StateCode.MA: {  # Massachusetts has no standard deduction
            FilingStatus.SINGLE: Decimal("0"),
            FilingStatus.MARRIED_FILING_JOINTLY: Decimal("0"),
        },
        StateCode.NJ: {
            FilingStatus.SINGLE: Decimal("0"),  # NJ doesn't have standard deduction
            FilingStatus.MARRIED_FILING_JOINTLY: Decimal("0"),
        },
        StateCode.PA: {
            FilingStatus.SINGLE: Decimal("0"),  # PA doesn't have standard deduction
            FilingStatus.MARRIED_FILING_JOINTLY: Decimal("0"),
        },
    }

    # 2025 State Personal Exemptions
    STATE_EXEMPTIONS_2025 = {
        StateCode.CA: {
            "personal": Decimal("144"),  # Credit, not deduction
            "dependent": Decimal("446"),  # Credit
        },
        StateCode.NY: {
            "personal": Decimal("0"),  # Included in standard deduction
            "dependent": Decimal("1000"),
        },
        StateCode.IL: {
            "personal": Decimal("2625"),
            "dependent": Decimal("2625"),
        },
        StateCode.MA: {
            "personal": Decimal("4400"),
            "dependent": Decimal("1000"),
        },
        StateCode.NJ: {
            "personal": Decimal("1000"),
            "dependent": Decimal("1500"),
        },
        StateCode.PA: {
            "personal": Decimal("0"),  # No exemptions
            "dependent": Decimal("0"),
        },
    }

    # State form identifiers
    STATE_FORMS = {
        StateCode.CA: {
            "resident": "Form 540",
            "non_resident": "Form 540NR",
            "schedules": ["Schedule CA", "Schedule D", "FTB 3514", "FTB 3800"],
        },
        StateCode.NY: {
            "resident": "IT-201",
            "non_resident": "IT-203",
            "schedules": ["IT-201-ATT", "IT-196", "IT-214", "IT-215"],
        },
        StateCode.IL: {
            "resident": "IL-1040",
            "schedules": ["Schedule M", "Schedule IL-E/EIC", "Schedule NR", "Schedule CR"],
        },
        StateCode.MA: {
            "resident": "Form 1",
            "non_resident": "Form 1-NR/PY",
            "schedules": ["Schedule B", "Schedule C", "Schedule D", "Schedule HC", "Schedule E"],
        },
        StateCode.NJ: {
            "resident": "NJ-1040",
            "non_resident": "NJ-1040NR",
            "schedules": ["Schedule A", "Schedule B", "Schedule C", "NJ-2450"],
        },
        StateCode.PA: {
            "resident": "PA-40",
            "non_resident": "PA-40NRC",
            "schedules": ["PA Schedule A", "PA Schedule C", "PA Schedule D", "PA-40 ES"],
        },
    }

    def __init__(self):
        """Initialize the state forms service."""
        self._init_additional_brackets()

    def _init_additional_brackets(self):
        """Initialize brackets for additional states."""
        # Add brackets for other filing statuses by copying single brackets
        for state, brackets in self.STATE_BRACKETS_2025.items():
            if FilingStatus.HEAD_OF_HOUSEHOLD not in brackets:
                # Use single brackets for HOH as default
                brackets[FilingStatus.HEAD_OF_HOUSEHOLD] = brackets.get(
                    FilingStatus.SINGLE, []
                )
            if FilingStatus.MARRIED_FILING_SEPARATELY not in brackets:
                # Use single brackets for MFS
                brackets[FilingStatus.MARRIED_FILING_SEPARATELY] = brackets.get(
                    FilingStatus.SINGLE, []
                )
            if FilingStatus.QUALIFYING_SURVIVING_SPOUSE not in brackets:
                # Use MFJ brackets for QSS
                brackets[FilingStatus.QUALIFYING_SURVIVING_SPOUSE] = brackets.get(
                    FilingStatus.MARRIED_FILING_JOINTLY, []
                )

    def generate_state_return(
        self,
        state: StateCode,
        federal_return: Dict[str, Any],
        filing_status: FilingStatus,
        residency_status: ResidencyStatus = ResidencyStatus.FULL_YEAR_RESIDENT,
        multi_state_info: Optional[Dict[str, Any]] = None,
        tax_year: int = 2025
    ) -> StateReturn:
        """Generate a complete state tax return.

        Args:
            state: State to file in.
            federal_return: Federal return data (facts dictionary).
            filing_status: Filing status.
            residency_status: Residency status in the state.
            multi_state_info: Multi-state filing information.
            tax_year: Tax year.

        Returns:
            Complete StateReturn with forms and calculations.
        """
        if state in self.NO_INCOME_TAX_STATES:
            return self._generate_no_tax_return(state, tax_year, filing_status)

        # Calculate state tax
        calculation = self._calculate_state_tax(
            state, federal_return, filing_status, residency_status, multi_state_info
        )

        # Generate forms based on state
        if state == StateCode.CA:
            return self._generate_california_return(
                federal_return, filing_status, residency_status, calculation, tax_year
            )
        elif state == StateCode.NY:
            return self._generate_new_york_return(
                federal_return, filing_status, residency_status, calculation, tax_year
            )
        elif state == StateCode.IL:
            return self._generate_illinois_return(
                federal_return, filing_status, residency_status, calculation, tax_year
            )
        elif state == StateCode.MA:
            return self._generate_massachusetts_return(
                federal_return, filing_status, residency_status, calculation, tax_year
            )
        elif state == StateCode.NJ:
            return self._generate_new_jersey_return(
                federal_return, filing_status, residency_status, calculation, tax_year
            )
        elif state == StateCode.PA:
            return self._generate_pennsylvania_return(
                federal_return, filing_status, residency_status, calculation, tax_year
            )
        else:
            return self._generate_generic_state_return(
                state, federal_return, filing_status, residency_status, calculation, tax_year
            )

    def calculate_multi_state_allocation(
        self,
        states: List[Dict[str, Any]],
        federal_return: Dict[str, Any],
        tax_year: int = 2025
    ) -> List[MultiStateAllocation]:
        """Calculate income allocation across multiple states.

        Args:
            states: List of state info with residency periods.
            federal_return: Federal return data.
            tax_year: Tax year.

        Returns:
            List of MultiStateAllocation for each state.
        """
        allocations = []
        total_days = 365 if tax_year % 4 != 0 else 366

        federal_wages = self._get_decimal(federal_return, "/wages", "/totalW2Wages")
        federal_business = self._get_decimal(federal_return, "/businessIncome", "/scheduleCNetProfit")
        federal_investment = (
            self._get_decimal(federal_return, "/interestIncome") +
            self._get_decimal(federal_return, "/dividendIncome") +
            self._get_decimal(federal_return, "/capitalGains")
        )
        total_income = federal_wages + federal_business + federal_investment

        for state_info in states:
            state_code = StateCode(state_info.get("state"))
            days = state_info.get("days", 0)

            # Calculate allocation percentage based on days
            allocation_pct = Decimal(str(days)) / Decimal(str(total_days))

            # Wages: allocate based on where work was performed
            wage_pct = Decimal(str(state_info.get("work_percentage", days / total_days)))
            wage_allocation = federal_wages * wage_pct

            # Business income: allocate based on business location
            business_pct = Decimal(str(state_info.get("business_percentage", allocation_pct)))
            business_allocation = federal_business * business_pct

            # Investment income: typically follows residency
            investment_allocation = federal_investment * allocation_pct

            income_sourced = wage_allocation + business_allocation + investment_allocation

            allocations.append(MultiStateAllocation(
                state=state_code,
                allocation_percentage=allocation_pct,
                days_resident=days,
                income_sourced=income_sourced,
                wage_allocation=wage_allocation,
                business_allocation=business_allocation,
                investment_allocation=investment_allocation
            ))

        return allocations

    def calculate_credit_for_taxes_paid_to_other_states(
        self,
        resident_state: StateCode,
        other_state_taxes: List[Dict[str, Any]],
        resident_state_tax: Decimal,
        income_taxed_in_other_states: Decimal,
        total_income: Decimal
    ) -> Decimal:
        """Calculate credit for taxes paid to other states.

        Args:
            resident_state: State of residence.
            other_state_taxes: List of taxes paid to other states.
            resident_state_tax: Tax calculated by resident state.
            income_taxed_in_other_states: Income taxed by other states.
            total_income: Total income.

        Returns:
            Credit amount.
        """
        if not other_state_taxes or total_income <= 0:
            return Decimal("0")

        total_other_taxes = sum(
            Decimal(str(t.get("tax_paid", 0))) for t in other_state_taxes
        )

        # Credit is limited to the lesser of:
        # 1. Actual taxes paid to other states
        # 2. Resident state tax on income taxed by other states

        proportion = income_taxed_in_other_states / total_income
        max_credit = resident_state_tax * proportion

        credit = min(total_other_taxes, max_credit)

        return credit.quantize(Decimal("0.01"), ROUND_HALF_UP)

    def get_state_credits(
        self,
        state: StateCode,
        federal_return: Dict[str, Any],
        filing_status: FilingStatus,
        state_agi: Decimal
    ) -> List[StateCredit]:
        """Get available state credits.

        Args:
            state: State code.
            federal_return: Federal return data.
            filing_status: Filing status.
            state_agi: State adjusted gross income.

        Returns:
            List of available StateCredits.
        """
        credits = []

        # Property Tax Credit
        property_tax = self._get_decimal(federal_return, "/propertyTax", "/propertyTaxesPaid")
        if property_tax > 0:
            credit = self._calculate_property_tax_credit(
                state, property_tax, state_agi, filing_status
            )
            if credit > 0:
                credits.append(StateCredit(
                    credit_id="property_tax",
                    name="Property Tax Credit",
                    amount=credit,
                    refundable=state in [StateCode.NY, StateCode.MA],
                    form_reference=self._get_credit_form(state, "property_tax")
                ))

        # Renter Credit
        rent_paid = self._get_decimal(federal_return, "/rentPaid", "/annualRent")
        if rent_paid > 0:
            credit = self._calculate_renter_credit(
                state, rent_paid, state_agi, filing_status
            )
            if credit > 0:
                credits.append(StateCredit(
                    credit_id="renter",
                    name="Renter's Credit",
                    amount=credit,
                    refundable=True,
                    form_reference=self._get_credit_form(state, "renter")
                ))

        # Child/Dependent Credit
        num_dependents = federal_return.get("/numberOfDependents", 0)
        children_under_17 = federal_return.get("/dependentsUnder17", 0)
        if num_dependents > 0 or children_under_17 > 0:
            credit = self._calculate_dependent_credit(
                state, num_dependents, children_under_17, state_agi, filing_status
            )
            if credit > 0:
                credits.append(StateCredit(
                    credit_id="dependent",
                    name="Child/Dependent Credit",
                    amount=credit,
                    refundable=state in [StateCode.CA, StateCode.NY],
                    form_reference=self._get_credit_form(state, "dependent")
                ))

        # State EITC
        federal_eitc = self._get_decimal(federal_return, "/earnedIncomeCredit", "/eitc")
        if federal_eitc > 0:
            credit = self._calculate_state_eitc(
                state, federal_eitc, state_agi, filing_status
            )
            if credit > 0:
                credits.append(StateCredit(
                    credit_id="eitc",
                    name="State Earned Income Credit",
                    amount=credit,
                    refundable=True,
                    form_reference=self._get_credit_form(state, "eitc")
                ))

        # Education Credits
        education_expenses = self._get_decimal(federal_return, "/educationExpenses")
        if education_expenses > 0:
            credit = self._calculate_education_credit(
                state, education_expenses, state_agi, filing_status
            )
            if credit > 0:
                credits.append(StateCredit(
                    credit_id="education",
                    name="Education Credit",
                    amount=credit,
                    refundable=False,
                    form_reference=self._get_credit_form(state, "education")
                ))

        return credits

    def get_state_deductions(
        self,
        state: StateCode,
        federal_return: Dict[str, Any],
        filing_status: FilingStatus
    ) -> Tuple[List[StateDeduction], Decimal, Decimal]:
        """Get state-specific deductions.

        Args:
            state: State code.
            federal_return: Federal return data.
            filing_status: Filing status.

        Returns:
            Tuple of (deductions list, standard deduction, itemized total).
        """
        deductions = []

        # Get standard deduction for state
        std_deductions = self.STATE_STANDARD_DEDUCTIONS_2025.get(state, {})
        standard_deduction = std_deductions.get(filing_status, Decimal("0"))

        # Calculate itemized deductions (state-specific adjustments)
        mortgage_interest = self._get_decimal(federal_return, "/mortgageInterest")
        state_taxes = min(
            self._get_decimal(federal_return, "/stateIncomeTax"),
            Decimal("10000")  # SALT cap still applies
        )
        property_taxes = self._get_decimal(federal_return, "/propertyTax")
        charitable = self._get_decimal(federal_return, "/charitableContributions")
        medical = self._get_decimal(federal_return, "/medicalExpenses")
        federal_agi = self._get_decimal(federal_return, "/adjustedGrossIncome", "/agi")

        # Medical expense floor varies by state
        medical_floor = self._get_medical_floor(state, federal_agi)
        medical_deduction = max(medical - medical_floor, Decimal("0"))

        if mortgage_interest > 0:
            deductions.append(StateDeduction(
                deduction_id="mortgage_interest",
                name="Mortgage Interest",
                amount=mortgage_interest,
                category="itemized",
                source="Federal Schedule A"
            ))

        # Most states don't allow deduction for state income taxes (circular)
        if state not in [StateCode.CA, StateCode.NY, StateCode.NJ]:
            if property_taxes > 0:
                deductions.append(StateDeduction(
                    deduction_id="property_taxes",
                    name="Property Taxes",
                    amount=property_taxes,
                    category="itemized",
                    source="Federal Schedule A"
                ))

        if charitable > 0:
            deductions.append(StateDeduction(
                deduction_id="charitable",
                name="Charitable Contributions",
                amount=charitable,
                category="itemized",
                source="Federal Schedule A"
            ))

        if medical_deduction > 0:
            deductions.append(StateDeduction(
                deduction_id="medical",
                name="Medical Expenses",
                amount=medical_deduction,
                category="itemized",
                source="Federal Schedule A"
            ))

        itemized_total = sum(d.amount for d in deductions if d.category == "itemized")

        return deductions, standard_deduction, itemized_total

    # Private calculation methods

    def _calculate_state_tax(
        self,
        state: StateCode,
        federal_return: Dict[str, Any],
        filing_status: FilingStatus,
        residency_status: ResidencyStatus,
        multi_state_info: Optional[Dict[str, Any]] = None
    ) -> StateTaxCalculation:
        """Calculate complete state tax."""

        # Get federal AGI
        federal_agi = self._get_decimal(
            federal_return, "/adjustedGrossIncome", "/agi"
        )

        # Calculate state additions and subtractions
        additions = self._calculate_state_additions(state, federal_return)
        subtractions = self._calculate_state_subtractions(state, federal_return)

        state_agi = federal_agi + additions - subtractions

        # Handle part-year/non-resident allocation
        if residency_status != ResidencyStatus.FULL_YEAR_RESIDENT and multi_state_info:
            allocation_pct = Decimal(str(multi_state_info.get("allocation_percentage", 1.0)))
            state_agi = state_agi * allocation_pct

        # Get deductions
        deductions, standard_ded, itemized_ded = self.get_state_deductions(
            state, federal_return, filing_status
        )

        if itemized_ded > standard_ded:
            deduction_used = "itemized"
            total_deduction = itemized_ded
        else:
            deduction_used = "standard"
            total_deduction = standard_ded

        # Get exemptions
        exemptions = self._calculate_exemptions(state, federal_return, filing_status)

        # Calculate taxable income
        state_taxable_income = max(state_agi - total_deduction - exemptions, Decimal("0"))

        # Calculate tax using brackets
        tax_before_credits, bracket_breakdown = self._calculate_bracket_tax(
            state, state_taxable_income, filing_status
        )

        # Get credits
        credit_list = self.get_state_credits(state, federal_return, filing_status, state_agi)

        nonrefundable = sum(
            c.amount for c in credit_list if not c.refundable
        )
        refundable = sum(
            c.amount for c in credit_list if c.refundable
        )

        # Calculate credit for other states
        other_state_credit = Decimal("0")
        if multi_state_info and multi_state_info.get("other_state_taxes"):
            other_state_credit = self.calculate_credit_for_taxes_paid_to_other_states(
                state,
                multi_state_info.get("other_state_taxes", []),
                tax_before_credits,
                multi_state_info.get("income_taxed_elsewhere", Decimal("0")),
                state_agi
            )

        # Apply credits
        net_tax = max(tax_before_credits - nonrefundable - other_state_credit, Decimal("0"))
        net_tax -= refundable  # Refundable credits can create negative (refund)

        # Withholding and payments
        withholding = self._get_decimal(
            federal_return, f"/stateWithholding_{state.value}", "/stateWithholding"
        )
        estimated = self._get_decimal(
            federal_return, f"/stateEstimatedPayments_{state.value}", "/stateEstimatedPayments"
        )

        # Final amount owed or refund
        total_payments = withholding + estimated
        if net_tax > total_payments:
            amount_owed = net_tax - total_payments
            refund_amount = Decimal("0")
        else:
            amount_owed = Decimal("0")
            refund_amount = total_payments - net_tax

        # Calculate rates
        marginal_rate = self._get_marginal_rate(state, state_taxable_income, filing_status)
        effective_rate = (
            (tax_before_credits / state_agi * 100)
            if state_agi > 0 else Decimal("0")
        )

        return StateTaxCalculation(
            federal_agi=federal_agi,
            state_additions=additions,
            state_subtractions=subtractions,
            state_agi=state_agi,
            standard_deduction=standard_ded,
            itemized_deduction=itemized_ded,
            deduction_used=deduction_used,
            total_deduction=total_deduction,
            exemptions=exemptions,
            state_taxable_income=state_taxable_income,
            tax_before_credits=tax_before_credits,
            tax_bracket_breakdown=bracket_breakdown,
            nonrefundable_credits=nonrefundable,
            refundable_credits=refundable,
            total_credits=nonrefundable + refundable + other_state_credit,
            credit_details=credit_list,
            net_tax=net_tax,
            withholding=withholding,
            estimated_payments=estimated,
            credits_for_other_states=other_state_credit,
            amount_owed=amount_owed.quantize(Decimal("0.01"), ROUND_HALF_UP),
            refund_amount=refund_amount.quantize(Decimal("0.01"), ROUND_HALF_UP),
            marginal_rate=marginal_rate,
            effective_rate=effective_rate.quantize(Decimal("0.01"), ROUND_HALF_UP)
        )

    def _calculate_state_additions(
        self,
        state: StateCode,
        federal_return: Dict[str, Any]
    ) -> Decimal:
        """Calculate state additions to federal AGI."""
        additions = Decimal("0")

        # Interest from other states' municipal bonds
        other_state_muni = self._get_decimal(
            federal_return, "/otherStateMunicipalBondInterest"
        )
        additions += other_state_muni

        # State-specific additions
        if state == StateCode.CA:
            # California adds back some federal deductions
            pass
        elif state == StateCode.NY:
            # NY adds interest on non-NY bonds
            pass
        elif state == StateCode.NJ:
            # NJ has extensive additions list
            bonus_depreciation = self._get_decimal(federal_return, "/bonusDepreciation")
            additions += bonus_depreciation

        return additions

    def _calculate_state_subtractions(
        self,
        state: StateCode,
        federal_return: Dict[str, Any]
    ) -> Decimal:
        """Calculate state subtractions from federal AGI."""
        subtractions = Decimal("0")

        # Interest on US obligations (most states)
        us_bond_interest = self._get_decimal(
            federal_return, "/usSavingsBondInterest", "/treasuryBondInterest"
        )
        subtractions += us_bond_interest

        # State-specific subtractions
        if state == StateCode.CA:
            # California allows Social Security subtraction
            social_security = self._get_decimal(federal_return, "/socialSecurityBenefits")
            subtractions += social_security
        elif state == StateCode.NY:
            # NY pension exclusion
            pension = self._get_decimal(federal_return, "/pensionIncome")
            if pension > 0:
                subtractions += min(pension, Decimal("20000"))
        elif state == StateCode.PA:
            # PA doesn't tax retirement income
            retirement = self._get_decimal(federal_return, "/retirementIncome")
            subtractions += retirement

        return subtractions

    def _calculate_exemptions(
        self,
        state: StateCode,
        federal_return: Dict[str, Any],
        filing_status: FilingStatus
    ) -> Decimal:
        """Calculate state personal exemptions."""
        exemptions_data = self.STATE_EXEMPTIONS_2025.get(state, {})
        personal = exemptions_data.get("personal", Decimal("0"))
        dependent = exemptions_data.get("dependent", Decimal("0"))

        num_dependents = federal_return.get("/numberOfDependents", 0)

        # Personal exemption (2 for MFJ)
        if filing_status == FilingStatus.MARRIED_FILING_JOINTLY:
            total = personal * 2
        else:
            total = personal

        # Dependent exemptions
        total += dependent * Decimal(str(num_dependents))

        return total

    def _calculate_bracket_tax(
        self,
        state: StateCode,
        taxable_income: Decimal,
        filing_status: FilingStatus
    ) -> Tuple[Decimal, List[Dict[str, Any]]]:
        """Calculate tax using state brackets."""
        brackets = self.STATE_BRACKETS_2025.get(state, {}).get(filing_status, [])

        if not brackets:
            # Default to single brackets if filing status not found
            brackets = self.STATE_BRACKETS_2025.get(state, {}).get(FilingStatus.SINGLE, [])

        if not brackets:
            return Decimal("0"), []

        tax = Decimal("0")
        breakdown = []
        remaining = taxable_income

        for bracket in brackets:
            if remaining <= 0:
                break

            bracket_size = (
                bracket.max_income - bracket.min_income
                if bracket.max_income else remaining
            )

            taxable_in_bracket = min(remaining, bracket_size)
            bracket_tax = taxable_in_bracket * bracket.rate
            tax += bracket_tax

            breakdown.append({
                "rate": float(bracket.rate * 100),
                "income_in_bracket": float(taxable_in_bracket),
                "tax": float(bracket_tax),
                "min": float(bracket.min_income),
                "max": float(bracket.max_income) if bracket.max_income else None
            })

            remaining -= taxable_in_bracket

        return tax.quantize(Decimal("0.01"), ROUND_HALF_UP), breakdown

    def _get_marginal_rate(
        self,
        state: StateCode,
        taxable_income: Decimal,
        filing_status: FilingStatus
    ) -> Decimal:
        """Get marginal tax rate for given income."""
        brackets = self.STATE_BRACKETS_2025.get(state, {}).get(filing_status, [])

        if not brackets:
            brackets = self.STATE_BRACKETS_2025.get(state, {}).get(FilingStatus.SINGLE, [])

        for bracket in brackets:
            if bracket.max_income is None or taxable_income <= bracket.max_income:
                return bracket.rate * 100

        if brackets:
            return brackets[-1].rate * 100
        return Decimal("0")

    # Credit calculation methods

    def _calculate_property_tax_credit(
        self,
        state: StateCode,
        property_tax: Decimal,
        state_agi: Decimal,
        filing_status: FilingStatus
    ) -> Decimal:
        """Calculate property tax credit."""
        if state == StateCode.NY:
            # NY STAR credit (simplified)
            if state_agi <= Decimal("250000"):
                return min(property_tax * Decimal("0.03"), Decimal("350"))
        elif state == StateCode.MA:
            # MA Circuit Breaker credit
            if state_agi <= Decimal("64000"):
                return min(property_tax - state_agi * Decimal("0.10"), Decimal("1200"))
        elif state == StateCode.NJ:
            # NJ Homestead Benefit
            if state_agi <= Decimal("150000"):
                return min(property_tax * Decimal("0.05"), Decimal("500"))

        return Decimal("0")

    def _calculate_renter_credit(
        self,
        state: StateCode,
        rent_paid: Decimal,
        state_agi: Decimal,
        filing_status: FilingStatus
    ) -> Decimal:
        """Calculate renter's credit."""
        if state == StateCode.CA:
            # California renter's credit
            if filing_status == FilingStatus.MARRIED_FILING_JOINTLY:
                if state_agi <= Decimal("103620"):
                    return Decimal("120")
            else:
                if state_agi <= Decimal("51810"):
                    return Decimal("60")
        elif state == StateCode.MA:
            # MA rent deduction (not credit, but handled here)
            max_deduction = Decimal("3000")
            return min(rent_paid * Decimal("0.50"), max_deduction)

        return Decimal("0")

    def _calculate_dependent_credit(
        self,
        state: StateCode,
        num_dependents: int,
        children_under_17: int,
        state_agi: Decimal,
        filing_status: FilingStatus
    ) -> Decimal:
        """Calculate child/dependent credit."""
        if state == StateCode.CA:
            # California Young Child Tax Credit
            if state_agi <= Decimal("30931") and children_under_17 > 0:
                return min(Decimal("1117") * children_under_17, Decimal("1117"))
        elif state == StateCode.NY:
            # NY Empire State Child Credit
            if children_under_17 > 0:
                base_credit = Decimal("330") * children_under_17
                if state_agi > Decimal("110000"):
                    reduction = (state_agi - Decimal("110000")) / Decimal("1000") * Decimal("16.50")
                    base_credit = max(base_credit - reduction, Decimal("0"))
                return base_credit
        elif state == StateCode.NJ:
            # NJ Child Tax Credit
            if state_agi <= Decimal("80000") and children_under_17 > 0:
                return Decimal("500") * children_under_17

        return Decimal("0")

    def _calculate_state_eitc(
        self,
        state: StateCode,
        federal_eitc: Decimal,
        state_agi: Decimal,
        filing_status: FilingStatus
    ) -> Decimal:
        """Calculate state earned income credit."""
        # State EITC is typically a percentage of federal EITC
        state_eitc_rates = {
            StateCode.CA: Decimal("0.85"),  # 85% (CalEITC + YCTC)
            StateCode.NY: Decimal("0.30"),  # 30%
            StateCode.IL: Decimal("0.20"),  # 20%
            StateCode.MA: Decimal("0.40"),  # 40%
            StateCode.NJ: Decimal("0.40"),  # 40%
        }

        rate = state_eitc_rates.get(state, Decimal("0"))
        return (federal_eitc * rate).quantize(Decimal("0.01"), ROUND_HALF_UP)

    def _calculate_education_credit(
        self,
        state: StateCode,
        education_expenses: Decimal,
        state_agi: Decimal,
        filing_status: FilingStatus
    ) -> Decimal:
        """Calculate state education credit."""
        if state == StateCode.NY:
            # NY College Tuition Credit
            if education_expenses > 0 and state_agi <= Decimal("80000"):
                return min(education_expenses * Decimal("0.04"), Decimal("400"))
        elif state == StateCode.MA:
            # MA Higher Education Deduction
            return min(education_expenses, Decimal("2500"))

        return Decimal("0")

    def _get_medical_floor(self, state: StateCode, agi: Decimal) -> Decimal:
        """Get medical expense deduction floor for state."""
        # Most states follow federal 7.5% floor
        return agi * Decimal("0.075")

    def _get_credit_form(self, state: StateCode, credit_type: str) -> str:
        """Get form reference for a credit type."""
        form_refs = {
            StateCode.CA: {
                "property_tax": "FTB 3514",
                "renter": "FTB 3514",
                "dependent": "FTB 3514",
                "eitc": "FTB 3514",
                "education": "Schedule CA",
            },
            StateCode.NY: {
                "property_tax": "IT-214",
                "renter": "IT-214",
                "dependent": "IT-215",
                "eitc": "IT-215",
                "education": "IT-272",
            },
            StateCode.IL: {
                "eitc": "Schedule IL-E/EIC",
                "property_tax": "Schedule ICR",
            },
        }
        return form_refs.get(state, {}).get(credit_type, "")

    # State-specific return generators

    def _generate_california_return(
        self,
        federal_return: Dict[str, Any],
        filing_status: FilingStatus,
        residency_status: ResidencyStatus,
        calculation: StateTaxCalculation,
        tax_year: int
    ) -> StateReturn:
        """Generate California Form 540/540NR."""
        form_id = "540NR" if residency_status != ResidencyStatus.FULL_YEAR_RESIDENT else "540"

        lines = [
            StateFormLine("1", "Wages, salaries, tips",
                         self._get_decimal(federal_return, "/wages")),
            StateFormLine("2", "Interest income",
                         self._get_decimal(federal_return, "/interestIncome")),
            StateFormLine("3", "Dividend income",
                         self._get_decimal(federal_return, "/dividendIncome")),
            StateFormLine("7", "Federal AGI", calculation.federal_agi),
            StateFormLine("8", "California additions", calculation.state_additions),
            StateFormLine("9", "Total (Line 7 + Line 8)",
                         calculation.federal_agi + calculation.state_additions),
            StateFormLine("10", "California subtractions", calculation.state_subtractions),
            StateFormLine("11", "California AGI", calculation.state_agi),
            StateFormLine("18", "Standard or itemized deduction", calculation.total_deduction),
            StateFormLine("19", "California taxable income", calculation.state_taxable_income),
            StateFormLine("31", "Tax before credits", calculation.tax_before_credits),
            StateFormLine("47", "Total credits", calculation.total_credits),
            StateFormLine("48", "Net tax", calculation.net_tax),
            StateFormLine("71", "Total payments",
                         calculation.withholding + calculation.estimated_payments),
            StateFormLine("91", "Amount owed", calculation.amount_owed),
            StateFormLine("95", "Refund", calculation.refund_amount),
        ]

        primary_form = StateForm(
            form_id=f"CA Form {form_id}",
            title=f"California Resident Income Tax Return" if form_id == "540"
                  else "California Nonresident or Part-Year Resident Income Tax Return",
            tax_year=tax_year,
            state=StateCode.CA,
            lines=lines
        )

        # Schedule CA (California Adjustments)
        schedule_ca = StateSchedule(
            schedule_id="Schedule CA",
            title="California Adjustments - Residents",
            lines=[
                StateFormLine("1", "Wages additions", Decimal("0")),
                StateFormLine("2", "Wages subtractions", Decimal("0")),
                StateFormLine("5", "Social Security subtractions",
                             self._get_decimal(federal_return, "/socialSecurityBenefits")),
            ],
            total=calculation.state_subtractions
        )

        return StateReturn(
            state=StateCode.CA,
            tax_year=tax_year,
            residency_status=residency_status,
            filing_status=filing_status,
            primary_form=primary_form,
            schedules=[schedule_ca],
            attachments=[],
            calculation=calculation,
            credits=calculation.credit_details,
            deductions=[]
        )

    def _generate_new_york_return(
        self,
        federal_return: Dict[str, Any],
        filing_status: FilingStatus,
        residency_status: ResidencyStatus,
        calculation: StateTaxCalculation,
        tax_year: int
    ) -> StateReturn:
        """Generate New York IT-201/IT-203."""
        form_id = "IT-203" if residency_status != ResidencyStatus.FULL_YEAR_RESIDENT else "IT-201"

        lines = [
            StateFormLine("1", "Wages, salaries, tips",
                         self._get_decimal(federal_return, "/wages")),
            StateFormLine("2", "Taxable interest",
                         self._get_decimal(federal_return, "/interestIncome")),
            StateFormLine("3", "Ordinary dividends",
                         self._get_decimal(federal_return, "/dividendIncome")),
            StateFormLine("19", "Federal AGI", calculation.federal_agi),
            StateFormLine("20", "Additions to federal AGI", calculation.state_additions),
            StateFormLine("21", "Subtotal",
                         calculation.federal_agi + calculation.state_additions),
            StateFormLine("24", "Subtractions from federal AGI", calculation.state_subtractions),
            StateFormLine("25", "New York AGI", calculation.state_agi),
            StateFormLine("33", "New York standard or itemized deduction",
                         calculation.total_deduction),
            StateFormLine("35", "New York taxable income", calculation.state_taxable_income),
            StateFormLine("39", "New York State tax", calculation.tax_before_credits),
            StateFormLine("46", "Total New York State credits", calculation.total_credits),
            StateFormLine("47", "Net New York State tax", calculation.net_tax),
            StateFormLine("72", "Total New York State tax withheld", calculation.withholding),
            StateFormLine("76", "Total payments",
                         calculation.withholding + calculation.estimated_payments),
            StateFormLine("78", "Amount owed", calculation.amount_owed),
            StateFormLine("79", "Refund", calculation.refund_amount),
        ]

        primary_form = StateForm(
            form_id=f"NY {form_id}",
            title="Resident Income Tax Return" if form_id == "IT-201"
                  else "Nonresident and Part-Year Resident Income Tax Return",
            tax_year=tax_year,
            state=StateCode.NY,
            lines=lines
        )

        return StateReturn(
            state=StateCode.NY,
            tax_year=tax_year,
            residency_status=residency_status,
            filing_status=filing_status,
            primary_form=primary_form,
            schedules=[],
            attachments=[],
            calculation=calculation,
            credits=calculation.credit_details,
            deductions=[]
        )

    def _generate_illinois_return(
        self,
        federal_return: Dict[str, Any],
        filing_status: FilingStatus,
        residency_status: ResidencyStatus,
        calculation: StateTaxCalculation,
        tax_year: int
    ) -> StateReturn:
        """Generate Illinois IL-1040."""
        lines = [
            StateFormLine("1", "Federal AGI", calculation.federal_agi),
            StateFormLine("2", "Federally tax-exempt interest and dividends",
                         calculation.state_additions),
            StateFormLine("3", "Other additions", Decimal("0")),
            StateFormLine("4", "Total additions", calculation.state_additions),
            StateFormLine("5", "Line 1 plus Line 4",
                         calculation.federal_agi + calculation.state_additions),
            StateFormLine("6", "Social Security and retirement subtractions",
                         calculation.state_subtractions),
            StateFormLine("7", "Other subtractions", Decimal("0")),
            StateFormLine("8", "Total subtractions", calculation.state_subtractions),
            StateFormLine("9", "Illinois base income", calculation.state_agi),
            StateFormLine("10", "Exemption allowance", calculation.exemptions),
            StateFormLine("11", "Net income", calculation.state_taxable_income),
            StateFormLine("12", "Illinois income tax (4.95%)", calculation.tax_before_credits),
            StateFormLine("14", "Total credits", calculation.total_credits),
            StateFormLine("15", "Illinois tax after credits", calculation.net_tax),
            StateFormLine("22", "Illinois tax withheld", calculation.withholding),
            StateFormLine("23", "Estimated tax payments", calculation.estimated_payments),
            StateFormLine("28", "Total payments",
                         calculation.withholding + calculation.estimated_payments),
            StateFormLine("32", "Amount owed", calculation.amount_owed),
            StateFormLine("35", "Refund", calculation.refund_amount),
        ]

        primary_form = StateForm(
            form_id="IL-1040",
            title="Illinois Individual Income Tax Return",
            tax_year=tax_year,
            state=StateCode.IL,
            lines=lines
        )

        # Schedule IL-E/EIC
        schedule_eic = StateSchedule(
            schedule_id="Schedule IL-E/EIC",
            title="Illinois Exemption and Earned Income Credit",
            lines=[
                StateFormLine("1", "Number of exemptions",
                             Decimal(str(federal_return.get("/numberOfDependents", 0) + 1))),
                StateFormLine("2", "Exemption allowance", calculation.exemptions),
                StateFormLine("3", "Illinois Earned Income Credit",
                             calculation.refundable_credits),
            ],
            total=calculation.exemptions + calculation.refundable_credits
        )

        return StateReturn(
            state=StateCode.IL,
            tax_year=tax_year,
            residency_status=residency_status,
            filing_status=filing_status,
            primary_form=primary_form,
            schedules=[schedule_eic],
            attachments=[],
            calculation=calculation,
            credits=calculation.credit_details,
            deductions=[]
        )

    def _generate_massachusetts_return(
        self,
        federal_return: Dict[str, Any],
        filing_status: FilingStatus,
        residency_status: ResidencyStatus,
        calculation: StateTaxCalculation,
        tax_year: int
    ) -> StateReturn:
        """Generate Massachusetts Form 1."""
        form_id = "Form 1-NR/PY" if residency_status != ResidencyStatus.FULL_YEAR_RESIDENT else "Form 1"

        lines = [
            StateFormLine("3", "Wages, salaries, tips",
                         self._get_decimal(federal_return, "/wages")),
            StateFormLine("4", "Interest and dividend income",
                         self._get_decimal(federal_return, "/interestIncome") +
                         self._get_decimal(federal_return, "/dividendIncome")),
            StateFormLine("5", "Business income/loss",
                         self._get_decimal(federal_return, "/businessIncome")),
            StateFormLine("10", "Total 5.0% income", calculation.state_agi),
            StateFormLine("14", "Total deductions", calculation.total_deduction),
            StateFormLine("15", "Exemptions", calculation.exemptions),
            StateFormLine("16", "Taxable 5.0% income", calculation.state_taxable_income),
            StateFormLine("17", "Tax on 5.0% income", calculation.tax_before_credits),
            StateFormLine("28", "Total credits", calculation.total_credits),
            StateFormLine("29", "Tax after credits", calculation.net_tax),
            StateFormLine("36", "Tax withheld", calculation.withholding),
            StateFormLine("37", "Estimated tax payments", calculation.estimated_payments),
            StateFormLine("40", "Total payments",
                         calculation.withholding + calculation.estimated_payments),
            StateFormLine("44", "Amount owed", calculation.amount_owed),
            StateFormLine("46", "Refund", calculation.refund_amount),
        ]

        primary_form = StateForm(
            form_id=f"MA {form_id}",
            title="Massachusetts Resident Income Tax Return",
            tax_year=tax_year,
            state=StateCode.MA,
            lines=lines
        )

        # Schedule HC (Health Care)
        schedule_hc = StateSchedule(
            schedule_id="Schedule HC",
            title="Health Care Information",
            lines=[
                StateFormLine("1", "Coverage status", Decimal("1")),  # 1 = full year coverage
            ],
            total=Decimal("0")
        )

        return StateReturn(
            state=StateCode.MA,
            tax_year=tax_year,
            residency_status=residency_status,
            filing_status=filing_status,
            primary_form=primary_form,
            schedules=[schedule_hc],
            attachments=[],
            calculation=calculation,
            credits=calculation.credit_details,
            deductions=[]
        )

    def _generate_new_jersey_return(
        self,
        federal_return: Dict[str, Any],
        filing_status: FilingStatus,
        residency_status: ResidencyStatus,
        calculation: StateTaxCalculation,
        tax_year: int
    ) -> StateReturn:
        """Generate New Jersey NJ-1040."""
        form_id = "NJ-1040NR" if residency_status != ResidencyStatus.FULL_YEAR_RESIDENT else "NJ-1040"

        lines = [
            StateFormLine("15", "Wages",
                         self._get_decimal(federal_return, "/wages")),
            StateFormLine("16", "Taxable interest",
                         self._get_decimal(federal_return, "/interestIncome")),
            StateFormLine("17", "Dividends",
                         self._get_decimal(federal_return, "/dividendIncome")),
            StateFormLine("27", "Total income",
                         calculation.federal_agi + calculation.state_additions),
            StateFormLine("28", "Total exemptions and deductions",
                         calculation.total_deduction + calculation.exemptions),
            StateFormLine("29", "NJ taxable income", calculation.state_taxable_income),
            StateFormLine("36", "Tax on income", calculation.tax_before_credits),
            StateFormLine("47", "Total credits", calculation.total_credits),
            StateFormLine("48", "Balance of tax", calculation.net_tax),
            StateFormLine("52", "NJ tax withheld", calculation.withholding),
            StateFormLine("53", "Estimated payments", calculation.estimated_payments),
            StateFormLine("58", "Total payments",
                         calculation.withholding + calculation.estimated_payments),
            StateFormLine("63", "Balance due", calculation.amount_owed),
            StateFormLine("66", "Refund", calculation.refund_amount),
        ]

        primary_form = StateForm(
            form_id=f"NJ {form_id}",
            title="New Jersey Resident Income Tax Return",
            tax_year=tax_year,
            state=StateCode.NJ,
            lines=lines
        )

        return StateReturn(
            state=StateCode.NJ,
            tax_year=tax_year,
            residency_status=residency_status,
            filing_status=filing_status,
            primary_form=primary_form,
            schedules=[],
            attachments=[],
            calculation=calculation,
            credits=calculation.credit_details,
            deductions=[]
        )

    def _generate_pennsylvania_return(
        self,
        federal_return: Dict[str, Any],
        filing_status: FilingStatus,
        residency_status: ResidencyStatus,
        calculation: StateTaxCalculation,
        tax_year: int
    ) -> StateReturn:
        """Generate Pennsylvania PA-40."""
        form_id = "PA-40NRC" if residency_status != ResidencyStatus.FULL_YEAR_RESIDENT else "PA-40"

        # PA has 8 classes of income
        wages = self._get_decimal(federal_return, "/wages")
        interest = self._get_decimal(federal_return, "/interestIncome")
        dividends = self._get_decimal(federal_return, "/dividendIncome")
        business = self._get_decimal(federal_return, "/businessIncome")

        lines = [
            StateFormLine("1a", "Compensation (Class 1)", wages),
            StateFormLine("1b", "Unreimbursed business expenses", Decimal("0")),
            StateFormLine("1c", "Net compensation", wages),
            StateFormLine("2", "Interest (Class 2)", interest),
            StateFormLine("3", "Dividends (Class 3)", dividends),
            StateFormLine("4", "Net gain/loss from property (Class 4)",
                         self._get_decimal(federal_return, "/capitalGains")),
            StateFormLine("5", "Net gain/loss from rents (Class 5)", Decimal("0")),
            StateFormLine("6", "Net business income (Class 6)", business),
            StateFormLine("7", "Gambling winnings (Class 7)", Decimal("0")),
            StateFormLine("8", "Income from estates or trusts (Class 8)", Decimal("0")),
            StateFormLine("9", "Total PA taxable income", calculation.state_taxable_income),
            StateFormLine("10", "PA income tax (3.07%)", calculation.tax_before_credits),
            StateFormLine("12", "Total PA tax liability", calculation.net_tax),
            StateFormLine("13", "PA tax withheld", calculation.withholding),
            StateFormLine("14", "Estimated tax payments", calculation.estimated_payments),
            StateFormLine("17", "Total payments and credits",
                         calculation.withholding + calculation.estimated_payments),
            StateFormLine("22", "Tax due", calculation.amount_owed),
            StateFormLine("24", "Overpayment", calculation.refund_amount),
        ]

        primary_form = StateForm(
            form_id=f"PA {form_id}",
            title="Pennsylvania Income Tax Return",
            tax_year=tax_year,
            state=StateCode.PA,
            lines=lines
        )

        return StateReturn(
            state=StateCode.PA,
            tax_year=tax_year,
            residency_status=residency_status,
            filing_status=filing_status,
            primary_form=primary_form,
            schedules=[],
            attachments=[],
            calculation=calculation,
            credits=calculation.credit_details,
            deductions=[]
        )

    def _generate_generic_state_return(
        self,
        state: StateCode,
        federal_return: Dict[str, Any],
        filing_status: FilingStatus,
        residency_status: ResidencyStatus,
        calculation: StateTaxCalculation,
        tax_year: int
    ) -> StateReturn:
        """Generate generic state return for states without specific handling."""
        form_info = self.STATE_FORMS.get(state, {"resident": "State Form", "schedules": []})
        form_id = form_info.get(
            "non_resident" if residency_status != ResidencyStatus.FULL_YEAR_RESIDENT else "resident",
            "State Form"
        )

        lines = [
            StateFormLine("1", "Federal AGI", calculation.federal_agi),
            StateFormLine("2", "State additions", calculation.state_additions),
            StateFormLine("3", "State subtractions", calculation.state_subtractions),
            StateFormLine("4", "State AGI", calculation.state_agi),
            StateFormLine("5", "Deductions", calculation.total_deduction),
            StateFormLine("6", "Exemptions", calculation.exemptions),
            StateFormLine("7", "Taxable income", calculation.state_taxable_income),
            StateFormLine("8", "Tax", calculation.tax_before_credits),
            StateFormLine("9", "Credits", calculation.total_credits),
            StateFormLine("10", "Net tax", calculation.net_tax),
            StateFormLine("11", "Withholding", calculation.withholding),
            StateFormLine("12", "Estimated payments", calculation.estimated_payments),
            StateFormLine("13", "Amount owed", calculation.amount_owed),
            StateFormLine("14", "Refund", calculation.refund_amount),
        ]

        primary_form = StateForm(
            form_id=form_id,
            title=f"{state.value} Income Tax Return",
            tax_year=tax_year,
            state=state,
            lines=lines
        )

        return StateReturn(
            state=state,
            tax_year=tax_year,
            residency_status=residency_status,
            filing_status=filing_status,
            primary_form=primary_form,
            schedules=[],
            attachments=[],
            calculation=calculation,
            credits=calculation.credit_details,
            deductions=[]
        )

    def _generate_no_tax_return(
        self,
        state: StateCode,
        tax_year: int,
        filing_status: FilingStatus
    ) -> StateReturn:
        """Generate return for no-income-tax state."""
        calculation = StateTaxCalculation(
            federal_agi=Decimal("0"),
            state_additions=Decimal("0"),
            state_subtractions=Decimal("0"),
            state_agi=Decimal("0"),
            standard_deduction=Decimal("0"),
            itemized_deduction=Decimal("0"),
            deduction_used="none",
            total_deduction=Decimal("0"),
            exemptions=Decimal("0"),
            state_taxable_income=Decimal("0"),
            tax_before_credits=Decimal("0"),
            tax_bracket_breakdown=[],
            nonrefundable_credits=Decimal("0"),
            refundable_credits=Decimal("0"),
            total_credits=Decimal("0"),
            credit_details=[],
            net_tax=Decimal("0"),
            withholding=Decimal("0"),
            estimated_payments=Decimal("0"),
            credits_for_other_states=Decimal("0"),
            amount_owed=Decimal("0"),
            refund_amount=Decimal("0"),
            marginal_rate=Decimal("0"),
            effective_rate=Decimal("0")
        )

        primary_form = StateForm(
            form_id="None",
            title=f"{state.value} - No Income Tax",
            tax_year=tax_year,
            state=state,
            lines=[]
        )

        return StateReturn(
            state=state,
            tax_year=tax_year,
            residency_status=ResidencyStatus.FULL_YEAR_RESIDENT,
            filing_status=filing_status,
            primary_form=primary_form,
            schedules=[],
            attachments=[],
            calculation=calculation,
            credits=[],
            deductions=[]
        )

    # Utility methods

    def _get_decimal(self, facts: Dict, *keys: str) -> Decimal:
        """Get a decimal value from facts, trying multiple keys."""
        for key in keys:
            val = facts.get(key)
            if val is not None:
                try:
                    return Decimal(str(val))
                except (ValueError, TypeError):
                    pass
        return Decimal("0")

    def get_supported_states(self) -> List[StateCode]:
        """Get list of states with income tax."""
        return [s for s in StateCode if s not in self.NO_INCOME_TAX_STATES]

    def get_state_form_info(self, state: StateCode) -> Dict[str, Any]:
        """Get form information for a state."""
        return self.STATE_FORMS.get(state, {
            "resident": "State Form",
            "schedules": []
        })

    def validate_state_return(self, state_return: StateReturn) -> List[str]:
        """Validate a state return for common errors.

        Args:
            state_return: State return to validate.

        Returns:
            List of validation error messages.
        """
        errors = []
        calc = state_return.calculation

        # Check for negative values that shouldn't be negative
        if calc.state_taxable_income < 0:
            errors.append("State taxable income cannot be negative")

        if calc.tax_before_credits < 0:
            errors.append("Tax before credits cannot be negative")

        # Verify math
        expected_agi = calc.federal_agi + calc.state_additions - calc.state_subtractions
        if abs(expected_agi - calc.state_agi) > Decimal("0.01"):
            errors.append("State AGI calculation error")

        # Check payment reconciliation
        total_payments = calc.withholding + calc.estimated_payments
        if calc.amount_owed > 0 and calc.refund_amount > 0:
            errors.append("Cannot have both amount owed and refund")

        return errors
