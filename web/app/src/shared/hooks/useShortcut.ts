import { useEffect, useRef, useSyncExternalStore } from "react";

/**
 * ⌘↵ on a Mac, Ctrl+↵ elsewhere, from anywhere on the page. Only for the one main action
 * of a screen, so it never clashes with typing.
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

const noop = () => () => {};
const isApple = () => /Mac|iPhone|iPad/.test(navigator.platform || navigator.userAgent);

/** The name of the modifier key for the hints: ⌘ on Apple devices, Ctrl elsewhere. */
export function useModifierKey(): string {
  return useSyncExternalStore(noop, () => (isApple() ? "⌘" : "Ctrl"), () => "⌘");
}
