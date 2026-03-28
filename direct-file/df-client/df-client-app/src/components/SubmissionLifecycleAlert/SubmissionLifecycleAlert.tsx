import { Alert, Button } from '@trussworks/react-uswds';
import { TaxReturn, TaxReturnSubmissionStatus } from '../../types/core.js';
import { getSubmissionLifecycleState } from '../../utils/submissionStatusUtils.js';

type SubmissionLifecycleAlertProps = {
  taxReturn: TaxReturn | null | undefined;
  submissionStatus: TaxReturnSubmissionStatus | undefined;
  isFetching: boolean;
  fetchError: unknown;
  lastFetchAttempt: Date | null;
  onRetry?: () => void;
  className?: string;
};

const SubmissionLifecycleAlert = ({
  taxReturn,
  submissionStatus,
  isFetching,
  fetchError,
  lastFetchAttempt,
  onRetry,
  className,
}: SubmissionLifecycleAlertProps) => {
  const lifecycleState = getSubmissionLifecycleState({
    taxReturn,
    submissionStatus,
    isFetching,
    fetchError,
    lastFetchAttempt,
  });

  if (lifecycleState === `not_submitted` || lifecycleState === `status_ready`) {
    return null;
  }

  if (lifecycleState === `checking_status`) {
    return (
      <Alert
        type='info'
        headingLevel='h3'
        heading='We are checking the latest federal submission status'
        className={className}
      >
        Your return was submitted. We are waiting for the status service to confirm the most recent IRS response.
      </Alert>
    );
  }

  if (lifecycleState === `status_fetch_error`) {
    return (
      <Alert
        type='warning'
        headingLevel='h3'
        heading='We could not refresh your submission status'
        className={className}
      >
        <span>
          Your return may still be progressing normally, but Direct File could not refresh the latest status just now.
        </span>
        {onRetry && (
          <span className='display-block margin-top-2'>
            <Button type='button' outline onClick={onRetry}>
              Try again
            </Button>
          </span>
        )}
      </Alert>
    );
  }

  const awaitingAcknowledgement = lifecycleState === `awaiting_acknowledgement`;
  const awaitingResubmissionAcknowledgement =
    lifecycleState === `resubmission_awaiting_acknowledgement`;
  const awaitingStatus = lifecycleState === `awaiting_status`;
  const awaitingResubmissionStatus = lifecycleState === `resubmission_awaiting_status`;

  return (
    <Alert
      type='info'
      headingLevel='h3'
      heading={
        awaitingAcknowledgement
          ? 'Your return was submitted and is waiting for acknowledgement'
          : awaitingResubmissionAcknowledgement
            ? 'Your resubmission is waiting for acknowledgement'
            : awaitingResubmissionStatus
              ? 'Your resubmission is acknowledged and waiting on a status update'
              : 'Your return is acknowledged and waiting on a status update'
      }
      className={className}
    >
      <span>
        {awaitingAcknowledgement
          ? 'Direct File has the submission request, but the latest filing has not been registered with the status service yet.'
          : awaitingResubmissionAcknowledgement
            ? 'Direct File recorded a newer submission attempt, and we are waiting for the status service to register that resubmission.'
            : awaitingStatus
              ? 'The latest submission has been acknowledged, and we are waiting for the IRS status response.'
              : 'The latest resubmission has been acknowledged, and we are waiting for the IRS status response.'}
      </span>
      {onRetry && (
        <span className='display-block margin-top-2'>
          <Button type='button' outline onClick={onRetry}>
            Refresh status now
          </Button>
        </span>
      )}
    </Alert>
  );
};

export default SubmissionLifecycleAlert;
