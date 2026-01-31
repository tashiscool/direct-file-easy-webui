# Prism - AI-Powered Tax Assistance Platform

## Project Overview
Prism is a private, AI-powered tax assistance platform that helps individuals understand and optimize their taxes. The platform uses advanced AI models to analyze tax documents, provide personalized recommendations, and help users make informed decisions about their tax situation.

## Tax Year 2025 Implementation Status

### Fully Implemented

#### OBBBA 2025 Provisions (One Big Beautiful Bill Act)
The following new provisions from the One Big Beautiful Bill Act of 2025 are fully implemented with complete phase-out calculations:

| Provision | Cap/Limit | Phase-out Start | Phase-out Range | Status |
|-----------|-----------|-----------------|-----------------|--------|
| **Overtime Income Exemption** | $12,500 / $25,000 | $150K / $300K | $50,000 | ✅ Complete |
| **Tip Income Exemption** | $25,000 | $150K / $300K | $50,000 | ✅ Complete |
| **Auto Loan Interest Deduction** | $10,000 | $100K / $200K | $50,000 | ✅ Complete |
| **Senior Bonus Deduction** | $6,000/person | $75K / $150K | $25,000 | ✅ Complete |

**Phase-out Formula:**
```
If MAGI ≤ threshold: Full deduction
If MAGI ≥ threshold + range: No deduction
Otherwise: deduction × (1 - (MAGI - threshold) / range)
```

**Implementation Files:**
- Backend: `direct-file/backend/src/main/resources/tax/schedule1A.xml`
- Frontend Flow: `direct-file/df-client/df-client-app/src/flow/flow-chunks/income/OBBBAIncomeSubcategory.tsx`
- Flow Integration: `direct-file/df-client/df-client-app/src/flow/flow.tsx`
- Localization: `direct-file/df-client/df-client-app/src/locales/en.yaml`

**Key Backend Facts:**
| Fact Path | Type | Description |
|-----------|------|-------------|
| `/hasQualifiedOvertime` | Boolean | User has overtime income |
| `/qualifiedOvertimeIncome` | Dollar | Amount of overtime premium |
| `/overtimeDeductionAmount` | Dollar | Final deduction after phase-out |
| `/hasQualifiedTips` | Boolean | User has tip income |
| `/qualifiedTipIncome` | Dollar | Amount of tips |
| `/tipDeductionAmount` | Dollar | Final deduction after phase-out |
| `/hasQualifiedAutoLoanInterest` | Boolean | User has auto loan |
| `/vehicleIsDomesticManufacture` | Boolean | Vehicle is US-made |
| `/autoLoanInterestDeductionAmount` | Dollar | Final deduction after phase-out |
| `/hasSeniorBonusEligibility` | Boolean | Any filer is 65+ |
| `/totalSeniorBonusDeduction` | Dollar | Senior bonus after phase-out |
| `/totalSchedule1ADeductions` | Dollar | Sum of all OBBBA deductions |

#### Standard Deduction (2025)
| Filing Status | Amount | Status |
|---------------|--------|--------|
| Single | $15,750 | ✅ Complete |
| Married Filing Jointly | $31,500 | ✅ Complete |
| Head of Household | $23,625 | ✅ Complete |
| Married Filing Separately | $15,750 | ✅ Complete |

**Implementation File:** `direct-file/backend/src/main/resources/tax/standardDeduction.xml`

#### Child Tax Credit (CTC) / Other Dependent Credit (ODC)
| Credit | Amount | Phase-out | Status |
|--------|--------|-----------|--------|
| Child Tax Credit (per child) | $2,200 | $200K/$400K | ✅ Complete |
| Additional CTC (refundable) | $1,700 | - | ✅ Complete |
| Other Dependent Credit | $500 | $200K/$400K | ✅ Complete |

**Implementation File:** `direct-file/backend/src/main/resources/tax/ctcOdc.xml`

#### Earned Income Tax Credit (EITC) - 2025
| Children | Max Credit | Income Limit (Single) | Income Limit (MFJ) | Status |
|----------|------------|----------------------|-------------------|--------|
| 0 | $649 | $19,104 | $26,214 | ✅ Complete |
| 1 | $4,328 | $50,434 | $57,554 | ✅ Complete |
| 2 | $7,152 | $57,310 | $64,430 | ✅ Complete |
| 3+ | $8,046 | $61,555 | $68,675 | ✅ Complete |

**Investment Income Limit:** $11,950 ✅

**Implementation File:** `direct-file/backend/src/main/resources/tax/eitc.xml`

#### Health Savings Account (HSA) Limits - 2025
| Coverage Type | Contribution Limit | Status |
|---------------|-------------------|--------|
| Self-only | $4,300 | ✅ Complete |
| Family | $8,550 | ✅ Complete |
| Catch-up (55+) | +$1,000 | ✅ Complete |

**Implementation File:** `direct-file/backend/src/main/resources/tax/hsa.xml`

#### Tax Brackets (2025)
All seven tax brackets (10%, 12%, 22%, 24%, 32%, 35%, 37%) are implemented with 2025 thresholds.

**Implementation File:** `direct-file/backend/src/main/resources/tax/taxCalculations.xml`

#### Other Deductions/Adjustments
| Deduction | Limit | Status |
|-----------|-------|--------|
| Educator Expenses | $300 | ✅ Complete |
| Student Loan Interest | $2,500 | ✅ Complete |
| Saver's Credit | Based on AGI | ✅ Complete |

### Entity Type Support (All Implemented)

The platform supports all major business entity types for comprehensive tax filing:

#### Form 1120 - C Corporations
| Feature | Description | Status |
|---------|-------------|--------|
| **Corporate Income** | Gross receipts, COGS, dividends, interest, rents, royalties, capital gains | ✅ Complete |
| **Corporate Deductions** | Officer compensation, salaries, repairs, taxes, interest, depreciation, charitable | ✅ Complete |
| **Corporate Tax** | 21% flat rate (TCJA), NOL deduction, DRD | ✅ Complete |
| **Credits** | Foreign tax credit, general business credit, R&D credit, WOTC | ✅ Complete |
| **Schedule M-1/M-2** | Book-tax reconciliation, retained earnings | ✅ Complete |

**Implementation File:** `direct-file/backend/src/main/resources/tax/form1120.xml`

#### Form 1120-S - S Corporations
| Feature | Description | Status |
|---------|-------------|--------|
| **Pass-Through Income** | Ordinary business income allocated to shareholders | ✅ Complete |
| **Schedule K** | Interest, dividends, royalties, capital gains, Section 1231, charitable | ✅ Complete |
| **Built-in Gains Tax** | Tax on C-corp conversions (21% rate) | ✅ Complete |
| **Excess Passive Income** | Tax on passive income with accumulated E&P | ✅ Complete |
| **QBI Information** | Section 199A data for shareholder K-1s | ✅ Complete |

**Implementation File:** `direct-file/backend/src/main/resources/tax/form1120S.xml`

#### Form 1065 - Partnerships
| Feature | Description | Status |
|---------|-------------|--------|
| **Partnership Income** | Gross receipts, COGS, other income | ✅ Complete |
| **Guaranteed Payments** | Services and capital payments to partners | ✅ Complete |
| **Schedule K** | All distributive share items (income, deductions, credits) | ✅ Complete |
| **Self-Employment** | SE earnings calculation for general partners | ✅ Complete |
| **Capital Accounts** | Partner capital tracking (M-2) | ✅ Complete |
| **QBI Information** | Section 199A data, W-2 wages, property basis | ✅ Complete |

**Implementation File:** `direct-file/backend/src/main/resources/tax/form1065.xml`

#### Form 1041 - Estates and Trusts
| Feature | Description | Status |
|---------|-------------|--------|
| **Fiduciary Income** | Interest, dividends, business, capital gains, rents, royalties | ✅ Complete |
| **DNI Calculation** | Distributable Net Income for beneficiary allocations | ✅ Complete |
| **Income Distribution Deduction** | Deduction for amounts distributed to beneficiaries | ✅ Complete |
| **Compressed Tax Brackets** | 10%/24%/35%/37% rates at $3,150/$11,450/$15,650 | ✅ Complete |
| **Net Investment Income Tax** | 3.8% NIIT above threshold | ✅ Complete |
| **K-1 Allocations** | Beneficiary share calculations | ✅ Complete |

**Implementation File:** `direct-file/backend/src/main/resources/tax/form1041.xml`

#### Form 990 - Non-Profit Organizations
| Feature | Description | Status |
|---------|-------------|--------|
| **Revenue** | Contributions, program service, investment income, fundraising | ✅ Complete |
| **Functional Expenses** | Grants, compensation, office, occupancy, depreciation | ✅ Complete |
| **Net Assets** | Balance sheet tracking, beginning and end of year | ✅ Complete |
| **Public Support Test** | 33 1/3% public charity test calculation | ✅ Complete |
| **UBIT** | Unrelated Business Income Tax (Form 990-T) | ✅ Complete |
| **Filing Requirements** | Form 990/990-EZ/990-N determination | ✅ Complete |

**Implementation File:** `direct-file/backend/src/main/resources/tax/form990.xml`

### Phase 5 - Investment & Credits (Implemented)

| Form/Schedule | Features | Status |
|---------------|----------|--------|
| **Schedule A** | Itemized Deductions: SALT ($40K cap), Mortgage Interest, Charitable, Medical | ✅ Complete |
| **Schedule B** | Interest & Dividends: Ordinary, Qualified, Foreign, Capital Gain Distributions | ✅ Complete |
| **Schedule D** | Capital Gains/Losses: Short-term, Long-term, $3K loss limit, Carryforward | ✅ Complete |
| **Form 8863** | Education Credits: AOTC ($2,500), LLC ($2,000), Phase-outs | ✅ Complete |
| **Form 8936** | Clean Vehicle Credit: New ($7,500), Used ($4,000), VIN, MSRP limits | ✅ Complete |
| **Form 8839** | Adoption Credit: $17,280 max, $5,000 refundable, Phase-outs | ✅ Complete |

**Implementation Files:**
- `direct-file/backend/src/main/resources/tax/scheduleA.xml`
- `direct-file/backend/src/main/resources/tax/scheduleB.xml`
- `direct-file/backend/src/main/resources/tax/scheduleD.xml`
- `direct-file/backend/src/main/resources/tax/educationCredits.xml`
- `direct-file/backend/src/main/resources/tax/cleanVehicleCredit.xml`
- `direct-file/backend/src/main/resources/tax/adoptionCredit.xml`

### Phase 6 - Business Income (Implemented)

| Form/Schedule | Features | Status |
|---------------|----------|--------|
| **Schedule C** | Self-Employment: Income, 20+ expense categories, Home office, SE tax | ✅ Complete |
| **Schedule E** | Rental Income: Rental/Royalty, Expenses, Passive loss limits ($25K) | ✅ Complete |
| **Form 8995** | QBI Deduction: 20% deduction, SSTB rules, W-2/Capital limits, REIT/PTP | ✅ Complete |
| **Form 5695** | Home Energy Credits: Residential clean energy (30%), Home improvement | ✅ Complete |

**Implementation Files:**
- `direct-file/backend/src/main/resources/tax/scheduleC.xml`
- `direct-file/backend/src/main/resources/tax/scheduleE.xml`
- `direct-file/backend/src/main/resources/tax/qbiDeduction.xml`
- `direct-file/backend/src/main/resources/tax/homeEnergyCredits.xml`

### Phase 7 - Advanced Tax Provisions (Implemented)

| Form/Schedule | Features | Status |
|---------------|----------|--------|
| **Form 1116** | Foreign Tax Credit: FTC limitation, Carryforward, Passive/General categories | ✅ Complete |
| **Schedule K-1** | Pass-Through Income: Partnership, S-Corp, Estate/Trust, QBI info | ✅ Complete |
| **Form 6251** | Alternative Minimum Tax: AMTI, Exemptions, 26%/28% rates, AMT credit | ✅ Complete |

**Implementation Files:**
- `direct-file/backend/src/main/resources/tax/foreignTaxCredit.xml`
- `direct-file/backend/src/main/resources/tax/scheduleK1.xml`
- `direct-file/backend/src/main/resources/tax/amt.xml`

### Future Tax Year Considerations (2026+)

The following changes will need implementation for TY 2026:
- Child and Dependent Care Credit rate increase (35% → 50%)
- QBI deduction changes ($400 minimum)
- Updated W-2/1099 reporting for tips and overtime
- New form field mappings

### Implementation Roadmap

```
Phase 5 (COMPLETE ✅):
├── Schedule A - Itemized Deductions ✅
│   ├── SALT Deduction ($40,000 cap) ✅
│   ├── Mortgage Interest ✅
│   ├── Charitable Contributions ✅
│   └── Medical Expenses ✅
├── Schedule B - Interest/Dividends ✅
│   ├── Ordinary Dividends ✅
│   └── Qualified Dividends ✅
├── Schedule D - Capital Gains ✅
│   ├── Short-term gains/losses ✅
│   └── Long-term gains/losses ✅
├── Form 8863 - Education Credits ✅
│   ├── American Opportunity Credit ✅
│   └── Lifetime Learning Credit ✅
├── Form 8936 - Clean Vehicle Credit ✅
└── Form 8839 - Adoption Credit ✅

Phase 6 (COMPLETE ✅):
├── Schedule C - Self-Employment ✅
│   ├── Business Income ✅
│   ├── Business Expenses (20+ categories) ✅
│   ├── Home Office Deduction ✅
│   └── Self-Employment Tax ✅
├── Schedule E - Rental Income ✅
│   ├── Rental Expenses ✅
│   └── Passive Loss Limits ✅
├── Form 8995 - QBI Deduction ✅
│   ├── 20% Deduction ✅
│   ├── SSTB Rules ✅
│   └── W-2/Capital Limits ✅
└── Form 5695 - Home Energy Credits ✅
    ├── Residential Clean Energy (30%) ✅
    └── Energy Efficient Home Improvement ✅

Phase 7 (COMPLETE ✅):
├── Form 1116 - Foreign Tax Credit ✅
│   ├── FTC Limitation ✅
│   └── Carryforward ✅
├── Schedule K-1 - Partnership/S-Corp/Estate/Trust ✅
│   ├── Ordinary Income ✅
│   ├── Portfolio Income ✅
│   ├── Capital Gains ✅
│   └── QBI Information ✅
└── Form 6251 - AMT ✅
    ├── AMTI Calculation ✅
    ├── Exemption Phase-out ✅
    └── AMT Credit ✅
```

---

## Core Features
1. **Document Analysis**
   - Upload and analyze tax documents
   - Extract key information automatically
   - Identify potential issues and opportunities
   - IRS tax code integration
   - Publication-based validation

2. **AI-Powered Insights**
   - Personalized tax recommendations
   - Risk assessment and audit probability
   - Tax optimization suggestions
   - IRS publication analysis
   - Tax code compliance checking

3. **User Dashboard**
   - Document management
   - Analysis history
   - Progress tracking
   - Subscription management
   - Tax code reference

4. **Security & Privacy**
   - End-to-end encryption
   - Secure document storage
   - Privacy-focused design
   - Regular security audits
   - IRS data compliance

## Technical Architecture

### Frontend
- React with TypeScript
- Tailwind CSS for styling
- Redux for state management
- React Query for API integration
- Tax code viewer component

### Backend
- Node.js with Express
- PostgreSQL database
- Redis for caching
- JWT authentication
- IRS data integration

### Direct File Core (Fact Graph)
- Scala-based tax calculation engine
- XML-based fact dictionary modules
- JVM backend + Scala.js frontend transpilation
- Declarative tax logic reasoning
- MeF (Modernized e-File) XML generation

### AI Service
- Python-based AI processing
- GPT-4 for document analysis
- Custom ML models for risk assessment
- Real-time processing pipeline
- IRS tax code processing
- Publication analysis

## Implementation Phases

### Phase 1: Foundation (Weeks 1-4)
- [x] Project setup and architecture
- [x] Basic frontend structure
- [x] Backend API framework
- [x] Database schema design
- [x] Authentication system
- [x] IRS data integration

### Phase 2: Core Features (Weeks 5-8)
- [x] Document upload system
- [x] Basic AI analysis integration
- [x] User dashboard
- [x] Document management
- [x] Basic reporting
- [x] Tax code processing
- [x] **Tax Year 2025 fact graph updates**

### Phase 3: AI Enhancement (Weeks 9-12)
- [x] Advanced document analysis
- [x] Risk assessment system
- [x] Recommendation engine
- [x] Performance optimization
- [x] Security hardening
- [x] Publication analysis
- [x] **OBBBA 2025 provisions implementation**

### Phase 4: Polish & Launch (Weeks 13-16)
- [ ] UI/UX refinement
- [ ] Performance testing
- [ ] Security audit
- [ ] Beta testing
- [ ] Production deployment
- [ ] IRS compliance verification

## Technology Stack

### Frontend
- React 18
- TypeScript 5
- Tailwind CSS 3
- Redux Toolkit
- React Query
- Vite

### Backend
- Node.js 18
- Express 4
- PostgreSQL 15
- Redis 7
- TypeORM
- JWT

### Fact Graph Engine
- Scala 2.13
- Scala.js
- XML-based fact dictionaries
- JVM runtime

### AI Service
- Python 3.8+
- GPT-4 API
- scikit-learn
- pandas
- numpy
- FastAPI
- PyPDF2
- BeautifulSoup4

### Infrastructure
- AWS (EC2, S3, RDS)
- Docker
- GitHub Actions
- Cloudflare

## Security Measures
1. **Data Protection**
   - End-to-end encryption
   - Secure document storage
   - Regular backups
   - Access controls
   - IRS data security

2. **Authentication**
   - Multi-factor authentication
   - Session management
   - Rate limiting
   - IP tracking
   - IRS compliance

3. **Compliance**
   - GDPR compliance
   - Data retention policies
   - Privacy policy
   - Terms of service
   - IRS regulations

## Performance Targets
- Page load time < 2s
- API response time < 200ms
- 99.9% uptime
- Support for 10,000+ concurrent users
- Tax code processing < 1s

## Monitoring & Analytics
- Real-time performance monitoring
- User behavior analytics
- Error tracking
- Usage statistics
- IRS data updates

## Revenue Model
1. **Annual Plans**
   - Basic: $49.99/year
     - Up to 20 documents
     - Basic analysis and recommendations
     - Email support
     - Standard processing time

   - Professional: $149.99/year
     - Up to 50 documents
     - Advanced analysis and risk assessment
     - Priority support
     - Faster processing time
     - Custom recommendations

   - Enterprise: Custom pricing
     - Unlimited documents
     - All Professional features
     - Dedicated support
     - API access
     - Custom solutions
     - Team management

2. **Additional Services**
   - Document Review: $29.99 per document
   - Priority Processing: $19.99 per document
   - Expert Consultation: $99.99 per hour
   - Custom Reports: $49.99 per report

3. **Seasonal Pricing**
   - Early Bird (Jan 1 - Feb 15): 20% discount
   - Regular Season (Feb 16 - Apr 15): Standard pricing
   - Late Season (Apr 16 - Oct 15): 10% surcharge
   - Off-Season (Oct 16 - Dec 31): 30% discount

4. **Features by Tier**
   - Basic: Document analysis, basic recommendations
   - Professional: Advanced analysis, risk assessment, priority support
   - Enterprise: Custom solutions, dedicated support, API access

## Success Metrics
1. **User Engagement**
   - Monthly active users
   - Document upload volume
   - Feature usage statistics
   - User retention rate
   - Tax code reference usage

2. **Business Metrics**
   - Revenue growth
   - Customer acquisition cost
   - Lifetime value
   - Churn rate
   - Service utilization

3. **Technical Metrics**
   - System uptime
   - Response times
   - Error rates
   - Resource utilization
   - IRS data accuracy

## Next Steps
1. Complete UI/UX refinement
2. Conduct performance testing
3. Complete security audit
4. Begin beta testing program
5. Prepare production deployment
6. Verify IRS compliance for 2025

## Timeline
- Phase 1: Completed
- Phase 2: Completed
- Phase 3: Completed
- Phase 4: In Progress
- Launch: Week 16
