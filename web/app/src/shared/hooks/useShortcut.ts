import { useEffect, useRef } from "react";

/**
 * ⌘↵ on a Mac, Ctrl+↵ elsewhere, from anywhere on the page. Only for the one main action
 * of a screen, so it never clashes with typing. No hint on screen: a parent who knows the
 * key uses it, and nobody else has to read about it.
 */
export function useSubmitShortcut(onSubmit: () => void, enabled = true) {
  const latest = useRef(onSubmit);
  useEffect(() => {
    latest.current = onSubmit;
  });

  useEffect(() => {
    if (!enabled) return;
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Enter" && (event.metaKey || event.ctrlKey) && !event.repeat) {
        event.preventDefault();
        latest.current();
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [enabled]);
}
