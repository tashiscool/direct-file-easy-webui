import { MEF_REJECTION_ERROR_CODES } from '../constants/rejectionConstants.js';
import { TaxReturn, TaxReturnSubmissionStatus, RejectedStatus } from '../types/core.js';
import { hasBeenSubmitted } from './taxReturnUtils.js';

export const areAnyRejectionsNotFixable = (rejectionCodes: RejectedStatus[]) => {
  return rejectionCodes.some((code) => MEF_REJECTION_ERROR_CODES.UNFIXABLE_BY_DF.includes(code.MeFErrorCode));
};

export type SubmissionLifecycleState =
  | `not_submitted`
  | `checking_status`
  | `status_fetch_error`
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

  if (submissionStatus) {
    return `status_ready`;
  }

  if (isFetching || !lastFetchAttempt) {
    return `checking_status`;
  }

  if (fetchError) {
    return `status_fetch_error`;
  }

  return `status_unavailable`;
};
