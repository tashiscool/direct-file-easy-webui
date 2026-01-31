# IRS MeF Materials Analysis
**Analysis Date:** January 31, 2026
**Purpose:** Documentation for converting IRS tax forms into machine-readable concepts

---

## 1. Overview of Downloaded Materials

### 1.1 Schema Package (py2026r1.zip)
- **Size:** 10.8MB
- **Internal Structure:** `PY2026R8/mef/rrprd/`
- **Contents:**
  - XML Schema Definitions (XSD) for all supported forms
  - XSLT stylesheets for rendering forms
  - Image assets (GIF/PNG) for form visual elements
  - Common schema components shared across forms

The schema package is the primary source for:
- Field names and their XML element mappings
- Data types and constraints
- Validation rules
- Cardinality (required vs optional, single vs repeating)

### 1.2 Test Scenarios by Tax Year

| Tax Year | Forms Covered | File Count |
|----------|---------------|------------|
| TY2023 | 990, 990EZ, 990PF, 990N, 990T, 4720, 5227, 5330, 8868, 1120POL | 10 |
| TY2024 | 8038CP | 1 |
| TY2025 | 990, 990EZ, 990PF, 990N, 4720, 5227, 5330, 8868, 1120POL, 709 | 10 |
| TY2026 | 8038CP | 1 |

Each test scenario ZIP contains filled PDF forms demonstrating:
- Valid field combinations
- Calculated field relationships
- Attachment requirements
- Edge cases for validation testing

### 1.3 Reference Data Files

| File | Purpose |
|------|---------|
| `tax-year-2025-709709-na-mef-accepted-forms-and-schedules.xlsx` | Form 709/709-NA attachment listing with min/max cardinality |
| `tax-year-2025-1042-mef-forms-attachment-listing.xlsx` | Form 1042 attachment rules |
| `tax-year-2025-accepted-forms-schedules-individual-tax-returns-extensions.xlsx` | 1040 series form acceptance matrix |
| `tax-year-2025-forms-attachments-1040-series-extensions.xlsx` | 1040 extension attachment rules |
| `tax-year-2025-recommended-pdf-names-attached-mef-1040-series-extensions.xlsx` | PDF naming conventions for attachments |

### 1.4 Known Issues Documentation

| File | Coverage |
|------|----------|
| `py2026-1040-series-extensions-ats-known-issues-solutions.xlsx` | 1040 series ATS testing issues |
| `94x-annual-ats-known-issues-ty2024.xls` | 94x series (payroll) testing issues |

---

## 2. Form 709 Deep Analysis (Gift Tax Return)

### 2.1 Form Structure

Form 709 (United States Gift and Generation-Skipping Transfer Tax Return) consists of:

```
Form 709
├── Part I: General Information (Lines 1-21)
├── Part II: Tax Computation (Lines 1-20)
├── Part III: Spouse's Consent on Gifts to Third Parties (Lines 1-7)
├── Schedule A: Computation of Taxable Gifts
│   ├── Part 1: Gifts Subject Only to Gift Tax
│   ├── Part 2: Direct Skips (GST)
│   ├── Part 3: Indirect Skips and Other Transfers in Trust
│   └── Part 4: Taxable Gift Reconciliation
├── Schedule B: Gifts From Prior Periods
├── Schedule C: DSUE Amount and Restored Exclusion
└── Schedule D: Generation-Skipping Transfer Tax
    ├── Part 1: Generation-Skipping Transfers
    ├── Part 2: GST Exemption Reconciliation
    └── Part 3: Tax Computation
```

### 2.2 Key Data Elements Extracted

#### Part I - General Information
| Line | Field Name | Data Type | Notes |
|------|-----------|-----------|-------|
| 1 | Donor First Name | String | |
| 2 | Donor Last Name | String | |
| 3 | Donor SSN | SSN (XXX-XX-XXXX) | Primary identifier |
| 4-5 | Address | String | Street + Apt |
| 6-8 | City/State/ZIP | String | |
| 9-11 | Foreign Address | String | Optional |
| 12 | Legal Residence | String | State of domicile |
| 13 | Citizenship | String | Country |
| 14 | Donor Death Date | Date | Conditional |
| 15 | Amended Return | Boolean | |
| 16 | Extension Filed | Boolean | |
| 17 | Number of Donees | Integer | Count from Schedule A |
| 18a | Previously Filed 709 | Boolean | Triggers Schedule B |
| 18b | Address Changed | Boolean | Conditional on 18a |
| 19 | Gifts by Spouses | Boolean | Triggers Part III |
| 20 | DSUE Applied | Boolean | Triggers Schedule C |
| 21 | Digital Asset Included | Boolean | New for recent years |

#### Part II - Tax Computation
| Line | Field Name | Calculation/Source |
|------|-----------|-------------------|
| 1 | Current Period Taxable Gifts | Schedule A, Part 4, Line 11 |
| 2 | Prior Period Taxable Gifts | Schedule B, Line 3 |
| 3 | Total Taxable Gifts | Line 1 + Line 2 |
| 4 | Tax on Line 3 | Tax table lookup |
| 5 | Tax on Line 2 | Tax table lookup |
| 6 | Balance | Line 4 - Line 5 |
| 7 | Applicable Credit Amount | Schedule C, Line 5 or instructions |
| 8 | Prior Period Credit Used | Schedule B, Line 1, Col (c) |
| 9 | Balance | Line 7 - Line 8 (min 0) |
| 10 | 20% Specific Exemption | Historical gifts 1976-1977 |
| 11 | Balance | Line 9 - Line 10 (min 0) |
| 12 | Applicable Credit | MIN(Line 6, Line 11) |
| 13 | Foreign Gift Tax Credit | Manual entry |
| 14 | Total Credits | Line 12 + Line 13 |
| 15 | Balance | Line 6 - Line 14 (min 0) |
| 16 | GST Taxes | Schedule D, Part 3, Col (g) total |
| 17 | Total Tax | Line 15 + Line 16 |
| 18 | Prepaid Tax | Extension payment |
| 19 | Tax Due | Line 17 - Line 18 (if positive) |
| 20a | Overpayment | Line 18 - Line 17 (if positive) |

#### Schedule A - Gift Details
Each gift entry contains:

| Column | Field | Data Type |
|--------|-------|-----------|
| (a) | Item Number | Integer |
| (b) | Donee Name and Address | String |
| (c) | Relationship to Donor | Enum (Child, Grndchld, Spouse, etc.) |
| (d) | Description of Gift | String |
| (e) | Donor's Adjusted Basis | Currency |
| (f) | Date of Gift | Date |
| (g) | Value at Date of Gift | Currency |
| (h) | Split Gift Amount (1/2 of g) | Currency |
| (i) | Net Transfer (g - h) | Currency |
| (j) | Reserved for Future Use | - |
| (k) | Charitable Gift | Boolean |
| (l) | Deductible Gift to Spouse | Boolean |
| (m) | 2652(a)(3) Election | Boolean |

#### Schedule B - Prior Period Gifts
| Column | Field | Data Type |
|--------|-------|-----------|
| (a) | Calendar Year/Quarter | Year or YYYYQN |
| (b) | IRS Office Where Filed | String |
| (c) | Applicable Credit Used | Currency |
| (d) | Specific Exemption (pre-1977) | Currency |
| (e) | Taxable Gifts Amount | Currency |

#### Schedule C - DSUE and Restored Exclusion
| Line | Field | Notes |
|------|-------|-------|
| Part 1 | Last Deceased Spouse DSUE | Single entry |
| Part 2 | Predeceased Spouses DSUE | Multiple entries possible |
| 1 | Basic Exclusion Amount | Per IRS guidance for year |
| 2 | Total DSUE from Parts 1 & 2 | Sum |
| 3 | Restored Exclusion Amount | Special cases |
| 4 | Total (Lines 1+2+3) | |
| 5 | Applicable Credit | Tax table on Line 4 |

### 2.3 Sample Data from Test Scenario

**Donor:** Kenneth Jones (SSN: 002-00-0006)
**Address:** P.O. BOX 1234, Delanco, NJ 08075
**Domicile:** New Jersey
**Citizenship:** United States

**Gift Summary:**
- 8 gifts to grandchildren (Mills family) - $200,000 each via trust
- 5 gifts to children (Jones family) - Property transfers
- Total value of gifts: $2,359,870
- Annual exclusions applied: $180,000
- Net taxable gifts: $2,179,870

**Prior Period (2013):**
- Taxable gifts: $143,614
- Credit used: $36,880

**Spouse Consent:**
- Consenting Spouse: Adeline Jones (SSN: 004-00-0001)
- Gift splitting enabled (50/50)

**Tax Computation Result:**
- Tax on cumulative gifts: $875,194
- Less tax on prior gifts: $36,884
- Current period tax: $838,310
- Applicable credit: $838,310
- **Tax due: $0**

### 2.4 Applicable Credit Statement (Attachment)

This attachment provides historical gift tax credit reconciliation:

| Column | Description |
|--------|-------------|
| A | Calendar Year or Quarter Code |
| B | Taxable Gifts for Current Period |
| C | Taxable Gifts for Prior Periods |
| D | Cumulative Taxable Gifts |
| E | Tax on Gifts for Prior Periods |
| F | Tax on Cumulative Gifts |
| G | Tax on Gifts for Current Period |
| H | Used DSUE Amount |
| I | Basic Exclusion Amount for Year |
| J | Applicable Exclusion Amount |
| K | Applicable Credit Amount |
| L | Credit Used in Prior Periods |
| M | Available Credit in Current Period |
| N | Credit Allowable |

---

## 3. Form 709 Accepted Attachments

From `tax-year-2025-709709-na-mef-accepted-forms-and-schedules.xlsx`:

| Schema Name | Description | Cardinality |
|-------------|-------------|-------------|
| IRSPayment | IRS Payment Schema | 0/1 |
| ApplicableCreditStatement | Historical credit reconciliation | 0/1 |
| ElectionOutQTIPTreatmentStmt | QTIP election out statement | 0/1 |
| NoticeOfAllocationStatement | GST exemption allocation notice | 0/1 |
| Section2632bElectionOutStatement | GST automatic allocation opt-out | 0/1 |
| Section2632cElectionStatement | GST election statement | 0/1 |
| Section529c2BElectionStatement | 529 plan 5-year election | 0/1 |
| ValuationDiscountStatement | Discount valuation explanation | 0/1 |
| AddressChangeStmt | Address change notification | 0/1 |
| Binary Attachments | PDF/other attachments | 0/unbounded |
| General Dependency Medium | General supporting documents | 0/unbounded |
| IRS712 | Life Insurance Statement | 0/unbounded |

---

## 4. 1040 Series Reference Data

### 4.1 Accepted Forms Matrix

The reference data shows form acceptance by return type:

| Form | 1040 | 1040SS | 1040NR | 56 | 2350 | 4868 | 9465 |
|------|------|--------|--------|-----|------|------|------|
| Form 1040 | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| Schedule 1 | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| Schedule 1A | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| Schedule 2 | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| Schedule 3 | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| Schedule 8812 | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| Schedule A | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| Schedule B | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| Schedule C | 8 | 8 | 8 | 0 | 0 | 0 | 0 |
| Schedule D | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| Schedule E | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| Schedule EIC | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| Schedule F | unbounded | unbounded | unbounded | 0 | 0 | 0 | 0 |
| Schedule H | 2 | 2 | 1 | 0 | 0 | 0 | 0 |
| Schedule J | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| Schedule LEP | 2 | 2 | 1 | 0 | 0 | 0 | 0 |
| Schedule R | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| Schedule SE | 2 | 2 | 1 | 0 | 0 | 0 | 0 |

**Key:** Number indicates max allowed instances. 0 = not accepted. "unbounded" = unlimited.

---

## 5. Exempt Organization Forms (990 Series)

### 5.1 Forms Included in Test Scenarios

| Form | Full Name | Purpose |
|------|-----------|---------|
| 990 | Return of Organization Exempt From Income Tax | Main exempt org return |
| 990-EZ | Short Form Return | Simplified version for smaller orgs |
| 990-PF | Return of Private Foundation | Private foundations |
| 990-N | e-Postcard | Very small organizations |
| 990-T | Exempt Organization Business Income Tax Return | UBIT |
| 4720 | Return of Certain Excise Taxes | Foundation excise taxes |
| 5227 | Split-Interest Trust Information Return | Charitable remainder trusts |
| 5330 | Return of Excise Taxes Related to Employee Benefit Plans | Pension excise taxes |
| 8868 | Application for Extension | Extension requests |
| 1120-POL | U.S. Income Tax Return for Political Organizations | Political orgs |

### 5.2 Test Scenario Contents (TY2025 Form 990)

Each scenario ZIP contains multiple test PDFs:
- `ty2025-990-test 1.pdf` (513KB)
- `ty2025-990-test 2.pdf` (998KB)
- `ty2025-990-test 3.pdf` (284KB)

These represent different filing scenarios with varying:
- Organization sizes
- Activity types
- Schedule requirements
- Attachment combinations

---

## 6. Form 8038-CP (Credit Payments to Issuers of Qualified Bonds)

Present in both TY2024 and TY2026 test scenarios, indicating:
- Active form for tax credit bond programs
- Used by state/local governments
- Involves Build America Bonds, Qualified School Construction Bonds, etc.

---

## 7. Schema Package Structure Analysis

### 7.1 Directory Layout
```
PY2026R8/
└── mef/
    └── rrprd/
        └── common/
            └── images/
                ├── Form display images (GIF/PNG)
                ├── Navigation icons
                └── Branding elements
```

### 7.2 Key Schema Components (Expected)

Based on IRS MeF standards, the schema package should contain:

| Component Type | Purpose |
|----------------|---------|
| `*Type.xsd` | Data type definitions |
| `IRS*.xsd` | Form-specific schemas |
| `efileTypes.xsd` | Common e-file types |
| `ReturnHeader*.xsd` | Return header schemas |
| `*.xsl` | Display stylesheets |

---

## 8. Data Type Patterns

### 8.1 Standard IRS Data Types

| Type | Format | Example |
|------|--------|---------|
| SSN | XXX-XX-XXXX | 002-00-0006 |
| EIN | XX-XXXXXXX | 12-3456789 |
| Phone | (XXX) XXX-XXXX | (609) 555-1234 |
| Date | MM/DD/YYYY or YYYY-MM-DD | 12/31/2025 |
| Currency | Decimal, no symbols | 200000.00 |
| Percentage | Decimal (0.XX) or whole (XX%) | 0.40 or 40% |
| Year | YYYY | 2025 |
| State | 2-letter code | NJ |
| Country | Text or ISO code | United States |
| ZIP | XXXXX or XXXXX-XXXX | 08075 |

### 8.2 Enumerated Values

**Relationship Types (Form 709):**
- Child
- Grndchld (Grandchild)
- Spouse
- Sibling
- Other

**Filing Status (Form 1040):**
- Single
- Married Filing Jointly
- Married Filing Separately
- Head of Household
- Qualifying Widow(er)

---

## 9. Validation Rules Observed

### 9.1 Calculation Validations
- Line 3 = Line 1 + Line 2
- Line 6 = Line 4 - Line 5
- Line 9 = MAX(0, Line 7 - Line 8)
- Line 12 = MIN(Line 6, Line 11)

### 9.2 Conditional Logic
- If Line 18a = "Yes" → Complete Schedule B
- If Line 19 = "Yes" → Complete Part III
- If Line 20 = "Yes" → Complete Schedule C
- If gift splitting → Both donor and spouse sections required

### 9.3 Cardinality Rules
- Most statements: 0 or 1
- Gift entries: unbounded (but practical limits)
- Binary attachments: unbounded

---

## 10. Recommendations for Machine-Readable Conversion

### 10.1 Priority Order

1. **Extract XSD schemas** from py2026r1.zip - These define the authoritative field structure
2. **Map PDF fields to XML elements** using test scenarios as reference
3. **Build calculation dependency graph** from Part II tax computation
4. **Create enumeration tables** for coded values
5. **Document conditional logic** as business rules

### 10.2 Suggested Output Formats

| Format | Use Case |
|--------|----------|
| JSON Schema | API validation, modern applications |
| OpenAPI/Swagger | REST API definitions |
| SQL DDL | Relational database storage |
| Protocol Buffers | High-performance serialization |
| CSV/Flat files | Data exchange, imports |

### 10.3 Key Entities to Model

```
TaxReturn
├── ReturnHeader (filer info, tax year, type)
├── Form (specific form data)
│   ├── Part (logical grouping)
│   │   └── Line (individual field)
│   └── Schedule (sub-form)
├── Attachment (supporting documents)
└── Signature (e-signature data)
```

### 10.4 Relationship Mapping

```
Donor (1) ──────< Gift (many)
Donor (1) ──────< PriorPeriodGift (many)
Donor (1) ─────── Spouse (0..1)
Donor (1) ──────< DSUESource (many)
Gift (1) ──────── Donee (1)
Gift (1) ──────── GSTAllocation (0..1)
```

---

## 11. Next Steps

1. **Unzip and catalog schema package** - Extract py2026r1.zip and inventory all XSD files
2. **Parse XSD to extract field definitions** - Build comprehensive field dictionary
3. **Cross-reference with test scenarios** - Validate understanding with real data
4. **Build form hierarchy model** - Parent/child relationships between forms
5. **Document business rules** - Calculations, conditions, validations
6. **Create transformation mappings** - PDF → XML → Target format

---

## Appendix A: File Inventory

### Test Scenarios
| File | Size | Forms |
|------|------|-------|
| ty2023-form-990-test-scenarios.zip | 2.1MB | 990 |
| ty2023-form-990ez-test-scenarios.zip | 1.1MB | 990-EZ |
| ty2023-form-990pf-test-scenarios.zip | 1.4MB | 990-PF |
| ty2023-form-990n-test-scenarios.zip | 549KB | 990-N |
| ty2023-form-990t-test-scenarios.zip | 2.5MB | 990-T |
| ty2023-form-4720-test-scenarios.zip | 2.0MB | 4720 |
| ty2023-form-5227-test-scenarios.zip | 1.6MB | 5227 |
| ty2023-form-5330-test-scenarios.zip | 2.7MB | 5330 |
| ty2023-form-8868-test-scenarios.zip | 1.1MB | 8868 |
| ty2023-form-1120pol-test-scenarios.zip | 385KB | 1120-POL |
| ty2024-form-8038cp-test-scenarios.zip | 1.3MB | 8038-CP |
| ty2025-form-990-test-scenarios.zip | 1.3MB | 990 |
| ty2025-form-990ez-test-scenarios.zip | 1.4MB | 990-EZ |
| ty2025-form-990pf-test-scenarios.zip | 2.5MB | 990-PF |
| ty2025-form-990n-test-scenarios.zip | 727KB | 990-N |
| ty2025-form-4720-test-scenarios.zip | 1.4MB | 4720 |
| ty2025-form-5227-test-scenarios.zip | 1.7MB | 5227 |
| ty2025-form-5330-test-scenarios.zip | 2.1MB | 5330 |
| ty2025-form-8868-test-scenarios.zip | 991KB | 8868 |
| ty2025-form-1120pol-test-scenarios.zip | 415KB | 1120-POL |
| ty2026-form-8038cp-test-scenarios.zip | 1.1MB | 8038-CP |
| 709-mef-ats-scenario-2.pdf | 824KB | 709 |

### Reference Data
| File | Purpose |
|------|---------|
| tax-year-2025-709709-na-mef-accepted-forms-and-schedules.xlsx | 709 attachments |
| tax-year-2025-1042-mef-forms-attachment-listing.xlsx | 1042 attachments |
| tax-year-2025-accepted-forms-schedules-individual-tax-returns-extensions.xlsx | 1040 acceptance |
| tax-year-2025-forms-attachments-1040-series-extensions.xlsx | 1040 attachments |
| tax-year-2025-recommended-pdf-names-attached-mef-1040-series-extensions.xlsx | PDF naming |

### Known Issues
| File | Coverage |
|------|----------|
| py2026-1040-series-extensions-ats-known-issues-solutions-11122025.xlsx | 1040 ATS issues |
| 94x-annual-ats-known-issues-ty2024.xls | 94x ATS issues |

---

*Document generated from analysis of IRS MeF materials downloaded January 31, 2026*
