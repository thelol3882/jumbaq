import { useFormatter } from "next-intl";
import { useSyncExternalStore } from "react";
import { hasFamilyHint } from "@/shared/session/familyHint";
import { useFamily } from "./useFamily";

const noop = () => () => {};

/**
 * The detectives' names for a header ("Fox & Owl"), or nothing while the family is unknown.
 * A visitor without the family hint makes no API call; the request is shared with `useFamily`.
 */
export function useDetectivesLabel(): string | undefined {
  const format = useFormatter();
  const hinted = useSyncExternalStore(noop, hasFamilyHint, () => false);
  const { family } = useFamily({ skip: !hinted });
  return family ? format.list(family.kids.map((kid) => kid.nickname), { type: "conjunction", style: "short" }) : undefined;
}
