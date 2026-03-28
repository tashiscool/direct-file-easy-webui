import { Provider } from 'react-redux';
import { render, screen } from '@testing-library/react';
import { v4 as uuidv4 } from 'uuid';
import { vi } from 'vitest';

import { TaxReturnDetails } from './TaxReturnDetails.js';
import { wrapComponent } from '../../test/helpers.js';
import { setupStore } from '../../redux/store.js';
import { CURRENT_TAX_YEAR, FEDERAL_RETURN_STATUS } from '../../constants/taxConstants.js';
import { SubmissionStatusContext } from '../../context/SubmissionStatusContext/SubmissionStatusContext.js';
import { TaxReturnsContext } from '../../context/TaxReturnsContext.js';
import { TaxReturn, TaxReturnSubmissionStatus } from '../../types/core.js';

const { mockUseTranslation } = vi.hoisted(() => ({
  mockUseTranslation: () => ({
    t: (key: string) => key,
    i18n: { language: `en`, options: {} },
  }),
}));

vi.mock(`../../components/Heading.js`, () => ({
  default: () => <h1>Federal tax return</h1>,
}));

vi.mock(`../../components/DownloadPDFButton/index.js`, () => ({
  default: () => <button type='button'>Download PDF</button>,
}));

vi.mock(`../../components/InfoDisplay.js`, () => ({
  default: () => <div data-testid='info-display' />,
}));

vi.mock(`../../components/ConditionalList/ConditionalList.js`, () => ({
  ConditionalList: () => <div data-testid='conditional-list' />,
}));

vi.mock(`../../components/Translation/index.js`, () => ({
  default: ({ i18nKey }: { i18nKey: string }) => <span>{i18nKey}</span>,
}));

vi.mock(`./RejectedReturnDetails/RejectedReturnDetails.js`, () => ({
  default: () => <div data-testid='rejected-return-details' />,
}));

vi.mock(`./ErroredReturnDetails/ErroredReturnDetails.js`, () => ({
  default: () => <div data-testid='errored-return-details' />,
}));

vi.mock(`../../components/FederalReturnStatusAlert/FederalReturnStatusAlert.js`, () => ({
  default: () => <div data-testid='federal-return-status-alert' />,
}));

vi.mock(`../../components/SubmissionLifecycleAlert/SubmissionLifecycleAlert.js`, () => ({
  default: () => <div data-testid='submission-lifecycle-alert' />,
}));

vi.mock(`../../hooks/useFact`, () => ({
  default: vi.fn(() => [false]),
}));

vi.mock(`react-i18next`, () => ({
  useTranslation: mockUseTranslation,
  initReactI18next: {
    type: `3rdParty`,
    init: () => {},
  },
  Trans: ({ children }: { children: unknown }) => children,
}));

describe(`TaxReturnDetails`, () => {
  const acknowledgedSubmission = {
    id: uuidv4(),
    submitUserId: uuidv4(),
    createdAt: new Date().toISOString(),
    submissionReceivedAt: new Date().toISOString(),
    receiptId: `receipt-1`,
  };

  const baseTaxReturn: TaxReturn = {
    id: uuidv4(),
    createdAt: new Date().toISOString(),
    taxYear: parseInt(CURRENT_TAX_YEAR),
    facts: {},
    taxReturnSubmissions: [acknowledgedSubmission],
    isEditable: true,
    surveyOptIn: null,
  };

  const pendingStatus: TaxReturnSubmissionStatus = {
    status: FEDERAL_RETURN_STATUS.PENDING,
    rejectionCodes: [],
    createdAt: acknowledgedSubmission.createdAt,
  };

  const renderComponent = ({
    taxReturn = baseTaxReturn,
    submissionStatus = pendingStatus,
  }: {
    taxReturn?: TaxReturn;
    submissionStatus?: TaxReturnSubmissionStatus;
  } = {}) => {
    render(
      wrapComponent(
        <Provider store={setupStore()}>
          <TaxReturnsContext.Provider
            value={{
              taxReturns: [taxReturn],
              currentTaxReturnId: taxReturn.id,
              fetchTaxReturns: vi.fn(),
              isFetching: false,
              fetchSuccess: true,
            }}
          >
            <SubmissionStatusContext.Provider
              value={{
                submissionStatus,
                setSubmissionStatus: vi.fn(),
                fetchSubmissionStatus: vi.fn(),
                isFetching: false,
                fetchSuccess: true,
                fetchError: false,
                lastFetchAttempt: new Date(),
              }}
            >
              <TaxReturnDetails />
            </SubmissionStatusContext.Provider>
          </TaxReturnsContext.Provider>
        </Provider>
      )
    );
  };

  it(`renders the latest acknowledgement date and receipt id`, () => {
    renderComponent();

    expect(screen.getByText(/IRS acknowledged receipt on/i)).toBeInTheDocument();
    expect(screen.getByText(/Submission receipt ID:/i)).toBeInTheDocument();
  });

  it(`warns when the latest resubmission is newer than the loaded status`, () => {
    const resubmittedTaxReturn: TaxReturn = {
      ...baseTaxReturn,
      taxReturnSubmissions: [
        ...baseTaxReturn.taxReturnSubmissions,
        {
          id: uuidv4(),
          submitUserId: uuidv4(),
          createdAt: new Date(Date.now() + 61_000).toISOString(),
          submissionReceivedAt: new Date(Date.now() + 62_000).toISOString(),
          receiptId: `receipt-2`,
        },
      ],
    };

    renderComponent({ taxReturn: resubmittedTaxReturn });

    expect(
      screen.getByText(/Your latest submission is newer than the status shown below/i)
    ).toBeInTheDocument();
  });
});
