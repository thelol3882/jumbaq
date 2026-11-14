import { useOpenPortalMutation } from "../api/billingApi";

/** Sends the parent to the Stripe page where the subscription is managed or cancelled. */
export function usePortal() {
  const [open, { isLoading, error }] = useOpenPortalMutation();
  const openPortal = async () => {
    try {
      const { url } = await open().unwrap();
      window.location.assign(url);
    } catch {
      // `error` holds it for the screen
    }
  };
  return { openPortal, redirecting: isLoading, error };
}
