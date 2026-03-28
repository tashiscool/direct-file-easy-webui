import { areAnyRejectionsNotFixable, getSubmissionLifecycleState } from './submissionStatusUtils.js';
import { RejectedStatus, TaxReturn, TaxReturnSubmissionStatus } from '../types/core.js';
import { MEF_REJECTION_ERROR_CODES } from '../constants/rejectionConstants.js';
import { CURRENT_TAX_YEAR, FEDERAL_RETURN_STATUS } from '../constants/taxConstants.js';

describe(`submissionStatusUtils`, () => {
  const submittedTaxReturn: TaxReturn = {
    id: `tax-return-1`,
    createdAt: new Date().toISOString(),
    taxYear: parseInt(CURRENT_TAX_YEAR),
    facts: {},
    taxReturnSubmissions: [
      {
        id: `submission-1`,
        receiptId: `receipt-1`,
        submitUserId: `user-1`,
        createdAt: new Date().toISOString(),
        submissionReceivedAt: new Date().toISOString(),
      },
    ],
    isEditable: true,
    surveyOptIn: null,
  };
  const acceptedStatus: TaxReturnSubmissionStatus = {
    status: FEDERAL_RETURN_STATUS.ACCEPTED,
    rejectionCodes: [],
    createdAt: new Date().toISOString(),
  };

  describe(areAnyRejectionsNotFixable.name, () => {
    it(`returns true if even one rejection code is not fixable`, () => {
      const rejectionCodes: RejectedStatus[] = [
        {
          MeFErrorCode: `IND-181-01`,
          MeFDescription: `not used`,
          TranslationKey: `not used`,
        },
        {
          MeFErrorCode: MEF_REJECTION_ERROR_CODES.UNFIXABLE_BY_DF[0],
          MeFDescription: `not used`,
          TranslationKey: `not used`,
        },
      ];

      expect(areAnyRejectionsNotFixable(rejectionCodes)).toBeTruthy();
    });

    it(`returns false if all of the rejection codes are fixable`, () => {
      const rejectionCodes: RejectedStatus[] = [
        {
          MeFErrorCode: `IND-181-01`,
          MeFDescription: `not used`,
          TranslationKey: `not used`,
        },
        {
          MeFErrorCode: `Some fixable error code`,
          MeFDescription: `not used`,
          TranslationKey: `not used`,
        },
        {
          MeFErrorCode: `Some other fixable error code`,
          MeFDescription: `not used`,
          TranslationKey: `not used`,
        },
      ];

      expect(areAnyRejectionsNotFixable(rejectionCodes)).toBeFalsy();
    });
  });

  describe(getSubmissionLifecycleState.name, () => {
    it(`returns checking_status before the first fetch finishes`, () => {
      expect(
        getSubmissionLifecycleState({
          taxReturn: submittedTaxReturn,
          submissionStatus: undefined,
          isFetching: true,
          fetchError: undefined,
          lastFetchAttempt: null,
        })
      ).toEqual(`checking_status`);
    });

    it(`returns status_fetch_error when status lookup fails`, () => {
      expect(
        getSubmissionLifecycleState({
          taxReturn: submittedTaxReturn,
          submissionStatus: undefined,
          isFetching: false,
          fetchError: new Error(`boom`),
          lastFetchAttempt: new Date(),
        })
      ).toEqual(`status_fetch_error`);
    });

    it(`returns awaiting_acknowledgement when the latest submission is not yet acknowledged`, () => {
      const unacknowledgedTaxReturn: TaxReturn = {
        ...submittedTaxReturn,
        taxReturnSubmissions: [
          {
            id: `submission-1`,
            receiptId: null,
            submitUserId: `user-1`,
            createdAt: new Date().toISOString(),
            submissionReceivedAt: null,
          },
        ],
      };

      expect(
        getSubmissionLifecycleState({
          taxReturn: unacknowledgedTaxReturn,
          submissionStatus: undefined,
          isFetching: false,
          fetchError: undefined,
          lastFetchAttempt: new Date(),
        })
      ).toEqual(`awaiting_acknowledgement`);
    });

    it(`returns awaiting_status when the latest submission is acknowledged but still has no status object`, () => {
      expect(
        getSubmissionLifecycleState({
          taxReturn: submittedTaxReturn,
          submissionStatus: undefined,
          isFetching: false,
          fetchError: undefined,
          lastFetchAttempt: new Date(),
        })
      ).toEqual(`awaiting_status`);
    });

    it(`returns resubmission_awaiting_status when the latest acknowledged resubmission is newer than the stored status`, () => {
      const resubmittedTaxReturn: TaxReturn = {
        ...submittedTaxReturn,
        taxReturnSubmissions: [
          ...submittedTaxReturn.taxReturnSubmissions,
          {
            id: `submission-2`,
            receiptId: `receipt-2`,
            submitUserId: `user-1`,
            createdAt: new Date(Date.now() + 60_000).toISOString(),
            submissionReceivedAt: new Date(Date.now() + 61_000).toISOString(),
          },
        ],
      };

      expect(
        getSubmissionLifecycleState({
          taxReturn: resubmittedTaxReturn,
          submissionStatus: acceptedStatus,
          isFetching: false,
          fetchError: undefined,
          lastFetchAttempt: new Date(),
        })
      ).toEqual(`resubmission_awaiting_status`);
    });

    it(`returns status_ready when a submission status is present`, () => {
      expect(
        getSubmissionLifecycleState({
          taxReturn: submittedTaxReturn,
          submissionStatus: acceptedStatus,
          isFetching: false,
          fetchError: undefined,
          lastFetchAttempt: new Date(),
        })
      ).toEqual(`status_ready`);
    });
  });
});
