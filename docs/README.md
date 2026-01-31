# Documentation

This directory contains comprehensive documentation for the Direct File Easy WebUI project.

## Quick Links

| Document | Description |
|----------|-------------|
| [../PROJECT_PLAN.md](../PROJECT_PLAN.md) | Project plan and Tax Year 2025 implementation status |
| [../ONBOARDING.md](../ONBOARDING.md) | Getting started guide for developers |
| [../CHANGELOG.md](../CHANGELOG.md) | Version history and changes |

## Documentation Structure

```
docs/
├── adr/                    # Architecture Decision Records
├── design/                 # Design documentation and guidelines
├── engineering/            # Technical documentation
├── product/                # Product documentation
├── rfc/                    # Request for Comments documents
└── testing/                # Testing documentation
```

## Tax Year 2025 Implementation

### Fully Implemented

#### OBBBA 2025 (Schedule 1-A) with Phase-out Calculations
| Provision | Cap | Phase-out | Range | Files |
|-----------|-----|-----------|-------|-------|
| Overtime Exemption | $12,500/$25,000 | $150K/$300K | $50K | `schedule1A.xml`, `OBBBAIncomeSubcategory.tsx` |
| Tip Exemption | $25,000 | $150K/$300K | $50K | `schedule1A.xml`, `OBBBAIncomeSubcategory.tsx` |
| Auto Loan Interest | $10,000 | $100K/$200K | $50K | `schedule1A.xml`, `OBBBAIncomeSubcategory.tsx` |
| Senior Bonus | $6,000/person | $75K/$150K | $25K | `schedule1A.xml` (auto-calculated) |

**Phase-out Formula:** `deduction × (1 - (MAGI - threshold) / range)`

#### Core Tax Provisions
| Provision | 2025 Value | File |
|-----------|------------|------|
| Standard Deduction (Single) | $15,750 | `standardDeduction.xml` |
| Standard Deduction (MFJ) | $31,500 | `standardDeduction.xml` |
| Child Tax Credit | $2,200 | `ctcOdc.xml` |
| EITC (3+ children max) | $8,046 | `eitc.xml` |
| HSA (Family) | $8,550 | `hsa.xml` |

### Planned for Future Phases

| Phase | Features | Forms |
|-------|----------|-------|
| **Phase 5** | Itemized deductions, Investment income, Education credits, Clean vehicle, Adoption | Sch A, Sch B, Sch D, 8863, 8936, 8839 |
| **Phase 6** | Self-employment, Rental income, QBI, Home energy | Sch C, Sch E, 5695 |
| **Phase 7** | Foreign tax credit, Partnership/S-Corp, AMT | 1116, K-1, 6251 |

See [PROJECT_PLAN.md](../PROJECT_PLAN.md) for detailed roadmap.

## Key Documentation

### Architecture Decision Records (ADR)
Located in `adr/`, these documents capture important architectural decisions:

- `adr-fact-modules.md` - Fact Dictionary module organization
- `adr-optional-facts.md` - Handling incomplete data
- `adr_encrypting-taxpayer-data.md` - Data security
- `adr-tax-year-2024-development.md` - Tax year development process

### Engineering Documentation
Located in `engineering/`:

- `Tax-Logic.md` - Understanding the Fact Graph
- `writing-facts.md` - How to write fact definitions
- `working-on-client-app.md` - Frontend development guide
- `df-tools/Flamingo-Fact-Checker.md` - Testing tools

### Design Documentation
Located in `design/`:

- `Direct File Design System Wiki.md` - Component library
- `Direct File Content Style Guide.md` - Writing guidelines
- `Direct File Design Guidelines & Processes.md` - Design workflow

### Testing Documentation
Located in `testing/`:

- `fact-graph-library.md` - Fact Graph testing
- `data-import-profiles.md` - Test data profiles

## Fact Dictionary Modules

The tax calculation engine uses XML-based fact dictionaries:

| Module | Location | Purpose |
|--------|----------|---------|
| `constants.xml` | `backend/.../tax/` | Global tax year constants |
| `standardDeduction.xml` | `backend/.../tax/` | Standard deduction rules |
| `taxCalculations.xml` | `backend/.../tax/` | AGI, MAGI, tax brackets |
| `eitc.xml` | `backend/.../tax/` | EITC calculations |
| `ctcOdc.xml` | `backend/.../tax/` | Child Tax Credit |
| `schedule1A.xml` | `backend/.../tax/` | **OBBBA 2025 deductions** |
| `studentLoanAdjustment.xml` | `backend/.../tax/` | Student loan interest |
| `hsa.xml` | `backend/.../tax/` | HSA contributions |
| `flow.xml` | `backend/.../tax/` | Flow control and completion |

## Frontend Flow

The tax filing wizard is organized into categories:

| Category | Route | Subcategories |
|----------|-------|---------------|
| You and Your Family | `/you-and-your-family` | About You, Spouse, Family, Filing Status |
| Income | `/income` | Sources, W-2s, 1099s, OBBBA Deductions |
| Credits & Deductions | `/credits-and-deductions` | Deductions, Credits |
| Your Taxes | `/your-taxes` | Estimated Taxes, Amount, Payment |
| Complete | `/complete` | Review, Sign, Submit |

## Contributing to Documentation

When adding new features:
1. Update `PROJECT_PLAN.md` with implementation status
2. Add entries to `CHANGELOG.md`
3. Update relevant `engineering/` docs
4. Add ADR for significant architectural decisions

## External Resources

- [IRS Direct File](https://directfile.irs.gov)
- [Internal Revenue Code](https://www.irs.gov/privacy-disclosure/tax-code-regulations-and-official-guidance)
- [MeF Program](https://www.irs.gov/e-file-providers/modernized-e-file-program-information)
- [IRS Publications](https://www.irs.gov/forms-instructions)
