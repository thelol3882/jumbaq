import { useEffect, useRef } from "react";
import { delayUntil } from "@/shared/lib/delay";

/**
 * Asks again just after an ISO time, so a screen that waits for it (an evening that opens at
 * a set hour) changes by itself. A tab that was asleep when the time came asks as soon as it is
 * visible again, because its timer may not have fired on time.
 */
export function useRefetchAt(iso: string | null, refetch: () => unknown): void {
  const latest = useRef(refetch);
  useEffect(() => {
    latest.current = refetch;
  });

  useEffect(() => {
    const delay = delayUntil(iso, Date.now());
    if (delay === null || !iso) return;
    const at = Date.parse(iso);
    const timer = window.setTimeout(() => void latest.current(), delay);
    const onVisibility = () => {
      if (document.visibilityState === "visible" && Date.now() >= at) void latest.current();
    };
    document.addEventListener("visibilitychange", onVisibility);
    return () => {
      window.clearTimeout(timer);
      document.removeEventListener("visibilitychange", onVisibility);
    };
  }, [iso]);
}
