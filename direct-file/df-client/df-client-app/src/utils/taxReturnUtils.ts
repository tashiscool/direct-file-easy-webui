import { TaxReturn, TaxReturnSubmission, TaxReturnSubmissionStatus } from '../types/core.js';
import { CURRENT_TAX_YEAR } from '../constants/taxConstants.js';

export const anyHasStarted = (taxReturns: TaxReturn[]) => {
  return taxReturns.some((tr: TaxReturn) => {
    return tr.id;
  });
};

export const hasBeenSubmitted = (taxReturn: TaxReturn) => taxReturn.taxReturnSubmissions.length > 0;

export const anyHasBeenSubmitted = (taxReturns: TaxReturn[]) => {
  return taxReturns.some((tr: TaxReturn) => {
    return hasBeenSubmitted(tr);
  });
};

export const getLatestSubmission = (taxReturn: TaxReturn) => {
  return taxReturn.taxReturnSubmissions
    .slice()
    .sort((s1, s2) => new Date(s2.createdAt).getTime() - new Date(s1.createdAt).getTime())
    .at(0);
};

export const hasSubmissionAcknowledgement = (submission?: TaxReturnSubmission | null): boolean =>
  Boolean(submission?.receiptId && submission?.submissionReceivedAt);

export type LatestSubmissionStage =
  | `not_submitted`
  | `submitted_unacknowledged`
  | `submitted_acknowledged`
  | `resubmitted_unacknowledged`
  | `resubmitted_acknowledged`;

export const getLatestSubmissionStage = (taxReturn?: TaxReturn | null): LatestSubmissionStage => {
  if (!taxReturn || !hasBeenSubmitted(taxReturn)) {
    return `not_submitted`;
  }

  const latestSubmission = getLatestSubmission(taxReturn);
  if (!latestSubmission) {
    return `not_submitted`;
  }

  const isResubmission = taxReturn.taxReturnSubmissions.length > 1;
  const acknowledged = hasSubmissionAcknowledgement(latestSubmission);

  if (isResubmission) {
    return acknowledged ? `resubmitted_acknowledged` : `resubmitted_unacknowledged`;
  }

  return acknowledged ? `submitted_acknowledged` : `submitted_unacknowledged`;
};

export const isSubmissionStatusStaleForLatestSubmission = (
  taxReturn?: TaxReturn | null,
  submissionStatus?: TaxReturnSubmissionStatus
): boolean => {
  if (!taxReturn || !submissionStatus) {
    return false;
  }

  const latestSubmission = getLatestSubmission(taxReturn);
  if (!latestSubmission) {
    return false;
  }

  return new Date(submissionStatus.createdAt).getTime() < new Date(latestSubmission.createdAt).getTime();
};

export const getTaxReturnById = (taxReturns: TaxReturn[], taxId: string | null) =>
  taxId ? taxReturns.find((tr) => tr.id === taxId) : undefined;

export const getCurrentTaxYearReturn = (taxReturns: TaxReturn[]) =>
  taxReturns.find((tr) => tr.taxYear.toString() === CURRENT_TAX_YEAR);
