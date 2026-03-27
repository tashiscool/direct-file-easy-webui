import { StateOrProvince } from './StateOrProvince.js';
import {
  StateCapabilityLane,
  StateCapabilitySubmissionMode,
} from './StateProfile.js';

export type StateCapability = {
  stateCode: StateOrProvince;
  taxYear: number;
  lane: StateCapabilityLane;
  submissionMode: StateCapabilitySubmissionMode;
  supportedForms: string[];
  statusSupport: string[];
  taxSystemName: string;
  acceptedOnly: boolean;
  urls: {
    landingUrl: string;
    defaultRedirectUrl: string | null;
    departmentOfRevenueUrl: string | null;
    filingRequirementsUrl: string | null;
    transferCancelUrl: string | null;
    waitingForAcceptanceCancelUrl: string | null;
    redirectUrls: string[];
    expertHandoffUrl: string | null;
  };
};
