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
        <p>
          Your return may still be progressing normally, but Direct File could not refresh the latest status just now.
        </p>
        {onRetry && (
          <div className='margin-top-2'>
            <Button type='button' outline onClick={onRetry}>
              Try again
            </Button>
          </div>
        )}
      </Alert>
    );
  }

  return (
    <Alert
      type='info'
      headingLevel='h3'
      heading='Your return was submitted and is waiting on a status update'
      className={className}
    >
      Direct File has your submission, but the status app has not returned a current acknowledgement yet. Check back again soon.
    </Alert>
  );
};

export default SubmissionLifecycleAlert;
