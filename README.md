# Direct File Easy WebUI

A tax filing platform built on the IRS Direct File open-source codebase, enhanced with AI-powered document analysis and tax optimization features.

**Current Tax Year: 2025**

## Overview

Direct File Easy WebUI combines the official IRS Direct File tax engine with a modern AI-powered interface to help users prepare and file their federal tax returns. The platform supports standard deduction filers with W-2 income, unemployment, interest income, and various credits and deductions.

## Tax Year 2025 Features

### Fully Supported

| Feature | Description |
|---------|-------------|
| **OBBBA Deductions** | New 2025 provisions: overtime exemption, tip exemption, auto loan interest, senior bonus |
| **Standard Deduction** | $15,750 (Single), $31,500 (MFJ), $23,625 (HOH) |
| **Child Tax Credit** | $2,200 per qualifying child |
| **EITC** | Full 2025 thresholds and phase-outs |
| **HSA** | $4,300 (self), $8,550 (family) contribution limits |
| **Education** | Educator expenses, student loan interest deduction |
| **Retirement** | Saver's Credit, 1099-R processing |

### New for 2025: Schedule 1-A (OBBBA)

The One Big Beautiful Bill Act of 2025 introduced new above-the-line deductions:

| Deduction | Cap | Phase-out |
|-----------|-----|-----------|
| Overtime Income Exemption | $12,500 / $25,000 | $150K / $300K |
| Tip Income Exemption | $25,000 | $150K / $300K |
| Auto Loan Interest (US-made) | $10,000 | $100K / $200K |
| Senior Bonus (65+) | $6,000 each | $75K / $150K |

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Direct File Easy WebUI                    │
├─────────────────┬─────────────────────┬────────────────────┤
│   df-client     │    Backend (JVM)    │    AI Service      │
│   (React/TS)    │    (Spring/Scala)   │    (Python)        │
├─────────────────┼─────────────────────┼────────────────────┤
│ • Tax Wizard    │ • Fact Graph Engine │ • Document Analysis│
│ • Flow Engine   │ • Tax Calculations  │ • Tax Optimization │
│ • Localization  │ • MeF XML Export    │ • IRS Data RAG     │
└─────────────────┴─────────────────────┴────────────────────┘
```

### Core Components

- **Fact Graph**: Declarative XML-based tax calculation engine (Scala)
- **df-client**: React/TypeScript tax filing wizard
- **AI Service**: Python-based document analysis and recommendations
- **State API**: Integration for state tax return handoff

## Quick Start

```bash
# Clone repository
git clone https://github.com/yourusername/direct-file-easy-webui.git
cd direct-file-easy-webui

# Install dependencies
cd direct-file/df-client/df-client-app && npm install
cd ../../..
cd ai_service && pip install -r requirements.txt

# Start development servers
# See ONBOARDING.md for detailed instructions
```

## Documentation

| Document | Description |
|----------|-------------|
| [ONBOARDING.md](./ONBOARDING.md) | Getting started guide |
| [PROJECT_PLAN.md](./PROJECT_PLAN.md) | Project plan & 2025 implementation status |
| [docs/engineering/](./docs/engineering/) | Technical documentation |
| [docs/adr/](./docs/adr/) | Architecture Decision Records |

## Project Structure

```
direct-file-easy-webui/
├── ai_service/                 # AI-powered analysis (Python)
├── direct-file/               # IRS Direct File core
│   ├── backend/               # JVM backend with Fact Graph
│   │   └── src/main/resources/tax/  # Tax calculation XMLs
│   ├── df-client/             # React frontend
│   ├── fact-graph-scala/      # Scala calculation engine
│   └── state-api/             # State integration API
├── docs/                      # Documentation
└── *.md                       # Project docs
```

## Key Implementation Files

### Tax Year 2025 Constants
- `direct-file/backend/src/main/resources/tax/constants.xml`
- `direct-file/backend/src/main/resources/tax/standardDeduction.xml`
- `direct-file/backend/src/main/resources/tax/taxCalculations.xml`

### OBBBA 2025 Provisions
- `direct-file/backend/src/main/resources/tax/schedule1A.xml`
- `direct-file/df-client/df-client-app/src/flow/flow-chunks/income/OBBBAIncomeSubcategory.tsx`

### Credits & Deductions
- `direct-file/backend/src/main/resources/tax/eitc.xml`
- `direct-file/backend/src/main/resources/tax/ctcOdc.xml`
- `direct-file/backend/src/main/resources/tax/studentLoanAdjustment.xml`

## Planned for Future Implementation

The following are on the roadmap for future releases:

| Phase | Features |
|-------|----------|
| **Phase 5** | Schedule A (itemized), Schedule B (dividends), Schedule D (capital gains), Education Credits, Clean Vehicle Credit, Adoption Credit |
| **Phase 6** | Schedule C (self-employment), Schedule E (rental), QBI Deduction, Home Energy Credits |
| **Phase 7** | Foreign Tax Credit, K-1 Processing, AMT |

See [PROJECT_PLAN.md](./PROJECT_PLAN.md) for the complete implementation roadmap.

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.

## License

This project incorporates open-source code from the IRS Direct File project.

## References

- [IRS Direct File](https://directfile.irs.gov)
- [IRS Publication 5969](https://www.irs.gov/pub/irs-pdf/p5969.pdf) - Direct File Overview
- [Internal Revenue Code (26 USC)](https://www.irs.gov/privacy-disclosure/tax-code-regulations-and-official-guidance)
- [Modernized e-File (MeF)](https://www.irs.gov/e-file-providers/modernized-e-file-program-information)

## Authorities

Legal foundations for this work include:
- Source Code Harmonization And Reuse in Information Technology Act of 2024 (P.L. 118-187)
- OMB Memorandum M-16-21 (Federal Source Code Policy)
- Federal Acquisition Regulation Part 27
- E-Government Act of 2002 (P.L. 107-347)
