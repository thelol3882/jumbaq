import { toApiError } from "@/shared/api/errors";
import { useStartNextCaseMutation } from "../api/casesApi";

/**
 * Starts the next case. `notYet` is the answer "needs a subscription": the widget decides what
 * follows (`onNotYet`), as it does after a start (`onStarted`). `error` is any other failure.
 */
export function useStartNextCase({ onStarted, onNotYet }: { onStarted: () => void; onNotYet?: () => void | Promise<void> }) {
  const [startNext, state] = useStartNextCaseMutation();
  const notYet = state.error !== undefined && toApiError(state.error).code === "billing.payment_required";

  const start = async () => {
    try {
      await startNext().unwrap();
      onStarted();
    } catch (error) {
      if (toApiError(error).code === "billing.payment_required") await onNotYet?.();
    }
  };

  return { start, starting: state.isLoading, notYet, error: notYet ? undefined : state.error };
}
