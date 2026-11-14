import { useStartCheckoutMutation } from "../api/billingApi";

/** Sends the parent to the payment page. The page stays as it is when that fails. */
export function useCheckout() {
  const [start, { isLoading, error }] = useStartCheckoutMutation();
  const checkout = async () => {
    try {
      const { url } = await start().unwrap();
      window.location.assign(url);
    } catch {
      // `error` holds it for the screen
    }
  };
  return { checkout, redirecting: isLoading, error };
}
