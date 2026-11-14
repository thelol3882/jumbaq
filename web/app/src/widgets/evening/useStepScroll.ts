import { useEffect, useRef } from "react";

/** Brings the top of the step into view when the step changes, so a phone never lands mid-page. Not on the first render. */
export function useStepScroll<T extends HTMLElement>(step: string) {
  const ref = useRef<T>(null);
  const previous = useRef(step);
  useEffect(() => {
    if (previous.current === step) return;
    previous.current = step;
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    ref.current?.scrollIntoView({ behavior: reduced ? "auto" : "smooth", block: "start" });
  }, [step]);
  return ref;
}
