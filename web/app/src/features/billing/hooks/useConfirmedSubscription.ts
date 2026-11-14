import { useRefetchWhile } from "@/shared/hooks/useRefetchWhile";
import { useGetSubscriptionQuery } from "../api/billingApi";

/**
 * After Stripe sends the parent back, the subscription is active only once Stripe's webhook has
 * reached the API, a few seconds later. Asks again until then, and says when it is slow.
 */
export function useConfirmedSubscription() {
  // A cached answer from before the payment would say "not active" for good.
  const query = useGetSubscriptionQuery(undefined, { refetchOnMountOrArgChange: true });
  const active = query.data?.active === true;
  const waiting = !active && !query.isError;
  const { slow } = useRefetchWhile(waiting, query.refetch, query.data?.status ?? "none");

  return { active, confirming: waiting, slow, error: query.error, retry: query.refetch };
}
