import { MEF_REJECTION_ERROR_CODES } from '../constants/rejectionConstants.js';
import { TaxReturn, TaxReturnSubmissionStatus, RejectedStatus } from '../types/core.js';
import {
  getLatestSubmissionStage,
  hasBeenSubmitted,
  isSubmissionStatusStaleForLatestSubmission,
} from './taxReturnUtils.js';

export const areAnyRejectionsNotFixable = (rejectionCodes: RejectedStatus[]) => {
  return rejectionCodes.some((code) => MEF_REJECTION_ERROR_CODES.UNFIXABLE_BY_DF.includes(code.MeFErrorCode));
};

export type SubmissionLifecycleState =
  | `not_submitted`
  | `checking_status`
  | `status_fetch_error`
  | `awaiting_acknowledgement`
  | `resubmission_awaiting_acknowledgement`
  | `awaiting_status`
  | `resubmission_awaiting_status`
  | `status_unavailable`
  | `status_ready`;

export const getSubmissionLifecycleState = ({
  taxReturn,
  submissionStatus,
  isFetching,
  fetchError,
  lastFetchAttempt,
}: {
  taxReturn?: TaxReturn | null;
  submissionStatus?: TaxReturnSubmissionStatus;
  isFetching: boolean;
  fetchError: unknown;
  lastFetchAttempt: Date | null;
}): SubmissionLifecycleState => {
  if (!taxReturn || !hasBeenSubmitted(taxReturn)) {
    return `not_submitted`;
  }

  if (submissionStatus && !isSubmissionStatusStaleForLatestSubmission(taxReturn, submissionStatus)) {
    return `status_ready`;
  }

  if (isFetching || !lastFetchAttempt) {
    return `checking_status`;
  }

  if (fetchError) {
    return `status_fetch_error`;
  }

  switch (getLatestSubmissionStage(taxReturn)) {
    case `submitted_unacknowledged`:
      return `awaiting_acknowledgement`;
    case `resubmitted_unacknowledged`:
      return `resubmission_awaiting_acknowledgement`;
    case `submitted_acknowledged`:
      return `awaiting_status`;
    case `resubmitted_acknowledged`:
      return `resubmission_awaiting_status`;
    default:
      return `status_unavailable`;
  }
};
