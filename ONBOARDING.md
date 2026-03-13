# Direct File Easy WebUI - Onboarding Guide

## Project Overview

This project is a tax filing platform built on top of the IRS Direct File open-source codebase. It provides a user-friendly interface for preparing and filing federal tax returns, with AI-powered assistance for document analysis and tax optimization.

**Current Tax Year:** 2025

## Prerequisites

- Node.js 18+
- Python 3.8+
- Java 17+ (for Scala/JVM backend)
- sbt (Scala Build Tool)
- PostgreSQL 15+
- Redis 7+
- Git
- OpenAI API key (for AI features)

## Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/direct-file-easy-webui.git
cd direct-file-easy-webui
```

### 2. Install Dependencies

#### Frontend (df-client)
```bash
cd direct-file/df-client/df-client-app
npm install
```

#### Backend (Scala Fact Graph)
```bash
cd direct-file/fact-graph-scala
sbt compile
```

#### AI Service
```bash
cd ai_service
pip install -r requirements.txt
```

### 3. Environment Setup

Copy the example environment files and configure:
```bash
cp .env.example .env
```

Required environment variables:
```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/directfile

# AI Service
OPENAI_API_KEY=your_openai_api_key

# Tax Year
TAX_YEAR=2025
```

### 4. Run Development Servers

```bash
# Terminal 1: Frontend
cd direct-file/df-client/df-client-app
npm run dev

# Terminal 2: Backend
cd direct-file/backend
./gradlew bootRun

# Terminal 3: AI Service
cd ai_service
python main.py
```

## Project Structure

```
direct-file-easy-webui/
├── ai_service/                    # Python AI service
│   ├── models/                    # AI/ML models
│   ├── retrieval/                 # RAG retrieval system
│   ├── routes/                    # API endpoints
│   ├── services/                  # Business logic
│   └── utils/                     # Utilities (IRS data integration)
│
├── direct-file/                   # IRS Direct File core
│   ├── backend/                   # Java/Spring backend
│   │   └── src/main/resources/tax/  # Fact Dictionary XMLs
│   │       ├── constants.xml         # Tax year constants
│   │       ├── standardDeduction.xml # Standard deduction rules
│   │       ├── taxCalculations.xml   # Tax bracket calculations
│   │       ├── eitc.xml              # EITC calculations
│   │       ├── ctcOdc.xml            # CTC/ODC calculations
│   │       ├── schedule1A.xml        # OBBBA 2025 deductions
│   │       └── ...                   # Other fact modules
│   │
│   ├── df-client/                 # React frontend
│   │   └── df-client-app/
│   │       ├── src/flow/          # Tax filing wizard flow
│   │       │   ├── flow.tsx       # Main flow configuration
│   │       │   └── flow-chunks/   # Flow subcategories
│   │       └── src/locales/       # Translations (en.yaml)
│   │
│   ├── fact-graph-scala/          # Scala fact graph engine
│   └── state-api/                 # State tax API integration
│
├── docs/                          # Documentation
│   ├── adr/                       # Architecture Decision Records
│   ├── design/                    # Design documentation
│   ├── engineering/               # Engineering docs
│   └── testing/                   # Testing documentation
│
├── PROJECT_PLAN.md               # Project plan & 2025 status
├── ONBOARDING.md                 # This file
└── README.md                     # Project overview
```

## Tax Year 2025 Implementation

### What's Implemented

#### OBBBA 2025 (One Big Beautiful Bill Act)
New above-the-line deductions on Schedule 1-A:
- **Overtime Income Exemption**: $12,500/$25,000 cap
- **Tip Income Exemption**: $25,000 cap
- **Auto Loan Interest Deduction**: $10,000 cap (vehicles meeting the final-assembly-in-the-United-States requirement)
- **Senior Bonus Deduction**: $6,000 per senior (65+)

#### Core Tax Provisions
- Standard Deduction: $15,750 (Single), $31,500 (MFJ), $23,625 (HOH)
- Child Tax Credit: $2,200 per child
- EITC: Full 2025 thresholds implemented
- HSA Limits: $4,300 (self), $8,550 (family)
- All 2025 tax brackets

### Completed Phases
| Phase | Features | Status |
|-------|----------|--------|
| Phase 5 | Schedule A (SALT), Schedule B/D (investments), Education Credits, Clean Vehicle, Adoption | ✅ Complete |
| Phase 6 | Schedule C (self-employment), Schedule E (rental), QBI, Home Energy Credits | ✅ Complete |
| Phase 7 | Foreign Tax Credit, K-1 Processing, AMT | ✅ Complete |

See [PROJECT_PLAN.md](./PROJECT_PLAN.md) for the complete implementation details.

## Key Files for Tax Logic

### Fact Dictionary Modules
Location: `direct-file/backend/src/main/resources/tax/`

#### Core Tax Calculations
| File | Purpose |
|------|---------|
| `constants.xml` | Tax year and universal constants |
| `standardDeduction.xml` | Standard deduction amounts by filing status |
| `taxCalculations.xml` | Tax bracket calculations, AGI, MAGI |
| `eitc.xml` | Earned Income Tax Credit logic |
| `ctcOdc.xml` | Child Tax Credit / Other Dependent Credit |
| `schedule1A.xml` | **OBBBA 2025 additional deductions** |
| `studentLoanAdjustment.xml` | Student loan interest deduction |
| `educatorAdjustment.xml` | Educator expense adjustment |
| `hsa.xml` | Health Savings Account logic |
| `saversCredits.xml` | Retirement savings credit |

#### Phase 5 - Investment & Credits
| File | Purpose |
|------|---------|
| `scheduleA.xml` | Itemized deductions (SALT, mortgage, charitable) |
| `scheduleB.xml` | Interest and dividend income |
| `scheduleD.xml` | Capital gains and losses |
| `educationCredits.xml` | AOTC and Lifetime Learning Credit |
| `cleanVehicleCredit.xml` | New and used EV credits |
| `adoptionCredit.xml` | Qualified adoption expenses |

#### Phase 6 - Business Income
| File | Purpose |
|------|---------|
| `scheduleC.xml` | Self-employment income and expenses |
| `scheduleE.xml` | Rental income and passive activity |
| `qbiDeduction.xml` | Qualified Business Income deduction |
| `homeEnergyCredits.xml` | Residential energy credits |

#### Phase 7 - Advanced Provisions
| File | Purpose |
|------|---------|
| `foreignTaxCredit.xml` | Foreign tax credit (Form 1116) |
| `scheduleK1.xml` | K-1 pass-through income processing |
| `amt.xml` | Alternative Minimum Tax (Form 6251) |

#### Entity Type Support
| File | Purpose |
|------|---------|
| `form1120.xml` | C-Corporation income tax (21% flat rate) |
| `form1120S.xml` | S-Corporation pass-through (built-in gains, LIFO recapture) |
| `form1065.xml` | Partnership income (guaranteed payments, K-1 allocations) |
| `form1041.xml` | Estate/Trust fiduciary income (DNI, compressed brackets) |
| `form990.xml` | Non-profit reporting (UBIT, public support test) |

### Frontend Flow
Location: `direct-file/df-client/df-client-app/src/flow/`

| File | Purpose |
|------|---------|
| `flow.tsx` | Main flow configuration |
| `flow-chunks/income/OBBBAIncomeSubcategory.tsx` | OBBBA deductions UI |
| `flow-chunks/credits-and-deductions/` | Credits and deductions screens |

### Localization
Location: `direct-file/df-client/df-client-app/src/locales/en.yaml`

Contains all user-facing text, help content, and data item labels.

## Understanding the Fact Graph

The Fact Graph is a declarative XML-based system for tax calculations:

```xml
<Fact path="/standardDeductionSingle">
  <Name>Standard deduction for Single filers</Name>
  <TaxYear>2025</TaxYear>
  <Derived>
    <Dollar>15750</Dollar>
  </Derived>
</Fact>
```

Key concepts:
- **Writable Facts**: User-entered data (e.g., income amounts)
- **Derived Facts**: Calculated values based on other facts
- **Dependencies**: Facts can reference other facts via `<Dependency>`
- **Conditions**: Logic using `<All>`, `<Any>`, `<Not>`, `<Switch>`

For more details, see `docs/engineering/Tax-Logic.md`.

## Running Tests

```bash
# Backend tests
cd direct-file/backend
./gradlew test

# Frontend tests
cd direct-file/df-client/df-client-app
npm test

# Fact Graph tests
cd direct-file/fact-graph-scala
sbt test

# AI Service tests
cd ai_service
pytest
```

## Common Tasks

### Adding a New Deduction/Credit

1. Add facts to appropriate XML file in `backend/src/main/resources/tax/`
2. Create flow subcategory in `df-client-app/src/flow/flow-chunks/`
3. Add import and integration in `flow.tsx`
4. Add localization strings in `en.yaml`
5. Update completion conditions in `flow.xml`

### Updating Tax Year Values

1. Search for `<TaxYear>` tags in XML files
2. Update dollar amounts and thresholds
3. Run tests to verify calculations
4. Update documentation

### Testing Tax Scenarios

See `direct-file/backend/src/test/resources/scenarios/` for example test cases.

## Debugging

### Fact Graph Issues
- Check XML syntax and fact path references
- Verify dependency paths exist
- Look for circular dependencies
- Check completion conditions in `flow.xml`

### Frontend Flow Issues
- Verify i18nKey paths match en.yaml
- Check condition/path references match backend facts
- Ensure data items have localization entries

### Common Errors
- "Fact not found": Check path spelling and module reference
- "Incomplete fact": Check writable facts have been set
- "Circular dependency": Review fact dependency chain

## Getting Help

- Check `docs/` directory for detailed documentation
- Review ADRs in `docs/adr/` for design decisions
- See `docs/engineering/` for technical guides
- File issues on GitHub for bugs/features

## Contributing

1. Create a feature branch from `main`
2. Make changes following existing patterns
3. Add tests for new functionality
4. Update documentation as needed
5. Submit PR for review

See [CONTRIBUTING.md](./CONTRIBUTING.md) for detailed guidelines.
