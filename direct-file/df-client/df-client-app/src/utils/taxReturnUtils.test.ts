import { TaxReturn } from '../types/core.js';
import { CURRENT_TAX_YEAR, FEDERAL_RETURN_STATUS } from '../constants/taxConstants.js';
import { v4 as uuidv4 } from 'uuid';
import {
  getLatestSubmission,
  getLatestSubmissionStage,
  hasSubmissionAcknowledgement,
  isSubmissionStatusStaleForLatestSubmission,
} from './taxReturnUtils.js';

describe(`taxReturnUtils`, () => {
  describe(`getLatestSubmission()`, () => {
    it(`returns undefined when there are no submissions to retrieve`, () => {
      const taxReturn: TaxReturn = {
        id: uuidv4(),
        createdAt: new Date().toISOString(),
        taxYear: parseInt(CURRENT_TAX_YEAR),
        facts: {},
        taxReturnSubmissions: [],
        isEditable: true,
        surveyOptIn: null,
      };

      const latest = getLatestSubmission(taxReturn);

      expect(latest).toBeUndefined();
    });
    it(`gets the latest submission`, () => {
      const userId = uuidv4();
      const taxReturn: TaxReturn = {
        id: uuidv4(),
        createdAt: new Date().toISOString(),
        taxYear: parseInt(CURRENT_TAX_YEAR),
        facts: {},
        surveyOptIn: null,
        taxReturnSubmissions: [
          {
            id: uuidv4(),
            receiptId: `old`,
            createdAt: `${CURRENT_TAX_YEAR}-01-01`,
            submitUserId: userId,
            submissionReceivedAt: `${CURRENT_TAX_YEAR}-01-01`,
          },
          {
            id: uuidv4(),
            receiptId: `new`,
            createdAt: `${CURRENT_TAX_YEAR}-04-15`,
            submitUserId: userId,
            submissionReceivedAt: `${CURRENT_TAX_YEAR}-04-15`,
          },
          {
            id: uuidv4(),
            receiptId: `middle`,
            createdAt: `${CURRENT_TAX_YEAR}-02-28`,
            submitUserId: userId,
            submissionReceivedAt: `${CURRENT_TAX_YEAR}-02-28`,
          },
        ],
        isEditable: false,
      };

      const latest = getLatestSubmission(taxReturn);

      expect(latest).not.toBeUndefined();
      expect(latest?.receiptId).toEqual(`new`);
    });
  });

  describe(hasSubmissionAcknowledgement.name, () => {
    it(`returns false when receipt or received-at is missing`, () => {
      expect(
        hasSubmissionAcknowledgement({
          id: uuidv4(),
          receiptId: null,
          createdAt: `${CURRENT_TAX_YEAR}-04-15`,
          submitUserId: uuidv4(),
          submissionReceivedAt: null,
        })
      ).toBe(false);
    });

    it(`returns true when both acknowledgement fields are present`, () => {
      expect(
        hasSubmissionAcknowledgement({
          id: uuidv4(),
          receiptId: `receipt-1`,
          createdAt: `${CURRENT_TAX_YEAR}-04-15`,
          submitUserId: uuidv4(),
          submissionReceivedAt: `${CURRENT_TAX_YEAR}-04-15`,
        })
      ).toBe(true);
    });
  });

  describe(getLatestSubmissionStage.name, () => {
    it(`detects an unacknowledged resubmission`, () => {
      const userId = uuidv4();
      const taxReturn: TaxReturn = {
        id: uuidv4(),
        createdAt: new Date().toISOString(),
        taxYear: parseInt(CURRENT_TAX_YEAR),
        facts: {},
        surveyOptIn: null,
        taxReturnSubmissions: [
          {
            id: uuidv4(),
            receiptId: `receipt-1`,
            createdAt: `${CURRENT_TAX_YEAR}-04-01T09:00:00.000Z`,
            submitUserId: userId,
            submissionReceivedAt: `${CURRENT_TAX_YEAR}-04-01T09:05:00.000Z`,
          },
          {
            id: uuidv4(),
            receiptId: null,
            createdAt: `${CURRENT_TAX_YEAR}-04-10T09:00:00.000Z`,
            submitUserId: userId,
            submissionReceivedAt: null,
          },
        ],
        isEditable: false,
      };

      expect(getLatestSubmissionStage(taxReturn)).toEqual(`resubmitted_unacknowledged`);
    });
  });

  describe(isSubmissionStatusStaleForLatestSubmission.name, () => {
    it(`detects when a stored status predates the latest submission`, () => {
      const userId = uuidv4();
      const taxReturn: TaxReturn = {
        id: uuidv4(),
        createdAt: new Date().toISOString(),
        taxYear: parseInt(CURRENT_TAX_YEAR),
        facts: {},
        surveyOptIn: null,
        taxReturnSubmissions: [
          {
            id: uuidv4(),
            receiptId: `receipt-1`,
            createdAt: `${CURRENT_TAX_YEAR}-04-15T15:00:00.000Z`,
            submitUserId: userId,
            submissionReceivedAt: `${CURRENT_TAX_YEAR}-04-15T15:05:00.000Z`,
          },
        ],
        isEditable: false,
      };

      expect(
        isSubmissionStatusStaleForLatestSubmission(taxReturn, {
          status: FEDERAL_RETURN_STATUS.ACCEPTED,
          rejectionCodes: [],
          createdAt: `${CURRENT_TAX_YEAR}-04-14T15:00:00.000Z`,
        })
      ).toBe(true);
    });
  });
});
