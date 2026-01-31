# Changelog

All notable changes to the Direct File Easy WebUI project.

## [Unreleased]

### Tax Year 2025 Implementation

#### Added - OBBBA 2025 Provisions (One Big Beautiful Bill Act)

**Schedule 1-A Additional Deductions with Full Phase-out Calculations:**

1. **Overtime Income Exemption**
   - Cap: $12,500 (Single/HOH/MFS), $25,000 (MFJ)
   - Phase-out starts: $150,000 (Single), $300,000 (MFJ)
   - Phase-out range: $50,000
   - Backend facts:
     - `/hasQualifiedOvertime` - Boolean writable
     - `/qualifiedOvertimeIncome` - Dollar writable
     - `/overtimeDeductionBeforePhaseout` - Calculated before phase-out
     - `/overtimeDeductionPhaseoutMultiplier` - Phase-out percentage (0-1)
     - `/overtimeDeductionAmount` - Final deduction after phase-out
   - Frontend: `OBBBAIncomeSubcategory.tsx`

2. **Tip Income Exemption**
   - Cap: $25,000 all filing statuses
   - Phase-out starts: $150,000 (Single), $300,000 (MFJ)
   - Phase-out range: $50,000
   - Backend facts:
     - `/hasQualifiedTips` - Boolean writable
     - `/qualifiedTipIncome` - Dollar writable
     - `/tipDeductionBeforePhaseout` - Calculated before phase-out
     - `/tipDeductionPhaseoutMultiplier` - Phase-out percentage (0-1)
     - `/tipDeductionAmount` - Final deduction after phase-out
   - Frontend: `OBBBAIncomeSubcategory.tsx`

3. **Auto Loan Interest Deduction**
   - Cap: $10,000 (US-manufactured vehicles only)
   - Phase-out starts: $100,000 (Single), $200,000 (MFJ)
   - Phase-out range: $50,000
   - Requires vehicle domestic manufacture verification
   - Backend facts:
     - `/hasQualifiedAutoLoanInterest` - Boolean writable
     - `/vehicleIsDomesticManufacture` - Boolean writable
     - `/vehicleMake`, `/vehicleModel`, `/vehicleYear` - String writables
     - `/qualifiedAutoLoanInterest` - Dollar writable
     - `/autoLoanInterestBeforePhaseout` - Calculated before phase-out
     - `/autoLoanInterestPhaseoutMultiplier` - Phase-out percentage (0-1)
     - `/autoLoanInterestDeductionAmount` - Final deduction after phase-out
   - Frontend: `OBBBAIncomeSubcategory.tsx`

4. **Senior Bonus Deduction (Automatic)**
   - Amount: $6,000 per qualifying senior (age 65+)
   - Phase-out starts: $75,000 (Single), $150,000 (MFJ)
   - Phase-out range: $25,000
   - Automatically calculated based on filer age
   - Backend facts:
     - `/primaryFilerIsSenior` - Derived from filer age
     - `/secondaryFilerIsSenior` - Derived from spouse age (MFJ only)
     - `/eligibleSeniorsCount` - Count of eligible seniors (0-2)
     - `/hasSeniorBonusEligibility` - Whether any senior qualifies
     - `/seniorBonusBeforePhaseout` - Calculated before phase-out
     - `/seniorBonusPhaseoutMultiplier` - Phase-out percentage (0-1)
     - `/totalSeniorBonusDeduction` - Final deduction after phase-out
   - Frontend: Displayed in OBBBA summary

**Flow Control Facts:**
- `/obbbaDeductionsIsDone` - Completion condition for flow
- `/obbbaPhaseOutApplies` - Whether any phase-out reduces deductions
- `/noObbbaDeductions` - Whether user has no OBBBA deductions
- `/hasSchedule1ADeductions` - Whether Schedule 1-A has any amounts
- `/pdfIncludeSchedule1A` - Whether to include Schedule 1-A in PDF

**Total Schedule 1-A:**
- `/totalSchedule1ADeductions` - Sum of all OBBBA deductions (exported to MeF)

#### Updated - 2025 Tax Constants

**Standard Deduction:**
| Filing Status | 2024 | 2025 |
|---------------|------|------|
| Single | $14,600 | $15,750 |
| MFJ | $29,200 | $31,500 |
| HOH | $21,900 | $23,625 |
| MFS | $14,600 | $15,750 |

**Child Tax Credit:**
| Credit | 2024 | 2025 |
|--------|------|------|
| CTC per child | $2,000 | $2,200 |
| ACTC (refundable) | $1,600 | $1,700 |
| ODC | $500 | $500 |

**EITC Income Limits (Single):**
| Children | 2024 | 2025 |
|----------|------|------|
| 0 | $18,591 | $19,104 |
| 1 | $49,084 | $50,434 |
| 2 | $55,768 | $57,310 |
| 3+ | $59,899 | $61,555 |

**EITC Investment Income Limit:**
- 2024: $11,600
- 2025: $11,950

**HSA Contribution Limits:**
| Coverage | 2024 | 2025 |
|----------|------|------|
| Self-only | $4,150 | $4,300 |
| Family | $8,300 | $8,550 |

**Student Loan Interest Deduction:**
- Max deduction: $2,500 (unchanged)
- Phase-out start: $85,000 (Single), $170,000 (MFJ)
- Phase-out complete: $100,000 (Single), $200,000 (MFJ)

#### Changed - Backend (schedule1A.xml)

- Added proper phase-out calculations for all OBBBA deductions
- Fixed eligibleSeniorsCount to use proper integer logic instead of Count
- Added senior bonus eligibility and phase-out facts
- Added intermediate facts for before/after phase-out tracking
- Added noObbbaDeductions fact for frontend display

#### Changed - Flow Integration

- Added `OBBBAIncomeSubcategory` import to `flow.tsx`
- Integrated OBBBA subcategory into income category flow
- Added OBBBA completion tracking to `/flowIncomplete` in `flow.xml`
- Updated deduction calculations to use boolean flow control facts
- Added senior bonus to data items display

#### Changed - Localization (en.yaml)

- Added OBBBA section headings and descriptions
- Added data item labels for all OBBBA deductions:
  - `obbbaOvertimeDeduction`
  - `obbbaTipDeduction`
  - `obbbaAutoLoanDeduction`
  - `obbbaSeniorBonusDeduction`
- Added modal content for OBBBA learn more links
- Added help text for overtime calculation methods
- Added summary display for senior bonus
- Added no-deductions message for users without OBBBA benefits
- Updated summary to show final deduction amounts (after phase-out)

### Technical Details

**Phase-out Calculation Formula:**
```
phaseoutMultiplier = 1.0 - ((MAGI - threshold) / phaseoutRange)
finalDeduction = deductionBeforePhaseout * phaseoutMultiplier
```

Where:
- If MAGI ≤ threshold: multiplier = 1.0 (no reduction)
- If MAGI ≥ threshold + range: multiplier = 0.0 (fully phased out)
- Otherwise: linear reduction

**Phase-out Ranges:**
| Deduction | Range |
|-----------|-------|
| Overtime | $50,000 |
| Tips | $50,000 |
| Auto Loan Interest | $50,000 |
| Senior Bonus | $25,000 |

### Planned for Future Implementation

The following 2025 provisions are scheduled for future phases:

| Provision | Phase | Dependencies |
|-----------|-------|--------------|
| SALT Deduction ($40,000 cap) | Phase 5 | Schedule A implementation |
| Adoption Tax Credit | Phase 5 | Form 8839 |
| Clean Vehicle Credit | Phase 5 | Form 8936, VIN verification |
| Education Credits (AOTC/LLC) | Phase 5 | Form 8863 |
| Capital Gains/Dividends | Phase 5 | Schedule B, Schedule D |
| QBI Deduction | Phase 6 | Schedule C, self-employment |
| Home Energy Credits | Phase 6 | Form 5695 |
| Rental Income | Phase 6 | Schedule E |
| Foreign Tax Credit | Phase 7 | Form 1116 |

### Files Modified

**Backend:**
- `direct-file/backend/src/main/resources/tax/schedule1A.xml` - Complete OBBBA implementation
- `direct-file/backend/src/main/resources/tax/flow.xml` - Completion tracking
- `direct-file/backend/src/main/resources/tax/taxCalculations.xml` - AGI integration

**Frontend:**
- `direct-file/df-client/df-client-app/src/flow/flow.tsx` - Flow integration
- `direct-file/df-client/df-client-app/src/flow/flow-chunks/income/OBBBAIncomeSubcategory.tsx` - UI flow
- `direct-file/df-client/df-client-app/src/locales/en.yaml` - Localization

**Documentation:**
- `PROJECT_PLAN.md` - Updated implementation status
- `ONBOARDING.md` - Developer guide
- `README.md` - Project overview
- `CURSOR.md` - Quick reference
- `docs/README.md` - Documentation index
- `CHANGELOG.md` - This file

---

## [1.0.0] - 2024-XX-XX

### Added
- Initial release based on IRS Direct File open-source code
- AI-powered document analysis service
- Tax Year 2024 support
- Basic credits and deductions support

### Technical
- Fact Graph XML-based calculation engine
- React/TypeScript frontend
- Scala.js client-side calculations
- Spring Boot backend
