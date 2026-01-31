"""Interview Wizard Service.

Provides a conversational interview flow with 40+ questions,
conditional branching, and skip logic based on user responses.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Union
import json


class QuestionType(Enum):
    """Types of interview questions."""
    YES_NO = "yes_no"
    SINGLE_CHOICE = "single_choice"
    MULTIPLE_CHOICE = "multiple_choice"
    TEXT = "text"
    NUMBER = "number"
    CURRENCY = "currency"
    DATE = "date"
    SSN = "ssn"
    PHONE = "phone"
    EMAIL = "email"
    ADDRESS = "address"
    EIN = "ein"


class QuestionCategory(Enum):
    """Question categories for organization."""
    PERSONAL_INFO = "personal_info"
    FILING_STATUS = "filing_status"
    DEPENDENTS = "dependents"
    INCOME_WAGES = "income_wages"
    INCOME_INTEREST = "income_interest"
    INCOME_DIVIDENDS = "income_dividends"
    INCOME_BUSINESS = "income_business"
    INCOME_INVESTMENTS = "income_investments"
    INCOME_RETIREMENT = "income_retirement"
    INCOME_OTHER = "income_other"
    DEDUCTIONS = "deductions"
    CREDITS = "credits"
    HEALTHCARE = "healthcare"
    STATE_LOCAL = "state_local"
    BANK_INFO = "bank_info"
    REVIEW = "review"


@dataclass
class QuestionOption:
    """Option for single/multiple choice questions."""
    value: str
    label: str
    description: Optional[str] = None
    icon: Optional[str] = None  # emoji or icon name


@dataclass
class ValidationRule:
    """Validation rule for question answers."""
    rule_type: str  # 'required', 'min', 'max', 'pattern', 'custom'
    value: Any = None
    error_message: str = ""


@dataclass
class Question:
    """An interview question."""
    id: str
    question_type: QuestionType
    category: QuestionCategory
    text: str
    help_text: Optional[str] = None
    options: List[QuestionOption] = field(default_factory=list)
    validations: List[ValidationRule] = field(default_factory=list)
    default_value: Any = None
    fact_path: Optional[str] = None  # Maps to fact dictionary path
    depends_on: Optional[str] = None  # Question ID this depends on
    show_if: Optional[str] = None  # Expression for conditional display
    skip_if: Optional[str] = None  # Expression for skip logic
    follow_up_questions: List[str] = field(default_factory=list)  # Question IDs


@dataclass
class InterviewState:
    """Current state of the interview."""
    current_question_id: str
    answers: Dict[str, Any]
    completed_questions: Set[str]
    skipped_questions: Set[str]
    question_history: List[str]  # For back navigation
    errors: Dict[str, str]
    is_complete: bool = False


@dataclass
class InterviewProgress:
    """Progress through the interview."""
    total_questions: int
    answered_questions: int
    skipped_questions: int
    current_category: str
    categories_complete: Dict[str, bool]
    percent_complete: float


class InterviewWizardService:
    """Service for managing tax interview flow."""

    def __init__(self):
        self.questions: Dict[str, Question] = {}
        self.question_order: List[str] = []
        self._build_questions()

    def _build_questions(self):
        """Build the complete question set."""

        # ============ Personal Information ============
        self._add_question(Question(
            id="welcome",
            question_type=QuestionType.SINGLE_CHOICE,
            category=QuestionCategory.PERSONAL_INFO,
            text="Welcome! Let's start your tax return. Have you filed a tax return before?",
            help_text="If you've filed before, we can import information from last year.",
            options=[
                QuestionOption("yes_import", "Yes, import from last year"),
                QuestionOption("yes_new", "Yes, but start fresh"),
                QuestionOption("no", "No, this is my first time")
            ],
            fact_path="/hasPriorReturn"
        ))

        self._add_question(Question(
            id="first_name",
            question_type=QuestionType.TEXT,
            category=QuestionCategory.PERSONAL_INFO,
            text="What is your first name?",
            help_text="Enter your first name exactly as it appears on your Social Security card.",
            validations=[
                ValidationRule("required", error_message="First name is required"),
                ValidationRule("pattern", r"^[A-Za-z\-\s]+$", "Name can only contain letters, spaces, and hyphens")
            ],
            fact_path="/primaryFirstName"
        ))

        self._add_question(Question(
            id="middle_initial",
            question_type=QuestionType.TEXT,
            category=QuestionCategory.PERSONAL_INFO,
            text="What is your middle initial? (optional)",
            fact_path="/primaryMiddleInitial"
        ))

        self._add_question(Question(
            id="last_name",
            question_type=QuestionType.TEXT,
            category=QuestionCategory.PERSONAL_INFO,
            text="What is your last name?",
            validations=[ValidationRule("required", error_message="Last name is required")],
            fact_path="/primaryLastName"
        ))

        self._add_question(Question(
            id="ssn",
            question_type=QuestionType.SSN,
            category=QuestionCategory.PERSONAL_INFO,
            text="What is your Social Security Number?",
            help_text="Your SSN is required for tax filing and is kept secure.",
            validations=[ValidationRule("required", error_message="SSN is required")],
            fact_path="/primarySSN"
        ))

        self._add_question(Question(
            id="date_of_birth",
            question_type=QuestionType.DATE,
            category=QuestionCategory.PERSONAL_INFO,
            text="What is your date of birth?",
            validations=[ValidationRule("required", error_message="Date of birth is required")],
            fact_path="/primaryDateOfBirth"
        ))

        self._add_question(Question(
            id="phone",
            question_type=QuestionType.PHONE,
            category=QuestionCategory.PERSONAL_INFO,
            text="What is your phone number?",
            fact_path="/primaryPhone"
        ))

        self._add_question(Question(
            id="email",
            question_type=QuestionType.EMAIL,
            category=QuestionCategory.PERSONAL_INFO,
            text="What is your email address?",
            help_text="We'll send you updates about your tax return status.",
            fact_path="/primaryEmail"
        ))

        self._add_question(Question(
            id="address",
            question_type=QuestionType.ADDRESS,
            category=QuestionCategory.PERSONAL_INFO,
            text="What is your current mailing address?",
            validations=[ValidationRule("required", error_message="Address is required")],
            fact_path="/address"
        ))

        # ============ Filing Status ============
        self._add_question(Question(
            id="filing_status",
            question_type=QuestionType.SINGLE_CHOICE,
            category=QuestionCategory.FILING_STATUS,
            text="What is your filing status?",
            help_text="Your filing status affects your tax rates and standard deduction.",
            options=[
                QuestionOption("single", "Single", "Not married, divorced, or legally separated"),
                QuestionOption("mfj", "Married Filing Jointly", "Married and filing one return together"),
                QuestionOption("mfs", "Married Filing Separately", "Married but filing separate returns"),
                QuestionOption("hoh", "Head of Household", "Unmarried with a qualifying dependent"),
                QuestionOption("qss", "Qualifying Surviving Spouse", "Spouse died in 2024 or 2025 with dependent child")
            ],
            validations=[ValidationRule("required")],
            fact_path="/filingStatus"
        ))

        self._add_question(Question(
            id="spouse_info",
            question_type=QuestionType.YES_NO,
            category=QuestionCategory.FILING_STATUS,
            text="Now let's get your spouse's information.",
            show_if="filing_status in ['mfj', 'mfs']",
            follow_up_questions=["spouse_first_name", "spouse_last_name", "spouse_ssn", "spouse_dob"]
        ))

        self._add_question(Question(
            id="spouse_first_name",
            question_type=QuestionType.TEXT,
            category=QuestionCategory.FILING_STATUS,
            text="What is your spouse's first name?",
            show_if="filing_status in ['mfj', 'mfs']",
            validations=[ValidationRule("required")],
            fact_path="/spouseFirstName"
        ))

        self._add_question(Question(
            id="spouse_last_name",
            question_type=QuestionType.TEXT,
            category=QuestionCategory.FILING_STATUS,
            text="What is your spouse's last name?",
            show_if="filing_status in ['mfj', 'mfs']",
            validations=[ValidationRule("required")],
            fact_path="/spouseLastName"
        ))

        self._add_question(Question(
            id="spouse_ssn",
            question_type=QuestionType.SSN,
            category=QuestionCategory.FILING_STATUS,
            text="What is your spouse's Social Security Number?",
            show_if="filing_status in ['mfj', 'mfs']",
            validations=[ValidationRule("required")],
            fact_path="/spouseSSN"
        ))

        self._add_question(Question(
            id="spouse_dob",
            question_type=QuestionType.DATE,
            category=QuestionCategory.FILING_STATUS,
            text="What is your spouse's date of birth?",
            show_if="filing_status in ['mfj', 'mfs']",
            fact_path="/spouseDateOfBirth"
        ))

        # ============ Dependents ============
        self._add_question(Question(
            id="has_dependents",
            question_type=QuestionType.YES_NO,
            category=QuestionCategory.DEPENDENTS,
            text="Do you have any dependents to claim?",
            help_text="Dependents include children, relatives, or others who live with you and rely on you for support.",
            fact_path="/hasDependents",
            follow_up_questions=["how_many_dependents"]
        ))

        self._add_question(Question(
            id="how_many_dependents",
            question_type=QuestionType.NUMBER,
            category=QuestionCategory.DEPENDENTS,
            text="How many dependents do you have?",
            show_if="has_dependents == true",
            validations=[
                ValidationRule("min", 1),
                ValidationRule("max", 20)
            ],
            fact_path="/numberOfDependents"
        ))

        # Dynamic dependent questions would be generated based on count
        self._add_question(Question(
            id="dependent_under_17",
            question_type=QuestionType.NUMBER,
            category=QuestionCategory.DEPENDENTS,
            text="How many of your dependents were under 17 at the end of 2025?",
            help_text="Children under 17 may qualify for the Child Tax Credit.",
            show_if="has_dependents == true",
            fact_path="/dependentsUnder17"
        ))

        # ============ Income - Wages ============
        self._add_question(Question(
            id="had_job",
            question_type=QuestionType.YES_NO,
            category=QuestionCategory.INCOME_WAGES,
            text="Did you have a job or receive wages in 2025?",
            help_text="Include all W-2 income from employers.",
            fact_path="/hasWageIncome",
            follow_up_questions=["how_many_w2s"]
        ))

        self._add_question(Question(
            id="how_many_w2s",
            question_type=QuestionType.NUMBER,
            category=QuestionCategory.INCOME_WAGES,
            text="How many W-2 forms did you receive?",
            show_if="had_job == true",
            validations=[ValidationRule("min", 1), ValidationRule("max", 10)],
            fact_path="/numberOfW2s"
        ))

        self._add_question(Question(
            id="total_wages",
            question_type=QuestionType.CURRENCY,
            category=QuestionCategory.INCOME_WAGES,
            text="What is the total of all wages from Box 1 of your W-2(s)?",
            help_text="Add up Box 1 from all your W-2 forms.",
            show_if="had_job == true",
            fact_path="/totalW2Wages"
        ))

        self._add_question(Question(
            id="federal_withholding",
            question_type=QuestionType.CURRENCY,
            category=QuestionCategory.INCOME_WAGES,
            text="What is the total federal tax withheld from Box 2 of your W-2(s)?",
            show_if="had_job == true",
            fact_path="/federalWithholding"
        ))

        # ============ Income - Interest ============
        self._add_question(Question(
            id="had_interest",
            question_type=QuestionType.YES_NO,
            category=QuestionCategory.INCOME_INTEREST,
            text="Did you earn any interest income in 2025?",
            help_text="This includes interest from bank accounts, CDs, bonds, or 1099-INT forms.",
            fact_path="/hasInterestIncome"
        ))

        self._add_question(Question(
            id="interest_over_1500",
            question_type=QuestionType.YES_NO,
            category=QuestionCategory.INCOME_INTEREST,
            text="Was your total interest income over $1,500?",
            help_text="If over $1,500, you'll need to complete Schedule B.",
            show_if="had_interest == true",
            fact_path="/interestOver1500"
        ))

        self._add_question(Question(
            id="total_interest",
            question_type=QuestionType.CURRENCY,
            category=QuestionCategory.INCOME_INTEREST,
            text="What is your total taxable interest income?",
            show_if="had_interest == true",
            fact_path="/totalInterestIncome"
        ))

        # ============ Income - Dividends ============
        self._add_question(Question(
            id="had_dividends",
            question_type=QuestionType.YES_NO,
            category=QuestionCategory.INCOME_DIVIDENDS,
            text="Did you receive any dividend income in 2025?",
            help_text="This includes dividends from stocks, mutual funds, or 1099-DIV forms.",
            fact_path="/hasDividendIncome"
        ))

        self._add_question(Question(
            id="total_dividends",
            question_type=QuestionType.CURRENCY,
            category=QuestionCategory.INCOME_DIVIDENDS,
            text="What is your total ordinary dividends?",
            show_if="had_dividends == true",
            fact_path="/totalOrdinaryDividends"
        ))

        self._add_question(Question(
            id="qualified_dividends",
            question_type=QuestionType.CURRENCY,
            category=QuestionCategory.INCOME_DIVIDENDS,
            text="What is your total qualified dividends?",
            help_text="Qualified dividends are taxed at lower capital gains rates.",
            show_if="had_dividends == true",
            fact_path="/qualifiedDividends"
        ))

        # ============ Income - Self-Employment ============
        self._add_question(Question(
            id="had_self_employment",
            question_type=QuestionType.YES_NO,
            category=QuestionCategory.INCOME_BUSINESS,
            text="Did you have any self-employment or freelance income in 2025?",
            help_text="This includes 1099-NEC, 1099-MISC, or other self-employment income.",
            fact_path="/hasSelfEmploymentIncome"
        ))

        self._add_question(Question(
            id="self_employment_type",
            question_type=QuestionType.SINGLE_CHOICE,
            category=QuestionCategory.INCOME_BUSINESS,
            text="What type of self-employment did you have?",
            show_if="had_self_employment == true",
            options=[
                QuestionOption("sole_prop", "Sole Proprietorship / Freelance"),
                QuestionOption("llc_single", "Single-Member LLC"),
                QuestionOption("gig", "Gig Economy (Uber, Lyft, DoorDash, etc.)"),
                QuestionOption("side_business", "Side Business")
            ],
            fact_path="/selfEmploymentType"
        ))

        self._add_question(Question(
            id="gross_self_employment",
            question_type=QuestionType.CURRENCY,
            category=QuestionCategory.INCOME_BUSINESS,
            text="What was your gross self-employment income before expenses?",
            show_if="had_self_employment == true",
            fact_path="/grossSelfEmploymentIncome"
        ))

        self._add_question(Question(
            id="business_expenses",
            question_type=QuestionType.CURRENCY,
            category=QuestionCategory.INCOME_BUSINESS,
            text="What were your total business expenses?",
            help_text="Include supplies, equipment, advertising, home office, vehicle, etc.",
            show_if="had_self_employment == true",
            fact_path="/totalBusinessExpenses"
        ))

        # ============ Income - Investments ============
        self._add_question(Question(
            id="sold_investments",
            question_type=QuestionType.YES_NO,
            category=QuestionCategory.INCOME_INVESTMENTS,
            text="Did you sell any stocks, bonds, or other investments in 2025?",
            help_text="This includes sales from brokerage accounts, cryptocurrency, real estate, etc.",
            fact_path="/hasInvestmentSales"
        ))

        self._add_question(Question(
            id="investment_gain_or_loss",
            question_type=QuestionType.SINGLE_CHOICE,
            category=QuestionCategory.INCOME_INVESTMENTS,
            text="Overall, did you have a gain or loss from your investment sales?",
            show_if="sold_investments == true",
            options=[
                QuestionOption("gain", "Gain (made money)"),
                QuestionOption("loss", "Loss (lost money)"),
                QuestionOption("both", "Both gains and losses")
            ],
            fact_path="/investmentGainOrLoss"
        ))

        self._add_question(Question(
            id="has_crypto",
            question_type=QuestionType.YES_NO,
            category=QuestionCategory.INCOME_INVESTMENTS,
            text="Did you sell, exchange, or dispose of any cryptocurrency in 2025?",
            help_text="This includes Bitcoin, Ethereum, and other virtual currencies.",
            fact_path="/hasCryptocurrencyTransactions"
        ))

        # ============ Income - Retirement ============
        self._add_question(Question(
            id="had_retirement_income",
            question_type=QuestionType.YES_NO,
            category=QuestionCategory.INCOME_RETIREMENT,
            text="Did you receive any retirement income in 2025?",
            help_text="This includes pensions, IRA distributions, Social Security, etc.",
            fact_path="/hasRetirementIncome"
        ))

        self._add_question(Question(
            id="retirement_types",
            question_type=QuestionType.MULTIPLE_CHOICE,
            category=QuestionCategory.INCOME_RETIREMENT,
            text="What types of retirement income did you receive?",
            show_if="had_retirement_income == true",
            options=[
                QuestionOption("social_security", "Social Security"),
                QuestionOption("pension", "Pension"),
                QuestionOption("ira", "IRA Distribution"),
                QuestionOption("401k", "401(k) Distribution"),
                QuestionOption("annuity", "Annuity")
            ],
            fact_path="/retirementIncomeTypes"
        ))

        self._add_question(Question(
            id="social_security_amount",
            question_type=QuestionType.CURRENCY,
            category=QuestionCategory.INCOME_RETIREMENT,
            text="What was your total Social Security benefits (Box 5 of SSA-1099)?",
            show_if="'social_security' in retirement_types",
            fact_path="/totalSocialSecurityBenefits"
        ))

        # ============ Deductions ============
        self._add_question(Question(
            id="deduction_method",
            question_type=QuestionType.SINGLE_CHOICE,
            category=QuestionCategory.DEDUCTIONS,
            text="Would you like to itemize deductions or take the standard deduction?",
            help_text="The standard deduction for 2025 is $15,000 (single) or $30,000 (married filing jointly). Itemize if your deductions exceed this.",
            options=[
                QuestionOption("standard", "Take the standard deduction", "Quick and easy, works for most people"),
                QuestionOption("itemize", "Itemize deductions", "If you have significant mortgage interest, property taxes, or charitable donations"),
                QuestionOption("help", "Help me decide", "We'll ask about your expenses to determine the best option")
            ],
            fact_path="/deductionMethod"
        ))

        self._add_question(Question(
            id="had_mortgage",
            question_type=QuestionType.YES_NO,
            category=QuestionCategory.DEDUCTIONS,
            text="Did you pay mortgage interest in 2025?",
            show_if="deduction_method in ['itemize', 'help']",
            fact_path="/hasMortgageInterest"
        ))

        self._add_question(Question(
            id="mortgage_interest",
            question_type=QuestionType.CURRENCY,
            category=QuestionCategory.DEDUCTIONS,
            text="How much mortgage interest did you pay?",
            help_text="This is on Form 1098 from your lender.",
            show_if="had_mortgage == true",
            fact_path="/mortgageInterestPaid"
        ))

        self._add_question(Question(
            id="property_taxes",
            question_type=QuestionType.CURRENCY,
            category=QuestionCategory.DEDUCTIONS,
            text="How much did you pay in property taxes?",
            show_if="deduction_method in ['itemize', 'help']",
            help_text="Include real estate taxes on your primary and second home.",
            fact_path="/propertyTaxesPaid"
        ))

        self._add_question(Question(
            id="charitable_contributions",
            question_type=QuestionType.CURRENCY,
            category=QuestionCategory.DEDUCTIONS,
            text="How much did you donate to charity?",
            show_if="deduction_method in ['itemize', 'help']",
            help_text="Include cash and non-cash donations to qualified organizations.",
            fact_path="/charitableContributions"
        ))

        self._add_question(Question(
            id="student_loan_interest",
            question_type=QuestionType.YES_NO,
            category=QuestionCategory.DEDUCTIONS,
            text="Did you pay student loan interest in 2025?",
            help_text="You can deduct up to $2,500 in student loan interest.",
            fact_path="/hasStudentLoanInterest"
        ))

        self._add_question(Question(
            id="student_loan_amount",
            question_type=QuestionType.CURRENCY,
            category=QuestionCategory.DEDUCTIONS,
            text="How much student loan interest did you pay?",
            show_if="student_loan_interest == true",
            help_text="This is shown on Form 1098-E from your loan servicer.",
            fact_path="/studentLoanInterestPaid"
        ))

        self._add_question(Question(
            id="contributed_to_ira",
            question_type=QuestionType.YES_NO,
            category=QuestionCategory.DEDUCTIONS,
            text="Did you contribute to a traditional IRA in 2025?",
            help_text="Traditional IRA contributions may be tax-deductible.",
            fact_path="/hasTraditionalIRAContribution"
        ))

        self._add_question(Question(
            id="ira_contribution",
            question_type=QuestionType.CURRENCY,
            category=QuestionCategory.DEDUCTIONS,
            text="How much did you contribute to your traditional IRA?",
            show_if="contributed_to_ira == true",
            validations=[ValidationRule("max", 7000, "Maximum IRA contribution for 2025 is $7,000 ($8,000 if 50+)")],
            fact_path="/traditionalIRAContribution"
        ))

        # ============ Credits ============
        self._add_question(Question(
            id="paid_childcare",
            question_type=QuestionType.YES_NO,
            category=QuestionCategory.CREDITS,
            text="Did you pay for childcare or dependent care in 2025?",
            help_text="This may qualify for the Child and Dependent Care Credit.",
            fact_path="/hasDependentCareExpenses"
        ))

        self._add_question(Question(
            id="childcare_expenses",
            question_type=QuestionType.CURRENCY,
            category=QuestionCategory.CREDITS,
            text="How much did you pay for childcare?",
            show_if="paid_childcare == true",
            fact_path="/dependentCareExpenses"
        ))

        self._add_question(Question(
            id="paid_education",
            question_type=QuestionType.YES_NO,
            category=QuestionCategory.CREDITS,
            text="Did you pay for higher education expenses in 2025?",
            help_text="This may qualify for education credits like the American Opportunity Credit.",
            fact_path="/hasEducationExpenses"
        ))

        self._add_question(Question(
            id="education_type",
            question_type=QuestionType.SINGLE_CHOICE,
            category=QuestionCategory.CREDITS,
            text="Who was the student?",
            show_if="paid_education == true",
            options=[
                QuestionOption("self", "Me"),
                QuestionOption("spouse", "My spouse"),
                QuestionOption("dependent", "My dependent"),
                QuestionOption("multiple", "Multiple people")
            ],
            fact_path="/educationStudent"
        ))

        self._add_question(Question(
            id="first_four_years",
            question_type=QuestionType.YES_NO,
            category=QuestionCategory.CREDITS,
            text="Was the student in the first 4 years of college?",
            show_if="paid_education == true",
            help_text="The American Opportunity Credit is for the first 4 years of higher education.",
            fact_path="/firstFourYearsCollege"
        ))

        self._add_question(Question(
            id="bought_ev",
            question_type=QuestionType.YES_NO,
            category=QuestionCategory.CREDITS,
            text="Did you buy or lease a new electric or plug-in hybrid vehicle in 2025?",
            help_text="You may qualify for the Clean Vehicle Credit.",
            fact_path="/hasElectricVehiclePurchase"
        ))

        self._add_question(Question(
            id="home_improvements",
            question_type=QuestionType.YES_NO,
            category=QuestionCategory.CREDITS,
            text="Did you make energy-efficient home improvements in 2025?",
            help_text="Solar panels, heat pumps, windows, and insulation may qualify for credits.",
            fact_path="/hasEnergyImprovements"
        ))

        # ============ Healthcare ============
        self._add_question(Question(
            id="had_health_insurance",
            question_type=QuestionType.YES_NO,
            category=QuestionCategory.HEALTHCARE,
            text="Did you have health insurance coverage for all of 2025?",
            fact_path="/hadFullYearHealthCoverage"
        ))

        self._add_question(Question(
            id="marketplace_insurance",
            question_type=QuestionType.YES_NO,
            category=QuestionCategory.HEALTHCARE,
            text="Did you have health insurance through the Health Insurance Marketplace?",
            help_text="If yes, you should have received Form 1095-A.",
            fact_path="/hasMarketplaceInsurance"
        ))

        self._add_question(Question(
            id="received_ptc",
            question_type=QuestionType.YES_NO,
            category=QuestionCategory.HEALTHCARE,
            text="Did you receive advance Premium Tax Credit payments?",
            show_if="marketplace_insurance == true",
            help_text="These payments were made directly to your insurance company.",
            fact_path="/receivedAdvancePTC"
        ))

        self._add_question(Question(
            id="had_hsa",
            question_type=QuestionType.YES_NO,
            category=QuestionCategory.HEALTHCARE,
            text="Did you have a Health Savings Account (HSA) in 2025?",
            fact_path="/hasHSA"
        ))

        self._add_question(Question(
            id="hsa_contributions",
            question_type=QuestionType.CURRENCY,
            category=QuestionCategory.HEALTHCARE,
            text="How much did you contribute to your HSA?",
            show_if="had_hsa == true",
            help_text="Include personal contributions (not employer contributions).",
            fact_path="/hsaContributions"
        ))

        # ============ State/Local ============
        self._add_question(Question(
            id="state_residence",
            question_type=QuestionType.TEXT,
            category=QuestionCategory.STATE_LOCAL,
            text="What state did you live in for most of 2025?",
            validations=[ValidationRule("required")],
            fact_path="/stateOfResidence"
        ))

        self._add_question(Question(
            id="changed_states",
            question_type=QuestionType.YES_NO,
            category=QuestionCategory.STATE_LOCAL,
            text="Did you move to a different state during 2025?",
            fact_path="/changedStates"
        ))

        self._add_question(Question(
            id="local_income_tax",
            question_type=QuestionType.YES_NO,
            category=QuestionCategory.STATE_LOCAL,
            text="Do you live in a city with local income tax?",
            help_text="Cities like NYC, Philadelphia, and many Ohio cities have local income taxes.",
            fact_path="/hasLocalIncomeTax"
        ))

        # ============ Bank Information ============
        self._add_question(Question(
            id="want_direct_deposit",
            question_type=QuestionType.YES_NO,
            category=QuestionCategory.BANK_INFO,
            text="If you're owed a refund, would you like it direct deposited?",
            help_text="Direct deposit is the fastest way to receive your refund.",
            fact_path="/wantDirectDeposit"
        ))

        self._add_question(Question(
            id="bank_routing",
            question_type=QuestionType.TEXT,
            category=QuestionCategory.BANK_INFO,
            text="What is your bank routing number?",
            help_text="This 9-digit number is on the bottom left of your checks.",
            show_if="want_direct_deposit == true",
            validations=[
                ValidationRule("pattern", r"^\d{9}$", "Routing number must be 9 digits")
            ],
            fact_path="/bankRoutingNumber"
        ))

        self._add_question(Question(
            id="bank_account",
            question_type=QuestionType.TEXT,
            category=QuestionCategory.BANK_INFO,
            text="What is your bank account number?",
            show_if="want_direct_deposit == true",
            fact_path="/bankAccountNumber"
        ))

        self._add_question(Question(
            id="bank_account_type",
            question_type=QuestionType.SINGLE_CHOICE,
            category=QuestionCategory.BANK_INFO,
            text="Is this a checking or savings account?",
            show_if="want_direct_deposit == true",
            options=[
                QuestionOption("checking", "Checking"),
                QuestionOption("savings", "Savings")
            ],
            fact_path="/bankAccountType"
        ))

        # ============ Review ============
        self._add_question(Question(
            id="review_complete",
            question_type=QuestionType.YES_NO,
            category=QuestionCategory.REVIEW,
            text="You've completed the interview! Would you like to review your answers?",
            help_text="You can make changes before we calculate your taxes."
        ))

    def _add_question(self, question: Question):
        """Add a question to the registry."""
        self.questions[question.id] = question
        self.question_order.append(question.id)

    def start_interview(self) -> InterviewState:
        """Start a new interview session."""
        return InterviewState(
            current_question_id=self.question_order[0],
            answers={},
            completed_questions=set(),
            skipped_questions=set(),
            question_history=[],
            errors={}
        )

    def get_current_question(self, state: InterviewState) -> Optional[Question]:
        """Get the current question."""
        return self.questions.get(state.current_question_id)

    def answer_question(
        self,
        state: InterviewState,
        answer: Any
    ) -> InterviewState:
        """Submit an answer and move to the next question.

        Args:
            state: Current interview state.
            answer: The answer to the current question.

        Returns:
            Updated interview state.
        """
        current_q = self.questions.get(state.current_question_id)
        if not current_q:
            return state

        # Validate answer
        errors = self._validate_answer(current_q, answer)
        if errors:
            state.errors[current_q.id] = errors[0]
            return state

        # Store answer
        state.answers[current_q.id] = answer
        state.completed_questions.add(current_q.id)
        state.question_history.append(current_q.id)
        state.errors.pop(current_q.id, None)

        # Find next question
        next_q_id = self._find_next_question(state, current_q)

        if next_q_id:
            state.current_question_id = next_q_id
        else:
            state.is_complete = True

        return state

    def go_back(self, state: InterviewState) -> InterviewState:
        """Go back to the previous question."""
        if state.question_history:
            prev_id = state.question_history.pop()
            state.current_question_id = prev_id
            state.completed_questions.discard(prev_id)
        return state

    def skip_question(self, state: InterviewState) -> InterviewState:
        """Skip the current question if allowed."""
        current_q = self.questions.get(state.current_question_id)
        if not current_q:
            return state

        # Check if question has required validation
        is_required = any(v.rule_type == "required" for v in current_q.validations)
        if is_required:
            state.errors[current_q.id] = "This question is required"
            return state

        state.skipped_questions.add(current_q.id)
        state.question_history.append(current_q.id)

        next_q_id = self._find_next_question(state, current_q)
        if next_q_id:
            state.current_question_id = next_q_id
        else:
            state.is_complete = True

        return state

    def get_progress(self, state: InterviewState) -> InterviewProgress:
        """Get interview progress."""
        total = len(self.question_order)
        answered = len(state.completed_questions)
        skipped = len(state.skipped_questions)

        current_q = self.questions.get(state.current_question_id)
        current_category = current_q.category.value if current_q else ""

        # Calculate category completion
        categories_complete = {}
        for cat in QuestionCategory:
            cat_questions = [q for q in self.questions.values() if q.category == cat]
            if cat_questions:
                completed = sum(1 for q in cat_questions if q.id in state.completed_questions)
                categories_complete[cat.value] = completed >= len(cat_questions)
            else:
                categories_complete[cat.value] = True

        return InterviewProgress(
            total_questions=total,
            answered_questions=answered,
            skipped_questions=skipped,
            current_category=current_category,
            categories_complete=categories_complete,
            percent_complete=round((answered + skipped) / total * 100, 1) if total > 0 else 0
        )

    def get_fact_mapping(self, state: InterviewState) -> Dict[str, Any]:
        """Convert interview answers to fact dictionary paths."""
        facts = {}

        for q_id, answer in state.answers.items():
            question = self.questions.get(q_id)
            if question and question.fact_path:
                facts[question.fact_path] = answer

        return facts

    def _validate_answer(self, question: Question, answer: Any) -> List[str]:
        """Validate an answer against question rules."""
        errors = []

        for rule in question.validations:
            if rule.rule_type == "required":
                if answer is None or answer == "" or answer == []:
                    errors.append(rule.error_message or "This field is required")

            elif rule.rule_type == "min":
                if isinstance(answer, (int, float)) and answer < rule.value:
                    errors.append(rule.error_message or f"Value must be at least {rule.value}")

            elif rule.rule_type == "max":
                if isinstance(answer, (int, float)) and answer > rule.value:
                    errors.append(rule.error_message or f"Value must be at most {rule.value}")

            elif rule.rule_type == "pattern":
                import re
                if isinstance(answer, str) and not re.match(rule.value, answer):
                    errors.append(rule.error_message or "Invalid format")

        return errors

    def _find_next_question(
        self,
        state: InterviewState,
        current_question: Question
    ) -> Optional[str]:
        """Find the next applicable question."""

        # Check for follow-up questions first
        for follow_up_id in current_question.follow_up_questions:
            if follow_up_id not in state.completed_questions:
                follow_up = self.questions.get(follow_up_id)
                if follow_up and self._should_show_question(follow_up, state):
                    return follow_up_id

        # Find next in order
        current_idx = self.question_order.index(current_question.id)

        for i in range(current_idx + 1, len(self.question_order)):
            q_id = self.question_order[i]
            if q_id in state.completed_questions or q_id in state.skipped_questions:
                continue

            question = self.questions.get(q_id)
            if question and self._should_show_question(question, state):
                return q_id

        return None  # Interview complete

    def _should_show_question(self, question: Question, state: InterviewState) -> bool:
        """Determine if a question should be shown based on conditions."""

        # Check show_if condition
        if question.show_if:
            if not self._evaluate_condition(question.show_if, state.answers):
                return False

        # Check skip_if condition
        if question.skip_if:
            if self._evaluate_condition(question.skip_if, state.answers):
                return False

        return True

    def _evaluate_condition(self, condition: str, answers: Dict[str, Any]) -> bool:
        """Evaluate a show_if/skip_if condition."""
        # Simple condition evaluation
        # Supports: field == value, field in [values], field != value

        try:
            # Handle "field in ['a', 'b']" style
            if " in " in condition:
                parts = condition.split(" in ")
                field = parts[0].strip()
                values_str = parts[1].strip()

                answer = answers.get(field)
                if answer is None:
                    return False

                # Parse list
                import ast
                try:
                    values = ast.literal_eval(values_str)
                    return answer in values
                except:
                    return False

            # Handle "'value' in field" (check if value in list answer)
            if condition.startswith("'") and "' in " in condition:
                parts = condition.split("' in ")
                value = parts[0][1:]  # Remove leading quote
                field = parts[1].strip()

                answer = answers.get(field, [])
                if isinstance(answer, list):
                    return value in answer
                return False

            # Handle "field == value"
            if " == " in condition:
                parts = condition.split(" == ")
                field = parts[0].strip()
                value_str = parts[1].strip()

                answer = answers.get(field)

                # Parse value
                if value_str == "true":
                    return answer == True
                elif value_str == "false":
                    return answer == False
                elif value_str.startswith("'") and value_str.endswith("'"):
                    return answer == value_str[1:-1]
                else:
                    return str(answer) == value_str

            # Handle "field != value"
            if " != " in condition:
                parts = condition.split(" != ")
                field = parts[0].strip()
                value_str = parts[1].strip()

                answer = answers.get(field)

                if value_str == "true":
                    return answer != True
                elif value_str == "false":
                    return answer != False
                elif value_str.startswith("'") and value_str.endswith("'"):
                    return answer != value_str[1:-1]
                else:
                    return str(answer) != value_str

        except Exception:
            pass

        return True  # Default to showing
