"""FastAPI routes for State Tax Forms API."""

from decimal import Decimal
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..services.state_forms_service import (
    StateFormsService,
    StateCode,
    FilingStatus,
    ResidencyStatus,
    StateReturn,
    StateTaxCalculation,
    StateCredit,
    StateDeduction,
    MultiStateAllocation,
    StateTaxBracket,
    StateForm,
    StateFormLine,
    StateSchedule,
)

router = APIRouter(prefix="/v1/state", tags=["State Tax Forms"])

# Initialize the service
service = StateFormsService()


# ============================================================================
# Pydantic Request/Response Models
# ============================================================================


class StateFormLineModel(BaseModel):
    """A single line item on a state tax form."""
    line_number: str
    description: str
    value: float
    source: Optional[str] = None
    notes: Optional[str] = None


class StateScheduleModel(BaseModel):
    """A state tax schedule attachment."""
    schedule_id: str
    title: str
    lines: List[StateFormLineModel] = []
    total: float = 0


class StateFormModel(BaseModel):
    """A state tax form with line-by-line breakdown."""
    form_id: str
    title: str
    tax_year: int
    state: str
    lines: List[StateFormLineModel] = []
    schedules: List[StateScheduleModel] = []


class StateCreditModel(BaseModel):
    """A state tax credit."""
    credit_id: str
    name: str
    amount: float
    refundable: bool = False
    carryforward_years: int = 0
    form_reference: Optional[str] = None


class StateDeductionModel(BaseModel):
    """A state-specific deduction."""
    deduction_id: str
    name: str
    amount: float
    category: str
    source: Optional[str] = None


class TaxBracketBreakdownModel(BaseModel):
    """Tax bracket breakdown detail."""
    rate: float
    income_in_bracket: float
    tax: float
    min: float
    max: Optional[float] = None


class StateTaxCalculationModel(BaseModel):
    """Complete state tax calculation breakdown."""
    # Income
    federal_agi: float
    state_additions: float
    state_subtractions: float
    state_agi: float

    # Deductions
    standard_deduction: float
    itemized_deduction: float
    deduction_used: str
    total_deduction: float
    exemptions: float

    # Taxable Income
    state_taxable_income: float

    # Tax
    tax_before_credits: float
    tax_bracket_breakdown: List[TaxBracketBreakdownModel]

    # Credits
    nonrefundable_credits: float
    refundable_credits: float
    total_credits: float
    credit_details: List[StateCreditModel]

    # Final
    net_tax: float
    withholding: float
    estimated_payments: float
    credits_for_other_states: float
    amount_owed: float
    refund_amount: float

    # Rates
    marginal_rate: float
    effective_rate: float


class MultiStateAllocationModel(BaseModel):
    """Income allocation for multi-state filing."""
    state: str
    allocation_percentage: float
    days_resident: int
    income_sourced: float
    wage_allocation: float
    business_allocation: float
    investment_allocation: float


class StateReturnModel(BaseModel):
    """Complete state tax return."""
    state: str
    tax_year: int
    residency_status: str
    filing_status: str
    primary_form: StateFormModel
    schedules: List[StateScheduleModel]
    attachments: List[StateFormModel]
    calculation: StateTaxCalculationModel
    multi_state_info: Optional[MultiStateAllocationModel] = None
    credits: List[StateCreditModel] = []
    deductions: List[StateDeductionModel] = []
    payment_info: Dict[str, Any] = {}


# Request Models

class GenerateStateReturnRequest(BaseModel):
    """Request to generate a state tax return from federal data."""
    state_code: str = Field(..., description="Two-letter state code (e.g., 'CA', 'NY')")
    federal_return: Dict[str, Any] = Field(..., description="Federal return data (facts dictionary)")
    filing_status: str = Field(..., description="Filing status: single, mfj, mfs, hoh, qss")
    residency_status: str = Field(
        default="full_year_resident",
        description="Residency: full_year_resident, part_year_resident, non_resident"
    )
    multi_state_info: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Multi-state filing information if applicable"
    )
    tax_year: int = Field(default=2025, description="Tax year")


class CalculateStateTaxRequest(BaseModel):
    """Request to calculate state tax liability."""
    state_code: str = Field(..., description="Two-letter state code")
    federal_return: Dict[str, Any] = Field(..., description="Federal return data")
    filing_status: str = Field(..., description="Filing status")
    residency_status: str = Field(default="full_year_resident", description="Residency status")
    multi_state_info: Optional[Dict[str, Any]] = None


class MultiStateRequest(BaseModel):
    """Request for multi-state filing allocation."""
    states: List[Dict[str, Any]] = Field(
        ...,
        description="List of states with days, work_percentage, business_percentage"
    )
    federal_return: Dict[str, Any] = Field(..., description="Federal return data")
    tax_year: int = Field(default=2025, description="Tax year")


class ValidateStateReturnRequest(BaseModel):
    """Request to validate a state return."""
    state_return: StateReturnModel = Field(..., description="State return to validate")


# Response Models

class SupportedStatesResponse(BaseModel):
    """Response listing states with income tax."""
    states: List[Dict[str, str]] = Field(
        ...,
        description="List of states with code and name"
    )
    no_income_tax_states: List[Dict[str, str]] = Field(
        ...,
        description="States without income tax"
    )


class StateInfoResponse(BaseModel):
    """Response with state form information."""
    state_code: str
    state_name: str
    forms: Dict[str, Any]
    has_income_tax: bool
    tax_type: str = Field(description="graduated, flat, or none")
    filing_deadline: str
    extension_deadline: str
    estimated_payment_dates: List[str]


class TaxBracketModel(BaseModel):
    """A state tax bracket."""
    rate: float
    min_income: float
    max_income: Optional[float] = None


class StateBracketsResponse(BaseModel):
    """Response with tax brackets for a state."""
    state_code: str
    state_name: str
    tax_year: int
    tax_type: str
    brackets_by_filing_status: Dict[str, List[TaxBracketModel]]


class StateCreditsResponse(BaseModel):
    """Response with available credits for a state."""
    state_code: str
    state_name: str
    available_credits: List[Dict[str, Any]]


class GenerateStateReturnResponse(BaseModel):
    """Response containing the generated state return."""
    state_return: StateReturnModel
    warnings: List[str] = []
    info: Dict[str, Any] = {}


class CalculateStateTaxResponse(BaseModel):
    """Response with state tax calculation."""
    calculation: StateTaxCalculationModel
    summary: Dict[str, Any]


class MultiStateResponse(BaseModel):
    """Response with multi-state allocation."""
    allocations: List[MultiStateAllocationModel]
    total_income_allocated: float
    warnings: List[str] = []


class ValidateStateReturnResponse(BaseModel):
    """Response with validation results."""
    is_valid: bool
    errors: List[str] = []
    warnings: List[str] = []


# ============================================================================
# Conversion Helpers
# ============================================================================


def _decimal_to_float(val: Decimal) -> float:
    """Convert Decimal to float for JSON serialization."""
    return float(val)


def _state_form_line_to_model(line: StateFormLine) -> StateFormLineModel:
    """Convert StateFormLine to Pydantic model."""
    return StateFormLineModel(
        line_number=line.line_number,
        description=line.description,
        value=_decimal_to_float(line.value),
        source=line.source,
        notes=line.notes
    )


def _state_schedule_to_model(schedule: StateSchedule) -> StateScheduleModel:
    """Convert StateSchedule to Pydantic model."""
    return StateScheduleModel(
        schedule_id=schedule.schedule_id,
        title=schedule.title,
        lines=[_state_form_line_to_model(line) for line in schedule.lines],
        total=_decimal_to_float(schedule.total)
    )


def _state_form_to_model(form: StateForm) -> StateFormModel:
    """Convert StateForm to Pydantic model."""
    return StateFormModel(
        form_id=form.form_id,
        title=form.title,
        tax_year=form.tax_year,
        state=form.state.value,
        lines=[_state_form_line_to_model(line) for line in form.lines],
        schedules=[_state_schedule_to_model(s) for s in form.schedules]
    )


def _state_credit_to_model(credit: StateCredit) -> StateCreditModel:
    """Convert StateCredit to Pydantic model."""
    return StateCreditModel(
        credit_id=credit.credit_id,
        name=credit.name,
        amount=_decimal_to_float(credit.amount),
        refundable=credit.refundable,
        carryforward_years=credit.carryforward_years,
        form_reference=credit.form_reference
    )


def _state_deduction_to_model(deduction: StateDeduction) -> StateDeductionModel:
    """Convert StateDeduction to Pydantic model."""
    return StateDeductionModel(
        deduction_id=deduction.deduction_id,
        name=deduction.name,
        amount=_decimal_to_float(deduction.amount),
        category=deduction.category,
        source=deduction.source
    )


def _multi_state_allocation_to_model(allocation: MultiStateAllocation) -> MultiStateAllocationModel:
    """Convert MultiStateAllocation to Pydantic model."""
    return MultiStateAllocationModel(
        state=allocation.state.value,
        allocation_percentage=_decimal_to_float(allocation.allocation_percentage),
        days_resident=allocation.days_resident,
        income_sourced=_decimal_to_float(allocation.income_sourced),
        wage_allocation=_decimal_to_float(allocation.wage_allocation),
        business_allocation=_decimal_to_float(allocation.business_allocation),
        investment_allocation=_decimal_to_float(allocation.investment_allocation)
    )


def _bracket_breakdown_to_model(breakdown: Dict[str, Any]) -> TaxBracketBreakdownModel:
    """Convert bracket breakdown dict to Pydantic model."""
    return TaxBracketBreakdownModel(
        rate=breakdown["rate"],
        income_in_bracket=breakdown["income_in_bracket"],
        tax=breakdown["tax"],
        min=breakdown["min"],
        max=breakdown.get("max")
    )


def _calculation_to_model(calc: StateTaxCalculation) -> StateTaxCalculationModel:
    """Convert StateTaxCalculation to Pydantic model."""
    return StateTaxCalculationModel(
        federal_agi=_decimal_to_float(calc.federal_agi),
        state_additions=_decimal_to_float(calc.state_additions),
        state_subtractions=_decimal_to_float(calc.state_subtractions),
        state_agi=_decimal_to_float(calc.state_agi),
        standard_deduction=_decimal_to_float(calc.standard_deduction),
        itemized_deduction=_decimal_to_float(calc.itemized_deduction),
        deduction_used=calc.deduction_used,
        total_deduction=_decimal_to_float(calc.total_deduction),
        exemptions=_decimal_to_float(calc.exemptions),
        state_taxable_income=_decimal_to_float(calc.state_taxable_income),
        tax_before_credits=_decimal_to_float(calc.tax_before_credits),
        tax_bracket_breakdown=[_bracket_breakdown_to_model(b) for b in calc.tax_bracket_breakdown],
        nonrefundable_credits=_decimal_to_float(calc.nonrefundable_credits),
        refundable_credits=_decimal_to_float(calc.refundable_credits),
        total_credits=_decimal_to_float(calc.total_credits),
        credit_details=[_state_credit_to_model(c) for c in calc.credit_details],
        net_tax=_decimal_to_float(calc.net_tax),
        withholding=_decimal_to_float(calc.withholding),
        estimated_payments=_decimal_to_float(calc.estimated_payments),
        credits_for_other_states=_decimal_to_float(calc.credits_for_other_states),
        amount_owed=_decimal_to_float(calc.amount_owed),
        refund_amount=_decimal_to_float(calc.refund_amount),
        marginal_rate=_decimal_to_float(calc.marginal_rate),
        effective_rate=_decimal_to_float(calc.effective_rate)
    )


def _state_return_to_model(state_return: StateReturn) -> StateReturnModel:
    """Convert StateReturn to Pydantic model."""
    return StateReturnModel(
        state=state_return.state.value,
        tax_year=state_return.tax_year,
        residency_status=state_return.residency_status.value,
        filing_status=state_return.filing_status.value,
        primary_form=_state_form_to_model(state_return.primary_form),
        schedules=[_state_schedule_to_model(s) for s in state_return.schedules],
        attachments=[_state_form_to_model(f) for f in state_return.attachments],
        calculation=_calculation_to_model(state_return.calculation),
        multi_state_info=(
            _multi_state_allocation_to_model(state_return.multi_state_info)
            if state_return.multi_state_info else None
        ),
        credits=[_state_credit_to_model(c) for c in state_return.credits],
        deductions=[_state_deduction_to_model(d) for d in state_return.deductions],
        payment_info=state_return.payment_info
    )


def _parse_filing_status(status: str) -> FilingStatus:
    """Parse filing status string to enum."""
    status_map = {
        "single": FilingStatus.SINGLE,
        "mfj": FilingStatus.MARRIED_FILING_JOINTLY,
        "married_filing_jointly": FilingStatus.MARRIED_FILING_JOINTLY,
        "mfs": FilingStatus.MARRIED_FILING_SEPARATELY,
        "married_filing_separately": FilingStatus.MARRIED_FILING_SEPARATELY,
        "hoh": FilingStatus.HEAD_OF_HOUSEHOLD,
        "head_of_household": FilingStatus.HEAD_OF_HOUSEHOLD,
        "qss": FilingStatus.QUALIFYING_SURVIVING_SPOUSE,
        "qualifying_surviving_spouse": FilingStatus.QUALIFYING_SURVIVING_SPOUSE,
    }
    status_lower = status.lower().replace("-", "_").replace(" ", "_")
    if status_lower not in status_map:
        raise ValueError(f"Invalid filing status: {status}")
    return status_map[status_lower]


def _parse_residency_status(status: str) -> ResidencyStatus:
    """Parse residency status string to enum."""
    status_map = {
        "full_year_resident": ResidencyStatus.FULL_YEAR_RESIDENT,
        "part_year_resident": ResidencyStatus.PART_YEAR_RESIDENT,
        "non_resident": ResidencyStatus.NON_RESIDENT,
    }
    status_lower = status.lower().replace("-", "_").replace(" ", "_")
    if status_lower not in status_map:
        raise ValueError(f"Invalid residency status: {status}")
    return status_map[status_lower]


def _parse_state_code(code: str) -> StateCode:
    """Parse state code string to enum."""
    code_upper = code.upper().strip()
    try:
        return StateCode(code_upper)
    except ValueError:
        raise ValueError(f"Invalid state code: {code}")


# ============================================================================
# State name mapping
# ============================================================================

STATE_NAMES = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas",
    "CA": "California", "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware",
    "FL": "Florida", "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho",
    "IL": "Illinois", "IN": "Indiana", "IA": "Iowa", "KS": "Kansas",
    "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
    "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi",
    "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada",
    "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York",
    "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma",
    "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina",
    "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah",
    "VT": "Vermont", "VA": "Virginia", "WA": "Washington", "WV": "West Virginia",
    "WI": "Wisconsin", "WY": "Wyoming", "DC": "District of Columbia"
}


# ============================================================================
# Route Implementations
# ============================================================================


@router.post("/generate", response_model=GenerateStateReturnResponse)
async def generate_state_return(request: GenerateStateReturnRequest):
    """Generate a state tax return from federal return data.

    Creates a complete state tax return with forms, schedules, and calculations
    based on the federal return data provided.

    Args:
        request: Generation request with state, federal data, and filing info.

    Returns:
        Complete state return with forms and calculations.
    """
    try:
        state_code = _parse_state_code(request.state_code)
        filing_status = _parse_filing_status(request.filing_status)
        residency_status = _parse_residency_status(request.residency_status)

        state_return = service.generate_state_return(
            state=state_code,
            federal_return=request.federal_return,
            filing_status=filing_status,
            residency_status=residency_status,
            multi_state_info=request.multi_state_info,
            tax_year=request.tax_year
        )

        warnings = []
        if state_code in service.NO_INCOME_TAX_STATES:
            warnings.append(f"{STATE_NAMES.get(request.state_code, request.state_code)} has no state income tax.")

        return GenerateStateReturnResponse(
            state_return=_state_return_to_model(state_return),
            warnings=warnings,
            info={
                "state_name": STATE_NAMES.get(request.state_code, request.state_code),
                "has_income_tax": state_code not in service.NO_INCOME_TAX_STATES
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/supported", response_model=SupportedStatesResponse)
async def get_supported_states():
    """List states with income tax.

    Returns two lists: states with income tax and states without income tax.

    Returns:
        Lists of states organized by income tax status.
    """
    try:
        supported = service.get_supported_states()
        no_tax = service.NO_INCOME_TAX_STATES

        return SupportedStatesResponse(
            states=[
                {"code": s.value, "name": STATE_NAMES.get(s.value, s.value)}
                for s in supported
            ],
            no_income_tax_states=[
                {"code": s.value, "name": STATE_NAMES.get(s.value, s.value)}
                for s in no_tax
            ]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{state_code}/info", response_model=StateInfoResponse)
async def get_state_info(state_code: str):
    """Get state tax form information.

    Returns information about available forms, tax rates, and filing deadlines
    for the specified state.

    Args:
        state_code: Two-letter state code (e.g., 'CA', 'NY').

    Returns:
        State form information, rates, and deadlines.
    """
    try:
        state = _parse_state_code(state_code)
        form_info = service.get_state_form_info(state)
        has_income_tax = state not in service.NO_INCOME_TAX_STATES

        # Determine tax type
        tax_type = "none"
        if has_income_tax:
            brackets = service.STATE_BRACKETS_2025.get(state, {})
            if brackets:
                single_brackets = brackets.get(FilingStatus.SINGLE, [])
                if len(single_brackets) == 1:
                    tax_type = "flat"
                else:
                    tax_type = "graduated"

        return StateInfoResponse(
            state_code=state.value,
            state_name=STATE_NAMES.get(state.value, state.value),
            forms=form_info,
            has_income_tax=has_income_tax,
            tax_type=tax_type,
            filing_deadline="April 15, 2026",  # 2025 tax year
            extension_deadline="October 15, 2026",
            estimated_payment_dates=[
                "April 15, 2025",
                "June 15, 2025",
                "September 15, 2025",
                "January 15, 2026"
            ]
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/calculate", response_model=CalculateStateTaxResponse)
async def calculate_state_tax(request: CalculateStateTaxRequest):
    """Calculate state tax liability.

    Calculates the complete state tax liability including AGI adjustments,
    deductions, credits, and final tax owed or refund.

    Args:
        request: Calculation request with state and federal data.

    Returns:
        Complete tax calculation with breakdown.
    """
    try:
        state_code = _parse_state_code(request.state_code)
        filing_status = _parse_filing_status(request.filing_status)
        residency_status = _parse_residency_status(request.residency_status)

        # Generate full return to get calculation
        state_return = service.generate_state_return(
            state=state_code,
            federal_return=request.federal_return,
            filing_status=filing_status,
            residency_status=residency_status,
            multi_state_info=request.multi_state_info,
            tax_year=2025
        )

        calc = state_return.calculation
        calc_model = _calculation_to_model(calc)

        summary = {
            "state": state_code.value,
            "state_name": STATE_NAMES.get(state_code.value, state_code.value),
            "federal_agi": calc_model.federal_agi,
            "state_taxable_income": calc_model.state_taxable_income,
            "tax_before_credits": calc_model.tax_before_credits,
            "total_credits": calc_model.total_credits,
            "net_tax": calc_model.net_tax,
            "amount_owed": calc_model.amount_owed,
            "refund_amount": calc_model.refund_amount,
            "marginal_rate": f"{calc_model.marginal_rate:.2f}%",
            "effective_rate": f"{calc_model.effective_rate:.2f}%"
        }

        return CalculateStateTaxResponse(
            calculation=calc_model,
            summary=summary
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{state_code}/credits", response_model=StateCreditsResponse)
async def get_state_credits(state_code: str):
    """Get available credits for a state.

    Returns information about tax credits available in the specified state,
    including eligibility requirements and whether they are refundable.

    Args:
        state_code: Two-letter state code.

    Returns:
        List of available credits with details.
    """
    try:
        state = _parse_state_code(state_code)

        # Define available credits by state
        credits_by_state = {
            StateCode.CA: [
                {
                    "credit_id": "caleitc",
                    "name": "California Earned Income Tax Credit (CalEITC)",
                    "description": "Refundable credit for low-income workers",
                    "refundable": True,
                    "max_amount": 3529,
                    "form": "FTB 3514"
                },
                {
                    "credit_id": "yctc",
                    "name": "Young Child Tax Credit",
                    "description": "Credit for families with children under 6",
                    "refundable": True,
                    "max_amount": 1117,
                    "form": "FTB 3514"
                },
                {
                    "credit_id": "renter",
                    "name": "Renter's Credit",
                    "description": "Credit for qualified renters",
                    "refundable": True,
                    "max_amount": 120,
                    "form": "Form 540"
                }
            ],
            StateCode.NY: [
                {
                    "credit_id": "nyeitc",
                    "name": "New York State Earned Income Credit",
                    "description": "30% of federal EITC",
                    "refundable": True,
                    "form": "IT-215"
                },
                {
                    "credit_id": "escc",
                    "name": "Empire State Child Credit",
                    "description": "Credit for qualifying children",
                    "refundable": True,
                    "max_amount": 330,
                    "form": "IT-213"
                },
                {
                    "credit_id": "star",
                    "name": "STAR Property Tax Credit",
                    "description": "School tax relief credit",
                    "refundable": True,
                    "form": "IT-214"
                },
                {
                    "credit_id": "college_tuition",
                    "name": "College Tuition Credit",
                    "description": "Credit for undergraduate tuition",
                    "refundable": False,
                    "max_amount": 400,
                    "form": "IT-272"
                }
            ],
            StateCode.IL: [
                {
                    "credit_id": "ileitc",
                    "name": "Illinois Earned Income Credit",
                    "description": "20% of federal EITC",
                    "refundable": True,
                    "form": "Schedule IL-E/EIC"
                },
                {
                    "credit_id": "property_tax",
                    "name": "Property Tax Credit",
                    "description": "5% of property taxes paid",
                    "refundable": False,
                    "form": "Schedule ICR"
                }
            ],
            StateCode.MA: [
                {
                    "credit_id": "maeitc",
                    "name": "Massachusetts Earned Income Credit",
                    "description": "40% of federal EITC",
                    "refundable": True,
                    "form": "Schedule EITC"
                },
                {
                    "credit_id": "circuit_breaker",
                    "name": "Senior Circuit Breaker Credit",
                    "description": "Property tax credit for seniors",
                    "refundable": True,
                    "max_amount": 2590,
                    "form": "Schedule CB"
                },
                {
                    "credit_id": "dependent_care",
                    "name": "Dependent Care Credit",
                    "description": "Credit for dependent care expenses",
                    "refundable": False,
                    "form": "Schedule DC"
                }
            ],
            StateCode.NJ: [
                {
                    "credit_id": "njeitc",
                    "name": "New Jersey Earned Income Tax Credit",
                    "description": "40% of federal EITC",
                    "refundable": True,
                    "form": "NJ-1040"
                },
                {
                    "credit_id": "child_tax_credit",
                    "name": "Child Tax Credit",
                    "description": "$500 per child under 6",
                    "refundable": True,
                    "max_amount": 500,
                    "form": "NJ-1040"
                },
                {
                    "credit_id": "homestead",
                    "name": "Homestead Benefit",
                    "description": "Property tax relief",
                    "refundable": True,
                    "form": "Separate application"
                }
            ],
            StateCode.PA: [
                {
                    "credit_id": "special_tax_forgiveness",
                    "name": "Special Tax Forgiveness",
                    "description": "Tax forgiveness for low-income filers",
                    "refundable": True,
                    "form": "PA Schedule SP"
                },
                {
                    "credit_id": "rent_rebate",
                    "name": "Property Tax/Rent Rebate",
                    "description": "Rebate for seniors and disabled",
                    "refundable": True,
                    "max_amount": 650,
                    "form": "PA-1000"
                }
            ]
        }

        available = credits_by_state.get(state, [])

        return StateCreditsResponse(
            state_code=state.value,
            state_name=STATE_NAMES.get(state.value, state.value),
            available_credits=available
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/multi-state", response_model=MultiStateResponse)
async def handle_multi_state_filing(request: MultiStateRequest):
    """Handle multi-state filing income allocation.

    Calculates how income should be allocated across multiple states
    for taxpayers who lived or worked in multiple states during the year.

    Args:
        request: Multi-state request with state residency information.

    Returns:
        Income allocation for each state.
    """
    try:
        allocations = service.calculate_multi_state_allocation(
            states=request.states,
            federal_return=request.federal_return,
            tax_year=request.tax_year
        )

        allocation_models = [_multi_state_allocation_to_model(a) for a in allocations]
        total_allocated = sum(a.income_sourced for a in allocation_models)

        warnings = []
        total_pct = sum(a.allocation_percentage for a in allocation_models)
        if abs(total_pct - 1.0) > 0.01:
            warnings.append(
                f"Total allocation percentage is {total_pct:.1%}, which differs from 100%."
            )

        return MultiStateResponse(
            allocations=allocation_models,
            total_income_allocated=total_allocated,
            warnings=warnings
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate", response_model=ValidateStateReturnResponse)
async def validate_state_return(request: ValidateStateReturnRequest):
    """Validate a state tax return.

    Checks the state return for common errors and inconsistencies
    in calculations and required fields.

    Args:
        request: Validation request with state return to validate.

    Returns:
        Validation results with any errors or warnings.
    """
    try:
        # Convert Pydantic model back to dataclass for validation
        # We'll do simplified validation on the model directly
        state_return = request.state_return
        errors = []
        warnings = []

        calc = state_return.calculation

        # Check for negative values that shouldn't be negative
        if calc.state_taxable_income < 0:
            errors.append("State taxable income cannot be negative")

        if calc.tax_before_credits < 0:
            errors.append("Tax before credits cannot be negative")

        # Verify AGI calculation
        expected_agi = calc.federal_agi + calc.state_additions - calc.state_subtractions
        if abs(expected_agi - calc.state_agi) > 0.01:
            errors.append("State AGI calculation error: expected {:.2f}, got {:.2f}".format(
                expected_agi, calc.state_agi
            ))

        # Check payment reconciliation
        if calc.amount_owed > 0 and calc.refund_amount > 0:
            errors.append("Cannot have both amount owed and refund")

        # Check deduction used
        if calc.deduction_used not in ["standard", "itemized", "none"]:
            errors.append(f"Invalid deduction type: {calc.deduction_used}")

        # Check rates
        if calc.marginal_rate < 0 or calc.marginal_rate > 100:
            warnings.append(f"Marginal rate {calc.marginal_rate}% seems incorrect")

        if calc.effective_rate < 0 or calc.effective_rate > 100:
            warnings.append(f"Effective rate {calc.effective_rate}% seems incorrect")

        # Check form has lines
        if not state_return.primary_form.lines and state_return.calculation.state_agi > 0:
            warnings.append("Primary form has no line items")

        return ValidateStateReturnResponse(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{state_code}/brackets", response_model=StateBracketsResponse)
async def get_state_brackets(state_code: str):
    """Get tax brackets for a state.

    Returns the income tax brackets for all filing statuses
    in the specified state.

    Args:
        state_code: Two-letter state code.

    Returns:
        Tax brackets organized by filing status.
    """
    try:
        state = _parse_state_code(state_code)
        brackets = service.STATE_BRACKETS_2025.get(state, {})

        has_income_tax = state not in service.NO_INCOME_TAX_STATES
        if not has_income_tax:
            return StateBracketsResponse(
                state_code=state.value,
                state_name=STATE_NAMES.get(state.value, state.value),
                tax_year=2025,
                tax_type="none",
                brackets_by_filing_status={}
            )

        # Determine tax type
        tax_type = "graduated"
        sample_brackets = brackets.get(FilingStatus.SINGLE, [])
        if len(sample_brackets) == 1:
            tax_type = "flat"

        # Convert brackets to response format
        brackets_by_status = {}
        for filing_status, bracket_list in brackets.items():
            status_key = filing_status.value
            brackets_by_status[status_key] = [
                TaxBracketModel(
                    rate=_decimal_to_float(b.rate * 100),
                    min_income=_decimal_to_float(b.min_income),
                    max_income=_decimal_to_float(b.max_income) if b.max_income else None
                )
                for b in bracket_list
            ]

        return StateBracketsResponse(
            state_code=state.value,
            state_name=STATE_NAMES.get(state.value, state.value),
            tax_year=2025,
            tax_type=tax_type,
            brackets_by_filing_status=brackets_by_status
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
