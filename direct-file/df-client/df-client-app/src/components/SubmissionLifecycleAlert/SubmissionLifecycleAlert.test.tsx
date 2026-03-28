import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';

import { CURRENT_TAX_YEAR, FEDERAL_RETURN_STATUS } from '../../constants/taxConstants.js';
import { TaxReturn, TaxReturnSubmissionStatus } from '../../types/core.js';
import SubmissionLifecycleAlert from './SubmissionLifecycleAlert.js';

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

describe(`SubmissionLifecycleAlert`, () => {
  it(`renders nothing once a submission status is ready`, () => {
    const { container } = render(
      <SubmissionLifecycleAlert
        taxReturn={submittedTaxReturn}
        submissionStatus={acceptedStatus}
        isFetching={false}
        fetchError={undefined}
        lastFetchAttempt={new Date()}
      />
    );

    expect(container).toBeEmptyDOMElement();
  });

  it(`renders a retry action when the status fetch fails`, async () => {
    const onRetry = vi.fn();
    const user = userEvent.setup();

    render(
      <SubmissionLifecycleAlert
        taxReturn={submittedTaxReturn}
        submissionStatus={undefined}
        isFetching={false}
        fetchError={new Error(`boom`)}
        lastFetchAttempt={new Date()}
        onRetry={onRetry}
      />
    );

    await user.click(screen.getByRole(`button`, { name: `Try again` }));

    expect(screen.getByText(/could not refresh your submission status/i)).toBeInTheDocument();
    expect(onRetry).toHaveBeenCalledTimes(1);
  });

  it(`renders a refresh action when the submission exists but acknowledgement is still unavailable`, async () => {
    const onRetry = vi.fn();
    const user = userEvent.setup();

    render(
      <SubmissionLifecycleAlert
        taxReturn={submittedTaxReturn}
        submissionStatus={undefined}
        isFetching={false}
        fetchError={undefined}
        lastFetchAttempt={new Date()}
        onRetry={onRetry}
      />
    );

    await user.click(screen.getByRole(`button`, { name: `Refresh status now` }));

    expect(
      screen.getByText(/waiting on a status update/i)
    ).toBeInTheDocument();
    expect(onRetry).toHaveBeenCalledTimes(1);
  });

  it(`renders acknowledgement-specific copy when the latest submission has not been registered yet`, () => {
    const unacknowledgedTaxReturn: TaxReturn = {
      ...submittedTaxReturn,
      taxReturnSubmissions: [
        {
          id: `submission-2`,
          receiptId: null,
          submitUserId: `user-2`,
          createdAt: new Date().toISOString(),
          submissionReceivedAt: null,
        },
      ],
    };

    render(
      <SubmissionLifecycleAlert
        taxReturn={unacknowledgedTaxReturn}
        submissionStatus={undefined}
        isFetching={false}
        fetchError={undefined}
        lastFetchAttempt={new Date()}
      />
    );

    expect(
      screen.getByText(/waiting for acknowledgement/i)
    ).toBeInTheDocument();
  });
});
