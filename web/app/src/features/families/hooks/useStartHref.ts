import { useSyncExternalStore } from "react";
import { hasFamilyHint } from "@/shared/session/familyHint";

const noop = () => () => {};

/** Where "Start tonight's case" goes: the setup, or the family this browser already has. */
export function useStartHref(): string {
  const hasFamily = useSyncExternalStore(noop, hasFamilyHint, () => false);
  return hasFamily ? "/family" : "/setup";
}
