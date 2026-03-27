import { StateCapability } from '../types/StateCapability.js';
import { StateProfile } from '../types/StateProfile.js';

function inferLane(profile: StateProfile): StateCapability['lane'] {
  if (profile.lane) return profile.lane;
  if (profile.defaultRedirectUrl) return `transfer_export`;
  return `expert_route`;
}

function inferSubmissionMode(
  lane: StateCapability['lane'],
  profile: StateProfile
): StateCapability['submissionMode'] {
  if (profile.submissionMode) return profile.submissionMode;
  if (lane === `expert_route`) return `expert_review`;
  if (profile.acceptedOnly) return `handoff`;
  return `self_service`;
}

export const normalizeStateCapability = (
  profile: StateProfile,
  taxYear: number
): StateCapability => {
  const lane = inferLane(profile);
  return {
    stateCode: profile.stateCode,
    taxYear,
    lane,
    submissionMode: inferSubmissionMode(lane, profile),
    supportedForms: profile.supportedForms ?? [`1040`],
    statusSupport: profile.statusSupport ?? [
      `pending`,
      `accepted`,
      `rejected`,
    ],
    taxSystemName: profile.taxSystemName,
    acceptedOnly: profile.acceptedOnly,
    urls: {
      landingUrl: profile.landingUrl,
      defaultRedirectUrl: profile.defaultRedirectUrl,
      departmentOfRevenueUrl: profile.departmentOfRevenueUrl,
      filingRequirementsUrl: profile.filingRequirementsUrl,
      transferCancelUrl: profile.transferCancelUrl,
      waitingForAcceptanceCancelUrl: profile.waitingForAcceptanceCancelUrl,
      redirectUrls: profile.redirectUrls,
      expertHandoffUrl: profile.expertHandoffUrl ?? null,
    },
  };
};
