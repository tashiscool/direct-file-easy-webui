"""Prior Year Tax Return Import Service.

Imports data from prior year tax returns (JSON/PDF) and carries forward
relevant information like names, addresses, dependents, and employers.
"""

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path


class ImportSource(Enum):
    """Supported import sources."""
    JSON_EXPORT = "json_export"  # Our own JSON export format
    IRS_TRANSCRIPT = "irs_transcript"  # IRS transcript data
    TURBOTAX = "turbotax"
    HR_BLOCK = "hrblock"
    TAXACT = "taxact"
    FREETAXUSA = "freetaxusa"


@dataclass
class CarryForwardField:
    """A field that can be carried forward from prior year."""
    field_path: str
    field_name: str
    prior_value: Any
    suggested_value: Any
    carry_forward_type: str  # 'exact', 'adjusted', 'reference'
    confidence: float
    notes: str = ""


@dataclass
class PriorYearData:
    """Extracted data from prior year return."""
    tax_year: int
    filing_status: str

    # Personal Information
    primary_taxpayer: Dict[str, Any] = field(default_factory=dict)
    spouse: Optional[Dict[str, Any]] = None
    dependents: List[Dict[str, Any]] = field(default_factory=list)

    # Address
    address: Dict[str, Any] = field(default_factory=dict)

    # Income Sources
    employers: List[Dict[str, Any]] = field(default_factory=list)
    interest_payers: List[Dict[str, Any]] = field(default_factory=list)
    dividend_payers: List[Dict[str, Any]] = field(default_factory=list)
    retirement_payers: List[Dict[str, Any]] = field(default_factory=list)

    # Key Figures (for reference, not direct carry-forward)
    prior_agi: Optional[Decimal] = None
    prior_refund: Optional[Decimal] = None
    prior_tax_due: Optional[Decimal] = None
    prior_estimated_payments: Optional[Decimal] = None

    # Carryover Items (direct carry-forward)
    capital_loss_carryover: Optional[Decimal] = None
    nol_carryover: Optional[Decimal] = None
    charitable_carryover: Optional[Decimal] = None
    amt_credit_carryover: Optional[Decimal] = None
    foreign_tax_credit_carryover: Optional[Decimal] = None

    # Bank Account (for direct deposit)
    bank_account: Optional[Dict[str, Any]] = None


@dataclass
class ImportResult:
    """Result of prior year import."""
    success: bool
    source: ImportSource
    prior_year_data: Optional[PriorYearData]
    carry_forward_fields: List[CarryForwardField]
    warnings: List[str]
    errors: List[str]


class PriorYearImportService:
    """Service for importing and processing prior year tax return data."""

    # Fields that typically carry forward exactly
    EXACT_CARRY_FIELDS = [
        "firstName", "middleInitial", "lastName", "ssn", "dateOfBirth",
        "spouseFirstName", "spouseMiddleInitial", "spouseLastName", "spouseSSN",
        "streetAddress", "apartmentNumber", "city", "state", "zipCode",
        "bankRoutingNumber", "bankAccountNumber", "bankAccountType"
    ]

    # Fields that need age/date adjustment
    ADJUSTED_CARRY_FIELDS = [
        "dependentAge",  # Increment by 1
    ]

    # Fields that are reference only (show prior year but don't auto-fill)
    REFERENCE_FIELDS = [
        "priorYearAGI", "priorYearPIN", "priorYearRefund"
    ]

    def __init__(self):
        self.current_year = 2025

    def import_json(self, json_content: str) -> ImportResult:
        """Import from our JSON export format.

        Args:
            json_content: JSON string of prior year return data.

        Returns:
            ImportResult with extracted and carry-forward data.
        """
        warnings = []
        errors = []
        carry_forward_fields = []

        try:
            data = json.loads(json_content)
        except json.JSONDecodeError as e:
            return ImportResult(
                success=False,
                source=ImportSource.JSON_EXPORT,
                prior_year_data=None,
                carry_forward_fields=[],
                warnings=[],
                errors=[f"Invalid JSON: {str(e)}"]
            )

        # Determine tax year from data
        tax_year = data.get("taxYear", self.current_year - 1)
        if tax_year >= self.current_year:
            errors.append(f"Prior year ({tax_year}) must be before current year ({self.current_year})")
            return ImportResult(
                success=False,
                source=ImportSource.JSON_EXPORT,
                prior_year_data=None,
                carry_forward_fields=[],
                warnings=warnings,
                errors=errors
            )

        # Extract taxpayer information
        primary = self._extract_taxpayer(data, "primary")
        spouse = self._extract_taxpayer(data, "spouse") if data.get("filingStatus") in ["mfj", "mfs"] else None

        # Extract dependents with age adjustment
        dependents = []
        for dep in data.get("dependents", []):
            adjusted_dep = self._adjust_dependent(dep, tax_year)
            dependents.append(adjusted_dep)

            # Check if dependent aged out
            if adjusted_dep.get("agedOut"):
                warnings.append(f"Dependent {adjusted_dep.get('firstName', 'Unknown')} may have aged out of eligibility")

        # Extract address
        address = self._extract_address(data)

        # Extract income sources (employers, etc.)
        employers = self._extract_employers(data)
        interest_payers = self._extract_payers(data, "interest")
        dividend_payers = self._extract_payers(data, "dividends")
        retirement_payers = self._extract_payers(data, "retirement")

        # Extract carryover items
        capital_loss_carryover = self._get_decimal(data, "capitalLossCarryover")
        nol_carryover = self._get_decimal(data, "nolCarryover")
        charitable_carryover = self._get_decimal(data, "charitableCarryover")

        # Extract prior year figures for reference
        prior_agi = self._get_decimal(data, "adjustedGrossIncome") or self._get_decimal(data, "agi")
        prior_refund = self._get_decimal(data, "refundAmount")
        prior_tax_due = self._get_decimal(data, "amountOwed")

        # Bank account
        bank_account = self._extract_bank_account(data)

        # Create prior year data object
        prior_year_data = PriorYearData(
            tax_year=tax_year,
            filing_status=data.get("filingStatus", "single"),
            primary_taxpayer=primary,
            spouse=spouse,
            dependents=dependents,
            address=address,
            employers=employers,
            interest_payers=interest_payers,
            dividend_payers=dividend_payers,
            retirement_payers=retirement_payers,
            prior_agi=prior_agi,
            prior_refund=prior_refund,
            prior_tax_due=prior_tax_due,
            capital_loss_carryover=capital_loss_carryover,
            nol_carryover=nol_carryover,
            charitable_carryover=charitable_carryover,
            bank_account=bank_account
        )

        # Generate carry-forward field suggestions
        carry_forward_fields = self._generate_carry_forward_fields(prior_year_data)

        return ImportResult(
            success=True,
            source=ImportSource.JSON_EXPORT,
            prior_year_data=prior_year_data,
            carry_forward_fields=carry_forward_fields,
            warnings=warnings,
            errors=errors
        )

    def import_irs_transcript(self, transcript_text: str) -> ImportResult:
        """Import from IRS transcript text.

        Args:
            transcript_text: Text content from IRS transcript.

        Returns:
            ImportResult with extracted data.
        """
        warnings = []
        errors = []

        # Parse transcript format
        data = self._parse_transcript(transcript_text)

        if not data:
            return ImportResult(
                success=False,
                source=ImportSource.IRS_TRANSCRIPT,
                prior_year_data=None,
                carry_forward_fields=[],
                warnings=[],
                errors=["Could not parse IRS transcript format"]
            )

        # Extract available data
        tax_year = data.get("tax_year", self.current_year - 1)

        prior_year_data = PriorYearData(
            tax_year=tax_year,
            filing_status=data.get("filing_status", "single"),
            primary_taxpayer={"ssn": data.get("ssn")},
            prior_agi=data.get("agi"),
            prior_refund=data.get("refund"),
            prior_tax_due=data.get("balance_due")
        )

        # Fewer fields available from transcript
        carry_forward_fields = [
            CarryForwardField(
                field_path="/priorYearAGI",
                field_name="Prior Year AGI",
                prior_value=data.get("agi"),
                suggested_value=data.get("agi"),
                carry_forward_type="reference",
                confidence=1.0,
                notes="Used for identity verification"
            )
        ]

        return ImportResult(
            success=True,
            source=ImportSource.IRS_TRANSCRIPT,
            prior_year_data=prior_year_data,
            carry_forward_fields=carry_forward_fields,
            warnings=warnings,
            errors=errors
        )

    def apply_carry_forward(
        self,
        current_facts: Dict[str, Any],
        carry_forward_fields: List[CarryForwardField],
        field_paths: Optional[List[str]] = None
    ) -> Tuple[Dict[str, Any], List[str]]:
        """Apply carry-forward fields to current year facts.

        Args:
            current_facts: Current year fact dictionary.
            carry_forward_fields: Fields to carry forward.
            field_paths: Optional list of specific fields to apply (applies all if None).

        Returns:
            Tuple of (updated facts, list of applied field paths).
        """
        updated_facts = current_facts.copy()
        applied = []

        for cf_field in carry_forward_fields:
            if field_paths and cf_field.field_path not in field_paths:
                continue

            if cf_field.carry_forward_type == "reference":
                # Reference fields are shown but not auto-applied
                continue

            # Apply the suggested value
            updated_facts[cf_field.field_path] = cf_field.suggested_value
            applied.append(cf_field.field_path)

        return updated_facts, applied

    def _extract_taxpayer(self, data: Dict, taxpayer_type: str) -> Dict[str, Any]:
        """Extract taxpayer information."""
        prefix = "" if taxpayer_type == "primary" else "spouse"

        result = {}

        # Try various field naming conventions
        for base_field, variations in [
            ("firstName", [f"{prefix}FirstName", f"{prefix}_first_name", "firstName"]),
            ("lastName", [f"{prefix}LastName", f"{prefix}_last_name", "lastName"]),
            ("middleInitial", [f"{prefix}MiddleInitial", f"{prefix}MI", "middleInitial"]),
            ("ssn", [f"{prefix}SSN", f"{prefix}_ssn", "ssn", "socialSecurityNumber"]),
            ("dateOfBirth", [f"{prefix}DOB", f"{prefix}DateOfBirth", "dateOfBirth", "dob"]),
        ]:
            for var in variations:
                if var in data and data[var]:
                    result[base_field] = data[var]
                    break

            # Also check nested objects
            for obj_key in ["primaryTaxpayer", "taxpayer", "filer"]:
                if obj_key in data and isinstance(data[obj_key], dict):
                    obj = data[obj_key]
                    if taxpayer_type == "primary":
                        for var in [base_field, base_field.lower()]:
                            if var in obj:
                                result[base_field] = obj[var]
                                break

        return result

    def _extract_address(self, data: Dict) -> Dict[str, Any]:
        """Extract address information."""
        address = {}

        # Try direct fields
        address_fields = {
            "streetAddress": ["streetAddress", "street", "address1", "addressLine1"],
            "apartmentNumber": ["apartmentNumber", "apt", "unit", "addressLine2"],
            "city": ["city"],
            "state": ["state", "stateCode"],
            "zipCode": ["zipCode", "zip", "postalCode"]
        }

        for field, variations in address_fields.items():
            for var in variations:
                if var in data and data[var]:
                    address[field] = data[var]
                    break

            # Check nested address object
            for obj_key in ["address", "mailingAddress", "homeAddress"]:
                if obj_key in data and isinstance(data[obj_key], dict):
                    obj = data[obj_key]
                    for var in variations:
                        if var in obj and obj[var]:
                            address[field] = obj[var]
                            break

        return address

    def _extract_employers(self, data: Dict) -> List[Dict[str, Any]]:
        """Extract employer/W-2 information."""
        employers = []

        # Try various locations for W-2 data
        w2_sources = [
            data.get("w2s", []),
            data.get("w2Forms", []),
            data.get("wages", []),
            data.get("income", {}).get("w2s", []) if isinstance(data.get("income"), dict) else []
        ]

        for source in w2_sources:
            if not source:
                continue
            for w2 in source:
                employer = {
                    "employerName": w2.get("employerName") or w2.get("employer"),
                    "employerEIN": w2.get("employerEIN") or w2.get("ein"),
                    "employerAddress": w2.get("employerAddress") or w2.get("address"),
                    # Don't carry forward amounts (they change each year)
                }
                if employer.get("employerName"):
                    employers.append(employer)

        return employers

    def _extract_payers(self, data: Dict, payer_type: str) -> List[Dict[str, Any]]:
        """Extract payer information for interest/dividends/retirement."""
        payers = []

        type_keys = {
            "interest": ["1099int", "1099ints", "interestIncome", "interest"],
            "dividends": ["1099div", "1099divs", "dividendIncome", "dividends"],
            "retirement": ["1099r", "1099rs", "retirementIncome", "retirement"]
        }

        for key in type_keys.get(payer_type, []):
            source = data.get(key, [])
            if isinstance(source, dict):
                source = source.get("forms", []) or source.get("items", [])

            for item in source:
                payer = {
                    "payerName": item.get("payerName") or item.get("payer") or item.get("institutionName"),
                    "payerTIN": item.get("payerTIN") or item.get("tin") or item.get("ein"),
                }
                if payer.get("payerName"):
                    payers.append(payer)

        return payers

    def _extract_bank_account(self, data: Dict) -> Optional[Dict[str, Any]]:
        """Extract bank account for direct deposit."""
        bank_sources = [
            data.get("bankAccount"),
            data.get("directDeposit"),
            data.get("refundAccount")
        ]

        for source in bank_sources:
            if source and isinstance(source, dict):
                return {
                    "routingNumber": source.get("routingNumber") or source.get("routing"),
                    "accountNumber": source.get("accountNumber") or source.get("account"),
                    "accountType": source.get("accountType") or source.get("type", "checking")
                }

        return None

    def _adjust_dependent(self, dep: Dict, prior_year: int) -> Dict[str, Any]:
        """Adjust dependent information for current year."""
        adjusted = dep.copy()

        # Increment age
        if "age" in dep:
            adjusted["age"] = dep["age"] + (self.current_year - prior_year)

            # Check age-out thresholds
            if adjusted["age"] >= 19 and dep.get("relationship") != "student":
                adjusted["agedOut"] = True
                adjusted["agedOutReason"] = "Over 18 and not a student"
            elif adjusted["age"] >= 24 and dep.get("relationship") == "student":
                adjusted["agedOut"] = True
                adjusted["agedOutReason"] = "Over 23 as a student"

        # Calculate age from DOB if available
        if "dateOfBirth" in dep and not adjusted.get("age"):
            try:
                dob = datetime.strptime(dep["dateOfBirth"], "%Y-%m-%d")
                adjusted["age"] = self.current_year - dob.year
            except (ValueError, TypeError):
                pass

        return adjusted

    def _get_decimal(self, data: Dict, *keys: str) -> Optional[Decimal]:
        """Get a decimal value from various possible keys."""
        for key in keys:
            if key in data and data[key] is not None:
                try:
                    return Decimal(str(data[key]))
                except (ValueError, TypeError):
                    pass
        return None

    def _parse_transcript(self, text: str) -> Optional[Dict[str, Any]]:
        """Parse IRS transcript text format."""
        data = {}

        # Common transcript patterns
        patterns = {
            "tax_year": r"TAX PERIOD.*?(\d{4})",
            "filing_status": r"FILING STATUS[:\s]+(\w+)",
            "agi": r"ADJUSTED GROSS INCOME[:\s]+\$?([\d,]+)",
            "refund": r"REFUND AMOUNT[:\s]+\$?([\d,]+)",
            "ssn": r"SSN[:\s]+(XXX-XX-\d{4}|\d{3}-\d{2}-\d{4})"
        }

        for field, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = match.group(1)
                if field in ["agi", "refund"]:
                    value = Decimal(value.replace(",", ""))
                elif field == "tax_year":
                    value = int(value)
                data[field] = value

        return data if data else None

    def _generate_carry_forward_fields(self, prior_data: PriorYearData) -> List[CarryForwardField]:
        """Generate carry-forward field suggestions."""
        fields = []

        # Primary taxpayer info
        if prior_data.primary_taxpayer:
            tp = prior_data.primary_taxpayer
            if tp.get("firstName"):
                fields.append(CarryForwardField(
                    field_path="/primaryFirstName",
                    field_name="First Name",
                    prior_value=tp["firstName"],
                    suggested_value=tp["firstName"],
                    carry_forward_type="exact",
                    confidence=1.0
                ))
            if tp.get("lastName"):
                fields.append(CarryForwardField(
                    field_path="/primaryLastName",
                    field_name="Last Name",
                    prior_value=tp["lastName"],
                    suggested_value=tp["lastName"],
                    carry_forward_type="exact",
                    confidence=1.0
                ))
            if tp.get("ssn"):
                fields.append(CarryForwardField(
                    field_path="/primarySSN",
                    field_name="Social Security Number",
                    prior_value=tp["ssn"],
                    suggested_value=tp["ssn"],
                    carry_forward_type="exact",
                    confidence=1.0
                ))

        # Spouse info
        if prior_data.spouse:
            sp = prior_data.spouse
            if sp.get("firstName"):
                fields.append(CarryForwardField(
                    field_path="/spouseFirstName",
                    field_name="Spouse First Name",
                    prior_value=sp["firstName"],
                    suggested_value=sp["firstName"],
                    carry_forward_type="exact",
                    confidence=1.0
                ))

        # Address
        if prior_data.address:
            addr = prior_data.address
            if addr.get("streetAddress"):
                fields.append(CarryForwardField(
                    field_path="/streetAddress",
                    field_name="Street Address",
                    prior_value=addr["streetAddress"],
                    suggested_value=addr["streetAddress"],
                    carry_forward_type="exact",
                    confidence=0.9,
                    notes="Verify address hasn't changed"
                ))
            if addr.get("city"):
                fields.append(CarryForwardField(
                    field_path="/city",
                    field_name="City",
                    prior_value=addr["city"],
                    suggested_value=addr["city"],
                    carry_forward_type="exact",
                    confidence=0.9
                ))
            if addr.get("state"):
                fields.append(CarryForwardField(
                    field_path="/state",
                    field_name="State",
                    prior_value=addr["state"],
                    suggested_value=addr["state"],
                    carry_forward_type="exact",
                    confidence=0.9
                ))
            if addr.get("zipCode"):
                fields.append(CarryForwardField(
                    field_path="/zipCode",
                    field_name="ZIP Code",
                    prior_value=addr["zipCode"],
                    suggested_value=addr["zipCode"],
                    carry_forward_type="exact",
                    confidence=0.9
                ))

        # Filing status (as reference)
        fields.append(CarryForwardField(
            field_path="/filingStatus",
            field_name="Filing Status",
            prior_value=prior_data.filing_status,
            suggested_value=prior_data.filing_status,
            carry_forward_type="reference",
            confidence=0.8,
            notes="Verify filing status hasn't changed"
        ))

        # Carryover items (exact carry-forward)
        if prior_data.capital_loss_carryover:
            fields.append(CarryForwardField(
                field_path="/capitalLossCarryforward",
                field_name="Capital Loss Carryforward",
                prior_value=prior_data.capital_loss_carryover,
                suggested_value=prior_data.capital_loss_carryover,
                carry_forward_type="exact",
                confidence=1.0,
                notes="From Schedule D, Line 21"
            ))

        if prior_data.nol_carryover:
            fields.append(CarryForwardField(
                field_path="/nolCarryforward",
                field_name="Net Operating Loss Carryforward",
                prior_value=prior_data.nol_carryover,
                suggested_value=prior_data.nol_carryover,
                carry_forward_type="exact",
                confidence=1.0
            ))

        if prior_data.charitable_carryover:
            fields.append(CarryForwardField(
                field_path="/charitableContributionCarryover",
                field_name="Charitable Contribution Carryover",
                prior_value=prior_data.charitable_carryover,
                suggested_value=prior_data.charitable_carryover,
                carry_forward_type="exact",
                confidence=1.0
            ))

        # Prior year AGI (reference for identity verification)
        if prior_data.prior_agi:
            fields.append(CarryForwardField(
                field_path="/priorYearAGI",
                field_name="Prior Year AGI",
                prior_value=prior_data.prior_agi,
                suggested_value=prior_data.prior_agi,
                carry_forward_type="reference",
                confidence=1.0,
                notes="Used for IRS identity verification"
            ))

        # Bank account
        if prior_data.bank_account:
            ba = prior_data.bank_account
            if ba.get("routingNumber"):
                fields.append(CarryForwardField(
                    field_path="/bankRoutingNumber",
                    field_name="Bank Routing Number",
                    prior_value=ba["routingNumber"],
                    suggested_value=ba["routingNumber"],
                    carry_forward_type="exact",
                    confidence=0.95,
                    notes="For direct deposit"
                ))
            if ba.get("accountNumber"):
                # Mask account number for display
                masked = "****" + ba["accountNumber"][-4:] if len(ba["accountNumber"]) > 4 else ba["accountNumber"]
                fields.append(CarryForwardField(
                    field_path="/bankAccountNumber",
                    field_name="Bank Account Number",
                    prior_value=masked,
                    suggested_value=ba["accountNumber"],
                    carry_forward_type="exact",
                    confidence=0.95,
                    notes="For direct deposit"
                ))

        # Dependents
        for i, dep in enumerate(prior_data.dependents):
            if dep.get("agedOut"):
                continue  # Don't suggest aged-out dependents

            if dep.get("firstName"):
                fields.append(CarryForwardField(
                    field_path=f"/dependent/{i}/firstName",
                    field_name=f"Dependent {i+1} First Name",
                    prior_value=dep["firstName"],
                    suggested_value=dep["firstName"],
                    carry_forward_type="exact",
                    confidence=0.95
                ))

        # Employers (just names for reference)
        for i, emp in enumerate(prior_data.employers):
            if emp.get("employerName"):
                fields.append(CarryForwardField(
                    field_path=f"/employer/{i}/name",
                    field_name=f"Employer {i+1}",
                    prior_value=emp["employerName"],
                    suggested_value=emp["employerName"],
                    carry_forward_type="reference",
                    confidence=0.8,
                    notes="Same employer? Add W-2 when received"
                ))

        return fields
