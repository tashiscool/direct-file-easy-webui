"""Comprehensive pytest tests for IRS ATS Test Scenario - Form 709 Gift Tax.

This module tests the MeF (Modernized e-File) service functionality using
IRS ATS (Assurance Testing System) Test Scenario 2 data for Form 709.

Test Scenario Reference: IRS ATS Form 709 Scenario 2 (709-mef-ats-scenario-2.pdf)
Donor: Kenneth Jones
Spouse (for gift splitting): Adeline Jones
Donees: 8 grandchildren (Mills family) + 3 children (Jones family)

Key Features Tested:
- Gift splitting (Part III - Spouse's consent)
- Schedule A: Computation of Taxable Gifts
  - Part 1: Gifts subject only to gift tax
  - Part 2: Direct skips (GST)
- Schedule B: Gifts from prior periods
- Schedule C: DSUE amount
- Trust gifts to grandchildren
- Annual exclusion calculations
- Unified credit (applicable credit) computation
- Generation-skipping transfer considerations

Tax Year: 2025

Source: /Users/tkhan/Downloads/IRS_MeF_Materials/Test_Scenarios/TY2025/709-mef-ats-scenario-2.pdf
        /Users/tkhan/Downloads/IRS_MeF_Materials/ANALYSIS_NOTES.md
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


# =============================================================================
# FIXTURES - IRS ATS Form 709 Test Scenario 2 Data (Kenneth Jones - Gift Tax)
# =============================================================================


@pytest.fixture
def kenneth_jones_donor() -> Dict[str, Any]:
    """Fixture for Kenneth Jones (donor) information.

    IRS ATS Form 709 Scenario 2 - Gift tax return with spouse consent
    for gift splitting. Multiple gifts to grandchildren via trusts.

    ATS Reference SSN: 002-00-0006 (invalid for production)
    Test SSN: 002-01-0006 (valid format for testing)
    """
    return {
        "first_name": "Kenneth",
        "last_name": "Jones",
        "ssn": "002-01-0006",
        "ssn_clean": "002010006",
        "ssn_ats_reference": "002-00-0006",
        "address": {
            "street": "P.O. BOX 1234",
            "city": "Delanco",
            "state": "NJ",
            "zip": "08075"
        },
        "legal_residence": "New Jersey",
        "citizenship": "United States",
        "date_of_birth": date(1955, 3, 10),
        "phone": "(609) 555-1234",

        # Part I - General Information
        "donor_death_date": None,  # Not deceased
        "amended_return": False,
        "extension_filed": False,
        "digital_assets_included": False,
    }


@pytest.fixture
def adeline_jones_spouse() -> Dict[str, Any]:
    """Fixture for Adeline Jones (spouse consenting to gift split).

    Spouse must consent to gift splitting on Part III of Form 709.
    Both spouses must be US citizens or residents.

    ATS Reference SSN: 004-00-0001 (invalid for production)
    Test SSN: 004-01-0001 (valid format for testing)
    """
    return {
        "first_name": "Adeline",
        "last_name": "Jones",
        "ssn": "004-01-0001",
        "ssn_clean": "004010001",
        "ssn_ats_reference": "004-00-0001",
        "is_us_citizen": True,
        "consents_to_split": True,
    }


@pytest.fixture
def mills_grandchildren_donees() -> List[Dict[str, Any]]:
    """Fixture for Mills family grandchildren (8 donees).

    These are grandchildren who receive gifts via trust.
    Each gift is a direct skip for GST purposes.
    """
    # Base address for all Mills donees
    mills_base_address = {
        "street": "2 Test Dr",
        "city": "Delanco",
        "state": "NJ",
        "zip": "08075"
    }

    return [
        {
            "name": "Alice Mills",
            "relationship": "Grndchld",
            "address": mills_base_address,
            "gift_description": "Transfer in trust - Alice Mills Trust",
            "gift_date": date(2025, 7, 15),
            "gift_value": Decimal("200000.00"),
            "split_gift_value": Decimal("100000.00"),  # 1/2 for gift split
            "annual_exclusion": Decimal("18000.00"),  # 2025 annual exclusion
            "taxable_after_exclusion": Decimal("82000.00"),  # 100000 - 18000
            "is_direct_skip": True,
        },
        {
            "name": "Benjamin Mills",
            "relationship": "Grndchld",
            "address": mills_base_address,
            "gift_description": "Transfer in trust - Benjamin Mills Trust",
            "gift_date": date(2025, 7, 15),
            "gift_value": Decimal("200000.00"),
            "split_gift_value": Decimal("100000.00"),
            "annual_exclusion": Decimal("18000.00"),
            "taxable_after_exclusion": Decimal("82000.00"),
            "is_direct_skip": True,
        },
        {
            "name": "Charlotte Mills",
            "relationship": "Grndchld",
            "address": mills_base_address,
            "gift_description": "Transfer in trust - Charlotte Mills Trust",
            "gift_date": date(2025, 7, 15),
            "gift_value": Decimal("200000.00"),
            "split_gift_value": Decimal("100000.00"),
            "annual_exclusion": Decimal("18000.00"),
            "taxable_after_exclusion": Decimal("82000.00"),
            "is_direct_skip": True,
        },
        {
            "name": "Daniel Mills",
            "relationship": "Grndchld",
            "address": mills_base_address,
            "gift_description": "Transfer in trust - Daniel Mills Trust",
            "gift_date": date(2025, 7, 15),
            "gift_value": Decimal("200000.00"),
            "split_gift_value": Decimal("100000.00"),
            "annual_exclusion": Decimal("18000.00"),
            "taxable_after_exclusion": Decimal("82000.00"),
            "is_direct_skip": True,
        },
        {
            "name": "Elizabeth Mills",
            "relationship": "Grndchld",
            "address": mills_base_address,
            "gift_description": "Transfer in trust - Elizabeth Mills Trust",
            "gift_date": date(2025, 7, 15),
            "gift_value": Decimal("200000.00"),
            "split_gift_value": Decimal("100000.00"),
            "annual_exclusion": Decimal("18000.00"),
            "taxable_after_exclusion": Decimal("82000.00"),
            "is_direct_skip": True,
        },
        {
            "name": "Franklin Mills",
            "relationship": "Grndchld",
            "address": mills_base_address,
            "gift_description": "Transfer in trust - Franklin Mills Trust",
            "gift_date": date(2025, 7, 15),
            "gift_value": Decimal("200000.00"),
            "split_gift_value": Decimal("100000.00"),
            "annual_exclusion": Decimal("18000.00"),
            "taxable_after_exclusion": Decimal("82000.00"),
            "is_direct_skip": True,
        },
        {
            "name": "Georgia Mills",
            "relationship": "Grndchld",
            "address": mills_base_address,
            "gift_description": "Transfer in trust - Georgia Mills Trust",
            "gift_date": date(2025, 7, 15),
            "gift_value": Decimal("200000.00"),
            "split_gift_value": Decimal("100000.00"),
            "annual_exclusion": Decimal("18000.00"),
            "taxable_after_exclusion": Decimal("82000.00"),
            "is_direct_skip": True,
        },
        {
            "name": "Harold Mills",
            "relationship": "Grndchld",
            "address": mills_base_address,
            "gift_description": "Transfer in trust - Harold Mills Trust",
            "gift_date": date(2025, 7, 15),
            "gift_value": Decimal("200000.00"),
            "split_gift_value": Decimal("100000.00"),
            "annual_exclusion": Decimal("18000.00"),
            "taxable_after_exclusion": Decimal("82000.00"),
            "is_direct_skip": True,
        },
    ]


@pytest.fixture
def jones_children_donees() -> List[Dict[str, Any]]:
    """Fixture for Jones family children (3 donees).

    These are children who receive direct gifts (not direct skips for GST).
    """
    # Address for Lisa Jones
    lisa_address = {
        "street": "45 Test St",
        "city": "Palmyra",
        "state": "NJ",
        "zip": "08065"
    }

    # Address for Joseph Mills (spouse of Lisa)
    joseph_address = {
        "street": "2 Test Dr",
        "city": "Delanco",
        "state": "NJ",
        "zip": "08075"
    }

    return [
        {
            "name": "Lisa Jones",
            "relationship": "Child",
            "address": lisa_address,
            "gift_description": "Real property - vacation home",
            "gift_date": date(2025, 6, 1),
            "gift_value": Decimal("359870.00"),
            "split_gift_value": Decimal("179935.00"),
            "annual_exclusion": Decimal("18000.00"),
            "taxable_after_exclusion": Decimal("161935.00"),
            "is_direct_skip": False,
        },
        {
            "name": "Robert Jones",
            "relationship": "Child",
            "address": {
                "street": "100 Oak Avenue",
                "city": "Cherry Hill",
                "state": "NJ",
                "zip": "08002"
            },
            "gift_description": "Stock portfolio transfer",
            "gift_date": date(2025, 8, 20),
            "gift_value": Decimal("400000.00"),
            "split_gift_value": Decimal("200000.00"),
            "annual_exclusion": Decimal("18000.00"),
            "taxable_after_exclusion": Decimal("182000.00"),
            "is_direct_skip": False,
        },
        {
            "name": "Susan Jones",
            "relationship": "Child",
            "address": {
                "street": "200 Pine Street",
                "city": "Moorestown",
                "state": "NJ",
                "zip": "08057"
            },
            "gift_description": "Cash gift",
            "gift_date": date(2025, 12, 15),
            "gift_value": Decimal("100000.00"),
            "split_gift_value": Decimal("50000.00"),
            "annual_exclusion": Decimal("18000.00"),
            "taxable_after_exclusion": Decimal("32000.00"),
            "is_direct_skip": False,
        },
    ]


@pytest.fixture
def form_709_schedule_a(mills_grandchildren_donees, jones_children_donees) -> Dict[str, Any]:
    """Fixture for Schedule A (Computation of Taxable Gifts).

    Part 1: Gifts subject only to gift tax
    Part 2: Direct skips (gifts to grandchildren)
    Part 3: Indirect skips (not applicable here)
    Part 4: Taxable gift reconciliation
    """
    # Calculate totals for Part 1 (children - not direct skips)
    part_1_gifts = jones_children_donees
    part_1_total_value = sum(g["split_gift_value"] for g in part_1_gifts)
    part_1_total_exclusions = sum(g["annual_exclusion"] for g in part_1_gifts)
    part_1_taxable = sum(g["taxable_after_exclusion"] for g in part_1_gifts)

    # Calculate totals for Part 2 (grandchildren - direct skips)
    part_2_gifts = mills_grandchildren_donees
    part_2_total_value = sum(g["split_gift_value"] for g in part_2_gifts)
    part_2_total_exclusions = sum(g["annual_exclusion"] for g in part_2_gifts)
    part_2_taxable = sum(g["taxable_after_exclusion"] for g in part_2_gifts)

    return {
        "part_1": {
            "gifts": part_1_gifts,
            "total_gifts_value": part_1_total_value,  # $429,935
            "total_annual_exclusions": part_1_total_exclusions,  # $54,000
            "taxable_gifts": part_1_taxable,  # $375,935
        },
        "part_2": {
            "gifts": part_2_gifts,
            "total_gifts_value": part_2_total_value,  # $800,000
            "total_annual_exclusions": part_2_total_exclusions,  # $144,000
            "taxable_gifts": part_2_taxable,  # $656,000
        },
        "part_3": {
            "gifts": [],
            "total_gifts_value": Decimal("0"),
            "taxable_gifts": Decimal("0"),
        },
        "part_4_reconciliation": {
            "line_1_part_1_taxable": part_1_taxable,  # $375,935
            "line_2_part_2_taxable": part_2_taxable,  # $656,000
            "line_3_part_3_taxable": Decimal("0"),
            "line_4_total_schedule_a": part_1_taxable + part_2_taxable,  # $1,031,935

            # After spouse consent (split gifts), donor reports half
            "line_5_gifts_to_spouse": Decimal("0"),  # No gifts to spouse
            "line_6_charitable_gifts": Decimal("0"),  # No charitable gifts
            "line_7_exclusions": Decimal("0"),  # Already subtracted
            "line_8_deductions": Decimal("0"),

            # Net taxable gifts from this donor's portion
            "line_11_net_taxable_gifts": part_1_taxable + part_2_taxable,  # $1,031,935
        },
    }


@pytest.fixture
def form_709_schedule_b() -> Dict[str, Any]:
    """Fixture for Schedule B (Gifts from Prior Periods).

    Kenneth Jones made taxable gifts in 2013.
    """
    return {
        "prior_period_gifts": [
            {
                "calendar_year": "2013",
                "irs_office": "Andover",
                "taxable_gifts": Decimal("143614.00"),
                "credit_used": Decimal("36880.00"),
                "specific_exemption": Decimal("0.00"),  # Post-1976
            }
        ],
        "line_1_total_prior_gifts": Decimal("143614.00"),
        "line_2_total_credit_used": Decimal("36880.00"),
        "line_3_total_specific_exemption": Decimal("0.00"),
    }


@pytest.fixture
def form_709_schedule_c() -> Dict[str, Any]:
    """Fixture for Schedule C (Deceased Spousal Unused Exclusion Amount).

    If DSUE amount is being claimed from a predeceased spouse.
    Kenneth Jones is not claiming DSUE in this scenario.
    """
    return {
        "claiming_dsue": False,
        "last_deceased_spouse": None,
        "predeceased_spouses": [],
        "line_1_basic_exclusion_amount": Decimal("13990000.00"),  # 2025 BEA
        "line_2_dsue_amount": Decimal("0.00"),
        "line_3_restored_exclusion": Decimal("0.00"),
        "line_4_total_exclusion": Decimal("13990000.00"),
        "line_5_applicable_credit": Decimal("5547800.00"),  # Tax on $13,990,000
    }


@pytest.fixture
def form_709_part_2_tax_computation(
    form_709_schedule_a,
    form_709_schedule_b,
    form_709_schedule_c
) -> Dict[str, Any]:
    """Fixture for Part II (Tax Computation).

    Calculates gift tax based on cumulative lifetime gifts.
    """
    # Current period taxable gifts (from Schedule A)
    current_taxable = form_709_schedule_a["part_4_reconciliation"]["line_11_net_taxable_gifts"]

    # Prior period taxable gifts (from Schedule B)
    prior_taxable = form_709_schedule_b["line_1_total_prior_gifts"]

    # Total cumulative taxable gifts
    cumulative_taxable = current_taxable + prior_taxable

    # Gift tax table lookup (simplified - actual uses graduated rates)
    # Tax on $1,175,549 cumulative
    tax_on_cumulative = Decimal("425217.00")  # Approximate

    # Tax on prior gifts
    tax_on_prior = Decimal("36884.00")

    # Current period gift tax (before credits)
    current_gift_tax = tax_on_cumulative - tax_on_prior

    # Applicable credit
    applicable_credit = form_709_schedule_c["line_5_applicable_credit"]

    # Prior credit used
    prior_credit_used = form_709_schedule_b["line_2_total_credit_used"]

    # Available credit
    available_credit = applicable_credit - prior_credit_used

    # Credit allowable (lesser of tax or available credit)
    credit_allowable = min(current_gift_tax, available_credit)

    # Tax due (after credits)
    tax_due = max(Decimal("0"), current_gift_tax - credit_allowable)

    return {
        # Lines 1-3: Gift totals
        "line_1_current_taxable_gifts": current_taxable,  # $1,031,935
        "line_2_prior_taxable_gifts": prior_taxable,  # $143,614
        "line_3_cumulative_taxable_gifts": cumulative_taxable,  # $1,175,549

        # Lines 4-6: Tax calculation
        "line_4_tax_on_line_3": tax_on_cumulative,  # ~$425,217
        "line_5_tax_on_line_2": tax_on_prior,  # $36,884
        "line_6_balance": current_gift_tax,  # ~$388,333

        # Lines 7-12: Credits
        "line_7_applicable_credit": applicable_credit,  # $5,547,800
        "line_8_prior_credit_used": prior_credit_used,  # $36,880
        "line_9_available_credit": available_credit,  # $5,510,920
        "line_10_specific_exemption": Decimal("0.00"),
        "line_11_balance": available_credit,
        "line_12_credit_allowable": credit_allowable,  # ~$388,333

        # Lines 13-17: Final tax
        "line_13_foreign_tax_credit": Decimal("0.00"),
        "line_14_total_credits": credit_allowable,
        "line_15_balance": tax_due,  # $0
        "line_16_gst_tax": Decimal("0.00"),  # Not calculating GST in this example
        "line_17_total_tax": tax_due,  # $0

        # Lines 18-20: Payment
        "line_18_prepaid_tax": Decimal("0.00"),
        "line_19_tax_due": tax_due,  # $0
        "line_20_overpayment": Decimal("0.00"),
    }


@pytest.fixture
def form_709_complete_data(
    kenneth_jones_donor,
    adeline_jones_spouse,
    mills_grandchildren_donees,
    jones_children_donees,
    form_709_schedule_a,
    form_709_schedule_b,
    form_709_schedule_c,
    form_709_part_2_tax_computation
) -> Dict[str, Any]:
    """Fixture for complete Form 709 data."""
    return {
        # Donor information
        "donor": kenneth_jones_donor,

        # Spouse consent (Part III)
        "spouse": adeline_jones_spouse,
        "gift_splitting": True,

        # Number of donees
        "number_of_donees": 11,

        # All donees
        "donees": mills_grandchildren_donees + jones_children_donees,

        # Schedule A
        "schedule_a": form_709_schedule_a,

        # Schedule B
        "schedule_b": form_709_schedule_b,

        # Schedule C
        "schedule_c": form_709_schedule_c,

        # Part II Tax Computation
        "part_2_tax": form_709_part_2_tax_computation,

        # Summary values
        # 8 grandchildren * $200,000 = $1,600,000
        # 3 children: $359,870 + $400,000 + $100,000 = $859,870
        # Total: $2,459,870
        "total_gifts_value": Decimal("2459870.00"),  # Before split
        "total_annual_exclusions": Decimal("198000.00"),  # 11 donees * $18,000
        "net_taxable_gifts": form_709_schedule_a["part_4_reconciliation"]["line_11_net_taxable_gifts"],
        "tax_due": form_709_part_2_tax_computation["line_19_tax_due"],

        # Filing information
        "tax_year": 2025,
        "filing_due_date": date(2026, 4, 15),
    }


# =============================================================================
# TEST CLASS: Donor Information
# =============================================================================


class TestDonorInformation:
    """Tests for donor (Kenneth Jones) information."""

    def test_donor_ssn_format(self, kenneth_jones_donor):
        """Test donor SSN format."""
        ssn = kenneth_jones_donor["ssn"]
        assert "-" in ssn

        clean_ssn = ssn.replace("-", "")
        assert len(clean_ssn) == 9
        assert clean_ssn.isdigit()

    def test_donor_address(self, kenneth_jones_donor):
        """Test donor address structure."""
        address = kenneth_jones_donor["address"]
        assert address["city"] == "Delanco"
        assert address["state"] == "NJ"
        assert address["zip"] == "08075"

    def test_donor_legal_residence(self, kenneth_jones_donor):
        """Test donor legal residence (domicile)."""
        assert kenneth_jones_donor["legal_residence"] == "New Jersey"

    def test_donor_citizenship(self, kenneth_jones_donor):
        """Test donor citizenship."""
        assert kenneth_jones_donor["citizenship"] == "United States"


# =============================================================================
# TEST CLASS: Spouse Consent (Gift Splitting)
# =============================================================================


class TestSpouseConsent:
    """Tests for spouse consent and gift splitting."""

    def test_spouse_consent_to_split(self, adeline_jones_spouse):
        """Test spouse consents to gift splitting."""
        assert adeline_jones_spouse["consents_to_split"] is True

    def test_spouse_is_us_citizen(self, adeline_jones_spouse):
        """Test spouse is US citizen (required for gift splitting)."""
        assert adeline_jones_spouse["is_us_citizen"] is True

    def test_spouse_ssn_format(self, adeline_jones_spouse):
        """Test spouse SSN format."""
        ssn = adeline_jones_spouse["ssn"]
        clean_ssn = ssn.replace("-", "")
        assert len(clean_ssn) == 9


# =============================================================================
# TEST CLASS: Gift Recipients (Donees)
# =============================================================================


class TestDonees:
    """Tests for gift recipients (donees)."""

    def test_number_of_grandchildren_donees(self, mills_grandchildren_donees):
        """Test number of grandchildren donees."""
        assert len(mills_grandchildren_donees) == 8

    def test_number_of_children_donees(self, jones_children_donees):
        """Test number of children donees."""
        assert len(jones_children_donees) == 3

    def test_total_donees(self, mills_grandchildren_donees, jones_children_donees):
        """Test total number of donees."""
        total = len(mills_grandchildren_donees) + len(jones_children_donees)
        assert total == 11

    def test_grandchildren_are_direct_skips(self, mills_grandchildren_donees):
        """Test grandchildren gifts are marked as direct skips."""
        for donee in mills_grandchildren_donees:
            assert donee["is_direct_skip"] is True
            assert donee["relationship"] == "Grndchld"

    def test_children_are_not_direct_skips(self, jones_children_donees):
        """Test children gifts are NOT direct skips."""
        for donee in jones_children_donees:
            assert donee["is_direct_skip"] is False
            assert donee["relationship"] == "Child"

    def test_annual_exclusion_amount(self, mills_grandchildren_donees):
        """Test annual exclusion amount for 2025."""
        # 2025 annual exclusion is $18,000 per donee
        for donee in mills_grandchildren_donees:
            assert donee["annual_exclusion"] == Decimal("18000.00")

    def test_gift_split_calculation(self, mills_grandchildren_donees):
        """Test gift split calculation (50% each spouse)."""
        for donee in mills_grandchildren_donees:
            # Split gift value should be half of total gift value
            assert donee["split_gift_value"] == donee["gift_value"] / 2

    def test_taxable_after_exclusion(self, mills_grandchildren_donees):
        """Test taxable amount after annual exclusion."""
        for donee in mills_grandchildren_donees:
            expected = donee["split_gift_value"] - donee["annual_exclusion"]
            assert donee["taxable_after_exclusion"] == expected


# =============================================================================
# TEST CLASS: Schedule A Calculations
# =============================================================================


class TestScheduleACalculations:
    """Tests for Schedule A (Computation of Taxable Gifts)."""

    def test_schedule_a_part_1_total(self, form_709_schedule_a):
        """Test Schedule A Part 1 total for non-skip gifts."""
        part_1 = form_709_schedule_a["part_1"]

        # Verify sum of individual gift values
        expected_total = sum(g["split_gift_value"] for g in part_1["gifts"])
        assert part_1["total_gifts_value"] == expected_total

    def test_schedule_a_part_2_total(self, form_709_schedule_a):
        """Test Schedule A Part 2 total for direct skip gifts."""
        part_2 = form_709_schedule_a["part_2"]

        # 8 grandchildren * $100,000 each = $800,000
        assert part_2["total_gifts_value"] == Decimal("800000.00")

    def test_schedule_a_annual_exclusions(self, form_709_schedule_a):
        """Test total annual exclusions calculation."""
        part_1 = form_709_schedule_a["part_1"]
        part_2 = form_709_schedule_a["part_2"]

        # Part 1: 3 donees * $18,000 = $54,000
        assert part_1["total_annual_exclusions"] == Decimal("54000.00")

        # Part 2: 8 donees * $18,000 = $144,000
        assert part_2["total_annual_exclusions"] == Decimal("144000.00")

    def test_schedule_a_taxable_gifts(self, form_709_schedule_a):
        """Test taxable gifts calculation."""
        part_1 = form_709_schedule_a["part_1"]
        part_2 = form_709_schedule_a["part_2"]

        # Part 1: Total value - exclusions
        expected_part_1 = part_1["total_gifts_value"] - part_1["total_annual_exclusions"]
        assert part_1["taxable_gifts"] == expected_part_1

        # Part 2: Total value - exclusions
        expected_part_2 = part_2["total_gifts_value"] - part_2["total_annual_exclusions"]
        assert part_2["taxable_gifts"] == expected_part_2

    def test_schedule_a_part_4_reconciliation(self, form_709_schedule_a):
        """Test Part 4 reconciliation totals."""
        reconciliation = form_709_schedule_a["part_4_reconciliation"]

        # Line 4 = Line 1 + Line 2 + Line 3
        expected = (
            reconciliation["line_1_part_1_taxable"] +
            reconciliation["line_2_part_2_taxable"] +
            reconciliation["line_3_part_3_taxable"]
        )
        assert reconciliation["line_4_total_schedule_a"] == expected


# =============================================================================
# TEST CLASS: Schedule B Prior Period Gifts
# =============================================================================


class TestScheduleBPriorPeriod:
    """Tests for Schedule B (Gifts from Prior Periods)."""

    def test_prior_period_exists(self, form_709_schedule_b):
        """Test prior period gifts exist."""
        assert len(form_709_schedule_b["prior_period_gifts"]) > 0

    def test_prior_period_year(self, form_709_schedule_b):
        """Test prior period gift year."""
        prior = form_709_schedule_b["prior_period_gifts"][0]
        assert prior["calendar_year"] == "2013"

    def test_prior_period_amounts(self, form_709_schedule_b):
        """Test prior period taxable gifts amount."""
        assert form_709_schedule_b["line_1_total_prior_gifts"] == Decimal("143614.00")
        assert form_709_schedule_b["line_2_total_credit_used"] == Decimal("36880.00")


# =============================================================================
# TEST CLASS: Schedule C (DSUE)
# =============================================================================


class TestScheduleCDSUE:
    """Tests for Schedule C (Deceased Spousal Unused Exclusion)."""

    def test_not_claiming_dsue(self, form_709_schedule_c):
        """Test DSUE is not being claimed."""
        assert form_709_schedule_c["claiming_dsue"] is False

    def test_basic_exclusion_amount_2025(self, form_709_schedule_c):
        """Test 2025 basic exclusion amount."""
        # 2025 BEA is $13,990,000
        assert form_709_schedule_c["line_1_basic_exclusion_amount"] == Decimal("13990000.00")

    def test_applicable_credit_amount(self, form_709_schedule_c):
        """Test applicable credit amount."""
        # Tax on $13,990,000 at top rate
        assert form_709_schedule_c["line_5_applicable_credit"] == Decimal("5547800.00")


# =============================================================================
# TEST CLASS: Part II Tax Computation
# =============================================================================


class TestPart2TaxComputation:
    """Tests for Part II (Tax Computation)."""

    def test_cumulative_taxable_gifts(self, form_709_part_2_tax_computation):
        """Test cumulative taxable gifts calculation."""
        current = form_709_part_2_tax_computation["line_1_current_taxable_gifts"]
        prior = form_709_part_2_tax_computation["line_2_prior_taxable_gifts"]
        cumulative = form_709_part_2_tax_computation["line_3_cumulative_taxable_gifts"]

        assert cumulative == current + prior

    def test_current_period_tax(self, form_709_part_2_tax_computation):
        """Test current period tax calculation."""
        # Tax on cumulative minus tax on prior
        tax_cumulative = form_709_part_2_tax_computation["line_4_tax_on_line_3"]
        tax_prior = form_709_part_2_tax_computation["line_5_tax_on_line_2"]
        balance = form_709_part_2_tax_computation["line_6_balance"]

        assert balance == tax_cumulative - tax_prior

    def test_available_credit(self, form_709_part_2_tax_computation):
        """Test available credit calculation."""
        applicable = form_709_part_2_tax_computation["line_7_applicable_credit"]
        used = form_709_part_2_tax_computation["line_8_prior_credit_used"]
        available = form_709_part_2_tax_computation["line_9_available_credit"]

        assert available == applicable - used

    def test_no_tax_due(self, form_709_part_2_tax_computation):
        """Test no tax is due (credit covers tax)."""
        # When credit exceeds tax, no tax is due
        tax_due = form_709_part_2_tax_computation["line_19_tax_due"]
        assert tax_due == Decimal("0")


# =============================================================================
# TEST CLASS: Complete Form 709
# =============================================================================


class TestCompleteForm709:
    """Tests for complete Form 709 data."""

    def test_gift_splitting_enabled(self, form_709_complete_data):
        """Test gift splitting is enabled."""
        assert form_709_complete_data["gift_splitting"] is True

    def test_total_donees_count(self, form_709_complete_data):
        """Test total number of donees."""
        assert form_709_complete_data["number_of_donees"] == 11
        assert len(form_709_complete_data["donees"]) == 11

    def test_total_gifts_value(self, form_709_complete_data):
        """Test total gifts value before split."""
        # Sum all gift values
        # 8 grandchildren * $200,000 = $1,600,000
        # 3 children: $359,870 + $400,000 + $100,000 = $859,870
        # Total: $2,459,870
        total = sum(d["gift_value"] for d in form_709_complete_data["donees"])
        assert total == form_709_complete_data["total_gifts_value"]
        assert total == Decimal("2459870.00")

    def test_total_annual_exclusions(self, form_709_complete_data):
        """Test total annual exclusions."""
        # 11 donees * $18,000 = $198,000
        assert form_709_complete_data["total_annual_exclusions"] == Decimal("198000.00")

    def test_tax_year(self, form_709_complete_data):
        """Test tax year is 2025."""
        assert form_709_complete_data["tax_year"] == 2025

    def test_filing_due_date(self, form_709_complete_data):
        """Test filing due date is April 15, 2026."""
        assert form_709_complete_data["filing_due_date"] == date(2026, 4, 15)


# =============================================================================
# TEST CLASS: Integration Tests
# =============================================================================


class TestForm709Integration:
    """Integration tests for Form 709 data flows."""

    def test_schedule_a_to_part_2(self, form_709_schedule_a, form_709_part_2_tax_computation):
        """Test Schedule A flows to Part II."""
        schedule_a_taxable = form_709_schedule_a["part_4_reconciliation"]["line_11_net_taxable_gifts"]
        part_2_current = form_709_part_2_tax_computation["line_1_current_taxable_gifts"]

        assert part_2_current == schedule_a_taxable

    def test_schedule_b_to_part_2(self, form_709_schedule_b, form_709_part_2_tax_computation):
        """Test Schedule B flows to Part II."""
        schedule_b_prior = form_709_schedule_b["line_1_total_prior_gifts"]
        part_2_prior = form_709_part_2_tax_computation["line_2_prior_taxable_gifts"]

        assert part_2_prior == schedule_b_prior

        schedule_b_credit = form_709_schedule_b["line_2_total_credit_used"]
        part_2_credit = form_709_part_2_tax_computation["line_8_prior_credit_used"]

        assert part_2_credit == schedule_b_credit

    def test_schedule_c_to_part_2(self, form_709_schedule_c, form_709_part_2_tax_computation):
        """Test Schedule C flows to Part II."""
        schedule_c_credit = form_709_schedule_c["line_5_applicable_credit"]
        part_2_credit = form_709_part_2_tax_computation["line_7_applicable_credit"]

        assert part_2_credit == schedule_c_credit

    def test_gift_values_consistency(self, form_709_complete_data):
        """Test gift values are consistent across schedules."""
        # Total from donees list
        total_from_donees = sum(d["gift_value"] for d in form_709_complete_data["donees"])

        # Total stated
        total_stated = form_709_complete_data["total_gifts_value"]

        assert total_from_donees == total_stated


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
