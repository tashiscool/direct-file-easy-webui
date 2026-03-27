import { normalizeStateCapability } from './stateCapabilityUtils.js';
import { StateProfile } from '../types/StateProfile.js';

describe(`stateCapabilityUtils`, () => {
  it(`derives a truthful transfer-export capability from a redirect-backed state profile`, () => {
    const profile: StateProfile = {
      stateCode: `MA`,
      landingUrl: `https://www.mass.gov/`,
      defaultRedirectUrl: `https://www.mtc.dor.state.ma.us/`,
      departmentOfRevenueUrl: `https://www.mass.gov/orgs/department-of-revenue`,
      filingRequirementsUrl: `https://www.mass.gov/info-details/massachusetts-personal-income-tax-forms-and-instructions`,
      transferCancelUrl: `https://www.mass.gov/`,
      waitingForAcceptanceCancelUrl: `https://www.mass.gov/`,
      redirectUrls: [],
      languages: {},
      taxSystemName: `MassTaxConnect`,
      acceptedOnly: true,
      customFilingDeadline: null,
    };

    expect(normalizeStateCapability(profile, 2025)).toEqual(
      expect.objectContaining({
        stateCode: `MA`,
        taxYear: 2025,
        lane: `transfer_export`,
        submissionMode: `handoff`,
        acceptedOnly: true,
        supportedForms: [`1040`],
      })
    );
  });

  it(`preserves an explicit expert-route profile`, () => {
    const profile: StateProfile = {
      stateCode: `CA`,
      landingUrl: `https://www.ftb.ca.gov/`,
      defaultRedirectUrl: null,
      departmentOfRevenueUrl: `https://www.ftb.ca.gov/`,
      filingRequirementsUrl: `https://www.ftb.ca.gov/file/personal/do-you-need-to-file.html`,
      transferCancelUrl: null,
      waitingForAcceptanceCancelUrl: null,
      redirectUrls: [],
      languages: {},
      taxSystemName: `California Franchise Tax Board`,
      acceptedOnly: false,
      lane: `expert_route`,
      submissionMode: `expert_review`,
      statusSupport: [`draft`, `expert_handoff`],
      supportedForms: [`540`],
      expertHandoffUrl: `https://example.com/expert-handoff`,
      customFilingDeadline: null,
    };

    expect(normalizeStateCapability(profile, 2025)).toEqual(
      expect.objectContaining({
        lane: `expert_route`,
        submissionMode: `expert_review`,
        supportedForms: [`540`],
        statusSupport: [`draft`, `expert_handoff`],
        urls: expect.objectContaining({
          expertHandoffUrl: `https://example.com/expert-handoff`,
        }),
      })
    );
  });
});
