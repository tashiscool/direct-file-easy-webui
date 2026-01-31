"""Tax Planning Calculator Service.

Provides what-if sliders, marginal/effective rate calculations,
and tax optimization recommendations.
"""

from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class FilingStatus(Enum):
    """Filing status options."""
    SINGLE = "single"
    MARRIED_FILING_JOINTLY = "mfj"
    MARRIED_FILING_SEPARATELY = "mfs"
    HEAD_OF_HOUSEHOLD = "hoh"
    QUALIFYING_SURVIVING_SPOUSE = "qss"


@dataclass
class TaxBracket:
    """A tax bracket with rate and threshold."""
    rate: Decimal
    min_income: Decimal
    max_income: Optional[Decimal] = None


@dataclass
class TaxCalculation:
    """Complete tax calculation result."""
    # Income
    gross_income: Decimal
    adjustments: Decimal
    adjusted_gross_income: Decimal

    # Deductions
    standard_deduction: Decimal
    itemized_deduction: Decimal
    deduction_used: str  # 'standard' or 'itemized'
    total_deduction: Decimal
    qbi_deduction: Decimal

    # Taxable Income
    taxable_income: Decimal

    # Tax
    regular_tax: Decimal
    amt: Decimal
    niit: Decimal  # Net Investment Income Tax
    self_employment_tax: Decimal
    total_tax_before_credits: Decimal

    # Credits
    child_tax_credit: Decimal
    education_credits: Decimal
    other_credits: Decimal
    total_credits: Decimal

    # Final
    total_tax: Decimal
    withholding: Decimal
    estimated_payments: Decimal
    refund_or_owed: Decimal

    # Rates
    marginal_rate: Decimal
    effective_rate: Decimal
    average_rate: Decimal


@dataclass
class WhatIfScenario:
    """A what-if scenario with changes and results."""
    name: str
    description: str
    changes: Dict[str, Any]
    original_calculation: TaxCalculation
    new_calculation: TaxCalculation
    tax_difference: Decimal
    recommendations: List[str]


@dataclass
class TaxPlanningRecommendation:
    """A tax planning recommendation."""
    category: str
    title: str
    description: str
    potential_savings: Decimal
    action_items: List[str]
    priority: int  # 1 = high, 2 = medium, 3 = low


class TaxPlanningService:
    """Service for tax planning calculations and what-if analysis."""

    # 2025 Tax Brackets
    BRACKETS_2025 = {
        FilingStatus.SINGLE: [
            TaxBracket(Decimal("0.10"), Decimal("0"), Decimal("11925")),
            TaxBracket(Decimal("0.12"), Decimal("11925"), Decimal("48475")),
            TaxBracket(Decimal("0.22"), Decimal("48475"), Decimal("103350")),
            TaxBracket(Decimal("0.24"), Decimal("103350"), Decimal("197300")),
            TaxBracket(Decimal("0.32"), Decimal("197300"), Decimal("250500")),
            TaxBracket(Decimal("0.35"), Decimal("250500"), Decimal("626350")),
            TaxBracket(Decimal("0.37"), Decimal("626350"), None),
        ],
        FilingStatus.MARRIED_FILING_JOINTLY: [
            TaxBracket(Decimal("0.10"), Decimal("0"), Decimal("23850")),
            TaxBracket(Decimal("0.12"), Decimal("23850"), Decimal("96950")),
            TaxBracket(Decimal("0.22"), Decimal("96950"), Decimal("206700")),
            TaxBracket(Decimal("0.24"), Decimal("206700"), Decimal("394600")),
            TaxBracket(Decimal("0.32"), Decimal("394600"), Decimal("501050")),
            TaxBracket(Decimal("0.35"), Decimal("501050"), Decimal("751600")),
            TaxBracket(Decimal("0.37"), Decimal("751600"), None),
        ],
        FilingStatus.HEAD_OF_HOUSEHOLD: [
            TaxBracket(Decimal("0.10"), Decimal("0"), Decimal("17000")),
            TaxBracket(Decimal("0.12"), Decimal("17000"), Decimal("64850")),
            TaxBracket(Decimal("0.22"), Decimal("64850"), Decimal("103350")),
            TaxBracket(Decimal("0.24"), Decimal("103350"), Decimal("197300")),
            TaxBracket(Decimal("0.32"), Decimal("197300"), Decimal("250500")),
            TaxBracket(Decimal("0.35"), Decimal("250500"), Decimal("626350")),
            TaxBracket(Decimal("0.37"), Decimal("626350"), None),
        ],
    }

    # 2025 Standard Deductions (Updated per OBBBA - One Big Beautiful Bill Act)
    # IRC §63(c) as amended
    STANDARD_DEDUCTIONS_2025 = {
        FilingStatus.SINGLE: Decimal("15750"),
        FilingStatus.MARRIED_FILING_JOINTLY: Decimal("31500"),
        FilingStatus.MARRIED_FILING_SEPARATELY: Decimal("15750"),
        FilingStatus.HEAD_OF_HOUSEHOLD: Decimal("23625"),
        FilingStatus.QUALIFYING_SURVIVING_SPOUSE: Decimal("31500"),
    }

    # Additional deduction for age 65+ or blind
    ADDITIONAL_DEDUCTION_2025 = {
        FilingStatus.SINGLE: Decimal("2000"),
        FilingStatus.HEAD_OF_HOUSEHOLD: Decimal("2000"),
        FilingStatus.MARRIED_FILING_JOINTLY: Decimal("1600"),  # per spouse
        FilingStatus.MARRIED_FILING_SEPARATELY: Decimal("1600"),
        FilingStatus.QUALIFYING_SURVIVING_SPOUSE: Decimal("1600"),
    }

    # AMT exemptions
    AMT_EXEMPTIONS_2025 = {
        FilingStatus.SINGLE: Decimal("88100"),
        FilingStatus.MARRIED_FILING_JOINTLY: Decimal("137000"),
        FilingStatus.HEAD_OF_HOUSEHOLD: Decimal("88100"),
        FilingStatus.MARRIED_FILING_SEPARATELY: Decimal("68500"),
    }

    # NIIT threshold (unchanged from recent years)
    NIIT_THRESHOLDS = {
        FilingStatus.SINGLE: Decimal("200000"),
        FilingStatus.MARRIED_FILING_JOINTLY: Decimal("250000"),
        FilingStatus.HEAD_OF_HOUSEHOLD: Decimal("200000"),
        FilingStatus.MARRIED_FILING_SEPARATELY: Decimal("125000"),
    }

    # Self-employment tax rates
    SE_TAX_RATE = Decimal("0.153")  # 15.3% (12.4% SS + 2.9% Medicare)
    SE_DEDUCTION_RATE = Decimal("0.5")  # 50% deductible
    SS_WAGE_BASE_2025 = Decimal("176100")  # Social Security wage base

    # Child Tax Credit (per OBBBA - increased from $2,000 to $2,200)
    # IRC §24 as amended
    CTC_AMOUNT = Decimal("2200")
    CTC_REFUNDABLE = Decimal("1700")  # Additional Child Tax Credit (ACTC)
    CTC_PHASEOUT_SINGLE = Decimal("200000")
    CTC_PHASEOUT_MFJ = Decimal("400000")

    def __init__(self):
        # Add MFS brackets same as single for simplicity
        self.BRACKETS_2025[FilingStatus.MARRIED_FILING_SEPARATELY] = self.BRACKETS_2025[FilingStatus.SINGLE]
        self.BRACKETS_2025[FilingStatus.QUALIFYING_SURVIVING_SPOUSE] = self.BRACKETS_2025[FilingStatus.MARRIED_FILING_JOINTLY]

    def calculate_tax(
        self,
        facts: Dict[str, Any],
        filing_status: FilingStatus
    ) -> TaxCalculation:
        """Calculate complete tax based on facts.

        Args:
            facts: Dictionary of tax facts (income, deductions, etc.)
            filing_status: Filing status for the taxpayer.

        Returns:
            Complete TaxCalculation with all components.
        """
        # Income
        wages = self._get_decimal(facts, "/wages", "/w2Wages", "/totalWages")
        interest = self._get_decimal(facts, "/interestIncome", "/totalInterest")
        dividends = self._get_decimal(facts, "/dividendIncome", "/ordinaryDividends")
        qualified_dividends = self._get_decimal(facts, "/qualifiedDividends")
        business_income = self._get_decimal(facts, "/businessIncome", "/scheduleCNetProfit")
        capital_gains = self._get_decimal(facts, "/capitalGains", "/netCapitalGain")
        retirement_income = self._get_decimal(facts, "/retirementIncome", "/pensionIncome")
        social_security = self._get_decimal(facts, "/socialSecurityBenefits")
        other_income = self._get_decimal(facts, "/otherIncome")

        gross_income = (
            wages + interest + dividends + business_income +
            capital_gains + retirement_income + other_income
        )

        # Add taxable portion of Social Security
        ss_taxable = self._calculate_taxable_social_security(
            social_security, gross_income, filing_status
        )
        gross_income += ss_taxable

        # Adjustments (above-the-line deductions)
        se_deduction = self._calculate_se_tax_deduction(business_income)
        ira_deduction = self._get_decimal(facts, "/iraDeduction", "/traditionalIRADeduction")
        student_loan = self._get_decimal(facts, "/studentLoanInterest")
        hsa = self._get_decimal(facts, "/hsaDeduction", "/hsaContributions")
        educator_expenses = min(self._get_decimal(facts, "/educatorExpenses"), Decimal("300"))
        other_adjustments = self._get_decimal(facts, "/otherAdjustments")

        adjustments = (
            se_deduction + ira_deduction + student_loan +
            hsa + educator_expenses + other_adjustments
        )

        agi = gross_income - adjustments

        # Deductions
        standard = self.STANDARD_DEDUCTIONS_2025.get(filing_status, Decimal("15000"))

        # Adjust for age/blindness
        if facts.get("/isOver65") or facts.get("/primaryAge", 0) >= 65:
            standard += self.ADDITIONAL_DEDUCTION_2025.get(filing_status, Decimal("1600"))
        if facts.get("/isBlind"):
            standard += self.ADDITIONAL_DEDUCTION_2025.get(filing_status, Decimal("1600"))

        # Itemized deductions (subject to SALT cap)
        mortgage_interest = self._get_decimal(facts, "/mortgageInterest")
        state_local_taxes = min(
            self._get_decimal(facts, "/stateIncomeTax") +
            self._get_decimal(facts, "/propertyTax"),
            Decimal("10000")  # SALT cap
        )
        charitable = self._get_decimal(facts, "/charitableContributions")
        medical = self._calculate_medical_deduction(
            self._get_decimal(facts, "/medicalExpenses"),
            agi
        )
        other_itemized = self._get_decimal(facts, "/otherItemizedDeductions")

        itemized = mortgage_interest + state_local_taxes + charitable + medical + other_itemized

        # Use better of standard or itemized
        if itemized > standard:
            deduction_used = "itemized"
            total_deduction = itemized
        else:
            deduction_used = "standard"
            total_deduction = standard

        # QBI deduction (20% of qualified business income, simplified)
        qbi = Decimal("0")
        if business_income > 0:
            qbi = min(
                business_income * Decimal("0.20"),
                (agi - total_deduction) * Decimal("0.20")
            )

        # Taxable income
        taxable_income = max(agi - total_deduction - qbi, Decimal("0"))

        # Regular tax calculation
        regular_tax = self._calculate_bracket_tax(taxable_income, filing_status)

        # Qualified dividends / long-term capital gains rate
        preferential_income = qualified_dividends + max(capital_gains, Decimal("0"))
        if preferential_income > 0:
            regular_tax = self._adjust_for_capital_gains(
                taxable_income, preferential_income, regular_tax, filing_status
            )

        # AMT (simplified)
        amt = self._calculate_amt(agi, itemized, filing_status)

        # NIIT (3.8% on investment income above threshold)
        investment_income = interest + dividends + capital_gains
        niit = self._calculate_niit(agi, investment_income, filing_status)

        # Self-employment tax
        se_tax = self._calculate_se_tax(business_income)

        total_tax_before_credits = max(regular_tax, amt) + niit + se_tax

        # Credits
        child_tax_credit = self._calculate_ctc(
            facts.get("/numberOfChildrenUnder17", 0),
            facts.get("/numberOfDependents", 0),
            agi,
            filing_status
        )

        education_credits = self._get_decimal(facts, "/educationCredits", "/aotcCredit", "/llcCredit")
        other_credits = (
            self._get_decimal(facts, "/dependentCareCredit") +
            self._get_decimal(facts, "/saverCredit") +
            self._get_decimal(facts, "/energyCredits") +
            self._get_decimal(facts, "/evCredit") +
            self._get_decimal(facts, "/earnedIncomeCredit", "/eitc") +
            self._get_decimal(facts, "/otherCredits")
        )

        total_credits = child_tax_credit + education_credits + other_credits

        # Final tax
        total_tax = max(total_tax_before_credits - total_credits, Decimal("0"))

        # Withholding and payments
        withholding = self._get_decimal(facts, "/federalWithholding", "/w2Withholding")
        estimated = self._get_decimal(facts, "/estimatedPayments")

        refund_or_owed = withholding + estimated - total_tax

        # Calculate rates
        marginal_rate = self._get_marginal_rate(taxable_income, filing_status)
        effective_rate = (
            (total_tax / gross_income * 100) if gross_income > 0 else Decimal("0")
        )
        average_rate = (
            (total_tax / taxable_income * 100) if taxable_income > 0 else Decimal("0")
        )

        return TaxCalculation(
            gross_income=gross_income,
            adjustments=adjustments,
            adjusted_gross_income=agi,
            standard_deduction=standard,
            itemized_deduction=itemized,
            deduction_used=deduction_used,
            total_deduction=total_deduction,
            qbi_deduction=qbi,
            taxable_income=taxable_income,
            regular_tax=regular_tax,
            amt=amt,
            niit=niit,
            self_employment_tax=se_tax,
            total_tax_before_credits=total_tax_before_credits,
            child_tax_credit=child_tax_credit,
            education_credits=education_credits,
            other_credits=other_credits,
            total_credits=total_credits,
            total_tax=total_tax,
            withholding=withholding,
            estimated_payments=estimated,
            refund_or_owed=refund_or_owed,
            marginal_rate=marginal_rate,
            effective_rate=effective_rate.quantize(Decimal("0.01")),
            average_rate=average_rate.quantize(Decimal("0.01"))
        )

    def analyze_scenario(
        self,
        facts: Dict[str, Any],
        changes: Dict[str, Any],
        filing_status: FilingStatus,
        scenario_name: str = "Custom Scenario"
    ) -> WhatIfScenario:
        """Analyze a what-if scenario.

        Args:
            facts: Current tax facts.
            changes: Dictionary of changes to apply.
            filing_status: Filing status.
            scenario_name: Name for this scenario.

        Returns:
            WhatIfScenario with comparison and recommendations.
        """
        original = self.calculate_tax(facts, filing_status)

        # Apply changes
        modified_facts = facts.copy()
        modified_facts.update(changes)

        new = self.calculate_tax(modified_facts, filing_status)

        difference = new.total_tax - original.total_tax

        # Generate recommendations
        recommendations = []
        if difference < 0:
            recommendations.append(
                f"This change would save you ${abs(difference):,.2f} in taxes."
            )
        elif difference > 0:
            recommendations.append(
                f"This change would increase your taxes by ${difference:,.2f}."
            )
        else:
            recommendations.append("This change would not affect your tax liability.")

        # Add specific recommendations based on changes
        recommendations.extend(self._generate_scenario_recommendations(
            original, new, changes
        ))

        return WhatIfScenario(
            name=scenario_name,
            description=f"Impact of changes: {list(changes.keys())}",
            changes=changes,
            original_calculation=original,
            new_calculation=new,
            tax_difference=difference,
            recommendations=recommendations
        )

    def get_planning_recommendations(
        self,
        facts: Dict[str, Any],
        filing_status: FilingStatus
    ) -> List[TaxPlanningRecommendation]:
        """Get tax planning recommendations.

        Args:
            facts: Current tax facts.
            filing_status: Filing status.

        Returns:
            List of recommendations sorted by potential savings.
        """
        recommendations = []
        calc = self.calculate_tax(facts, filing_status)

        # IRA contribution recommendation
        ira_current = self._get_decimal(facts, "/iraDeduction", "/traditionalIRADeduction")
        ira_max = Decimal("7000")  # 2025 limit
        if facts.get("/isOver50") or facts.get("/primaryAge", 0) >= 50:
            ira_max = Decimal("8000")  # Catch-up

        if ira_current < ira_max:
            additional = ira_max - ira_current
            savings = additional * calc.marginal_rate / 100
            recommendations.append(TaxPlanningRecommendation(
                category="Retirement",
                title="Maximize IRA Contributions",
                description=f"You can contribute ${additional:,.0f} more to your Traditional IRA.",
                potential_savings=savings,
                action_items=[
                    f"Contribute ${additional:,.0f} to Traditional IRA before April 15",
                    "Consider Roth IRA if income is below phase-out threshold"
                ],
                priority=1
            ))

        # HSA recommendation
        hsa_current = self._get_decimal(facts, "/hsaContributions")
        if facts.get("/hasHSA") or facts.get("/hasHighDeductiblePlan"):
            hsa_max = Decimal("4300")  # 2025 single limit
            if filing_status == FilingStatus.MARRIED_FILING_JOINTLY:
                hsa_max = Decimal("8550")

            if hsa_current < hsa_max:
                additional = hsa_max - hsa_current
                savings = additional * calc.marginal_rate / 100
                recommendations.append(TaxPlanningRecommendation(
                    category="Healthcare",
                    title="Maximize HSA Contributions",
                    description=f"Triple tax advantage: deductible, grows tax-free, tax-free for medical.",
                    potential_savings=savings,
                    action_items=[
                        f"Contribute ${additional:,.0f} more to your HSA",
                        "Keep receipts for future tax-free withdrawals"
                    ],
                    priority=1
                ))

        # Charitable giving timing
        if calc.deduction_used == "standard" and calc.itemized_deduction > Decimal("0"):
            gap = calc.standard_deduction - calc.itemized_deduction
            if gap < Decimal("5000"):
                recommendations.append(TaxPlanningRecommendation(
                    category="Deductions",
                    title="Consider Charitable Bunching",
                    description="You're close to itemizing. Bundle 2 years of donations.",
                    potential_savings=gap * calc.marginal_rate / 100,
                    action_items=[
                        "Prepay next year's charitable donations",
                        "Consider a Donor Advised Fund for bunching",
                        "Time large donations to alternate years"
                    ],
                    priority=2
                ))

        # Tax-loss harvesting
        capital_gains = self._get_decimal(facts, "/capitalGains")
        if capital_gains > 0:
            recommendations.append(TaxPlanningRecommendation(
                category="Investments",
                title="Tax-Loss Harvesting Opportunity",
                description="Offset capital gains by selling investments at a loss.",
                potential_savings=min(capital_gains, Decimal("3000")) * calc.marginal_rate / 100,
                action_items=[
                    "Review portfolio for unrealized losses",
                    "Sell losing positions before year-end",
                    "Wait 31+ days before repurchasing (wash sale rule)"
                ],
                priority=2
            ))

        # Roth conversion consideration
        if calc.marginal_rate <= Decimal("22"):
            recommendations.append(TaxPlanningRecommendation(
                category="Retirement",
                title="Consider Roth Conversion",
                description="Your marginal rate is low. Convert Traditional IRA to Roth.",
                potential_savings=Decimal("0"),  # Long-term benefit
                action_items=[
                    "Calculate room in 22% bracket",
                    "Convert portion of Traditional IRA to Roth",
                    "Pay taxes now at lower rate, grow tax-free"
                ],
                priority=3
            ))

        # Estimated payments
        if calc.refund_or_owed < Decimal("-1000"):
            recommendations.append(TaxPlanningRecommendation(
                category="Planning",
                title="Review Estimated Tax Payments",
                description="You may owe a penalty for underpayment.",
                potential_savings=abs(calc.refund_or_owed) * Decimal("0.08"),
                action_items=[
                    "Increase W-4 withholding",
                    "Make quarterly estimated payments",
                    "Use safe harbor: pay 100% of prior year tax"
                ],
                priority=1
            ))

        # Sort by potential savings
        recommendations.sort(key=lambda r: r.potential_savings, reverse=True)

        return recommendations

    def calculate_marginal_impact(
        self,
        facts: Dict[str, Any],
        filing_status: FilingStatus,
        additional_income: Decimal
    ) -> Dict[str, Decimal]:
        """Calculate the marginal tax impact of additional income.

        Args:
            facts: Current tax facts.
            filing_status: Filing status.
            additional_income: Amount of additional income.

        Returns:
            Dictionary with tax breakdown of additional income.
        """
        current = self.calculate_tax(facts, filing_status)

        # Add income
        modified = facts.copy()
        current_wages = self._get_decimal(facts, "/wages")
        modified["/wages"] = current_wages + additional_income

        new = self.calculate_tax(modified, filing_status)

        additional_tax = new.total_tax - current.total_tax
        marginal_rate = (
            (additional_tax / additional_income * 100)
            if additional_income > 0 else Decimal("0")
        )

        return {
            "additional_income": additional_income,
            "additional_tax": additional_tax,
            "take_home": additional_income - additional_tax,
            "marginal_rate": marginal_rate.quantize(Decimal("0.01")),
            "new_bracket": new.marginal_rate,
            "bracket_changed": new.marginal_rate != current.marginal_rate
        }

    # Private helper methods

    def _get_decimal(self, facts: Dict, *keys: str) -> Decimal:
        """Get a decimal value from facts, trying multiple keys."""
        for key in keys:
            val = facts.get(key)
            if val is not None:
                try:
                    return Decimal(str(val))
                except:
                    pass
        return Decimal("0")

    def _calculate_bracket_tax(
        self,
        taxable_income: Decimal,
        filing_status: FilingStatus
    ) -> Decimal:
        """Calculate tax using progressive brackets."""
        brackets = self.BRACKETS_2025.get(
            filing_status,
            self.BRACKETS_2025[FilingStatus.SINGLE]
        )

        tax = Decimal("0")
        remaining = taxable_income

        for bracket in brackets:
            if remaining <= 0:
                break

            bracket_size = (
                bracket.max_income - bracket.min_income
                if bracket.max_income else remaining
            )

            taxable_in_bracket = min(remaining, bracket_size)
            tax += taxable_in_bracket * bracket.rate
            remaining -= taxable_in_bracket

        return tax.quantize(Decimal("0.01"), ROUND_HALF_UP)

    def _get_marginal_rate(
        self,
        taxable_income: Decimal,
        filing_status: FilingStatus
    ) -> Decimal:
        """Get the marginal tax rate for given income."""
        brackets = self.BRACKETS_2025.get(
            filing_status,
            self.BRACKETS_2025[FilingStatus.SINGLE]
        )

        for bracket in brackets:
            if bracket.max_income is None or taxable_income <= bracket.max_income:
                return bracket.rate * 100

        return brackets[-1].rate * 100

    def _calculate_se_tax(self, business_income: Decimal) -> Decimal:
        """Calculate self-employment tax."""
        if business_income <= 0:
            return Decimal("0")

        # Net earnings = 92.35% of business income
        net_earnings = business_income * Decimal("0.9235")

        # Social Security portion (12.4% up to wage base)
        ss_portion = min(net_earnings, self.SS_WAGE_BASE_2025) * Decimal("0.124")

        # Medicare portion (2.9% on all, plus 0.9% above $200k)
        medicare_portion = net_earnings * Decimal("0.029")
        if net_earnings > Decimal("200000"):
            medicare_portion += (net_earnings - Decimal("200000")) * Decimal("0.009")

        return (ss_portion + medicare_portion).quantize(Decimal("0.01"))

    def _calculate_se_tax_deduction(self, business_income: Decimal) -> Decimal:
        """Calculate the deductible portion of SE tax."""
        se_tax = self._calculate_se_tax(business_income)
        return (se_tax * self.SE_DEDUCTION_RATE).quantize(Decimal("0.01"))

    def _calculate_taxable_social_security(
        self,
        ss_benefits: Decimal,
        other_income: Decimal,
        filing_status: FilingStatus
    ) -> Decimal:
        """Calculate taxable portion of Social Security benefits."""
        if ss_benefits <= 0:
            return Decimal("0")

        combined_income = other_income + (ss_benefits * Decimal("0.5"))

        # Thresholds
        if filing_status == FilingStatus.MARRIED_FILING_JOINTLY:
            threshold1 = Decimal("32000")
            threshold2 = Decimal("44000")
        else:
            threshold1 = Decimal("25000")
            threshold2 = Decimal("34000")

        if combined_income <= threshold1:
            return Decimal("0")
        elif combined_income <= threshold2:
            return min(
                (combined_income - threshold1) * Decimal("0.5"),
                ss_benefits * Decimal("0.5")
            )
        else:
            base_taxable = min(
                (threshold2 - threshold1) * Decimal("0.5"),
                ss_benefits * Decimal("0.5")
            )
            additional = (combined_income - threshold2) * Decimal("0.85")
            total = base_taxable + additional
            return min(total, ss_benefits * Decimal("0.85"))

    def _calculate_medical_deduction(
        self,
        medical_expenses: Decimal,
        agi: Decimal
    ) -> Decimal:
        """Calculate deductible medical expenses (exceeding 7.5% of AGI)."""
        threshold = agi * Decimal("0.075")
        return max(medical_expenses - threshold, Decimal("0"))

    def _calculate_amt(
        self,
        agi: Decimal,
        itemized: Decimal,
        filing_status: FilingStatus
    ) -> Decimal:
        """Calculate Alternative Minimum Tax (simplified)."""
        # AMT taxable income starts with AGI
        amti = agi

        # Add back SALT deduction (limited under regular tax too)
        # Add back misc deductions
        # For simplicity, just check if AMT might apply

        exemption = self.AMT_EXEMPTIONS_2025.get(filing_status, Decimal("88100"))

        # Phase out exemption above thresholds
        if filing_status == FilingStatus.MARRIED_FILING_JOINTLY:
            phaseout_start = Decimal("1252700")
        else:
            phaseout_start = Decimal("626350")

        if amti > phaseout_start:
            reduction = (amti - phaseout_start) * Decimal("0.25")
            exemption = max(exemption - reduction, Decimal("0"))

        amt_taxable = max(amti - exemption, Decimal("0"))

        # AMT rates: 26% up to $220,700 (MFJ) / $110,350 (others), 28% above
        if filing_status == FilingStatus.MARRIED_FILING_JOINTLY:
            breakpoint = Decimal("220700")
        else:
            breakpoint = Decimal("110350")

        if amt_taxable <= breakpoint:
            amt = amt_taxable * Decimal("0.26")
        else:
            amt = (breakpoint * Decimal("0.26") +
                   (amt_taxable - breakpoint) * Decimal("0.28"))

        return amt.quantize(Decimal("0.01"))

    def _calculate_niit(
        self,
        agi: Decimal,
        investment_income: Decimal,
        filing_status: FilingStatus
    ) -> Decimal:
        """Calculate Net Investment Income Tax (3.8%)."""
        threshold = self.NIIT_THRESHOLDS.get(filing_status, Decimal("200000"))

        if agi <= threshold:
            return Decimal("0")

        excess_agi = agi - threshold
        taxable_niit = min(investment_income, excess_agi)

        return (taxable_niit * Decimal("0.038")).quantize(Decimal("0.01"))

    def _adjust_for_capital_gains(
        self,
        taxable_income: Decimal,
        preferential_income: Decimal,
        regular_tax: Decimal,
        filing_status: FilingStatus
    ) -> Decimal:
        """Adjust tax for preferential capital gains rates."""
        # Capital gains brackets (0%, 15%, 20%)
        if filing_status == FilingStatus.MARRIED_FILING_JOINTLY:
            threshold_0 = Decimal("96700")
            threshold_15 = Decimal("600050")
        elif filing_status == FilingStatus.HEAD_OF_HOUSEHOLD:
            threshold_0 = Decimal("64750")
            threshold_15 = Decimal("566700")
        else:  # Single, MFS
            threshold_0 = Decimal("48350")
            threshold_15 = Decimal("533400")

        ordinary_income = taxable_income - preferential_income

        # Calculate tax savings from preferential rates
        # This is simplified - actual calculation is more complex
        if taxable_income <= threshold_0:
            # All at 0%
            savings = preferential_income * self._get_marginal_rate(taxable_income, filing_status) / 100
        elif ordinary_income >= threshold_15:
            # All at 20%
            ordinary_rate = self._get_marginal_rate(taxable_income, filing_status) / 100
            savings = preferential_income * (ordinary_rate - Decimal("0.20"))
        else:
            # Mix of 0%, 15%, 20%
            ordinary_rate = self._get_marginal_rate(taxable_income, filing_status) / 100
            savings = preferential_income * (ordinary_rate - Decimal("0.15"))

        return max(regular_tax - savings, Decimal("0")).quantize(Decimal("0.01"))

    def _calculate_ctc(
        self,
        children_under_17: int,
        total_dependents: int,
        agi: Decimal,
        filing_status: FilingStatus
    ) -> Decimal:
        """Calculate Child Tax Credit."""
        if children_under_17 <= 0:
            return Decimal("0")

        credit = Decimal(children_under_17) * self.CTC_AMOUNT

        # Phase-out
        if filing_status == FilingStatus.MARRIED_FILING_JOINTLY:
            threshold = self.CTC_PHASEOUT_MFJ
        else:
            threshold = self.CTC_PHASEOUT_SINGLE

        if agi > threshold:
            reduction = ((agi - threshold) / Decimal("1000")).quantize(
                Decimal("1"), ROUND_HALF_UP
            ) * Decimal("50")
            credit = max(credit - reduction, Decimal("0"))

        return credit

    def _generate_scenario_recommendations(
        self,
        original: TaxCalculation,
        new: TaxCalculation,
        changes: Dict[str, Any]
    ) -> List[str]:
        """Generate specific recommendations based on scenario changes."""
        recs = []

        # Check for bracket changes
        if new.marginal_rate != original.marginal_rate:
            if new.marginal_rate > original.marginal_rate:
                recs.append(
                    f"Warning: This moves you into the {new.marginal_rate}% bracket "
                    f"(from {original.marginal_rate}%)."
                )
            else:
                recs.append(
                    f"Benefit: This moves you to the {new.marginal_rate}% bracket "
                    f"(from {original.marginal_rate}%)."
                )

        # Check for NIIT impact
        if new.niit != original.niit:
            if new.niit > original.niit:
                recs.append(
                    f"This triggers an additional ${new.niit - original.niit:,.2f} "
                    "in Net Investment Income Tax (3.8%)."
                )

        # Check deduction method change
        if new.deduction_used != original.deduction_used:
            recs.append(
                f"This changes your deduction from {original.deduction_used} "
                f"to {new.deduction_used}."
            )

        return recs
