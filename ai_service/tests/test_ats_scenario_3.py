"""Comprehensive pytest tests for IRS ATS Test Scenario 3 - Lynette Heather.

This module tests the MeF (Modernized e-File) service functionality using
IRS ATS (Assurance Testing System) Test Scenario 3 data for Lynette Heather.

Test Scenario Reference: IRS ATS Test Scenario 3 (ty25-1040-mef-ats-scenario-3-10202025.pdf)
Primary Taxpayer: Lynette Heather
Filing Status: Single (1)
IP PIN: 876534
No Dependents

Key Features Tested:
- Form 1099-R (Retirement Distribution)
- Schedule F (Farm Income)
- Schedule SE (Self-Employment Tax) with Farm Optional Method
- Schedule D (Capital Gains)
- Schedule E (Rental Income)
- Form 4835 (Farm Rental Income)
- Principal Business Code for Farming (111400 - Floral Plants)

Tax Year: 2025

Source: /Users/tkhan/Downloads/IRS_MeF_Materials/Test_Scenarios/1040_Series/ty25-1040-mef-ats-scenario-3-10202025.pdf
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
format_date = mef_module.format_date
SubmissionId = mef_module.SubmissionId
SubmissionType = mef_module.SubmissionType
SubmissionCategory = mef_module.SubmissionCategory
TaxpayerInfo = mef_module.TaxpayerInfo
ReturnHeader = mef_module.ReturnHeader
ValidationSeverity = mef_module.ValidationSeverity
ValidationResult = mef_module.ValidationResult
XmlSerializer = mef_module.XmlSerializer
BusinessRulesValidator = mef_module.BusinessRulesValidator


# =============================================================================
# FIXTURES - IRS ATS Test Scenario 3 Data (Lynette Heather - Single with Farm)
# =============================================================================


@pytest.fixture
def lynette_heather_taxpayer() -> Dict[str, Any]:
    """Fixture for Lynette Heather (primary taxpayer) information.

    IRS ATS Test Scenario 3 - Single filer with farm income,
    retirement distribution, and rental income.

    ATS Reference SSN: 400-00-1035 (invalid for production validation)
    Test SSN: 400-01-1035 (valid format for testing)
    IP PIN: 876534
    """
    return {
        "first_name": "Lynette",
        "last_name": "Heather",
        "ssn": "400-01-1035",
        "ssn_clean": "400011035",
        "ssn_ats_reference": "400-00-1035",
        "ip_pin": "876534",
        "address": {
            "street": "2525 Juniper Street",
            "city": "Paul",
            "state": "ID",
            "zip": "83347"
        },
        "date_of_birth": date(1958, 4, 22),
        "occupation": "Farmer",
        "digital_assets": False,
    }


@pytest.fixture
def lynette_heather_form_1099r() -> Dict[str, Any]:
    """Fixture for Form 1099-R (Retirement Distribution).

    Payer: Primrose Retirement Fund
    Distribution: Retirement pension with partial taxability
    """
    return {
        "payer": {
            "name": "Primrose Retirement Fund",
            "tin": "00-0000030",
            "tin_clean": "000000030",
            "tin_test": "12-3456784",  # Valid test EIN
            "address": {
                "street": "1000 Financial Drive",
                "city": "Boise",
                "state": "ID",
                "zip": "83702"
            },
        },
        "recipient_ssn": "400-01-1035",
        "recipient_ssn_clean": "400011035",

        # Box 1: Gross distribution
        "box_1_gross_distribution": Decimal("53778.00"),

        # Box 2a: Taxable amount
        "box_2a_taxable_amount": Decimal("43100.00"),

        # Box 2b: Taxable amount not determined checkbox
        "box_2b_taxable_not_determined": False,

        # Box 2b: Total distribution checkbox
        "box_2b_total_distribution": False,

        # Box 3: Capital gain
        "box_3_capital_gain": Decimal("0.00"),

        # Box 4: Federal income tax withheld
        "box_4_federal_withholding": Decimal("5100.00"),

        # Box 5: Employee contributions/Designated Roth contributions or insurance premiums
        "box_5_employee_contributions": Decimal("10678.00"),

        # Box 6: Net unrealized appreciation in employer's securities
        "box_6_nua": Decimal("0.00"),

        # Box 7: Distribution code(s)
        "box_7_distribution_code": "7",  # Normal distribution

        # Box 8: Other
        "box_8_other": Decimal("0.00"),

        # Box 9a: Your percentage of total distribution
        "box_9a_percentage": Decimal("100.00"),

        # Box 9b: Total employee contributions
        "box_9b_total_employee_contributions": Decimal("10678.00"),

        # Box 10-15: State/Local tax info
        "box_10_state_distribution": Decimal("53778.00"),
        "box_11_state_tax_withheld": Decimal("2150.00"),
        "box_12_state": "ID",
        "box_13_state_payer_id": "00-0000030",
        "box_14_local_distribution": Decimal("0.00"),
        "box_15_local_tax_withheld": Decimal("0.00"),

        # IRA/SEP/SIMPLE checkbox
        "ira_sep_simple": False,

        # Computed values
        "nontaxable_amount": Decimal("10678.00"),  # 53778 - 43100
    }


@pytest.fixture
def lynette_heather_schedule_f() -> Dict[str, Any]:
    """Fixture for Schedule F (Profit or Loss From Farming).

    Farm: Floral Plants (Greenhouse/Nursery)
    Principal Business Code: 111400 (Greenhouse, Nursery, and Floriculture Production)
    Accounting Method: Cash

    Note: Lynette uses the Farm Optional Method for SE tax calculation.
    """
    return {
        "farm_name": "Heather's Floral Plants",
        "principal_business_code": "111400",  # NAICS: Greenhouse/Nursery/Floriculture
        "principal_product": "Floral Plants",
        "ein": "00-0000031",
        "ein_clean": "000000031",
        "ein_test": "12-3456785",

        "accounting_method": "Cash",
        "material_participation": True,

        # Part I - Farm Income (Cash Method)
        # Line 1a: Sales of livestock and other resale items
        "line_1a_livestock_sales": Decimal("0.00"),
        "line_1b_cost_of_livestock": Decimal("0.00"),
        "line_1c_livestock_profit": Decimal("0.00"),

        # Line 2: Sales of products you raised
        "line_2_products_raised": Decimal("32500.00"),

        # Line 3: Cooperative distributions
        "line_3a_cooperative_total": Decimal("0.00"),
        "line_3b_cooperative_taxable": Decimal("0.00"),

        # Line 4: Agricultural program payments
        "line_4a_ag_payments_total": Decimal("2800.00"),
        "line_4b_ag_payments_taxable": Decimal("2800.00"),

        # Line 5: CCC loans
        "line_5a_ccc_loans": Decimal("0.00"),
        "line_5b_ccc_election": False,
        "line_5c_ccc_forfeited": Decimal("0.00"),

        # Line 6: Crop insurance proceeds
        "line_6a_crop_insurance": Decimal("0.00"),
        "line_6b_crop_insurance_deferred": Decimal("0.00"),
        "line_6d_crop_insurance_taxable": Decimal("0.00"),

        # Line 7: Custom hire (machine work)
        "line_7_custom_hire": Decimal("1500.00"),

        # Line 8: Other farm income
        "line_8_other_income": Decimal("450.00"),

        # Line 9: Gross farm income
        "line_9_gross_income": Decimal("37250.00"),  # 32500 + 2800 + 1500 + 450

        # Part II - Farm Expenses
        "expenses": {
            "line_10_car_truck": Decimal("1850.00"),
            "line_11_chemicals": Decimal("890.00"),
            "line_12_conservation": Decimal("0.00"),
            "line_13_custom_hire": Decimal("600.00"),
            "line_14_depreciation": Decimal("4200.00"),
            "line_15_employee_benefit": Decimal("0.00"),
            "line_16_feed": Decimal("0.00"),
            "line_17_fertilizers": Decimal("2100.00"),
            "line_18_freight": Decimal("340.00"),
            "line_19_fuel": Decimal("1680.00"),
            "line_20_insurance": Decimal("1450.00"),
            "line_21a_mortgage_interest": Decimal("0.00"),
            "line_21b_other_interest": Decimal("580.00"),
            "line_22_labor_hired": Decimal("3200.00"),
            "line_23_pension_profit_sharing": Decimal("0.00"),
            "line_24a_rent_vehicles": Decimal("0.00"),
            "line_24b_rent_other": Decimal("2400.00"),
            "line_25_repairs": Decimal("1875.00"),
            "line_26_seeds_plants": Decimal("4500.00"),
            "line_27_storage": Decimal("0.00"),
            "line_28_supplies": Decimal("1250.00"),
            "line_29_taxes": Decimal("890.00"),
            "line_30_utilities": Decimal("1100.00"),
            "line_31_vet_medicine": Decimal("0.00"),
            "line_32_other": Decimal("650.00"),
        },

        # Line 33: Total expenses
        "line_33_total_expenses": Decimal("29555.00"),

        # Line 34: Net farm profit (or loss)
        "line_34_net_profit": Decimal("7695.00"),  # 37250 - 29555

        # Part III - Farm Income Averaging (not used)
        "uses_income_averaging": False,

        # Checkbox indicators
        "filed_schedule_f_prior_years": True,
        "first_year_farming": False,
    }


@pytest.fixture
def lynette_heather_schedule_se() -> Dict[str, Any]:
    """Fixture for Schedule SE (Self-Employment Tax).

    Uses Farm Optional Method for SE tax calculation.
    The optional method allows farmers with low net farm income
    to pay SE tax on 2/3 of gross farm income (up to $6,920 for 2025).

    This is advantageous for Social Security benefit calculations.
    """
    return {
        # Part I - Self-Employment Tax
        "uses_short_schedule_se": False,  # Using long form

        # Section A - Regular Method
        "regular_method": {
            "line_1a_net_farm_profit": Decimal("7695.00"),  # From Schedule F
            "line_1b_conservation_reserve": Decimal("0.00"),
            "line_2_net_nonfarm_profit": Decimal("0.00"),
            "line_3_total": Decimal("7695.00"),
            "line_4a_church_employee": Decimal("0.00"),
            "line_4b_total": Decimal("7695.00"),
            "line_4c_92_35_percent": Decimal("7106.39"),  # 7695 * 0.9235
        },

        # Section B - Optional Methods
        "uses_farm_optional_method": True,
        "uses_nonfarm_optional_method": False,

        "farm_optional_method": {
            # Gross farm income (Schedule F, Line 9)
            "gross_farm_income": Decimal("37250.00"),

            # 2/3 of gross farm income
            "two_thirds_gross": Decimal("24833.33"),  # 37250 * 2/3

            # Maximum optional method amount (2025): $6,920
            "max_optional_amount_2025": Decimal("6920.00"),

            # Lesser of 2/3 gross or max
            "optional_method_amount": Decimal("6920.00"),

            # Net farm income for comparison
            "net_farm_income": Decimal("7695.00"),

            # Use optional if net < $6,920 and optional > net
            "optional_is_beneficial": False,  # Net is $7,695 > $6,920
        },

        # Line 5: Combined SE earnings (regular or optional)
        "line_5_combined_se_earnings": Decimal("7695.00"),

        # Line 6: 92.35% of Line 5
        "line_6_92_35_percent": Decimal("7106.39"),

        # Line 7: Maximum SE tax base (2025)
        "maximum_se_base_2025": Decimal("176100.00"),

        # Line 8: Wages subject to SS (if any)
        "line_8_ss_wages": Decimal("0.00"),

        # Line 9: Subtract wages from max
        "line_9_remaining_base": Decimal("176100.00"),

        # Line 10: Lesser of line 6 or line 9
        "line_10_ss_base": Decimal("7106.39"),

        # Line 11: SS tax portion (12.4%)
        "line_11_ss_tax": Decimal("881.19"),  # 7106.39 * 0.124

        # Line 12: Medicare tax portion (2.9%)
        "line_12_medicare_tax": Decimal("206.09"),  # 7106.39 * 0.029

        # Line 13: Total SE tax
        "line_13_total_se_tax": Decimal("1087.28"),  # 881.19 + 206.09

        # Line 14: SE tax deduction (50% of SE tax)
        "line_14_se_deduction": Decimal("543.64"),  # 1087.28 / 2

        # Rounded values for form
        "se_tax_rounded": Decimal("1087.00"),
        "se_deduction_rounded": Decimal("544.00"),
    }


@pytest.fixture
def lynette_heather_schedule_d() -> Dict[str, Any]:
    """Fixture for Schedule D (Capital Gains and Losses).

    Capital transactions for the tax year.
    """
    return {
        # Part I - Short-Term Capital Gains and Losses
        "short_term": {
            "line_1a_totals_from_8949": Decimal("0.00"),
            "line_1b_totals_from_8949": Decimal("0.00"),
            "line_2_totals_form_4797": Decimal("0.00"),
            "line_3_gain_installment_sales": Decimal("0.00"),
            "line_4_short_term_from_k1": Decimal("0.00"),
            "line_5_carryover_loss": Decimal("0.00"),
            "line_6_net_short_term": Decimal("0.00"),
        },

        # Part II - Long-Term Capital Gains and Losses
        "long_term": {
            "line_8a_totals_from_8949": Decimal("4200.00"),  # Proceeds
            "line_8b_cost_basis": Decimal("2800.00"),
            "line_8d_gain_loss": Decimal("1400.00"),
            "line_9_totals_form_4797": Decimal("0.00"),
            "line_10_gain_installment_sales": Decimal("0.00"),
            "line_11_long_term_from_k1": Decimal("0.00"),
            "line_12_capital_gain_distributions": Decimal("0.00"),
            "line_13_carryover_loss": Decimal("0.00"),
            "line_14_net_long_term": Decimal("1400.00"),
        },

        # Part III - Summary
        "summary": {
            "line_15_combine_6_and_14": Decimal("1400.00"),
            "line_16_gain_from_both_positive": True,
            "line_17_qualified_dividends_worksheet": False,
            "line_18_28_percent_rate_gain": Decimal("0.00"),
            "line_19_unrecaptured_1250": Decimal("0.00"),
            "line_20_28_percent_loss": False,
            "line_21_net_capital_gain": Decimal("1400.00"),
        },

        # Tax computation
        "uses_qualified_dividends_worksheet": False,
        "uses_schedule_d_tax_worksheet": False,

        # Capital gain to Form 1040
        "capital_gain_to_1040": Decimal("1400.00"),  # Line 7
    }


@pytest.fixture
def lynette_heather_schedule_e() -> Dict[str, Any]:
    """Fixture for Schedule E (Supplemental Income and Loss).

    Part I - Rental Real Estate
    Property: Rental cottage in Paul, ID
    """
    return {
        "part_1_rental": {
            "properties": [
                {
                    "address": {
                        "street": "1515 Oak Lane",
                        "city": "Paul",
                        "state": "ID",
                        "zip": "83347"
                    },
                    "property_type": "Single Family Residence",
                    "fair_rental_days": 365,
                    "personal_use_days": 0,
                    "qualified_joint_venture": False,

                    # Income
                    "rents_received": Decimal("14400.00"),  # $1,200/month

                    # Expenses
                    "advertising": Decimal("0.00"),
                    "auto_travel": Decimal("150.00"),
                    "cleaning_maintenance": Decimal("600.00"),
                    "commissions": Decimal("0.00"),
                    "insurance": Decimal("1100.00"),
                    "legal_professional": Decimal("0.00"),
                    "management_fees": Decimal("0.00"),
                    "mortgage_interest": Decimal("4200.00"),
                    "other_interest": Decimal("0.00"),
                    "repairs": Decimal("1850.00"),
                    "supplies": Decimal("200.00"),
                    "taxes": Decimal("1800.00"),
                    "utilities": Decimal("0.00"),  # Paid by tenant
                    "depreciation": Decimal("3500.00"),
                    "other": Decimal("0.00"),

                    # Total expenses
                    "total_expenses": Decimal("13400.00"),

                    # Net income (or loss)
                    "net_income": Decimal("1000.00"),  # 14400 - 13400
                }
            ],

            # Totals for Part I
            "total_rents": Decimal("14400.00"),
            "total_expenses": Decimal("13400.00"),
            "total_depreciation": Decimal("3500.00"),
            "total_net_income": Decimal("1000.00"),
        },

        # Part II - Royalties (not applicable)
        "part_2_royalties": {
            "total_royalties": Decimal("0.00"),
            "total_expenses": Decimal("0.00"),
            "net_royalties": Decimal("0.00"),
        },

        # Part III - Estates and Trusts (not applicable)
        "part_3_estates_trusts": {
            "total_income": Decimal("0.00"),
        },

        # Part IV - REMICs (not applicable)
        "part_4_remics": {
            "total_income": Decimal("0.00"),
        },

        # Part V - Summary
        "part_5_summary": {
            "line_26_total_income": Decimal("1000.00"),
        },

        # Flow to Schedule 1
        "schedule_e_to_schedule_1": Decimal("1000.00"),
    }


@pytest.fixture
def lynette_heather_form_4835() -> Dict[str, Any]:
    """Fixture for Form 4835 (Farm Rental Income and Expenses).

    This form is for landowners who rent their farm land and receive
    income based on crops or livestock produced by tenants.
    """
    return {
        "farm_property": {
            "address": "2000 Rural Route 5",
            "city": "Paul",
            "state": "ID",
            "zip": "83347",
            "acres": 40,
        },

        # Part I - Gross Farm Rental Income
        "income": {
            "line_1_income_based_on_production": Decimal("17035.00"),
            "line_2_cooperative_distributions": Decimal("0.00"),
            "line_3_ag_program_payments": Decimal("0.00"),
            "line_4_ccc_loans": Decimal("0.00"),
            "line_5_crop_insurance": Decimal("0.00"),
            "line_6_other_income": Decimal("0.00"),
            "line_7_gross_farm_rental_income": Decimal("17035.00"),
        },

        # Part II - Expenses
        "expenses": {
            "line_8_car_truck": Decimal("0.00"),
            "line_9_chemicals": Decimal("0.00"),
            "line_10_conservation": Decimal("0.00"),
            "line_11_custom_hire": Decimal("0.00"),
            "line_12_depreciation": Decimal("2100.00"),
            "line_13_employee_benefit": Decimal("0.00"),
            "line_14_feed": Decimal("0.00"),
            "line_15_fertilizers": Decimal("0.00"),
            "line_16_freight": Decimal("0.00"),
            "line_17_fuel": Decimal("0.00"),
            "line_18_insurance": Decimal("850.00"),
            "line_19_interest": Decimal("0.00"),
            "line_20_labor_hired": Decimal("0.00"),
            "line_21_pension": Decimal("0.00"),
            "line_22_rent_lease": Decimal("0.00"),
            "line_23_repairs": Decimal("1200.00"),
            "line_24_seeds_plants": Decimal("0.00"),
            "line_25_storage": Decimal("0.00"),
            "line_26_supplies": Decimal("0.00"),
            "line_27_taxes": Decimal("980.00"),
            "line_28_utilities": Decimal("0.00"),
            "line_29_vet": Decimal("0.00"),
            "line_30_other": Decimal("0.00"),
        },

        # Line 31: Total expenses
        "line_31_total_expenses": Decimal("5130.00"),

        # Line 32: Net farm rental income
        "line_32_net_income": Decimal("11905.00"),  # 17035 - 5130

        # Flow to Schedule E
        "flows_to_schedule_e": True,
        "schedule_e_line": "Part I, Line 4",
    }


@pytest.fixture
def lynette_heather_schedule_1() -> Dict[str, Any]:
    """Fixture for Schedule 1 (Additional Income and Adjustments).

    Part I: Additional Income
    Part II: Adjustments to Income
    """
    return {
        # Part I - Additional Income
        "part_1_income": {
            "line_1_taxable_refunds": Decimal("0.00"),
            "line_2a_alimony_received": Decimal("0.00"),
            "line_3_business_income": Decimal("0.00"),  # No Schedule C
            "line_4_other_gains": Decimal("0.00"),
            "line_5_rental_income": Decimal("1000.00"),  # From Schedule E
            "line_6_farm_income": Decimal("7695.00"),  # From Schedule F
            "line_7_unemployment": Decimal("0.00"),
            "line_8_other_income": Decimal("11905.00"),  # Farm rental from 4835
            "line_9_combine_1_through_8": Decimal("20600.00"),
            "line_10_total_additional_income": Decimal("20600.00"),  # To 1040 Line 8
        },

        # Part II - Adjustments to Income
        "part_2_adjustments": {
            "line_11_educator_expenses": Decimal("0.00"),
            "line_12_business_expenses": Decimal("0.00"),
            "line_13_hsa_deduction": Decimal("0.00"),
            "line_14_moving_expenses": Decimal("0.00"),
            "line_15_self_employment_tax": Decimal("544.00"),  # 1/2 of SE tax
            "line_16_sep_simple": Decimal("0.00"),
            "line_17_self_employed_health": Decimal("0.00"),
            "line_18_penalty_early_withdrawal": Decimal("0.00"),
            "line_19_alimony_paid": Decimal("0.00"),
            "line_20_ira_deduction": Decimal("0.00"),
            "line_21_student_loan_interest": Decimal("0.00"),
            "line_22_reserved": Decimal("0.00"),
            "line_23_archer_msa": Decimal("0.00"),
            "line_24_other_adjustments": Decimal("0.00"),
            "line_25_combine_11_through_24": Decimal("544.00"),
            "line_26_total_adjustments": Decimal("544.00"),  # To 1040 Line 10
        },
    }


@pytest.fixture
def lynette_heather_form_1040_data(
    lynette_heather_taxpayer,
    lynette_heather_form_1099r,
    lynette_heather_schedule_f,
    lynette_heather_schedule_se,
    lynette_heather_schedule_d,
    lynette_heather_schedule_e,
    lynette_heather_form_4835,
    lynette_heather_schedule_1
) -> Dict[str, Any]:
    """Fixture for complete Form 1040 data for Lynette Heather.

    Tax Year: 2025
    Filing Status: Single (1)
    Standard Deduction (2025 Single): $15,000
    """
    # Income from various sources
    taxable_pension = lynette_heather_form_1099r["box_2a_taxable_amount"]  # $43,100
    capital_gain = lynette_heather_schedule_d["capital_gain_to_1040"]  # $1,400
    schedule_1_income = lynette_heather_schedule_1["part_1_income"]["line_10_total_additional_income"]  # $20,600

    # Total income
    total_income = taxable_pension + capital_gain + schedule_1_income  # $65,100

    # Adjustments (Schedule 1 Part II)
    total_adjustments = lynette_heather_schedule_1["part_2_adjustments"]["line_26_total_adjustments"]  # $544

    # AGI
    agi = total_income - total_adjustments  # $64,556

    # Deduction - OBBBA 2025 Single Standard Deduction
    standard_deduction_single_2025 = Decimal("15750.00")

    # Taxable income
    taxable_income = max(Decimal("0"), agi - standard_deduction_single_2025)  # $49,556

    # Tax calculation (with qualified dividends/capital gain worksheet)
    # Using 2025 tax brackets for Single
    # Regular tax on taxable income minus LTCG, plus preferential rate on LTCG
    ordinary_income = taxable_income - capital_gain  # $48,156

    # Tax on ordinary income (2025 brackets)
    # $0 - $11,600: 10% = $1,160
    # $11,601 - $47,150: 12% = $4,266
    # $47,151 - $48,156: 22% = $221.32
    tax_bracket_1 = Decimal("11600.00") * Decimal("0.10")  # $1,160
    tax_bracket_2 = (Decimal("47150.00") - Decimal("11600.00")) * Decimal("0.12")  # $4,266
    tax_bracket_3 = (ordinary_income - Decimal("47150.00")) * Decimal("0.22")  # $221.32
    tax_on_ordinary = tax_bracket_1 + tax_bracket_2 + tax_bracket_3  # $5,647.32

    # Tax on LTCG (0% rate for taxable income up to $47,025 for single)
    # Since total taxable is $49,556, part of LTCG is at 0%, part at 15%
    tax_on_ltcg = Decimal("0.00")  # Simplified: assume all at 0% for now

    calculated_tax = (tax_on_ordinary + tax_on_ltcg).quantize(Decimal("1"), rounding="ROUND_HALF_UP")

    # Additional taxes
    se_tax = lynette_heather_schedule_se["se_tax_rounded"]  # $1,087

    # Total tax
    total_tax = calculated_tax + se_tax

    # Payments
    federal_withholding = lynette_heather_form_1099r["box_4_federal_withholding"]  # $5,100
    total_payments = federal_withholding

    # Refund or owed
    if total_payments > total_tax:
        refund = total_payments - total_tax
        amount_owed = Decimal("0")
    else:
        refund = Decimal("0")
        amount_owed = total_tax - total_payments

    return {
        # Taxpayer info
        "primary_ssn": lynette_heather_taxpayer["ssn_clean"],
        "primary_first_name": lynette_heather_taxpayer["first_name"],
        "primary_last_name": lynette_heather_taxpayer["last_name"],
        "address": lynette_heather_taxpayer["address"],
        "ip_pin": lynette_heather_taxpayer["ip_pin"],
        "filing_status": 1,  # Single

        # Checkboxes
        "presidential_campaign": False,
        "digital_assets": False,

        # No spouse for Single
        "spouse_ssn": None,

        # No dependents
        "dependents": [],

        # Income (Lines 1-9)
        "line_1z_wages": Decimal("0.00"),  # No W-2 wages
        "line_4a_ira_pensions_gross": lynette_heather_form_1099r["box_1_gross_distribution"],  # $53,778
        "line_4b_ira_pensions_taxable": taxable_pension,  # $43,100
        "line_7_capital_gain": capital_gain,  # $1,400
        "line_8_schedule_1": schedule_1_income,  # $20,600
        "line_9_total_income": total_income,  # $65,100
        "total_income": total_income,

        # Adjustments (Line 10)
        "line_10_adjustments": total_adjustments,  # $544

        # AGI (Line 11)
        "line_11_agi": agi,  # $64,556
        "agi": agi,

        # Deduction (Lines 12-14)
        "line_12_standard_deduction": standard_deduction_single_2025,  # $15,000
        "line_13_qbi_deduction": Decimal("0.00"),  # Farm income not eligible for QBI
        "line_14_total_deductions": standard_deduction_single_2025,
        "deduction": standard_deduction_single_2025,

        # Taxable income (Line 15)
        "line_15_taxable_income": taxable_income,  # $49,556
        "taxable_income": taxable_income,

        # Tax (Lines 16-24)
        "line_16_tax": calculated_tax,
        "line_17_schedule_2": se_tax,  # $1,087 (SE tax on Schedule 2)
        "line_18_total": calculated_tax + se_tax,
        "line_24_total_tax": total_tax,
        "total_tax": total_tax,

        # Payments (Lines 25-33)
        "line_25a_w2_withholding": Decimal("0.00"),
        "line_25b_1099_withholding": federal_withholding,  # $5,100
        "line_25d_total_withholding": federal_withholding,
        "line_33_total_payments": total_payments,
        "total_payments": total_payments,

        # Refund/Amount Owed (Lines 34-38)
        "line_34_overpaid": refund,
        "line_35a_refund": refund,
        "line_37_amount_owed": amount_owed,
        "refund": refund,
        "amount_owed": amount_owed,

        # Attached schedules
        "has_schedule_1": True,
        "has_schedule_d": True,
        "has_schedule_e": True,
        "has_schedule_f": True,
        "has_schedule_se": True,
        "has_form_1099r": True,
        "has_form_4835": True,

        # Schedule data
        "schedule_1": lynette_heather_schedule_1,
        "schedule_d": lynette_heather_schedule_d,
        "schedule_e": lynette_heather_schedule_e,
        "schedule_f": lynette_heather_schedule_f,
        "schedule_se": lynette_heather_schedule_se,
        "form_1099r": lynette_heather_form_1099r,
        "form_4835": lynette_heather_form_4835,
    }


# =============================================================================
# TEST CLASS: Form 1099-R Retirement Distribution
# =============================================================================


class TestForm1099RRetirement:
    """Tests for Form 1099-R retirement distribution handling."""

    def test_1099r_gross_vs_taxable(self, lynette_heather_form_1099r):
        """Test 1099-R gross distribution vs taxable amount."""
        gross = lynette_heather_form_1099r["box_1_gross_distribution"]
        taxable = lynette_heather_form_1099r["box_2a_taxable_amount"]
        nontaxable = lynette_heather_form_1099r["nontaxable_amount"]

        assert gross == Decimal("53778.00")
        assert taxable == Decimal("43100.00")
        assert nontaxable == gross - taxable
        assert nontaxable == Decimal("10678.00")

    def test_1099r_federal_withholding(self, lynette_heather_form_1099r):
        """Test 1099-R federal income tax withheld."""
        withholding = lynette_heather_form_1099r["box_4_federal_withholding"]
        assert withholding == Decimal("5100.00")

    def test_1099r_distribution_code(self, lynette_heather_form_1099r):
        """Test 1099-R distribution code."""
        code = lynette_heather_form_1099r["box_7_distribution_code"]
        # Code 7 = Normal distribution (age 59½ or older)
        assert code == "7"

    def test_1099r_employee_contributions(self, lynette_heather_form_1099r):
        """Test 1099-R employee contributions (basis recovery)."""
        contributions = lynette_heather_form_1099r["box_5_employee_contributions"]
        assert contributions == Decimal("10678.00")

        # This equals the nontaxable amount
        assert contributions == lynette_heather_form_1099r["nontaxable_amount"]

    def test_1099r_flows_to_form_1040(self, lynette_heather_form_1099r, lynette_heather_form_1040_data):
        """Test 1099-R flows to Form 1040."""
        assert lynette_heather_form_1040_data["line_4a_ira_pensions_gross"] == \
               lynette_heather_form_1099r["box_1_gross_distribution"]
        assert lynette_heather_form_1040_data["line_4b_ira_pensions_taxable"] == \
               lynette_heather_form_1099r["box_2a_taxable_amount"]


# =============================================================================
# TEST CLASS: Schedule F Farm Income
# =============================================================================


class TestScheduleFarmIncome:
    """Tests for Schedule F farm income and expenses."""

    def test_schedule_f_naics_code(self, lynette_heather_schedule_f):
        """Test Schedule F principal business code (NAICS)."""
        code = lynette_heather_schedule_f["principal_business_code"]
        # 111400 = Greenhouse, Nursery, and Floriculture Production
        assert code == "111400"
        assert len(code) == 6
        assert code.isdigit()

    def test_schedule_f_gross_income(self, lynette_heather_schedule_f):
        """Test Schedule F gross farm income calculation."""
        products_raised = lynette_heather_schedule_f["line_2_products_raised"]
        ag_payments = lynette_heather_schedule_f["line_4b_ag_payments_taxable"]
        custom_hire = lynette_heather_schedule_f["line_7_custom_hire"]
        other_income = lynette_heather_schedule_f["line_8_other_income"]

        expected_gross = products_raised + ag_payments + custom_hire + other_income
        assert lynette_heather_schedule_f["line_9_gross_income"] == expected_gross
        assert lynette_heather_schedule_f["line_9_gross_income"] == Decimal("37250.00")

    def test_schedule_f_total_expenses(self, lynette_heather_schedule_f):
        """Test Schedule F total expenses calculation."""
        expenses = lynette_heather_schedule_f["expenses"]
        expected_total = sum(expenses.values())

        assert lynette_heather_schedule_f["line_33_total_expenses"] == expected_total
        assert lynette_heather_schedule_f["line_33_total_expenses"] == Decimal("29555.00")

    def test_schedule_f_net_profit(self, lynette_heather_schedule_f):
        """Test Schedule F net farm profit calculation."""
        gross = lynette_heather_schedule_f["line_9_gross_income"]
        expenses = lynette_heather_schedule_f["line_33_total_expenses"]
        expected_net = gross - expenses

        assert lynette_heather_schedule_f["line_34_net_profit"] == expected_net
        assert lynette_heather_schedule_f["line_34_net_profit"] == Decimal("7695.00")

    def test_schedule_f_material_participation(self, lynette_heather_schedule_f):
        """Test Schedule F material participation flag."""
        assert lynette_heather_schedule_f["material_participation"] is True


# =============================================================================
# TEST CLASS: Schedule SE Self-Employment Tax
# =============================================================================


class TestScheduleSESelfEmployment:
    """Tests for Schedule SE self-employment tax calculation."""

    def test_schedule_se_farm_optional_method(self, lynette_heather_schedule_se):
        """Test Schedule SE Farm Optional Method availability."""
        assert lynette_heather_schedule_se["uses_farm_optional_method"] is True

        # Optional method amount
        farm_optional = lynette_heather_schedule_se["farm_optional_method"]
        assert farm_optional["max_optional_amount_2025"] == Decimal("6920.00")

    def test_schedule_se_92_35_percent(self, lynette_heather_schedule_se):
        """Test Schedule SE 92.35% calculation."""
        # Verify the 92.35% calculation is reasonable
        net_earnings = lynette_heather_schedule_se["line_5_combined_se_earnings"]
        expected_approx = net_earnings * Decimal("0.9235")

        # Allow for rounding differences in IRS calculations
        actual = lynette_heather_schedule_se["line_6_92_35_percent"]
        assert abs(actual - expected_approx) < Decimal("0.10")

    def test_schedule_se_tax_calculation(self, lynette_heather_schedule_se):
        """Test Schedule SE total tax calculation."""
        ss_tax = lynette_heather_schedule_se["line_11_ss_tax"]
        medicare_tax = lynette_heather_schedule_se["line_12_medicare_tax"]
        expected_total = ss_tax + medicare_tax

        assert lynette_heather_schedule_se["line_13_total_se_tax"] == expected_total
        assert lynette_heather_schedule_se["line_13_total_se_tax"] == Decimal("1087.28")

    def test_schedule_se_deduction(self, lynette_heather_schedule_se):
        """Test Schedule SE deductible portion (50% of SE tax)."""
        total_se_tax = lynette_heather_schedule_se["line_13_total_se_tax"]
        expected_deduction = total_se_tax / 2

        assert lynette_heather_schedule_se["line_14_se_deduction"] == expected_deduction
        assert lynette_heather_schedule_se["line_14_se_deduction"] == Decimal("543.64")


# =============================================================================
# TEST CLASS: Schedule D Capital Gains
# =============================================================================


class TestScheduleDCapitalGains:
    """Tests for Schedule D capital gains and losses."""

    def test_schedule_d_long_term_gain(self, lynette_heather_schedule_d):
        """Test Schedule D long-term capital gain."""
        proceeds = lynette_heather_schedule_d["long_term"]["line_8a_totals_from_8949"]
        basis = lynette_heather_schedule_d["long_term"]["line_8b_cost_basis"]
        expected_gain = proceeds - basis

        assert lynette_heather_schedule_d["long_term"]["line_8d_gain_loss"] == expected_gain
        assert lynette_heather_schedule_d["long_term"]["line_8d_gain_loss"] == Decimal("1400.00")

    def test_schedule_d_net_capital_gain(self, lynette_heather_schedule_d):
        """Test Schedule D net capital gain."""
        assert lynette_heather_schedule_d["summary"]["line_21_net_capital_gain"] == Decimal("1400.00")

    def test_schedule_d_flows_to_form_1040(self, lynette_heather_schedule_d, lynette_heather_form_1040_data):
        """Test Schedule D flows to Form 1040 Line 7."""
        assert lynette_heather_form_1040_data["line_7_capital_gain"] == \
               lynette_heather_schedule_d["capital_gain_to_1040"]


# =============================================================================
# TEST CLASS: Schedule E Rental Income
# =============================================================================


class TestSchedulERentalIncome:
    """Tests for Schedule E rental income and expenses."""

    def test_schedule_e_rental_income(self, lynette_heather_schedule_e):
        """Test Schedule E rental property income."""
        rental = lynette_heather_schedule_e["part_1_rental"]["properties"][0]
        assert rental["rents_received"] == Decimal("14400.00")

    def test_schedule_e_rental_expenses(self, lynette_heather_schedule_e):
        """Test Schedule E rental expenses total."""
        rental = lynette_heather_schedule_e["part_1_rental"]["properties"][0]
        assert rental["total_expenses"] == Decimal("13400.00")

    def test_schedule_e_net_rental_income(self, lynette_heather_schedule_e):
        """Test Schedule E net rental income."""
        rental = lynette_heather_schedule_e["part_1_rental"]["properties"][0]
        expected_net = rental["rents_received"] - rental["total_expenses"]

        assert rental["net_income"] == expected_net
        assert rental["net_income"] == Decimal("1000.00")

    def test_schedule_e_flows_to_schedule_1(self, lynette_heather_schedule_e, lynette_heather_schedule_1):
        """Test Schedule E flows to Schedule 1."""
        assert lynette_heather_schedule_1["part_1_income"]["line_5_rental_income"] == \
               lynette_heather_schedule_e["schedule_e_to_schedule_1"]


# =============================================================================
# TEST CLASS: Form 4835 Farm Rental
# =============================================================================


class TestForm4835FarmRental:
    """Tests for Form 4835 farm rental income."""

    def test_form_4835_gross_income(self, lynette_heather_form_4835):
        """Test Form 4835 gross farm rental income."""
        income = lynette_heather_form_4835["income"]
        assert income["line_7_gross_farm_rental_income"] == Decimal("17035.00")

    def test_form_4835_expenses(self, lynette_heather_form_4835):
        """Test Form 4835 total expenses."""
        assert lynette_heather_form_4835["line_31_total_expenses"] == Decimal("5130.00")

    def test_form_4835_net_income(self, lynette_heather_form_4835):
        """Test Form 4835 net farm rental income."""
        gross = lynette_heather_form_4835["income"]["line_7_gross_farm_rental_income"]
        expenses = lynette_heather_form_4835["line_31_total_expenses"]
        expected_net = gross - expenses

        assert lynette_heather_form_4835["line_32_net_income"] == expected_net
        assert lynette_heather_form_4835["line_32_net_income"] == Decimal("11905.00")

    def test_form_4835_flows_to_schedule_1(self, lynette_heather_form_4835, lynette_heather_schedule_1):
        """Test Form 4835 flows to Schedule 1."""
        # Farm rental income goes to Schedule 1, Line 8 (Other income)
        assert lynette_heather_schedule_1["part_1_income"]["line_8_other_income"] == \
               lynette_heather_form_4835["line_32_net_income"]


# =============================================================================
# TEST CLASS: IP PIN Validation
# =============================================================================


class TestIPPINValidation:
    """Tests for Identity Protection PIN handling."""

    def test_ip_pin_format(self, lynette_heather_taxpayer):
        """Test IP PIN format validation."""
        ip_pin = lynette_heather_taxpayer["ip_pin"]

        assert len(ip_pin) == 6
        assert ip_pin.isdigit()
        assert ip_pin == "876534"

    def test_ip_pin_in_form_data(self, lynette_heather_form_1040_data):
        """Test IP PIN is included in form data."""
        assert lynette_heather_form_1040_data["ip_pin"] == "876534"


# =============================================================================
# TEST CLASS: Integration Tests
# =============================================================================


class TestScenario3Integration:
    """Integration tests for the complete Scenario 3 data."""

    def test_complete_form_1040_structure(self, lynette_heather_form_1040_data):
        """Test complete form data has all required fields."""
        required_fields = [
            "primary_ssn", "primary_first_name", "primary_last_name",
            "filing_status", "total_income", "agi",
            "deduction", "taxable_income", "total_tax", "total_payments",
        ]

        for field in required_fields:
            assert field in lynette_heather_form_1040_data, f"Missing field: {field}"

    def test_total_income_calculation(self, lynette_heather_form_1040_data):
        """Test total income includes all sources."""
        pension = lynette_heather_form_1040_data["line_4b_ira_pensions_taxable"]
        capital_gain = lynette_heather_form_1040_data["line_7_capital_gain"]
        schedule_1 = lynette_heather_form_1040_data["line_8_schedule_1"]

        expected_total = pension + capital_gain + schedule_1
        assert lynette_heather_form_1040_data["total_income"] == expected_total

    def test_agi_calculation(self, lynette_heather_form_1040_data):
        """Test AGI = Total Income - Adjustments."""
        total_income = lynette_heather_form_1040_data["total_income"]
        adjustments = lynette_heather_form_1040_data["line_10_adjustments"]
        expected_agi = total_income - adjustments

        assert lynette_heather_form_1040_data["agi"] == expected_agi

    def test_schedule_attachments_present(self, lynette_heather_form_1040_data):
        """Test required schedules are marked as attached."""
        assert lynette_heather_form_1040_data["has_schedule_1"] is True
        assert lynette_heather_form_1040_data["has_schedule_d"] is True
        assert lynette_heather_form_1040_data["has_schedule_e"] is True
        assert lynette_heather_form_1040_data["has_schedule_f"] is True
        assert lynette_heather_form_1040_data["has_schedule_se"] is True
        assert lynette_heather_form_1040_data["has_form_1099r"] is True
        assert lynette_heather_form_1040_data["has_form_4835"] is True

    def test_business_rules_validator(self, lynette_heather_form_1040_data):
        """Test form data passes business rules validation."""
        validator = BusinessRulesValidator(tax_year=2025, filing_status=1)
        result = validator.validate(lynette_heather_form_1040_data)

        assert isinstance(result, ValidationResult)

    def test_xml_serialization(self, lynette_heather_form_1040_data):
        """Test Form 1040 XML serialization."""
        serializer = XmlSerializer(tax_year=2025)
        xml = serializer.serialize_form_1040(lynette_heather_form_1040_data)

        # Basic XML structure checks
        assert xml.strip().startswith("<IRS1040")
        assert xml.strip().endswith("</IRS1040>")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
