import { useEffect } from "react";

const EVERY_MS = 3000;

/** Asks again every few seconds while the worker is still writing what the screen waits for. */
export function useRefetchWhile(waiting: boolean, refetch: () => unknown) {
  useEffect(() => {
    if (!waiting) return;
    const timer = window.setInterval(() => void refetch(), EVERY_MS);
    return () => window.clearInterval(timer);
  }, [waiting, refetch]);
}
