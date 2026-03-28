import { ReactNode, useContext, useState } from 'react';
import { act, renderHook } from '@testing-library/react';
import { v4 as uuidv4 } from 'uuid';
import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest';

import { CURRENT_TAX_YEAR, FEDERAL_RETURN_STATUS } from '../constants/taxConstants.js';
import { SubmissionStatusContext } from '../context/SubmissionStatusContext/SubmissionStatusContext.js';
import { TaxReturnsContext } from '../context/TaxReturnsContext.js';
import { TaxReturn, TaxReturnSubmissionStatus } from '../types/core.js';
import { getCurrentTaxYearReturn } from '../utils/taxReturnUtils.js';
import { SubmissionStatusPollResult, usePollForSubmissionStatus } from './usePollForSubmissionStatus.js';

const TEST_POLLING_INTERVAL_MS = 100;
const TEST_POLLING_MAXIMUM_ATTEMPTS = 3;

const mockFetchTaxReturnsApiRequest = vi.fn();
const mockFetchSubmissionStatusApiRequest = vi.fn();

type SubmissionTestData = {
  taxReturn: TaxReturn;
  status?: TaxReturnSubmissionStatus;
};

const buildTaxReturn = (submissions: TaxReturn['taxReturnSubmissions']): TaxReturn => ({
  id: uuidv4(),
  createdAt: new Date().toISOString(),
  taxYear: parseInt(CURRENT_TAX_YEAR),
  facts: {},
  taxReturnSubmissions: submissions,
  isEditable: false,
  surveyOptIn: null,
});

const acceptedStatus: TaxReturnSubmissionStatus = {
  status: FEDERAL_RETURN_STATUS.ACCEPTED,
  rejectionCodes: [],
  createdAt: new Date().toISOString(),
};

const pendingStatus: TaxReturnSubmissionStatus = {
  status: FEDERAL_RETURN_STATUS.PENDING,
  rejectionCodes: [],
  createdAt: new Date().toISOString(),
};

type WrapperProps = {
  children: ReactNode;
  initialTaxReturn: TaxReturn;
  initialStatus?: TaxReturnSubmissionStatus;
};

const Wrapper = ({ children, initialTaxReturn, initialStatus }: WrapperProps) => {
  const [taxReturns, setTaxReturns] = useState([initialTaxReturn]);
  const [submissionStatus, setSubmissionStatus] = useState<TaxReturnSubmissionStatus | undefined>(initialStatus);

  const fetchTaxReturns = () => {
    const fetchedReturns = mockFetchTaxReturnsApiRequest();
    if (fetchedReturns) {
      setTaxReturns(fetchedReturns);
    }
  };

  const fetchSubmissionStatus = () => {
    const fetchedStatus = mockFetchSubmissionStatusApiRequest();
    setSubmissionStatus(fetchedStatus);
  };

  return (
    <TaxReturnsContext.Provider
      value={{
        taxReturns,
        currentTaxReturnId: initialTaxReturn.id,
        fetchTaxReturns,
        isFetching: false,
        fetchSuccess: true,
      }}
    >
      <SubmissionStatusContext.Provider
        value={{
          submissionStatus,
          setSubmissionStatus,
          fetchSubmissionStatus,
          isFetching: false,
          fetchSuccess: false,
          fetchError: false,
          lastFetchAttempt: new Date(),
        }}
      >
        {children}
      </SubmissionStatusContext.Provider>
    </TaxReturnsContext.Provider>
  );
};

const HookRenderer = (): SubmissionTestData & SubmissionStatusPollResult => {
  const { taxReturns } = useContext(TaxReturnsContext);
  const { submissionStatus } = useContext(SubmissionStatusContext);
  const currentTaxReturn = getCurrentTaxYearReturn(taxReturns)!;

  const { hasFinishedPolling, numPollsAttempted } = usePollForSubmissionStatus(
    currentTaxReturn,
    TEST_POLLING_INTERVAL_MS,
    TEST_POLLING_MAXIMUM_ATTEMPTS
  );

  return {
    hasFinishedPolling,
    numPollsAttempted,
    taxReturn: currentTaxReturn,
    status: submissionStatus,
  };
};

describe(`usePollForSubmissionStatus`, () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it(`does not poll when the return has not been submitted`, () => {
    const taxReturn = buildTaxReturn([]);

    const { result } = renderHook(HookRenderer, {
      wrapper: ({ children }) => (
        <Wrapper initialTaxReturn={taxReturn}>{children}</Wrapper>
      ),
    });

    act(() => {
      vi.advanceTimersByTime(TEST_POLLING_INTERVAL_MS * 4);
    });

    expect(result.current.hasFinishedPolling).toBe(false);
    expect(result.current.numPollsAttempted).toBe(0);
    expect(mockFetchTaxReturnsApiRequest).not.toHaveBeenCalled();
    expect(mockFetchSubmissionStatusApiRequest).not.toHaveBeenCalled();
  });

  it(`polls until a missing acknowledgement is replaced by a real status`, async () => {
    const taxReturn = buildTaxReturn([
      {
        id: uuidv4(),
        submitUserId: uuidv4(),
        createdAt: new Date().toISOString(),
        submissionReceivedAt: null,
        receiptId: null,
      },
    ]);

    mockFetchTaxReturnsApiRequest.mockReturnValue([taxReturn]);
    mockFetchSubmissionStatusApiRequest.mockReturnValueOnce(undefined).mockReturnValue(acceptedStatus);

    const { result } = renderHook(HookRenderer, {
      wrapper: ({ children }) => (
        <Wrapper initialTaxReturn={taxReturn}>{children}</Wrapper>
      ),
    });

    await act(async () => {
      await vi.advanceTimersByTimeAsync(TEST_POLLING_INTERVAL_MS);
    });

    expect(mockFetchSubmissionStatusApiRequest).toHaveBeenCalledTimes(1);

    await act(async () => {
      await vi.advanceTimersByTimeAsync(TEST_POLLING_INTERVAL_MS);
    });

    expect(result.current.status?.status).toBe(FEDERAL_RETURN_STATUS.ACCEPTED);

    await act(async () => {
      await vi.advanceTimersByTimeAsync(0);
    });

    expect(result.current.hasFinishedPolling).toBe(true);

    expect(mockFetchTaxReturnsApiRequest).toHaveBeenCalled();
    expect(mockFetchSubmissionStatusApiRequest).toHaveBeenCalled();
    expect(result.current.numPollsAttempted).toBeGreaterThan(0);
  });

  it(`continues polling while the latest acknowledgement is still pending`, async () => {
    const taxReturn = buildTaxReturn([
      {
        id: uuidv4(),
        submitUserId: uuidv4(),
        createdAt: new Date().toISOString(),
        submissionReceivedAt: new Date().toISOString(),
        receiptId: uuidv4(),
      },
    ]);

    mockFetchTaxReturnsApiRequest.mockReturnValue([taxReturn]);
    mockFetchSubmissionStatusApiRequest
      .mockReturnValueOnce(pendingStatus)
      .mockReturnValueOnce(acceptedStatus)
      .mockReturnValue(acceptedStatus);

    const { result } = renderHook(HookRenderer, {
      wrapper: ({ children }) => (
        <Wrapper initialTaxReturn={taxReturn} initialStatus={pendingStatus}>
          {children}
        </Wrapper>
      ),
    });

    await act(async () => {
      await vi.advanceTimersByTimeAsync(TEST_POLLING_INTERVAL_MS);
    });

    expect(mockFetchSubmissionStatusApiRequest).toHaveBeenCalledTimes(1);

    await act(async () => {
      await vi.advanceTimersByTimeAsync(TEST_POLLING_INTERVAL_MS);
    });

    expect(result.current.status?.status).toBe(FEDERAL_RETURN_STATUS.ACCEPTED);

    await act(async () => {
      await vi.advanceTimersByTimeAsync(0);
    });

    expect(result.current.hasFinishedPolling).toBe(true);

    expect(mockFetchTaxReturnsApiRequest).toHaveBeenCalledTimes(2);
    expect(mockFetchSubmissionStatusApiRequest).toHaveBeenCalledTimes(2);
  });
});
