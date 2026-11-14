import { useSyncExternalStore } from "react";

// True on the server and during hydration: parents play on a phone, so the first HTML is
// the mobile one, and the desktop UI swaps in right after hydration.
export function useIsMobile(breakpoint = 768) {
  const query = `(max-width: ${breakpoint}px)`;
  return useSyncExternalStore(
    (onChange) => {
      const mql = window.matchMedia(query);
      mql.addEventListener("change", onChange);
      return () => mql.removeEventListener("change", onChange);
    },
    () => window.matchMedia(query).matches,
    () => true,
  );
}
