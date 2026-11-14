import { useEffect, useState } from "react";

const EVERY_MS = 3000;
const SLOW_EVERY_MS = 15000;
// Each step of the worker (plan, one evening) takes under 90 s with real Claude.
const SLOW_AFTER_MS = 90_000;

/**
 * Asks again every few seconds while the worker is still writing what the screen waits for.
 * A hidden tab does not ask. When `progress` (what the screen shows of the worker's state) has
 * not changed for about 90 s, it asks less often and says it is slow.
 */
export function useRefetchWhile(waiting: boolean, refetch: () => unknown, progress = ""): { slow: boolean } {
  const [slow, setSlow] = useState(false);

  useEffect(() => {
    if (!waiting) return;
    const started = Date.now();
    let timer: number | undefined;
    const visible = () => document.visibilityState === "visible";
    const tick = () => {
      const late = Date.now() - started > SLOW_AFTER_MS;
      setSlow(late);
      if (visible()) void refetch();
      timer = window.setTimeout(tick, late ? SLOW_EVERY_MS : EVERY_MS);
    };
    const onVisibility = () => {
      if (visible()) void refetch();
    };
    timer = window.setTimeout(tick, EVERY_MS);
    document.addEventListener("visibilitychange", onVisibility);
    return () => {
      window.clearTimeout(timer);
      document.removeEventListener("visibilitychange", onVisibility);
      setSlow(false);
    };
  }, [waiting, refetch, progress]);

  return { slow: waiting && slow };
}
