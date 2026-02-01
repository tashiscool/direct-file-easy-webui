# IRS ATS Scenario Test Implementation Guide

This guide provides all the context needed to continue implementing IRS ATS (Assurance Testing System) scenario tests for the MeF (Modernized e-File) service.

## Overview

ATS scenarios are official IRS test cases used to validate e-file submissions. Each scenario represents a complete tax return with specific features (forms, schedules, credits, etc.) that must be tested for MeF compliance.

### Location
- **Test files**: `/Users/tkhan/IdeaProjects/taxes/direct-file-easy-webui/ai_service/tests/test_ats_scenario_*.py`
- **IRS PDFs**: `/Users/tkhan/Downloads/IRS_MeF_Materials/Test_Scenarios/1040_Series/`
- **MeF Service**: `/Users/tkhan/IdeaProjects/taxes/direct-file-easy-webui/ai_service/services/mef_efile_service.py`

## Scenarios Implemented

| Scenario | File | Taxpayer | SSN (ATS) | Filing Status | Key Features |
|----------|------|----------|-----------|---------------|--------------|
| 1 | `test_ats_scenario_1.py` | Tara Black | 400-00-1032 | Single | Multiple W-2s, Schedule H, Form 5695 |
| 2 | `test_ats_scenario_2.py` | John & Judy Jones | 400-00-1038 | MFJ | Deceased spouse, Schedule C (statutory), Schedule A, Form 8283 |
| 3 | `test_ats_scenario_3.py` | Lynette Heather | 400-00-1035 | Single | 1099-R, Schedule F/SE/D/E, Farm income |
| 4 | `test_ats_scenario_4.py` | Sarah Smith | 400-00-1037 | Single | Form 8835 (Solar), Form 8936 (Clean Vehicle), Form 3800 |
| 5 | `test_ats_scenario_5.py` | Bobby Barker | 400-00-1039 | HOH | Blind, 2 dependents, Form 2441, Form 8863, EIC, Form 8862, Schedule 8812 |
| 6 | `test_ats_scenario_6.py` | Juan Torres | 400-00-1041 | 1040-SS | Puerto Rico, Schedule C, Schedule SE |
| 7 | `test_ats_scenario_7.py` | Charlie Boone | 400-00-1042 | Single | Form 4868 Extension only |
| 8 | `test_ats_scenario_8.py` | Carter Lewis | 400-00-1039 | MFS | 1099-R pension/rollover, SSA-1099, Social Security taxation |
| 12 | `test_ats_scenario_12.py` | Sam Gardenia | 400-00-1212 | Single | Schedule C, Schedule SE, Form 7206, Form 7217 |
| 13 | `test_ats_scenario_13.py` | William & Nancy Birch | 400-00-1313 | MFJ | Form 8911 (EV refueling credit), Form 6251 (AMT), Schedule 3 |
| NR-1 | `test_ats_scenario_nr1.py` | Lucas LeBlanc | 123-00-1111 | MFS (1040-NR) | Nonresident alien, 2 W-2s, Schedule C, Schedule SE (Form 4361), Form 5329, Foreign address |
| NR-2 | `test_ats_scenario_nr2.py` | Genesis DeSilva | 123-00-3333 | MFS (1040-NR) | Schedule NEC (30% flat tax), Schedule OI, Schedule E (Partnership), Paid preparer |
| NR-3 | `test_ats_scenario_nr3.py` | Jace Alfaro | 123-00-4444 | Single (1040-NR) | Schedule A (Itemized), Form 8283 (Vehicle donation), Form 8888 (Refund allocation), 301.9100-2 filing |
| NR-4 | `test_ats_scenario_nr4.py` | Isaac Hill | 123-00-5555 | QSS (1040-NR) | W-2, IRA distribution, Form 5329, Form 8835 (Solar), Form 8936 (Clean Vehicle), Form 3800, Foreign address (Thailand) |
| NR-12 | `test_ats_scenario_nr12.py` | John Harrier | 123-00-1112 | MFS (1040-NR) | Schedule P (Partnership interest transfer), Schedule D, Form 8949, Foreign address (Australia) |

## Test File Structure

Each test file follows this pattern:

```python
"""Comprehensive pytest tests for IRS ATS Test Scenario X - [Taxpayer Name].

This module tests the MeF (Modernized e-File) service functionality using
IRS ATS (Assurance Testing System) Test Scenario X data for [Taxpayer Name].

Test Scenario Reference: IRS ATS Test Scenario X (ty25-1040-mef-ats-scenario-X-MMDDYYYY.pdf)
Primary Taxpayer: [Name]
Filing Status: [Status] ([Code])
[Dependents info if applicable]

Key Features Tested:
- [List of forms/schedules/features]

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

# Import from the module file using dynamic loading
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
```

## Fixture Organization

### 1. Primary Taxpayer Fixture
```python
@pytest.fixture
def taxpayer_name_taxpayer() -> Dict[str, Any]:
    """Fixture for [Name] (primary taxpayer) information."""
    return {
        "first_name": "...",
        "last_name": "...",
        "ssn": "400-01-XXXX",           # Valid format for testing
        "ssn_clean": "400011XXX",        # 9 digits, no dashes
        "ssn_ats_reference": "400-00-XXXX",  # Original ATS SSN
        "address": {
            "street": "...",
            "city": "...",
            "state": "XX",
            "zip": "XXXXX"
        },
        "date_of_birth": date(YYYY, M, D),
        "occupation": "...",
        "digital_assets": False,
        # Add any special flags: is_blind, is_bona_fide_pr_resident, etc.
    }
```

### 2. Income Source Fixtures (W-2, 1099-R, etc.)
```python
@pytest.fixture
def taxpayer_name_w2_data() -> Dict[str, Any]:
    """Fixture for W-2 data."""
    return {
        "employee_name": "...",
        "employer_name": "...",
        "employer_ein": "00-0000XXX",
        "employer_ein_clean": "00000XXXX",
        "employer_ein_test": "12-3456XXX",  # Valid test EIN
        "employer_address": {...},
        "wages": Decimal("XXXXX.XX"),
        "federal_withholding": Decimal("XXXX.XX"),
        "ss_wages": Decimal("XXXXX.XX"),
        "ss_tax": Decimal("XXX.XX"),
        "medicare_wages": Decimal("XXXXX.XX"),
        "medicare_tax": Decimal("XXX.XX"),
        "state": "XX",
        "state_wages": Decimal("XXXXX.XX"),
        "state_tax": Decimal("XXX.XX"),
    }
```

### 3. Form/Schedule Fixtures
Each form gets its own fixture with all relevant line items:
```python
@pytest.fixture
def taxpayer_name_form_XXXX() -> Dict[str, Any]:
    """Fixture for Form XXXX (Description)."""
    return {
        "line_1_description": Decimal("XXX.XX"),
        "line_2_description": Decimal("XXX.XX"),
        # ... all relevant lines
    }
```

### 4. Complete Form 1040 Fixture
Combines all other fixtures and calculates totals:
```python
@pytest.fixture
def taxpayer_name_form_1040_data(
    taxpayer_name_taxpayer,
    taxpayer_name_w2_data,
    taxpayer_name_form_xxxx,
    # ... other fixtures
) -> Dict[str, Any]:
    """Complete Form 1040 data."""
    # Calculate income, deductions, tax, credits, payments
    # Return complete dictionary with all Form 1040 lines
```

## Test Class Organization

Standard test classes for each scenario:

```python
class TestW2Income:
    """Tests for W-2 wage income."""

class TestForm[XXXX][Description]:
    """Tests for Form XXXX (Description)."""

class TestTaxCalculation:
    """Tests for Form 1040 tax calculations."""

class TestScenarioXXMLSerialization:
    """Tests for XML serialization."""

class TestScenarioXBusinessRules:
    """Tests for business rules validation."""

class TestScenarioXIntegration:
    """Integration tests for complete data flow."""
```

## Key Tax Values for 2025

### Standard Deductions
| Filing Status | Standard | Blind/65+ Additional |
|--------------|----------|---------------------|
| Single | $15,000 | $1,950 |
| MFJ | $30,000 | $1,550 each |
| MFS | $15,000 | $1,550 |
| HOH | $22,500 | $1,950 |

### Tax Brackets (Single/MFS)
- 10%: $0 - $11,600
- 12%: $11,601 - $47,150
- 22%: $47,151 - $100,525
- 24%: $100,526 - $191,950

### Tax Brackets (HOH)
- 10%: $0 - $16,550
- 12%: $16,551 - $63,100
- 22%: $63,101 - $100,500

### Self-Employment Tax Rates
- Social Security: 12.4% (on 92.35% of net earnings)
- Medicare: 2.9% (on 92.35% of net earnings)
- Additional Medicare: 0.9% (over $200,000)
- SS Wage Base 2025: $176,100

### Credit Limits
- Child Tax Credit: $2,000 per child
- ACTC: 15% of earned income over $2,500
- Dependent Care: 20-35% of up to $3,000 (1 child) or $6,000 (2+ children)
- EIC (2 children): Max ~$7,012, phaseout starts $22,200

## Filing Status Codes
- 1 = Single
- 2 = Married Filing Jointly
- 3 = Married Filing Separately
- 4 = Head of Household
- 5 = Qualifying Surviving Spouse

## Common Distribution Codes (1099-R Box 7)
- 1 = Early distribution, no exception
- 2 = Early distribution, exception applies
- 7 = Normal distribution
- G = Direct rollover to qualified plan/IRA
- H = Direct rollover from 401(k) to Roth IRA

## SSN Pattern for ATS
- ATS uses `400-00-XXXX` format (invalid for real validation)
- Tests use `400-01-XXXX` format (passes validation logic)

## Running Tests

```bash
# Run all ATS scenario tests
python -m pytest ai_service/tests/test_ats_scenario_*.py -v

# Run specific scenario
python -m pytest ai_service/tests/test_ats_scenario_5.py -v

# Run with coverage
python -m pytest ai_service/tests/test_ats_scenario_*.py --cov=ai_service/services

# Quick summary
python -m pytest ai_service/tests/test_ats_scenario_*.py --tb=no -q
```

## Extracting Data from IRS PDFs

When reading an ATS scenario PDF:

1. **Identify the taxpayer**: Name, SSN, address, filing status
2. **List all forms/schedules**: Check what's included in the scenario
3. **Extract line-by-line values**: Use Decimal for all monetary amounts
4. **Note special circumstances**: Blind, 65+, Puerto Rico resident, etc.
5. **Verify calculations**: Cross-check totals against IRS instructions

## Tips for New Scenarios

1. **Start with the PDF**: Read the entire scenario document first
2. **Create fixtures bottom-up**: Start with income sources, then forms, finally 1040
3. **Use Decimal everywhere**: Never use float for money
4. **Test calculations**: Verify line math flows correctly between forms
5. **Check business rules**: MFS can't claim EIC, HOH needs qualifying person, etc.
6. **Include flow tests**: Ensure data flows correctly from source forms to 1040

## Remaining Scenarios to Implement

Available PDFs in `/Users/tkhan/Downloads/IRS_MeF_Materials/Test_Scenarios/1040_Series/`:

### Form 1040 Scenarios (Not Yet Implemented)
All Form 1040 scenarios have been implemented.

### Form 1040-NR Scenarios (Non-Resident)
| Scenario | PDF File | Status |
|----------|----------|--------|
| NR-1 | `ty25-1040-nr-mef-ats-scenario-1-10202025.pdf` | ✅ Done |
| NR-2 | `ty25-form-1040-nr-mef-ats-scenario-2-10202025.pdf` | ✅ Done |
| NR-3 | `ty25-1040-nr-mef-ats-scenario-3-12012025.pdf` | ✅ Done |
| NR-4 | `ty25-1040-nr-mef-ats-scenario-4-10212025.pdf` | ✅ Done |
| NR-12 | `ty2025-form-1040-nr-scenario-12.pdf` | ✅ Done |

### Duplicate/Reference Files
- `1040_mef_ats_scenario_7_09152025.pdf` - Earlier version of Scenario 7
- `1040-mef-ats-scenario-8-10212025.pdf` - Alternative naming for Scenario 8
- `1040ss-mef-ats-scenario-6-10202025.pdf` - Alternative naming for Scenario 6

### Notes on 1040-NR Scenarios
Form 1040-NR is for non-resident aliens. These scenarios may require:
- Different standard deduction rules
- Treaty-based exemptions
- ITIN handling instead of SSN
- Special withholding rules

## Contact/Reference

- IRS MeF Program: https://www.irs.gov/e-file-providers/modernized-e-file-mef-program-information
- ATS Documentation: Available through IRS e-Services
- Tax Year 2025 Instructions: https://www.irs.gov/forms-instructions
