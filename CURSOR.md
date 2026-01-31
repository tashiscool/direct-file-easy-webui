# Direct File Easy WebUI - Quick Index

## Project Overview
Direct File Easy WebUI is a tax filing platform built on the IRS Direct File open-source codebase. It provides AI-powered document analysis and tax optimization for federal tax returns.

**Current Tax Year: 2025**

## Key Components

### 1. Fact Graph Engine (Scala)
- XML-based declarative tax calculations
- Location: `direct-file/backend/src/main/resources/tax/`
- Key files:
  - `constants.xml` - Tax year constants
  - `standardDeduction.xml` - Deduction amounts
  - `taxCalculations.xml` - AGI, brackets
  - `schedule1A.xml` - **OBBBA 2025 deductions**
  - `eitc.xml` - EITC calculations
  - `ctcOdc.xml` - CTC/ODC calculations

### 2. Frontend (React/TypeScript)
- Tax filing wizard flow
- Location: `direct-file/df-client/df-client-app/`
- Key files:
  - `src/flow/flow.tsx` - Main flow config
  - `src/flow/flow-chunks/` - Category subcategories
  - `src/locales/en.yaml` - Translations

### 3. AI Service (Python)
- Document analysis and recommendations
- Location: `ai_service/`
- Key files:
  - `main.py` - FastAPI server
  - `services/` - Business logic
  - `utils/` - IRS data integration

## Tax Year 2025 Status

### Fully Implemented

| Feature | Value | File |
|---------|-------|------|
| Standard Deduction (Single) | $15,750 | `standardDeduction.xml` |
| Standard Deduction (MFJ) | $31,500 | `standardDeduction.xml` |
| Standard Deduction (HOH) | $23,625 | `standardDeduction.xml` |
| Child Tax Credit | $2,200 | `ctcOdc.xml` |
| Additional CTC | $1,700 | `ctcOdc.xml` |
| EITC (0 children) | $649 max, $19,104 limit | `eitc.xml` |
| EITC (1 child) | $4,328 max, $50,434 limit | `eitc.xml` |
| EITC (2 children) | $7,152 max, $57,310 limit | `eitc.xml` |
| EITC (3+ children) | $8,046 max, $61,555 limit | `eitc.xml` |
| HSA (Self) | $4,300 | `hsa.xml` |
| HSA (Family) | $8,550 | `hsa.xml` |

### OBBBA 2025 (Schedule 1-A) with Full Phase-out

| Deduction | Cap | Phase-out Start | Range | Status |
|-----------|-----|-----------------|-------|--------|
| Overtime Exemption | $12,500/$25,000 | $150K/$300K | $50K | ✅ |
| Tip Exemption | $25,000 | $150K/$300K | $50K | ✅ |
| Auto Loan Interest | $10,000 | $100K/$200K | $50K | ✅ |
| Senior Bonus | $6,000/person | $75K/$150K | $25K | ✅ |

**Phase-out Formula:** `deduction × (1 - (MAGI - threshold) / range)`

**Key OBBBA Facts:**
- `/hasQualifiedOvertime` - Boolean
- `/overtimeDeductionAmount` - Final after phase-out
- `/hasQualifiedTips` - Boolean
- `/tipDeductionAmount` - Final after phase-out
- `/hasQualifiedAutoLoanInterest` - Boolean
- `/vehicleIsDomesticManufacture` - Boolean
- `/autoLoanInterestDeductionAmount` - Final after phase-out
- `/hasSeniorBonusEligibility` - Boolean (auto from age)
- `/totalSeniorBonusDeduction` - Final after phase-out
- `/totalSchedule1ADeductions` - Sum of all
- `/obbbaDeductionsIsDone` - Completion check
- `/obbbaPhaseOutApplies` - Any phase-out active

### Planned for Future Phases

| Phase | Features |
|-------|----------|
| **Phase 5** | Schedule A (SALT $40K), Schedule B/D (investments), Form 8863 (education), Form 8936 (clean vehicle), Form 8839 (adoption) |
| **Phase 6** | Schedule C (self-employment), Schedule E (rental), QBI, Form 5695 (energy) |
| **Phase 7** | Form 1116 (foreign tax), K-1, AMT |

## Project Structure

```
direct-file-easy-webui/
├── ai_service/                    # Python AI service
├── direct-file/                   # IRS Direct File core
│   ├── backend/src/main/resources/tax/  # Fact XMLs
│   ├── df-client/df-client-app/   # React frontend
│   └── fact-graph-scala/          # Scala engine
├── docs/                          # Documentation
├── CHANGELOG.md                   # Version history
├── ONBOARDING.md                  # Setup guide
├── PROJECT_PLAN.md                # Plan & status
└── README.md                      # Overview
```

## Common Tasks

### Update Tax Year Values
1. Search `<TaxYear>` in XML files
2. Update dollar amounts
3. Run tests
4. Update docs

### Add New Deduction/Credit
1. Add facts in `backend/.../tax/*.xml`
2. Create flow in `flow-chunks/`
3. Add to `flow.tsx`
4. Add strings in `en.yaml`
5. Update `flow.xml` completion

### Debug Fact Issues
- Check path spelling
- Verify dependencies exist
- Check module references
- Look for circular deps

## Key Documentation

| File | Purpose |
|------|---------|
| `PROJECT_PLAN.md` | 2025 implementation status |
| `ONBOARDING.md` | Developer setup |
| `CHANGELOG.md` | Version history |
| `docs/engineering/Tax-Logic.md` | Fact Graph guide |
| `docs/engineering/writing-facts.md` | XML authoring |

## Development

### Start Servers
```bash
# Frontend
cd direct-file/df-client/df-client-app && npm run dev

# Backend
cd direct-file/backend && ./gradlew bootRun

# AI Service
cd ai_service && python main.py
```

### Run Tests
```bash
# Backend
cd direct-file/backend && ./gradlew test

# Frontend
cd direct-file/df-client/df-client-app && npm test

# Fact Graph
cd direct-file/fact-graph-scala && sbt test
```

## Recent Changes (2025)

### Added
- OBBBA Schedule 1-A deductions
- 2025 standard deduction amounts
- Updated CTC to $2,200
- 2025 EITC thresholds
- OBBBA flow integration

### Updated
- `schedule1A.xml` - Flow control facts
- `flow.xml` - Completion tracking
- `en.yaml` - OBBBA localization
- `flow.tsx` - OBBBA subcategory

## Testing Status

- Fact Graph: 85% coverage
- Frontend: 70% coverage
- OBBBA scenarios: Needs expansion
- Integration: Active

## Performance Targets

- Page load: < 2s
- API response: < 200ms
- Tax calc: < 1s
- Uptime: 99.9%

## Security

- End-to-end encryption
- Secure document storage
- IRS data compliance
- Regular audits

## Support

- See `docs/` for detailed guides
- Check `ONBOARDING.md` for setup
- File issues on GitHub
